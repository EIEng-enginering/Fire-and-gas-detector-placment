"""Rev H regression tests for review findings F08-F25 (integrity, provenance, outputs, UI, imports).
Expected results are fixed by the review's requirements, not by the implementation."""
import io,json,math,os,shutil,subprocess,sys,tempfile,threading,time,unittest,zipfile,random
from decimal import Decimal,localcontext
from pathlib import Path
from unittest import mock
from fgmapping.services import coverage as cov
from fgmapping.services import lifecycle
from fgmapping.services import workspace as w
from fgmapping.services import scenario_coverage as scs
from fgmapping.services.geometry import set_scene,get_scene
from fgmapping.services.fingerprint import fingerprint,dependency_closure,ENTRY
from fgmapping.services.safe_paths import OutputPathError
from fgmapping.domain.scene import Scene,Frame,Component,box_mesh
from fgmapping.domain.detector_library import write_csv,parse_library,CSV_HEADERS
from fgmapping.engine.detection import engineering_flame_coverage,engineering_gas_coverage,EngineeringUnavailable
from fgmapping.engine.optimisation import enumerate_layouts,SyntheticMount,pareto_frontier
from fgmapping.errors import CaseError
from tests.unit.test_coverage_engine import flame_entry,gas_entry,flame_setup,gas_setup,det,scene
import tests.integration.test_coverage_rev_g as base
EV=base.EV
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'src/fgmapping'

class Fixture(unittest.TestCase):
    setUp=base.CoverageServices.setUp;enable=base.CoverageServices.enable;fsetup=base.CoverageServices.fsetup;assign_all=base.CoverageServices.assign_all
    def ready(self,**k):
        self.enable();self.assign_all();cov.set_zone_setup(self.s,self.fsetup(**k),EV,'T')
    def run_fz(self,rid='R1',sensitivity=False):return cov.run_zone(self.s,'FZ',rid,'T',sensitivity=sensitivity)

