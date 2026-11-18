"""Rev G coverage services: schema 4, library import/assignment (F03), per-zone readiness gate,
stored reproducible runs with staleness. Engineer-reviewed results - not independently certified."""
import json,tempfile,unittest
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene,get_scene
from fgmapping.services.study_schema import enable_study
from fgmapping.services import workspace as w
from fgmapping.services import coverage as cov
from fgmapping.services.basis import set_basis,readiness
from fgmapping.domain.scene import Scene,Frame,Component,box_mesh,content_hash
from fgmapping.domain.detector_library import write_csv
from fgmapping.engine.detection import engineering_flame_coverage
from fgmapping.errors import CaseError
from tests.unit.test_coverage_engine import flame_entry,gas_entry,flame_setup,gas_setup
ROOT=Path(__file__).resolve().parents[2]
EV='TEST-EV'
def test_scene():
    comps=(Component('DECK','deck','DECK','L',box_mesh((-1,-11,-.3),(11,11,0)),EV),Component('WALL','wall','WALL','L',box_mesh((4,0,0),(4.6,10,3)),EV))
    return Scene((Frame('L','m','test frame'),),comps,'T1','1'*64)
class CoverageServices(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.path=create_case(self.root/'c.fgcase','Rev G coverage test')
        s=self.s=CaseSession(self.path,self.root/'r');self.addCleanup(lambda:self.s.close(discard_unsaved=True))
        enable_geometry(s,'T');s.add_evidence(EV,'SYNTHETIC','test','A','unit','T');set_scene(s,test_scene(),'T');enable_study(s,'T')
        for id,kind,x,az in (('F1','FLAME',0.,0.),('F2','FLAME',10.,180.),('G1','POINT_GAS',5.,0.),('O1','OPEN_PATH',0.,0.)):
            w.detector_command(s,{'id':id,'detector_type':kind,'x':x,'y':-5. if kind=='OPEN_PATH' else 0.,'z':1.,'azimuth':az,'elevation':0.,'roll':0.,'evidence_id':EV},None,'T',create=True)
        w.record_command(s,'FZ','FIRE_ZONE',{'low':[0,-10,0],'high':[10,10,2],'units':'m','description':'fire zone'},EV,'T',create=True)
        w.record_command(s,'GZ','GAS_ZONE',{'low':[0,-10,0],'high':[10,10,2],'units':'m','description':'gas zone'},EV,'T',create=True)
        w.record_command(s,'O1-RX','EQUIPMENT',{'description':'receiver','position':[10.,-5.,1.]},EV,'T',create=True)
        set_basis(s,{'contract':'fg-study-basis/1','revision':'A','study_type':'BOTH','coordinate_reference':'L','target_description':'per zone','fuel_or_gas':'per zone','voting':1,'criterion_reference':'per zone setup','target_fraction':'NOT SUPPLIED','exclusions':[],'uncertainty_reference':'grid convergence'},EV,'T')
    def enable(self):
        cov.enable_coverage(self.s,'T')
        lib=[flame_entry('FL',contour=((0,10),(45,10))),gas_entry('PG','POINT_GAS',20.),gas_entry('OP','OPEN_PATH',1.,{'min':1.,'max':50.})]
        return cov.import_library(self.s,write_csv(lib),'CSV','T')
    def fsetup(self,**k):
        p=flame_setup(spacing=.5,mode='SLICES',slices=(1.,),**k);p['zone_id']='FZ';return p
    def assign_all(self):
        cov.assign_library(self.s,'F1','FL',EV,'T');cov.assign_library(self.s,'F2','FL',EV,'T');cov.assign_library(self.s,'G1','PG',EV,'T');cov.assign_library(self.s,'O1','OP',EV,'T',receiver={'record_id':'O1-RX'})
    def test_schema4_upgrade_backup_and_reopen(self):
        self.assertEqual(readiness(self.s)['engineering_calculation_status'],'BLOCKED')
        with self.assertRaises(CaseError):cov.library(self.s)
        self.enable();self.assertEqual(self.s.con.execute('PRAGMA user_version').fetchone()[0],4);self.assertTrue(list((self.root/'r/Backups').glob('*pre_coverage4*')))
        self.s.save();self.s.close();self.s=CaseSession(self.path,self.root/'r');self.assertEqual(self.s.con.execute('PRAGMA user_version').fetchone()[0],4);self.assertEqual(len(cov.library(self.s)),3)
    def test_library_import_immutable_by_id_and_xlsx_equivalent(self):
        r=self.enable();self.assertEqual(sorted(r['added']),['FL','OP','PG'])
        self.assertEqual(cov.import_library(self.s,write_csv([flame_entry('FL',contour=((0,10),(45,10)))]),'CSV','T')['skipped_identical'],['FL'])
        with self.assertRaises(CaseError):cov.import_library(self.s,write_csv([flame_entry('FL',contour=((0,12),(45,10)))]),'CSV','T')
        starter=ROOT/'examples/library'
        a=cov.import_library(self.s,(starter/'STARTER_DETECTOR_LIBRARY_EXAMPLE_VALUES.csv').read_bytes(),'CSV','T')
        b=cov.import_library(self.s,(starter/'STARTER_DETECTOR_LIBRARY_EXAMPLE_VALUES.xlsx').read_bytes(),'XLSX','T')
        self.assertEqual(len(a['added']),7);self.assertEqual(sorted(b['skipped_identical']),sorted(a['added']))
        self.assertTrue(all(e['source']['data_status'].startswith('EXAMPLE VALUES') for k,e in cov.library(self.s).items() if k.startswith('EX-')))
        w.history(self.s,'T');self.assertNotIn('EX-GAS-OPGD-METHANE',cov.library(self.s))
    def test_assignment_is_explicit_and_type_checked(self):
        self.enable()
        with self.assertRaises(CaseError):cov.assign_library(self.s,'F1','PG',EV,'T')
        with self.assertRaises(CaseError):cov.assign_library(self.s,'O1','OP',EV,'T')
        with self.assertRaises(CaseError):cov.assign_library(self.s,'O1','OP',EV,'T',receiver={'record_id':'NOPE'})
        with self.assertRaises(CaseError):cov.assign_library(self.s,'G1','PG',EV,'T',receiver={'x':1,'y':1,'z':1})
        cov.set_zone_setup(self.s,self.fsetup(),EV,'T')
        r=readiness(self.s);self.assertEqual(r['engineering_calculation_status'],'BLOCKED');self.assertIn('LIBRARY_ENTRY_NOT_ASSIGNED:F1',r['zones']['FZ']['blockers'])
        self.assertEqual(r['zones']['GZ']['status'],'NOT CONFIGURED')
        with self.assertRaises(CaseError):cov.run_zone(self.s,'FZ','RUN1','T')
    def test_readiness_gates_fuel_fire_size_and_method(self):
        self.enable();self.assign_all()
        bad=self.fsetup();bad['method']='GAS_GEOGRAPHIC';bad['flame']=None;bad['gas']=gas_setup({'shape':'SPHERE','diameter_m':5.},100.,['POINT_GAS'])['gas']
        with self.assertRaises(CaseError):cov.set_zone_setup(self.s,bad,EV,'T')
        p=self.fsetup();p['flame']['fuel']='methane';cov.set_zone_setup(self.s,p,EV,'T')
        self.assertTrue(any(b.startswith('FUEL_MISMATCH:F1') for b in cov.coverage_readiness(self.s)['FZ']['blockers']))
        cov.set_zone_setup(self.s,self.fsetup(kw=400.),EV,'T');self.assertTrue(any(b.startswith('FIRE_SIZE_MISMATCH') for b in cov.coverage_readiness(self.s)['FZ']['blockers']))
        cov.set_zone_setup(self.s,self.fsetup(kw=400.,scaling='INVERSE_SQUARE'),EV,'T');st=cov.coverage_readiness(self.s)['FZ'];self.assertEqual(st['status'],'READY');self.assertIn('INVERSE_SQUARE_FIRE_SIZE_SCALING:FZ',st['review'])
        p=self.fsetup();p['criterion_reference']='NOT SUPPLIED';cov.set_zone_setup(self.s,p,EV,'T');self.assertIn('CRITERION_REFERENCE:FZ',cov.coverage_readiness(self.s)['FZ']['blockers'])
    def test_ready_run_store_reproduce_and_stale(self):
        self.enable();self.assign_all();cov.set_zone_setup(self.s,self.fsetup(vote=2,targets={'1ooN':'0.5','2ooN':'0.9'}),EV,'T')
        g=gas_setup({'shape':'SPHERE','diameter_m':5.},100.,['POINT_GAS','OPEN_PATH'],spacing=.5,slices=(1.,));g['zone_id']='GZ';cov.set_zone_setup(self.s,g,EV,'T')
        r=readiness(self.s);self.assertEqual(r['engineering_calculation_status'],'READY',r['engineering_blockers']);self.assertEqual(r['qualification'],'ENGINEER-REVIEWED - NOT INDEPENDENTLY CERTIFIED')
        out=cov.run_all(self.s,'R1','ENGINEER_A');self.assertEqual(sorted(out),['FZ','GZ'])
        fz=out['FZ'];self.assertEqual(fz['method_version'],'FG-FLAME-GEO/1.0');self.assertEqual(fz['label'],'Engineer-reviewed results - not independently certified')
        self.assertGreater(fz['fractions']['1ooN'],fz['fractions']['2ooN']);self.assertGreater(fz['excluded_measure']['inside_obstruction'],0)
        self.assertEqual(fz['performance_targets']['2ooN']['status'],'BELOW USER TARGET')
        gz=out['GZ'];self.assertEqual(gz['method_version'],'FG-GAS-GEO/1.0');self.assertEqual(gz['detectors_considered'],['G1','O1'])
        run=cov.runs(self.s,'FZ')[0];self.assertEqual(cov.run_currency(self.s,run),'CURRENT')
        env=json.loads(run['input_json']);self.assertEqual(content_hash(env),run['input_hash']);self.assertEqual(env['scene_sha256'],get_scene(self.s).sha256)
        again,_=engineering_flame_coverage(zone={**env['zone'],'low':tuple(env['zone']['low']),'high':tuple(env['zone']['high'])},setup=env['setup'],detectors=env['detectors'],library=env['library'],scene=get_scene(self.s),excluded_component_ids=env['excluded_component_ids'])
        stored=json.loads(run['result_json']);self.assertEqual(again['fractions'],stored['fractions'])
        w.paste_detectors(self.s,[{'id':'F2','x':9.5}],'T')
        self.assertEqual(cov.run_currency(self.s,run),'STALE');self.assertEqual(cov.runs(self.s,'FZ')[0]['status'],'STALE')
        w.history(self.s,'T');self.assertEqual(cov.run_currency(self.s,run),'CURRENT')
        with self.assertRaises(CaseError):cov.run_zone(self.s,'FZ','R1-FZ','T')
        self.s.save();self.s.close();self.s=CaseSession(self.path,self.root/'r');self.assertEqual(len(cov.runs(self.s)),2)
    def test_remove_detector_removes_assignment_undoably(self):
        self.enable();self.assign_all();w.remove_detector(self.s,'G1','T');self.assertIsNone(w.row(self.s,'detector_library_assignment','G1'))
        w.history(self.s,'T');self.assertEqual(w.row(self.s,'detector_library_assignment','G1')['library_id'],'PG')
