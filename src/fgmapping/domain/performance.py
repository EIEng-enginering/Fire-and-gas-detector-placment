"""Closed synthetic detector performance-data preparation contract.

Validating this record is NOT vendor verification or a detector response method.
There is no interpolation, extrapolation, conformity or qualification function.
"""
import json,math,hashlib
from fgmapping.domain.scene import canonical,content_hash

KEYS={'contract','data_class','manufacturer','model','revision','sensitivity','source','conditions','units','samples'}
def validate_dataset(payload):
 if not isinstance(payload,dict) or set(payload)!=KEYS or payload['contract']!='fg-performance-preparation/1' or payload['data_class']!='SYNTHETIC':raise ValueError('Closed synthetic performance preparation contract required; project/vendor data needs separate authorisation')
 for key in ('manufacturer','model','revision','sensitivity'):
  if not isinstance(payload[key],str) or payload[key].strip().upper() in ('','NOT SUPPLIED'):raise ValueError('Explicit performance '+key+' required')
 source=payload['source']
 if not isinstance(source,dict) or set(source)!={'title','revision','locator','sha256','licence_basis'} or any(not isinstance(v,str) or not v.strip() for v in source.values()):raise ValueError('Complete source title/revision/locator/hash/licence basis required')
 if len(source['sha256'])!=64 or any(c not in '0123456789abcdef' for c in source['sha256']):raise ValueError('Source SHA256 required')
 if payload['units']!={'distance':'m','angle':'deg','response_time':'s'}:raise ValueError('Explicit metres/degrees/seconds required; no inferred conversion')
 conditions=payload['conditions']
 if not isinstance(conditions,dict) or set(conditions)!={'fuel_or_gas','target_description','environment_reference','method_scope'} or any(not isinstance(v,str) or not v.strip() for v in conditions.values()):raise ValueError('Explicit target/fuel/environment and scope required')
 if conditions['method_scope']!='PREPARATION ONLY / NO ENGINEERING RESPONSE':raise ValueError('Preparation dataset cannot declare engineering response')
 samples=payload['samples']
 if not isinstance(samples,list) or not 1<=len(samples)<=2000:raise ValueError('1..2000 explicit samples required')
 seen=set()
 for s in samples:
  if not isinstance(s,dict) or set(s)!={'azimuth_deg','elevation_deg','range_m','response_time_s','source_locator'}:raise ValueError('Closed response sample fields required')
  vals=[s[k] for k in ('azimuth_deg','elevation_deg','range_m','response_time_s')]
  if any(type(v) not in (int,float) or not math.isfinite(v) for v in vals) or not -180<=vals[0]<=180 or not -90<=vals[1]<=90 or min(vals[2:])<0 or not isinstance(s['source_locator'],str) or not s['source_locator'].strip():raise ValueError('Finite explicit sample values/locators required')
  key=tuple(vals[:3])
  if key in seen:raise ValueError('Duplicate angular/range response sample')
  seen.add(key)
 return json.loads(canonical(payload))

def parse_dataset(raw):
 if len(raw)>4_000_000:raise ValueError('Performance source exceeds 4 MB development budget')
 text=raw.decode('utf-8',errors='strict');payload=validate_dataset(json.loads(text))
 return {'payload':payload,'raw_text':text,'import_sha256':hashlib.sha256(raw).hexdigest(),'content_sha256':content_hash(payload),'qualification':'UNVERIFIED'}

def exact_source_sample(payload,azimuth_deg,elevation_deg,range_m,conditions):
    """Return only an explicitly supplied source row; never a detection decision."""
    payload=validate_dataset(payload)
    if canonical(conditions)!=canonical(payload['conditions']):raise ValueError('Source conditions differ; substitution is not permitted')
    values=(azimuth_deg,elevation_deg,range_m)
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in values):raise ValueError('Finite exact query coordinates required')
    match=next((s for s in payload['samples'] if (s['azimuth_deg'],s['elevation_deg'],s['range_m'])==values),None)
    if match is None:raise ValueError('No supplied source row at this condition; interpolation and extrapolation are not implemented')
    return {'label':'SOURCE PREPARATION ROW ONLY / NOT DETECTOR RESPONSE','sample':match,'source':payload['source'],'qualification':'UNVERIFIED'}
