import tempfile,unittest,json
from pathlib import Path
from fgmapping.services.case import CaseSession,create_case
from fgmapping.services.geometry import enable_geometry,set_scene
from fgmapping.services.study_schema import enable_study
from fgmapping.services import workspace as w
from fgmapping.services.mounts import set_mount
from fgmapping.services.basis import set_basis
from fgmapping.services.reporting import normalized_snapshot,write_reports,qa_reports
from fgmapping.domain.scene import synthetic_scene
class Schema3Reports(unittest.TestCase):
 def test_basis_mount_and_readiness_all_formats(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'s.fgcase','SYNTHETIC')
   with CaseSession(p,root/'r') as s:
    enable_geometry(s,'TEST_ENGINE');s.add_evidence('SYN-GEOM-01','SYNTHETIC','Synthetic','A','test','TEST_ENGINE');set_scene(s,synthetic_scene(),'TEST_ENGINE');enable_study(s,'TEST_ENGINE')
    w.detector_command(s,{'id':'D','detector_type':'FLAME','x':0,'y':0,'z':0,'evidence_id':'SYN-GEOM-01'},None,'TEST_ENGINE',create=True,place_marker=True)
    set_mount(s,'D','V101',(3,3,5),(0,0,.5),(0,-20,15),'SYN-GEOM-01','TEST_ENGINE')
    basis={'contract':'fg-study-basis/1','revision':'SYN-A','study_type':'FLAME','coordinate_reference':'SYN','target_description':'Synthetic target','fuel_or_gas':'SYNTHETIC','voting':2,'criterion_reference':'NOT SUPPLIED','target_fraction':'NOT SUPPLIED','exclusions':[],'uncertainty_reference':'NOT SUPPLIED'}
    set_basis(s,basis,'SYN-GEOM-01','TEST_ENGINE');snapshot=normalized_snapshot(s)
    self.assertEqual(snapshot['snapshot_version'],'fg-report/2');self.assertEqual(snapshot['readiness']['engineering_calculation_status'],'BLOCKED');self.assertEqual(snapshot['datasets']['mounts'][0]['component_id'],'V101')
    result=write_reports(snapshot,root/'reports');qa_reports(snapshot,root/'reports');self.assertGreater(result['record_rows'],0)
 def test_large_audit_field_is_chunked_without_losing_values(self):
  from fgmapping.services.reporting import audit_pairs
  text='Synthetic complete source value '*200
  pairs=audit_pairs({'source':text})
  self.assertGreater(len(pairs),1);self.assertEqual(''.join(value for key,value in pairs),text);self.assertTrue(all(len(value)<=1000 for key,value in pairs))
