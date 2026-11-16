import unittest,tempfile,csv,io,json,base64
from pathlib import Path
from dataclasses import replace
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene,get_scene
from fgmapping.services.study_schema import enable_study
from fgmapping.services import workspace as w
from fgmapping.services.preparation import apply_plan,state_hash
from fgmapping.services.bulk_import import prepare_bulk,HEADERS
from fgmapping.services.preparation_job import PreparationJob
from fgmapping.services.mounts import set_mount
from fgmapping.services.reconciliation import prepare_revision
from fgmapping.domain.scene import synthetic_scene,canonical
from fgmapping.errors import CaseError

def csv_bytes(rows):
 out=io.StringIO(newline='');wr=csv.DictWriter(out,fieldnames=HEADERS);wr.writeheader()
 for row in rows:wr.writerow({**{k:'' for k in HEADERS},**row})
 return out.getvalue().encode()
def detector(id='D',action='CREATE',x='1'):
 return {'data_class':'SYNTHETIC','action':action,'kind':'DETECTOR','id':id,'evidence_id':'SYN-GEOM-01','detector_type':'FLAME','x':x,'y':'2','z':'3','azimuth':'0','elevation':'0','roll':'0','manufacturer':'NOT SUPPLIED','model':'NOT SUPPLIED','sensitivity':'NOT SUPPLIED'}
