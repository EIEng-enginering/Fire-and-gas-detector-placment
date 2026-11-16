"""Atomic candidate workspace commands with durable conflict-aware undo/redo.

Existing legacy APIs remain available; the Rev C GUI uses these commands. Source
attachments/calculation history are retained as evidence and not erased by undo.
"""
from __future__ import annotations
import json,math
from fgmapping.domain.scene import canonical,vector,Scene,Mesh,Component,Frame,box_mesh,content_hash
from fgmapping.errors import CaseError

TABLES={
'evidence':('id','kind','description','document_revision','location_ref','data_class'),
'detectors':('id','detector_type','x','y','z','evidence_id','review_status'),
'detector_details':('detector_id','azimuth','elevation','roll','manufacturer','model','sensitivity'),
'engineering_record':('id','kind','payload_json','evidence_id','review_status'),
'geometry_scene':('id','payload_json','sha256','status'),
'detector_mount':('detector_id','component_id','anchor_local_json','offset_m_json','orientation_local_json','component_fingerprint','evidence_id','status'),
'study_basis':('id','payload_json','evidence_id','status'),
'performance_dataset':('id','payload_json','import_sha256','raw_text','status'),
'detector_performance_link':('detector_id','dataset_id','evidence_id','status'),
'preparation_review':('id','subject_kind','subject_id','subject_hash','decision','reviewer','rationale','evidence_id','utc')}

def row(session,table,key):
    cols=TABLES[table];r=session.con.execute('SELECT '+','.join(cols)+' FROM '+table+' WHERE '+cols[0]+'=?',(key,)).fetchone()
    return None if r is None else dict(zip(cols,r))

def change(session,table,key,after):
    if after is not None:
        after=dict(after)
        fields={'detectors':('x','y','z'),'detector_details':('azimuth','elevation','roll')}.get(table,())
        for field in fields:after[field]=float(after[field])
    return {'table':table,'key':key,'before':row(session,table,key),'after':after}

def execute(session,changes,actor,description):
    if not isinstance(actor,str) or not actor.strip():raise CaseError('ACTOR','Named editor or explicit automation actor required')
    if session.con.execute('PRAGMA user_version').fetchone()[0] not in (2,3):raise CaseError('MIGRATION_REQUIRED','Enable candidate geometry schema first')
    if not changes:return
    if len({(c['table'],c['key']) for c in changes})!=len(changes):raise CaseError('COMMAND','One change per entity per command required')
    with session.con:
        _apply(session,changes)
        session._log(actor,'WORKSPACE_EDIT',{'description':description,'changes':changes},{'changes':_inverse(changes)})
    session._dirty=True

def _inverse(changes):return [{**c,'before':c['after'],'after':c['before']} for c in reversed(changes)]

def _apply(session,changes):
    for c in changes:
        if c['table'] not in TABLES:raise CaseError('COMMAND','Unknown workspace entity')
        if canonical(row(session,c['table'],c['key']))!=canonical(c['before']):raise CaseError('EDIT_CONFLICT','Record changed since this command was prepared')
        if c['after'] is not None and set(c['after'])!=set(TABLES[c['table']]):raise CaseError('COMMAND','Closed row schema required')
        if c['after'] is not None and c['table'] in ('detector_mount','study_basis','performance_dataset','detector_performance_link') and c['after']['status']!='CANDIDATE':raise CaseError('QUALIFICATION_GATE','Preparation entities cannot be promoted by a workspace command')
    for c in changes:
        cols=TABLES[c['table']];value=c['after']
        if value is None:session.con.execute('DELETE FROM '+c['table']+' WHERE '+cols[0]+'=?',(c['key'],))
        else:
            session.con.execute('INSERT INTO '+c['table']+'('+','.join(cols)+') VALUES('+','.join('?' for _ in cols)+') ON CONFLICT('+cols[0]+') DO UPDATE SET '+','.join(col+'=excluded.'+col for col in cols[1:]),tuple(value[col] for col in cols))
    session.con.execute("UPDATE calculation_run SET calculation_status='STALE'")

