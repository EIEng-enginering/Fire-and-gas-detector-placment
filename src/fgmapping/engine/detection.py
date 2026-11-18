"""Engineering coverage entry points (Rev G) and WP05/06 synthetic exercises.

Rev G (owner approval 18 Nov 2026): engineering_flame_coverage / engineering_gas_coverage
run the geographic coverage engine (engine/coverage.py) and refuse unless the complete
inputs are supplied. Engineer-reviewed results - not independently certified.
The synthetic exercise functions below remain demonstrations only.
"""
from dataclasses import dataclass
import math
from fgmapping.domain.scene import vector

class EngineeringUnavailable(ValueError):pass

FLAME_REQUIRED=('zone','setup','detectors','library','scene')
def engineering_flame_coverage(*,performance=None,basis=None,**kwargs):
    """Rev G flame geographic coverage (FG-FLAME-GEO/1.0), gated on complete inputs.

    Refuses (EngineeringUnavailable) unless a zone, a validated FLAME coverage setup
    (target fire, grid, voting), detectors each with an explicitly assigned library
    entry carrying a contour table, and facility geometry are all supplied.
    Engineer-reviewed results - not independently certified.
    """
    missing=[k for k in FLAME_REQUIRED if kwargs.get(k) is None]
    if not missing:missing=_check_inputs(kwargs,'FLAME_GEOGRAPHIC')
    if missing:
        missing=['complete coverage inputs: '+', '.join(missing)]
        raise EngineeringUnavailable('CANNOT CALCULATE engineering flame coverage: '+', '.join(missing))
    return _run(kwargs)

def engineering_gas_coverage(*,performance=None,field=None,**kwargs):
    """Rev G geographic gas coverage (FG-GAS-GEO/1.0; design-cloud method, not dispersion)."""
    missing=[k for k in FLAME_REQUIRED if kwargs.get(k) is None]
    if not missing:missing=_check_inputs(kwargs,'GAS_GEOGRAPHIC')
    if missing:raise EngineeringUnavailable('CANNOT CALCULATE engineering gas coverage: complete coverage inputs: '+', '.join(missing))
    return _run(kwargs)

def _check_inputs(kw,method):
    from fgmapping.domain.coverage_setup import validate_setup
    from fgmapping.domain.detector_library import validate_entry
    missing=[]
    try:
        setup=validate_setup(kw['setup'])
        if setup['method']!=method:missing.append('setup method '+method)
    except (ValueError,TypeError,KeyError) as exc:return ['valid coverage setup ('+str(exc)+')']
    lib=kw['library']
    if not isinstance(lib,dict):return ['library entries']
    dets=kw['detectors']
    if not dets:missing.append('detectors')
    for d in dets or ():
        e=lib.get(d.get('library_id')) if isinstance(d,dict) else None
        if e is None:missing.append('explicit library entry for '+str(d.get('id') if isinstance(d,dict) else d));continue
        try:validate_entry(e)
        except (ValueError,TypeError,KeyError):missing.append('valid library entry for '+str(d['id']));continue
        if e['detector_type']!=d.get('detector_type'):missing.append('matching library type for '+d['id'])
        if d.get('detector_type')=='OPEN_PATH' and d.get('receiver') is None:missing.append('open-path receiver for '+d['id'])
    if dets and len(dets)<setup['voting_required']:missing.append('at least voting_required detectors')
    return missing

def _run(kw):
    from fgmapping.engine.coverage import Obstructions,zone_coverage
    from fgmapping.domain.coverage_setup import validate_setup
    setup=validate_setup(kw['setup'])
    obs=Obstructions(kw['scene'],kw.get('excluded_component_ids') or (),setup['tolerance_m'])
    dets=[dict(d,position=tuple(d['position']),receiver=None if d.get('receiver') is None else tuple(d['receiver'])) for d in kw['detectors']]
    return zone_coverage(kw['zone'],setup,dets,kw['library'],obs,kw.get('cancel'),kw.get('progress'),kw.get('sensitivity',False))

def synthetic_weighted_votes(rows,required_votes):
    """Explicit synthetic Boolean responses; cannot infer detector response."""
    rows=tuple(rows)
    if type(required_votes) is not int or required_votes<1 or not rows:raise ValueError('Explicit positive voting and nonempty samples required')
    counts=set();numerator=[];weights=[]
    for id,weight,responses in rows:
        if not id or id in counts:raise ValueError('Unique sample IDs required')
        counts.add(id)
        if not math.isfinite(weight) or weight<=0 or any(type(v) is not bool for v in responses):raise ValueError('Finite positive weights and Boolean responses required')
        weights.append(weight)
        if sum(responses)>=required_votes:numerator.append(weight)
    denominator=math.fsum(weights)
    return {'metric':'SYNTHETIC weighted voting fraction / NOT ENGINEERING COVERAGE','fraction':math.fsum(numerator)/denominator,'eligible_weight':denominator,'required_votes':required_votes,'qualification':'UNVERIFIED'}

@dataclass(frozen=True)
class UniformDesignCloud:
    """Synthetic axis-aligned uniform concentration construct, not dispersion/CFD."""
    low:tuple
    high:tuple
    concentration_ppm:float
    basis:str
    def __post_init__(self):
        lo=vector(self.low);hi=vector(self.high)
        if any(a>=b for a,b in zip(lo,hi)) or not math.isfinite(self.concentration_ppm) or self.concentration_ppm<0 or not self.basis.strip():raise ValueError('Ordered cloud bounds, nonnegative ppm and explicit synthetic basis required')
        object.__setattr__(self,'low',lo);object.__setattr__(self,'high',hi)
    def concentration(self,point):
        point=vector(point)
        return self.concentration_ppm if all(a<=p<=b for a,p,b in zip(self.low,point,self.high)) else 0.
    def path_integral_ppm_m(self,start,end):
        start=vector(start);end=vector(end);delta=tuple(b-a for a,b in zip(start,end))
        length=math.sqrt(sum(x*x for x in delta))
        if length==0:raise ValueError('Open path requires positive beam length')
        from fractions import Fraction
        lower,upper=Fraction(0),Fraction(1)
        for i,d in enumerate(delta):
            if d==0:
                if not self.low[i]<=start[i]<=self.high[i]:return 0.
            else:
                a,b=sorted(((Fraction(str(self.low[i]))-Fraction(str(start[i])))/(Fraction(str(end[i]))-Fraction(str(start[i]))),(Fraction(str(self.high[i]))-Fraction(str(start[i])))/(Fraction(str(end[i]))-Fraction(str(start[i])))))
                lower=max(lower,a);upper=min(upper,b)
                if lower>=upper:return 0.
        value=self.concentration_ppm*length*float(max(0,upper-lower))
        if not math.isfinite(value):raise ValueError('Uniform cloud integral exceeds finite numerical range')
        return value

def synthetic_threshold(reading,threshold,units):
    if units not in ('ppm','ppm*m'):raise ValueError('Only explicit ppm or ppm*m supported; LEL conversion requires gas-specific data')
    if not all(math.isfinite(x) for x in (reading,threshold)) or reading<0 or threshold<=0:raise ValueError('Nonnegative reading and positive threshold required')
    return reading>=threshold
