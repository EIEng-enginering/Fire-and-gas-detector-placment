"""Undoable study basis and separate input vs engineering-method readiness."""
import json
from fgmapping.services import workspace as w
from fgmapping.services.study_schema import require_study
from fgmapping.services.geometry import get_scene
from fgmapping.services.mounts import mount_status
from fgmapping.domain.study_basis import validate_basis
from fgmapping.errors import CaseError

def set_basis(session,payload,evidence_id,actor):
 require_study(session);payload=validate_basis(payload)
 if w.row(session,'evidence',evidence_id) is None:raise CaseError('EVIDENCE','Study basis evidence required')
 scene=get_scene(session);ids={c.id for c in scene.components} if scene else set()
 for exclusion in payload['exclusions']:
  if exclusion['component_id'] not in ids or w.row(session,'evidence',exclusion['evidence_id']) is None:raise CaseError('EXCLUSION','Exclusion geometry or evidence missing')
 after={'id':'STUDY','payload_json':json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False),'evidence_id':evidence_id,'status':'CANDIDATE'}
 w.execute(session,[w.change(session,'study_basis','STUDY',after)],actor,'Set candidate study basis '+payload['revision'])

def readiness(session):
 require_study(session);missing=[];blocked=[];review=[]
 for table in ('detector_mount','study_basis','performance_dataset','detector_performance_link'):
  if session.con.execute('SELECT 1 FROM '+table+" WHERE status!='CANDIDATE' LIMIT 1").fetchone():blocked.append('UNEXPECTED_PREPARATION_STATUS:'+table)
 stored=w.row(session,'study_basis','STUDY');basis=None if stored is None else validate_basis(json.loads(stored['payload_json']))
 if basis is None:missing.append('STUDY_BASIS')
 else:
  for key in ('revision','coordinate_reference','target_description','fuel_or_gas','criterion_reference','uncertainty_reference'):
   if not basis[key].strip() or basis[key]=='NOT SUPPLIED':missing.append(key.upper())
  if basis['target_fraction'] in (None,'','NOT SUPPLIED'):missing.append('TARGET_FRACTION')
  scene=get_scene(session);components={c.id for c in scene.components} if scene else set()
  for exclusion in basis['exclusions']:
   if exclusion['component_id'] not in components:blocked.append('MISSING_EXCLUDED_COMPONENT:'+exclusion['component_id'])
 detectors=w.detector_rows(session)
 if not detectors:missing.append('DETECTORS')
 if basis:
  if basis['study_type']=='BOTH':blocked.append('MIXED_STUDY_REQUIRES_SEPARATE_METHOD_BASES')
  permitted={'FLAME':{'FLAME'},'GAS':{'POINT_GAS','OPEN_PATH'},'BOTH':{'FLAME','POINT_GAS','OPEN_PATH'}}[basis['study_type']]
  eligible=sum(d['detector_type'] in permitted for d in detectors)
  if basis['voting']>eligible:blocked.append('VOTING_EXCEEDS_ELIGIBLE_DETECTORS')
  for d in detectors:
   if d['detector_type']=='ULTRASONIC':blocked.append('UNSUPPORTED_ULTRASONIC_METHOD:'+d['id'])
 if get_scene(session) is None:missing.append('FACILITY_GEOMETRY')
 for d in detectors:
  details=w.row(session,'detector_details',d['id'])
  if details is None:missing.append('ORIENTATION:'+d['id'])
  link=w.row(session,'detector_performance_link',d['id'])
  if not link:missing.append('PERFORMANCE_DATASET:'+d['id'])
  else:
   dataset=w.row(session,'performance_dataset',link['dataset_id'])
   try:
    from fgmapping.domain.performance import parse_dataset
    from fgmapping.domain.scene import canonical
    parsed=parse_dataset(dataset['raw_text'].encode('utf8'));p=parsed['payload']
    if parsed['import_sha256']!=dataset['import_sha256'] or canonical(p)!=dataset['payload_json']:raise ValueError('Dataset content changed')
   except (ValueError,TypeError,KeyError):blocked.append('PERFORMANCE_INTEGRITY:'+d['id']);continue
   if not details or any(details[k]!=p[k] for k in ('manufacturer','model','sensitivity')):blocked.append('PERFORMANCE_MISMATCH:'+d['id'])
   review.append('SYNTHETIC_PERFORMANCE_ONLY:'+d['id'])
  mount=w.row(session,'detector_mount',d['id'])
  if mount and mount_status(session,mount)!='CURRENT_SOURCE':blocked.append('STALE_OR_MISSING_MOUNT:'+d['id'])
 review.append('GEOMETRY_AND_MOUNT_FEASIBILITY_NOT_QUALIFIED')
 if session.con.execute('PRAGMA user_version').fetchone()[0]>=4:return _coverage_readiness(session,missing,blocked,review)
 return {'input_status':'BLOCKED' if blocked else 'MISSING' if missing else 'INPUTS_PRESENT','missing':sorted(missing),'blocking':sorted(blocked),'review':sorted(review),'engineering_calculation_status':'BLOCKED','engineering_blockers':['No qualified manufacturer response engine','No authorised real vendor performance basis','Independent engineering review and owner promotion required'],'qualification':'UNVERIFIED','review_status':'CANDIDATE'}

def _coverage_readiness(session,missing,blocked,review):
 """Schema 4 (Rev G): engineering calculation is gated per zone on complete inputs.
 Per-zone library assignments/targets replace the schema-3 preparation-dataset and
 single-basis target items. COMPUTED - UNREVIEWED development results - not independently verified."""
 from fgmapping.services.coverage import coverage_readiness
 replaced=('PERFORMANCE_DATASET:','TARGET_FRACTION','CRITERION_REFERENCE')
 missing=[m for m in missing if not m.startswith(replaced)]
 blocked=[b for b in blocked if b!='MIXED_STUDY_REQUIRES_SEPARATE_METHOD_BASES']
 review=[r for r in review if not r.startswith('SYNTHETIC_PERFORMANCE_ONLY:')]
 zones=coverage_readiness(session);eng=[]
 for z,st in zones.items():
  eng+=[z+': '+b for b in st['blockers']];review+=st['review']
 configured=[st for st in zones.values() if st['status']!='NOT CONFIGURED']
 if not configured:eng.append('No zone has a coverage setup')
 status='READY' if configured and all(st['status']=='READY' for st in configured) else 'BLOCKED'
 return {'input_status':'BLOCKED' if blocked else 'MISSING' if missing else 'INPUTS_PRESENT','missing':sorted(missing),'blocking':sorted(blocked),'review':sorted(set(review)),
  'engineering_calculation_status':status,'engineering_blockers':sorted(eng),'zones':zones,'qualification':'COMPUTED - UNREVIEWED - NOT INDEPENDENTLY VERIFIED','review_status':'CANDIDATE'}