class F08Fingerprints(Fixture):
    def copy_src(self,where):
        dst=Path(where)/'src_copy/fgmapping';shutil.copytree(SRC,dst,ignore=shutil.ignore_patterns('__pycache__'));return dst
    def test_dependency_closure_contains_shared_and_study_modules(self):
        z=set(dependency_closure(ENTRY['ZONE_COVERAGE']))
        for f in ('engine/coverage.py','engine/solid_geometry.py','engine/mesh_visibility.py','engine/spatial.py','engine/geometry.py','domain/mounting.py','domain/compatibility.py','domain/coverage_setup.py','domain/detector_library.py','services/coverage.py','services/fingerprint.py'):self.assertIn(f,z)
        for m in ('SCENARIO_COVERAGE','LAYOUT_OPTIONS'):
            d=set(dependency_closure(ENTRY[m]));self.assertTrue(z<=d)
            for f in ('engine/scenario_coverage.py','services/scenario_coverage.py','engine/scenarios.py','engine/optimisation.py'):self.assertIn(f,d)
    def test_dependency_mutations_mark_stale(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            ca=self.copy_src(a);cb=self.copy_src(b)
            for m in ENTRY:self.assertEqual(fingerprint(m,ca)[1],fingerprint(m,cb)[1])  # no machine paths
            p=cb/'engine/coverage.py';p.write_bytes(p.read_bytes().replace(b'\n',b'\r\n'))
            self.assertEqual(fingerprint('ZONE_COVERAGE',ca)[1],fingerprint('ZONE_COVERAGE',cb)[1])  # LF-normalised
            for rel,affected in (('engine/scenario_coverage.py',('SCENARIO_COVERAGE','LAYOUT_OPTIONS')),('engine/scenarios.py',('SCENARIO_COVERAGE','LAYOUT_OPTIONS')),('engine/optimisation.py',('SCENARIO_COVERAGE','LAYOUT_OPTIONS')),
                                 ('engine/solid_geometry.py',tuple(ENTRY)),('domain/mounting.py',tuple(ENTRY)),('domain/compatibility.py',tuple(ENTRY)),('engine/spatial.py',tuple(ENTRY)),('ui/viewer.py',())):
                before={m:fingerprint(m,cb)[1] for m in ENTRY}
                f=cb/rel;old=f.read_bytes();f.write_bytes(old+b'\n# mutation\n')
                after={m:fingerprint(m,cb)[1] for m in ENTRY}
                for m in ENTRY:self.assertEqual(before[m]!=after[m],m in affected,(rel,m))
                f.write_bytes(old)
            # stored run turns STALE when an isolated copy of one dependency changes
            self.ready();run=cov.latest_runs(self.s) or None;self.run_fz();run=cov.latest_runs(self.s)['FZ'];self.assertEqual(cov.run_currency(self.s,run),'CURRENT')
            real=fingerprint
            with mock.patch('fgmapping.services.coverage.fingerprint',lambda m:real(m,cb)):
                self.assertEqual(cov.run_currency(self.s,run),'CURRENT')
                f=cb/'engine/solid_geometry.py';f.write_bytes(f.read_bytes()+b'\n# changed\n')
                self.assertEqual(cov.run_currency(self.s,run),'STALE')

class F24Sensitivity(Fixture):
    def test_sensitivity_is_calculation_input(self):
        self.ready()
        a,_,_=cov.gather(self.s,'FZ',False);b,_,_=cov.gather(self.s,'FZ',True)
        from fgmapping.domain.scene import content_hash
        self.assertNotEqual(content_hash(a),content_hash(b));self.assertEqual(b['sensitivity'],{'enabled':True,'range_factors':[0.9,1.1]})
        r=self.run_fz('RS',sensitivity=True);self.assertIn('sensitivity_range_factor',r)
        run=cov.latest_runs(self.s)['FZ'];self.assertEqual(cov.run_currency(self.s,run),'CURRENT')
        env,_,scene=cov.prepare_run(self.s,'FZ','RX',False)
        with self.assertRaises(CaseError):cov.compute(env,scene,sensitivity=True)

class F09HistoricalFigures(Fixture):
    def test_historical_figure_uses_run_scene(self):
        self.ready();self.run_fz();run=cov.latest_runs(self.s)['FZ']
        from fgmapping.services import heatmap
        old=get_scene(self.s);moved=Scene(old.frames,tuple(Component(c.id,c.label,c.semantic,c.frame_id,box_mesh((6,0,0),(6.6,10,3)) if c.id=='WALL' else c.mesh,c.evidence_id) for c in old.components),old.source_revision,old.source_sha256)
        set_scene(self.s,moved,'T');self.assertEqual(cov.run_currency(self.s,run),'STALE')
        seen=[]
        real=heatmap.render_slice
        def spy(res,samples,z,sc,*a,**k):seen.append((sc.sha256 if sc else None,k.get('stale')));return real(res,samples,z,sc,*a,**k)
        with mock.patch.object(heatmap,'render_slice',spy):figs=heatmap.run_figures(self.s,run)
        self.assertTrue(seen and all(sha==json.loads(run['input_json'])['scene_sha256'] and stale for sha,stale in seen))
        self.assertNotEqual(seen[0][0],get_scene(self.s).sha256)
        self.assertTrue(all(f['description'].startswith('STALE RUN') and f['stale'] for f in figs))
    def test_distinct_library_versions_not_merged(self):
        self.ready();self.run_fz('R1')
        row=self.s.con.execute("SELECT input_json FROM coverage_run WHERE id='R1'").fetchone()[0];env=json.loads(row)
        env['library']['FL']['contour']=[[0,7.0],[45,7.0]]  # simulate an older stored library version in that historical run
        with self.s.con:self.s.con.execute("UPDATE coverage_run SET input_json=? WHERE id='R1'",(json.dumps(env),))
        w.record_command(self.s,'FZ2','FIRE_ZONE',{'low':[0,-10,0],'high':[10,10,2],'units':'m','description':'fire zone 2'},EV,'T',create=True)
        p=self.fsetup();p['zone_id']='FZ2';cov.set_zone_setup(self.s,p,EV,'T');cov.run_zone(self.s,'FZ2','R2','T')
        from fgmapping.services.coverage_report import coverage_snapshot
        snap=coverage_snapshot(self.s);fl=[e for e in snap['library'] if e['id']=='FL']
        self.assertEqual(len(fl),2);self.assertEqual({tuple(e['used_by_runs']) for e in fl},{('R1',),('R2',)})

class F10F11Export(Fixture):
    def test_export_name_containment(self):
        from fgmapping.services.coverage_report import export_coverage_report
        self.ready();self.run_fz()
        out=self.root/'out';out.mkdir();(out/'sibling.txt').write_text('keep');(self.root/'escaped').mkdir() if False else None
        before=sorted(p.name for p in self.root.iterdir())
        for bad in ('../escaped','..','.','/tmp/abs','C:\\abs','a/b','..\\x','CON','nul.txt','LPT1','a:b','x?y','a*b','','  lead','trail.','tab\tname','x'*121):
            with self.assertRaises(OutputPathError,msg=bad):export_coverage_report(self.s,out,bad)
        self.assertEqual(sorted(p.name for p in out.iterdir()),['sibling.txt']);self.assertEqual((out/'sibling.txt').read_text(),'keep')
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),before)
        r=export_coverage_report(self.s,out,'Report & Co ü 1');self.assertTrue(Path(r['folder']).is_dir());self.assertEqual(Path(r['folder']).parent.resolve(),out.resolve())
        with self.assertRaises(OutputPathError):export_coverage_report(self.s,out,'Report & Co ü 1')
        self.assertFalse([p for p in out.iterdir() if '.staging-' in p.name])
    def test_export_text_is_literal(self):
        from fgmapping.services.coverage_report import export_coverage_report
        self.enable();self.assign_all();p=self.fsetup();p['criterion_reference']='=1+1';cov.set_zone_setup(self.s,p,EV,'T');self.run_fz()
        r=export_coverage_report(self.s,self.root/'o','REP');x=Path(r['folder'])/'REP.xlsx'
        from openpyxl import load_workbook
        wb=load_workbook(x);hits=[c for ws in wb for row in ws.iter_rows() for c in row if c.value=='=1+1']
        self.assertTrue(hits);self.assertTrue(all(c.data_type=='s' for c in hits))
        with zipfile.ZipFile(x) as z:
            for n in z.namelist():
                if n.startswith('xl/worksheets/'):self.assertNotIn(b'<f>',z.read(n))

