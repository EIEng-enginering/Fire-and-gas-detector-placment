"""Candidate study input basis and readiness rules. No built-in engineering targets."""
import json,math
from decimal import Decimal
from fgmapping.domain.scene import canonical
KEYS={'contract','revision','study_type','coordinate_reference','target_description','fuel_or_gas','voting','criterion_reference','target_fraction','exclusions','uncertainty_reference'}
def validate_basis(p):
 if not isinstance(p,dict) or set(p)!=KEYS or p['contract']!='fg-study-basis/1' or p['study_type'] not in ('FLAME','GAS','BOTH'):raise ValueError('Closed study basis contract and explicit study type required')
 for key in ('revision','coordinate_reference','target_description','fuel_or_gas','criterion_reference','uncertainty_reference'):
  if not isinstance(p[key],str):raise ValueError('Basis references are text; unknown inputs must remain blank/NOT SUPPLIED')
 if type(p['voting']) is not int or p['voting']<1:raise ValueError('Explicit positive required voting count required')
 target=p['target_fraction']
 if target not in (None,'','NOT SUPPLIED'):
  if not isinstance(target,str):raise ValueError('Explicit decimal target string or NOT SUPPLIED required')
  v=Decimal(target)
  if not v.is_finite() or not 0<=v<=1:raise ValueError('Target fraction must be finite in [0,1]')
 if not isinstance(p['exclusions'],list) or len(p['exclusions'])>10000:raise ValueError('Explicit exclusion records required')
 ids=set()
 for x in p['exclusions']:
  if not isinstance(x,dict) or set(x)!={'component_id','reason','evidence_id'} or any(not isinstance(v,str) or not v.strip() for v in x.values()) or x['component_id'] in ids:raise ValueError('Unique exclusions with reason and evidence required')
  ids.add(x['component_id'])
 return json.loads(canonical(p))
