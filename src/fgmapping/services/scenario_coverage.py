"""Rev G M5 services: user scenario sets and candidate layout options, stored as reproducible
runs (coverage_run rows with method SCENARIO_COVERAGE / LAYOUT_OPTIONS). Never mutates the
detector layout. COMPUTED - UNREVIEWED development results - not independently verified."""
from __future__ import annotations
import json,math
from fgmapping.domain.scene import canonical,content_hash
from fgmapping.errors import CaseError
from fgmapping.engine.scenarios import decimal
from fgmapping.services import coverage as cov
from fgmapping.services import workspace as w
from fgmapping.services.case import utc_now
from fgmapping.services.geometry import get_scene
SCENARIO_CONTRACT='fg-coverage-scenarios/1';OPTIONS_CONTRACT='fg-coverage-options/1'
STUDY_METHODS=('SCENARIO_COVERAGE','LAYOUT_OPTIONS')

def _err(msg):raise CaseError('CONTRACT',msg)
def _finite(x):return not isinstance(x,bool) and isinstance(x,(int,float)) and math.isfinite(x)
def _pos(v):return _finite(v) and 0<v<1000
def _xyz(v,name):
    # F18: NaN / +-inf rejected at contract entry
    if not isinstance(v,list) or len(v)!=3 or any(not _finite(x) for x in v):_err(name+' must be [x,y,z] finite numbers in metres')
    return [float(x) for x in v]
def _dec(v,name):
    try:d=decimal(v)
    except Exception:_err(name+' must be a decimal string')
    if not d.is_finite():_err(name+' must be finite')
    return d

def validate_scenarios(p):
    if not isinstance(p,dict) or p.get('contract')!=SCENARIO_CONTRACT:_err('Contract '+SCENARIO_CONTRACT+' required')
    if set(p)-{'contract','scenarios','notes'}:_err('Unknown keys: '+', '.join(sorted(set(p)-{'contract','scenarios','notes'})))
    sc=p.get('scenarios')
    if not isinstance(sc,list) or not sc or len(sc)>5000:_err('1-5000 scenarios required')
    out=[];ids=set()
    for s in sc:
        if not isinstance(s,dict) or set(s)-{'id','zone_id','location','frequency_per_year','frequency_source','cloud','notes'}:_err('Scenario keys: id, zone_id, location, frequency_per_year, frequency_source, cloud (optional), notes')
        if not str(s.get('id','')).strip() or s['id'] in ids:_err('Unique scenario IDs required')
        ids.add(s['id'])
        if not isinstance(s.get('frequency_per_year'),str):_err(s['id']+': frequency_per_year must be a decimal string (user-supplied)')
        f=_dec(s['frequency_per_year'],s['id']+': frequency_per_year')
        if f<0:_err(s['id']+': negative frequency')
        if not str(s.get('frequency_source','')).strip() or s['frequency_source'].strip().upper()=='NOT SUPPLIED':_err(s['id']+': frequency_source required')
        cloud=s.get('cloud')
        if cloud is not None:
            ok=isinstance(cloud,dict) and ((cloud.get('shape')=='SPHERE' and set(cloud)=={'shape','diameter_m'} and _pos(cloud['diameter_m'])) or
                (cloud.get('shape')=='ELLIPSOID' and set(cloud)=={'shape','axes_m'} and isinstance(cloud['axes_m'],list) and len(cloud['axes_m'])==3 and all(_pos(a) for a in cloud['axes_m'])))
            if not ok:_err(s['id']+': cloud must be {shape:SPHERE,diameter_m>0} or {shape:ELLIPSOID,axes_m:[a,b,c]>0}')
            cloud=dict(cloud,**({'diameter_m':float(cloud['diameter_m'])} if cloud['shape']=='SPHERE' else {'axes_m':[float(a) for a in cloud['axes_m']]}))
        out.append({'id':s['id'],'zone_id':str(s.get('zone_id','')),'location':_xyz(s.get('location'),s['id']+' location'),'frequency_per_year':s['frequency_per_year'],'frequency_source':s['frequency_source'],'cloud':cloud,'notes':str(s.get('notes',''))})
    return {'contract':SCENARIO_CONTRACT,'scenarios':out,'notes':str(p.get('notes',''))}

