"""Audited backup restoration into a NEW portable case; never overwrites a case."""
import os,json,sqlite3,tempfile,shutil
from pathlib import Path
from contextlib import closing
from fgmapping.services.case import digest,utc_now,fsync_directory,fsync_file
from fgmapping.errors import CaseError

def inspect_backup(path):
 path=Path(path).expanduser().resolve()
 if not path.is_file() or path.stat().st_size>256*1024*1024:raise CaseError('BACKUP','Missing backup or exceeds 256 MB development bound')
 try:
  with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as con:
   version=con.execute('PRAGMA user_version').fetchone()[0]
   if version not in (1,2,3,4) or con.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or con.execute('PRAGMA foreign_key_check').fetchone() is not None:raise CaseError('BACKUP','Unsupported or corrupt backup')
   name,uuid=con.execute('SELECT name,case_uuid FROM case_info WHERE id=1').fetchone()
   return {'filename':path.name,'sha256':digest(path),'schema':version,'name':name,'case_uuid':uuid,'size_bytes':path.stat().st_size}
 except sqlite3.Error as exc:raise CaseError('BACKUP','Backup SQLite structure could not be verified') from exc

def list_backups(runtime):
 folder=Path(runtime)/'Backups';results=[]
 if not folder.exists():return results
 for path in sorted(folder.glob('*.fgcase')):
  try:results.append({'path':str(path),**inspect_backup(path),'check':'PASS'})
  except CaseError as exc:results.append({'path':str(path),'filename':path.name,'check':'REFUSED','reason':str(exc)})
 return results

def restore_as_new(backup,destination,actor,*,_temp_prefix='.fg_restore_'):
 if not actor.strip():raise CaseError('ACTOR','Named restoration actor required')
 source=Path(backup).resolve();target=Path(destination).expanduser().resolve()
 if target.suffix!='.fgcase' or target.exists():raise CaseError('RESTORE_TARGET','Choose a new .fgcase path; existing cases are never overwritten')
 info=inspect_backup(source);target.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(prefix=_temp_prefix,suffix='.sqlite',dir=target.parent);os.close(fd)
 try:
  shutil.copyfile(source,name)
  if digest(Path(name))!=info['sha256'] or digest(source)!=info['sha256']:raise CaseError('BACKUP_CONFLICT','Backup changed while preparing restoration')
  con=sqlite3.connect(name)
  try:
   with con:con.execute('INSERT INTO ledger(utc,actor,command,forward_json,inverse_json,is_compensation) VALUES(?,?,?,?,?,0)',(utc_now(),actor,'RESTORE_BACKUP_AS_NEW',json.dumps({'source_filename':source.name,'source_sha256':info['sha256'],'case_uuid':info['case_uuid']},sort_keys=True),json.dumps({'retain':'Original backup/case untouched; restored copy is a separate artifact'})))
  finally:con.close()
  fsync_file(name)
  try:os.link(name,target)
  except FileExistsError as exc:raise CaseError('RESTORE_TARGET','Destination appeared concurrently; refused overwrite') from exc
  fsync_directory(target.parent)
 finally:
  if os.path.exists(name):os.unlink(name)
 return target


class RestoreJob:
 """Background restoration; cancellation never removes an installed target."""
 def __init__(self,backup,destination,actor,seconds=60):
  import subprocess,sys
  from uuid import uuid4
  if not actor.strip() or not 0<seconds<=120:raise CaseError('RESTORE','Named actor and bounded job time required')
  self.destination=Path(destination).expanduser().resolve();self.prefix='.fg_restore_'+uuid4().hex+'_';self.seconds=seconds
  self.temp=tempfile.TemporaryDirectory(prefix='fg_restore_job_');self.out=tempfile.TemporaryFile();self.err=tempfile.TemporaryFile()
  request=Path(self.temp.name)/'request.json';request.write_text(json.dumps({'backup':str(Path(backup).resolve()),'destination':str(self.destination),'actor':actor,'prefix':self.prefix}))
  self.process=subprocess.Popen([sys.executable,'-B','-m','fgmapping.services.recovery',str(request)],stdout=self.out,stderr=self.err)
 def _close(self):
  self.out.close();self.err.close();self.temp.cleanup()
  # Exact random-token files belong to this job; never touch source/installed case.
  if self.destination.parent.exists():
   for p in self.destination.parent.glob(self.prefix+'*.sqlite'):p.unlink(missing_ok=True)
 def cancel(self):
  if self.process.poll() is None:self.process.kill()
  self.process.wait();self._close()
 def result(self):
  import subprocess
  try:self.process.wait(timeout=self.seconds)
  except subprocess.TimeoutExpired:self.cancel();raise CaseError('RESTORE_TIMEOUT','Restore timed out; inspect the new target path before retrying')
  self.out.seek(0);self.err.seek(0);out=self.out.read(100000);err=self.err.read(4000);code=self.process.returncode;self._close()
  if code:raise CaseError('RESTORE_FAILED',err.decode('utf8')[-1500:])
  return json.loads(out)

if __name__=='__main__':
 import sys
 try:
  if os.name=='posix':
   import resource
   resource.setrlimit(resource.RLIMIT_AS,(1024*1024*1024,1024*1024*1024));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
  request=json.loads(Path(sys.argv[1]).read_text());p=restore_as_new(request['backup'],request['destination'],request['actor'],_temp_prefix=request['prefix']);print(json.dumps({'path':str(p),'source_untouched':True,'result':'RESTORED_NEW_COPY'}))
 except Exception as exc:print(str(exc),file=sys.stderr);sys.exit(2)
