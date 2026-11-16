"""Explicit candidate preparation schema; never an automatic case upgrade."""
import json,hashlib,sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4
from fgmapping.errors import CaseError
ROOT=Path(__file__).resolve().parents[3]

def enable_study(session,actor):
 if not actor.strip():raise CaseError('ACTOR','Explicit upgrade actor required')
 version=session.con.execute('PRAGMA user_version').fetchone()[0]
 if version==3:return
 if version!=2:raise CaseError('MIGRATION_REQUIRED','Enable geometry schema2 before study schema3')
 manifest=json.loads((ROOT/'contracts/candidate_manifest.json').read_text())
 for name,expected in manifest['migrations_sha256'].items():
  if hashlib.sha256((ROOT/'contracts/migrations'/name).read_bytes()).hexdigest()!=expected:raise CaseError('CONTRACT_HASH','Candidate migration hash mismatch')
 session._backup()
 backup=session.runtime/'Backups'/(session.key+'_pre_study3_'+uuid4().hex+'.fgcase')
 with closing(sqlite3.connect(backup)) as dst:session.con.backup(dst)
 with session.con:
  session.con.execute('BEGIN IMMEDIATE');statement=''
  for line in (ROOT/'contracts/migrations/0003_study_preparation.sql').read_text().splitlines(True):
   statement+=line
   if sqlite3.complete_statement(statement):session.con.execute(statement);statement=''
  if statement.strip():raise CaseError('MIGRATION','Incomplete candidate SQL')
  session._log(actor,'ENABLE_STUDY3',{'schema':3},{'restore_backup':backup.name})
 session._dirty=True

def require_study(session):
 if session.con.execute('PRAGMA user_version').fetchone()[0]!=3:raise CaseError('MIGRATION_REQUIRED','Explicit candidate study schema3 upgrade required')
