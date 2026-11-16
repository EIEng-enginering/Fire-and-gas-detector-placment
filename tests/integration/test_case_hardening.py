import json,os,tempfile,unittest,subprocess,sys
from pathlib import Path
from unittest.mock import patch
from fgmapping.services.case import create_case,CaseSession,digest
from fgmapping.errors import CaseError
import fgmapping.services.case as module
class CaseHardening(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.path=create_case(self.root/'s.fgcase','SYNTHETIC')
 def test_writer_fence_across_runtimes(self):
  with CaseSession(self.path,self.root/'r1'):
   with self.assertRaises(CaseError) as c:CaseSession(self.path,self.root/'r2')
   self.assertEqual(c.exception.code,'LOCKED')
 def test_symlink_alias_fenced(self):
  p=self.root/'alias.fgcase';p.symlink_to(self.path)
  with CaseSession(self.path,self.root/'r1'):
   with self.assertRaises(CaseError):CaseSession(p,self.root/'r2')
 def test_hardlink_alias_refused(self):
  p=self.root/'alias.fgcase';os.link(self.path,p)
  with self.assertRaises(CaseError) as c:CaseSession(p,self.root/'r')
  self.assertEqual(c.exception.code,'ALIASED_CASE')
 def test_failure_before_replace_keeps_original_and_recoverable_work(self):
  before=digest(self.path);s=CaseSession(self.path,self.root/'r');s.set_name('SYNTHETIC EDIT','TEST_ENGINE');replace=module.os.replace
  def fail(src,dst):
   if Path(dst)==self.path:raise OSError('SYNTHETIC injected replace failure')
   return replace(src,dst)
  with patch.object(module.os,'replace',fail):
   with self.assertRaises(OSError):s.save()
  self.assertEqual(digest(self.path),before);s.close()
  with CaseSession(self.path,self.root/'r',recover=True) as recovered:self.assertEqual(recovered.name(),'SYNTHETIC EDIT');recovered.save()
 def test_failure_after_install_reconciles_metadata(self):
  s=CaseSession(self.path,self.root/'r');s.set_name('SYNTHETIC EDIT','TEST_ENGINE');write=module.atomic_json
  def fail(path,payload):
   if 'saved' in payload:raise OSError('SYNTHETIC metadata failure after install')
   return write(path,payload)
  with patch.object(module,'atomic_json',fail):
   with self.assertRaises(OSError):s.save()
  s.close()
  with CaseSession(self.path,self.root/'r',recover=True) as recovered:self.assertEqual(recovered.name(),'SYNTHETIC EDIT');recovered.save()
 def test_native_lock_released_after_process_kill(self):
  script="from fgmapping.services.case import CaseSession;import time; s=CaseSession(__import__('sys').argv[1],__import__('sys').argv[2]);print('LOCKED',flush=True);time.sleep(30)"
  p=subprocess.Popen([sys.executable,'-B','-c',script,str(self.path),str(self.root/'r')],stdout=subprocess.PIPE,text=True)
  try:self.assertEqual(p.stdout.readline().strip(),'LOCKED')
  finally:p.kill();p.wait();p.stdout.close()
  with CaseSession(self.path,self.root/'r',recover=True) as recovered:self.assertEqual(recovered.name(),'SYNTHETIC')
  self.assertTrue(list((self.root/'r/Logs').glob('*stale_lock*')))

 def test_live_legacy_runtime_lock_is_not_quarantined(self):
  import hashlib
  runtime=self.root/'r';(runtime/'Locks').mkdir(parents=True)
  key=hashlib.sha256(str(self.path.resolve()).encode()).hexdigest()[:24]
  lock=runtime/'Locks'/(key+'.lock');lock.write_text(json.dumps({'pid':os.getpid(),'case':str(self.path)}))
  with self.assertRaises(CaseError) as c:CaseSession(self.path,runtime)
  self.assertEqual(c.exception.code,'LOCKED');self.assertTrue(lock.exists())
