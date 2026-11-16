import unittest,tempfile,io,csv,json,base64
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry
from fgmapping.services.bulk_import import HEADERS,prepare_bulk
from fgmapping.services.preparation import apply_plan
from fgmapping.services.reporting import normalized_snapshot,write_reports,qa_reports
class PreparationReports(unittest.TestCase):
 def test_import_history_and_raw_source_all_formats_and_undo(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'s.fgcase','SYNTHETIC REV E REPORT')
   with CaseSession(p,root/'r') as s:
    enable_geometry(s,'TEST_ENGINE');s.add_evidence('E','SYNTHETIC','Synthetic evidence','A','fixture','TEST_ENGINE');out=io.StringIO();wr=csv.DictWriter(out,fieldnames=HEADERS);wr.writeheader();wr.writerow({**{k:'' for k in HEADERS},'data_class':'SYNTHETIC','action':'CREATE','kind':'DETECTOR','id':'=SYNTHETIC_LITERAL','evidence_id':'E','detector_type':'FLAME','x':'1','y':'2','z':'3','azimuth':'0','elevation':'0','roll':'0'});raw=out.getvalue().encode();apply_plan(s,prepare_bulk(s,raw,'CSV'),'SYNTHETIC_REVIEWER','Synthetic source reviewed');snap=normalized_snapshot(s)
    self.assertEqual(base64.b64decode(snap['preparation_source_assets'][0]['raw_base64']),raw);self.assertEqual(snap['datasets']['source_preparation_history'][0]['register_rows'],1);write_reports(snap,root/'output');qa_reports(snap,root/'output')
    from openpyxl import load_workbook
    wb=load_workbook(root/'output/Registers.xlsx',data_only=False)
    try:
     matching=[c for sheet in wb for row in sheet for c in row if c.value=='=SYNTHETIC_LITERAL'];self.assertTrue(matching);self.assertTrue(all(c.data_type=='s' for c in matching))
    finally:wb.close()
    from fgmapping.services import workspace as w
    w.history(s,'TEST_ENGINE');after=normalized_snapshot(s);self.assertFalse(after['datasets']['detectors']);self.assertTrue(after['datasets']['source_preparation_history'])
