"""Deliberately break new guards/calculation logic in private source copies."""
import tempfile,shutil,os,subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];records=[]
mutants=[('scene-candidates-dropped','src/fgmapping/engine/spatial.py','visit(self.root);return tuple(sorted(found))','visit(self.root);return ()','unit','test_scene_broadphase.py'),('follow-mount-not-recomputed','src/fgmapping/services/reconciliation.py',"    set_mount(stage,id,new.id,json.loads(m['anchor_local_json']),json.loads(m['offset_m_json']),json.loads(m['orientation_local_json']),d['evidence_id'],'AUTOMATION_ENGINE')",'    pass # Deliberately broken follow','integration','test_preparation_imports.py'),('missing-mount-decisions-accepted','src/fgmapping/services/reconciliation.py',"if set(byid)!={x['detector_id'] for x in impact['affected_mounts']}:",'if False:','integration','test_preparation_imports.py')]
for label,name,old,new,suite,test in mutants:
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp)
  for folder in ['src','tests','contracts']:shutil.copytree(ROOT/folder,root/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
  p=root/name;text=p.read_text();assert old in text,label;p.write_text(text.replace(old,new,1));env=dict(os.environ,PYTHONPATH=str(root/'src')+os.pathsep+str(root),PYTHONDONTWRITEBYTECODE='1');run=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(root/'tests'/suite),'-p',test,'-v'],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=45);(ROOT/'TEST_RESULTS'/('REV_E_MUTANT_'+label+'.txt')).write_text(run.stdout)
  caught=run.returncode==1 and '\nFAIL:' in run.stdout and '\nERROR:' not in run.stdout;assert caught,(label,run.stdout);records.append({'mutation':label,'caught_by_assertion':caught,'exit_code':run.returncode})
(ROOT/'TEST_RESULTS/REV_E_MUTATIONS.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))
