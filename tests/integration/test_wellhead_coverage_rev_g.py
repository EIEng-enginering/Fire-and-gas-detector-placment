"""Rev G M3/M6 + wellhead application: full coverage workflow on the SYNTHETIC wellhead example
(EXAMPLE library values), coverage report outputs, heatmap known-answer pixels, offscreen UI overlay.
Engineer-reviewed results - not independently certified."""
import hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from build_wellhead_coverage_example import build
from fgmapping.services.case import CaseSession
from fgmapping.services import coverage as cov
from fgmapping.services import workspace as w
from fgmapping.services.basis import readiness
from fgmapping.services.coverage_report import export_coverage_report,LABEL
from fgmapping.services.heatmap import render_slice,VOTE_RGB
from fgmapping.services.findings import study_findings
from fgmapping.services.reporting import normalized_snapshot
SHIPPED=ROOT/'examples/wellhead_coverage/SYNTHETIC_WELLHEAD_COVERAGE.fgcase'

class WellheadCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name)
        cls.case,cls.summary,cls.report=build(cls.root/'out',grid=2.0,refine=1,progress=lambda *a:None)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def session(self):
        s=CaseSession(self.case,self.root/'rt');self.addCleanup(lambda:s.close(discard_unsaved=True));return s
    def test_all_detectors_assigned_all_zones_ready_and_run(self):
        s=self.session();self.assertEqual(len(w.detector_rows(s)),23)
        self.assertTrue(all(w.row(s,'detector_library_assignment',d['id']) for d in w.detector_rows(s)))
        r=readiness(s);self.assertEqual(r['engineering_calculation_status'],'READY');self.assertEqual(r['qualification'],'ENGINEER-REVIEWED - NOT INDEPENDENTLY CERTIFIED')
        runs=cov.latest_runs(s);self.assertEqual(sorted(runs),['FZ-MANIFOLD','FZ-WELLBAY','FZ-WIRELINE','GZ-MANIFOLD','GZ-MODULE','GZ-WELLBAY'])
        for z,run in runs.items():
            res=json.loads(run['result_json']);self.assertEqual(run['label'],LABEL);self.assertEqual(cov.run_currency(s,run),'CURRENT')
            self.assertTrue(any(x.startswith('EXAMPLE_LIBRARY_VALUES') for x in res['review']))
            fr=res['fractions'];self.assertAlmostEqual(fr['0ooN']+fr['1ooN'],1.0,9);self.assertGreaterEqual(fr['1ooN'],fr['2ooN']);self.assertGreaterEqual(fr['2ooN'],fr['3ooN'])
            env=json.loads(run['input_json']);self.assertEqual(env['method'],'FLAME_GEOGRAPHIC' if z.startswith('FZ') else 'GAS_GEOGRAPHIC')
        op=[d for d in json.loads(runs['GZ-MODULE']['input_json'])['detectors'] if d['detector_type']=='OPEN_PATH']
        self.assertEqual({d['id']:d['receiver'] for d in op},{'GD-OP-01':[29.0,2.0,1.5],'GD-OP-02':[28.5,18.5,1.5],'GD-OP-03':[22.8,9.6,2.0]})
    def test_edit_marks_runs_stale_and_findings_report_it(self):
        s=self.session();d=w.row(s,'detector_details','FD-101')
        w.detector_command(s,{**{k:d[k] for k in ('azimuth','elevation','roll')},'id':'FD-101','detector_type':'FLAME','x':1.2,'y':0.9,'z':7.5,'evidence_id':'SYN-WHM-COV-01'},None,'T')
        runs=cov.latest_runs(s);self.assertEqual(cov.run_currency(s,runs['FZ-WELLBAY']),'STALE');self.assertEqual(cov.run_currency(s,runs['GZ-WELLBAY']),'CURRENT')
        self.assertTrue(any(f['id'].startswith('COVERAGE-STALE') for f in study_findings(s)))
    def test_report_outputs_hashes_labels_and_no_overwrite(self):
        folder=Path(self.report['folder']);names={p.name for p in folder.iterdir()}
        for ext in ('json','xlsx','docx','pdf'):self.assertIn('WELLHEAD_COVERAGE_REPORT.'+ext,names)
        self.assertGreaterEqual(len([n for n in names if n.startswith('FIG_') and n.endswith('.png')]),6)
        man=json.loads((folder/'MANIFEST.json').read_text());self.assertEqual(man['label'],LABEL)
        for n,v in man['files'].items():self.assertEqual(hashlib.sha256((folder/n).read_bytes()).hexdigest(),v['sha256'])
        snap=json.loads((folder/'WELLHEAD_COVERAGE_REPORT.json').read_text())
        self.assertEqual(snap['label'],LABEL);self.assertEqual(len(snap['example_library_entries']),3);self.assertEqual(len(snap['detectors']),23)
        from docx import Document
        text='\n'.join(p.text for p in Document(folder/'WELLHEAD_COVERAGE_REPORT.docx').paragraphs)
        self.assertIn(LABEL,text);self.assertIn('EXAMPLE library values used',text);self.assertNotIn('certified by',text.lower())
        from openpyxl import load_workbook
        wb=load_workbook(folder/'WELLHEAD_COVERAGE_REPORT.xlsx');self.assertEqual(wb['Summary']['A1'].value,LABEL);self.assertIn('Hashes',wb.sheetnames)
        self.assertTrue((folder/'WELLHEAD_COVERAGE_REPORT.pdf').read_bytes().startswith(b'%PDF'))
        s=self.session()
        with self.assertRaises(ValueError):export_coverage_report(s,folder.parent,folder.name)
        again=export_coverage_report(s,self.root/'again','R2');self.assertEqual(again['content_sha256'],self.report['content_sha256'])
    def test_normalized_snapshot_lists_runs_and_qualified_limitation(self):
        s=self.session();snap=normalized_snapshot(s)
        self.assertEqual(len(snap['datasets']['coverage_runs']),6);self.assertIn('not independently certified',snap['limitations'][0])
    def test_shipped_example_is_current_with_this_code(self):
        self.assertTrue(SHIPPED.exists());tmp=self.root/'shipped.fgcase';shutil.copyfile(SHIPPED,tmp)
        s=CaseSession(tmp,self.root/'rt2');self.addCleanup(lambda:s.close(discard_unsaved=True))
        runs=cov.latest_runs(s);self.assertEqual(len(runs),6)
        self.assertEqual({z:cov.run_currency(s,r) for z,r in runs.items()},{z:'CURRENT' for z in runs})
        summ=json.loads((SHIPPED.parent/'WELLHEAD_COVERAGE_SUMMARY.json').read_text())['zones']
        for z,r in runs.items():self.assertEqual(json.loads(r['result_json'])['fractions']['2ooN'],summ[z]['2ooN'])

