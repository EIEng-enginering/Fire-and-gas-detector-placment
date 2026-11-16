"""Independent piecewise-linear concentration integral convergence exercise."""
import json,math
from fgmapping.engine.concentration import ConcentrationField
axis=[0,1.3,4];other=[0,1];times=[0,1]
values=[min(2*x,2.6) for t in times for z in other for y in other for x in axis]
f=ConcentrationField(tuple(axis),tuple(other),tuple(other),tuple(times),tuple(values),'0'*64,'SYN-A','Synthetic piecewise C=min(2x,2.6) ppm')
# Independent exact area: triangle (1.3*2.6/2) + rectangle (4-1.3)*2.6.
exact=8.71;rows=[]
for n in (2,4,8,16,32,64,128):
 result=f.beam_integral((0,.5,.5),(4,.5,.5),.5,n)['ppm_m'];rows.append({'subdivisions':n,'ppm_m':result,'absolute_error_ppm_m':abs(result-exact)})
assert rows[-1]['absolute_error_ppm_m']<.0003 and rows[-1]['absolute_error_ppm_m']<rows[0]['absolute_error_ppm_m']
print(json.dumps({'label':'SYNTHETIC numerical exercise / not gas detector coverage','exact_ppm_m':exact,'source_basis':f.evidence_locator,'results':rows,'qualification':'UNVERIFIED'},indent=2))
