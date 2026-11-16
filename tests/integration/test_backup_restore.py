from contextlib import closing
import json,tempfile,unittest,sqlite3
from pathlib import Path
from unittest.mock import patch
from fgmapping.services.case import create_case,CaseSession,digest
from fgmapping.services.recovery import restore_as_new,inspect_backup,list_backups
from fgmapping.errors import CaseError
class BackupRestore(unittest.TestCase):
 def test_restore_new_copy_no_overwrite_and_source_intact(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=create_case(root/'source.fgcase','SYNTHETIC RESTORE');before=digest(source);restored=restore_as_new(source,root/'restored.fgcase','SYNTHETIC_TEST_ACTOR')
   self.assertEqual(digest(source),before)
   with CaseSession(restored,root/'r') as s:self.assertEqual(s.name(),'SYNTHETIC RESTORE');self.assertEqual(s.snapshot()['ledger'][-1]['command'],'RESTORE_BACKUP_AS_NEW')
   with self.assertRaises(CaseError):restore_as_new(source,restored,'TEST_ENGINE')
 def test_corruption_and_missing_actor_refused(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=root/'bad.fgcase';p.write_bytes(b'not sqlite')
   with self.assertRaises(CaseError):inspect_backup(p)
   with self.assertRaises(CaseError):restore_as_new(p,root/'new.fgcase','')
 def test_install_failure_leaves_no_partial_target(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'source.fgcase','SYNTHETIC')
   with patch('fgmapping.services.recovery.os.link',side_effect=OSError('Injected restore install failure')):
    with self.assertRaises(OSError):restore_as_new(p,root/'new.fgcase','TEST_ENGINE')
   self.assertFalse((root/'new.fgcase').exists());self.assertFalse(list(root.glob('.fg_restore_*')))
 def test_worker_restore_with_hash_in_path_and_cancel(self):
  from fgmapping.services.recovery import RestoreJob
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'source # synthetic.fgcase','SYNTHETIC');result=RestoreJob(p,root/'new copy.fgcase','TEST_ENGINE').result();self.assertTrue((root/'new copy.fgcase').exists());self.assertTrue(result['source_untouched'])
   job=RestoreJob(p,root/'cancelled.fgcase','TEST_ENGINE');job.cancel();self.assertIsNotNone(job.process.poll());self.assertFalse(list(root.glob(job.prefix+'*.sqlite')))
 def test_broken_reference_case_refused_on_open(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'broken.fgcase','SYNTHETIC')
   with closing(sqlite3.connect(p)) as con, con:con.execute("INSERT INTO detectors(id,detector_type,x,y,z,evidence_id) VALUES('D','FLAME',0,0,0,'MISSING')")
   with self.assertRaises(CaseError) as exc:CaseSession(p,root/'r')
   self.assertEqual(exc.exception.code,'REFERENTIAL_INTEGRITY')
 def test_backup_with_broken_reference_is_not_verified(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=create_case(root/'broken.fgcase','SYNTHETIC')
   with closing(sqlite3.connect(p)) as con, con:con.execute("INSERT INTO detectors(id,detector_type,x,y,z,evidence_id) VALUES('D','FLAME',0,0,0,'MISSING')")
   with self.assertRaises(CaseError):inspect_backup(p)
