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
  add('PERFORMANCE-'+id,id,'BLOCKING','No implemented authorised manufacturer response dataset; engineering coverage unavailable')
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
 return findings
