"""WP03 candidate evidence-linked engineering records; no acceptance promotion."""
from __future__ import annotations
import json,math,sqlite3
from fgmapping.domain.scene import vector,canonical
from fgmapping.errors import CaseError

def add_record(session,id,kind,payload,evidence_id,actor):
    if not isinstance(id,str) or not id.strip():raise CaseError('IDENTITY','Record identity required')
    if kind not in ('EQUIPMENT','FIRE_ZONE','GAS_ZONE','TARGET'):raise CaseError('KIND','Unsupported engineering record kind')
    if kind in ('FIRE_ZONE','GAS_ZONE'):
        lo=vector(payload.get('low',()));hi=vector(payload.get('high',()))
        if any(a>=b for a,b in zip(lo,hi)):raise CaseError('ZONE','Ordered metre bounds required')
        if payload.get('units')!='m':raise CaseError('UNITS','Register zone bounds must explicitly use metres')
    if 'position' in payload:vector(payload['position'])
    encoded=canonical(payload)
    try:
        with session.con:
            session.con.execute('INSERT INTO engineering_record(id,kind,payload_json,evidence_id) VALUES(?,?,?,?)',(id,kind,encoded,evidence_id))
            session._log(actor,'ADD_RECORD',{'id':id,'kind':kind,'payload':payload,'evidence_id':evidence_id},{'delete_id':id})
            session.con.execute("UPDATE calculation_run SET calculation_status='STALE'")
    except sqlite3.IntegrityError as exc:raise CaseError('RECORD_CONFLICT','Duplicate ID or missing evidence; record not added') from exc
    session._dirty=True

def records(session,kind=None):
    query='SELECT id,kind,payload_json,evidence_id,review_status FROM engineering_record';args=()
    if kind:query+=' WHERE kind=?';args=(kind,)
    return [{'id':id,'kind':k,'payload':json.loads(p),'evidence_id':e,'review_status':r} for id,k,p,e,r in session.con.execute(query+' ORDER BY id',args)]

def _detector_state(session,id):
    from fgmapping.services.geometry import get_scene
    row=session.con.execute('SELECT x,y,z,review_status FROM detectors WHERE id=?',(id,)).fetchone()
    if row is None:raise CaseError('MISSING','Detector not found')
    details=session.con.execute('SELECT azimuth,elevation,roll FROM detector_details WHERE detector_id=?',(id,)).fetchone()
    scene=get_scene(session)
    return {'id':id,'position':list(row[:3]),'orientation':None if details is None else list(details),'review_status':row[3],'scene':None if scene is None else scene.to_dict()}

def _apply_detector_state(session,state):
    from fgmapping.services.geometry import _put
    session.con.execute('UPDATE detectors SET x=?,y=?,z=?,review_status=? WHERE id=?',(*state['position'],state['review_status'],state['id']))
    if state['orientation'] is None:
        session.con.execute('DELETE FROM detector_details WHERE detector_id=?',(state['id'],))
    else:
        session.con.execute('INSERT INTO detector_details(detector_id,azimuth,elevation,roll) VALUES(?,?,?,?) ON CONFLICT(detector_id) DO UPDATE SET azimuth=excluded.azimuth,elevation=excluded.elevation,roll=excluded.roll',(state['id'],*state['orientation']))
    _put(session,state['scene'])

def edit_detector(session,id,position,orientation,actor):
    from fgmapping.domain.scene import Scene,Mesh
    if session.con.execute('PRAGMA user_version').fetchone()[0]==3 and session.con.execute('SELECT 1 FROM detector_mount WHERE detector_id=?',(id,)).fetchone():raise CaseError('MOUNTED_EDIT','Use explicit mount editing or detach first')
    position=vector(position);orientation=vector(orientation)
    if not -180<=orientation[0]<=180 or not -90<=orientation[1]<=90 or not -180<=orientation[2]<=180:raise CaseError('ORIENTATION','Azimuth/roll [-180,180], elevation [-90,90] required')
    old=_detector_state(session,id)
    new={**old,'position':list(position),'orientation':list(orientation),'review_status':'CANDIDATE'}
    if old['scene']:
        scene=Scene.from_dict(old['scene']);payload=scene.to_dict()
        # Explicit shared persistent ID and DETECTOR semantic only; no tag guessing.
        for component in payload['components']:
            if component['id']==id and component['semantic']=='DETECTOR':
                frame=scene.frame(component['frame_id']);delta=tuple(position[i]-old['position'][i] for i in range(3))
                component['mesh']['vertices']=[frame.local(tuple(frame.world(p)[i]+delta[i] for i in range(3))) for p in component['mesh']['vertices']]
        payload['source_revision']+=' | detector-edit '+id
        new['scene']=Scene.from_dict(payload).to_dict()
    with session.con:
        _apply_detector_state(session,new)
        session._log(actor,'EDIT_DETECTOR',new,old)
    session._dirty=True

def detector_history(session,actor,redo=False):
    from fgmapping.domain.scene import canonical
    rows=session.con.execute("SELECT event_id,command,forward_json,inverse_json FROM ledger WHERE command IN ('EDIT_DETECTOR','UNDO_DETECTOR_EDIT','REDO_DETECTOR_EDIT') ORDER BY event_id").fetchall()
    undo=[];redos=[];originals={}
    for id,command,fwd,inv in rows:
        fwd=json.loads(fwd);inv=json.loads(inv)
        if command=='EDIT_DETECTOR':originals[id]=(fwd,inv);undo.append(id);redos=[]
        elif command=='UNDO_DETECTOR_EDIT':
            if undo and undo[-1]==fwd['target']:redos.append(undo.pop())
        elif command=='REDO_DETECTOR_EDIT':
            if redos and redos[-1]==fwd['target']:undo.append(redos.pop())
    stack=redos if redo else undo
    if not stack:raise CaseError('UNDO_EMPTY','No detector edit available')
    target=stack[-1];fwd,inv=originals[target];expected=inv if redo else fwd;state=fwd if redo else inv
    current=_detector_state(session,state['id'])
    if canonical(current)!=canonical(expected):raise CaseError('UNDO_CONFLICT','Detector or linked scene changed since this command; history refused')
    with session.con:
        _apply_detector_state(session,state)
        session._log(actor,'REDO_DETECTOR_EDIT' if redo else 'UNDO_DETECTOR_EDIT',{'target':target,'state':state},{'state':current},True)
    session._dirty=True

def store_attachment(session,raw,format,frame,manifest,evidence_id,actor):
    import hashlib
    sha=hashlib.sha256(raw).hexdigest()
    if len(raw)>4000000 or sha!=manifest['source_sha256']:raise CaseError('SOURCE_HASH','Source bytes changed or exceed budget')
    with session.con:
        session.con.execute('INSERT OR IGNORE INTO geometry_attachment VALUES(?,?,?,?,?,?)',(sha,raw,format,canonical(frame),canonical(manifest),evidence_id))
        session._log(actor,'STORE_GEOMETRY_SOURCE',{'source_sha256':sha,'evidence_id':evidence_id},{'retain':'Source evidence is retained, not silently deleted'})
    session._dirty=True
