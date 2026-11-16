"""Real Windows Qt smoke only. Explicitly refuses offscreen/Linux acceptance."""
import json,os,sys,tempfile
from pathlib import Path
from PySide6 import __version__
from PySide6.QtWidgets import QApplication
from fgmapping.ui.main import MainWindow
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene
from fgmapping.domain.scene import synthetic_scene
from fgmapping.services.study_schema import enable_study
from fgmapping.services import workspace
from fgmapping.services.mounts import set_mount
from fgmapping.services.basis import readiness
from fgmapping.services.process_inspection import windows_process_state,ALIVE
app=QApplication([])
if sys.platform!='win32' or app.platformName()!='windows' or sys.version_info[:2]!=(3,12) or __version__!='6.12.0':raise SystemExit('Windows11/Python3.12/PySide6.12 real Windows Qt platform required')
if windows_process_state(os.getpid())!=ALIVE:raise SystemExit('Native Windows process inspection did not identify this process as alive')
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
 p=create_case(Path(tmp)/'synthetic.fgcase','SYNTHETIC WINDOWS SMOKE');w=MainWindow();w.session=CaseSession(p,Path(tmp)/'runtime');s=w.session
 enable_geometry(s,'AUTOMATION_ENGINE');s.add_evidence('SYN-GEOM-01','SYNTHETIC','Generated synthetic scene','A','test','AUTOMATION_ENGINE');set_scene(s,synthetic_scene(),'AUTOMATION_ENGINE');enable_study(s,'AUTOMATION_ENGINE')
 workspace.detector_command(s,{'id':'SYN-WIN-D','detector_type':'FLAME','x':0,'y':0,'z':0,'evidence_id':'SYN-GEOM-01'},None,'AUTOMATION_ENGINE',create=True,place_marker=True)
 set_mount(s,'SYN-WIN-D','V101',(3,3,5),(0,0,.5),(0,-15,0),'SYN-GEOM-01','AUTOMATION_ENGINE')
 assert readiness(s)['engineering_calculation_status']=='BLOCKED'
 s.save();w.refresh();w.show();app.processEvents()
 for theme in ('grey','dark','light'):
  w.theme.setCurrentText(theme);app.processEvents();assert w.grab().save(str(out/(theme+'.png')))
 w.close();app.processEvents()
print(json.dumps({'platform':sys.platform,'Qt_platform':app.platformName(),'python':sys.version,'PySide6':__version__,'smoke':'PASS','native_process_probe':'ALIVE','candidate_schema':3,'engineering_gate':'BLOCKED','engineering_qualification':'UNVERIFIED','manual_acceptance':'STILL REQUIRED'}))
