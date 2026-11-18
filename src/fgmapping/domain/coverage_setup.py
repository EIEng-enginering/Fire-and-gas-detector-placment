"""Per-zone coverage setup contract fg-coverage-setup/1 (Rev G).

Every value is engineer-supplied: grid, target fire / design gas cloud, voting and
the performance targets used for comparison. Nothing is defaulted and no pass
percentage is embedded in the software (F05).
"""
from __future__ import annotations
import json,math
from decimal import Decimal
from fgmapping.domain.scene import canonical

CONTRACT='fg-coverage-setup/1'
KEYS={'contract','zone_id','method','grid_spacing_m','mode','slice_elevations_m','voting_required','performance_targets','convergence','criterion_reference','standoff_m','tolerance_m','flame','gas','notes'}
TARGET_KEYS=('1ooN','2ooN','3ooN')
FLAME_KEYS={'fuel','heat_release_kw','fire_size_scaling','target_geometry','min_visible_fraction'}
GAS_KEYS={'gas','cloud','cloud_concentration_pct_lel','detector_types'}

def _num(v,name,low=None,high=None,positive=False):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError('Coverage setup '+name+' must be a finite number')
    if positive and v<=0 or low is not None and v<low or high is not None and v>high:raise ValueError('Coverage setup '+name+' out of range')
    return float(v)

def validate_setup(p):
    if not isinstance(p,dict) or set(p)!=KEYS or p['contract']!=CONTRACT:raise ValueError('Closed coverage setup contract fg-coverage-setup/1 required')
    if not isinstance(p['zone_id'],str) or not p['zone_id'].strip():raise ValueError('Zone ID required')
    if p['method'] not in ('FLAME_GEOGRAPHIC','GAS_GEOGRAPHIC'):raise ValueError('Method must be FLAME_GEOGRAPHIC or GAS_GEOGRAPHIC')
    _num(p['grid_spacing_m'],'grid_spacing_m',.05,10)
    if p['mode'] not in ('VOLUME','SLICES'):raise ValueError('Mode must be VOLUME or SLICES')
    z=p['slice_elevations_m']
    if not isinstance(z,list) or len(z)>50 or (p['mode']=='SLICES')!=bool(z) or len(set(z))!=len(z):raise ValueError('SLICES mode needs 1..50 unique elevations; VOLUME mode none')
    for v in z:_num(v,'slice elevation')
    if type(p['voting_required']) is not int or not 1<=p['voting_required']<=3:raise ValueError('Explicit voting_required 1..3 required')
    t=p['performance_targets']
    if not isinstance(t,dict) or not set(t)<=set(TARGET_KEYS):raise ValueError('Performance targets keyed 1ooN/2ooN/3ooN only')
    for k,v in t.items():
        if v=='NOT SUPPLIED':continue
        if not isinstance(v,str):raise ValueError('Targets are decimal strings or NOT SUPPLIED')
        d=Decimal(v)
        if not d.is_finite() or not 0<=d<=1:raise ValueError('Target fractions must be in [0,1]')
    c=p['convergence']
    if not isinstance(c,dict) or set(c)!={'refinement','tolerance'} or c['refinement'] not in (1,2,3) or not isinstance(c['tolerance'],str):raise ValueError('Convergence {refinement:1|2|3, tolerance:"0.02"} required (1 = not checked)')
    if not 0<=Decimal(c['tolerance'])<=1:raise ValueError('Convergence tolerance in [0,1]')
    if not isinstance(p['criterion_reference'],str) or not isinstance(p['notes'],str):raise ValueError('Criterion reference/notes are text')
    _num(p['standoff_m'],'standoff_m',0,1);_num(p['tolerance_m'],'tolerance_m',1e-9,.001)
    if p['method']=='FLAME_GEOGRAPHIC':
        f=p['flame']
        if p['gas'] is not None or not isinstance(f,dict) or set(f)!=FLAME_KEYS:raise ValueError('Flame setup requires flame {fuel, heat_release_kw, fire_size_scaling, target_geometry, min_visible_fraction}')
        if not isinstance(f['fuel'],str) or not f['fuel'].strip():raise ValueError('Target fuel required')
        _num(f['heat_release_kw'],'heat_release_kw',positive=True)
        if f['fire_size_scaling'] not in ('NONE','INVERSE_SQUARE'):raise ValueError('fire_size_scaling NONE or INVERSE_SQUARE')
        g=f['target_geometry']
        if not isinstance(g,dict) or g.get('type') not in ('POINT','CYLINDER'):raise ValueError('Target geometry POINT or CYLINDER required')
        if g['type']=='POINT' and set(g)!={'type'}:raise ValueError('POINT target has no dimensions')
        if g['type']=='CYLINDER':
            if set(g)!={'type','diameter_m','height_m','rings','levels'}:raise ValueError('CYLINDER target requires diameter_m, height_m, rings, levels')
            _num(g['diameter_m'],'diameter_m',positive=True,high=50);_num(g['height_m'],'height_m',positive=True,high=50)
            if type(g['rings']) is not int or not 3<=g['rings']<=16 or type(g['levels']) is not int or not 1<=g['levels']<=8:raise ValueError('rings 3..16, levels 1..8')
        _num(f['min_visible_fraction'],'min_visible_fraction',high=1,positive=True)
    else:
        gs=p['gas']
        if p['flame'] is not None or not isinstance(gs,dict) or set(gs)!=GAS_KEYS:raise ValueError('Gas setup requires gas {gas, cloud, cloud_concentration_pct_lel, detector_types}')
        if not isinstance(gs['gas'],str) or not gs['gas'].strip():raise ValueError('Gas identity required')
        cl=gs['cloud']
        if not isinstance(cl,dict) or cl.get('shape') not in ('SPHERE','ELLIPSOID'):raise ValueError('Design cloud SPHERE or ELLIPSOID required')
        if cl['shape']=='SPHERE':
            if set(cl)!={'shape','diameter_m'}:raise ValueError('SPHERE cloud requires diameter_m')
            _num(cl['diameter_m'],'diameter_m',positive=True,high=200)
        else:
            if set(cl)!={'shape','axes_m'} or not isinstance(cl['axes_m'],list) or len(cl['axes_m'])!=3:raise ValueError('ELLIPSOID cloud requires axes_m [x,y,z] full diameters')
            for v in cl['axes_m']:_num(v,'axes_m',positive=True,high=200)
        _num(gs['cloud_concentration_pct_lel'],'cloud_concentration_pct_lel',positive=True,high=1000)
        if not isinstance(gs['detector_types'],list) or not gs['detector_types'] or not set(gs['detector_types'])<={'POINT_GAS','OPEN_PATH'} or len(set(gs['detector_types']))!=len(gs['detector_types']):raise ValueError('Gas detector_types subset of POINT_GAS/OPEN_PATH required')
    return json.loads(canonical(p))
