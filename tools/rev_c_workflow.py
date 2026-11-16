"""Execute actual Qt forms, virtual register, paste preview and report export.

Linux offscreen evidence only, not Windows platform acceptance.
"""
import json,os,tempfile,time,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QDialog,QLineEdit,QDoubleSpinBox,QDialogButtonBox
from PySide6.QtCore import Qt,QTimer
from PySide6.QtTest import QTest
from fgmapping.ui.main import MainWindow
from fgmapping.services.case import CaseSession,create_case
from fgmapping.services.geometry import enable_geometry,set_scene,get_scene
from fgmapping.domain.scene import synthetic_scene
from fgmapping.services import workspace
import argparse
from datetime import datetime
parser=argparse.ArgumentParser();parser.add_argument('--output-dir');parser.add_argument('--case-output');args=parser.parse_args()
run_id=datetime.now().strftime('%Y%m%dT%H%M%S%f')
ROOT=Path(__file__).resolve().parents[1];app=QApplication([]);app.setQuitOnLastWindowClosed(False)
errors=[]
def automate(fields,button=QDialogButtonBox.Ok):
 def fill():
  try:
   dialog=app.activeModalWidget();assert isinstance(dialog,QDialog)
   for name,value in fields.items():
    field=dialog.findChild(QLineEdit,name) or dialog.findChild(QDoubleSpinBox,name);assert field is not None,name
    if isinstance(field,QDoubleSpinBox):field.setValue(value)
    else:field.setText(value)
   buttons=dialog.findChild(QDialogButtonBox);QTest.mouseClick(buttons.button(button),Qt.LeftButton)
  except Exception as exc:
   errors.append(str(exc))
   if app.activeModalWidget():app.activeModalWidget().reject()
 QTimer.singleShot(30,fill)
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);p=create_case(root/'syn.fgcase','SYNTHETIC Rev C workflow');w=MainWindow();w.settings.clear();w.session=CaseSession(p,root/'runtime');s=w.session
 enable_geometry(s,'TEST_ENGINE');s.add_evidence('SYN-GEOM-01','SYNTHETIC','Generated envelopes','A','scene','TEST_ENGINE');set_scene(s,synthetic_scene(),'TEST_ENGINE');w.refresh();w.show();app.processEvents()
 automate({'detector_id':'SYN-GUI-01','detector_evidence_id':'SYN-GEOM-01','detector_x':2,'detector_y':3,'detector_z':4,'detector_azimuth':45,'editor_actor':'SYNTHETIC_UI_TEST'})
 w.detector_form(True);assert not errors,errors;assert w.table.rowCount()==1
 w.table.select_id('SYN-GUI-01');automate({'detector_x':6,'editor_actor':'SYNTHETIC_UI_TEST'});w.detector_form(False)
 assert workspace.row(s,'detectors','SYN-GUI-01')['x']==6
 w.workspace_history(False);assert workspace.row(s,'detectors','SYN-GUI-01')['x']==2
 w.workspace_history(True);assert workspace.row(s,'detectors','SYN-GUI-01')['x']==6
 workspace.remove_detector(s,'SYN-GUI-01','SYNTHETIC_UI_TEST');w.refresh();assert w.table.rowCount()==0
 w.workspace_history(False);assert w.table.rowCount()==1
 w.filter_box.setText('NO_MATCH');app.processEvents();assert w.table.rowCount()==0
 w.filter_box.setText('GUI');app.processEvents();assert w.table.rowCount()==1
 w.table.select_id('SYN-GUI-01');w.table.setCurrentIndex(w.table.proxy.index(0,2))
 QTest.keyClick(w.table,Qt.Key_C,Qt.ControlModifier);assert QApplication.clipboard().text()=='6.0'
 automate({'paste_actor':'SYNTHETIC_UI_TEST'},QDialogButtonBox.Apply);w.preview_paste('10\t11\t12',0,2)
 assert not errors,errors;assert workspace.row(s,'detectors','SYN-GUI-01')['x']==10
 marker=next(c for c in get_scene(s).components if c.id=='SYN-GUI-01');assert marker.mesh.vertices[0]==(10,11,12)
 w.tabs.setCurrentIndex(1);automate({'record_id':'SYN-EQUIP-01','record_class':'VESSEL','record_label':'Synthetic vessel','editor_actor':'SYNTHETIC_UI_TEST'});w.record_form(True)
 assert workspace.row(s,'engineering_record','SYN-EQUIP-01') is not None
 w.tabs.setCurrentIndex(2);automate({'record_id':'SYN-FIRE-01','record_high_0':20,'record_high_1':12,'record_high_2':6,'editor_actor':'SYNTHETIC_UI_TEST'});w.record_form(True)
 assert workspace.row(s,'engineering_record','SYN-FIRE-01') is not None
 w.tabs.setCurrentIndex(0);w.filter_box.clear();w.refresh();app.processEvents()
 # Save/reopen and per-case view preservation.
 w.viewer.camera('Top');w.viewer.pan=[12.,23.];s.save();saved=w.viewer.state();w.close_case();w.session=CaseSession(p,root/'runtime');w.refresh()
 caseview=json.loads(w.settings.value('case_view/'+w.session.key));assert caseview['camera']==saved
 w.viewer.camera('Isometric');app.processEvents()
 for theme in ('grey','dark','light'):
  w.theme.setCurrentText(theme);app.processEvents();assert w.grab().save(str(ROOT/'screenshots'/('REV_C_WORKFLOW_'+theme+'.png')))
 from fgmapping.services.calculations import run_synthetic
 exercise=json.loads((ROOT/'examples/SYNTHETIC_FIELD_PATH_EXERCISE.json').read_text())
 run_synthetic(w.session,'SYN-FIELD-PATH',exercise['method'],exercise['inputs'],'AUTOMATION_ENGINE')
 output=Path(args.output_dir).resolve() if args.output_dir else ROOT/'OUTPUT_SAMPLES'/('REV_C_WORKFLOW_STUDY_'+run_id)
 if output.exists():raise ValueError('Workflow sample exists; run in a fresh extraction')
 w.start_report(output)
 deadline=time.monotonic()+40
 while w.report_job is not None and time.monotonic()<deadline:app.processEvents();QTest.qWait(20)
 assert w.report_job is None,'Report did not finish';assert (output/'QA.json').exists();assert json.loads((output/'QA.json').read_text())['status']=='PASS'
 w.session.save();w.close();app.processEvents()
 import shutil
 destination=Path(args.case_output).resolve() if args.case_output else ROOT/'examples'/('SYNTHETIC_REV_C_CONNECTED_'+run_id+'.fgcase')
 if destination.exists():raise ValueError('Connected example already exists')
 shutil.copyfile(p,destination)
 # Case is now closed; examine saved records in independent session.
 with CaseSession(p,root/'verify') as restored:
  assert len(restored.detectors())==1;assert len(workspace.display_annotations(restored)['zones'])==1
 print(json.dumps({'status':'PASS','Qt_platform':app.platformName(),'Windows':'NOT RUN','checks':['actual detector create/edit forms','generic undo/redo','detector removal/restoration','filtered virtual detector grid','Ctrl+C','paste preview/apply','atomic linked-marker bulk move','equipment form','fire zone form and overlay','save/reopen','per-case viewport state','three theme captures','asynchronous five-format report export'],'output':str(output),'saved_case':str(destination)},indent=2))
