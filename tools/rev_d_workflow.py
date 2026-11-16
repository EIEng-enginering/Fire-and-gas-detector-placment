"""Actual Qt mounting/basis/link/diagnostic/report workflow; synthetic only."""
import os,sys,json,time,tempfile,shutil,argparse
from pathlib import Path
from datetime import datetime
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QDialog,QLineEdit,QDoubleSpinBox,QComboBox,QDialogButtonBox
from PySide6.QtCore import QTimer,Qt
from PySide6.QtTest import QTest
from fgmapping.ui.main import MainWindow
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene,get_scene
from fgmapping.services.study_schema import enable_study
from fgmapping.domain.scene import synthetic_scene
from fgmapping.services import workspace as w
from fgmapping.services.performance import import_dataset,review_draft
from fgmapping.services.basis import readiness
from fgmapping.services.reporting import normalized_snapshot
from fgmapping.services.comparison import compare_snapshots
from fgmapping.services.recovery import RestoreJob
ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('--output-dir');parser.add_argument('--case-output');args=parser.parse_args();run_id=datetime.now().strftime('%Y%m%dT%H%M%S%f')
app=QApplication([]);app.setQuitOnLastWindowClosed(False);errors=[]
def automate(values):
 def fill():
  d=app.activeModalWidget()
  try:
   assert isinstance(d,QDialog)
   for name,value in values.items():
    widget=d.findChild(QLineEdit,name) or d.findChild(QDoubleSpinBox,name) or d.findChild(QComboBox,name);assert widget is not None,name
    if isinstance(widget,QDoubleSpinBox):widget.setValue(value)
    elif isinstance(widget,QComboBox):widget.setCurrentText(str(value))
    else:widget.setText(str(value))
   buttons=d.findChild(QDialogButtonBox);QTest.mouseClick(buttons.button(QDialogButtonBox.Ok),Qt.LeftButton)
  except Exception as exc:
   errors.append(str(exc))
   if d:d.reject()
 QTimer.singleShot(40,fill)
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);case=create_case(root/'s.fgcase','SYNTHETIC Rev D integrated preparation');window=MainWindow();window.settings.clear();window.session=CaseSession(case,root/'runtime');s=window.session
 enable_geometry(s,'AUTOMATION_ENGINE');s.add_evidence('SYN-GEOM-01','SYNTHETIC','Generated case layout','A','domain.scene','AUTOMATION_ENGINE');set_scene(s,synthetic_scene(),'AUTOMATION_ENGINE');enable_study(s,'AUTOMATION_ENGINE')
 w.detector_command(s,{'id':'SYN-D01','detector_type':'FLAME','x':1,'y':1,'z':3,'azimuth':0,'elevation':0,'roll':0,'manufacturer':'SYNTHETIC_VENDOR','model':'SYNTHETIC_MODEL','sensitivity':'TEST','evidence_id':'SYN-GEOM-01'},None,'AUTOMATION_ENGINE',create=True,place_marker=True)
 window.refresh();window.show();app.processEvents();window.table.select_id('SYN-D01');previous=normalized_snapshot(s)
 automate({'mount_component':'V101','mount_anchor_0':3,'mount_anchor_1':3,'mount_anchor_2':5,'mount_offset_2':.5,'mount_orientation_0':30,'mount_orientation_1':-15,'mount_orientation_2':10,'mount_actor':'SYNTHETIC_UI_TEST'})
 window.mount_dialog();assert not errors,errors;assert w.row(s,'detector_mount','SYN-D01')['component_id']=='V101';assert w.row(s,'detectors','SYN-D01')['z']==5.5
 automate({'basis_revision':'SYN-D1','basis_coordinate_reference':'Synthetic local XYZ','basis_target_description':'Synthetic rectangular geometric target; no physical fire model','basis_fuel_or_gas':'SYNTHETIC','basis_criterion_reference':'Synthetic software fixture only','basis_target_fraction':'0.5','basis_uncertainty_reference':'Synthetic convergence benchmark','basis_voting':'1','basis_actor':'SYNTHETIC_UI_TEST'})
 window.basis_dialog();assert not errors,errors;assert w.row(s,'study_basis','STUDY')
 fixture=json.loads((ROOT/'examples/SYNTHETIC_PERFORMANCE_PREPARATION.json').read_text());import_dataset(s,'SYN-PERF-A',json.dumps(fixture).encode(),'AUTOMATION_ENGINE')
 automate({'performance_dataset':'SYN-PERF-A','performance_link_actor':'SYNTHETIC_UI_TEST'});window.link_performance_dialog();assert not errors,errors
 review_draft(s,'SYN-REVIEW-01','BASIS','STUDY','NEEDS_INFORMATION','SYNTHETIC_REVIEWER','No authorised physical detector method or qualification is supplied','SYN-GEOM-01')
 r=readiness(s);assert r['input_status']=='INPUTS_PRESENT';assert r['engineering_calculation_status']=='BLOCKED'
 window.suppress_diagnostic_popup=True;target={'center_m':[8,3,3],'u':[0,1,0],'v':[0,0,1],'width_m':2,'height_m':2,'nx':8,'ny':8}
 window.start_geometry_inspection('SYN-GEO-01','SYNTHETIC_UI_TEST',[1,1,3],['V101','WALL'],target,1e-8)
 deadline=time.monotonic()+30
 while window.geometry_job and time.monotonic()<deadline:app.processEvents();QTest.qWait(20)
 assert window.geometry_job is None and window.last_geometry_result;assert len(window.last_geometry_result['samples'])==64
 current=normalized_snapshot(s);window.last_comparison=compare_snapshots(previous,current);assert window.last_comparison['changes']
 window.refresh();window.viewer.camera('Isometric');app.processEvents()
 for theme in ('grey','dark','light'):
  window.theme.setCurrentText(theme);app.processEvents();assert window.grab().save(str(ROOT/'screenshots'/('REV_D_WORKFLOW_'+theme+'.png')))
 output=Path(args.output_dir).resolve() if args.output_dir else ROOT/'OUTPUT_SAMPLES'/('REV_D_STUDY_'+run_id)
 window.start_report(output);deadline=time.monotonic()+60
 while window.report_job and time.monotonic()<deadline:app.processEvents();QTest.qWait(20)
 assert window.report_job is None;assert (output/'QA.json').exists();qa=json.loads((output/'QA.json').read_text());assert qa['status']=='PASS';assert qa['change_rows']>0
 s.save();destination=Path(args.case_output).resolve() if args.case_output else ROOT/'examples'/('SYNTHETIC_REV_D_'+run_id+'.fgcase')
 if destination.exists():raise ValueError('Saved example path already exists')
 window.close();app.processEvents();shutil.copyfile(case,destination)
 restored=root/'restored.fgcase';restore=RestoreJob(destination,restored,'SYNTHETIC_TEST_ACTOR').result();assert restored.exists()
 with CaseSession(restored,root/'restore_runtime') as check:assert check.con.execute('PRAGMA user_version').fetchone()[0]==3;assert readiness(check)['engineering_calculation_status']=='BLOCKED'
 print(json.dumps({'status':'PASS','Qt_platform':app.platformName(),'Windows':'NOT RUN','checks':['explicit mount dialog','basis dialog with explicit voting','performance preparation exact-match link dialog','draft review without approval','input readiness separate from engineering gate','cancellable geometry worker and 64 traces','diagnostic overlay','revision comparison','all-format report and QA','three-theme screenshots','schema3 save/reopen','restore-as-new worker'],'readiness':r,'geometry_bounds':[window.last_geometry_result['visibility_lower_bound'],window.last_geometry_result['visibility_upper_bound']],'output':str(output),'saved_case':str(destination)},indent=2))