def history(session,actor,redo=False):
    events=session.con.execute("SELECT event_id,command,forward_json FROM ledger WHERE command IN ('WORKSPACE_EDIT','WORKSPACE_UNDO','WORKSPACE_REDO') ORDER BY event_id").fetchall()
    undo=[];redos=[];originals={}
    for id,cmd,payload in events:
        p=json.loads(payload)
        if cmd=='WORKSPACE_EDIT':originals[id]=p['changes'];undo.append(id);redos=[]
        elif cmd=='WORKSPACE_UNDO' and undo and undo[-1]==p['target']:redos.append(undo.pop())
        elif cmd=='WORKSPACE_REDO' and redos and redos[-1]==p['target']:undo.append(redos.pop())
    stack=redos if redo else undo
    if not stack:raise CaseError('UNDO_EMPTY','No workspace command available')
    target=stack[-1];changes=originals[target] if redo else _inverse(originals[target])
    with session.con:
        _apply(session,changes)
        session._log(actor,'WORKSPACE_REDO' if redo else 'WORKSPACE_UNDO',{'target':target,'changes':changes},{'changes':_inverse(changes)},True)
    session._dirty=True

def synthetic_evidence(id,description,revision,locator):
    if not all(isinstance(x,str) and x.strip() for x in (id,description,revision,locator)):raise CaseError('EVIDENCE','Evidence ID, description, revision and locator are required')
    return dict(zip(TABLES['evidence'],(id,'MANUAL_SYNTHETIC',description,revision,locator,'SYNTHETIC')))

def detector_rows(session):
    return [dict(zip(TABLES['detectors'],r)) for r in session.con.execute('SELECT '+','.join(TABLES['detectors'])+' FROM detectors ORDER BY id')]

def detector_plan(session,values,evidence,*,create=False,place_marker=False,mount_update=False):
    id=values['id'];old=row(session,'detectors',id)
    if session.con.execute('PRAGMA user_version').fetchone()[0]==3 and row(session,'detector_mount',id) and not mount_update:raise CaseError('MOUNTED_EDIT','Detach or edit the explicit mount before changing this detector')
    if not isinstance(id,str) or not id.strip() or any(ord(c)<32 for c in id):raise CaseError('IDENTITY','Detector ID must be nonblank and contain no control characters')
    if create and old is not None or not create and old is None:raise CaseError('IDENTITY','Detector ID already exists or was not found')
    if values['detector_type'] not in ('FLAME','POINT_GAS','OPEN_PATH','ULTRASONIC'):raise CaseError('TYPE','Unknown detector type')
    position=vector(tuple(values[k] for k in ('x','y','z')))
    orientation=vector(tuple(values.get(k,0.) for k in ('azimuth','elevation','roll')))
    if not -180<=orientation[0]<=180 or not -90<=orientation[1]<=90 or not -180<=orientation[2]<=180:raise CaseError('ORIENTATION','Azimuth/roll [-180,180], elevation [-90,90] required')
    changes=[];eid=values['evidence_id']
    existing=row(session,'evidence',eid)
    if existing is None:
        if evidence is None or evidence['id']!=eid:raise CaseError('EVIDENCE','Select existing evidence or supply complete synthetic evidence')
        changes.append(change(session,'evidence',eid,evidence))
    elif evidence is not None and canonical(evidence)!=canonical(existing):raise CaseError('EVIDENCE_CONFLICT','Existing evidence is immutable in this editor; use a new evidence revision ID')
    detector=dict(zip(TABLES['detectors'],(id,values['detector_type'],*position,eid,'CANDIDATE')))
    changes.append(change(session,'detectors',id,detector))
    details=dict(zip(TABLES['detector_details'],(id,*orientation,*[str(values.get(k,'NOT SUPPLIED')).strip() or 'NOT SUPPLIED' for k in ('manufacturer','model','sensitivity')])))
    changes.append(change(session,'detector_details',id,details))
    scene_row=row(session,'geometry_scene',1)
    if scene_row:
        scene=Scene.from_dict(json.loads(scene_row['payload_json']));payload=json.loads(canonical(scene.to_dict()));found=False
        for component in payload['components']:
            if component['id']==id and component['semantic']=='DETECTOR':
                if old is None:raise CaseError('GEOMETRY_CONFLICT','Geometry ID exists without an explicit detector relationship')
                f=scene.frame(component['frame_id']);delta=tuple(position[i]-old[k] for i,k in enumerate(('x','y','z')))
                component['mesh']['vertices']=[f.local(tuple(f.world(p)[i]+delta[i] for i in range(3))) for p in component['mesh']['vertices']];component['evidence_id']=eid;found=True
        if place_marker and not found:
            if any(c.id==id for c in scene.components):raise CaseError('GEOMETRY_CONFLICT','Component ID already used by another object')
            if 'PLACEMENT_SI' not in [f.id for f in scene.frames]:payload['frames'].append({'id':'PLACEMENT_SI','units':'m','datum':'Explicit manual synthetic detector placement','handedness':'RIGHT','matrix':Frame('PLACEMENT_SI','m','Synthetic').matrix})
            component=Component(id,'Candidate detector '+id,'DETECTOR','PLACEMENT_SI',box_mesh(position,tuple(x+.2 for x in position)),eid)
            from dataclasses import asdict
            payload['components'].append(asdict(component));found=True
        if found:
            payload['source_revision']+=' | workspace '+id;newscene=Scene.from_dict(payload)
            changes.append(change(session,'geometry_scene',1,{'id':1,'payload_json':canonical(newscene.to_dict()),'sha256':newscene.sha256,'status':'UNVERIFIED'}))
    elif place_marker:
        from dataclasses import asdict
        scene=Scene((Frame('PLACEMENT_SI','m','Explicit manual synthetic detector placement'),),(Component(id,'Candidate detector '+id,'DETECTOR','PLACEMENT_SI',box_mesh(position,tuple(x+.2 for x in position)),eid),),'MANUAL_SYNTHETIC',content_hash(values))
        changes.append(change(session,'geometry_scene',1,{'id':1,'payload_json':canonical(scene.to_dict()),'sha256':scene.sha256,'status':'UNVERIFIED'}))
    return changes

