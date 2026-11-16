import unittest,tempfile
from pathlib import Path
from fgmapping.services.case import CaseSession,create_case
from fgmapping.services.geometry import enable_geometry
from fgmapping.services.reporting import normalized_snapshot
from fgmapping.services.comparison import compare_snapshots
from fgmapping.services import workspace as w
class SnapshotRevision(unittest.TestCase):
 def test_stable_field_diff_and_cross_case_refusal(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'s.fgcase','SYNTHETIC')
   with CaseSession(p,root/'r') as s:
    enable_geometry(s,'TEST_ENGINE');w.detector_command(s,{'id':'D','detector_type':'FLAME','x':0,'y':0,'z':0,'evidence_id':'E'},w.synthetic_evidence('E','Synthetic','A','test'),'TEST_ENGINE',create=True)
    old=normalized_snapshot(s);w.paste_detectors(s,[{'id':'D','x':4}],'TEST_ENGINE');new=normalized_snapshot(s);r=compare_snapshots(old,new)
    self.assertTrue(any(c['object_id']=='D' and c['field']=='x' and c['before']==0 and c['after']==4 for c in r['changes']))
    new['case']['case_uuid']='DIFFERENT'
    with self.assertRaises(ValueError):compare_snapshots(old,new)
