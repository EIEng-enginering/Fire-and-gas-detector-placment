"""WP02 candidate services. Edits occur in CaseSession-owned local database only."""
import json
import sqlite3
from contextlib import closing
import hashlib
from fgmapping.services.case import utc_now
from pathlib import Path
from fgmapping.domain.scene import Scene, canonical
from fgmapping.errors import CaseError

MIGRATION=Path(__file__).resolve().parents[3]/'contracts/migrations/0002_candidate_geometry.sql'

def enable_geometry(session,actor):
    """Explicit local candidate upgrade, not implicit on open; backup before changes."""
    if not actor.strip(): raise CaseError('ACTOR','Explicit actor required')
    version=session.con.execute('PRAGMA user_version').fetchone()[0]
    if version in (2,3,4):return
    if version!=1: raise CaseError('VERSION','Only v1 to v2 candidate upgrade supported')
    manifest=json.loads((MIGRATION.parent.parent/'candidate_manifest.json').read_text())
    for name,sha in manifest['migrations_sha256'].items():
        if hashlib.sha256((MIGRATION.parent/name).read_bytes()).hexdigest()!=sha:raise CaseError('CONTRACT_HASH','Candidate migration differs from its manifest')
    session._backup()
    # Preserve unsaved pre-upgrade work as well as the original saved case.
    backup=session.runtime/'Backups'/(session.key+'_pre_geometry_'+utc_now().replace(':','-')+'.fgcase')
    with closing(sqlite3.connect(backup)) as dst:session.con.backup(dst)
    try:
        with session.con:
            session.con.execute('BEGIN IMMEDIATE')
            statement=''
            for line in MIGRATION.read_text().splitlines(True):
                statement+=line
                if sqlite3.complete_statement(statement):
                    session.con.execute(statement);statement=''
            if statement.strip():raise CaseError('MIGRATION','Incomplete SQL statement')
            session._log(actor,'ENABLE_GEOMETRY',{'schema':2},{'rollback':'restore pre-upgrade backup; no destructive downgrade'})
    except Exception:
        session.con.rollback();raise
    session._dirty=True

def get_scene(session):
    if session.con.execute('PRAGMA user_version').fetchone()[0]==1: return None
    row=session.con.execute('SELECT payload_json,sha256 FROM geometry_scene WHERE id=1').fetchone()
    if not row:return None
    scene=Scene.from_dict(json.loads(row[0]))
    if scene.sha256!=row[1]: raise CaseError('GEOMETRY_HASH','Stored scene hash does not match its content')
    return scene

def _put(session,payload):
    if payload is None: session.con.execute('DELETE FROM geometry_scene WHERE id=1')
    else:
        scene=Scene.from_dict(payload)
        session.con.execute('INSERT OR REPLACE INTO geometry_scene(id,payload_json,sha256) VALUES(1,?,?)',(canonical(payload),scene.sha256))
    session.con.execute("UPDATE calculation_run SET calculation_status='STALE'")

def set_scene(session,scene,actor):
    if session.con.execute('PRAGMA user_version').fetchone()[0] not in (2,3,4): raise CaseError('MIGRATION_REQUIRED','Explicit candidate schema upgrade required')
    scene=Scene.from_dict(scene.to_dict())
    for evidence in {c.evidence_id for c in scene.components}:
        if not session.con.execute('SELECT 1 FROM evidence WHERE id=?',(evidence,)).fetchone():raise CaseError('EVIDENCE','Geometry evidence not found')
    old=get_scene(session)
    with session.con:
        _put(session,scene.to_dict())
        session._log(actor,'SET_SCENE',{'scene':scene.to_dict()},{'scene':None if old is None else old.to_dict()})
    session._dirty=True

def compensate_scene(session,actor,redo=False):
    commands=session.con.execute("SELECT event_id,command,forward_json,inverse_json FROM ledger WHERE command IN ('SET_SCENE','UNDO_SCENE','REDO_SCENE') ORDER BY event_id").fetchall()
    undo=[]; redos=[]; originals={}
    for id,cmd,fwd,inv in commands:
        fwd=json.loads(fwd); inv=json.loads(inv)
        if cmd=='SET_SCENE': originals[id]=(fwd,inv); undo.append(id); redos=[]
        elif cmd=='UNDO_SCENE':
            if undo and undo[-1]==fwd['target']: redos.append(undo.pop())
        elif cmd=='REDO_SCENE':
            if redos and redos[-1]==fwd['target']: undo.append(redos.pop())
    stack=redos if redo else undo
    if not stack:raise CaseError('UNDO_EMPTY','No scene command available')
    target=stack[-1]; fwd,inv=originals[target]
    payload=(fwd if redo else inv)['scene']; old=get_scene(session)
    expected=(inv if redo else fwd)['scene']
    if canonical(None if old is None else old.to_dict())!=canonical(expected):raise CaseError('UNDO_CONFLICT','Scene changed outside this history; undo/redo refused')
    with session.con:
        _put(session,payload)
        session._log(actor,'REDO_SCENE' if redo else 'UNDO_SCENE',{'target':target,'scene':payload},{'scene':None if old is None else old.to_dict()},True)
    session._dirty=True
