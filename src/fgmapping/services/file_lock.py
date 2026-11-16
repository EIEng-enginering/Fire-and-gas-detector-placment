"""OS-held writer fence shared across runtime directories; no stale PID unlocking.

Stable sidecar survives atomic case replacement; it is operational, not case data.
Hard-linked source aliases are refused because replacing one link forks identity.
Windows msvcrt branch is supplied but requires actual Windows acceptance.
"""
import os
from pathlib import Path
from fgmapping.errors import CaseError
class WriterFence:
    def __init__(self,path):
        self.file=None;path=Path(path)
        if path.stat().st_nlink!=1:raise CaseError('ALIASED_CASE','Hard-linked case files cannot be edited; make a separate portable copy')
        self.path=path.with_name(path.name+'.writer.lock')
        handle=self.path.open('a+b')
        try:
            handle.seek(0,os.SEEK_END)
            if handle.tell()==0:handle.write(b'0');handle.flush()
            handle.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:
            handle.close();raise CaseError('LOCKED','Another process holds the case writer fence') from exc
        self.file=handle
    def close(self):
        if self.file is not None:
            self.file.close();self.file=None
