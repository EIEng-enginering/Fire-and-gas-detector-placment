import json,tempfile,unittest,sqlite3
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene,get_scene
from fgmapping.services.workspace import *
from fgmapping.domain.scene import synthetic_scene
class Workspace(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.path=create_case(self.root/'s.fgcase','SYNTHETIC')
  self.s=CaseSession(self.path,self.root/'runtime');self.addCleanup(lambda:self.s.close(discard_unsaved=True));enable_geometry(self.s,'TEST_ENGINE')
 def vals(self,id='SYN-D'):return {'id':id,'detector_type':'FLAME','x':1,'y':2,'z':3,'evidence_id':'SYN-E','azimuth':45,'elevation':10,'roll':0}
 def add(self,marker=False):detector_command(self.s,self.vals(),synthetic_evidence('SYN-E','Synthetic source','A','test'),'TEST_ENGINE',create=True,place_marker=marker)
 def test_add_evidence_detector_geometry_atomic_undo_redo(self):
  self.add(True);self.assertEqual(len(self.s.detectors()),1);self.assertIsNotNone(get_scene(self.s))
  history(self.s,'TEST_ENGINE');self.assertEqual(self.s.detectors(),[]);self.assertIsNone(row(self.s,'evidence','SYN-E'));self.assertIsNone(get_scene(self.s))
  history(self.s,'TEST_ENGINE',True);self.assertEqual(len(self.s.detectors()),1)
 def test_missing_actor_rolls_back_every_entity(self):
  with self.assertRaises(CaseError):detector_command(self.s,self.vals(),synthetic_evidence('SYN-E','Synthetic','A','test'),'',create=True,place_marker=True)
  self.assertIsNone(row(self.s,'evidence','SYN-E'));self.assertEqual(self.s.detectors(),[]);self.assertIsNone(get_scene(self.s))
 def test_duplicate_does_not_leave_orphan_evidence(self):
  self.add();v={**self.vals(),'evidence_id':'OTHER'}
  with self.assertRaises(CaseError):detector_command(self.s,v,synthetic_evidence('OTHER','Synthetic','A','test'),'TEST_ENGINE',create=True)
  self.assertIsNone(row(self.s,'evidence','OTHER'))
 def test_record_edit_remove_undo(self):
  self.add();record_command(self.s,'ZONE','FIRE_ZONE',{'low':[0,0,0],'high':[2,3,4],'units':'m'},'SYN-E','TEST_ENGINE',create=True)
  remove_record(self.s,'ZONE','TEST_ENGINE');self.assertIsNone(row(self.s,'engineering_record','ZONE'));history(self.s,'TEST_ENGINE');self.assertIsNotNone(row(self.s,'engineering_record','ZONE'))
 def test_record_invalid_bounds_no_change(self):
  self.add()
  with self.assertRaises(CaseError):record_command(self.s,'ZONE','FIRE_ZONE',{'low':[0,0,0],'high':[0,1,1],'units':'m'},'SYN-E','TEST_ENGINE',create=True)
  self.assertIsNone(row(self.s,'engineering_record','ZONE'))
 def test_undo_persists_across_reopen(self):
  self.add();self.s.save();self.s.close();self.s=CaseSession(self.path,self.root/'runtime');history(self.s,'TEST_ENGINE');self.assertEqual(self.s.detectors(),[])
 def test_redo_invalidated_by_new_edit(self):
  self.add();history(self.s,'TEST_ENGINE');self.add()
  with self.assertRaises(CaseError):history(self.s,'TEST_ENGINE',True)
 def test_foreign_edit_conflict_no_overwrite(self):
  self.add()
  with self.s.con:self.s.con.execute("UPDATE detectors SET x=999")
  with self.assertRaises(CaseError):history(self.s,'TEST_ENGINE')
  self.assertEqual(self.s.detectors()[0][2],999)
 def test_edit_marker_moves_and_undo_restores(self):
  self.add(True);before=get_scene(self.s);v={**self.vals(),'x':8};detector_command(self.s,v,None,'TEST_ENGINE',place_marker=True)
  self.assertEqual(get_scene(self.s).components[0].mesh.vertices[0],(8,2,3));history(self.s,'TEST_ENGINE');self.assertEqual(get_scene(self.s),before)
 def test_multirow_paste_is_atomic(self):
  self.add();detector_command(self.s,self.vals('SYN-B'),None,'TEST_ENGINE',create=True)
  with self.assertRaises(ValueError):paste_detectors(self.s,[{'id':'SYN-D','x':7},{'id':'SYN-B','x':float('nan')}],'TEST_ENGINE')
  self.assertEqual(row(self.s,'detectors','SYN-D')['x'],1)
  paste_detectors(self.s,[{'id':'SYN-D','x':7},{'id':'SYN-B','x':9}],'TEST_ENGINE');history(self.s,'TEST_ENGINE');self.assertEqual(row(self.s,'detectors','SYN-D')['x'],1)

 def test_second_marker_and_bulk_move_undo(self):
  self.add(True);detector_command(self.s,self.vals('SYN-B'),None,'TEST_ENGINE',create=True,place_marker=True)
  old=get_scene(self.s);self.assertEqual(len(old.components),2)
  paste_detectors(self.s,[{'id':'SYN-D','x':10},{'id':'SYN-B','y':8}],'TEST_ENGINE')
  moved={c.id:c for c in get_scene(self.s).components};self.assertEqual(moved['SYN-D'].mesh.vertices[0],(10,2,3));self.assertEqual(moved['SYN-B'].mesh.vertices[0],(1,8,3))
  history(self.s,'TEST_ENGINE');self.assertEqual(get_scene(self.s),old)

 def test_detector_remove_restores_details_marker_and_keeps_evidence(self):
  self.add(True);before=get_scene(self.s);remove_detector(self.s,'SYN-D','TEST_ENGINE')
  self.assertEqual(self.s.detectors(),[]);self.assertIsNotNone(row(self.s,'evidence','SYN-E'))
  self.assertEqual(len(get_scene(self.s).components),0);history(self.s,'TEST_ENGINE');self.assertEqual(get_scene(self.s),before);self.assertEqual(len(self.s.detectors()),1)
 def test_referenced_detector_removal_refused(self):
  self.add(True);record_command(self.s,'EQ','EQUIPMENT',{'geometry_component_id':'SYN-D'},'SYN-E','TEST_ENGINE',create=True)
  with self.assertRaises(CaseError):remove_detector(self.s,'SYN-D','TEST_ENGINE')
  self.assertEqual(len(self.s.detectors()),1)
