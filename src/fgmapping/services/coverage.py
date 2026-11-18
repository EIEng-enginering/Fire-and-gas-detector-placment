"""Rev G coverage services: schema 4, detector library, assignments, zone setups,
readiness gate and reproducible coverage runs stored in the case.

ENGINEER-REVIEWED RESULTS - NOT INDEPENDENTLY CERTIFIED. Results depend on the
detector data entered by the user; EXAMPLE library values must be replaced by
verified manufacturer data before project use.
"""
from __future__ import annotations
import hashlib,json,sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4
from fgmapping.errors import CaseError
from fgmapping.domain.scene import canonical,content_hash
from fgmapping.domain.detector_library import validate_entry,parse_library
from fgmapping.domain.coverage_setup import validate_setup
from fgmapping.services import workspace as w
from fgmapping.services.geometry import get_scene
from fgmapping.services.case import utc_now

ROOT=Path(__file__).resolve().parents[3]
SRC=Path(__file__).resolve().parents[1]
IMPLEMENTATION=('engine/coverage.py','engine/mesh_visibility.py','engine/spatial.py','engine/geometry.py','domain/detector_library.py','domain/coverage_setup.py','domain/pose.py','services/coverage.py')
EXAMPLE_STATUS='EXAMPLE VALUES - replace with manufacturer data'

def version(session):return session.con.execute('PRAGMA user_version').fetchone()[0]

def enable_coverage(session,actor):
    """Explicit schema 3 -> 4 upgrade with a restorable backup."""
    if not actor.strip():raise CaseError('ACTOR','Explicit upgrade actor required')
    v=version(session)
    if v==4:return
    if v!=3:raise CaseError('MIGRATION_REQUIRED','Enable geometry schema2 and study schema3 before coverage schema4')
    manifest=json.loads((ROOT/'contracts/candidate_manifest.json').read_text())
    for name,expected in manifest['migrations_sha256'].items():
        if hashlib.sha256((ROOT/'contracts/migrations'/name).read_bytes()).hexdigest()!=expected:raise CaseError('CONTRACT_HASH','Migration hash mismatch')
    session._backup()
    backup=session.runtime/'Backups'/(session.key+'_pre_coverage4_'+uuid4().hex+'.fgcase')
    with closing(sqlite3.connect(backup)) as dst:session.con.backup(dst)
    with session.con:
        session.con.execute('BEGIN IMMEDIATE');statement=''
        for line in (ROOT/'contracts/migrations/0004_coverage.sql').read_text().splitlines(True):
            statement+=line
            if sqlite3.complete_statement(statement):session.con.execute(statement);statement=''
        if statement.strip():raise CaseError('MIGRATION','Incomplete SQL')
        session._log(actor,'ENABLE_COVERAGE4',{'schema':4},{'restore_backup':backup.name})
    session._dirty=True

def require_coverage(session):
    if version(session)!=4:raise CaseError('MIGRATION_REQUIRED','Enable coverage schema 4 first (Coverage > Enable coverage schema)')

# ---------------- detector library ----------------
def library(session):
    require_coverage(session)
    return {id:json.loads(p) for id,p in session.con.execute('SELECT id,payload_json FROM detector_library ORDER BY id')}

def add_library_entries(session,entries,actor,description='Add detector library entries'):
    """Entries are immutable by ID: identical re-import is skipped, changed content needs a new ID."""
    require_coverage(session);changes=[];added=[];skipped=[]
    for e in entries:
        e=validate_entry(e);old=w.row(session,'detector_library',e['id']);h=content_hash(e)
        if old:
            if old['content_sha256']!=h:raise CaseError('LIBRARY_ID','Library entry '+e['id']+' already exists with different data; use a new ID/revision')
            skipped.append(e['id']);continue
        changes.append(w.change(session,'detector_library',e['id'],{'id':e['id'],'payload_json':canonical(e),'content_sha256':h,'status':'CANDIDATE'}));added.append(e['id'])
    w.execute(session,changes,actor,description)
    return {'added':added,'skipped_identical':skipped}

def import_library(session,raw,fmt,actor):
    return add_library_entries(session,parse_library(raw,fmt),actor,'Import detector library '+fmt)

