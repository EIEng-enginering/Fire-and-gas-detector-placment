"""Rev F: deliberately reintroduce the Windows portability defects in private copies.

Each mutant must be caught by an assertion FAIL. On POSIX no ERROR is allowed;
on native Windows collateral ERRORs from real EBADF/sharing violations are recorded."""
import tempfile,shutil,os,subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];records=[]
T='test_windows_portability_rev_f.py'
mutants=[
 ('fsync-read-only-descriptor','src/fgmapping/services/case.py',"    with open(p,'r+b') as f:\n        os.fsync(f.fileno())","    with open(p,'rb') as f:\n        os.fsync(f.fileno())",'integration',T),
 ('inspect-backup-connection-leak','src/fgmapping/services/recovery.py',"  with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as con:","  with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as con:",'integration',T),
 ('geometry-backup-connection-leak','src/fgmapping/services/geometry.py',"    with closing(sqlite3.connect(backup)) as dst:session.con.backup(dst)","    dst=sqlite3.connect(backup);session.con.backup(dst)",'integration',T),
]
for label,name,old,new,suite,test in mutants:
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp)
  for folder in ['src','tests','contracts']:shutil.copytree(ROOT/folder,root/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
  p=root/name;text=p.read_text(encoding='utf8');assert old in text,label;p.write_text(text.replace(old,new,1),encoding='utf8')
  env=dict(os.environ,PYTHONPATH=str(root/'src')+os.pathsep+str(root),PYTHONDONTWRITEBYTECODE='1')
  run=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(root/'tests'/suite),'-p',test,'-v'],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
  (ROOT/'TEST_RESULTS'/('REV_F_MUTANT_'+label+'_'+sys.platform+'.txt')).write_text(run.stdout,encoding='utf8')
  fails=run.stdout.count('\nFAIL:');errors=run.stdout.count('\nERROR:')
  caught=run.returncode==1 and fails>0
  # POSIX: emulated semantics must be caught purely by assertions (no ERROR).
  # Windows: the real defect also breaks native setUp/temp cleanup (EBADF /
  # WinError 32), so collateral ERRORs are expected and recorded, but at least
  # one assertion FAIL is still required.
  accepted=caught and (errors==0 if os.name!='nt' else True)
  records.append({'mutation':label,'platform':sys.platform,'caught_by_assertion':caught,'assertion_failures':fails,'collateral_errors':errors,'accepted':accepted,'exit_code':run.returncode})
out=ROOT/'TEST_RESULTS'/('REV_F_MUTATIONS_'+sys.platform+'.json');out.write_text(json.dumps(records,indent=2)+'\n',encoding='utf8');print(json.dumps(records,indent=2))
raise SystemExit(0 if all(r['accepted'] for r in records) else 1)
