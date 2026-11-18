import json,tempfile,unittest
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry
from fgmapping.services.calculations import run_synthetic
class Fingerprint(unittest.TestCase):
 def test_run_records_exact_implementation_and_input_revision(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'s.fgcase','SYNTHETIC')
   with CaseSession(p,root/'r') as s:
    enable_geometry(s,'TEST_ENGINE');run_synthetic(s,'RUN','SYNTHETIC_VOTES/1',{'rows':[['A',1,[True]]],'required_votes':1},'TEST_ENGINE')
    payload=json.loads(s.con.execute('SELECT input_json FROM calculation_run').fetchone()[0]);self.assertEqual(payload['software_version'],'0.7.0a1');self.assertEqual(len(payload['implementation_sha256']),64);self.assertIn('engine/detection.py',payload['implementation_files'])