class HeatmapKnownAnswer(unittest.TestCase):
    def test_cell_pixels_coloured_by_votes(self):
        from PIL import Image;import io
        rows=[[0.5,0.5,1.0,1.0,[]],[1.5,0.5,1.0,1.0,[0]],[2.5,0.5,1.0,1.0,[0,1]],[3.5,0.5,1.0,1.0,[0,1,2]],[0.5,0.5,2.0,1.0,[0]]]
        res={'zone_id':'Z','method_version':'FG-FLAME-GEO/1.0','grid_spacing_m':1.0,'mode':'VOLUME','fractions':{'1ooN':.75,'2ooN':.5,'3ooN':.25},'zone_bounds':([0,0,0],[4,1,3])}
        img=Image.open(io.BytesIO(render_slice(res,{'rows':rows},1.0,px_per_m=20))).convert('RGB')
        for i,rgb in enumerate(VOTE_RGB):self.assertEqual(img.getpixel((60+20*i+10,70+10)),rgb)

class CoverageUiOffscreen(unittest.TestCase):
    def test_heatmap_fov_and_results_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            case,_,_=build(Path(tmp)/'o',grid=2.0,refine=1,progress=lambda *a:None)
            code='''import sys,json
from pathlib import Path
from PySide6.QtWidgets import QApplication,QTableWidget
from PySide6.QtCore import QTimer
from fgmapping.ui.main import MainWindow
from fgmapping.services.case import CaseSession
from fgmapping.services import coverage as cov
app=QApplication([]);w=MainWindow();w.settings.clear();w.session=CaseSession(Path(sys.argv[1]),Path(sys.argv[2]));w.refresh();w.show();app.processEvents()
runs=cov.latest_runs(w.session);w.show_heatmap(runs['FZ-WELLBAY'],1.0);app.processEvents()
c=w.viewer.coverage;assert c and c['slice_z']==1.0 and 'EXAMPLE' in c['legend'] and 'not independently certified' in c['legend'],c
assert not w.viewer.grab().isNull()
w.toggle_fov();assert len(w.viewer.fov)==8;w.viewer.grab();w.toggle_fov();assert w.viewer.fov==[]
w.clear_overlay();assert w.viewer.coverage is None
seen={}
def grab():
    d=app.activeModalWidget()
    if d is None:QTimer.singleShot(50,grab);return
    t=d.findChild(QTableWidget,'results_table');seen['rows']=t.rowCount();seen['state']=t.item(0,3).text();d.reject()
QTimer.singleShot(50,grab);w.results_dialog();assert seen=={'rows':6,'state':'CURRENT'},seen
w.session.close(discard_unsaved=True);print('UI_OK')
'''
            env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PYTHONPATH=str(ROOT/'src')+os.pathsep+os.environ.get('PYTHONPATH',''))
            r=subprocess.run([sys.executable,'-B','-c',code,str(case),str(Path(tmp)/'rt')],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
            self.assertIn('UI_OK',r.stdout,r.stdout)