def assign_library(session,detector_id,library_id,evidence_id,actor,receiver=None):
    """Explicit engineer selection of the library entry for a detector (F03)."""
    require_coverage(session);d=w.row(session,'detectors',detector_id);e=w.row(session,'detector_library',library_id)
    if d is None or e is None:raise CaseError('MISSING','Detector or library entry not found')
    if w.row(session,'evidence',evidence_id) is None:raise CaseError('EVIDENCE','Assignment evidence required')
    entry=json.loads(e['payload_json'])
    if entry['detector_type']!=d['detector_type']:raise CaseError('TYPE_MISMATCH','Library entry type '+entry['detector_type']+' does not match detector type '+d['detector_type'])
    if d['detector_type']=='OPEN_PATH':
        if not isinstance(receiver,dict) or not (set(receiver)=={'record_id'} or set(receiver)=={'x','y','z'}):raise CaseError('RECEIVER','Open-path detector needs an explicit receiver {record_id} or {x,y,z}')
        resolve_receiver(session,receiver)
    elif receiver is not None:raise CaseError('RECEIVER','Only open-path detectors take a receiver')
    after={'detector_id':detector_id,'library_id':library_id,'receiver_json':canonical(receiver),'evidence_id':evidence_id,'status':'CANDIDATE'}
    w.execute(session,[w.change(session,'detector_library_assignment',detector_id,after)],actor,'Assign library entry '+library_id+' to '+detector_id)

def unassign_library(session,detector_id,actor):
    require_coverage(session)
    if w.row(session,'detector_library_assignment',detector_id) is None:raise CaseError('MISSING','No assignment')
    w.execute(session,[w.change(session,'detector_library_assignment',detector_id,None)],actor,'Remove library assignment '+detector_id)

def resolve_receiver(session,receiver):
    if receiver is None:return None
    if 'record_id' in receiver:
        r=w.row(session,'engineering_record',receiver['record_id'])
        if r is None:raise CaseError('RECEIVER','Receiver record not found: '+receiver['record_id'])
        p=json.loads(r['payload_json']).get('position')
        if not isinstance(p,list) or len(p)!=3:raise CaseError('RECEIVER','Receiver record has no explicit position')
        return tuple(float(v) for v in p)
    return (float(receiver['x']),float(receiver['y']),float(receiver['z']))

# ---------------- zone setup ----------------
def zones(session):
    out=[]
    for id,kind,payload in session.con.execute("SELECT id,kind,payload_json FROM engineering_record WHERE kind IN ('FIRE_ZONE','GAS_ZONE') ORDER BY id"):
        p=json.loads(payload);out.append({'id':id,'kind':kind,'low':tuple(float(v) for v in p['low']),'high':tuple(float(v) for v in p['high']),'description':p.get('description','')})
    return out

def set_zone_setup(session,payload,evidence_id,actor):
    require_coverage(session);p=validate_setup(payload)
    zone=next((z for z in zones(session) if z['id']==p['zone_id']),None)
    if zone is None:raise CaseError('ZONE','Zone record not found: '+p['zone_id'])
    if (zone['kind']=='FIRE_ZONE')!=(p['method']=='FLAME_GEOGRAPHIC'):raise CaseError('METHOD','FIRE_ZONE uses FLAME_GEOGRAPHIC and GAS_ZONE uses GAS_GEOGRAPHIC')
    if w.row(session,'evidence',evidence_id) is None:raise CaseError('EVIDENCE','Setup evidence required')
    w.execute(session,[w.change(session,'coverage_setup',p['zone_id'],{'zone_id':p['zone_id'],'payload_json':canonical(p),'evidence_id':evidence_id,'status':'CANDIDATE'})],actor,'Set coverage setup '+p['zone_id'])

def zone_setup(session,zone_id):
    r=w.row(session,'coverage_setup',zone_id);return None if r is None else json.loads(r['payload_json'])

# ---------------- readiness ----------------
def _norm(s):return ' '.join(str(s).lower().split())

