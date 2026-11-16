import tempfile,unittest
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene,get_scene,compensate_scene
from fgmapping.services.registers import edit_detector,detector_history
from fgmapping.domain.scene import synthetic_scene
from fgmapping.errors import CaseError
class LinkedDetectorHistory(unittest.TestCase):
    def test_move_undo_redo_reopen_and_scene_history_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=create_case(root/'s.fgcase','SYNTHETIC')
            with CaseSession(p,root/'runtime') as s:
                enable_geometry(s,'TEST_ENGINE');s.add_evidence('SYN-GEOM-01','SYNTHETIC','Synthetic','A','test','TEST_ENGINE')
                s.add_detector('FD101','FLAME',0,0,3,'SYN-GEOM-01','TEST_ENGINE');set_scene(s,synthetic_scene(),'TEST_ENGINE')
                before=get_scene(s);edit_detector(s,'FD101',(5,2,4),(30,20,0),'TEST_ENGINE');moved=get_scene(s)
                c=next(c for c in moved.components if c.id=='FD101');self.assertEqual(c.mesh.vertices[0],(5,2,4))
                with self.assertRaises(CaseError):compensate_scene(s,'TEST_ENGINE')
                detector_history(s,'TEST_ENGINE');self.assertEqual(get_scene(s),before);self.assertEqual(s.detectors()[0][2:5],(0,0,3));s.save()
            with CaseSession(p,root/'runtime') as s:
                detector_history(s,'TEST_ENGINE',True);self.assertEqual(get_scene(s),moved);self.assertEqual(s.detectors()[0][2:5],(5,2,4));s.save()
    def test_empty_actor_preserves_geometry_and_detector(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=create_case(root/'s.fgcase','SYNTHETIC')
            with CaseSession(p,root/'runtime') as s:
                enable_geometry(s,'TEST_ENGINE');s.add_evidence('SYN-GEOM-01','SYNTHETIC','Synthetic','A','test','TEST_ENGINE')
                s.add_detector('FD101','FLAME',0,0,3,'SYN-GEOM-01','TEST_ENGINE');set_scene(s,synthetic_scene(),'TEST_ENGINE')
                with self.assertRaises(CaseError):edit_detector(s,'FD101',(5,2,4),(30,20,0),'')
                self.assertEqual(get_scene(s),synthetic_scene());self.assertEqual(s.detectors()[0][2:5],(0,0,3))
