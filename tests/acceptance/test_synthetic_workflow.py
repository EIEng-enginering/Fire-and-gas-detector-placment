from pathlib import Path
import tempfile
import unittest
from fgmapping.services.case import create_case,CaseSession
from fgmapping.engine.geometry import DemoDetector,illustrative_coverage

class SyntheticAcceptance(unittest.TestCase):
    def test_end_to_end_no_real_data(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'synthetic.fgcase'
            create_case(p,'SYNTHETIC TEST FACILITY')
            with CaseSession(p,Path(t)/'runtime') as s:
                s.add_evidence('SYN-DOC','SYNTHETIC','Created for tests','A','synthetic drawing box 1','TEST_ENGINEER')
                s.add_detector('SYN-FD-01','FLAME',0,0,0,'SYN-DOC','TEST_ENGINEER')
                s.save()
            with CaseSession(p,Path(t)/'runtime') as s:
                self.assertEqual(s.snapshot()['detectors'][0]['review_status'],'CANDIDATE')
                self.assertEqual(s.snapshot()['case']['status'],'DEVELOPMENT BUILD')
            detector=DemoDetector('SYN-FD-01',(0,0,0),(1,0,0),10,45)
            synthetic_fraction=illustrative_coverage([detector],[((3,0,0),1),((-3,0,0),1)],[],1)
            self.assertAlmostEqual(synthetic_fraction,.5)

if __name__=='__main__':unittest.main()
