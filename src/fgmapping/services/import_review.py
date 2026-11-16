"""Reviewed synthetic import proposal and atomic append/replace; no qualification."""
import hashlib,json
from dataclasses import dataclass
from fgmapping.domain.scene import Frame,Scene,Mesh,Component,canonical
from fgmapping.services import workspace
from fgmapping.errors import CaseError
@dataclass(frozen=True)
class ImportProposal:
 raw:bytes
 format:str
 result:dict
 @classmethod
 def prepare(cls,raw,format,result):
  if len(raw)>4000000 or hashlib.sha256(raw).hexdigest()!=result['source_sha256']:raise CaseError('SOURCE_HASH','Source changed before import review')
  mesh=Mesh(**result['mesh'])
  if mesh.sha256!=result['mesh_sha256']:raise CaseError('MESH_HASH','Derived mesh hash mismatch')
  Frame(**result['frame'])
  return cls(raw,format,json.loads(canonical(result)))
 @property
 def source_hash(self):return self.result['source_sha256']
 def apply(self,session,actor,mode):
  if mode not in ('APPEND','REPLACE'):raise CaseError('IMPORT_MODE','Explicit append or replacement required')
  if not actor.strip():raise CaseError('ACTOR','Named import reviewer required; this does not approve engineering geometry')
  ImportProposal.prepare(self.raw,self.format,self.result)
  sha=self.source_hash;eid='SYN-IMPORT-'+sha[:16];frameid='IMPORT-SI-'+sha[:12];componentid='IMPORT-'+sha[:12]
  existing=workspace.row(session,'geometry_scene',1);mesh=Mesh(**self.result['mesh'])
  frame=Frame(frameid,'m','Normalized from explicit source frame '+self.result['frame']['datum'])
  component=Component(componentid,'Reviewed candidate synthetic mesh','MESH',frameid,mesh,eid)
  if mode=='APPEND' and existing:
   before=Scene.from_dict(json.loads(existing['payload_json']))
   if componentid in {c.id for c in before.components}:raise CaseError('IMPORT_DUPLICATE','This source component is already present')
   scene=Scene(before.frames+(frame,),before.components+(component,),before.source_revision+' | append '+sha[:12],sha)
  else:scene=Scene((frame,),(component,),'SYNTHETIC reviewed import',sha)
  changes=[]
  if workspace.row(session,'evidence',eid) is None:changes.append(workspace.change(session,'evidence',eid,workspace.synthetic_evidence(eid,'Reviewed synthetic mesh '+sha,'UNVERIFIED','Source SHA256 '+sha)))
  changes.append(workspace.change(session,'geometry_scene',1,{'id':1,'payload_json':canonical(scene.to_dict()),'sha256':scene.sha256,'status':'UNVERIFIED'}))
  with session.con:
   workspace._apply(session,changes)
   session.con.execute('INSERT OR IGNORE INTO geometry_attachment VALUES(?,?,?,?,?,?)',(sha,self.raw,self.format,canonical(self.result['frame']),canonical(self.result),eid))
   retained=[c for c in changes if c['table']=='evidence']
   if retained:session._log(actor,'RETAIN_IMPORT_SOURCE',{'changes':retained,'source_sha256':sha},{'retain':'Raw source and its provenance remain retained when geometry is undone'})
   reversible=[c for c in changes if c['table']!='evidence']
   session._log(actor,'WORKSPACE_EDIT',{'description':mode+' reviewed candidate synthetic geometry '+sha,'changes':reversible},{'changes':workspace._inverse(reversible)})
  session._dirty=True
  return componentid
