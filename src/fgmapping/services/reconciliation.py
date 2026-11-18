"""Stable-ID synthetic facility revision review; explicit affected-mount decisions."""
import json
from dataclasses import replace
from fgmapping.domain.scene import Scene,Frame,Mesh,canonical
from fgmapping.domain.mounting import component_fingerprint
from fgmapping.services.geometry import get_scene
from fgmapping.services.mounts import set_mount
from fgmapping.services.preparation import staging,make_plan
from fgmapping.services import workspace as w
from fgmapping.errors import CaseError

def revision_impact(s,target):
 old=get_scene(s)
 if old is None:raise CaseError('GEOMETRY','Existing facility scene required')
 a={c.id:c for c in old.components if c.semantic!='DETECTOR'};b={c.id:c for c in target.components}
 if any(c.semantic=='DETECTOR' for c in b.values()):raise CaseError('REVISION_MARKERS','Supply facility geometry only; detector display markers are preserved separately')
 changes=[]
 for id in sorted(set(a)|set(b)):
  state='ADDED' if id not in a else 'REMOVED' if id not in b else 'CHANGED' if component_fingerprint(old,a[id])!=component_fingerprint(target,b[id]) else 'UNCHANGED'
  if state!='UNCHANGED':changes.append({'component_id':id,'change':state})
 changed={x['component_id'] for x in changes if x['change']!='ADDED'};mounts=[]
 if s.con.execute('PRAGMA user_version').fetchone()[0]>=3:
  for (id,) in s.con.execute('SELECT detector_id FROM detector_mount ORDER BY detector_id'):
   m=w.row(s,'detector_mount',id)
   if m['component_id'] in changed or m['component_id'] not in a:mounts.append({'detector_id':id,'component_id':m['component_id'],'target_present':m['component_id'] in b})
 references=[]
 for id,payload in s.con.execute('SELECT id,payload_json FROM engineering_record ORDER BY id'):
  ref=json.loads(payload).get('geometry_component_id')
  if ref and ref not in b and ref not in {c.id for c in old.components if c.semantic=='DETECTOR'}:references.append({'record_id':id,'missing_component_id':ref})
 return {'components':changes,'affected_mounts':mounts,'missing_record_references':references,'qualification':'UNVERIFIED'}

def prepare_revision(s,raw):
 if not isinstance(raw,bytes) or not 0<len(raw)<=4_000_000:raise CaseError('REVISION_SIZE','Revision JSON up to 4 MB required')
 try:p=json.loads(raw)
 except (ValueError,UnicodeError) as exc:raise CaseError('REVISION_JSON','UTF-8 JSON revision required') from exc
 if set(p)!={'contract','data_class','scene','mount_decisions'} or p['contract']!='fg-geometry-revision/1' or p['data_class']!='SYNTHETIC':raise CaseError('REVISION_CONTRACT','Closed fg-geometry-revision/1 SYNTHETIC contract required')
 target=Scene.from_dict(p['scene']);old=get_scene(s);impact=revision_impact(s,target)
 if any(w.row(s,'evidence',c.evidence_id) is None or w.row(s,'evidence',c.evidence_id)['data_class']!='SYNTHETIC' for c in target.components):raise CaseError('EVIDENCE','Every revision component must name existing synthetic evidence')
 if impact['missing_record_references']:raise CaseError('REVISION_REFERENCES','Detach or revise missing equipment references before preparing this scene revision')
 decisions=p['mount_decisions']
 if not isinstance(decisions,list):raise CaseError('REVISION_DECISIONS','Explicit affected-mount decisions required')
 byid={}
 for d in decisions:
  if set(d)!={'detector_id','action','target_component_id','reason','evidence_id'} or d['action'] not in ('FOLLOW_COMPONENT','KEEP_WORLD_DETACH') or any(not isinstance(v,str) for v in d.values()) or not d['reason'].strip():raise CaseError('REVISION_DECISIONS','Closed explicit mount action, reason and evidence required')
  if d['detector_id'] in byid:raise CaseError('REVISION_DECISIONS','Duplicate mount decision')
  if d['action']=='KEEP_WORLD_DETACH' and d['target_component_id']:raise CaseError('REVISION_DECISIONS','Detached mount must not name a target')
  byid[d['detector_id']]=d
 if set(byid)!={x['detector_id'] for x in impact['affected_mounts']}:raise CaseError('REVISION_DECISIONS','Exactly one decision for every affected mount required; no implicit moves')
 stage=staging(s)
 try:
  markers=[];frameid='REVISION_MARKERS_SI'
  if frameid in {f.id for f in target.frames}:raise CaseError('REVISION_FRAME','Reserved marker frame ID conflicts with facility source')
  for c in old.components:
   if c.semantic=='DETECTOR':
    if c.id in {x.id for x in target.components}:raise CaseError('REVISION_ID','Facility component collides with retained detector marker')
    markers.append(replace(c,frame_id=frameid,mesh=Mesh(tuple(old.frame(c.frame_id).world(v) for v in c.mesh.vertices),c.mesh.faces)))
  merged=replace(target,components=target.components+tuple(markers),frames=target.frames+((Frame(frameid,'m','Retained detector display positions'),) if markers else ()))
  with stage.con:w._apply(stage,[w.change(stage,'geometry_scene',1,{'id':1,'payload_json':canonical(merged.to_dict()),'sha256':merged.sha256,'status':'UNVERIFIED'})])
  for id,d in sorted(byid.items()):
   if w.row(stage,'evidence',d['evidence_id']) is None or w.row(stage,'evidence',d['evidence_id'])['data_class']!='SYNTHETIC':raise CaseError('EVIDENCE','Existing decision evidence required')
   m=w.row(stage,'detector_mount',id)
   if d['action']=='KEEP_WORLD_DETACH':
    with stage.con:w._apply(stage,[w.change(stage,'detector_mount',id,None)])
   else:
    source=next((c for c in old.components if c.id==m['component_id']),None);new=next((c for c in target.components if c.id==d['target_component_id']),None)
    if source is None or new is None or component_fingerprint(old,source)!=m['component_fingerprint']:raise CaseError('REVISION_MOUNT','Resolve stale/missing prior mount before following a component')
    if old.frame(source.frame_id).units!=target.frame(new.frame_id).units:raise CaseError('REVISION_UNITS','Source anchor units changed; detach and redeclare the mount manually')
    set_mount(stage,id,new.id,json.loads(m['anchor_local_json']),json.loads(m['offset_m_json']),json.loads(m['orientation_local_json']),d['evidence_id'],'AUTOMATION_ENGINE')
  return make_plan(s,stage,'GEOMETRY_REVISION',raw,'JSON',{**impact,'mount_decisions':decisions,'source_revision':target.source_revision,'geometry_sha256':target.sha256})
 finally:stage.con.close()
