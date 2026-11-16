"""Reviewed source preparation UI; parsing/planning runs in a killable worker."""
import json,time,hashlib
from pathlib import Path
from PySide6.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QLineEdit,QPlainTextEdit,QDialogButtonBox,QFileDialog,QProgressDialog,QMessageBox
from fgmapping.services.preparation_job import PreparationJob
from fgmapping.services.preparation import apply_plan
class PreparationDialogs:
 def bulk_import_dialog(self):
  if not self.ensure_geometry():return
  path,_=QFileDialog.getOpenFileName(self,'Synthetic register source','','CSV (*.csv);;Excel (*.xlsx)')
  if path:
   try:self.start_preparation(Path(path).read_bytes(),'XLSX' if Path(path).suffix.lower()=='.xlsx' else 'CSV','BULK_REGISTER')
   except Exception as exc:QMessageBox.critical(self,'Preparation refused',str(exc))
 def revision_import_dialog(self):
  if not self.ensure_geometry():return
  path,_=QFileDialog.getOpenFileName(self,'Synthetic geometry revision and explicit mount decisions','','JSON (*.json)')
  if path:
   try:self.start_preparation(Path(path).read_bytes(),'JSON','GEOMETRY_REVISION')
   except Exception as exc:QMessageBox.critical(self,'Revision refused',str(exc))
 def start_preparation(self,raw,format,kind):
  if self.preparation_job:raise ValueError('A preparation preview is already running')
  self.preparation_job=PreparationJob(self.session,raw,format,kind);self.preparation_deadline=time.monotonic()+30
  self.preparation_progress=QProgressDialog('Preparing synthetic source preview; case is unchanged','Cancel',0,0,self);self.preparation_progress.setWindowTitle('Candidate preparation');self.preparation_progress.canceled.connect(self.cancel_preparation);self.preparation_progress.show();self.preparation_timer.start(100)
 def cancel_preparation(self):
  self.preparation_timer.stop()
  if self.preparation_job:self.preparation_job.cancel();self.preparation_job=None
  if hasattr(self,'preparation_progress'):self.preparation_progress.close()
 def poll_preparation(self):
  if not self.preparation_job:return
  if time.monotonic()>self.preparation_deadline:self.cancel_preparation();self.status.setText('Preparation timed out; case unchanged');return
  if self.preparation_job.process.poll() is None:return
  job=self.preparation_job;self.preparation_job=None;self.preparation_timer.stop();self.preparation_progress.close()
  try:
   plan=job.result();self.last_preparation_plan=plan;self.review_preparation_plan(plan)
  except Exception as exc:QMessageBox.critical(self,'Preparation refused',str(exc))
 def review_preparation_plan(self,plan):
  dialog=QDialog(self);dialog.setObjectName('preparation_review');dialog.setWindowTitle('Review '+plan.kind.replace('_',' ').lower());dialog.resize(900,660);layout=QVBoxLayout(dialog)
  layout.addWidget(self.wrapped('Apply candidate changes only after reviewing this preview. Engineering acceptance remains UNVERIFIED. Source bytes and rationale will be retained; edits can be undone.'))
  rows=[]
  for change in json.loads(plan.changes_json):
   before,after=change['before'],change['after'];fields=[]
   for key in sorted(set(before or {})|set(after or {})):
    a=(before or {}).get(key);b=(after or {}).get(key)
    if a==b:continue
    def text(v):
     t=json.dumps(v,ensure_ascii=False)
     return t if len(t)<=250 else '[Full value retained; SHA256 '+hashlib.sha256(t.encode()).hexdigest()+']'
    fields.append(key+': '+text(a)+' → '+text(b))
   rows.append(change['table']+' / '+str(change['key'])+'\n'+'\n'.join(fields))
  preview=QPlainTextEdit();preview.setObjectName('preparation_preview');preview.setReadOnly(True);preview.setPlainText('SOURCE SHA256 '+plan.source_sha256+'\n'+json.dumps(json.loads(plan.summary_json),indent=2)+'\n\n'+'\n\n'.join(rows));layout.addWidget(preview,1)
  form=QFormLayout();actor=QLineEdit();actor.setObjectName('preparation_actor');reason=QLineEdit();reason.setObjectName('preparation_reason');form.addRow('Named editor',actor);form.addRow('Review rationale',reason);layout.addLayout(form)
  buttons=QDialogButtonBox(QDialogButtonBox.Apply|QDialogButtonBox.Cancel);buttons.button(QDialogButtonBox.Apply).clicked.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
  if dialog.exec()!=QDialog.Accepted:return
  apply_plan(self.session,plan,actor.text(),reason.text());self.refresh();self.status.setText('Candidate preparation applied with retained source | engineering UNVERIFIED')
