"""Candidate study preparation dialogs. All state changes use services."""
import json,hashlib,time
from pathlib import Path
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QFormLayout,QHBoxLayout,QLabel,QLineEdit,QComboBox,QDoubleSpinBox,QSpinBox,QDialogButtonBox,QMessageBox,QPlainTextEdit,QFileDialog,QListWidget,QListWidgetItem,QAbstractItemView,QProgressDialog,QScrollArea,QWidget)
from fgmapping.services.study_schema import enable_study
from fgmapping.services.geometry import get_scene
from fgmapping.services import workspace as w
from fgmapping.services.mounts import set_mount,detach_mount
from fgmapping.domain.mounting import mount_pose
from fgmapping.services.basis import set_basis,readiness
from fgmapping.services.performance import import_dataset,link_dataset,review_draft
from fgmapping.domain.performance import parse_dataset
from fgmapping.services.geometry_inspection import GeometryJob,commit_inspection
from fgmapping.services.comparison import compare_snapshots
from fgmapping.services.reporting import normalized_snapshot
from fgmapping.domain.scene import content_hash

class StudyDialogs:
 def ensure_study(self):
  if not self.ensure_geometry():return False
  if self.session.con.execute('PRAGMA user_version').fetchone()[0]==2:
   if QMessageBox.question(self,'Candidate study schema3','Enable candidate study/mount/performance preparation in this synthetic case? Backups are retained. Older schema2-only versions cannot open schema3.')!=QMessageBox.Yes:return False
   enable_study(self.session,'AUTOMATION_ENGINE')
  return True
 def show_text(self,title,value):
  d=QDialog(self);d.setWindowTitle(title);d.resize(820,590);layout=QVBoxLayout(d);text=QPlainTextEdit();text.setReadOnly(True);text.setPlainText(value if isinstance(value,str) else json.dumps(value,indent=2));layout.addWidget(text)
  buttons=QDialogButtonBox(QDialogButtonBox.Close);buttons.rejected.connect(d.reject);layout.addWidget(buttons);d.exec()
 def wrapped(self,text):
  label=QLabel(text);label.setWordWrap(True);return label
 def evidence_combo(self,current=None):
  field=QComboBox();field.addItems([r[0] for r in self.session.con.execute('SELECT id FROM evidence ORDER BY id')])
  if current:field.setCurrentText(current)
  return field
 def numeric(self,name,value=0,minimum=-1e7,maximum=1e7):
  field=QDoubleSpinBox();field.setDecimals(8);field.setRange(minimum,maximum);field.setValue(value);field.setObjectName(name);return field
 def buttons(self,dialog,layout):
  b=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);b.accepted.connect(dialog.accept);b.rejected.connect(dialog.reject);(layout.addRow(b) if isinstance(layout,QFormLayout) else layout.addWidget(b));return b
 def mount_dialog(self):
  try:
   if not self.ensure_study():return
   scene=get_scene(self.session)
   if scene is None:raise ValueError('Supply facility geometry first')
   detector=self.selected_id() if self.active_kind()=='DETECTOR' else None
   if not detector or w.row(self.session,'detectors',detector) is None:raise ValueError('Select a detector register row first')
   old=w.row(self.session,'detector_mount',detector)
   d=QDialog(self);d.setWindowTitle('Explicit candidate detector mount');form=QFormLayout(d)
   form.addRow(self.wrapped('Source anchor uses declared source units. Offsets are physical metres in orthonormal component axes. Mount feasibility remains unverified.'))
   component=QComboBox();component.setObjectName('mount_component');component.addItems([c.id for c in scene.components if c.semantic!='DETECTOR'])
   if old:
    if component.findText(old['component_id'])<0:component.insertItem(0,'NOT SUPPLIED - prior component missing');component.setCurrentIndex(0)
    else:component.setCurrentText(old['component_id'])
   form.addRow('Facility component',component);info=QLabel();form.addRow(info)
   fields={}
   for group,label,values in [('anchor','Source anchor',json.loads(old['anchor_local_json']) if old else [0,0,0]),('offset','Offset (m)',json.loads(old['offset_m_json']) if old else [0,0,0]),('orientation','Local azimuth / elevation / roll (deg)',json.loads(old['orientation_local_json']) if old else [0,0,0])]:
    for i,axis in enumerate(('X','Y','Z') if group!='orientation' else ('Azimuth','Elevation','Roll')):
     field=self.numeric('mount_'+group+'_'+str(i),values[i]);fields[group,i]=field;form.addRow(label+' '+axis,field)
   def component_info():
    c=next((c for c in scene.components if c.id==component.currentText()),None)
    info.setText('Source frame '+c.frame_id+'; anchor units '+scene.frame(c.frame_id).units if c else 'NOT SUPPLIED')
   component.currentTextChanged.connect(component_info);component_info()
   evidence=self.evidence_combo(old['evidence_id'] if old else None);form.addRow('Mount source evidence',evidence)
   actor=QLineEdit();actor.setObjectName('mount_actor');form.addRow('Named editor required',actor);self.buttons(d,form)
   if d.exec()!=QDialog.Accepted:return
   set_mount(self.session,detector,component.currentText(),[fields['anchor',i].value() for i in range(3)],[fields['offset',i].value() for i in range(3)],[fields['orientation',i].value() for i in range(3)],evidence.currentText(),actor.text());self.refresh()
  except Exception as exc:QMessageBox.critical(self,'Mount refused',str(exc))
 def detach_mount_dialog(self):
  try:
   if not self.ensure_study():return
   detector=self.selected_id()
   from PySide6.QtWidgets import QInputDialog
   actor,ok=QInputDialog.getText(self,'Detach candidate mount','Named editor:')
   if ok:detach_mount(self.session,detector,actor);self.refresh()
  except Exception as exc:QMessageBox.critical(self,'Detach refused',str(exc))
 def basis_dialog(self):
  try:
   if not self.ensure_study():return
   old=w.row(self.session,'study_basis','STUDY');p=json.loads(old['payload_json']) if old else {}
   d=QDialog(self);d.setWindowTitle('Candidate study design basis');form=QFormLayout(d);form.addRow(self.wrapped('Record supplied references and criteria. Missing inputs remain missing; this does not approve a calculation method.'))
   fields={}
   for key,label in [('revision','Basis revision'),('coordinate_reference','Coordinate reference'),('target_description','Target geometry / definition reference'),('fuel_or_gas','Fuel or gas'),('criterion_reference','Performance criterion reference'),('target_fraction','Supplied target fraction 0..1 or NOT SUPPLIED'),('uncertainty_reference','Uncertainty / sensitivity basis')]:
    field=QLineEdit(str(p.get(key,'NOT SUPPLIED')));field.setObjectName('basis_'+key);fields[key]=field;form.addRow(label,field)
   kind=QComboBox();kind.setObjectName('basis_type');kind.addItems(['FLAME','GAS','BOTH']);kind.setCurrentText(p.get('study_type','FLAME'));form.addRow('Study type',kind)
   voting=QComboBox();voting.setObjectName('basis_voting');voting.addItem('NOT SUPPLIED')
   for i in range(1,33):voting.addItem(str(i))
   if 'voting' in p:voting.setCurrentText(str(p['voting']))
   form.addRow('Required votes explicitly selected',voting);evidence=self.evidence_combo(old['evidence_id'] if old else None);form.addRow('Basis evidence',evidence)
   exclusions=QListWidget();exclusions.setSelectionMode(QAbstractItemView.MultiSelection);exclusions.setMaximumHeight(110);scene=get_scene(self.session);prior={x['component_id']:x for x in p.get('exclusions',[])}
   if scene:
    for c in scene.components:
     if c.semantic=='DETECTOR':continue
     item=QListWidgetItem(c.id);exclusions.addItem(item);item.setSelected(c.id in prior)
   form.addRow('Excluded components explicitly selected',exclusions);reason=QLineEdit();reason.setPlaceholderText('Reason for new exclusions; existing reasons retained unless replaced');form.addRow('Exclusion reason',reason)
   actor=QLineEdit();actor.setObjectName('basis_actor');form.addRow('Named editor required',actor);self.buttons(d,form)
   if d.exec()!=QDialog.Accepted:return
   if voting.currentText()=='NOT SUPPLIED':raise ValueError('Explicit voting selection required before saving this basis')
   ex=[]
   for item in exclusions.selectedItems():
    id=item.text();ex.append({'component_id':id,'reason':reason.text().strip() or prior.get(id,{}).get('reason',''),'evidence_id':evidence.currentText() if reason.text().strip() or id not in prior else prior[id]['evidence_id']})
   payload={'contract':'fg-study-basis/1',**{key:field.text() for key,field in fields.items()},'study_type':kind.currentText(),'voting':int(voting.currentText()),'exclusions':ex}
   set_basis(self.session,payload,evidence.currentText(),actor.text());self.refresh()
  except Exception as exc:QMessageBox.critical(self,'Basis refused',str(exc))
 def readiness_dialog(self):
  try:
   if self.ensure_study():self.show_text('Input readiness and separate engineering blockers',readiness(self.session))
  except Exception as exc:QMessageBox.critical(self,'Readiness unavailable',str(exc))
 def import_performance_dialog(self):
  try:
   if not self.ensure_study():return
   path,_=QFileDialog.getOpenFileName(self,'Authorised synthetic preparation JSON only','','JSON (*.json)')
   if not path:return
   source=Path(path)
   if source.stat().st_size>4_000_000:raise ValueError('Performance source exceeds development input budget')
   raw=source.read_bytes();proposal=parse_dataset(raw);d=QDialog(self);d.resize(800,620);d.setWindowTitle('Review synthetic performance preparation');layout=QVBoxLayout(d)
   layout.addWidget(self.wrapped('SYNTHETIC PREPARATION ONLY. No real vendor dataset, interpolation or detector coverage is enabled.'))
   text=QPlainTextEdit();text.setReadOnly(True);text.setPlainText(json.dumps(proposal['payload'],indent=2));layout.addWidget(text)
   form=QFormLayout();layout.addLayout(form);id=QLineEdit();id.setObjectName('performance_id');actor=QLineEdit();actor.setObjectName('performance_actor');form.addRow('New immutable dataset/revision ID',id);form.addRow('Named editor',actor);self.buttons(d,form)
   if d.exec()!=QDialog.Accepted:return
   import_dataset(self.session,id.text(),raw,actor.text());self.refresh()
  except Exception as exc:QMessageBox.critical(self,'Performance import refused',str(exc))
 def link_performance_dialog(self):
  try:
   if not self.ensure_study():return
   detector=self.selected_id()
   if self.active_kind()!='DETECTOR' or not detector:raise ValueError('Select a detector first')
   d=QDialog(self);d.setWindowTitle('Link candidate preparation dataset');form=QFormLayout(d);form.addRow(self.wrapped('Manufacturer/model/sensitivity must match exactly. Engineering calculation remains blocked.'))
   dataset=QComboBox();dataset.setObjectName('performance_dataset');dataset.addItems([r[0] for r in self.session.con.execute('SELECT id FROM performance_dataset ORDER BY id')]);form.addRow('Dataset',dataset);evidence=self.evidence_combo();form.addRow('Assignment evidence',evidence)
   actor=QLineEdit();actor.setObjectName('performance_link_actor');form.addRow('Named editor',actor);self.buttons(d,form)
   if d.exec()==QDialog.Accepted:link_dataset(self.session,detector,dataset.currentText(),evidence.currentText(),actor.text());self.refresh()
  except Exception as exc:QMessageBox.critical(self,'Dataset link refused',str(exc))
 def review_preparation_dialog(self):
  try:
   if not self.ensure_study():return
   d=QDialog(self);d.setWindowTitle('Record draft preparation review');form=QFormLayout(d);form.addRow(self.wrapped('This records a draft review only. Approval and engineering qualification are not available.'))
   kind=QComboBox();kind.addItems(['BASIS','MOUNT','PERFORMANCE']);subject=QComboBox()
   def update_subject():
    table={'BASIS':'study_basis','MOUNT':'detector_mount','PERFORMANCE':'performance_dataset'}[kind.currentText()];key=w.TABLES[table][0];subject.clear();subject.addItems([r[0] for r in self.session.con.execute('SELECT '+key+' FROM '+table+' ORDER BY '+key)])
   kind.currentTextChanged.connect(update_subject);update_subject();form.addRow('Subject kind',kind);form.addRow('Subject ID',subject)
   decision=QComboBox();decision.addItems(['DRAFT_REVIEW','NEEDS_INFORMATION','REJECTED']);form.addRow('Draft decision',decision)
   fields={}
   for key,label in [('id','New review ID'),('reviewer','Named reviewer'),('rationale','Rationale')]:field=QLineEdit();fields[key]=field;form.addRow(label,field)
   evidence=self.evidence_combo();form.addRow('Review evidence',evidence);self.buttons(d,form)
   if d.exec()==QDialog.Accepted:review_draft(self.session,fields['id'].text(),kind.currentText(),subject.currentText(),decision.currentText(),fields['reviewer'].text(),fields['rationale'].text(),evidence.currentText());self.refresh()
  except Exception as exc:QMessageBox.critical(self,'Draft review refused',str(exc))
 def geometry_inspection_dialog(self):
  try:
   if not self.ensure_geometry():return
   scene=get_scene(self.session)
   if scene is None:raise ValueError('Load geometry first')
   d=QDialog(self);d.resize(720,700);d.setWindowTitle('Geometric target inspection only');outer=QVBoxLayout(d);scroll=QScrollArea();scroll.setWidgetResizable(True);body=QWidget();form=QFormLayout(body);scroll.setWidget(body);outer.addWidget(scroll);form.addRow(self.wrapped('Surface obstruction diagnostic, not flame/gas coverage. Indeterminate samples remain in the denominator.'))
   fields={}
   for group,label,values in [('origin','Origin m',(0,0,3)),('center','Target center m',(8,3,3)),('u','Unit target U',(0,1,0)),('v','Unit target V',(0,0,1))]:
    for i,axis in enumerate('XYZ'):field=self.numeric('geometry_'+group+'_'+str(i),values[i]);fields[group,i]=field;form.addRow(label+' '+axis,field)
   width=self.numeric('geometry_width',2,.000001,1e6);height=self.numeric('geometry_height',2,.000001,1e6);form.addRow('Supplied geometric target width m',width);form.addRow('Supplied geometric target height m',height)
   n=QSpinBox();n.setRange(1,64);n.setValue(8);n.setObjectName('geometry_n');form.addRow('Samples per axis',n)
   eps=self.numeric('geometry_tolerance',.000001,.00000001,.001);form.addRow('Numerical tolerance m',eps)
   obstacles=QListWidget();obstacles.setMaximumHeight(100);obstacles.setSelectionMode(QAbstractItemView.MultiSelection)
   for c in scene.components:
    if c.semantic!='DETECTOR':obstacles.addItem(c.id)
   form.addRow('Explicit obstruction selection',obstacles)
   id=QLineEdit();id.setObjectName('geometry_id');actor=QLineEdit();actor.setObjectName('geometry_actor');form.addRow('Unique diagnostic run ID',id);form.addRow('Named editor',actor);self.buttons(d,outer)
   if d.exec()!=QDialog.Accepted:return
   if not id.text().strip() or not actor.text().strip():raise ValueError('Diagnostic ID and actor required')
   target={'center_m':[fields['center',i].value() for i in range(3)],'u':[fields['u',i].value() for i in range(3)],'v':[fields['v',i].value() for i in range(3)],'width_m':width.value(),'height_m':height.value(),'nx':n.value(),'ny':n.value()}
   self.start_geometry_inspection(id.text(),actor.text(),[fields['origin',i].value() for i in range(3)],[x.text() for x in obstacles.selectedItems()],target,eps.value())
  except Exception as exc:QMessageBox.critical(self,'Geometry inspection refused',str(exc))
 def start_geometry_inspection(self,id,actor,origin,obstacles,target,eps):
  if self.geometry_job:raise ValueError('A geometry diagnostic is already running')
  self.geometry_run_id=id;self.geometry_actor=actor;self.geometry_job=GeometryJob(get_scene(self.session),origin,obstacles,target,eps);self.geometry_deadline=time.monotonic()+30;self.geometry_timer.start(100)
  self.geometry_progress=QProgressDialog('Running geometric demonstration','Cancel',0,0,self);self.geometry_progress.canceled.connect(self.cancel_geometry);self.geometry_progress.show()
 def cancel_geometry(self):
  if self.geometry_job:self.geometry_job.cancel();self.geometry_job=None
  self.geometry_timer.stop()
  if hasattr(self,'geometry_progress'):self.geometry_progress.close()
 def poll_geometry(self):
  if not self.geometry_job:return
  if time.monotonic()>self.geometry_deadline:self.cancel_geometry();self.status.setText('Geometry diagnostic timed out; no result committed');return
  if self.geometry_job.process.poll() is None:return
  job=self.geometry_job;self.geometry_job=None;self.geometry_timer.stop();self.geometry_progress.close()
  try:
   result=job.result();commit_inspection(self.session,self.geometry_run_id,job.inputs,result,self.geometry_actor);self.last_geometry_result=result;self.viewer.inspection_result=result;self.viewer.update()
   self.status.setText('GEOMETRIC DEMONSTRATION ONLY | visible bounds '+str(result['visibility_lower_bound'])+' .. '+str(result['visibility_upper_bound'])+' | UNVERIFIED')
   if not getattr(self,'suppress_diagnostic_popup',False):self.show_text('Geometric diagnostic trace / not coverage',{k:v for k,v in result.items() if k!='samples'}|{'sample_trace':result['samples']})
  except Exception as exc:QMessageBox.critical(self,'Diagnostic failed',str(exc))
 def compare_snapshot_dialog(self):
  try:
   if not self.session:return
   path,_=QFileDialog.getOpenFileName(self,'Prior synthetic normalized snapshot','','JSON (*.json)')
   if not path:return
   p=Path(path)
   if p.stat().st_size>16_000_000:raise ValueError('Snapshot comparison input exceeds development budget')
   self.last_comparison=compare_snapshots(json.loads(p.read_text()),normalized_snapshot(self.session));self.show_text('Stable-ID study revision comparison',self.last_comparison)
  except Exception as exc:QMessageBox.critical(self,'Comparison refused',str(exc))
 def restore_backup_dialog(self):
  try:
   from fgmapping.services.recovery import inspect_backup,RestoreJob
   from PySide6.QtWidgets import QInputDialog
   path,_=QFileDialog.getOpenFileName(self,'Choose backup to restore as a NEW case',str(self.session.runtime/'Backups') if self.session else '', 'Cases (*.fgcase)')
   if not path:return
   info=inspect_backup(path);self.show_text('Verified backup metadata / original remains untouched',info)
   target,_=QFileDialog.getSaveFileName(self,'New restored case path','','Cases (*.fgcase)')
   if not target:return
   actor,ok=QInputDialog.getText(self,'Restore as new case','Named restoration actor:')
   if not ok:return
   if self.restore_job:raise ValueError('A backup restore is already running')
   self.restore_job=RestoreJob(path,target,actor);self.restore_deadline=time.monotonic()+60;self.restore_timer.start(100)
   self.restore_progress=QProgressDialog('Restoring backup into a NEW case','Cancel',0,0,self);self.restore_progress.canceled.connect(self.cancel_restore);self.restore_progress.show()
  except Exception as exc:QMessageBox.critical(self,'Restore refused',str(exc))

 def cancel_restore(self):
  if self.restore_job:self.restore_job.cancel();self.restore_job=None
  self.restore_timer.stop()
  if hasattr(self,'restore_progress'):self.restore_progress.close()
 def poll_restore(self):
  if not self.restore_job:return
  if time.monotonic()>self.restore_deadline:self.cancel_restore();self.status.setText('Restore timed out; inspect the new target before retrying');return
  if self.restore_job.process.poll() is None:return
  job=self.restore_job;self.restore_job=None;self.restore_timer.stop();self.restore_progress.close()
  try:
   result=job.result();self.status.setText('Restored NEW case: '+result['path']+' | original untouched')
  except Exception as exc:QMessageBox.critical(self,'Restore failed',str(exc))
