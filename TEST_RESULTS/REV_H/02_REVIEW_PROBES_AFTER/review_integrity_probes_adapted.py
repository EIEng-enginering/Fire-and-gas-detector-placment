# ADAPTED COPY for Rev H: calls that Rev H now refuses are wrapped in try/except so the
# refusal is recorded instead of aborting the probe. Constructions and expectations unchanged.
"""Isolated integrity/security probes. Never edits supplied source or user cases."""
from pathlib import Path
import sys,json,tempfile,shutil,subprocess,os,sqlite3
from unittest.mock import patch
ROOT=Path(sys.argv[1]);sys.path[:0]=[str(ROOT/'src'),str(ROOT)];out={}
from fgmapping.services.coverage_report import export_coverage_report
snap=json.loads((ROOT/'examples/wellhead_coverage/WELLHEAD_COVERAGE_REPORT/WELLHEAD_COVERAGE_REPORT.json').read_text());snap['figures']=[]
with tempfile.TemporaryDirectory() as td:
 root=Path(td);chosen=root/'chosen';chosen.mkdir();victim=root/'escaped.json';victim.write_text('SYNTHETIC PREEXISTING FILE')
 refused=None
 try:
  with patch('fgmapping.services.coverage_report.coverage_snapshot',return_value=snap):export_coverage_report(None,chosen,'../escaped')
 except Exception as exc:refused=type(exc).__name__+': '+str(exc)
 out['report_path_traversal']={'refused':refused,'selected_folder':'chosen','input_name':'../escaped','created_sibling_folder':(root/'escaped').is_dir(),'existing_sibling_json_overwritten':victim.read_text()!='SYNTHETIC PREEXISTING FILE'}
# Direct engineering entry point ignores fuel/fire-size compatibility checked by UI services.
from tests.unit.test_coverage_engine import flame_entry,flame_setup,det,scene
from fgmapping.engine.detection import engineering_flame_coverage
setup=flame_setup(spacing=.5,mode='VOLUME',kw=400);setup['flame']['fuel']='methane'
ref=None
try:
 r,_=engineering_flame_coverage(zone={'id':'Z','kind':'FIRE_ZONE','low':(1,-.5,-.5),'high':(2,.5,.5)},setup=setup,detectors=[det('D',(0,0,0))],library={'E':flame_entry(kw=100,fuel='heptane')},scene=scene())
except Exception as exc:
 r=None;ref=type(exc).__name__+": "+str(exc)
out['direct_engine_gate_mismatch']={'setup_fuel':'methane','library_fuel':'heptane','setup_kW':400,'rated_kW':100,'scaling':'NONE','actual_result_1ooN':(r['fractions']['1ooN'] if r else 'REFUSED: '+ref),'expected':'refuse incompatible fuel/fire basis'}
# An actual modified copy of an un-hashed study engine remains CURRENT.
with tempfile.TemporaryDirectory() as td:
 root=Path(td)
 shutil.copytree(ROOT/'src',root/'src');shutil.copytree(ROOT/'contracts',root/'contracts');case=root/'case.fgcase';shutil.copyfile(ROOT/'examples/wellhead_coverage/SYNTHETIC_WELLHEAD_COVERAGE.fgcase',case)
 p=root/'src/fgmapping/engine/scenario_coverage.py';p.write_text(p.read_text()+"\n# INJECTED REVIEW FAULT: a changed detection decision rule\ndef _votes(points,dets,setup,obs,findings):\n    return [(p,w,[]) for p,w in points]\n")
 script="""import json,sys,tempfile
from pathlib import Path
from fgmapping.services.case import CaseSession
from fgmapping.services.scenario_coverage import study_runs,study_run_currency,scenario_envelope
from fgmapping.engine.scenario_coverage import scenario_coverage
from fgmapping.services.geometry import get_scene
from fgmapping.domain.scene import content_hash
with CaseSession(Path(sys.argv[1]),Path(sys.argv[2])) as s:
 r=next(v for v in study_runs(s) if v['method']=='SCENARIO_COVERAGE');payload=json.loads(r['input_json'])['payload'];env=scenario_envelope(s,payload);result=scenario_coverage(env['zones'],get_scene(s),env['payload'])
 print(json.dumps({'stored_run_currency':study_run_currency(s,r),'stored_input_hash':r['input_hash'],'new_input_hash':content_hash(env),'stored_fraction':json.loads(r['result_json'])['overall']['frequency_weighted_detected_fraction'],'changed_code_fraction':result['overall']['frequency_weighted_detected_fraction']}))
"""
 env=dict(os.environ,PYTHONPATH=str(root/'src'),PYTHONDONTWRITEBYTECODE='1');proc=subprocess.run([sys.executable,'-B','-c',script,str(case),str(root/'runtime')],env=env,cwd=root,text=True,capture_output=True,timeout=40);assert proc.returncode==0,proc.stderr;out['changed_study_source_not_stale']=json.loads(proc.stdout)
# NaN accepted by scenario validator (later canonical serialization may refuse).
from fgmapping.services.scenario_coverage import validate_scenarios
p={'contract':'fg-coverage-scenarios/1','scenarios':[{'id':'A','zone_id':'Z','location':[float('nan'),0.,0.],'frequency_per_year':'1','frequency_source':'review'}]}
try:
 validate_scenarios(p);out['scenario_nonfinite_validation']={'accepted_by_contract':True}
except Exception as exc:out['scenario_nonfinite_validation']={'accepted_by_contract':False,'refused':type(exc).__name__+': '+str(exc)}
print(json.dumps(out,indent=2))
