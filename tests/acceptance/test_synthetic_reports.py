import tempfile,unittest
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene
from fgmapping.domain.scene import synthetic_scene
from fgmapping.services.reporting import normalized_snapshot,write_reports,qa_reports
class Reports(unittest.TestCase):
    def test_all_formats_and_corruption_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);path=create_case(root/'syn.fgcase','SYNTHETIC')
            with CaseSession(path,root/'runtime') as s:
                enable_geometry(s,'TEST_ENGINE');s.add_evidence('SYN-GEOM-01','SYNTHETIC','Generated','A','test','TEST_ENGINE')
                s.add_detector('SYN-FD','FLAME',1,2,3,'SYN-GEOM-01','TEST_ENGINE');set_scene(s,synthetic_scene(),'TEST_ENGINE')
                snap=normalized_snapshot(s);result=write_reports(snap,root/'reports');self.assertEqual(result['record_rows'],15)
                with self.assertRaises(ValueError):write_reports(snap,root/'reports')
                from openpyxl import load_workbook
                p=root/'reports/Registers.xlsx';wb=load_workbook(p);wb['detectors']['C2']=999;wb.save(p)
                with self.assertRaises(ValueError):qa_reports(snap,root/'reports')
