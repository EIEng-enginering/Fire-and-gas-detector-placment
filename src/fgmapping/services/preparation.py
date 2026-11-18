"""Closed synthetic preparation plans; preview is read-only, commit conflict-aware."""
import hashlib,json,sqlite3
from dataclasses import dataclass,asdict
from types import SimpleNamespace
from fgmapping.services import workspace as w
from fgmapping.domain.scene import canonical,content_hash
from fgmapping.errors import CaseError

@dataclass(frozen=True)
class PreparationPlan:
 kind:str
 raw_base64:str
 format:str
 source_sha256:str
 base_hash:str
 changes_json:str
 summary_json:str
 def to_dict(self):return asdict(self)

def snapshot(s):
 version=s.con.execute('PRAGMA user_version').fetchone()[0]
 if version not in (2,3,4):raise CaseError('MIGRATION_REQUIRED','Enable candidate geometry schema first')
 tables=['evidence','detectors','detector_details','engineering_record','geometry_scene']+(['detector_mount','study_basis','performance_dataset','detector_performance_link','preparation_review'] if version>=3 else [])+(['detector_library','detector_library_assignment','coverage_setup'] if version>=4 else [])
 return {t:{str(row[0]):dict(zip(w.TABLES[t],row)) for row in s.con.execute('SELECT '+','.join(w.TABLES[t])+' FROM '+t+' ORDER BY '+w.TABLES[t][0])} for t in tables}

def state_hash(s):
 return content_hash({'rows':snapshot(s),'uuid':s.con.execute('SELECT case_uuid FROM case_info').fetchone()[0],'ledger':s.con.execute('SELECT coalesce(max(event_id),0) FROM ledger').fetchone()[0]})

def staging(s):
 con=sqlite3.connect(':memory:');s.con.backup(con);con.execute('PRAGMA foreign_keys=ON')
 return SimpleNamespace(con=con,_log=lambda *args:None,_dirty=False)

def make_plan(s,stage,kind,raw,format,summary):
 import base64
 before=snapshot(s);after=snapshot(stage);changes=[]
 for table in before:
  for key in sorted(set(before[table])|set(after[table])):
   a,b=before[table].get(key),after[table].get(key)
   if canonical(a)!=canonical(b):changes.append({'table':table,'key':(b or a)[w.TABLES[table][0]],'before':a,'after':b})
 # Parents precede inserts; deletes are not supported by these preparation plans.
 order={'evidence':0,'geometry_scene':1,'detectors':2,'detector_details':3,'engineering_record':4,'detector_mount':5}
 changes.sort(key=lambda c:(order.get(c['table'],9),str(c['key'])))
 return PreparationPlan(kind,base64.b64encode(raw).decode('ascii'),format,hashlib.sha256(raw).hexdigest(),state_hash(s),canonical(changes),canonical(summary))

def apply_plan(s,plan,actor,reason):
 import base64
 if not isinstance(actor,str) or not actor.strip() or not isinstance(reason,str) or not reason.strip():raise CaseError('REVIEW','Named editor and review rationale required')
 if state_hash(s)!=plan.base_hash:raise CaseError('PREVIEW_STALE','Case changed after preview; prepare and review again')
 raw=base64.b64decode(plan.raw_base64,validate=True)
 if hashlib.sha256(raw).hexdigest()!=plan.source_sha256:raise CaseError('SOURCE_HASH','Preparation source hash mismatch')
 if plan.kind=='BULK_REGISTER':
  from fgmapping.services.bulk_import import prepare_bulk
  rebuilt=prepare_bulk(s,raw,plan.format)
 elif plan.kind=='GEOMETRY_REVISION':
  from fgmapping.services.reconciliation import prepare_revision
  rebuilt=prepare_revision(s,raw)
 else:raise CaseError('PREPARATION_KIND','Unknown preparation plan')
 if rebuilt!=plan:raise CaseError('PLAN_TAMPER','Preview differs from independently rebuilt source plan')
 changes=json.loads(plan.changes_json)
 with s.con:
  w._apply(s,changes)
  s._log(actor,'WORKSPACE_EDIT',{'description':plan.kind+' reviewed synthetic source '+plan.source_sha256,'changes':changes},{'changes':w._inverse(changes)})
  s._log(actor,'RETAIN_PREPARATION_SOURCE',{'kind':plan.kind,'source_sha256':plan.source_sha256,'format':plan.format,'raw_base64':plan.raw_base64,'data_class':'SYNTHETIC','review_rationale':reason,'summary':json.loads(plan.summary_json)},{'retain':'Source bytes and review are retained; undo restores candidate entities only'})
 s._dirty=True