class F12Lifecycle(Fixture):
    def test_unreviewed_run_not_reviewed_label(self):
        self.ready();res=self.run_fz();run=cov.latest_runs(self.s)['FZ']
        self.assertEqual(res['lifecycle'],'COMPUTED - UNREVIEWED');self.assertIn('UNREVIEWED',run['label']);self.assertNotIn('Engineer-reviewed',run['label'])
        st=lifecycle.run_state(self.s,run);self.assertEqual(st['lifecycle'],'COMPUTED - UNREVIEWED')
        with self.assertRaises(CaseError):lifecycle.record_review(self.s,'R1','','ACCEPTED','','T')
        rec=lifecycle.record_review(self.s,'R1','A. Engineer','ACCEPTED','checked','T')
        self.assertEqual(rec['input_hash'],run['input_hash']);self.assertEqual(rec['result_sha256'],lifecycle.result_hash(run));self.assertTrue(rec['utc'])
        self.assertEqual(lifecycle.run_state(self.s,run)['lifecycle'],'ENGINEER REVIEWED')
        with self.assertRaises(CaseError):lifecycle.record_review(self.s,'R1','A. Engineer','ACCEPTED','','T',independent=True,evidence_id=EV)
        with self.assertRaises(CaseError):lifecycle.record_review(self.s,'R1','B. Verifier','ACCEPTED','','T',independent=True,evidence_id=None)
        lifecycle.record_review(self.s,'R1','B. Verifier','ACCEPTED','','T',independent=True,evidence_id=EV)
        self.assertEqual(lifecycle.run_state(self.s,run)['lifecycle'],'INDEPENDENTLY VERIFIED')
        d=w.row(self.s,'detector_details','F1');w.detector_command(self.s,{**{k:d[k] for k in ('azimuth','elevation','roll')},'id':'F1','detector_type':'FLAME','x':0.5,'y':0.,'z':1.,'evidence_id':EV},None,'T')
        self.assertEqual(lifecycle.run_state(self.s,run)['lifecycle'],'REVIEW INVALIDATED - inputs or result changed')
        with self.assertRaises(CaseError):lifecycle.record_review(self.s,'R1','A. Engineer','ACCEPTED','','T')

