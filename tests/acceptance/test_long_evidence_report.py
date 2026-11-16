import tempfile,unittest
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry
from fgmapping.services.reporting import normalized_snapshot,write_reports,qa_reports
class LongEvidenceReport(unittest.TestCase):
 def test_long_source_field_all_formats_no_loss(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'s.fgcase','SYNTHETIC LONG EVIDENCE')
   with CaseSession(p,root/'r') as s:
    enable_geometry(s,'TEST_ENGINE');s.add_evidence('E','SYNTHETIC','Synthetic complete source evidence '*220,'A','Synthetic source','TEST_ENGINE');snap=normalized_snapshot(s)
    write_reports(snap,root/'reports');qa_reports(snap,root/'reports')
    from pypdf import PdfReader
    embedded=[]
    for page in PdfReader(root/'reports/Study.pdf').pages:
     for resource in page['/Resources']['/Font'].values():
      font=resource.get_object()
      if 'VeraSans' in str(font.get('/BaseFont','')):
       descriptor=font['/FontDescriptor'].get_object();self.assertIn('/FontFile2',descriptor);embedded.append(font['/BaseFont'])
    self.assertTrue(embedded,'Report text must use embedded fonts')