def validate_options(p):
    keys={'contract','zone_id','include_existing','max_detectors','required_votes','grid_spacing_m','candidates','notes'}
    if not isinstance(p,dict) or p.get('contract')!=OPTIONS_CONTRACT:_err('Contract '+OPTIONS_CONTRACT+' required')
    if set(p)-keys:_err('Unknown keys: '+', '.join(sorted(set(p)-keys)))
    if type(p.get('include_existing')) is not bool:_err('include_existing must be true/false')
    if type(p.get('max_detectors')) is not int or not 0<=p['max_detectors']<=16:_err('max_detectors 0-16 required')
    if type(p.get('required_votes')) is not int or not 1<=p['required_votes']<=3:_err('required_votes 1-3 required')
    g=p.get('grid_spacing_m')
    if g is not None and (isinstance(g,bool) or not isinstance(g,(int,float)) or not 0.05<=g<=10):_err('grid_spacing_m 0.05-10 or null')
    c=p.get('candidates')
    if not isinstance(c,list) or not 1<=len(c)<=16:_err('1-16 candidates required (exhaustive enumeration)')
    out=[];ids=set()
    for x in c:
        ck={'id','detector_type','position','azimuth','elevation','roll','library_id','receiver','cost','feasible','maintainable','notes'}
        if not isinstance(x,dict) or set(x)-ck:_err('Candidate keys: '+', '.join(sorted(ck)))
        if not str(x.get('id','')).strip() or x['id'] in ids:_err('Unique candidate IDs required')
        ids.add(x['id'])
        if x.get('detector_type') not in ('FLAME','POINT_GAS','OPEN_PATH'):_err(x['id']+': detector_type FLAME/POINT_GAS/OPEN_PATH')
        for k in ('azimuth','elevation','roll'):
            if not _finite(x.get(k,0.0)):_err(x['id']+': '+k+' must be a finite number')
        if not -180<=x.get('azimuth',0.)<=180 or not -90<=x.get('elevation',0.)<=90 or not -180<=x.get('roll',0.)<=180:_err(x['id']+': azimuth -180..180, elevation -90..90 and roll -180..180 required')
        if not isinstance(x.get('cost'),str):_err(x['id']+': cost must be a decimal string (user-supplied)')
        if _dec(x['cost'],x['id']+': cost')<0:_err(x['id']+': negative cost')
        if type(x.get('feasible')) is not bool or type(x.get('maintainable')) is not bool:_err(x['id']+': feasible and maintainable must be explicit true/false')
        rec=x.get('receiver')
        if x['detector_type']=='OPEN_PATH':rec=_xyz(rec,x['id']+' receiver')
        elif rec is not None:_err(x['id']+': receiver only for OPEN_PATH')
        out.append({'id':x['id'],'detector_type':x['detector_type'],'position':_xyz(x.get('position'),x['id']+' position'),'azimuth':float(x.get('azimuth',0.)),'elevation':float(x.get('elevation',0.)),'roll':float(x.get('roll',0.)),
                    'library_id':str(x.get('library_id','')),'receiver':rec,'cost':x['cost'],'feasible':x['feasible'],'maintainable':x['maintainable'],'notes':str(x.get('notes',''))})
    return {'contract':OPTIONS_CONTRACT,'zone_id':str(p.get('zone_id','')),'include_existing':p['include_existing'],'max_detectors':p['max_detectors'],'required_votes':p['required_votes'],'grid_spacing_m':None if g is None else float(g),'candidates':out,'notes':str(p.get('notes',''))}

def _envs(session,zone_ids):
    envs={}
    for z in sorted(set(zone_ids)):
        env,blockers,review=cov.gather(session,z)
        if env is None:raise CaseError('NOT_READY','Zone '+z+' not READY: '+'; '.join(blockers))
        envs[z]=env
    return envs

def _layout_hash(session):
    """Fingerprint of the baseline layout tables; must be identical before and after a study run."""
    return content_hash({t:[[str(x) for x in r] for r in session.con.execute('SELECT * FROM '+t+' ORDER BY 1')] for t in ('detectors','detector_details','detector_library_assignment')})

