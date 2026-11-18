"""Rev G M5: scenario-based coverage and candidate layout options (proposals only).

Scenario coverage: each user scenario (location + user-supplied frequency and source) is tested
with the same geographic detection rule as its zone (FG-FLAME-GEO/1.0 or FG-GAS-GEO/1.0) and the
frequency-weighted detected fraction is aggregated exactly with Decimal (engine.scenarios).
It is NOT risk reduction, availability or SIL credit.

Layout options: user candidate positions (with library entries, costs and feasibility) are tested
against the zone grid; the exhaustive Pareto enumeration (engine.optimisation, <=16 candidates)
returns PROPOSALS ONLY. Nothing here persists or changes the detector layout.
Engineer-reviewed results - not independently certified.
"""
from __future__ import annotations
from fgmapping.engine.coverage import (Obstructions,_prepare_detectors,_flame_votes,_gas_votes,discretise,_classify,LABEL)
from fgmapping.engine.scenarios import SyntheticScenario,aggregate,decimal
from fgmapping.engine.optimisation import SyntheticMount,enumerate_layouts
SCENARIO_METHOD='FG-SCENARIO/1.0';OPTIONS_METHOD='FG-OPTIONS/1.0'

def _plain(x):
    d=decimal(x).normalize();return format(d,'f') if d!=0 else '0'

def _dets(env):
    return [dict(d,position=tuple(d['position']),receiver=None if d.get('receiver') is None else tuple(d['receiver'])) for d in env['detectors']]

def _votes(points,dets,setup,obs,findings):
    if setup['method']=='FLAME_GEOGRAPHIC':return _flame_votes(points,dets,setup,obs)
    return _gas_votes(points,dets,setup,obs,findings=findings)

def scenario_coverage(envs,scene,payload,cancel=None):
    """envs: {zone_id: frozen zone envelope}. Returns the result dict (Decimal strings for aggregates)."""
    rows=[];agg=[];findings=[];by_zone={}
    obs_cache={}
    for sc in payload['scenarios']:
        if cancel and cancel():raise RuntimeError('Cancelled')
        env=envs[sc['zone_id']];setup=dict(env['setup'])
        if sc.get('cloud'):
            setup=dict(setup,gas=dict(setup['gas'],cloud=sc['cloud']))
        key=(sc['zone_id'],tuple(env['excluded_component_ids']))
        if key not in obs_cache:obs_cache[key]=Obstructions(scene,env['excluded_component_ids'],setup['tolerance_m'])
        obs=obs_cache[key];dets=_prepare_detectors(_dets(env),env['library']);p=tuple(float(v) for v in sc['location'])
        inside=obs.inside(p) or obs.inside_excluded(p)
        if inside:
            votes=[];status='LOCATION INSIDE SOLID '+inside+' - not detectable in this method (move the scenario point)'
            findings.append({'severity':'REVIEW','scenario':sc['id'],'text':status})
        else:
            f=[];votes=_votes([(p,1.0)],dets,setup,obs,f)[0][2];status='EVALUATED'
            for x in f:
                if x['severity']=='BLOCKING' and not any(y.get('detector')==x['detector'] and y['text']==x['text'] for y in findings):findings.append(dict(x,first_scenario=sc['id']))
        detected=len(votes)>=setup['voting_required']
        rows.append({'id':sc['id'],'zone_id':sc['zone_id'],'location':list(p),'frequency_per_year':sc['frequency_per_year'],'frequency_source':sc['frequency_source'],
                     'detectors_responding':[dets[i]['id'] for i in votes],'votes':len(votes),'voting_required':setup['voting_required'],'detected':detected,'status':status})
        row=SyntheticScenario(sc['id'],sc['frequency_per_year'],'1' if detected else '0',sc['frequency_source'],'Geographic detection test '+env['method_version']+' zone '+sc['zone_id'])
        agg.append(row);by_zone.setdefault(sc['zone_id'],[]).append(row)
    a=aggregate(agg)
    def clean(x):return {'frequency_weighted_detected_fraction':x['frequency_weighted_detection_fraction'],'detected_count_fraction':x['unweighted_mean_detection_probability'],'total_frequency_per_year':x['total_frequency_per_year']}
    return {'method_version':SCENARIO_METHOD,'label':LABEL,'scenario_count':len(rows),'overall':clean(a),'by_zone':{z:clean(aggregate(r)) for z,r in sorted(by_zone.items())},
            'scenarios':rows,'findings':findings,'frequency_units':'1/year','not_calculated':['risk reduction','availability','SIL credit','response time'],
            'basis':'Frequencies and their sources are user-supplied; detection is the deterministic geographic test of the scenario zone.'}

def layout_options(env,scene,payload,cancel=None):
    """Exhaustive candidate enumeration over the zone grid. Returns proposals only."""
    setup=env['setup'];spacing=payload.get('grid_spacing_m') or setup['grid_spacing_m']
    obs=Obstructions(scene,env['excluded_component_ids'],setup['tolerance_m'])
    samples=discretise(tuple(env['zone']['low']),tuple(env['zone']['high']),spacing,setup['mode'],setup['slice_elevations_m'])
    eligible,excl,_=_classify(samples,obs)
    if not eligible:raise ValueError('No eligible volume in zone')
    findings=[]
    base={}
    if payload['include_existing']:
        rows=_votes(eligible,_prepare_detectors(_dets(env),env['library']),setup,obs,findings)
        base={str(i):len(v) for i,(_,_,v) in enumerate(rows)}
    mounts=[];incid={}
    for c in sorted(payload['candidates'],key=lambda c:c['id']):
        if cancel and cancel():raise RuntimeError('Cancelled')
        d=_prepare_detectors([dict(c,position=tuple(c['position']),receiver=None if c.get('receiver') is None else tuple(c['receiver']))],payload['_library'])
        f=[];rows=_votes(eligible,d,setup,obs,f)
        vis=frozenset(str(i) for i,(_,_,v) in enumerate(rows) if v)
        findings+=[dict(x,candidate=c['id']) for x in f if x['severity']=='BLOCKING']
        incid[c['id']]=len(vis)
        mounts.append(SyntheticMount(c['id'],vis,c['cost'],bool(c['feasible']),bool(c['maintainable'])))
    weights={str(i):repr(w) for i,(_,w) in enumerate(eligible)}
    out=enumerate_layouts(mounts,weights,payload['max_detectors'],payload['required_votes'],base if payload['include_existing'] else None)
    existing=None
    if payload['include_existing']:
        tot=sum(decimal(w) for w in weights.values());existing=_plain(sum((decimal(weights[k]) for k,v in base.items() if v>=payload['required_votes']),decimal('0'))/tot)
    return {'method_version':OPTIONS_METHOD,'label':LABEL,'status':'PROPOSALS ONLY - the baseline detector layout is unchanged; adopt a proposal only through normal, reviewed detector edits',
            'zone_id':env['zone']['id'],'grid_spacing_m':spacing,'eligible_samples':len(eligible),'required_votes':payload['required_votes'],'include_existing':payload['include_existing'],
            'existing_layout_fraction':existing,'candidate_visible_samples':incid,'enumerated':out['enumerated'],'pareto':[dict(a,fraction=_plain(a['fraction'])) for a in out['pareto']],'findings':findings,
            'note':'Costs, feasibility and maintainability are user-supplied; exhaustive enumeration limited to 16 candidates.'}
