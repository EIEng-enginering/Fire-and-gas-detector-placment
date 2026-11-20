"""Rev H (F10): validated output names, resolved containment, exclusive staged creation."""
from __future__ import annotations
import os,re,shutil,uuid
from pathlib import Path
from fgmapping.errors import CaseError
class OutputPathError(CaseError,ValueError):
    """Refused output path (also a ValueError for callers that catch ValueError)."""

RESERVED={'CON','PRN','AUX','NUL',*('COM%d' % i for i in range(1,10)),*('LPT%d' % i for i in range(1,10)),'COM¹','COM²','COM³','LPT¹','LPT²','LPT³'}
BAD=re.compile(r'[<>:"/\\|?*\x00-\x1f]')

def validate_name(name):
    """A single portable file/folder name component (Windows + POSIX). Spaces, Unicode and '&'
    are allowed; separators, '..', absolute/drive forms, reserved device names, control and
    Windows-invalid characters, trailing dot/space and >120 characters are refused."""
    if not isinstance(name,str) or not name or name!=name.strip() or len(name)>120:raise OutputPathError('OUTPUT_NAME','Output name must be 1-120 characters without leading/trailing spaces')
    if name in ('.','..') or BAD.search(name) or name.endswith('.'):raise OutputPathError('OUTPUT_NAME','Output name contains a path separator, ".." or an invalid character: '+repr(name))
    if name.split('.')[0].upper().rstrip() in RESERVED:raise OutputPathError('OUTPUT_NAME','Reserved Windows device name: '+name)
    return name

def contained_child(folder,name):
    validate_name(name);base=Path(folder)
    if not base.exists():base.mkdir(parents=True)
    base=base.resolve()
    if not base.is_dir():raise OutputPathError('OUTPUT_FOLDER','Output folder is not a directory: '+str(folder))
    dest=(base/name).resolve()
    if dest.parent!=base:raise OutputPathError('OUTPUT_NAME','Output escapes the selected folder')
    if dest.exists() or os.path.lexists(base/name):raise OutputPathError('OUTPUT_EXISTS','Output already exists; outputs are never overwritten')
    return base,dest

class StagedFolder:
    """Write into a hidden sibling staging folder, then publish with one rename. Files are
    created exclusively ('xb'); on any error the staging folder is removed and nothing is published."""
    def __init__(self,folder,name):
        self.base,self.dest=contained_child(folder,name)
        self.stage=self.base/('.%s.staging-%s' % (name,uuid.uuid4().hex[:12]));self.stage.mkdir()
    def path(self,filename):
        validate_name(filename);p=(self.stage/filename)
        if p.resolve().parent!=self.stage.resolve():raise OutputPathError('OUTPUT_NAME','File escapes staging folder')
        return p
    def write_bytes(self,filename,data):
        with open(self.path(filename),'xb') as f:f.write(data)
    def publish(self):
        if os.path.lexists(self.dest):raise OutputPathError('OUTPUT_EXISTS','Output appeared during export; nothing overwritten')
        os.rename(self.stage,self.dest);return self.dest
    def abort(self):shutil.rmtree(self.stage,ignore_errors=True)