def gather(session,zone_id):
    """Collect the complete, hashable input envelope for one zone, or the blockers."""
    blockers=[];review=[]
    zone=next((z for z in zones(session) if z['id']==zone_id),None)
    if zone is None:return None,['ZONE_NOT_FOUND:'+zone_id],review
    setup=zone_setup(session,zone_id)
    if setup is None:return None,['NO_COVERAGE_SETUP:'+zone_id],review
    scene=get_scene(session)
    if scene is None:blockers.append('FACILITY_GEOMETRY')
    basis_row=w.row(session,'study_basis','STUDY');basis=json.loads(basis_row['payload_json']) if basis_row else None
    if basis is None:blockers.append('STUDY_BASIS')
    crit=setup['criterion_reference'].strip()
    if not crit or crit.upper()=='NOT SUPPLIED':blockers.append('CRITERION_REFERENCE:'+zone_id)
    if all(v=='NOT SUPPLIED' for v in setup['performance_targets'].values()) or not setup['performance_targets']:review.append('NO_USER_PERFORMANCE_TARGET:'+zone_id)
    flame=setup['method']=='FLAME_GEOGRAPHIC'
    types={'FLAME'} if flame else set(setup['gas']['detector_types'])
    lib={};dets=[]
    for d in w.detector_rows(session):
        if d['detector_type'] not in types:continue
        a=w.row(session,'detector_library_assignment',d['id']);det=w.row(session,'detector_details',d['id'])
        if a is None:blockers.append('LIBRARY_ENTRY_NOT_ASSIGNED:'+d['id']);continue
        e=json.loads(w.row(session,'detector_library',a['library_id'])['payload_json'])
        if e['detector_type']!=d['detector_type']:blockers.append('LIBRARY_TYPE_MISMATCH:'+d['id']);continue
        if det is None or any(det[k] is None for k in ('azimuth','elevation')):
            if flame:blockers.append('ORIENTATION:'+d['id']);continue
            det=det or {'azimuth':0.,'elevation':0.,'roll':0.}
        if e['source']['data_status']==EXAMPLE_STATUS:review.append('EXAMPLE_LIBRARY_VALUES:'+e['id'])
        elif e['source']['data_status']!='MANUFACTURER DATA - verified by engineer':review.append('LIBRARY_DATA_TO_BE_VERIFIED:'+e['id'])
        if flame:
            f=setup['flame']
            if _norm(e['fuel_or_gas'])!=_norm(f['fuel']):blockers.append('FUEL_MISMATCH:'+d['id']+' library '+e['fuel_or_gas']+' vs target '+f['fuel'])
            if f['fire_size_scaling']=='NONE' and abs(e['target_fire']['heat_release_kw']-f['heat_release_kw'])>1e-9:blockers.append('FIRE_SIZE_MISMATCH:'+d['id']+' (select INVERSE_SQUARE scaling explicitly or use a matching entry)')
            if f['fire_size_scaling']=='INVERSE_SQUARE':review.append('INVERSE_SQUARE_FIRE_SIZE_SCALING:'+zone_id)
        else:
            if _norm(e['fuel_or_gas'])!=_norm(setup['gas']['gas']):blockers.append('GAS_MISMATCH:'+d['id']+' library '+e['fuel_or_gas']+' vs cloud '+setup['gas']['gas'])
        receiver=None
        if d['detector_type']=='OPEN_PATH':
            try:receiver=resolve_receiver(session,json.loads(a['receiver_json']))
            except CaseError:blockers.append('RECEIVER:'+d['id']);continue
            if receiver is None:blockers.append('RECEIVER:'+d['id']);continue
        mount=w.row(session,'detector_mount',d['id'])
        if mount:
            from fgmapping.services.mounts import mount_status
            if mount_status(session,mount)!='CURRENT_SOURCE':blockers.append('STALE_OR_MISSING_MOUNT:'+d['id'])
        lib[e['id']]=e
        dets.append({'id':d['id'],'detector_type':d['detector_type'],'position':[float(d['x']),float(d['y']),float(d['z'])],'azimuth':float(det['azimuth']),'elevation':float(det['elevation']),'roll':float(det['roll'] or 0.),'library_id':e['id'],'receiver':None if receiver is None else list(receiver)})
    if not dets and not any(b.startswith('LIBRARY_ENTRY_NOT_ASSIGNED') for b in blockers):blockers.append('NO_ELIGIBLE_DETECTORS:'+zone_id)
    if len(dets)<setup['voting_required'] and not blockers:blockers.append('VOTING_EXCEEDS_ASSIGNED_DETECTORS:'+zone_id)
    excluded=sorted(x['component_id'] for x in basis['exclusions']) if basis else []
    files={name:hashlib.sha256((SRC/name).read_bytes()).hexdigest() for name in IMPLEMENTATION}
    from fgmapping import __version__
    from fgmapping.engine.coverage import METHOD_VERSION
    envelope={'method':setup['method'],'method_version':METHOD_VERSION[setup['method']],'zone':{**zone,'low':list(zone['low']),'high':list(zone['high'])},'setup':setup,'detectors':dets,'library':lib,
              'scene_sha256':scene.sha256 if scene else None,'excluded_component_ids':excluded,'software_version':__version__,'implementation_files':files,'implementation_sha256':content_hash(files)}
    return (None if blockers else envelope),sorted(set(blockers)),sorted(set(review))

