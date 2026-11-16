import tempfile,unittest
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene
from fgmapping.services.geometry_inspection import GeometryJob,commit_inspection
from fgmapping.domain.scene import synthetic_scene
from fgmapping.errors import CaseError
class InspectionWorker(unittest.TestCase):
 def test_worker_commit_and_stale_refusal(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'s.fgcase','SYNTHETIC')
   with CaseSession(p,root/'r') as s:
    enable_geometry(s,'TEST_ENGINE');s.add_evidence('SYN-GEOM-01','SYNTHETIC','Synthetic','A','test','TEST_ENGINE');scene=synthetic_scene();set_scene(s,scene,'TEST_ENGINE')
    t={'center_m':[8,3,3],'u':[0,1,0],'v':[0,0,1],'width_m':2,'height_m':2,'nx':4,'ny':4}
    job=GeometryJob(scene,(1,1,3),[],t,1e-9);r=job.result();commit_inspection(s,'G1',job.inputs,r,'TEST_ENGINE');self.assertEqual(r['visibility_fraction'],1)
    s.con.execute("UPDATE geometry_scene SET sha256='bad'")
    with self.assertRaises(CaseError):commit_inspection(s,'G2',job.inputs,r,'TEST_ENGINE')
 def test_worker_cancel(self):
  scene=synthetic_scene();t={'center_m':[8,3,3],'u':[0,1,0],'v':[0,0,1],'width_m':2,'height_m':2,'nx':4,'ny':4};job=GeometryJob(scene,(1,1,3),[],t,1e-9);job.cancel();self.assertIsNotNone(job.process.poll())
