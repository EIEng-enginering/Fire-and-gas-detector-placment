"""Runnable synthetic exercises across WP02-WP11; no engineering results."""
from pathlib import Path
import json,tempfile
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene
from fgmapping.services.registers import add_record
from fgmapping.services.calculations import run_synthetic
from fgmapping.domain.scene import synthetic_scene
from fgmapping.services.reporting import normalized_snapshot,write_reports
from fgmapping.engine.detection import UniformDesignCloud,engineering_flame_coverage,EngineeringUnavailable
from fgmapping.engine.scenarios import SyntheticScenario,aggregate
from fgmapping.engine.optimisation import SyntheticMount,enumerate_layouts
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'examples/SYNTHETIC_WP02_MODULE.fgcase'
if path.exists():raise SystemExit('Example exists; use a fresh source extraction for reproducible demo')
create_case(path,'SYNTHETIC Offshore Module WP02')
with tempfile.TemporaryDirectory() as runtime:
    with CaseSession(path,runtime) as s:
        enable_geometry(s,'AUTOMATION_ENGINE')
        s.add_evidence('SYN-GEOM-01','SYNTHETIC','Generated example envelopes','SYN-A','domain.scene.synthetic_scene','AUTOMATION_ENGINE')
        for tag,position in [('FD101',(0,0,3)),('FD102',(19,11,4))]:s.add_detector(tag,'FLAME',*position,'SYN-GEOM-01','AUTOMATION_ENGINE')
        set_scene(s,synthetic_scene(),'AUTOMATION_ENGINE')
        for id in ('V101','V102'):add_record(s,id,'EQUIPMENT',{'class':'VESSEL ENVELOPE','geometry_component_id':id},'SYN-GEOM-01','AUTOMATION_ENGINE')
        add_record(s,'SYN-FZ1','FIRE_ZONE',{'low':[0,0,0],'high':[20,12,6],'units':'m','criteria':'NOT SUPPLIED'},'SYN-GEOM-01','AUTOMATION_ENGINE')
        add_record(s,'SYN-GZ1','GAS_ZONE',{'low':[0,0,0],'high':[20,12,6],'units':'m','criteria':'NOT SUPPLIED'},'SYN-GEOM-01','AUTOMATION_ENGINE')
        run_synthetic(s,'SYN-PATH-01','SYNTHETIC_UNIFORM_PATH/1',{'low':[0,0,0],'high':[2,3,4],'ppm':100,'basis':'SYNTHETIC uniform cloud','start':[-5,1,1],'end':[5,1,1]},'AUTOMATION_ENGINE')
        s.save();snapshot=normalized_snapshot(s)
    result=write_reports(snapshot,ROOT/'OUTPUT_SAMPLES/SYNTHETIC_STUDY')
cloud=UniformDesignCloud((0,0,0),(2,3,4),100,'SYNTHETIC uniform cloud / not CFD')
result['gas_demo_ppm_m']=cloud.path_integral_ppm_m((-5,1,1),(5,1,1))
result['scenario_demo']=aggregate([SyntheticScenario('SYN-A','0.1','1','SYN-F','SYN-R'),SyntheticScenario('SYN-B','0.3','0','SYN-F','SYN-R')])
result['layout_demo']=enumerate_layouts([SyntheticMount('SYN-A',frozenset({'s1'}),'1',True,True)],{'s1':'1'},1,1)
try:engineering_flame_coverage()
except EngineeringUnavailable as exc:result['engineering_refusal']=str(exc)
(ROOT/'OUTPUT_SAMPLES/DEMO_RESULTS.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