def coverage_readiness(session):
    require_coverage(session);out={}
    for z in zones(session):
        if zone_setup(session,z['id']) is None:out[z['id']]={'status':'NOT CONFIGURED','blockers':[],'review':[]};continue
        env,b,r=gather(session,z['id']);out[z['id']]={'status':'READY' if env else 'BLOCKED','blockers':b,'review':r}
    return out

# ---------------- runs ----------------
def prepare_run(session,zone_id,run_id):
    require_coverage(session)
    if not run_id.strip() or session.con.execute('SELECT 1 FROM coverage_run WHERE id=?',(run_id,)).fetchone():raise CaseError('RUN_ID','New explicit run ID required')
    env,blockers,review=gather(session,zone_id)
    if env is None:raise CaseError('NOT_READY','Coverage inputs incomplete for '+zone_id+': '+'; '.join(blockers))
    return env,review,get_scene(session)

def compute(env,scene,cancel=None,progress=None,sensitivity=False):
    """Pure computation from a frozen input envelope (safe to run off the UI thread)."""
    from fgmapping.engine.detection import engineering_flame_coverage,engineering_gas_coverage
    if scene is None or scene.sha256!=env['scene_sha256']:raise CaseError('SCENE','Scene changed since the run was prepared')
    fn=engineering_flame_coverage if env['method']=='FLAME_GEOGRAPHIC' else engineering_gas_coverage
    return fn(zone={**env['zone'],'low':tuple(env['zone']['low']),'high':tuple(env['zone']['high'])},setup=env['setup'],detectors=env['detectors'],library=env['library'],scene=scene,excluded_component_ids=env['excluded_component_ids'],cancel=cancel,progress=progress,sensitivity=sensitivity)

def store_run(session,run_id,env,review,result,samples,actor):
    """Persist a computed run; refused if inputs changed while computing."""
    now,_,_=gather(session,env['zone']['id'])
    if now is None or content_hash(now)!=content_hash(env):raise CaseError('STALE_INPUTS','Inputs changed during the calculation; result discarded - run again')
    result=dict(result,review=review,input_hash=content_hash(env),run_id=run_id)
    with session.con:
        session.con.execute('INSERT INTO coverage_run(id,kind,zone_id,method,method_version,input_hash,input_json,result_json,samples_json,actor,utc,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
            (run_id,env['zone']['kind'],env['zone']['id'],env['method'],env['method_version'],content_hash(env),canonical(env),canonical(result),canonical(samples),actor,utc_now(),'CURRENT'))
        session._log(actor,'RUN_COVERAGE',{'id':run_id,'zone':env['zone']['id'],'input_hash':content_hash(env),'method':env['method_version']},{'retain':'Coverage run history retained; input changes mark it stale'})
    session._dirty=True
    return result

def run_zone(session,zone_id,run_id,actor,cancel=None,progress=None,sensitivity=False):
    if not actor.strip():raise CaseError('ACTOR','Named engineer/actor required')
    env,review,scene=prepare_run(session,zone_id,run_id)
    result,samples=compute(env,scene,cancel,progress,sensitivity)
    return store_run(session,run_id,env,review,result,samples,actor)

def run_all(session,prefix,actor,cancel=None,progress=None,sensitivity=False):
    out={}
    for z,st in coverage_readiness(session).items():
        if st['status']=='READY':out[z]=run_zone(session,z,prefix+'-'+z,actor,cancel,progress,sensitivity)
    return out

RUN_COLUMNS=('id','kind','zone_id','method','method_version','input_hash','input_json','result_json','samples_json','actor','utc','status','label')
def runs(session,zone_id=None):
    require_coverage(session)
    q='SELECT '+','.join(RUN_COLUMNS)+' FROM coverage_run'+(' WHERE zone_id=?' if zone_id else '')+' ORDER BY utc,id'
    return [dict(zip(RUN_COLUMNS,r)) for r in session.con.execute(q,(zone_id,) if zone_id else ())]

def run_currency(session,run):
    """CURRENT only when the recomputed input envelope hash still matches."""
    env,_,_=gather(session,run['zone_id'])
    return 'CURRENT' if env is not None and content_hash(env)==run['input_hash'] else 'STALE'

def latest_runs(session):
    out={}
    for r in runs(session):out[r['zone_id']]=r
    return out