class F13CentralGate(unittest.TestCase):
    def test_direct_gate_matches_service_gate(self):
        lib={'E':flame_entry(kw=100.,fuel='heptane')};s=flame_setup(kw=400.);s['flame']['fuel']='methane'
        with self.assertRaises(EngineeringUnavailable) as e:engineering_flame_coverage(zone={'id':'Z','kind':'FIRE_ZONE','low':(0,0,0),'high':(1,1,1)},setup=s,detectors=[det('D',(0,0,0))],library=lib,scene=scene())
        self.assertIn('FUEL_MISMATCH',str(e.exception));self.assertIn('FIRE_SIZE_MISMATCH',str(e.exception))
        g=gas_setup({'shape':'SPHERE','diameter_m':2.},100,['POINT_GAS']);g['gas']['gas']='hydrogen'
        with self.assertRaises(EngineeringUnavailable) as e:engineering_gas_coverage(zone={'id':'Z','kind':'GAS_ZONE','low':(0,0,0),'high':(1,1,1)},setup=g,detectors=[det('G',(0,0,0),lib='G',kind='POINT_GAS')],library={'G':gas_entry('G','POINT_GAS',20.)},scene=scene())
        self.assertIn('GAS_MISMATCH',str(e.exception))
        g=gas_setup({'shape':'SPHERE','diameter_m':2.},100,['POINT_GAS'])
        with self.assertRaises(EngineeringUnavailable) as e:engineering_gas_coverage(zone={'id':'Z','kind':'GAS_ZONE','low':(0,0,0),'high':(1,1,1)},setup=g,detectors=[det('G',(0,0,0),lib='G',kind='POINT_GAS',receiver=(1,0,0))],library={'G':gas_entry('G','POINT_GAS',20.)},scene=scene())
        self.assertIn('RECEIVER_NOT_ALLOWED',str(e.exception))
        for bad in (dict(position=(float('nan'),0,0)),dict(azimuth=float('inf')),dict(elevation=95.)):
            with self.assertRaises(EngineeringUnavailable):engineering_flame_coverage(zone={'id':'Z','kind':'FIRE_ZONE','low':(0,0,0),'high':(1,1,1)},setup=flame_setup(),detectors=[dict(det('D',(0,0,0)),**bad)],library={'E':flame_entry()},scene=scene())

class F18NonFinite(Fixture):
    def test_contract_rejects_nonfinite_pose(self):
        ok={'contract':scs.SCENARIO_CONTRACT,'scenarios':[{'id':'S1','zone_id':'FZ','location':[1.,1.,1.],'frequency_per_year':'1e-3','frequency_source':'user'}]}
        scs.validate_scenarios(ok)
        for loc in ([float('nan'),1.,1.],[float('inf'),1.,1.],[1.,-float('inf'),1.]):
            with self.assertRaises(CaseError):scs.validate_scenarios({**ok,'scenarios':[dict(ok['scenarios'][0],location=loc)]})
        for f in ('NaN','Infinity','-inf'):
            with self.assertRaises(CaseError):scs.validate_scenarios({**ok,'scenarios':[dict(ok['scenarios'][0],frequency_per_year=f)]})
        c={'id':'C1','detector_type':'FLAME','position':[0.,0.,1.],'azimuth':0.,'elevation':0.,'roll':0.,'library_id':'FL','receiver':None,'cost':'1','feasible':True,'maintainable':True}
        base={'contract':scs.OPTIONS_CONTRACT,'zone_id':'FZ','include_existing':True,'max_detectors':1,'required_votes':1,'grid_spacing_m':None,'candidates':[c]}
        scs.validate_options(base)
        for bad in (dict(position=[float('nan'),0.,1.]),dict(azimuth=float('nan')),dict(roll=float('inf')),dict(elevation=float('-inf')),dict(cost='NaN'),dict(roll=200.)):
            with self.assertRaises(CaseError,msg=str(bad)):scs.validate_options({**base,'candidates':[dict(c,**bad)]})

