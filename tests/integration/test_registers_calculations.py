import tempfile,unittest,json
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene
from fgmapping.services.registers import add_record,records,edit_detector,store_attachment
from fgmapping.services.calculations import run_synthetic
from fgmapping.services.reporting import normalized_snapshot
from fgmapping.domain.scene import synthetic_scene,Frame
from fgmapping.services.mesh_import import parse_mesh,ImportJob
from fgmapping.errors import CaseError
class Registers(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        p=create_case(self.root/'syn.fgcase','SYNTHETIC');self.s=CaseSession(p,self.root/'runtime');self.addCleanup(lambda:self.s.close(discard_unsaved=True))
        enable_geometry(self.s,'TEST_ENGINE');self.s.add_evidence('SYN-GEOM-01','SYNTHETIC','Synthetic source','A','test','TEST_ENGINE')
    def test_registers_evidence_and_duplicates(self):
        add_record(self.s,'SYN-E','EQUIPMENT',{'class':'VESSEL'},'SYN-GEOM-01','TEST_ENGINE')
        self.assertEqual(len(records(self.s)),1)
        for id,evidence in (('SYN-E','SYN-GEOM-01'),('SYN-X','MISSING')):
            with self.assertRaises(CaseError):add_record(self.s,id,'EQUIPMENT',{},evidence,'TEST_ENGINE')
    def test_bad_zone(self):
        for payload in ({'low':[0,0,0],'high':[1,1,1]},{'low':[2,0,0],'high':[1,1,1],'units':'m'}):
            with self.assertRaises(CaseError):add_record(self.s,'ZONE','FIRE_ZONE',payload,'SYN-GEOM-01','TEST_ENGINE')
    def test_detector_edit_orientation_and_stale(self):
        self.s.add_detector('FD','FLAME',0,0,0,'SYN-GEOM-01','TEST_ENGINE')
        run_synthetic(self.s,'RUN','SYNTHETIC_VOTES/1',{'rows':[['SYN',1,[True]]],'required_votes':1},'TEST_ENGINE')
        edit_detector(self.s,'FD',(1,2,3),(45,20,0),'NAMED_SYNTHETIC_TEST_ACTOR')
        self.assertEqual(self.s.detectors()[0][2:5],(1,2,3))
        self.assertEqual(self.s.con.execute('SELECT calculation_status FROM calculation_run').fetchone()[0],'STALE')
        self.assertEqual(normalized_snapshot(self.s)['datasets']['detectors'][0]['azimuth_deg'],45)
        with self.assertRaises(CaseError):edit_detector(self.s,'FD',(1,2,3),(0,91,0),'TEST_ENGINE')
    def test_adding_detector_stales_existing_run(self):
        run_synthetic(self.s,'RUN','SYNTHETIC_VOTES/1',{'rows':[['SYN',1,[True]]],'required_votes':1},'TEST_ENGINE')
        self.s.add_detector('NEW','FLAME',0,0,0,'SYN-GEOM-01','TEST_ENGINE')
        self.assertEqual(self.s.con.execute('SELECT calculation_status FROM calculation_run').fetchone()[0],'STALE')
    def test_geometry_stales_calculation(self):
        r=run_synthetic(self.s,'RUN','SYNTHETIC_VOTES/1',{'rows':[['SYN',1,[True]]],'required_votes':1},'TEST_ENGINE')
        self.assertEqual(r['fraction'],1);set_scene(self.s,synthetic_scene(),'TEST_ENGINE')
        row=self.s.con.execute('SELECT calculation_status,input_json,qualification_status FROM calculation_run').fetchone()
        self.assertEqual(row[0],'STALE');self.assertIn('inputs',json.loads(row[1]));self.assertEqual(row[2],'UNVERIFIED')
    def test_no_qualified_method(self):
        with self.assertRaises(CaseError):run_synthetic(self.s,'RUN','FLAME_ENGINEERING/1',{},'TEST_ENGINE')
    def test_embedded_mesh_source_and_hash(self):
        raw=b'v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3';f=Frame('F','m','SYN');m=parse_mesh(raw,'.obj',f)
        store_attachment(self.s,raw,'.obj',f.__dict__,m,'SYN-GEOM-01','TEST_ENGINE')
        self.assertEqual(self.s.con.execute('SELECT raw_bytes FROM geometry_attachment').fetchone()[0],raw)
        with self.assertRaises(CaseError):store_attachment(self.s,raw+b'\n','.obj',f.__dict__,m,'SYN-GEOM-01','TEST_ENGINE')
    def test_large_worker_output_does_not_deadlock(self):
        # >64 KiB JSON output exercises worker stdout without pipe-buffer blocking.
        raw=''.join(f'v {i} 0 0\nv {i} 1 0\nv {i} 0 1\nf {3*i+1} {3*i+2} {3*i+3}\n' for i in range(1200))
        p=self.root/'synthetic.obj';p.write_text(raw)
        r=ImportJob(p,Frame('F','m','SYN')).result();self.assertEqual(len(r['mesh']['faces']),1200)
    def test_real_evidence_export_refused(self):
        self.s.add_evidence('PROJECT','MANUAL','Not actual client data; tests refusal only','A','test','TEST_ENGINE','PROJECT_BASIS')
        with self.assertRaises(ValueError):normalized_snapshot(self.s)
