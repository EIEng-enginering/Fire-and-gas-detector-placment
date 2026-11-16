"""First Windows Qt user interface, no engineering coverage results shown."""
from __future__ import annotations
import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
    QPushButton,QTableWidget,QTableWidgetItem,QLabel,QFileDialog,QInputDialog,QMessageBox,
    QComboBox,QSplitter,QGroupBox,QFormLayout,QLineEdit,QDoubleSpinBox,QTreeWidget,QTreeWidgetItem,QTabWidget,QTableView,QDialog,QDialogButtonBox,QCheckBox,QPlainTextEdit,QProgressDialog)
from PySide6.QtCore import Qt, QSettings, QTimer
from fgmapping.services.case import CaseSession,create_case
from fgmapping.errors import CaseError
from fgmapping.ui.viewer import MeshViewer
from fgmapping.services.geometry import enable_geometry,get_scene,set_scene,compensate_scene
from fgmapping.domain.scene import synthetic_scene,Frame,Mesh,Scene,Component
from fgmapping.services.mesh_import import ImportJob
from fgmapping.ui.register_model import RegisterModel
from fgmapping.ui.worksheet import WorksheetView
from fgmapping.services import workspace
from fgmapping.services.paste import detector_paste_preview
from fgmapping.services.reporting import normalized_snapshot
from fgmapping.services.report_job import ReportJob
from fgmapping.services.import_review import ImportProposal
from fgmapping.services.findings import study_findings
from fgmapping.services.registers import records,edit_detector,store_attachment,detector_history
import json,hashlib
from fgmapping.theme import stylesheet,THEMES
from fgmapping.ui.study_dialogs import StudyDialogs
from fgmapping.domain.scene import content_hash

def local_root() -> Path:
    return Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local'/'share')))/'FGMappingEngineering'

from fgmapping.ui.preparation_dialogs import PreparationDialogs

