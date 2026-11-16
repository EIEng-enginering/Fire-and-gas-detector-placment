"""Synthetic rectilinear concentration/time field and numerical beam integration.

Not CFD or an engineering gas detector model. Explicit source identity, axes,
units, time and bounded values are required; extrapolation is refused.
"""
from dataclasses import dataclass
from bisect import bisect_right
import math
from fgmapping.domain.scene import vector,content_hash

@dataclass(frozen=True)
class ConcentrationField:
    x:tuple
    y:tuple
    z:tuple
    times_s:tuple
    ppm:tuple
    source_sha256:str
    revision:str
    evidence_locator:str
    def __post_init__(self):
        for axis in (self.x,self.y,self.z,self.times_s):
            if not 2<=len(axis)<=1000 or any(type(v) not in (int,float) or not math.isfinite(v) for v in axis) or any(a>=b for a,b in zip(axis,axis[1:])):raise ValueError('At least two finite strictly increasing axis/time coordinates required')
        if self.times_s[0]<0:raise ValueError('Nonnegative time axis required')
        count=len(self.x)*len(self.y)*len(self.z)*len(self.times_s)
        if count>200000 or len(self.ppm)!=count:raise ValueError('Field shape differs from axes or exceeds development budget')
        if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in self.ppm):raise ValueError('Finite nonnegative concentration ppm required')
        if len(self.source_sha256)!=64 or any(c not in '0123456789abcdef' for c in self.source_sha256) or not self.revision.strip() or not self.evidence_locator.strip():raise ValueError('Source hash/revision/locator required')
    @classmethod
    def from_dict(cls,payload):
        keys={'contract','data_class','axes_units','concentration_units','time_units','x','y','z','times_s','ppm','source_sha256','revision','evidence_locator','layout'}
        if set(payload)!=keys or payload['contract']!='fg-synthetic-field/1' or payload['data_class']!='SYNTHETIC' or payload['axes_units']!='m' or payload['concentration_units']!='ppm' or payload['time_units']!='s' or payload['layout']!='t,z,y,x':raise ValueError('Closed synthetic field contract with explicit SI axes, seconds and ppm required')
        return cls(*(tuple(payload[k]) for k in ('x','y','z','times_s','ppm')),payload['source_sha256'],payload['revision'],payload['evidence_locator'])
    def sample(self,position,time_s):
        position=vector(position)
        if not isinstance(time_s,(int,float)) or not math.isfinite(time_s):raise ValueError('Finite time required')
        indices=[];fractions=[]
        for axis,value in zip((self.times_s,self.z,self.y,self.x),(time_s,position[2],position[1],position[0])):
            if not axis[0]<=value<=axis[-1]:raise ValueError('Outside field envelope; extrapolation refused')
            i=min(len(axis)-2,bisect_right(axis,value)-1);indices.append(i);fractions.append((value-axis[i])/(axis[i+1]-axis[i]))
        total=[];nt,nz,ny,nx=len(self.times_s),len(self.z),len(self.y),len(self.x)
        for mask in range(16):
            idx=[];weight=1.
            for k in range(4):
                bit=(mask>>k)&1;idx.append(indices[k]+bit);weight*=fractions[k] if bit else 1-fractions[k]
            t,z,y,x=idx;total.append(weight*self.ppm[((t*nz+z)*ny+y)*nx+x])
        return math.fsum(total)
    def beam_integral(self,start,end,time_s,subdivisions):
        start=vector(start);end=vector(end)
        if type(subdivisions) is not int or not 2<=subdivisions<=10000 or subdivisions%2:raise ValueError('Explicit even Simpson subdivisions 2..10000 required')
        length=math.dist(start,end)
        if length==0:raise ValueError('Positive beam length required')
        values=[self.sample(tuple(start[k]+(end[k]-start[k])*i/subdivisions for k in range(3)),time_s) for i in range(subdivisions+1)]
        integral=length/(3*subdivisions)*math.fsum(v*(1 if i in (0,subdivisions) else 4 if i%2 else 2) for i,v in enumerate(values))
        if not math.isfinite(integral):raise ValueError('Beam integral exceeds finite numerical range')
        return {'metric':'SYNTHETIC concentration beam integral / not detector coverage','ppm_m':integral,'time_s':time_s,'subdivisions':subdivisions,'source_sha256':self.source_sha256,'qualification':'UNVERIFIED'}

def first_order_step_response(initial_ppm,final_ppm,tau_s,elapsed_s):
    """Synthetic specified first-order step exercise, not a manufacturer response."""
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in (initial_ppm,final_ppm,tau_s,elapsed_s)) or min(initial_ppm,final_ppm,elapsed_s)<0 or tau_s<=0:raise ValueError('Explicit finite nonnegative readings/time and positive supplied tau required')
    return final_ppm+(initial_ppm-final_ppm)*math.exp(-elapsed_s/tau_s)
