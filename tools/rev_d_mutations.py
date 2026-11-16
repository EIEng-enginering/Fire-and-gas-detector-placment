"""Critical new-method refusal/unit/denominator mutants in disposable source."""
import os,shutil,tempfile,subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
mutants=[('physical-offset-double-scaled','domain/mounting.py','basis[i][j]*offset[j]','basis[i][j]*offset[j]*lengths[j]','unit','test_mounting_pose.py'),('indeterminate-rays-declared-clear','engine/inspection.py',"state='BLOCKED' if blockers else 'INDETERMINATE' if uncertain else 'CLEAR'","state='BLOCKED' if blockers else 'CLEAR'",'unit','test_target_inspection.py'),('engineering-gate-bypassed','services/basis.py',"'engineering_calculation_status':'BLOCKED'","'engineering_calculation_status':'READY'",'integration','test_study_preparation.py')]
results=[]
for label,path,before,after,suite,pattern in mutants:
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);shutil.copytree(ROOT/'src',root/'src');shutil.copytree(ROOT/'contracts',root/'contracts');p=root/'src/fgmapping'/path;text=p.read_text();assert before in text;p.write_text(text.replace(before,after))
  env=dict(os.environ,PYTHONPATH=str(root/'src')+os.pathsep+str(ROOT),PYTHONDONTWRITEBYTECODE='1');command=[sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'tests'/suite),'-p',pattern,'-v'];r=subprocess.run(command,cwd=root,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
  (ROOT/'TEST_RESULTS'/('REV_D_MUTANT_'+label+'.txt')).write_text('COMMAND '+str(command)+'\n'+r.stdout)
  detected=r.returncode!=0 and 'FAIL:' in r.stdout;assert detected and 'ModuleNotFoundError' not in r.stdout
  results.append({'mutation':label,'detected_by_assertion':detected,'exit_code':r.returncode})
print(json.dumps(results,indent=2))
