"""Bounded killable preview worker operating only on a SQLite snapshot."""
import json,sys,os,time,tempfile,subprocess
from pathlib import Path
from fgmapping.services.preparation import PreparationPlan
class PreparationJob:
 def __init__(self,session,raw,format,kind,seconds=30):
  import sqlite3
  if not isinstance(raw,bytes) or not 0<len(raw)<=4_000_000 or kind not in ('BULK_REGISTER','GEOMETRY_REVISION') or not 0<seconds<=60:raise ValueError('Bounded synthetic preparation request required')
  self.temp=tempfile.TemporaryDirectory(prefix='fg_preparation_');root=Path(self.temp.name);self.seconds=seconds;self.started=time.monotonic();self.out=tempfile.TemporaryFile();self.err=tempfile.TemporaryFile()
  from contextlib import closing
  with closing(sqlite3.connect(root/'snapshot.fgcase')) as dest:session.con.backup(dest)
  (root/'source.bin').write_bytes(raw);(root/'request.json').write_text(json.dumps({'format':format,'kind':kind}))
  self.process=subprocess.Popen([sys.executable,'-B','-m','fgmapping.services.preparation_job',str(root)],stdout=self.out,stderr=self.err)
 def close(self):self.out.close();self.err.close();self.temp.cleanup()
 def cancel(self):
  if self.process.poll() is None:self.process.kill()
  self.process.wait();self.close()
 def result(self):
  try:self.process.wait(timeout=self.seconds)
  except subprocess.TimeoutExpired:self.cancel();raise ValueError('Preparation preview timed out; no case change')
  self.out.seek(0);self.err.seek(0);data=self.out.read(20_000_001);err=self.err.read(4000);code=self.process.returncode;self.close()
  if code or len(data)>20_000_000:raise ValueError('Preparation refused: '+err.decode('utf8')[-1500:])
  return PreparationPlan(**json.loads(data))
if __name__=='__main__':
 try:
  if os.name=='posix':
   import resource
   resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
  from fgmapping.services.case import CaseSession
  from fgmapping.services.bulk_import import prepare_bulk
  from fgmapping.services.reconciliation import prepare_revision
  root=Path(sys.argv[1]);p=json.loads((root/'request.json').read_text());raw=(root/'source.bin').read_bytes()
  with CaseSession(root/'snapshot.fgcase',root/'runtime') as s:plan=prepare_bulk(s,raw,p['format']) if p['kind']=='BULK_REGISTER' else prepare_revision(s,raw)
  print(json.dumps(plan.to_dict()))
 except Exception as exc:print(str(exc),file=sys.stderr);sys.exit(2)
