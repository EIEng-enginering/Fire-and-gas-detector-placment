from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from fgmapping.services.case import create_case,CaseSession,digest
from fgmapping.errors import CaseError

class CaseIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.case=create_case(self.base/'plant.fgcase','SYNTHETIC FACILITY')
        self.runtime=self.base/'runtime'

    def test_create_edit_save_reopen(self):
        with CaseSession(self.case,self.runtime) as s:
            s.add_evidence('DOC-S','SYNTHETIC_DRAWING','Synthetic layout','A','Page 1','TEST_ENGINEER')
            s.add_detector('SYN-FD-01','FLAME',1,2,3,'DOC-S','TEST_ENGINEER')
            self.assertEqual(len(s.detectors()),1)
            s.save()
        with CaseSession(self.case,self.runtime) as s:
            self.assertEqual(len(s.detectors()),1)
            self.assertEqual(s.snapshot()['case']['name'],'SYNTHETIC FACILITY')
            self.assertEqual(len(s.snapshot()['ledger']),2)
        backups=list((self.runtime/'Backups').glob('*.fgcase'))
        self.assertEqual(len(backups),1)
        with closing(sqlite3.connect(backups[0])) as old, old:
            self.assertEqual(old.execute('SELECT count(*) FROM detectors').fetchone()[0],0)

    def test_lock_refuses_second_writer(self):
        with CaseSession(self.case,self.runtime) as s:
            with self.assertRaises(CaseError) as ctx:CaseSession(self.case,self.runtime)
            self.assertEqual(ctx.exception.code,'LOCKED')

    def test_save_conflict_refuses_silent_overwrite(self):
        with CaseSession(self.case,self.runtime) as s:
            s.set_name('EDITED','TEST_ENGINEER')
            with closing(sqlite3.connect(self.case)) as raw, raw:
                raw.execute("UPDATE case_info SET name='EXTERNAL CHANGE' WHERE id=1")
            with self.assertRaises(CaseError) as ctx:s.save()
            self.assertEqual(ctx.exception.code,'SAVE_CONFLICT')
        with closing(sqlite3.connect(self.case)) as raw, raw:
            self.assertEqual(raw.execute('SELECT name FROM case_info').fetchone()[0],'EXTERNAL CHANGE')

    def test_crash_recovery_explicit(self):
        with CaseSession(self.case,self.runtime) as s:
            s.set_name('UNSAVED SYNTHETIC','TEST_ENGINEER')
        with self.assertRaises(CaseError) as ctx:CaseSession(self.case,self.runtime)
        self.assertEqual(ctx.exception.code,'RECOVERY_REQUIRED')
        with CaseSession(self.case,self.runtime,recover=True) as s:
            self.assertEqual(s.name(),'UNSAVED SYNTHETIC')
            s.save()
        with CaseSession(self.case,self.runtime) as s:
            self.assertEqual(s.name(),'UNSAVED SYNTHETIC')

    def test_undo_is_compensating_event(self):
        with CaseSession(self.case,self.runtime) as s:
            s.set_name('A','PERSON_A')
            s.set_name('B','PERSON_A')
            s.undo_last_name('PERSON_A')
            self.assertEqual(s.name(),'A')
            self.assertEqual(len(s.snapshot()['ledger']),3)
            s.undo_last_name('PERSON_A')
            self.assertEqual(s.name(),'SYNTHETIC FACILITY')

    def test_evidence_mandatory_and_synthetic(self):
        with CaseSession(self.case,self.runtime) as s:
            with self.assertRaises(sqlite3.IntegrityError):s.add_detector('FD','FLAME',1,2,3,'UNKNOWN','TEST_ENGINEER')
            self.assertEqual(len(s.detectors()),0)
            with self.assertRaises(CaseError):s.add_evidence('E','K','Desc','Rev','Page','ACTOR','NOT_KNOWN')

    def test_existing_case_not_overwritten(self):
        before=digest(self.case)
        with self.assertRaises(CaseError):create_case(self.case,'ANOTHER')
        self.assertEqual(before,digest(self.case))

    def test_unsupported_schema_refused(self):
        with closing(sqlite3.connect(self.case)) as con, con:con.execute('PRAGMA user_version=10')
        with self.assertRaises(CaseError) as ctx:CaseSession(self.case,self.runtime)
        self.assertEqual(ctx.exception.code,'VERSION')

if __name__=='__main__':unittest.main()
