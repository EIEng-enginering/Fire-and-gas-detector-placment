"""Rev F: synthetic report containing literal '=' text, for native Excel/Word read-back.

Writes a fresh output folder (refuses an existing one). Synthetic only; the
values are text, not formulas, and are not engineering data."""
import sys,json,tempfile
from pathlib import Path
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services import workspace as w
from fgmapping.services.geometry import enable_geometry,set_scene
from fgmapping.services.study_schema import enable_study
from fgmapping.domain.scene import synthetic_scene
from fgmapping.services.performance import import_dataset
from fgmapping.services.reporting import normalized_snapshot,write_reports,qa_reports
out=Path(sys.argv[1]).resolve()
if out.exists():raise SystemExit('Refusing existing output folder: '+str(out))
LITERALS=['=1+1','=HYPERLINK("http://example.invalid","SYNTHETIC")']
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);case=create_case(root/'lit.fgcase','SYNTHETIC LITERAL EQUALS REPORT')
    with CaseSession(case,root/'r') as s:
        enable_geometry(s,'AUTOMATION_ENGINE')
        s.add_evidence('SYN-GEOM-01','SYNTHETIC',LITERALS[0]+' synthetic literal evidence text','A','generated','AUTOMATION_ENGINE')
        set_scene(s,synthetic_scene(),'AUTOMATION_ENGINE');enable_study(s,'AUTOMATION_ENGINE')
        for i,text in enumerate(LITERALS):
            w.detector_command(s,{'id':f'SYN-LIT-D{i}','detector_type':'FLAME','x':i,'y':0,'z':3,'azimuth':0,'elevation':0,'roll':0,'manufacturer':text,'model':text,'sensitivity':'TEST','evidence_id':'SYN-GEOM-01'},None,'AUTOMATION_ENGINE',create=True)
        fixture=json.loads((Path(__file__).resolve().parents[1]/'examples/SYNTHETIC_PERFORMANCE_PREPARATION.json').read_text())
        for i,text in enumerate(LITERALS):
            import_dataset(s,f'SYN-LIT-PERF-{i}',json.dumps({**fixture,'manufacturer':text,'model':text,'revision':text}).encode(),'AUTOMATION_ENGINE')
        snap=normalized_snapshot(s);write_reports(snap,out);qa=qa_reports(snap,out)
print(json.dumps({'output':str(out),'literals':LITERALS,'qa':qa},default=str)[:3000])
