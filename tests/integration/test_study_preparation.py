import json,tempfile,unittest,sqlite3
from dataclasses import replace
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene,get_scene
from fgmapping.services.study_schema import enable_study
from fgmapping.services import workspace as w
from fgmapping.services.mounts import set_mount,detach_mount,mount_status
from fgmapping.services.basis import set_basis,readiness
from fgmapping.services.performance import import_dataset,link_dataset,review_draft
from fgmapping.domain.scene import synthetic_scene
from fgmapping.engine.detection import engineering_flame_coverage,EngineeringUnavailable
from fgmapping.errors import CaseError
class StudyPreparation(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.path=create_case(self.root/'s.fgcase','SYNTHETIC')
  self.s=CaseSession(self.path,self.root/'r');self.addCleanup(lambda:self.s.close(discard_unsaved=True));enable_geometry(self.s,'TEST_ENGINE')
  self.s.add_evidence('SYN-GEOM-01','SYNTHETIC','Generated layout','A','synthetic scene','TEST_ENGINE');set_scene(self.s,synthetic_scene(),'TEST_ENGINE');enable_study(self.s,'TEST_ENGINE')
  w.detector_command(self.s,{'id':'D','detector_type':'FLAME','x':0,'y':0,'z':0,'evidence_id':'SYN-GEOM-01','manufacturer':'SYNTHETIC_VENDOR','model':'SYNTHETIC_MODEL','sensitivity':'TEST'},None,'TEST_ENGINE',create=True,place_marker=True)
 def basis(self):return {'contract':'fg-study-basis/1','revision':'SYN-A','study_type':'FLAME','coordinate_reference':'SYN LOCAL','target_description':'Synthetic target only','fuel_or_gas':'SYNTHETIC','voting':1,'criterion_reference':'SYNTHETIC test criterion, not a project target','target_fraction':'0.5','exclusions':[],'uncertainty_reference':'Synthetic test basis'}
 def dataset(self):return {'contract':'fg-performance-preparation/1','data_class':'SYNTHETIC','manufacturer':'SYNTHETIC_VENDOR','model':'SYNTHETIC_MODEL','revision':'SYN-A','sensitivity':'TEST','source':{'title':'Generated schema fixture, not vendor data','revision':'A','locator':'Synthetic table','sha256':'0'*64,'licence_basis':'SYNTHETIC GENERATED'},'conditions':{'fuel_or_gas':'SYNTHETIC','target_description':'Synthetic schema-only target','environment_reference':'Synthetic test','method_scope':'PREPARATION ONLY / NO ENGINEERING RESPONSE'},'units':{'distance':'m','angle':'deg','response_time':'s'},'samples':[{'azimuth_deg':0,'elevation_deg':0,'range_m':1,'response_time_s':1,'source_locator':'Synthetic row 1'}]}
 def test_upgrade_backup_and_reopen(self):
  self.assertEqual(self.s.con.execute('PRAGMA user_version').fetchone()[0],3);self.assertTrue(list((self.root/'r/Backups').glob('*pre_study3*')));self.s.save();self.s.close();self.s=CaseSession(self.path,self.root/'r');self.assertEqual(self.s.con.execute('PRAGMA user_version').fetchone()[0],3)
 def test_mount_edit_detach_and_undo(self):
  p=set_mount(self.s,'D','V101',(3,3,5),(0,0,.5),(0,-20,15),'SYN-GEOM-01','TEST_ENGINE');self.assertEqual(p['position'],(3,3,5.5))
  with self.assertRaises(CaseError):w.paste_detectors(self.s,[{'id':'D','x':5}],'TEST_ENGINE')
  detach_mount(self.s,'D','TEST_ENGINE');self.assertIsNone(w.row(self.s,'detector_mount','D'));w.history(self.s,'TEST_ENGINE');self.assertIsNotNone(w.row(self.s,'detector_mount','D'))
  w.history(self.s,'TEST_ENGINE');self.assertIsNone(w.row(self.s,'detector_mount','D'));self.assertEqual(w.row(self.s,'detectors','D')['x'],0)
 def test_mount_source_missing_or_stale_is_blocked(self):
  set_mount(self.s,'D','V101',(3,3,5),(0,0,0),(0,0,0),'SYN-GEOM-01','TEST_ENGINE');scene=get_scene(self.s);changed=replace(scene,components=tuple(c for c in scene.components if c.id!='V101'));set_scene(self.s,changed,'TEST_ENGINE')
  self.assertIn('STALE_OR_MISSING_MOUNT:D',readiness(self.s)['blocking'])
 def test_basis_targets_never_defaulted(self):
  p=self.basis();p['target_fraction']='NOT SUPPLIED';set_basis(self.s,p,'SYN-GEOM-01','TEST_ENGINE');self.assertIn('TARGET_FRACTION',readiness(self.s)['missing'])
 def test_input_complete_still_engineering_blocked(self):
  import_dataset(self.s,'SYN-P',json.dumps(self.dataset()).encode(),'TEST_ENGINE');link_dataset(self.s,'D','SYN-P','SYN-GEOM-01','TEST_ENGINE');set_basis(self.s,self.basis(),'SYN-GEOM-01','TEST_ENGINE')
  r=readiness(self.s);self.assertEqual(r['input_status'],'INPUTS_PRESENT');self.assertEqual(r['engineering_calculation_status'],'BLOCKED')
  with self.assertRaises(EngineeringUnavailable):engineering_flame_coverage(performance=self.dataset(),basis=self.basis())
 def test_dataset_revision_is_immutable_and_source_preserved(self):
  raw=json.dumps(self.dataset()).encode();import_dataset(self.s,'SYN-P',raw,'TEST_ENGINE');self.assertEqual(w.row(self.s,'performance_dataset','SYN-P')['raw_text'],raw.decode())
  with self.assertRaises(CaseError):import_dataset(self.s,'SYN-P',raw,'TEST_ENGINE')
 def test_mismatch_and_project_basis_import_refused(self):
  p=self.dataset();p['model']='DIFFERENT';import_dataset(self.s,'SYN-P',json.dumps(p).encode(),'TEST_ENGINE')
  with self.assertRaises(CaseError):link_dataset(self.s,'D','SYN-P','SYN-GEOM-01','TEST_ENGINE')
  p=self.dataset();p['data_class']='PROJECT_BASIS'
  with self.assertRaises(ValueError):import_dataset(self.s,'REAL-NOT-AUTHORISED',json.dumps(p).encode(),'TEST_ENGINE')
 def test_no_approval_review_state(self):
  set_basis(self.s,self.basis(),'SYN-GEOM-01','TEST_ENGINE')
  with self.assertRaises(CaseError):review_draft(self.s,'R','BASIS','STUDY','APPROVED','TEST_REVIEWER','test','SYN-GEOM-01')
  review_draft(self.s,'R','BASIS','STUDY','NEEDS_INFORMATION','TEST_REVIEWER','No actual engineering basis supplied','SYN-GEOM-01');self.assertEqual(readiness(self.s)['engineering_calculation_status'],'BLOCKED')
 def test_missing_mount_actor_rolls_back(self):
  with self.assertRaises(CaseError):set_mount(self.s,'D','V101',(3,3,5),(0,0,0),(0,0,0),'SYN-GEOM-01','')
  self.assertIsNone(w.row(self.s,'detector_mount','D'));self.assertEqual(w.row(self.s,'detectors','D')['x'],0)
 def test_corrupt_performance_blocks_readiness(self):
  import_dataset(self.s,'SYN-P',json.dumps(self.dataset()).encode(),'TEST_ENGINE');link_dataset(self.s,'D','SYN-P','SYN-GEOM-01','TEST_ENGINE')
  with self.s.con:self.s.con.execute("UPDATE performance_dataset SET import_sha256='bad'")
  self.assertIn('PERFORMANCE_INTEGRITY:D',readiness(self.s)['blocking'])
 def test_remount_moves_between_components_and_undo_restores(self):
  set_mount(self.s,'D','V101',(3,3,5),(0,0,0),(10,-20,0),'SYN-GEOM-01','TEST_ENGINE');before=w.row(self.s,'detectors','D')
  set_mount(self.s,'D','V102',(12,6,4),(0,0,.2),(30,-10,5),'SYN-GEOM-01','TEST_ENGINE');self.assertEqual(w.row(self.s,'detector_mount','D')['component_id'],'V102')
  w.history(self.s,'TEST_ENGINE');self.assertEqual(w.row(self.s,'detectors','D'),before);self.assertEqual(w.row(self.s,'detector_mount','D')['component_id'],'V101')
 def test_voting_infeasibility_is_input_blocker(self):
  p=self.basis();p['voting']=2;set_basis(self.s,p,'SYN-GEOM-01','TEST_ENGINE');self.assertIn('VOTING_EXCEEDS_ELIGIBLE_DETECTORS',readiness(self.s)['blocking'])
 def test_workspace_cannot_promote_preparation_entity(self):
  set_basis(self.s,self.basis(),'SYN-GEOM-01','TEST_ENGINE');before=w.row(self.s,'study_basis','STUDY')
  with self.assertRaises(CaseError):w.execute(self.s,[w.change(self.s,'study_basis','STUDY',{**before,'status':'APPROVED'})],'TEST_ENGINE','Invalid attempted promotion')
  self.assertEqual(w.row(self.s,'study_basis','STUDY')['status'],'CANDIDATE')

 def test_source_row_lookup_never_interpolates_or_substitutes_conditions(self):
  from fgmapping.domain.performance import exact_source_sample
  p=self.dataset();r=exact_source_sample(p,0,0,1,p['conditions']);self.assertEqual(r['sample']['response_time_s'],1);self.assertEqual(r['qualification'],'UNVERIFIED')
  with self.assertRaises(ValueError):exact_source_sample(p,0,0,1.5,p['conditions'])
  with self.assertRaises(ValueError):exact_source_sample(p,0,0,1,{**p['conditions'],'fuel_or_gas':'DIFFERENT'})
 def test_stored_status_anomaly_blocks_readiness(self):
  set_basis(self.s,self.basis(),'SYN-GEOM-01','TEST_ENGINE')
  with self.s.con:self.s.con.execute("UPDATE study_basis SET status='APPROVED'")
  self.assertIn('UNEXPECTED_PREPARATION_STATUS:study_basis',readiness(self.s)['blocking'])
