"""Rev G coverage UI: detector library, explicit assignment, zone setup, runs,
results table, heatmap overlay and FOV display. All state changes use services.
Engineer-reviewed results - not independently certified."""
import json,threading,time
from pathlib import Path
from PySide6.QtCore import Qt,QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QComboBox,QDialogButtonBox,QMessageBox,QPlainTextEdit,QFileDialog,
    QTableWidget,QTableWidgetItem,QPushButton,QInputDialog,QProgressDialog,QLineEdit,QCheckBox)
from fgmapping.services import coverage as cov
from fgmapping.services import workspace as w
from fgmapping.engine.coverage import detector_frame,LABEL
from fgmapping.domain.detector_library import contour_range

def setup_template(zone):
    flame=zone['kind']=='FIRE_ZONE'
    return {'contract':'fg-coverage-setup/1','zone_id':zone['id'],'method':'FLAME_GEOGRAPHIC' if flame else 'GAS_GEOGRAPHIC','grid_spacing_m':1.0,'mode':'VOLUME','slice_elevations_m':[],
            'voting_required':1 if not flame else 2,'performance_targets':{'1ooN':'NOT SUPPLIED','2ooN':'NOT SUPPLIED'},'convergence':{'refinement':2,'tolerance':'0.02'},
            'criterion_reference':'NOT SUPPLIED','standoff_m':0.05,'tolerance_m':1e-6,
            'flame':{'fuel':'NOT SUPPLIED','heat_release_kw':1.0,'fire_size_scaling':'NONE','target_geometry':{'type':'POINT'},'min_visible_fraction':1.0} if flame else None,
            'gas':None if flame else {'gas':'NOT SUPPLIED','cloud':{'shape':'SPHERE','diameter_m':5.0},'cloud_concentration_pct_lel':100.0,'detector_types':['POINT_GAS','OPEN_PATH']},'notes':''}

def fmt(v):return '-' if v is None else '%.1f %%' % (100*v)

