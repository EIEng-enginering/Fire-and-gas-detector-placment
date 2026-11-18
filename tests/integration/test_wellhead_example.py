"""SYNTHETIC wellhead module example: reproducible build, opens and validates.

Geometry + study setup only. Asserts the engineering gate stays BLOCKED and no
mounts, performance links or calculation runs are created by the example.
"""
import json,shutil,sqlite3,tempfile,unittest
from contextlib import closing
from pathlib import Path
from fgmapping.services.case import CaseSession
from fgmapping.services.geometry import get_scene
from fgmapping.services.basis import readiness
from fgmapping.services.bulk_import import prepare_bulk
from fgmapping.services import workspace as w
from tools import build_wellhead_example as gen
ROOT=Path(__file__).resolve().parents[2];SHIPPED=ROOT/'examples'/'SYNTHETIC_WELLHEAD_MODULE.fgcase';INPUTS=ROOT/'examples'/'wellhead'

def content(s):
    scene=get_scene(s)
    return {'scene_sha256':scene.sha256,'detectors':w.detector_rows(s),
            'details':[w.row(s,'detector_details',d['id']) for d in w.detector_rows(s)],
            'records':s.con.execute('SELECT id,kind,payload_json,evidence_id,review_status FROM engineering_record ORDER BY id').fetchall(),
            'basis':w.row(s,'study_basis','STUDY')['payload_json']}

class WellheadExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name);cls.inputs=root/'inputs';cls.case=root/'whm.fgcase'
        gen.write_inputs(cls.inputs);cls.summary=gen.build_case(cls.case,cls.inputs)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def open(self,path):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);copy=Path(tmp.name)/'c.fgcase';shutil.copyfile(path,copy)
        s=CaseSession(copy,Path(tmp.name)/'rt');self.addCleanup(s.close,True);return s
    def test_model_contents_and_levels(self):
        s=self.open(self.case);scene=get_scene(s);self.assertEqual(s.con.execute('PRAGMA user_version').fetchone()[0],3)
        self.assertEqual(len(scene.components),116);ids={c.id for c in scene.components}
        for n in range(1,9):
            for part in ('WH','XT','CAP','WV','CH','FL-R','FL-H','DROP','MV'):self.assertIn(f'W{n:02d}-{part}',ids)
        self.assertTrue({'CD-PLATE','BW-NORTH','BW-WEST','MF-SKID','HDR-PROD','HDR-TEST','WL-UNIT','WL-LUB','ER-SOUTH','ER-EAST'}<=ids)
        self.assertFalse(any(c.semantic=='DETECTOR' for c in scene.components),'example adds no detector display geometry')
        lo=[min(scene.frame(c.frame_id).world(p)[k] for c in scene.components for p in c.mesh.vertices) for k in range(3)]
        hi=[max(scene.frame(c.frame_id).world(p)[k] for c in scene.components for p in c.mesh.vertices) for k in range(3)]
        self.assertEqual((lo[0],lo[1],hi[0],hi[1]),(0.,0.,30.,20.))
        decks={c.id:max(p[2] for p in c.mesh.vertices) for c in scene.components if c.semantic in ('DECK','GRATING')}
        self.assertEqual(decks['CD-PLATE'],0.);self.assertEqual(decks['MZ-GRATE-1'],4.5);self.assertEqual(min(p[2] for c in scene.components if c.id=='UD-PLATE-S' for p in c.mesh.vertices),9.)
        for c in scene.components:
            d=c.mesh.diagnostics();self.assertEqual((d['boundary_edges'],d['nonmanifold_edges']),(0,0),c.id)
            self.assertEqual(c.evidence_id,gen.EVIDENCE)
            if c.semantic in ('ESCAPE_ROUTE','AREA_MARKER'):self.assertEqual(c.occlusion_role,'NON_OBSTRUCTING_ANNOTATION')
    def test_register_zones_basis_and_blocked_gate(self):
        s=self.open(self.case);dets=w.detector_rows(s);types=[d['detector_type'] for d in dets]
        self.assertEqual((types.count('FLAME'),types.count('POINT_GAS'),types.count('OPEN_PATH'),len(dets)),(8,12,3,23))
        self.assertTrue(all(d['review_status']=='CANDIDATE' and d['evidence_id']==gen.EVIDENCE for d in dets))
        self.assertTrue(all(0<=d['x']<=30 and 0<=d['y']<=20 and 0<d['z']<9 for d in dets))
        kinds=dict(s.con.execute('SELECT kind,count(*) FROM engineering_record GROUP BY kind').fetchall());self.assertEqual(kinds,{'EQUIPMENT':17,'FIRE_ZONE':3,'GAS_ZONE':3})
        for table in ('detector_mount','detector_performance_link','performance_dataset','calculation_run'):
            self.assertEqual(s.con.execute('SELECT count(*) FROM '+table).fetchone()[0],0,table)
        r=readiness(s);self.assertEqual(r['engineering_calculation_status'],'BLOCKED');self.assertEqual(r['qualification'],'UNVERIFIED')
        self.assertEqual(r['input_status'],'BLOCKED');self.assertIn('MIXED_STUDY_REQUIRES_SEPARATE_METHOD_BASES',r['blocking'])
        self.assertIn('PERFORMANCE_DATASET:FD-101',r['missing'])
        retained=s.con.execute("SELECT count(*) FROM ledger WHERE command='RETAIN_PREPARATION_SOURCE'").fetchone()[0];self.assertEqual(retained,1)
    def test_xlsx_template_equals_csv_template(self):
        # The shipped XLSX template carries exactly the same rows as the CSV that was imported.
        a=gen.register_rows()[1];import csv,io
        rows=list(csv.DictReader(io.StringIO((INPUTS/gen.FILES['csv']).read_text(encoding='utf8'))))
        self.assertEqual(rows,a)
        from openpyxl import load_workbook
        wb=load_workbook(INPUTS/gen.FILES['xlsx'],read_only=True);vals=[[('' if c is None else str(c)) for c in r] for r in wb['Registers'].iter_rows(values_only=True)];wb.close()
        self.assertEqual(vals[0],list(gen.register_rows()[0]));self.assertEqual([dict(zip(vals[0],v)) for v in vals[1:]],a)
    def test_shipped_example_matches_regenerated_build(self):
        self.assertTrue(SHIPPED.is_file())
        for key in ('geometry','csv','zones','basis'):
            self.assertEqual((INPUTS/gen.FILES[key]).read_bytes(),(self.inputs/gen.FILES[key]).read_bytes(),key)
        shipped=self.open(SHIPPED);built=self.open(self.case)
        self.assertEqual(content(shipped),content(built))
        self.assertEqual(shipped.name(),gen.CASE_NAME)
        with closing(sqlite3.connect(SHIPPED.as_uri()+'?mode=ro',uri=True)) as con:
            self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0],'ok');self.assertIsNone(con.execute('PRAGMA foreign_key_check').fetchone())
    def test_generator_refuses_existing_destinations(self):
        with self.assertRaises(SystemExit):gen.write_inputs(self.inputs)
        with self.assertRaises(SystemExit):gen.build_case(self.case,self.inputs)
