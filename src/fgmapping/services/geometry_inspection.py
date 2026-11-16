"""Killable snapshot geometry diagnostic and conflict-aware immutable run commit."""
import json,os,sys,tempfile,subprocess,hashlib
from pathlib import Path
from fgmapping.domain.scene import Scene,canonical,content_hash
from fgmapping.engine.inspection import inspect_target
from fgmapping.services.geometry import get_scene
from fgmapping.services.case import utc_now
from fgmapping.errors import CaseError

class GeometryJob:
 def __init__(self,scene,origin,obstacle_ids,target,tolerance_m,seconds=30):
  if not 0<seconds<=60:raise ValueError('Geometry worker budget must be in (0,60] seconds')
  self.inputs={'scene':scene.to_dict(),'origin':origin,'obstacle_ids':obstacle_ids,'target':target,'tolerance_m':tolerance_m};self.seconds=seconds
  self.temp=tempfile.TemporaryDirectory(prefix='fg_geometry_');path=Path(self.temp.name)/'input.json';path.write_text(canonical(self.inputs));self.out=tempfile.TemporaryFile();self.err=tempfile.TemporaryFile()
  self.process=subprocess.Popen([sys.executable,'-B','-m','fgmapping.services.geometry_inspection',str(path)],stdout=self.out,stderr=self.err)
 def cancel(self):
  if self.process.poll() is None:self.process.kill()
  self.process.wait();self._close()
 def _close(self):self.out.close();self.err.close();self.temp.cleanup()
 def result(self):
  try:self.process.wait(timeout=self.seconds)
  except subprocess.TimeoutExpired:self.cancel();raise ValueError('Geometry worker timed out; no result committed')
  self.out.seek(0);self.err.seek(0);data=self.out.read(4_000_001);err=self.err.read(4000);code=self.process.returncode;self._close()
  if code or len(data)>4_000_000:raise ValueError('Geometry worker refused: '+err.decode()[-1000:])
  return json.loads(data)

def commit_inspection(session,id,inputs,result,actor):
 if not id.strip():raise CaseError('IDENTITY','Unique run ID required')
 scene=get_scene(session)
 if scene is None or scene.sha256!=result['scene_hash'] or scene.sha256!=Scene.from_dict(inputs['scene']).sha256:raise CaseError('STALE_WORKER','Geometry changed while inspection ran; result not committed')
 from fgmapping import __version__
 root=Path(__file__).resolve().parents[1];names=['engine/spatial.py','engine/inspection.py','engine/mesh_visibility.py','engine/geometry.py','domain/scene.py','services/geometry_inspection.py'];files={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
 envelope={'method':'GEOMETRIC_TARGET_INSPECTION/1','inputs':inputs,'scene_hash':scene.sha256,'software_version':__version__,'implementation_files':files,'implementation_sha256':content_hash(files)}
 with session.con:
  session.con.execute('INSERT INTO calculation_run(id,input_hash,method,result_json,calculation_status,input_json) VALUES(?,?,?,?,?,?)',(id,content_hash(envelope),envelope['method'],canonical(result),'COMPUTED_GEOMETRIC_DEMONSTRATION',canonical(envelope)))
  session._log(actor,'GEOMETRY_INSPECTION',{'id':id,'input_hash':content_hash(envelope)},{'retain':'Diagnostic history retained; not engineering coverage'})
 session._dirty=True

if __name__=='__main__':
 try:
  if os.name=='posix':
   import resource
   resource.setrlimit(resource.RLIMIT_AS,(1024*1024*1024,1024*1024*1024));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
  p=json.loads(Path(sys.argv[1]).read_text());print(canonical(inspect_target(Scene.from_dict(p['scene']),p['origin'],p['obstacle_ids'],p['target'],p['tolerance_m'])))
 except Exception as exc:print(str(exc),file=sys.stderr);sys.exit(2)