class PreparationImports(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.path=create_case(self.root/'s.fgcase','SYNTHETIC IMPORT');self.s=CaseSession(self.path,self.root/'r');enable_geometry(self.s,'TEST_ENGINE');self.s.add_evidence('SYN-GEOM-01','SYNTHETIC','Synthetic test','A','test','TEST_ENGINE');set_scene(self.s,synthetic_scene(),'TEST_ENGINE');enable_study(self.s,'TEST_ENGINE')
 def tearDown(self):self.s.close(discard_unsaved=True);self.tmp.cleanup()
 def apply(self,p):apply_plan(self.s,p,'SYNTHETIC_TEST_REVIEWER','Synthetic reviewed values only')
 def test_preview_no_mutation_commit_one_history_and_raw_retained(self):
  raw=csv_bytes([detector(),{'data_class':'SYNTHETIC','action':'CREATE','kind':'EQUIPMENT','id':'EQ','evidence_id':'SYN-GEOM-01','x':'2','y':'3','z':'4','equipment_type':'Synthetic vessel','geometry_component_id':'V101'}]);before=state_hash(self.s);p=prepare_bulk(self.s,raw,'CSV');self.assertEqual(state_hash(self.s),before);self.apply(p)
  self.assertEqual(w.row(self.s,'detectors','D')['x'],1);self.assertEqual(w.row(self.s,'engineering_record','EQ')['kind'],'EQUIPMENT');entry=json.loads(self.s.con.execute("SELECT forward_json FROM ledger WHERE command='RETAIN_PREPARATION_SOURCE'").fetchone()[0]);self.assertEqual(base64.b64decode(entry['raw_base64']),raw)
  w.history(self.s,'TEST_ENGINE');self.assertIsNone(w.row(self.s,'detectors','D'));self.assertIsNone(w.row(self.s,'engineering_record','EQ'));w.history(self.s,'TEST_ENGINE',redo=True);self.assertIsNotNone(w.row(self.s,'detectors','D'))
 def test_duplicate_unknown_header_nonfinite_and_scope_refused(self):
  for raw in [csv_bytes([detector(),detector()]),csv_bytes([detector(x='nan')]),csv_bytes([{**detector(),'data_class':'CLIENT'}]),csv_bytes([detector()]).replace(b'data_class',b'unknown')]:
   before=state_hash(self.s)
   with self.assertRaises(CaseError):prepare_bulk(self.s,raw,'CSV')
   self.assertEqual(state_hash(self.s),before)
 def test_last_row_failure_is_atomic(self):
  with self.assertRaises(CaseError):prepare_bulk(self.s,csv_bytes([detector(),{**detector('D2'),'evidence_id':'MISSING'}]),'CSV')
  self.assertIsNone(w.row(self.s,'detectors','D'))
 def test_stale_preview_and_tampering_refused(self):
  p=prepare_bulk(self.s,csv_bytes([detector()]),'CSV')
  with self.assertRaises(CaseError):self.apply(replace(p,changes_json='[]'))
  self.s.add_evidence('EXTRA','SYNTHETIC','Other change','B','test','TEST_ENGINE')
  with self.assertRaises(CaseError):self.apply(p)
  self.assertIsNone(w.row(self.s,'detectors','D'))
 def test_xlsx_literals_and_formulas(self):
  from openpyxl import Workbook
  def workbook(formula=False):
   book=Workbook();sheet=book.active;sheet.title='Registers';sheet.append(HEADERS);r={**{k:'' for k in HEADERS},**detector()};r['x']='=1+1' if formula else 2;sheet.append([r[k] for k in HEADERS]);out=io.BytesIO();book.save(out);return out.getvalue()
  p=prepare_bulk(self.s,workbook(),'XLSX');self.apply(p);self.assertEqual(w.row(self.s,'detectors','D')['x'],2)
  with self.assertRaises(CaseError):prepare_bulk(self.s,workbook(True),'XLSX')
 def test_update_marker_and_mounted_edit_guard(self):
  w.detector_command(self.s,{**detector(),'x':1,'y':2,'z':3,'azimuth':0,'elevation':0,'roll':0},None,'TEST_ENGINE',create=True,place_marker=True);before=get_scene(self.s);self.apply(prepare_bulk(self.s,csv_bytes([detector(action='UPDATE',x='4')]),'CSV'));after=get_scene(self.s);a=next(c for c in before.components if c.id=='D');b=next(c for c in after.components if c.id=='D');self.assertAlmostEqual(b.mesh.vertices[0][0]-a.mesh.vertices[0][0],3)
  set_mount(self.s,'D','V101',[1,2,3],[0,0,0],[0,0,0],'SYN-GEOM-01','TEST_ENGINE')
  with self.assertRaises(CaseError):prepare_bulk(self.s,csv_bytes([detector(action='UPDATE')]),'CSV')
 def test_worker_and_cancellation_leave_live_case_unchanged(self):
  raw=csv_bytes([detector()]);before=state_hash(self.s);p=PreparationJob(self.s,raw,'CSV','BULK_REGISTER').result();self.assertEqual(p,prepare_bulk(self.s,raw,'CSV'));self.assertEqual(state_hash(self.s),before)
  job=PreparationJob(self.s,raw,'CSV','BULK_REGISTER');job.cancel();self.assertIsNotNone(job.process.poll());self.assertEqual(state_hash(self.s),before)
 def revision(self,action='FOLLOW_COMPONENT',remove=False):
  scene=get_scene(self.s);p=scene.to_dict();p['components']=[c for c in p['components'] if c['semantic']!='DETECTOR' and not(remove and c['id']=='V101')]
  for c in p['components']:
   if c['id']=='V101':c['mesh']['vertices']=[[x+2,y,z] for x,y,z in c['mesh']['vertices']]
  p['source_revision']='SYNTHETIC REV B';return canonical({'contract':'fg-geometry-revision/1','data_class':'SYNTHETIC','scene':p,'mount_decisions':[{'detector_id':'D','action':action,'target_component_id':'V101' if action=='FOLLOW_COMPONENT' else '', 'reason':'Explicit synthetic revision decision','evidence_id':'SYN-GEOM-01'}]}).encode()
 def mounted(self):
  w.detector_command(self.s,{**detector(),'x':1,'y':2,'z':3,'azimuth':0,'elevation':0,'roll':0},None,'TEST_ENGINE',create=True,place_marker=True);set_mount(self.s,'D','V101',[1,2,3],[0,0,0],[0,0,0],'SYN-GEOM-01','TEST_ENGINE')
 def test_revision_follow_recalculates_frame_pose_and_history(self):
  self.mounted();p=json.loads(self.revision());p['scene']['frames'][0]['matrix'][0][3]+=2;raw=canonical(p).encode();before=get_scene(self.s).sha256;plan=prepare_revision(self.s,raw);self.assertEqual(w.row(self.s,'detectors','D')['x'],1);self.apply(plan);self.assertEqual(w.row(self.s,'detectors','D')['x'],3)
  w.history(self.s,'TEST_ENGINE');self.assertEqual(w.row(self.s,'detectors','D')['x'],1);self.assertEqual(get_scene(self.s).sha256,before);w.history(self.s,'TEST_ENGINE',redo=True);self.assertEqual(w.row(self.s,'detectors','D')['x'],3)
 def test_revision_missing_component_explicit_detach(self):
  self.mounted();self.apply(prepare_revision(self.s,self.revision('KEEP_WORLD_DETACH',True)));self.assertIsNone(w.row(self.s,'detector_mount','D'));self.assertEqual(w.row(self.s,'detectors','D')['x'],1)
 def test_revision_missing_decision_or_reference_refused(self):
  self.mounted();p=json.loads(self.revision());p['mount_decisions']=[]
  with self.assertRaises(CaseError):prepare_revision(self.s,canonical(p).encode())
  w.record_command(self.s,'EQ','EQUIPMENT',{'geometry_component_id':'V101'},'SYN-GEOM-01','TEST_ENGINE',create=True)
  with self.assertRaises(CaseError):prepare_revision(self.s,self.revision('KEEP_WORLD_DETACH',True))
 def test_revision_unit_change_needs_manual_anchor_redeclaration(self):
  self.mounted();p=json.loads(self.revision());p['scene']['frames'][0]['units']='mm'
  with self.assertRaises(CaseError):prepare_revision(self.s,canonical(p).encode())
