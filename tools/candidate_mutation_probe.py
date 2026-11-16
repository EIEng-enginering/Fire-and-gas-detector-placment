"""Critical candidate mutation checks in disposable copies; source/tests preserved."""
import os,shutil,subprocess,sys,tempfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
mutants=[('missing-physics-gate','engine/detection.py',"raise EngineeringUnavailable('CANNOT CALCULATE engineering flame coverage: '+', '.join(missing))","return {}",'test_detection_scenarios.py'),
('triangle-edge-sense','engine/mesh_visibility.py',"if dot(n,cross(sub(y,x),sub(p,x))) < -eps*norm(sub(y,x)):return False","if dot(n,cross(sub(y,x),sub(p,x))) > eps*norm(sub(y,x)):return False",'test_mesh_visibility.py'),
('coordinate-unit-conversion','domain/scene.py',"scale=UNITS[self.units]; m=self.matrix","scale=1.; m=self.matrix",'test_scene.py')]
results=[]
for name,path,old,new,pattern in mutants:
    with tempfile.TemporaryDirectory() as temp:
        base=Path(temp);shutil.copytree(ROOT/'src/fgmapping',base/'fgmapping')
        p=base/'fgmapping'/path;text=p.read_text();assert old in text;p.write_text(text.replace(old,new))
        env=dict(os.environ,PYTHONPATH=str(base)+os.pathsep+str(ROOT),PYTHONDONTWRITEBYTECODE='1')
        cmd=[sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'tests/unit'),'-p',pattern,'-v']
        r=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (ROOT/'TEST_RESULTS'/('MUTANT_'+name+'.txt')).write_text('COMMAND '+str(cmd)+'\n'+r.stdout)
        detected=r.returncode!=0 and 'FAIL:' in r.stdout
        results.append({'mutation':name,'exit_code':r.returncode,'detected_by_assertion':detected})
        assert detected, 'Mutant survived or failed only because of environment/import error'
print(json.dumps(results,indent=2))
