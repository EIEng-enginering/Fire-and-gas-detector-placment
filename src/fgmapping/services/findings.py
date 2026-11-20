"""Deterministic preparation findings; no standards compliance or acceptance score."""
import json
from fgmapping.services.geometry import get_scene
from fgmapping.services.workspace import detector_rows,row

def study_findings(session):
 findings=[]
 def add(id,object_id,severity,message):findings.append({'id':id,'object_id':object_id,'severity':severity,'message':message,'status':'OPEN','qualification':'UNVERIFIED'})
 scene=get_scene(session);components={c.id for c in scene.components} if scene else set()
 if not scene:add('GEO-NOT-SUPPLIED','STUDY','BLOCKING','No facility geometry supplied')
 else:add('GEO-UNVERIFIED','STUDY','REVIEW','Self-intersections, CAD fidelity and engineering obstruction roles remain unverified')
 for d in detector_rows(session):
  id=d['id'];details=row(session,'detector_details',id)
  if session.con.execute('PRAGMA user_version').fetchone()[0]>=4:
   a=row(session,'detector_library_assignment',id)
   if a is None:add('LIBRARY-'+id,id,'BLOCKING','No detector library entry assigned; this detector cannot contribute to engineering coverage')
   else:
    e=json.loads(row(session,'detector_library',a['library_id'])['payload_json'])
    if e['source']['data_status'].startswith('EXAMPLE'):add('LIBRARY-EXAMPLE-'+id,id,'REVIEW','Assigned library entry '+e['id']+' carries EXAMPLE VALUES; replace with verified manufacturer data before project use')
  else:add('PERFORMANCE-'+id,id,'BLOCKING','No implemented authorised manufacturer response dataset; engineering coverage unavailable')
  if details is None:add('ORIENTATION-'+id,id,'REVIEW','Detector orientation not supplied')
  if id not in components:add('PLACEMENT-'+id,id,'REVIEW','No explicit shared-ID detector geometry marker; stored register coordinates remain available')
 for id,kind,payload in session.con.execute('SELECT id,kind,payload_json FROM engineering_record ORDER BY id'):
  p=json.loads(payload)
  if p.get('geometry_component_id') and p['geometry_component_id'] not in components:add('ORPHAN-'+id,id,'BLOCKING','Referenced geometry component is absent from the current scene')
  if kind in ('FIRE_ZONE','GAS_ZONE') and p.get('criteria','NOT SUPPLIED') in ('','NOT SUPPLIED'):add('BASIS-'+id,id,'BLOCKING','Zone design criterion reference not supplied')
 for id,status in session.con.execute('SELECT id,calculation_status FROM calculation_run ORDER BY id'):
  if status=='STALE':add('STALE-'+id,id,'REVIEW','Calculation inputs changed; retained result is stale')
 if session.con.execute('PRAGMA user_version').fetchone()[0]>=3:
  from fgmapping.services.basis import readiness
  r=readiness(session)
  for i,item in enumerate(r['missing']):add('READINESS-MISSING-'+str(i),'STUDY','BLOCKING','Missing input: '+item)
  for i,item in enumerate(r['blocking']):add('READINESS-BLOCK-'+str(i),'STUDY','BLOCKING',item)
 if session.con.execute('PRAGMA user_version').fetchone()[0]>=4:
  from fgmapping.services import coverage as cov
  for z,r in cov.latest_runs(session).items():
   res=json.loads(r['result_json'])
   if cov.run_currency(session,r)=='STALE':add('COVERAGE-STALE-'+z,z,'REVIEW','Latest coverage run '+r['id']+' is stale; inputs changed since it was computed')
   for k,t in res['performance_targets'].items():
    if t['status']=='BELOW USER TARGET':add('COVERAGE-TARGET-'+z+'-'+k,z,'REVIEW','%s %s achieved %.1f %% is below the user target %s' % (z,k,100*t['achieved'],t['target']))
   st=res['convergence']['status']
   if st.startswith(('GRID DISAGREEMENT','UNRESOLVED FEATURE','NOT EVALUABLE','NOT CONVERGED')):add('COVERAGE-GRID-'+z,z,'REVIEW','Grid check for '+z+': '+st+('; '+'; '.join(res['convergence'].get('unresolved_features',[])) if res['convergence'].get('unresolved_features') else ''))
   if res.get('measure_error_bound'):add('COVERAGE-MEASURE-BOUND-'+z,z,'REVIEW','%s: approximate partial-cell measure for non-box meshes; rigorous bound %.4g %s' % (z,res['measure_error_bound'],res['measure_unit']))
   if res.get('unsampled_free_measure'):add('COVERAGE-UNSAMPLED-'+z,z,'REVIEW','%s: %.4g %s of free measure could not be sampled at this grid and is excluded from eligible measure' % (z,res['unsampled_free_measure'],res['measure_unit']))
   for i,f in enumerate(res['findings']):add('COVERAGE-RUN-'+z+'-'+str(i),f.get('detector',z),f['severity'],f['text'])
 return findings
