import tempfile,unittest
from pathlib import Path
from fgmapping.services.case import CaseSession,create_case
from fgmapping.services.geometry import enable_geometry,set_scene,get_scene
from fgmapping.services.mesh_import import parse_mesh
from fgmapping.domain.scene import Frame,synthetic_scene
from fgmapping.services.import_review import ImportProposal
from fgmapping.services.workspace import history,record_command
from fgmapping.services.findings import study_findings
from fgmapping.errors import CaseError
class ImportReview(unittest.TestCase):
 def test_append_replace_history_and_source_retention(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'s.fgcase','SYNTHETIC')
   with CaseSession(p,root/'r') as s:
    enable_geometry(s,'TEST_ENGINE');s.add_evidence('SYN-GEOM-01','SYNTHETIC','Synthetic','A','test','TEST_ENGINE');set_scene(s,synthetic_scene(),'TEST_ENGINE')
    record_command(s,'SYN-EQ','EQUIPMENT',{'geometry_component_id':'V101'},'SYN-GEOM-01','TEST_ENGINE',create=True)
    raw=b'v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3';proposal=ImportProposal.prepare(raw,'.obj',parse_mesh(raw,'.obj',Frame('F','m','SYN')))
    proposal.apply(s,'TEST_ENGINE','APPEND');self.assertEqual(len(get_scene(s).components),14)
    with self.assertRaises(CaseError):proposal.apply(s,'TEST_ENGINE','APPEND')
    history(s,'TEST_ENGINE');self.assertEqual(len(get_scene(s).components),13)
    self.assertEqual(s.con.execute('SELECT count(*) FROM geometry_attachment').fetchone()[0],1)
    proposal.apply(s,'TEST_ENGINE','REPLACE');self.assertEqual(len(get_scene(s).components),1);self.assertTrue(any(f['id']=='ORPHAN-SYN-EQ' for f in study_findings(s)))
    history(s,'TEST_ENGINE');self.assertEqual(len(get_scene(s).components),13)
 def test_refuse_modified_raw(self):
  raw=b'v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3';result=parse_mesh(raw,'.obj',Frame('F','m','SYN'))
  with self.assertRaises(CaseError):ImportProposal.prepare(raw+b'x','.obj',result)