class CoverageDialogs:
    def coverage_menu(self,bar):
        m=bar.addMenu('Coverage')
        for title,cb in [('Enable coverage schema (schema 4)',self.coverage_enable),('Import detector library CSV / Excel',self.library_import),('Detector library',self.library_dialog),
                         ('Assign library entry to selected detector',self.assign_dialog),('Zone coverage setup',self.setup_dialog),('Coverage readiness',self.coverage_readiness_dialog),
                         ('Run coverage (all READY zones)',self.run_coverage),('Coverage results / heatmap',self.results_dialog),('Show / hide detector FOV',self.toggle_fov),('Clear coverage overlay',self.clear_overlay),
                         ('Export coverage report',self.export_coverage_report)]:
            m.addAction(title,cb)
        self.coverage_job=None;self.coverage_timer=QTimer(self);self.coverage_timer.timeout.connect(self.poll_coverage);self.fov_on=False
        return m
    def need_coverage(self):
        if not self.session:raise ValueError('Open a case first')
        if cov.version(self.session)!=4:raise ValueError('Enable the coverage schema first (Coverage > Enable coverage schema)')
    def coverage_error(self,title,exc):QMessageBox.warning(self,title,str(exc))
    def coverage_enable(self):
        try:
            if not self.session:raise ValueError('Open a case first')
            if cov.version(self.session)==4:QMessageBox.information(self,'Coverage schema','Coverage schema 4 already enabled');return
            if cov.version(self.session)<3 and not self.ensure_study():return
            if QMessageBox.question(self,'Coverage schema 4','Enable detector library, coverage setups and stored coverage runs in this case? A restorable backup is retained. Older program versions cannot open schema 4.')!=QMessageBox.Yes:return
            cov.enable_coverage(self.session,'AUTOMATION_ENGINE');self.refresh()
        except Exception as exc:self.coverage_error('Coverage schema',exc)
    def library_import(self):
        try:
            self.need_coverage()
            path,_=QFileDialog.getOpenFileName(self,'Detector library','','Library (*.csv *.xlsx)')
            if not path:return
            r=cov.import_library(self.session,Path(path).read_bytes(),'XLSX' if path.lower().endswith('.xlsx') else 'CSV','AUTOMATION_ENGINE')
            QMessageBox.information(self,'Detector library','Added: %s\nIdentical (skipped): %s\n\nResults depend on these data. EXAMPLE VALUES must be replaced by verified manufacturer data before project use.' % (', '.join(r['added']) or '-',', '.join(r['skipped_identical']) or '-'))
        except Exception as exc:self.coverage_error('Detector library import',exc)
    def library_dialog(self):
        try:
            self.need_coverage();lib=cov.library(self.session)
            d=QDialog(self);d.setWindowTitle('Detector library (engineer-supplied performance data)');d.resize(1100,520);lay=QVBoxLayout(d)
            lay.addWidget(self.wrapped('Coverage uses ONLY the entry explicitly assigned to each detector (no generic cone). Rows in red carry EXAMPLE VALUES and must be replaced by verified manufacturer data before project use.'))
            cols=['ID','Type','Technology','Fuel/gas','Rated fire (kW)','FOV H x V (deg)','Contour (deg:m)','Alarm threshold','Data status','Source']
            t=QTableWidget(len(lib),len(cols));t.setHorizontalHeaderLabels(cols);t.setObjectName('library_table')
            for i,(id,e) in enumerate(lib.items()):
                vals=[id,e['detector_type'],e['technology'],e['fuel_or_gas'],'' if not e['target_fire'] else '%g' % e['target_fire']['heat_release_kw'],
                      '' if not e['fov'] else '%g x %g' % (e['fov']['horizontal_deg'],e['fov']['vertical_deg']),';'.join('%g:%g' % tuple(r) for r in (e['contour'] or [])),
                      '' if not e['alarm_threshold'] else '%g %s' % (e['alarm_threshold']['value'],e['alarm_threshold']['units']),e['source']['data_status'],e['source']['title']+' rev '+e['source']['revision']+' p.'+e['source']['page']]
                for j,v in enumerate(vals):
                    it=QTableWidgetItem(v)
                    if e['source']['data_status'].startswith('EXAMPLE'):it.setForeground(QColor('#b03a2e'))
                    t.setItem(i,j,it)
            t.resizeColumnsToContents();lay.addWidget(t)
            b=QDialogButtonBox(QDialogButtonBox.Close);b.rejected.connect(d.reject);lay.addWidget(b);d.exec()
        except Exception as exc:self.coverage_error('Detector library',exc)
    def assign_dialog(self):
        try:
            self.need_coverage()
            det=self.selected_id() if self.active_kind()=='DETECTOR' else None
            row=w.row(self.session,'detectors',det) if det else None
            if row is None:raise ValueError('Select a detector register row first')
            lib={k:e for k,e in cov.library(self.session).items() if e['detector_type']==row['detector_type']}
            if not lib:raise ValueError('No library entry of type '+row['detector_type']+'; import one first')
            old=w.row(self.session,'detector_library_assignment',det)
            d=QDialog(self);d.setWindowTitle('Assign library entry to '+det);form=QFormLayout(d)
            form.addRow(self.wrapped('Explicit engineer selection (F03). The entry\'s range/FOV/threshold data drive the coverage result for this detector.'))
            entry=QComboBox();entry.setObjectName('assign_entry');entry.addItems(sorted(lib));form.addRow('Library entry',entry)
            if old:entry.setCurrentText(old['library_id'])
            ev=self.evidence_combo(old['evidence_id'] if old else None);form.addRow('Evidence',ev)
            rx=None
            if row['detector_type']=='OPEN_PATH':
                rx=QComboBox();rx.setObjectName('assign_receiver')
                recs=[r[0] for r in self.session.con.execute("SELECT id FROM engineering_record WHERE kind='EQUIPMENT' AND payload_json LIKE '%\"position\"%' ORDER BY id")]
                rx.addItems(recs);form.addRow('Receiver position record',rx)
                if old and json.loads(old['receiver_json']):rx.setCurrentText(json.loads(old['receiver_json']).get('record_id',''))
            self.buttons(d,form)
            if d.exec()!=QDialog.Accepted:return
            cov.assign_library(self.session,det,entry.currentText(),ev.currentText(),'AUTOMATION_ENGINE',{'record_id':rx.currentText()} if rx is not None else None);self.refresh()
        except Exception as exc:self.coverage_error('Assign library entry',exc)
    def setup_dialog(self):
        try:
            self.need_coverage();zones=cov.zones(self.session)
            if not zones:raise ValueError('Add a fire or gas zone record first')
            names=[z['id'] for z in zones];zid,ok=QInputDialog.getItem(self,'Zone coverage setup','Zone',names,0,False)
            if not ok:return
            zone=next(z for z in zones if z['id']==zid);current=cov.zone_setup(self.session,zid) or setup_template(zone)
            d=QDialog(self);d.setWindowTitle('Coverage setup '+zid+' (fg-coverage-setup/1)');d.resize(760,640);lay=QVBoxLayout(d)
            lay.addWidget(self.wrapped('All values are engineer-supplied: grid, target fire or design cloud, voting and the user performance targets used for comparison. No pass percentage is built into the program.'))
            text=QPlainTextEdit(json.dumps(current,indent=2));text.setObjectName('setup_json');lay.addWidget(text)
            form=QFormLayout();ev=self.evidence_combo();form.addRow('Evidence',ev);lay.addLayout(form);self.buttons(d,lay)
            while d.exec()==QDialog.Accepted:
                try:cov.set_zone_setup(self.session,json.loads(text.toPlainText()),ev.currentText(),'AUTOMATION_ENGINE');self.refresh();return
                except Exception as exc:QMessageBox.warning(self,'Coverage setup refused',str(exc))
        except Exception as exc:self.coverage_error('Coverage setup',exc)
    def coverage_readiness_dialog(self):
        try:self.need_coverage();self.show_text('Coverage readiness (per zone)',cov.coverage_readiness(self.session))
        except Exception as exc:self.coverage_error('Coverage readiness',exc)
    def run_coverage(self):
        try:
            self.need_coverage()
            if self.coverage_job:return
            ready=[z for z,st in cov.coverage_readiness(self.session).items() if st['status']=='READY']
            if not ready:raise ValueError('No zone is READY. See Coverage > Coverage readiness.')
            prefix,ok=QInputDialog.getText(self,'Run coverage','Run ID prefix (stored with every result):',text='RUN-'+time.strftime('%Y%m%d-%H%M%S'))
            if not ok or not prefix.strip():return
            jobs=[(z,prefix+'-'+z)+cov.prepare_run(self.session,z,prefix+'-'+z) for z in ready]
            state={'done':[],'error':None,'cancel':False,'progress':''}
            def work():
                try:
                    for z,rid,env,review,scene in jobs:
                        state['progress']=z
                        res,samples=cov.compute(env,scene,cancel=lambda:state['cancel'],progress=lambda n,t,z=z:state.__setitem__('progress','%s %d/%d' % (z,n,t)))
                        state['done'].append((rid,env,review,res,samples))
                except Exception as exc:state['error']=exc
                state['finished']=True
            self.coverage_progress=QProgressDialog('Computing coverage...','Cancel',0,0,self);self.coverage_progress.setWindowModality(Qt.WindowModal)
            self.coverage_progress.canceled.connect(lambda:state.__setitem__('cancel',True));self.coverage_progress.show()
            self.coverage_job=state;threading.Thread(target=work,daemon=True).start();self.coverage_timer.start(150)
        except Exception as exc:self.coverage_error('Run coverage',exc)
    def poll_coverage(self):
        state=self.coverage_job
        if not state:return
        self.coverage_progress.setLabelText('Computing coverage: '+state['progress'])
        if not state.get('finished'):return
        self.coverage_timer.stop();self.coverage_progress.close();self.coverage_job=None
        if state['error']:QMessageBox.warning(self,'Coverage','Calculation stopped: '+str(state['error']));return
        stored=[]
        try:
            for rid,env,review,res,samples in state['done']:cov.store_run(self.session,rid,env,review,res,samples,'AUTOMATION_ENGINE');stored.append(rid)
        except Exception as exc:QMessageBox.warning(self,'Coverage','Not stored: '+str(exc))
        self.refresh();self.results_dialog()
    def results_rows(self):
        out=[]
        for z,r in cov.latest_runs(self.session).items():
            res=json.loads(r['result_json']);out.append((z,r,res,cov.run_currency(self.session,r)))
        return out
    def results_dialog(self):
        try:
            self.need_coverage();rows=self.results_rows()
            if not rows:raise ValueError('No coverage runs stored yet')
            d=QDialog(self);d.setWindowTitle('Coverage results - '+LABEL);d.resize(1180,420);lay=QVBoxLayout(d)
            example=any(x.startswith('EXAMPLE_LIBRARY_VALUES') for _,_,res,_ in rows for x in res.get('review',[]))
            lay.addWidget(self.wrapped(LABEL+'. Results depend on the detector library data entered.'+(' WARNING: EXAMPLE library values used - not for project design.' if example else '')))
            cols=['Zone','Method','Run','State','Eligible','0ooN','1ooN','2ooN','3ooN','Voting','Targets','Convergence','Findings']
            t=QTableWidget(len(rows),len(cols));t.setHorizontalHeaderLabels(cols);t.setObjectName('results_table')
            for i,(z,r,res,state) in enumerate(rows):
                tg='; '.join('%s %s: %s' % (k,v['target'],v['status']) for k,v in res['performance_targets'].items() if v['target']!='NOT SUPPLIED') or 'no user targets'
                vals=[z,res['method_version'],r['id'],state,'%.1f %s' % (res['eligible_measure'],res['measure_unit']),fmt(res['fractions']['0ooN']),fmt(res['fractions']['1ooN']),fmt(res['fractions']['2ooN']),fmt(res['fractions']['3ooN']),
                      '%dooN = %s' % (res['voting_required'],fmt(res['required_voting_fraction'])),tg,res['convergence']['status'],str(len(res['findings']))]
                for j,v in enumerate(vals):
                    it=QTableWidgetItem(v)
                    if state=='STALE':it.setForeground(QColor('#8a6d3b'))
                    t.setItem(i,j,it)
            t.resizeColumnsToContents();lay.addWidget(t)
            bl=QHBoxLayout();lay.addLayout(bl)
            show=QPushButton('Show heatmap for selected zone');show.clicked.connect(lambda:(self.show_heatmap(rows[max(t.currentRow(),0)][1]),d.accept()));bl.addWidget(show)
            det=QPushButton('Details / findings');det.clicked.connect(lambda:self.show_text('Coverage result '+rows[max(t.currentRow(),0)][0],rows[max(t.currentRow(),0)][2]));bl.addWidget(det)
            b=QDialogButtonBox(QDialogButtonBox.Close);b.rejected.connect(d.reject);lay.addWidget(b);t.selectRow(0);d.exec()
        except Exception as exc:self.coverage_error('Coverage results',exc)
    def show_heatmap(self,run,slice_z=None):
        res=json.loads(run['result_json']);samples=json.loads(run['samples_json'])
        zs=sorted({round(r[2],6) for r in samples['rows']})
        if not zs:return
        if slice_z is None:
            if len(zs)>1:
                item,ok=QInputDialog.getItem(self,'Heatmap slice','Plan slice elevation (m)',['%.3f' % z for z in zs],0,False)
                if not ok:return
                slice_z=float(item)
            else:slice_z=zs[0]
        slice_z=min(zs,key=lambda z:abs(z-slice_z))
        example=any(x.startswith('EXAMPLE_LIBRARY_VALUES') for x in res.get('review',[]))
        state=cov.run_currency(self.session,run)
        self.viewer.coverage={'rows':samples['rows'],'spacing':res['grid_spacing_m'],'slice_z':slice_z,
            'title':'%s %s run %s (%s) | 1ooN %s | 2ooN %s' % (res['zone_id'],res['method_version'],run['id'],state,fmt(res['fractions']['1ooN']),fmt(res['fractions']['2ooN'])),
            'legend':LABEL+(' | EXAMPLE LIBRARY VALUES' if example else '')}
        self.viewer.update()
    def clear_overlay(self):self.viewer.coverage=None;self.viewer.update()
    def fov_items(self):
        out=[];sel=self.selected_id() if self.active_kind()=='DETECTOR' else None
        lib=cov.library(self.session)
        for d in w.detector_rows(self.session):
            a=w.row(self.session,'detector_library_assignment',d['id']);det=w.row(self.session,'detector_details',d['id'])
            if not a or d['detector_type']!='FLAME' or not det:continue
            e=lib[a['library_id']]
            out.append({'id':d['id'],'position':(d['x'],d['y'],d['z']),'frame':detector_frame(det['azimuth'],det['elevation'],det['roll'] or 0.),'fov_h':e['fov']['horizontal_deg'],'fov_v':e['fov']['vertical_deg'],
                        'range':lambda off,e=e:contour_range(e,min(off,e['contour'][-1][0])),'selected':d['id']==sel})
        return out
    def toggle_fov(self):
        try:
            self.need_coverage();self.fov_on=not self.fov_on;self.viewer.fov=self.fov_items() if self.fov_on else [];self.viewer.update()
        except Exception as exc:self.coverage_error('Detector FOV',exc)
    def export_coverage_report(self):
        try:
            self.need_coverage()
            folder=QFileDialog.getExistingDirectory(self,'Coverage report folder (new files only)')
            if not folder:return
            from fgmapping.services.coverage_report import export_coverage_report
            name,ok=QInputDialog.getText(self,'Coverage report','Report base name:',text='COVERAGE_REPORT')
            if not ok or not name.strip():return
            out=export_coverage_report(self.session,Path(folder),name.strip())
            QMessageBox.information(self,'Coverage report','Written:\n'+'\n'.join(out['files']))
        except Exception as exc:self.coverage_error('Coverage report',exc)
