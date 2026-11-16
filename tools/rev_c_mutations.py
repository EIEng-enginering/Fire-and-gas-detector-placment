"""Exercise native-writer and transactional-history regressions in disposable source."""
import os,shutil,subprocess,sys,tempfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
mutants=[('writer-fence-bypass','services/file_lock.py','fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)','pass # intentionally disable writer fence','test_case_hardening.py'),('undo-wrong-state','services/workspace.py',"'before':c['after'],'after':c['before']","'before':c['before'],'after':c['after']",'test_workspace.py')]
results=[]
for name,path,old,new,pattern in mutants:
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);shutil.copytree(ROOT/'src',root/'src');shutil.copytree(ROOT/'contracts',root/'contracts')
  p=root/'src/fgmapping'/path;s=p.read_text();assert old in s;p.write_text(s.replace(old,new))
  env=dict(os.environ,PYTHONPATH=str(root/'src')+os.pathsep+str(ROOT),PYTHONDONTWRITEBYTECODE='1')
  command=[sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'tests/integration'),'-p',pattern,'-v'];r=subprocess.run(command,env=env,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
  (ROOT/'TEST_RESULTS'/('REV_C_MUTANT_'+name+'.txt')).write_text('COMMAND '+str(command)+'\n'+r.stdout)
  detected=r.returncode!=0 and ('FAIL:' in r.stdout or 'ERROR:' in r.stdout)
  # Guard against an import/environment-only failure being counted as detection.
  assert detected and 'ModuleNotFoundError' not in r.stdout and 'migration not found' not in r.stdout.lower()
  results.append({'mutation':name,'detected':True,'exit':r.returncode})
print(json.dumps(results,indent=2))
