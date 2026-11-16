import tempfile,unittest,sqlite3
from pathlib import Path
from unittest.mock import patch
from fgmapping.services.case import create_case,CaseSession,digest
from fgmapping.services.recovery import restore_as_new,inspect_backup
from fgmapping.errors import CaseError
import fgmapping.services.recovery as module
class RecoveryFaults(unittest.TestCase):
 def test_restore_concurrent_destination_never_overwritten(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=create_case(root/'source.fgcase','SYNTHETIC SOURCE');before=digest(source);target=root/'new.fgcase';original=module.os.link
   def race(src,dst):target.write_bytes(b'SYNTHETIC CONCURRENT OWNER');return original(src,dst)
   with patch.object(module.os,'link',race):
    with self.assertRaises(CaseError):restore_as_new(source,target,'TEST_ENGINE')
   self.assertEqual(target.read_bytes(),b'SYNTHETIC CONCURRENT OWNER');self.assertEqual(digest(source),before);self.assertFalse(list(root.glob('.fg_restore_*')))
 def test_restore_copy_corruption_refused(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=create_case(root/'source.fgcase','SYNTHETIC SOURCE');before=digest(source);copy=module.shutil.copyfile
   def corrupt(src,dst):copy(src,dst);Path(dst).write_bytes(b'SYNTHETIC CORRUPTION')
   with patch.object(module.shutil,'copyfile',corrupt):
    with self.assertRaises(CaseError):restore_as_new(source,root/'new.fgcase','TEST_ENGINE')
   self.assertEqual(digest(source),before);self.assertFalse((root/'new.fgcase').exists());self.assertFalse(list(root.glob('.fg_restore_*')))
 def test_fsync_failure_before_install_retains_source_and_no_target(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=create_case(root/'source.fgcase','SYNTHETIC SOURCE');before=digest(source)
   with patch.object(module.os,'fsync',side_effect=OSError('Synthetic injected fsync failure')):
    with self.assertRaises(OSError):restore_as_new(source,root/'new.fgcase','TEST_ENGINE')
   self.assertEqual(digest(source),before);self.assertFalse((root/'new.fgcase').exists());self.assertFalse(list(root.glob('.fg_restore_*')))
 def test_failure_after_install_leaves_identifiable_valid_copy(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=create_case(root/'source.fgcase','SYNTHETIC SOURCE');before=digest(source);target=root/'new.fgcase'
   with patch.object(module,'fsync_directory',side_effect=OSError('Synthetic injected post-install failure')):
    with self.assertRaises(OSError):restore_as_new(source,target,'TEST_ENGINE')
   self.assertEqual(digest(source),before);self.assertEqual(inspect_backup(target)['name'],'SYNTHETIC SOURCE');self.assertFalse(list(root.glob('.fg_restore_*')))
 def test_cancel_removes_only_job_token_and_preserves_installed_copy(self):
  from fgmapping.services.recovery import RestoreJob
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=create_case(root/'source.fgcase','SYNTHETIC SOURCE');before=digest(source);unrelated=root/'.fg_restore_other.sqlite';unrelated.write_bytes(b'SYNTHETIC UNRELATED');target=root/'new.fgcase';job=RestoreJob(source,target,'TEST_ENGINE');job.process.wait(timeout=15);self.assertTrue(target.exists());job.cancel();self.assertTrue(target.exists());self.assertEqual(digest(source),before);self.assertEqual(unrelated.read_bytes(),b'SYNTHETIC UNRELATED')
 def test_interrupted_bulk_save_reopens_recoverable_source_records(self):
  from fgmapping.services.geometry import enable_geometry
  from fgmapping.services.bulk_import import prepare_bulk,HEADERS
  from fgmapping.services.preparation import apply_plan
  import csv,io
  import fgmapping.services.case as case
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'s.fgcase','SYNTHETIC BULK RECOVERY');s=CaseSession(p,root/'runtime');enable_geometry(s,'TEST_ENGINE');s.add_evidence('E','SYNTHETIC','Synthetic source','A','fixture','TEST_ENGINE');s.save();before=digest(p)
   out=io.StringIO();wr=csv.DictWriter(out,fieldnames=HEADERS);wr.writeheader();wr.writerow({**{k:'' for k in HEADERS},'data_class':'SYNTHETIC','kind':'DETECTOR','action':'CREATE','id':'D','evidence_id':'E','detector_type':'FLAME','x':'1','y':'2','z':'3','azimuth':'0','elevation':'0','roll':'0'});apply_plan(s,prepare_bulk(s,out.getvalue().encode(),'CSV'),'TEST_ENGINE','Synthetic source reviewed')
   replace=case.os.replace
   def fail(src,dst):
    if Path(dst)==p:raise OSError('Synthetic interrupted bulk save')
    return replace(src,dst)
   with patch.object(case.os,'replace',fail):
    with self.assertRaises(OSError):s.save()
   s.close(discard_unsaved=False);self.assertEqual(digest(p),before)
   with CaseSession(p,root/'runtime',recover=True) as recovered:
    self.assertEqual(recovered.con.execute("SELECT x FROM detectors WHERE id='D'").fetchone()[0],1);self.assertEqual(recovered.con.execute("SELECT count(*) FROM ledger WHERE command='RETAIN_PREPARATION_SOURCE'").fetchone()[0],1);recovered.save()
