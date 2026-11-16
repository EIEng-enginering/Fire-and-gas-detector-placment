"""Offline-first prototype case service. One portable SQLite case file per project.

No direct editing of a case stored in a synchronised folder. A local working
copy is locked and saved by an atomic destination replacement.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from uuid import uuid4
from fgmapping.errors import CaseError
from fgmapping.services.file_lock import WriterFence

SCHEMA = Path(__file__).resolve().parents[3] / 'contracts' / 'migrations' / '0001_initial.sql'

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):
            h.update(c)
    return h.hexdigest()

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def fsync_directory(p: Path):
    if os.name != 'nt':
        fd=os.open(str(p),os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)

def fsync_file(p):
    """Flush a closed file's contents to stable storage.

    Windows' fsync (_commit) requires a write-capable descriptor; a read-only
    descriptor fails with EBADF. 'r+b' opens for update without truncation.
    """
    with open(p,'r+b') as f:
        os.fsync(f.fileno())

def atomic_json(path,payload):
    path=Path(path)
    fd,name=tempfile.mkstemp(prefix='.fg_meta_',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf8') as f:
            json.dump(payload,f,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(name,path);fsync_directory(path.parent)
    finally:
        if os.path.exists(name):os.unlink(name)

def create_case(path: str | Path, name: str) -> Path:
    target = Path(path).expanduser().resolve()
    if target.suffix != '.fgcase':
        raise CaseError('EXTENSION', 'Case file must have .fgcase extension')
    if target.exists():
        raise CaseError('EXISTS','File exists; never overwrite an existing project')
    if not name.strip():
        raise CaseError('NAME','Study name is required')
    if not SCHEMA.exists():
        raise CaseError('SCHEMA','Frozen migration not found')
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.fg_new_',suffix='.sqlite',dir=target.parent)
    os.close(fd)
    try:
        con=sqlite3.connect(tmp)
        try:
            con.executescript(SCHEMA.read_text(encoding='utf8'))
            con.execute('INSERT INTO case_info(id,case_uuid,name) VALUES (1,?,?)',(str(uuid4()),name))
            con.commit()
        finally: con.close()
        fsync_file(tmp)
        # Exclusive destination creation; no overwrite race.
        os.link(tmp,target)
        fsync_directory(target.parent)
    except FileExistsError as e:
        raise CaseError('EXISTS','File created concurrently, refused overwrite') from e
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return target

class CaseSession:
    """Single writer session; not safe to share across threads."""
    def __init__(self,path: str|Path,runtime: str|Path,recover: bool=False):
        self.path=Path(path).expanduser().resolve()
        if not self.path.is_file(): raise CaseError('MISSING','Case not found')
        self.runtime=Path(runtime).expanduser().resolve()
        self.runtime.mkdir(parents=True,exist_ok=True)
        for n in ('Sessions','Backups','Locks','Logs'):
            (self.runtime/n).mkdir(exist_ok=True)
        self.key=hashlib.sha256(str(self.path).encode()).hexdigest()[:24]
        self.work=self.runtime/'Sessions'/(self.key+'.sqlite')
        self.lock=self.runtime/'Locks'/(self.key+'.lock')
        self.meta=self.runtime/'Sessions'/(self.key+'.json')
        self._con=None
        self._dirty=False
        self._fence=WriterFence(self.path)
        self._original_sha=digest(self.path)
        # The native fence proves no cooperating writer is active, even if a
        # previous process left runtime metadata. Preserve that stale lock as evidence.
        try:
            if self.lock.exists():
                # Older app versions do not take the native fence. Never quarantine
                # their live runtime lock merely because our native fence succeeded.
                try:pid=json.loads(self.lock.read_text())['pid']
                except (ValueError,KeyError,TypeError):raise CaseError('LOCKED','Runtime lock is malformed; explicit inspection required')
                if type(pid) is not int or pid<=0:raise CaseError('LOCKED','Runtime lock PID is invalid; explicit inspection required')
                from fgmapping.services.process_inspection import process_state,DEAD
                if process_state(pid)!=DEAD:raise CaseError('LOCKED','Runtime lock names a live or uninspectable process; recovery refused')
                stale=self.runtime/'Logs'/(self.key+'_stale_lock_'+uuid4().hex+'.json')
                shutil.copy2(self.lock,stale);self.lock.unlink()
            fd=os.open(str(self.lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'w') as f:
                json.dump({'pid':os.getpid(),'case':str(self.path),'utc':utc_now()},f)
                f.flush();os.fsync(f.fileno())
        except BaseException:
            self._fence.close();raise
        try:
            if self.work.exists():
                self._dirty=True
                if not recover: raise CaseError('RECOVERY_REQUIRED','Unsaved work exists; explicit recovery is required')
                meta=json.loads(self.meta.read_text(encoding='utf8')) if self.meta.exists() else {}
                if meta.get('pending_sha')==self._original_sha and meta.get('work_sha')==digest(self.work):
                    meta={'original_sha':self._original_sha,'case':str(self.path),'reconciled_interrupted_save':utc_now()}
                    atomic_json(self.meta,meta)
                if meta.get('original_sha')!=self._original_sha:
                    raise CaseError('RECOVERY_CONFLICT','Original case changed since the working session')
            else:
                shutil.copy2(self.path,self.work)
                atomic_json(self.meta,{'original_sha':self._original_sha,'case':str(self.path),'created':utc_now()})
            self._con=sqlite3.connect(self.work)
            self._con.execute('PRAGMA foreign_keys=ON')
            if self._con.execute('PRAGMA user_version').fetchone()[0] not in (1,2,3):
                raise CaseError('VERSION','Only schema versions 1 and candidate 2/3 supported; explicit migration required')
            if self._con.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise CaseError('INTEGRITY','SQLite integrity check failed')
            if self._con.execute('PRAGMA foreign_key_check').fetchone() is not None:raise CaseError('REFERENTIAL_INTEGRITY','Case contains broken source/data references; restore a verified backup')
        except BaseException:
            if self._con: self._con.close()
            self.lock.unlink(missing_ok=True)
            self._fence.close()
            raise

    def __enter__(self):return self
    def __exit__(self,*args):self.close()

    @property
    def con(self):
        if self._con is None: raise CaseError('CLOSED','Session is closed')
        return self._con

    def name(self):
        return self.con.execute('SELECT name FROM case_info WHERE id=1').fetchone()[0]

    def _log(self, actor:str,command:str,forward:dict,inverse:dict,comp:bool=False):
        if not actor.strip():raise CaseError('ACTOR','Named editor or explicit automation actor required')
        self.con.execute('INSERT INTO ledger(utc,actor,command,forward_json,inverse_json,is_compensation) VALUES(?,?,?,?,?,?)',(utc_now(),actor,command,json.dumps(forward,sort_keys=True),json.dumps(inverse,sort_keys=True),int(comp)))

    def set_name(self,new_name:str,actor:str):
        if not new_name.strip():raise CaseError('NAME','Study name is required')
        old=self.name()
        with self.con:
            self.con.execute('UPDATE case_info SET name=? WHERE id=1',(new_name,))
            self._log(actor,'SET_NAME',{'name':new_name},{'name':old})
        self._dirty=True

    def undo_last_name(self,actor:str):
        rows=self.con.execute("SELECT event_id,inverse_json FROM ledger WHERE command='SET_NAME' AND is_compensation=0 ORDER BY event_id DESC").fetchall()
        compensated={json.loads(x[0])['undid'] for x in self.con.execute("SELECT forward_json FROM ledger WHERE command='UNDO_NAME'").fetchall()}
        pending=next(((i,j) for i,j in rows if i not in compensated),None)
        if not pending:raise CaseError('UNDO_EMPTY','No remaining name change to undo')
        event_id, inv=pending
        previous=self.name();new=json.loads(inv)['name']
        with self.con:
            self.con.execute('UPDATE case_info SET name=? WHERE id=1',(new,))
            self._log(actor,'UNDO_NAME',{'undid':event_id,'name':new},{'name':previous},comp=True)
        self._dirty=True

    def add_evidence(self,identifier,kind,description,revision,location,actor,data_class='SYNTHETIC'):
        if not all(isinstance(v,str) and v.strip() for v in (identifier,kind,description,revision,location)):
            raise CaseError('EVIDENCE','Evidence fields are required; do not invent unavailable values')
        if data_class not in ('SYNTHETIC','PROJECT_BASIS'):raise CaseError('DATA_CLASS','Invalid data class')
        with self.con:
            self.con.execute('INSERT INTO evidence VALUES(?,?,?,?,?,?)',(identifier,kind,description,revision,location,data_class))
            self._log(actor,'ADD_EVIDENCE',{'id':identifier,'kind':kind,'source':revision,'location':location,'data_class':data_class},{'delete_id':identifier})
        self._dirty=True

    def add_detector(self,tag,kind,x,y,z,evidence_id,actor):
        import math
        if not all(math.isfinite(float(v)) for v in (x,y,z)):
            raise CaseError('COORDINATE','Coordinates must be finite')
        if not actor.strip(): raise CaseError('ACTOR','Named editor required')
        with self.con:
            self.con.execute('INSERT INTO detectors(id,detector_type,x,y,z,evidence_id) VALUES(?,?,?,?,?,?)',(tag,kind,x,y,z,evidence_id))
            self._log(actor,'ADD_DETECTOR',{'id':tag,'type':kind,'x':x,'y':y,'z':z,'source':evidence_id},{'delete_id':tag})
            if self.con.execute('PRAGMA user_version').fetchone()[0]>=2:
                self.con.execute("UPDATE calculation_run SET calculation_status='STALE'")
        self._dirty=True

    def detectors(self):
        return self.con.execute('SELECT id,detector_type,x,y,z,evidence_id,review_status FROM detectors ORDER BY id').fetchall()

    def snapshot(self):
        def records(q,cols):return [dict(zip(cols,r)) for r in self.con.execute(q).fetchall()]
        return {'snapshot_version':'0.1.0a1','status':'DEVELOPMENT BUILD',
            'case':records('SELECT case_uuid,name,status,schema_version FROM case_info',['case_uuid','name','status','schema_version'])[0],
            'evidence':records('SELECT id,kind,description,document_revision,location_ref,data_class FROM evidence ORDER BY id',['id','kind','description','document_revision','location_ref','data_class']),
            'detectors':records('SELECT id,detector_type,x,y,z,evidence_id,review_status FROM detectors ORDER BY id',['id','detector_type','x','y','z','evidence_id','review_status']),
            'ledger':records('SELECT event_id,utc,actor,command,forward_json,inverse_json,is_compensation FROM ledger ORDER BY event_id',['event_id','utc','actor','command','forward_json','inverse_json','is_compensation'])}

    def save(self):
        self.con.commit()
        if digest(self.path)!=self._original_sha:
            raise CaseError('SAVE_CONFLICT','Case changed on disk since opening; save refused')
        fd,tmp=tempfile.mkstemp(prefix='.fg_saving_',suffix='.sqlite',dir=self.path.parent)
        os.close(fd)
        try:
            dst=sqlite3.connect(tmp)
            try:self.con.backup(dst)
            finally:dst.close()
            fsync_file(tmp)
            self._backup()
            pending=digest(Path(tmp))
            atomic_json(self.meta,{'original_sha':self._original_sha,'pending_sha':pending,'work_sha':digest(self.work),'case':str(self.path)})
            if digest(self.path)!=self._original_sha:raise CaseError('SAVE_CONFLICT','Source changed while preparing save; replacement refused')
            os.replace(tmp,self.path)
            fsync_directory(self.path.parent)
            self._original_sha=digest(self.path)
            atomic_json(self.meta,{'original_sha':self._original_sha,'case':str(self.path),'saved':utc_now()})
            self._dirty=False
        finally:
            if os.path.exists(tmp):os.unlink(tmp)

    def _backup(self):
        backup=self.runtime/'Backups'/(self.key+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.fgcase')
        shutil.copy2(self.path,backup)
        fsync_file(backup)

    def close(self,discard_unsaved:bool=False):
        if self._con:
            self._con.close();self._con=None
        self.lock.unlink(missing_ok=True)
        self._fence.close()
        if discard_unsaved or not self._dirty:
            self.work.unlink(missing_ok=True);self.meta.unlink(missing_ok=True)