def detector_command(session,values,evidence,actor,*,create=False,place_marker=False):
    changes=detector_plan(session,values,evidence,create=create,place_marker=place_marker)
    execute(session,changes,actor,('Add' if create else 'Edit')+' detector '+values['id'])

def record_command(session,id,kind,payload,evidence_id,actor,*,create=False):
    old=row(session,'engineering_record',id)
    if not id.strip() or kind not in ('EQUIPMENT','FIRE_ZONE','GAS_ZONE','TARGET'):raise CaseError('RECORD','Explicit ID and known kind required')
    if create and old is not None or not create and old is None:raise CaseError('IDENTITY','Record already exists or is missing')
    if old and old['kind']!=kind:raise CaseError('KIND','Record kind cannot be silently changed')
    if row(session,'evidence',evidence_id) is None:raise CaseError('EVIDENCE','Evidence not found')
    if kind in ('FIRE_ZONE','GAS_ZONE'):
        low=vector(payload.get('low',()));high=vector(payload.get('high',()))
        if payload.get('units')!='m' or any(a>=b for a,b in zip(low,high)):raise CaseError('ZONE','Ordered explicit SI metre bounds required')
    if 'position' in payload:vector(payload['position'])
    if payload.get('geometry_component_id'):
        scene=row(session,'geometry_scene',1)
        if not scene or payload['geometry_component_id'] not in {c.id for c in Scene.from_dict(json.loads(scene['payload_json'])).components}:raise CaseError('GEOMETRY','Selected geometry component not found')
    record=dict(zip(TABLES['engineering_record'],(id,kind,canonical(payload),evidence_id,'CANDIDATE')))
    execute(session,[change(session,'engineering_record',id,record)],actor,('Add ' if create else 'Edit ')+kind+' '+id)

def remove_record(session,id,actor):
    if row(session,'engineering_record',id) is None:raise CaseError('MISSING','Record not found')
    execute(session,[change(session,'engineering_record',id,None)],actor,'Remove study record '+id+'; retained in ledger')

