"""Rev F: Windows file-handle/fsync portability regressions (synthetic only).

Found by the first native Windows 11 / Python 3.12 run of the untouched Rev E
suite: os.fsync on a read-only descriptor fails with EBADF on Windows, and
SQLite connections left open by `with sqlite3.connect(...)` (which commits but
does not close) keep files locked so they cannot be deleted/renamed.

These tests emulate the Windows semantics on POSIX so the regressions are
caught on every platform, and exercise the native behaviour on Windows.
"""
import os,re,sqlite3,stat,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import fgmapping.services.case as case_module
from fgmapping.services.case import create_case,CaseSession,digest,fsync_file
from fgmapping.services.recovery import restore_as_new,inspect_backup,list_backups
from fgmapping.services.geometry import enable_geometry
from fgmapping.services.study_schema import enable_study
from fgmapping.services.preparation_job import PreparationJob
SRC=Path(__file__).resolve().parents[2]/'src'/'fgmapping'
_real_fsync=os.fsync

def windows_like_fsync(fd):
    """Refuse read-only descriptors, as Windows _commit does (EBADF)."""
    if os.name!='nt' and not stat.S_ISDIR(os.fstat(fd).st_mode):
        # POSIX-only directory fsync (fsync_directory) is skipped on Windows.
        import fcntl
        if fcntl.fcntl(fd,fcntl.F_GETFL)&os.O_ACCMODE==os.O_RDONLY:
            raise OSError(9,'Bad file descriptor (emulated Windows read-only fsync)')
    return _real_fsync(fd)

def open_handles(path):
    """Return evidence that this process still holds `path` open.

    Linux: inspect /proc/self/fd. Windows: an exclusive rename fails while a
    handle without FILE_SHARE_DELETE is open."""
    path=Path(path).resolve()
    if os.name=='nt':
        probe=path.with_name(path.name+'.rename_probe')
        try:os.rename(path,probe)
        except PermissionError:return ['WINDOWS_SHARING_VIOLATION']
        os.rename(probe,path);return []
    fds=Path('/proc/self/fd')
    if not fds.exists():raise unittest.SkipTest('No /proc handle inspection on this host')
    found=[]
    for fd in fds.iterdir():
        try:
            if Path(os.readlink(fd))==path:found.append(fd.name)
        except OSError:pass
    return found

class WindowsFsyncSemantics(unittest.TestCase):
    def test_emulator_rejects_read_only_descriptor(self):
        # Guard: the emulation must actually reproduce the Windows failure.
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.bin';p.write_bytes(b'SYNTHETIC')
            with open(p,'rb') as f:
                with self.assertRaises(OSError):windows_like_fsync(f.fileno())
            with open(p,'r+b') as f:windows_like_fsync(f.fileno())
            self.assertEqual(p.read_bytes(),b'SYNTHETIC')
    def test_fsync_file_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.bin';p.write_bytes(b'SYNTHETIC BYTES');before=digest(p)
            with patch.object(case_module.os,'fsync',windows_like_fsync):
                try:fsync_file(p)
                except OSError as exc:self.fail('fsync_file used a descriptor Windows rejects: '+str(exc))
            self.assertEqual(digest(p),before)
    def test_create_save_backup_restore_under_windows_fsync(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch('os.fsync',windows_like_fsync):
                try:
                    p=create_case(root/'s.fgcase','SYNTHETIC FSYNC')
                    with CaseSession(p,root/'r') as s:
                        s.set_name('SYNTHETIC FSYNC EDIT','TEST_ENGINE');s.save()
                    restored=restore_as_new(p,root/'restored.fgcase','TEST_ENGINE')
                except OSError as exc:self.fail('Durability path used a descriptor Windows rejects: '+str(exc))
            with CaseSession(restored,root/'r2') as s:self.assertEqual(s.name(),'SYNTHETIC FSYNC EDIT')
            self.assertEqual(len(list((root/'r'/'Backups').glob('*.fgcase'))),1)
    def test_no_read_only_fsync_pattern_in_source(self):
        bad=[]
        for f in SRC.rglob('*.py'):
            text=f.read_text(encoding='utf8')
            for m in re.finditer(r"open\([^)]*'rb'\)\s+as\s+(\w+)\s*:\s*os\.fsync",text):bad.append(f'{f.name}:{m.group(0)}')
        self.assertEqual(bad,[])

class SqliteHandleRelease(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.path=create_case(self.root/'s.fgcase','SYNTHETIC HANDLES')
    def test_inspect_backup_releases_file(self):
        info=inspect_backup(self.path);self.assertEqual(info['name'],'SYNTHETIC HANDLES')
        self.assertEqual(open_handles(self.path),[])
    def test_list_backups_releases_files(self):
        with CaseSession(self.path,self.root/'r') as s:s.set_name('SYNTHETIC B','TEST_ENGINE');s.save()
        rows=list_backups(self.root/'r');self.assertEqual([r['check'] for r in rows],['PASS'])
        for r in rows:self.assertEqual(open_handles(r['path']),[])
    def test_refused_open_releases_case_and_work_copy(self):
        with sqlite3.connect(self.path) as con:con.execute('PRAGMA user_version=10')
        con.close()
        with self.assertRaises(Exception):CaseSession(self.path,self.root/'r')
        self.assertEqual(open_handles(self.path),[])
        for f in (self.root/'r'/'Sessions').glob('*.sqlite'):self.assertEqual(open_handles(f),[])
    def test_schema_upgrade_backups_released(self):
        with CaseSession(self.path,self.root/'r') as s:
            enable_geometry(s,'TEST_ENGINE');enable_study(s,'TEST_ENGINE')
            backups=sorted((self.root/'r'/'Backups').glob('*.fgcase'))
            self.assertTrue(any('_pre_geometry_' in b.name for b in backups));self.assertTrue(any('_pre_study3_' in b.name for b in backups))
            for b in backups:self.assertEqual(open_handles(b),[],b.name)
    def test_preparation_snapshot_released_before_worker(self):
        with CaseSession(self.path,self.root/'r') as s:
            enable_geometry(s,'TEST_ENGINE')
            job=PreparationJob(s,b'data_class\nSYNTHETIC\n','CSV','BULK_REGISTER')
            try:self.assertEqual(open_handles(Path(job.temp.name)/'snapshot.fgcase'),[])
            finally:job.cancel()
            self.assertFalse(Path(job.temp.name).exists())
    def test_no_unclosed_connect_context_in_source(self):
        bad=[]
        for f in SRC.rglob('*.py'):
            for n,line in enumerate(f.read_text(encoding='utf8').splitlines(),1):
                if re.search(r'with\s+sqlite3\.connect\(',line):bad.append(f'{f.name}:{n}')
        self.assertEqual(bad,[],'sqlite3 connection context managers commit but do not close; use contextlib.closing')

if __name__=='__main__':unittest.main()