class F16F23F25Options(Fixture):
    def test_pareto_sorted_frontier_matches_pairwise(self):
        rnd=random.Random(7)
        for _ in range(200):
            ans=[{'mount_ids':[str(i)],'fraction':Decimal(rnd.randint(0,6))/6,'cost':Decimal(rnd.randint(0,5))} for i in range(rnd.randint(1,30))]
            ref=[a for a in ans if not any(b['fraction']>=a['fraction'] and b['cost']<=a['cost'] and (b['fraction']>a['fraction'] or b['cost']<a['cost']) for b in ans)]
            self.assertEqual(sorted(a['mount_ids'][0] for a in pareto_frontier(ans)),sorted(a['mount_ids'][0] for a in ref))
    def test_options_independent_bruteforce(self):
        w_={'a':'1','b':'2','c':'3'};m=[SyntheticMount('M1',frozenset({'a'}),'1',True,True),SyntheticMount('M2',frozenset({'b','c'}),'2',True,True),SyntheticMount('M3',frozenset({'a','b','c'}),'4',True,True)]
        r=enumerate_layouts(m,w_,2,1,{'a':0,'b':0,'c':1})
        # hand enumeration (weights a1 b2 c3, base c=1 vote, 1ooN): {}: c -> 3/6 cost 0; M1: a,c -> 4/6 cost 1; M2: b,c -> 5/6 cost 2;
        # M3: all -> 1 cost 4; M1+M2: all -> 1 cost 3; M1+M3 1 cost 5; M2+M3 1 cost 6. Pareto: M1+M2 (1,3), M2 (5/6,2), M1 (2/3,1), {} (1/2,0)
        self.assertEqual([(p['mount_ids'],p['fraction'],p['cost']) for p in r['pareto']],[(['M1','M2'],'1','3'),(['M2'],'0.8333333333333333333333333333333333','2'),(['M1'],'0.6666666666666666666666666666666667','1'),([],'0.5','0')])
        self.assertEqual(r['enumerated'],7)
    def test_decimal_context_independence(self):
        m=[SyntheticMount('M1',frozenset({'a'}),'1',True,True)];out=[]
        for prec in (6,28):
            with localcontext() as ctx:
                ctx.prec=prec;out.append(enumerate_layouts(m,{'a':'1','b':'1','c':'1'},1,1))
        self.assertEqual(out[0],out[1]);self.assertEqual(out[0]['pareto'][0]['fraction'],'0.3333333333333333333333333333333333')
        from fgmapping.engine.scenario_coverage import _plain
        with localcontext() as ctx:
            ctx.prec=6;a=_plain(Decimal(1)/Decimal(3) if False else '0.33333333333333333333')
        self.assertEqual(a,'0.33333333333333333333')
    def test_options_cancel_and_budget_16(self):
        m=[SyntheticMount('M%02d' % i,frozenset({str(j) for j in range(40) if (i*7+j)%5==0}),str(i+1),True,True) for i in range(16)]
        wts={str(j):'1' for j in range(40)};calls=[0];t=time.time()
        def cancel():calls[0]+=1;return calls[0]>20
        with self.assertRaises(RuntimeError):enumerate_layouts(m,wts,16,2,None,cancel)
        self.assertLess(time.time()-t,5.0)
        t=time.time();r=enumerate_layouts(m,wts,16,2);self.assertEqual(r['enumerated'],2**16);self.budget=time.time()-t
        self.assertLess(self.budget,120)
    def test_options_worker_split_and_resolution_shown(self):
        self.ready();self.run_fz()
        c={'id':'C1','detector_type':'FLAME','position':[0.,5.,1.],'azimuth':0.,'elevation':0.,'roll':0.,'library_id':'FL','receiver':None,'cost':'1','feasible':True,'maintainable':True}
        pay={'contract':scs.OPTIONS_CONTRACT,'zone_id':'FZ','include_existing':True,'max_detectors':1,'required_votes':1,'grid_spacing_m':1.0,'candidates':[c]}
        job=scs.prepare_study(self.s,'LAYOUT_OPTIONS',pay);box={}
        th=threading.Thread(target=lambda:box.setdefault('r',scs.compute_study(job)));th.start();th.join(60)
        r=box['r'];self.assertEqual(r['grid_spacing_m'],1.0);self.assertEqual(r['zone_run_grid_spacing_m'],.5);self.assertFalse(r['common_resolution_with_zone_run'])
        self.assertIn('NOT directly comparable',r['resolution_note']);self.assertEqual(r['mode'],'SLICES');self.assertGreater(r['eligible_measure'],0)
        stored=scs.store_study(self.s,job,'OPT1',r,'T');self.assertEqual(stored['run_id'],'OPT1')
        job2=scs.prepare_study(self.s,'LAYOUT_OPTIONS',dict(pay,grid_spacing_m=None));r2=scs.compute_study(job2)
        self.assertTrue(r2['common_resolution_with_zone_run'])
        d=w.row(self.s,'detector_details','F1');w.detector_command(self.s,{**{k:d[k] for k in ('azimuth','elevation','roll')},'id':'F1','detector_type':'FLAME','x':0.5,'y':0.,'z':1.,'evidence_id':EV},None,'T')
        with self.assertRaises(CaseError):scs.store_study(self.s,job2,'OPT2',r2,'T')
        c2=dict(c,id='C2',azimuth=float('nan'))
        with self.assertRaises(CaseError):scs.prepare_study(self.s,'LAYOUT_OPTIONS',dict(pay,candidates=[c2]))

