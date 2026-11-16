"""WP05/06 numerical exercises and hard engineering refusal boundary.

No manufacturer response or qualified fire/gas study engine is implemented.
All available numerical methods are explicitly SYNTHETIC demonstrations.
"""
from dataclasses import dataclass
import math
from fgmapping.domain.scene import vector

class EngineeringUnavailable(ValueError):pass

def engineering_flame_coverage(*,performance=None,basis=None,**kwargs):
    missing=[]
    if performance is None:missing.append('authorised manufacturer performance dataset')
    if basis is None:missing.append('reviewed extended-fire target and study basis')
    missing.append('independently reviewed flame response method and owner qualification')
    raise EngineeringUnavailable('CANNOT CALCULATE engineering flame coverage: '+', '.join(missing))

def engineering_gas_coverage(*,performance=None,field=None,**kwargs):
    missing=[]
    if performance is None:missing.append('authorised gas sensor response data')
    if field is None:missing.append('reviewed concentration field and units')
    missing.append('independently reviewed gas method and owner qualification')
    raise EngineeringUnavailable('CANNOT CALCULATE engineering gas coverage: '+', '.join(missing))

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
