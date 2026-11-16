from contextlib import closing
import json,sqlite3,tempfile,unittest
from pathlib import Path
from fgmapping.services.case import CaseSession,create_case,digest
from fgmapping.services.geometry import enable_geometry,get_scene,set_scene,compensate_scene
from fgmapping.services.mesh_import import ImportJob
from fgmapping.domain.scene import synthetic_scene,Frame
from fgmapping.errors import CaseError
class GeometryStore(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.path=create_case(self.root/'syn.fgcase','SYNTHETIC')
    def session(self):return CaseSession(self.path,self.root/'runtime')
    def prepare(self,s):
        enable_geometry(s,'TEST_ENGINE');s.add_evidence('SYN-GEOM-01','SYNTHETIC','Generated test mesh','A','scene','TEST_ENGINE')
    def test_explicit_backup_original_preserved(self):
        old=digest(self.path)
        with self.session() as s:
            self.assertIsNone(get_scene(s));enable_geometry(s,'TEST_ENGINE');self.assertEqual(old,digest(self.path))
            self.assertEqual(s.con.execute('PRAGMA user_version').fetchone()[0],2)
            backups=list((self.root/'runtime/Backups').glob('*.fgcase'))
            saved=[p for p in backups if '_pre_geometry_' not in p.name];working=[p for p in backups if '_pre_geometry_' in p.name]
            self.assertEqual(len(saved),1);self.assertEqual(digest(saved[0]),old);self.assertEqual(len(working),1)
            with closing(sqlite3.connect(working[0])) as pre, pre:self.assertEqual(pre.execute('PRAGMA user_version').fetchone()[0],1)
            s.save()
        with self.session() as s:self.assertEqual(s.con.execute('PRAGMA user_version').fetchone()[0],2)
    def test_migration_backup_preserves_unsaved_edits(self):
        with self.session() as s:
            s.set_name('SYNTHETIC UNSAVED','TEST_ENGINE');enable_geometry(s,'TEST_ENGINE')
            backup=next((self.root/'runtime/Backups').glob('*_pre_geometry_*'))
            with closing(sqlite3.connect(backup)) as pre, pre:
                self.assertEqual(pre.execute('SELECT name FROM case_info').fetchone()[0],'SYNTHETIC UNSAVED')
                self.assertEqual(pre.execute('PRAGMA user_version').fetchone()[0],1)
    def test_scene_save_reopen(self):
        with self.session() as s:self.prepare(s);set_scene(s,synthetic_scene(),'TEST_ENGINE');s.save()
        with self.session() as s:self.assertEqual(get_scene(s),synthetic_scene())
    def test_undo_redo_reopen(self):
        with self.session() as s:
            self.prepare(s);set_scene(s,synthetic_scene(),'TEST_ENGINE');compensate_scene(s,'TEST_ENGINE');self.assertIsNone(get_scene(s));s.save()
        with self.session() as s:compensate_scene(s,'TEST_ENGINE',True);self.assertEqual(get_scene(s),synthetic_scene());s.save()
    def test_missing_evidence(self):
        with self.session() as s:
            enable_geometry(s,'TEST_ENGINE')
            with self.assertRaises(CaseError):set_scene(s,synthetic_scene(),'TEST_ENGINE')
            self.assertIsNone(get_scene(s))
    def test_empty_actor_rolls_back(self):
        with self.session() as s:
            self.prepare(s)
            with self.assertRaises(CaseError):set_scene(s,synthetic_scene(),'')
            self.assertIsNone(get_scene(s))
    def test_corrupt_hash(self):
        with self.session() as s:
            self.prepare(s);set_scene(s,synthetic_scene(),'TEST_ENGINE')
            with s.con:s.con.execute("UPDATE geometry_scene SET sha256='bad'")
            with self.assertRaises(CaseError):get_scene(s)
    def test_immutable_ledger(self):
        with self.session() as s:
            self.prepare(s)
            for sql in ('DELETE FROM ledger',"UPDATE ledger SET actor='OTHER'"):
                with self.assertRaises(sqlite3.IntegrityError):s.con.execute(sql)
    def test_worker(self):
        p=self.root/'synthetic.obj';p.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3')
        self.assertEqual(len(ImportJob(p,Frame('F','m','SYN')).result()['mesh']['faces']),1)
        p.write_text('mtllib network.mtl')
        with self.assertRaises(ValueError):ImportJob(p,Frame('F','m','SYN')).result()
    def test_cancel(self):
        p=self.root/'synthetic.obj';p.write_text('invalid');j=ImportJob(p,Frame('F','m','SYN'));j.cancel();self.assertIsNotNone(j.process.poll())
    def test_original_contract_hash(self):
        root=Path(__file__).resolve().parents[2];m=json.loads((root/'contracts/manifest.json').read_text())
        for name,sha in m['migrations_sha256'].items():self.assertEqual(digest(root/'contracts/migrations'/name),sha)