def _store(session,run_id,kind,zone_id,method,version,envelope,result,actor):
    if not actor.strip():raise CaseError('ACTOR','Named engineer/actor required')
    if not run_id.strip() or session.con.execute('SELECT 1 FROM coverage_run WHERE id=?',(run_id,)).fetchone():raise CaseError('RUN_ID','New explicit run ID required')
    h=content_hash(envelope);result=dict(result,input_hash=h,run_id=run_id)
    with session.con:
        session.con.execute('INSERT INTO coverage_run(id,kind,zone_id,method,method_version,input_hash,input_json,result_json,samples_json,actor,utc,status,label) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (run_id,kind,zone_id,method,version,h,canonical(envelope),canonical(result),'{}',actor,utc_now(),'CURRENT',cov.LIFECYCLE_LABEL))
        session._log(actor,'RUN_'+method,{'id':run_id,'zone':zone_id,'input_hash':h,'method':version},{'retain':'Study run retained; baseline detector layout unchanged'})
    session._dirty=True
    return result

def scenario_envelope(session,payload):
    payload=validate_scenarios(payload);cov.require_coverage(session)
    envs=_envs(session,[s['zone_id'] for s in payload['scenarios']])
    from fgmapping.engine.scenario_coverage import SCENARIO_METHOD
    files,impl=cov.fingerprint('SCENARIO_COVERAGE')  # F08: study dependency closure
    return {'method':'SCENARIO_COVERAGE','method_version':SCENARIO_METHOD,'payload':payload,'zones':envs,'study_implementation_files':files,'study_implementation_sha256':impl}

def run_scenarios(session,payload,run_id,actor,cancel=None):
    from fgmapping.engine.scenario_coverage import scenario_coverage
    env=scenario_envelope(session,payload);before=_layout_hash(session)
    result=scenario_coverage(env['zones'],get_scene(session),env['payload'],cancel)
    assert _layout_hash(session)==before
    return _store(session,run_id,'SCENARIO_SET',','.join(sorted(env['zones'])),'SCENARIO_COVERAGE',env['method_version'],env,result,actor)

def options_envelope(session,payload):
    payload=validate_options(payload);cov.require_coverage(session)
    env=_envs(session,[payload['zone_id']])[payload['zone_id']];setup=env['setup'];lib=cov.library(session)
    flame=setup['method']=='FLAME_GEOGRAPHIC';types={'FLAME'} if flame else set(setup['gas']['detector_types'])
    existing={d['id'] for d in w.detector_rows(session)};used={}
    for c in payload['candidates']:
        if c['id'] in existing:_err(c['id']+': candidate ID duplicates an existing detector (candidates are proposals, not edits)')
        if c['detector_type'] not in types:_err(c['id']+': type '+c['detector_type']+' not used by zone method')
        e=lib.get(c['library_id'])
        if e is None:_err(c['id']+': library entry '+c['library_id']+' not in case library (F03: no generic default)')
        if e['detector_type']!=c['detector_type']:_err(c['id']+': library type mismatch')
        if flame:
            if cov._norm(e['fuel_or_gas'])!=cov._norm(setup['flame']['fuel']):_err(c['id']+': library fuel differs from zone target fuel')
            if setup['flame']['fire_size_scaling']=='NONE' and abs(e['target_fire']['heat_release_kw']-setup['flame']['heat_release_kw'])>1e-9:_err(c['id']+': library fire size differs from zone target (select INVERSE_SQUARE explicitly)')
        elif cov._norm(e['fuel_or_gas'])!=cov._norm(setup['gas']['gas']):_err(c['id']+': library gas differs from zone cloud gas')
        used[e['id']]=e
    from fgmapping.engine.scenario_coverage import OPTIONS_METHOD
    for c in payload['candidates']:
        from fgmapping.domain.compatibility import detector_blockers
        bad=detector_blockers(setup,lib[c['library_id']],c)  # F13: same central check
        if bad:_err(c['id']+': '+'; '.join(bad))
    files,impl=cov.fingerprint('LAYOUT_OPTIONS')
    return {'method':'LAYOUT_OPTIONS','method_version':OPTIONS_METHOD,'payload':payload,'zone':env,'candidate_library':used,'study_implementation_files':files,'study_implementation_sha256':impl}

def run_options(session,payload,run_id,actor,cancel=None):
    from fgmapping.engine.scenario_coverage import layout_options
    env=options_envelope(session,payload);before=_layout_hash(session)
    result=layout_options(env['zone'],get_scene(session),dict(env['payload'],_library=env['candidate_library']),cancel)
    assert _layout_hash(session)==before
    return _store(session,run_id,'LAYOUT_OPTIONS',env['payload']['zone_id'],'LAYOUT_OPTIONS',env['method_version'],env,result,actor)

# F16: split prepare (GUI thread, DB) / compute (worker thread, no DB) / store (GUI thread, DB, re-validated)
def prepare_study(session,kind,payload):
    env=scenario_envelope(session,payload) if kind=='SCENARIO_COVERAGE' else options_envelope(session,payload)
    return {'kind':kind,'env':env,'scene':get_scene(session),'layout_hash':_layout_hash(session),'input_hash':content_hash(env)}

def compute_study(job,cancel=None):
    from fgmapping.engine.scenario_coverage import scenario_coverage,layout_options
    env=job['env']
    if job['kind']=='SCENARIO_COVERAGE':return scenario_coverage(env['zones'],job['scene'],env['payload'],cancel)
    return layout_options(env['zone'],job['scene'],dict(env['payload'],_library=env['candidate_library']),cancel)

def store_study(session,job,run_id,result,actor):
    env=job['env'];kind=job['kind']
    now=scenario_envelope(session,env['payload']) if kind=='SCENARIO_COVERAGE' else options_envelope(session,env['payload'])
    if content_hash(now)!=job['input_hash'] or _layout_hash(session)!=job['layout_hash']:raise CaseError('STALE_INPUTS','Inputs changed during the study calculation; result discarded - run again')
    if kind=='SCENARIO_COVERAGE':return _store(session,run_id,'SCENARIO_SET',','.join(sorted(env['zones'])),'SCENARIO_COVERAGE',env['method_version'],env,result,actor)
    return _store(session,run_id,'LAYOUT_OPTIONS',env['payload']['zone_id'],'LAYOUT_OPTIONS',env['method_version'],env,result,actor)

RUN_COLUMNS=cov.RUN_COLUMNS
def study_runs(session,method=None):
    cov.require_coverage(session)
    q='SELECT '+','.join(RUN_COLUMNS)+' FROM coverage_run WHERE method IN (?,?)'+(' AND method=?' if method else '')+' ORDER BY utc,id'
    return [dict(zip(RUN_COLUMNS,r)) for r in session.con.execute(q,STUDY_METHODS+((method,) if method else ()))]

def study_run_currency(session,run):
    try:
        payload=json.loads(run['input_json'])['payload']
        env=scenario_envelope(session,payload) if run['method']=='SCENARIO_COVERAGE' else options_envelope(session,payload)
    except CaseError:return 'STALE'
    return 'CURRENT' if content_hash(env)==run['input_hash'] else 'STALE'

def scenario_template(session):
    zs=[z for z in cov.zones(session)]
    return {'contract':SCENARIO_CONTRACT,'notes':'User-supplied scenarios; frequencies and sources must come from the project study.','scenarios':[{'id':'SC-001','zone_id':zs[0]['id'] if zs else 'ZONE','location':[0.0,0.0,1.0],'frequency_per_year':'NOT SUPPLIED','frequency_source':'NOT SUPPLIED','notes':''}]}

def options_template(session):
    zs=[z for z in cov.zones(session)]
    return {'contract':OPTIONS_CONTRACT,'zone_id':zs[0]['id'] if zs else 'ZONE','include_existing':True,'max_detectors':2,'required_votes':2,'grid_spacing_m':1.0,'notes':'Candidates are proposals only.',
            'candidates':[{'id':'CAND-01','detector_type':'FLAME','position':[0.0,0.0,5.0],'azimuth':0.0,'elevation':-30.0,'roll':0.0,'library_id':'LIBRARY-ID','receiver':None,'cost':'1','feasible':True,'maintainable':True,'notes':''}]}