class F17ImportBudgets(unittest.TestCase):
    def test_duplicate_csv_headers_refused(self):
        raw=(','.join(list(CSV_HEADERS)+[CSV_HEADERS[0]])+'\n').encode()
        with self.assertRaises(ValueError):parse_library(raw,'CSV')
    def test_import_zip_and_row_budgets(self):
        from openpyxl import Workbook
        wb=Workbook();ws=wb.active;ws.title='Library';ws.append(list(CSV_HEADERS))
        for i in range(6000):ws.append(['x']*len(CSV_HEADERS))
        b=io.BytesIO();wb.save(b);raw=b.getvalue();self.assertLess(len(raw),8_000_000)
        import openpyxl
        with mock.patch.object(openpyxl,'load_workbook',side_effect=AssertionError('materialised before preflight')):
            with self.assertRaises(ValueError) as e:parse_library(raw,'XLSX')
        self.assertIn('bound',str(e.exception))
        from fgmapping.services.bulk_import import parse_rows,HEADERS
        wb=Workbook();ws=wb.active;ws.title='Registers';ws.append(list(HEADERS))
        for i in range(2500):ws.append(['SYNTHETIC']*len(HEADERS))
        b=io.BytesIO();wb.save(b)
        with mock.patch.object(openpyxl,'load_workbook',side_effect=AssertionError('materialised before preflight')):
            with self.assertRaises(CaseError):parse_rows(b.getvalue(),'XLSX')
        bomb=io.BytesIO()
        with zipfile.ZipFile(bomb,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('xl/worksheets/sheet1.xml',b'<a>'+b' '*40_000_000+b'</a>')
        with self.assertRaises(ValueError):parse_library(bomb.getvalue(),'XLSX')

class F20F21Rendering(unittest.TestCase):
    def test_edge_cell_plot_bounds(self):
        from fgmapping.engine.coverage import zone_coverage,Obstructions
        from fgmapping.services.heatmap import render_slice
        from PIL import Image
        lib={'E':flame_entry(contour=((0,100),(90,100)),fov=(180,180))}
        r,samples=engineering_flame_coverage(zone={'id':'Z','kind':'FIRE_ZONE','low':(0,0,0),'high':(1,1,1)},setup=flame_setup(spacing=.3,slices=(.5,)),detectors=[det('D',(-5,.5,.5))],library=lib,scene=scene())
        last=[row for row in samples['rows'] if row[5][0]>=0.9-1e-9]
        self.assertTrue(last);self.assertTrue(all(abs((row[6][0]-row[5][0])-0.1)<1e-9 for row in last))
        res=dict(r,zone_bounds=((0,0,0),(1,1,1)))
        img=Image.open(io.BytesIO(render_slice(res,samples,.5,None,(),px_per_m=100)))
        # the zone spans x in [0,1]: pixel just beyond x=1.0 must not carry a cell colour (no nominal 0.3 m overdraw)
        P=lambda x,y:(60+x*100,70+(1.0-y)*100)  # no detectors drawn: plot bounds = zone [0,1]
        x,y=P(1.02,.5);self.assertEqual(img.getpixel((int(x),int(y))),(255,255,255))
        x,y=P(.97,.5);self.assertNotEqual(img.getpixel((int(x),int(y))),(255,255,255))
    def test_report_long_names_and_tall_figures(self):
        from fgmapping.services.coverage_report import _figure_size
        from PIL import Image
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'tall.png';Image.new('RGB',(400,4000),(0,0,0)).save(p)
            wi,hi=_figure_size(p,9.5,5.6);self.assertLessEqual(hi,5.6+1e-9);self.assertLessEqual(wi,9.5+1e-9)
            p=Path(t)/'wide.png';Image.new('RGB',(8000,400),(0,0,0)).save(p)
            wi,hi=_figure_size(p,9.5,5.6);self.assertLessEqual(wi,9.5+1e-9)

class F15QtLifecycle(unittest.TestCase):
    def test_case_close_during_coverage(self):
        code=r'''
import sys,threading,time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from fgmapping.ui.main import MainWindow
app=QApplication([]);w=MainWindow();w.settings.clear()
class S:key='K1'
w.session=S()
stop=threading.Event();stored=[]
state={'done':[],'error':None,'cancel':False,'progress':'','session':w.session,'case_key':'K1','kind':'COVERAGE'}
def work():
    while not state['cancel']:time.sleep(.01)
    state['finished']=True
w.start_job(state,work,'test');assert w.coverage_timer.isActive()
w.cancel_coverage();assert state['cancel'] and state['orphaned'] and w.coverage_job is None and not w.coverage_timer.isActive()
assert not state['thread'].is_alive()
# late result for a different case is rejected, never stored
state2={'done':[('X',None,None,None,None)],'error':None,'cancel':False,'progress':'','session':object(),'case_key':'K0','kind':'COVERAGE','finished':True}
import fgmapping.services.coverage as cov
cov.store_run=lambda *a,**k:stored.append(a)
from PySide6.QtWidgets import QProgressDialog
w.coverage_progress=QProgressDialog();w.coverage_job=state2;w.coverage_timer.start(10);w.poll_coverage()
assert stored==[] and w.coverage_job is None and not w.coverage_timer.isActive() and state2['cancel']
w.session=None;print('LIFECYCLE_OK')
'''
        env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PYTHONPATH=str(ROOT/'src')+os.pathsep+os.environ.get('PYTHONPATH',''))
        r=subprocess.run([sys.executable,'-B','-c',code],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
        self.assertIn('LIFECYCLE_OK',r.stdout,r.stdout)

class F14F22Provenance(Fixture):
    def test_outputs_keep_example_provenance(self):
        self.ready();res=self.run_fz()
        self.assertIn('sampled',res['measure_basis']);self.assertEqual(set(res['library_used']),{'FL'});self.assertEqual(len(res['library_used']['FL']['sha256']),64)
        from fgmapping.services.coverage_report import coverage_snapshot
        snap=coverage_snapshot(self.s);z=snap['zones'][0]
        self.assertEqual(z['library_used'][0]['id'],'FL');self.assertIn('lifecycle',z);self.assertTrue(all('library_used' in f and 'lifecycle' in f for f in snap['figures']))
        from fgmapping.services.coverage_report import setup_text
        self.assertIn('sampled-point visible fraction',setup_text(z['setup']))  # F14 naming

if __name__=='__main__':unittest.main()