def paste_detectors(session,patches,actor):
    """Atomic numeric/type paste into existing detectors; no implicit new IDs or evidence."""
    ids=set();changes=[]
    stored_scene=row(session,'geometry_scene',1)
    scene=Scene.from_dict(json.loads(stored_scene['payload_json'])) if stored_scene else None
    payload=json.loads(canonical(scene.to_dict())) if scene else None
    moved=False
    for patch in patches:
        id=patch['id']
        if session.con.execute('PRAGMA user_version').fetchone()[0]==3 and row(session,'detector_mount',id):raise CaseError('MOUNTED_EDIT','Edit the explicit mount rather than pasting a mounted detector')
        if id in ids:raise CaseError('PASTE','Duplicate detector in paste')
        ids.add(id);before=row(session,'detectors',id)
        if before is None:raise CaseError('MISSING','Paste only edits existing detector IDs')
        if set(patch)-{'id','x','y','z','detector_type'}:raise CaseError('PASTE','Paste supports type and XYZ only')
        after={**before,**patch,'review_status':'CANDIDATE'}
        vector(tuple(after[k] for k in ('x','y','z')))
        if after['detector_type'] not in ('FLAME','POINT_GAS','OPEN_PATH','ULTRASONIC'):raise CaseError('TYPE','Invalid pasted detector type')
        if scene:
            for component in payload['components']:
                if component['id']==id and component['semantic']=='DETECTOR':
                    frame=scene.frame(component['frame_id']);delta=tuple(after[k]-before[k] for k in ('x','y','z'))
                    component['mesh']['vertices']=[frame.local(tuple(frame.world(p)[i]+delta[i] for i in range(3))) for p in component['mesh']['vertices']];moved=True
        changes.append(change(session,'detectors',id,after))
    if moved:
        payload['source_revision']+=' | detector paste';newscene=Scene.from_dict(payload)
        changes.append(change(session,'geometry_scene',1,{'id':1,'payload_json':canonical(newscene.to_dict()),'sha256':newscene.sha256,'status':'UNVERIFIED'}))
    execute(session,changes,actor,'Paste detector cells')


def display_annotations(session):
    """Explicit stored placements/zones for display; no response/FOV inferred."""
    from fgmapping.domain.pose import direction
    placements=[]
    for d in detector_rows(session):
        details=row(session,'detector_details',d['id'])
        placements.append({'id':d['id'],'position':[d['x'],d['y'],d['z']],'direction':None if details is None else direction(details['azimuth'],details['elevation'])})
    zones=[]
    for id,kind,payload in session.con.execute("SELECT id,kind,payload_json FROM engineering_record WHERE kind IN ('FIRE_ZONE','GAS_ZONE') ORDER BY id"):
        p=json.loads(payload);zones.append({'id':id,'kind':kind,'low':p['low'],'high':p['high']})
    return {'placements':placements,'zones':zones}

def remove_detector(session,id,actor):
    old=row(session,'detectors',id)
    if old is None:raise CaseError('MISSING','Detector not found')
    changes=[]
    if session.con.execute('PRAGMA user_version').fetchone()[0]==3:
        for table in ('detector_mount','detector_performance_link'):
            if row(session,table,id):changes.append(change(session,table,id,None))
    if row(session,'detector_details',id) is not None:changes.append(change(session,'detector_details',id,None))
    changes.append(change(session,'detectors',id,None))
    stored=row(session,'geometry_scene',1)
    if stored:
        scene=Scene.from_dict(json.loads(stored['payload_json']))
        if any(c.id==id and c.semantic=='DETECTOR' for c in scene.components):
            if any(c.parent_id==id for c in scene.components):raise CaseError('REFERENCED','Detector geometry has child components; detach them before removal')
            for (payload,) in session.con.execute('SELECT payload_json FROM engineering_record'):
                if json.loads(payload).get('geometry_component_id')==id:raise CaseError('REFERENCED','A study record references the detector geometry; detach it before removal')
            from dataclasses import replace
            remaining=replace(scene,components=tuple(c for c in scene.components if c.id!=id),source_revision=scene.source_revision+' | remove '+id)
            changes.append(change(session,'geometry_scene',1,{'id':1,'payload_json':canonical(remaining.to_dict()),'sha256':remaining.sha256,'status':'UNVERIFIED'}))
    execute(session,changes,actor,'Remove detector and its explicit marker '+id+'; source evidence retained')
