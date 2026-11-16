"""Killable offline report worker using an immutable synthetic snapshot, not a case."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
from fgmapping.domain.scene import canonical
class ReportJob:
 def __init__(self,snapshot,destination,seconds=60):
  if snapshot.get('data_class')!='SYNTHETIC':raise ValueError('Only synthetic report snapshots permitted')
  if not 0<seconds<=300:raise ValueError('Explicit report timeout in (0,300] required')
  self.seconds=seconds;self.temp=tempfile.TemporaryDirectory(prefix='fg_report_');self.output=tempfile.TemporaryFile();self.error=tempfile.TemporaryFile()
  path=Path(self.temp.name)/'snapshot.json';path.write_text(canonical(snapshot));self.destination=Path(destination)
  self.process=subprocess.Popen([sys.executable,'-B','-m','fgmapping.services.report_job','--worker',str(path),str(self.destination)],stdout=self.output,stderr=self.error)
 def cancel(self):
  if self.process.poll() is None:self.process.kill()
  self.process.wait();self._close()
 def _close(self):self.output.close();self.error.close();self.temp.cleanup()
 def result(self):
  try:self.process.wait(timeout=self.seconds)
  except subprocess.TimeoutExpired:self.cancel();raise ValueError('Report worker timed out; incomplete output retained for inspection')
  self.output.seek(0);self.error.seek(0);out=self.output.read(100000);err=self.error.read(4000);code=self.process.returncode;self._close()
  if code:raise ValueError('Report worker failed: '+err.decode('utf8')[-1500:])
  return json.loads(out)
if __name__=='__main__':
 try:
  if os.name=='posix':
   import resource
   resource.setrlimit(resource.RLIMIT_AS,(1536*1024*1024,1536*1024*1024))
   resource.setrlimit(resource.RLIMIT_CPU,(60,60))
  from fgmapping.services.reporting import write_reports
  print(json.dumps(write_reports(json.loads(Path(sys.argv[2]).read_text()),sys.argv[3])))
 except Exception as exc:print(str(exc),file=sys.stderr);sys.exit(2)
