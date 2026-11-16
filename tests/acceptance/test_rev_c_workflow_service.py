import tempfile,unittest,json
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry
from fgmapping.services.workspace import detector_command,synthetic_evidence,record_command,paste_detectors,history
from fgmapping.services.calculations import run_synthetic
from fgmapping.services.reporting import normalized_snapshot,qa_reports
from fgmapping.services.report_job import ReportJob
class RevCStudy(unittest.TestCase):
 def test_connected_study_save_reopen_report_worker(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'s.fgcase','SYNTHETIC CONNECTED STUDY')
   with CaseSession(p,root/'r') as s:
    enable_geometry(s,'TEST_ENGINE')
    detector_command(s,{'id':'SYN-FD','detector_type':'FLAME','x':1,'y':2,'z':3,'evidence_id':'SYN-E'},synthetic_evidence('SYN-E','Generated test source','A','test'),'TEST_ENGINE',create=True,place_marker=True)
    record_command(s,'SYN-ZONE','FIRE_ZONE',{'low':[0,0,0],'high':[10,10,5],'units':'m','criteria':'NOT SUPPLIED'},'SYN-E','TEST_ENGINE',create=True)
    run_synthetic(s,'SYN-RUN','SYNTHETIC_UNIFORM_PATH/1',{'low':[0,0,0],'high':[2,3,4],'ppm':100,'basis':'SYNTHETIC','start':[-5,1,1],'end':[5,1,1]},'TEST_ENGINE')
    paste_detectors(s,[{'id':'SYN-FD','x':4}],'TEST_ENGINE');history(s,'TEST_ENGINE');s.save()
   with CaseSession(p,root/'other_runtime') as s:
    self.assertEqual(s.detectors()[0][2],1);snap=normalized_snapshot(s)
    self.assertTrue(snap['datasets']['findings']);result=ReportJob(snap,root/'reports').result();self.assertEqual(result['record_rows'],5);self.assertGreater(result['finding_rows'],0);qa_reports(snap,root/'reports')
    self.assertEqual(json.loads((root/'reports/QA.json').read_text())['status'],'PASS')
 def test_report_cancel_reaps_child(self):
  snapshot={'data_class':'SYNTHETIC'}
  with tempfile.TemporaryDirectory() as tmp:
   job=ReportJob(snapshot,Path(tmp)/'reports');job.cancel();self.assertIsNotNone(job.process.poll())