class MainWindow(PreparationDialogs,StudyDialogs,QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Fire & Gas Mapping Engineering System | DEVELOPMENT BUILD')
        self.resize(1250,780)
        self.session=None
        root=QWidget();self.setCentralWidget(root)
        base=QVBoxLayout(root)
        menu=self.menuBar().addMenu('Case')
        menu.addAction('New case',self.new_case)
        menu.addAction('Open case',self.open_case)
        menu.addAction('Save case',self.save_case)
        menu.addAction('Close case',self.close_case)
        menu.addAction('Export synthetic study reports',self.export_reports)
        menu.addAction('Run supplied synthetic exercise',self.run_exercise)
        menu.addAction('Restore backup as new case',self.restore_backup_dialog)
        menu.addAction('Compare prior study snapshot',self.compare_snapshot_dialog)
        menu.addAction('Import synthetic register CSV / Excel',self.bulk_import_dialog)
        menu.addAction('Review synthetic facility revision',self.revision_import_dialog)
        study=self.menuBar().addMenu('Study preparation')
        for title,callback in [('Mount selected detector',self.mount_dialog),('Detach selected mount',self.detach_mount_dialog),('Edit candidate design basis',self.basis_dialog),('Input readiness and engineering blockers',self.readiness_dialog),('Import synthetic performance preparation',self.import_performance_dialog),('Link selected detector dataset',self.link_performance_dialog),('Record draft preparation review',self.review_preparation_dialog),('Geometric target inspection only',self.geometry_inspection_dialog)]:study.addAction(title,callback)
        top=QHBoxLayout();base.addLayout(top)
        self.header=QLabel('DEVELOPMENT BUILD | no study loaded')
        top.addWidget(self.header,1)
        self.theme=QComboBox();self.theme.addItems(['grey','dark','light'])
        self.theme.currentTextChanged.connect(self.apply_theme)
        top.addWidget(self.theme)
        splitter=QSplitter(Qt.Horizontal);base.addWidget(splitter,1)
        pane=QWidget();left=QVBoxLayout(pane)
        left.addWidget(QLabel('Detector register (CANDIDATE records only)'))
        self.table=WorksheetView(('Tag','Type','X (m)','Y (m)','Z (m)','Evidence ID','Review'))
        self.tabs=QTabWidget();self.tabs.addTab(self.table,'Detectors');left.addWidget(self.tabs)
        self.register_views={}
        for title,kind in [('Equipment','EQUIPMENT'),('Fire zones','FIRE_ZONE'),('Gas zones','GAS_ZONE')]:
            view=WorksheetView(('ID','Evidence','Review','Inputs'));self.tabs.addTab(view,title);self.register_views[kind]=(view,view.cache)
            view.cellClicked.connect(lambda row,col,v=view:self.record_selection(v,row))
        self.filter_box=QLineEdit();self.filter_box.setPlaceholderText('Filter current register');left.addWidget(self.filter_box)
        self.filter_box.textChanged.connect(self.filter_current);self.tabs.currentChanged.connect(lambda:self.filter_current(self.filter_box.text()))
        for title,callback in [('Add candidate record',self.add_candidate),('Edit selected record',self.edit_candidate),('Remove selected candidate record',self.remove_candidate),('Inspect evidence / findings',self.inspect_evidence)]:
            button=QPushButton(title);button.clicked.connect(callback);left.addWidget(button)
        history=QHBoxLayout();left.addLayout(history)
        for title,redo in [('Undo workspace edit',False),('Redo workspace edit',True)]:
            button=QPushButton(title);button.clicked.connect(lambda checked=False,r=redo:self.workspace_history(r));history.addWidget(button)
        self.table.pasteRequested.connect(self.preview_paste)
        for view in [self.table]+[v for v,m in self.register_views.values()]:
            view.notice.connect(lambda text:self.status.setText(text));view.doubleClicked.connect(lambda:self.edit_candidate())
        splitter.addWidget(pane)
        right=QGroupBox('3D facility | CANDIDATE geometry')
        rv=QVBoxLayout(right)
        controls=QHBoxLayout();rv.addLayout(controls)
        for name in ('Isometric','Top','Front','Side','Perspective'):
            button=QPushButton(name);button.clicked.connect(lambda checked=False,n=name:self.viewer.camera(n));controls.addWidget(button)
        fit=QPushButton('Fit');fit.clicked.connect(lambda:self.viewer.fit());controls.addWidget(fit)
        self.viewer=MeshViewer();rv.addWidget(self.viewer,1)
        self.tree=QTreeWidget();self.tree.setHeaderLabels(['Component / visible','Kind / geometry QA'])
        self.tree.setMaximumHeight(170);rv.addWidget(self.tree)
        self.tree.itemChanged.connect(self.geometry_visibility)
        self.tree.currentItemChanged.connect(self.geometry_selection)
        self.viewer.selected.connect(self.select_geometry)
        self.table.cellClicked.connect(self.select_detector_geometry)
        for title,callback in [('Load synthetic module',self.load_synthetic),('Import synthetic mesh',self.import_mesh),('Cancel import',self.cancel_import),('Undo scene',lambda:self.scene_history(False)),('Redo scene',lambda:self.scene_history(True))]:
            button=QPushButton(title);button.clicked.connect(callback);left.addWidget(button)
        self.preparation_job=None
        self.last_preparation_plan=None
        self.preparation_timer=QTimer(self);self.preparation_timer.timeout.connect(self.poll_preparation)
        self.restore_job=None
        self.restore_timer=QTimer(self);self.restore_timer.timeout.connect(self.poll_restore)
        self.geometry_job=None
        self.geometry_timer=QTimer(self);self.geometry_timer.timeout.connect(self.poll_geometry)
        self.last_comparison=None
        self.last_geometry_result=None
        self.report_job=None
        self.report_timer=QTimer(self);self.report_timer.timeout.connect(self.poll_report)
        self.import_job=None
        self.import_timer=QTimer(self);self.import_timer.timeout.connect(self.poll_import)
        splitter.addWidget(right)
        splitter.setSizes([420,830])
        self.settings=QSettings('EIE','FGMappingEngineeringCandidate')
        for i,view in enumerate([self.table]+[v for v,m in self.register_views.values()]):
            state=self.settings.value('columns/'+str(i))
            if state is not None:view.horizontalHeader().restoreState(state)
        viewport=self.settings.value('viewport','')
        if viewport:
            try:self.viewer.restore(json.loads(viewport))
            except (ValueError,TypeError):pass
        self.status=QLabel('No calculations | Engine qualification: UNVERIFIED')
        base.addWidget(self.status)
        saved_theme=self.settings.value('theme','grey')
        if saved_theme not in THEMES:saved_theme='grey'
        self.theme.setCurrentText(saved_theme);self.apply_theme(saved_theme)

    def apply_theme(self,name):
        self.setStyleSheet(stylesheet(name))
        self.table.cache.theme=name;self.table.viewport().update()
        if hasattr(self,'settings'):self.settings.setValue('theme',name)
        self.viewer.theme=name;self.viewer.update()
        if hasattr(self,'register_views'):
            for view,model in self.register_views.values():model.theme=name;view.viewport().update()

    def new_case(self):
        if self.session:
            QMessageBox.information(self,'Close first','Close the current case before creating another.')
            return
        name,ok=QInputDialog.getText(self,'New case','Synthetic study name:')
        if not ok or not name.strip():return
        path,_=QFileDialog.getSaveFileName(self,'New .fgcase case','','Fire and Gas Case (*.fgcase)')
        if not path:return
        try:
            create_case(path,name)
            self.start_case(path)
        except Exception as e:QMessageBox.critical(self,'Case error',str(e))

    def open_case(self):
        if self.session:
            QMessageBox.information(self,'Close first','Close the current case before opening another.')
            return
        path,_=QFileDialog.getOpenFileName(self,'Open .fgcase case','','Fire and Gas Case (*.fgcase)')
        if path:self.start_case(path)

    def start_case(self,path):
        try:
            self.session=CaseSession(path,local_root())
        except CaseError as e:
            if e.code=='RECOVERY_REQUIRED':
                msg=QMessageBox.question(self,'Recovery available','An unsaved local session exists. Recover it?')
                if msg==QMessageBox.Yes:
                    try:self.session=CaseSession(path,local_root(),recover=True)
                    except Exception as err:QMessageBox.critical(self,'Recovery blocked',str(err));return
                else:return
            else:QMessageBox.critical(self,'Case error',str(e));return
        self.refresh()
        saved=self.settings.value('case_view/'+self.session.key,'')
        if saved:
            try:
                value=json.loads(saved);self.viewer.restore(value['camera']);self.viewer.hidden=set(value.get('hidden',[]));self.viewer.update()
                self.refresh_geometry()
            except (ValueError,KeyError,TypeError):pass

    def refresh(self):
        if not self.session:return
        self.header.setText(f"DEVELOPMENT BUILD | {self.session.name()}")
        rows=self.session.detectors()
        selected=self.table.item(self.table.currentRow(),0).text() if self.table.currentRow()>=0 else None
        self.table.set_rows(('Tag','Type','X (m)','Y (m)','Z (m)','Evidence ID','Review'),rows)
        if selected:self.table.select_id(selected)
        self.refresh_geometry()
        if self.session.con.execute('PRAGMA user_version').fetchone()[0]>=2:
            for kind,(view,model) in self.register_views.items():
                view.set_rows(('ID','Evidence','Review','Inputs'),[(r['id'],r['evidence_id'],r['review_status'],json.dumps(r['payload'])) for r in records(self.session,kind)])
        self.status.setText(f'{len(rows)} CANDIDATE detectors | NO COVERAGE | UNVERIFIED')

    def add_detector(self):
        self.detector_form(True)

    def save_case(self):
        if self.session:
            try:self.session.save();self.status.setText('Case saved atomically | DEVELOPMENT BUILD')
            except Exception as e:QMessageBox.critical(self,'Save blocked',str(e))

    def close_case(self):
        if not self.session:return
        self.cancel_preparation()
        self.cancel_import()
        self.cancel_report()
        self.cancel_geometry()
        self.cancel_restore()
        self.settings.setValue('case_view/'+self.session.key,json.dumps({'camera':self.viewer.state(),'hidden':sorted(self.viewer.hidden)}))
        for i,view in enumerate([self.table]+[v for v,m in self.register_views.values()]):self.settings.setValue('columns/'+str(i),view.horizontalHeader().saveState())
        if self.session._dirty:
            response=QMessageBox.question(self,'Unsaved work','Yes: save. No: preserve unsaved work for recovery. Cancel: keep editing.',QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if response==QMessageBox.Cancel:return
            if response==QMessageBox.Yes:
                try:self.session.save()
                except Exception as e:QMessageBox.critical(self,'Save blocked',str(e));return
            else:
                self.session.close(discard_unsaved=False);self.session=None;self.table.setRowCount(0);self.refresh_geometry();return
        self.session.close();self.session=None
        self.table.setRowCount(0);self.refresh_geometry();self.header.setText('DEVELOPMENT BUILD | no study loaded')

    def edit_selected_detector(self):
        self.detector_form(False)

    def detector_history_action(self,redo):
        if not self.session:return
        try:detector_history(self.session,'AUTOMATION_ENGINE',redo);self.refresh()
        except Exception as exc:QMessageBox.information(self,'Detector history',str(exc))

    def active_kind(self):
        return ('DETECTOR','EQUIPMENT','FIRE_ZONE','GAS_ZONE')[self.tabs.currentIndex()]

    def active_view(self):return self.tabs.currentWidget()
    def filter_current(self,text):self.active_view().filter(text)
    def selected_id(self):
        view=self.active_view();return view.item(view.currentRow(),0).text() if view.currentRow()>=0 else None
    def add_candidate(self):
        if self.active_kind()=='DETECTOR':self.detector_form(True)
        else:self.record_form(True)
    def edit_candidate(self):
        if self.active_kind()=='DETECTOR':self.detector_form(False)
        else:self.record_form(False)
    def workspace_history(self,redo):
        if not self.session:return
        try:workspace.history(self.session,'AUTOMATION_ENGINE',redo);self.refresh()
        except Exception as exc:QMessageBox.information(self,'Workspace history',str(exc))
    def remove_candidate(self):
        if not self.session:return
        id=self.selected_id()
        if not id:return
        if QMessageBox.question(self,'Remove study record','Remove '+id+' from the study? Its prior values remain in the immutable undo ledger; source evidence is retained.')!=QMessageBox.Yes:return
        try:
            if self.active_kind()=='DETECTOR':workspace.remove_detector(self.session,id,'AUTOMATION_ENGINE')
            else:workspace.remove_record(self.session,id,'AUTOMATION_ENGINE')
            self.refresh()
        except Exception as exc:QMessageBox.critical(self,'Removal refused',str(exc))
    def record_selection(self,view,row):
        if not self.session:return
        id=view.item(row,0).text()
        found=next((r for r in records(self.session) if r['id']==id),None)
        if found and found['payload'].get('geometry_component_id'):
            self.viewer.selection=found['payload']['geometry_component_id'];self.viewer.update()

    def detector_form(self,create):
        if not self.ensure_geometry():return
        id=None if create else self.selected_id()
        old=None if create else workspace.row(self.session,'detectors',id)
        if not create and old is None:return
        details=workspace.row(self.session,'detector_details',id) if old else None
        dialog=QDialog(self);dialog.setWindowTitle('Add candidate detector' if create else 'Edit candidate detector')
        form=QFormLayout(dialog);form.addRow(QLabel('Synthetic placement in SI metres. No detector coverage or engineering acceptance.'))
        fields={}
        for key,label in [('id','Detector ID'),('evidence_id','Evidence ID'),('manufacturer','Manufacturer'),('model','Model'),('sensitivity','Sensitivity')]:
            default=(old or {}).get(key,(details or {}).get(key,'' if key in ('id','evidence_id') else 'NOT SUPPLIED'))
            field=QLineEdit(str(default));fields[key]=field;field.setObjectName('detector_'+key);form.addRow(label,field)
        fields['id'].setReadOnly(not create)
        kind=QComboBox();kind.addItems(['FLAME','POINT_GAS','OPEN_PATH','ULTRASONIC']);kind.setCurrentText((old or {}).get('detector_type','FLAME'));form.addRow('Detector type',kind)
        for key,label in [('x','X (m)'),('y','Y (m)'),('z','Z (m)'),('azimuth','Azimuth (deg)'),('elevation','Elevation (deg)'),('roll','Roll (deg)')]:
            field=QDoubleSpinBox();field.setDecimals(6);field.setRange(-1e7,1e7);field.setValue((old or {}).get(key,(details or {}).get(key,0)));fields[key]=field;field.setObjectName('detector_'+key);form.addRow(label,field)
        desc=QLineEdit();revision=QLineEdit();locator=QLineEdit()
        form.addRow('New source description',desc);form.addRow('Source revision',revision);form.addRow('Source page / locator',locator)
        marker=QCheckBox('Create explicit synthetic placement marker if none exists');marker.setChecked(True);form.addRow(marker)
        actor=QLineEdit();actor.setObjectName('editor_actor');form.addRow('Named editor required',actor)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);form.addRow(buttons)
        if dialog.exec()!=QDialog.Accepted:return
        try:
            values={k:(f.value() if isinstance(f,QDoubleSpinBox) else f.text().strip()) for k,f in fields.items()};values['detector_type']=kind.currentText()
            evidence=None
            if workspace.row(self.session,'evidence',values['evidence_id']) is None:evidence=workspace.synthetic_evidence(values['evidence_id'],desc.text(),revision.text(),locator.text())
            workspace.detector_command(self.session,values,evidence,actor.text(),create=create,place_marker=marker.isChecked());self.refresh();self.table.select_id(values['id'])
        except Exception as exc:QMessageBox.critical(self,'Detector refused',str(exc))

    def record_form(self,create):
        if not self.ensure_geometry():return
        kind=self.active_kind();id=None if create else self.selected_id()
        old=workspace.row(self.session,'engineering_record',id) if id else None
        if not create and old is None:return
        payload=json.loads(old['payload_json']) if old else {}
        dialog=QDialog(self);dialog.setWindowTitle('Candidate '+kind.replace('_',' ').lower());form=QFormLayout(dialog)
        identifier=QLineEdit(id or '');identifier.setObjectName('record_id');identifier.setReadOnly(not create);form.addRow('Persistent record ID',identifier)
        evidence=QComboBox();evidence.addItems([r[0] for r in self.session.con.execute('SELECT id FROM evidence ORDER BY id')]);form.addRow('Evidence ID',evidence)
        if old:evidence.setCurrentText(old['evidence_id'])
        fields={}
        if kind=='EQUIPMENT':
            for key,label in [('label','Equipment name'),('class','Equipment class')]:
                f=QLineEdit(payload.get(key,''));f.setObjectName('record_'+key);form.addRow(label,f);fields[key]=f
            component=QComboBox();component.addItem('NOT SUPPLIED');scene=get_scene(self.session)
            if scene:component.addItems([c.id for c in scene.components])
            component.setCurrentText(payload.get('geometry_component_id','NOT SUPPLIED'));form.addRow('Geometry component',component);fields['geometry_component_id']=component
        else:
            for bound,label in [('low','Lower'),('high','Upper')]:
                for i,axis in enumerate('XYZ'):
                    f=QDoubleSpinBox();f.setRange(-1e7,1e7);f.setDecimals(6);f.setValue(payload.get(bound,[0,0,0] if bound=='low' else [1,1,1])[i]);f.setObjectName('record_'+bound+'_'+str(i));form.addRow(label+' '+axis+' (m)',f);fields[(bound,i)]=f
            criteria=QLineEdit(payload.get('criteria','NOT SUPPLIED'));form.addRow('Design criterion reference',criteria);fields['criteria']=criteria
        actor=QLineEdit();actor.setObjectName('editor_actor');form.addRow('Named editor required',actor)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);form.addRow(buttons)
        if dialog.exec()!=QDialog.Accepted:return
        try:
            if kind=='EQUIPMENT':
                data={k:(f.currentText() if isinstance(f,QComboBox) else f.text()) for k,f in fields.items()}
                if data['geometry_component_id']=='NOT SUPPLIED':data.pop('geometry_component_id')
            else:data={'units':'m','low':[fields['low',i].value() for i in range(3)],'high':[fields['high',i].value() for i in range(3)],'criteria':fields['criteria'].text()}
            workspace.record_command(self.session,identifier.text(),kind,data,evidence.currentText(),actor.text(),create=create);self.refresh();self.active_view().select_id(identifier.text())
        except Exception as exc:QMessageBox.critical(self,'Record refused',str(exc))

    def preview_paste(self,text,start_row,start_col):
        if not self.session or not self.ensure_geometry():return
        try:
            ids=[self.table.item(i,0).text() for i in range(self.table.rowCount())]
            byid={r['id']:r for r in workspace.detector_rows(self.session)}
            patches,preview=detector_paste_preview([byid[id] for id in ids],text,start_row,start_col)
            dialog=QDialog(self);dialog.resize(700,450);dialog.setWindowTitle('Review detector paste');layout=QVBoxLayout(dialog)
            layout.addWidget(QLabel('All changes apply together. Evidence and IDs cannot be pasted.'))
            table=WorksheetView(('Detector','Field','Before','After'));table.set_rows(table.cache.headers,preview);layout.addWidget(table)
            actor=QLineEdit();actor.setObjectName('paste_actor');actor.setPlaceholderText('Named editor required');layout.addWidget(actor)
            buttons=QDialogButtonBox(QDialogButtonBox.Apply|QDialogButtonBox.Cancel);buttons.button(QDialogButtonBox.Apply).clicked.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
            if dialog.exec()!=QDialog.Accepted:return
            workspace.paste_detectors(self.session,patches,actor.text());self.refresh()
        except Exception as exc:QMessageBox.critical(self,'Paste refused',str(exc))

    def ensure_geometry(self):
        if not self.session:
            QMessageBox.information(self,'No case','Open a synthetic case first.');return False
        if self.session.con.execute('PRAGMA user_version').fetchone()[0]==1:
            answer=QMessageBox.question(self,'Candidate schema upgrade','Enable candidate geometry schema 2 in this synthetic case? A backup is retained; the original program cannot open schema 2.')
            if answer!=QMessageBox.Yes:return False
            enable_geometry(self.session,'AUTOMATION_ENGINE')
        return True

    def load_synthetic(self):
        try:
            if not self.ensure_geometry():return
            if not self.session.con.execute("SELECT 1 FROM evidence WHERE id='SYN-GEOM-01'").fetchone():
                self.session.add_evidence('SYN-GEOM-01','SYNTHETIC','Generated module envelopes, not actual equipment','SYN-A','domain.scene.synthetic_scene','AUTOMATION_ENGINE')
            set_scene(self.session,synthetic_scene(),'AUTOMATION_ENGINE');self.refresh_geometry()
        except Exception as exc:QMessageBox.critical(self,'Geometry blocked',str(exc))

    def refresh_geometry(self):
        scene=get_scene(self.session) if self.session else None
        old_state=self.viewer.state();hidden=set(self.viewer.hidden);selection=self.viewer.selection
        previous=self.viewer.scene
        self.viewer.set_scene(scene)
        if previous is not None and scene is not None:
            self.viewer.restore(old_state);self.viewer.hidden=hidden;self.viewer.selection=selection
        self.tree.blockSignals(True);self.tree.clear()
        if scene:
            for c in scene.components:
                diag=c.mesh.diagnostics()
                item=QTreeWidgetItem([c.id+' | '+c.label,c.semantic+' | UNVERIFIED'])
                item.setData(0,Qt.UserRole,c.id);item.setCheckState(0,Qt.Unchecked if c.id in self.viewer.hidden else Qt.Checked)
                item.setToolTip(1,json.dumps(diag,indent=2));self.tree.addTopLevelItem(item)
        self.tree.blockSignals(False)
        self.viewer.annotations=workspace.display_annotations(self.session) if self.session and self.session.con.execute('PRAGMA user_version').fetchone()[0]>=2 else {'placements':[],'zones':[]}
        if self.last_geometry_result and (scene is None or self.last_geometry_result['scene_hash']!=scene.sha256):self.viewer.inspection_result=None
        self.viewer.update()

    def geometry_visibility(self,item,column):
        id=item.data(0,Qt.UserRole)
        if item.checkState(0)==Qt.Checked:self.viewer.hidden.discard(id)
        else:self.viewer.hidden.add(id)
        self.viewer.update()

    def geometry_selection(self,item,previous):
        if item:self.viewer.selection=item.data(0,Qt.UserRole);self.viewer.update()

    def select_geometry(self,id):
        for i in range(self.tree.topLevelItemCount()):
            item=self.tree.topLevelItem(i)
            if item.data(0,Qt.UserRole)==id:self.tree.setCurrentItem(item);break
        # Exact identity only; never infer a tag-to-geometry association.
        self.table.select_id(id)
        for kind,(view,model) in self.register_views.items():
            if self.session and self.session.con.execute('PRAGMA user_version').fetchone()[0]>=2:
                for record in records(self.session,kind):
                    if record['payload'].get('geometry_component_id')==id:view.select_id(record['id'])

    def select_detector_geometry(self,row,column):
        self.select_geometry(self.table.item(row,0).text())

    def scene_history(self,redo):
        if not self.session:return
        try:compensate_scene(self.session,'AUTOMATION_ENGINE',redo);self.refresh_geometry()
        except Exception as exc:QMessageBox.information(self,'Scene history',str(exc))

    def import_mesh(self):
        if self.import_job:return
        try:
            if not self.ensure_geometry():return
            path,_=QFileDialog.getOpenFileName(self,'Synthetic mesh only','','Triangle meshes (*.obj *.stl)')
            if not path:return
            units,ok=QInputDialog.getItem(self,'Source units','Explicit source units:',list(('m','mm','cm','ft')),0,False)
            if not ok:return
            datum,ok=QInputDialog.getText(self,'Source coordinate basis','Confirm synthetic source datum and right-handed XYZ axes. Identity transform and zero origin will be used:')
            if not ok or not datum.strip():return
            # File bytes must be stable until result commit; bounded read and hash.
            self.import_path=Path(path)
            if self.import_path.stat().st_size>4000000:raise ValueError('Mesh exceeds 4 MB development budget')
            self.import_sha=hashlib.sha256(self.import_path.read_bytes()).hexdigest()
            self.import_job=ImportJob(path,Frame('IMPORT',units,datum))
            import time
            self.import_deadline=time.monotonic()+10
            self.import_timer.start(100);self.status.setText('Import running | cancel available | UNVERIFIED')
        except Exception as exc:QMessageBox.critical(self,'Import blocked',str(exc))

    def cancel_import(self):
        if self.import_job:self.import_job.cancel();self.import_job=None
        if hasattr(self,'import_timer'):self.import_timer.stop()

    def poll_import(self):
        import time
        if not self.import_job:return
        if time.monotonic()>self.import_deadline:
            self.cancel_import();self.status.setText('Import timed out and was terminated');return
        if self.import_job.process.poll() is None:return
        job=self.import_job;self.import_job=None;self.import_timer.stop()
        try:
            result=job.result()
            if result['source_sha256']!=self.import_sha:raise ValueError('Source changed during import')
            proposal=ImportProposal.prepare(self.import_path.read_bytes(),self.import_path.suffix,result)
            dialog=QDialog(self);dialog.resize(650,480);dialog.setWindowTitle('Review synthetic geometry import');layout=QVBoxLayout(dialog)
            layout.addWidget(QLabel('Review source and diagnostics before adding CANDIDATE geometry. This is not engineering acceptance.'))
            info=QPlainTextEdit();info.setReadOnly(True);info.setPlainText(json.dumps({'source_sha256':proposal.source_hash,'original_frame':result['frame'],'mesh_sha256':result['mesh_sha256'],'diagnostics':result['diagnostics']},indent=2));layout.addWidget(info)
            mode=QComboBox();mode.addItems(['APPEND','REPLACE']);layout.addWidget(mode)
            actor=QLineEdit();actor.setPlaceholderText('Named import reviewer required');layout.addWidget(actor)
            buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
            if dialog.exec()!=QDialog.Accepted:self.status.setText('Import proposal not applied');return
            proposal.apply(self.session,actor.text(),mode.currentText());self.refresh()
            self.status.setText('Reviewed candidate mesh imported | UNVERIFIED | engineering diagnostics incomplete')
        except Exception as exc:QMessageBox.critical(self,'Import refused',str(exc))

    def inspect_evidence(self):
        if not self.ensure_geometry():return
        id=self.selected_id();kind=self.active_kind()
        record=workspace.row(self.session,'detectors' if kind=='DETECTOR' else 'engineering_record',id) if id else None
        data={'record':record,'evidence':None if not record else workspace.row(self.session,'evidence',record['evidence_id']),'findings':study_findings(self.session)}
        if record and kind=='DETECTOR' and self.session.con.execute('PRAGMA user_version').fetchone()[0]==3:
            data['explicit_mount']=workspace.row(self.session,'detector_mount',id);data['preparation_dataset_link']=workspace.row(self.session,'detector_performance_link',id)
        dialog=QDialog(self);dialog.resize(780,550);dialog.setWindowTitle('Evidence and preparation findings');layout=QVBoxLayout(dialog)
        text=QPlainTextEdit();text.setReadOnly(True);text.setPlainText(json.dumps(data,indent=2));layout.addWidget(text)
        buttons=QDialogButtonBox(QDialogButtonBox.Close);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons);dialog.exec()

    def run_exercise(self):
        if not self.ensure_geometry():return
        path,_=QFileDialog.getOpenFileName(self,'Synthetic exercise JSON only','','JSON (*.json)')
        if not path:return
        try:
            from fgmapping.services.calculations import run_synthetic
            source=Path(path)
            if source.stat().st_size>4000000:raise ValueError('Exercise exceeds 4 MB development limit')
            payload=json.loads(source.read_text())
            if set(payload)!={'data_class','method','inputs'} or payload['data_class']!='SYNTHETIC':raise ValueError('Closed synthetic exercise contract required')
            id,ok=QInputDialog.getText(self,'Synthetic run','Unique calculation run ID:')
            if not ok:return
            result=run_synthetic(self.session,id,payload['method'],payload['inputs'],'AUTOMATION_ENGINE')
            self.status.setText('SYNTHETIC ONLY / UNVERIFIED: '+json.dumps(result))
        except Exception as exc:QMessageBox.critical(self,'Exercise refused',str(exc))

    def export_reports(self):
        if not self.session or self.report_job:return
        parent=QFileDialog.getExistingDirectory(self,'Choose report parent folder')
        if not parent:return
        name,ok=QInputDialog.getText(self,'New output folder','New report folder name:')
        if not ok or not name.strip():return
        if Path(name).name!=name or name in ('.','..'):
            QMessageBox.critical(self,'Output refused','Use a single new folder name.');return
        try:self.start_report(Path(parent)/name)
        except Exception as exc:QMessageBox.critical(self,'Report refused',str(exc))

    def start_report(self,destination):
        import time,base64
        from PySide6.QtCore import QBuffer,QIODevice
        snapshot=normalized_snapshot(self.session)
        if self.last_comparison and self.last_comparison['current_snapshot_hash']==content_hash(snapshot):
            from fgmapping.services.comparison import attach_comparison
            snapshot=attach_comparison(snapshot,self.last_comparison)
        buffer=QBuffer();buffer.open(QIODevice.WriteOnly);self.viewer.grab().save(buffer,'PNG');raw=bytes(buffer.data())
        snapshot['figures']=[{'id':'FACILITY_VIEW','description':'Synthetic facility view with mounting/zone annotations'+('; geometric diagnostic samples only' if self.viewer.inspection_result else '')+'; no detector coverage','sha256':hashlib.sha256(raw).hexdigest(),'png_base64':base64.b64encode(raw).decode(),'camera':self.viewer.state()}]
        self.report_job=ReportJob(snapshot,destination);self.report_deadline=time.monotonic()+60;self.report_timer.start(100)
        self.report_progress=QProgressDialog('Exporting synthetic register reports','Cancel',0,0,self);self.report_progress.setWindowTitle('Report export');self.report_progress.canceled.connect(self.cancel_report);self.report_progress.show()
        self.status.setText('Report export running in cancellable worker | UNVERIFIED')

    def cancel_report(self):
        if self.report_job:self.report_job.cancel();self.report_job=None
        self.report_timer.stop()
        if hasattr(self,'report_progress'):self.report_progress.close()

    def poll_report(self):
        import time
        if not self.report_job:return
        if time.monotonic()>self.report_deadline:
            self.cancel_report();self.status.setText('Report timed out; incomplete output retained');return
        if self.report_job.process.poll() is None:return
        job=self.report_job;self.report_job=None;self.report_timer.stop();self.report_progress.close()
        try:
            result=job.result();self.status.setText(str(result['record_rows'])+' synthetic records exported | parser QA passed | visual/engineering review separate')
        except Exception as exc:QMessageBox.critical(self,'Report failed',str(exc))

    def closeEvent(self,event):
        self.cancel_preparation()
        self.cancel_import()
        self.cancel_report()
        self.cancel_geometry()
        self.cancel_restore()
        self.settings.setValue('viewport',json.dumps(self.viewer.state()))
        self.close_case()
        if self.session:event.ignore()
        else:event.accept()

def main():
    app=QApplication([])
    window=MainWindow();window.show()
    return app.exec()
