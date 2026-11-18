"""Rev G known-answer tests for the geographic coverage engine (FG-FLAME-GEO/1.0, FG-GAS-GEO/1.0)."""
import math,unittest
from fgmapping.engine.coverage import Obstructions,zone_coverage,discretise,chord_length,detector_frame,flame_geometry_ok,target_points
from fgmapping.engine.detection import engineering_flame_coverage,engineering_gas_coverage,EngineeringUnavailable
from fgmapping.domain.detector_library import contour_range,validate_entry,CONTRACT
from fgmapping.domain.scene import Scene,Frame,Component,box_mesh,content_hash

SRC={'title':'Unit-test analytic entry','revision':'T','page':'n/a','data_status':'USER DATA - to be verified'}
def flame_entry(id='E',contour=((0,10),(45,10)),fov=(180,180),kw=100.0,fuel='heptane'):
    return validate_entry({'contract':CONTRACT,'id':id,'manufacturer':'TEST','model':id,'detector_type':'FLAME','technology':'IR3','fuel_or_gas':fuel,'target_fire':{'description':'t','heat_release_kw':kw,'area_m2':None},
        'sensitivity_setting':'s','fov':{'horizontal_deg':fov[0],'vertical_deg':fov[1]},'contour':[list(r) for r in contour],'alarm_threshold':None,'path_length_m':None,'mounting':'m','source':SRC,'notes':''})
def gas_entry(id,kind,thr,path=None):
    return validate_entry({'contract':CONTRACT,'id':id,'manufacturer':'TEST','model':id,'detector_type':kind,'technology':'IR','fuel_or_gas':'methane','target_fire':None,'sensitivity_setting':'s','fov':None,'contour':None,
        'alarm_threshold':{'value':thr,'units':'%LEL' if kind=='POINT_GAS' else 'LEL.m'},'path_length_m':path,'mounting':'m','source':SRC,'notes':''})
def flame_setup(spacing=.25,mode='SLICES',slices=(0.,),geom=None,need=1.0,scaling='NONE',kw=100.0,vote=1,ref=1,targets=None):
    return {'contract':'fg-coverage-setup/1','zone_id':'Z','method':'FLAME_GEOGRAPHIC','grid_spacing_m':spacing,'mode':mode,'slice_elevations_m':list(slices) if mode=='SLICES' else [],'voting_required':vote,
            'performance_targets':targets or {},'convergence':{'refinement':ref,'tolerance':'0.01'},'criterion_reference':'unit test','standoff_m':0.0,'tolerance_m':1e-6,
            'flame':{'fuel':'heptane','heat_release_kw':kw,'fire_size_scaling':scaling,'target_geometry':geom or {'type':'POINT'},'min_visible_fraction':need},'gas':None,'notes':''}
def gas_setup(cloud,conc,types,spacing=.25,mode='SLICES',slices=(0.,)):
    return {'contract':'fg-coverage-setup/1','zone_id':'Z','method':'GAS_GEOGRAPHIC','grid_spacing_m':spacing,'mode':mode,'slice_elevations_m':list(slices) if mode=='SLICES' else [],'voting_required':1,
            'performance_targets':{},'convergence':{'refinement':1,'tolerance':'0.01'},'criterion_reference':'unit test','standoff_m':0.0,'tolerance_m':1e-6,'flame':None,
            'gas':{'gas':'methane','cloud':cloud,'cloud_concentration_pct_lel':conc,'detector_types':types},'notes':''}
def det(id,pos,az=0.,el=0.,lib='E',kind='FLAME',receiver=None):
    return {'id':id,'detector_type':kind,'position':pos,'azimuth':az,'elevation':el,'roll':0.,'library_id':lib,'receiver':receiver}
def scene(*boxes):
    comps=tuple(Component(id,id,'WALL','L',box_mesh(lo,hi),'EV') for id,lo,hi in boxes) or (Component('FAR','far','EQUIPMENT','L',box_mesh((900,900,900),(901,901,901)),'EV'),)
    return Scene((Frame('L','m','test'),),comps,'T',content_hash([list(b) for b in boxes]))
def run(zone_low,zone_high,setup,dets,lib,sc=None,excluded=()):
    kw=dict(zone={'id':'Z','kind':'FIRE_ZONE' if setup['method']=='FLAME_GEOGRAPHIC' else 'GAS_ZONE','low':zone_low,'high':zone_high},setup=setup,detectors=dets,library=lib,scene=sc or scene(),excluded_component_ids=excluded)
    return (engineering_flame_coverage if setup['method']=='FLAME_GEOGRAPHIC' else engineering_gas_coverage)(**kw)

class Discretisation(unittest.TestCase):
    def test_partial_cells_weighted_by_actual_volume(self):
        s=discretise((0,0,0),(1.25,1,1),.5,'VOLUME')
        self.assertAlmostEqual(sum(w for _,w in s),1.25);self.assertEqual(len(s),3*2*2)
        self.assertIn(((1.125,.25,.25),.25*.5*.5),s)
    def test_slices_are_area_weighted_and_inside_zone(self):
        s=discretise((0,0,0),(2,1,3),1,'SLICES',(1.,2.));self.assertEqual(sum(w for _,w in s),4.)
        with self.assertRaises(ValueError):discretise((0,0,0),(2,1,3),1,'SLICES',(5.,))

class FlameKnownAnswers(unittest.TestCase):
    def test_contour_interpolation_and_cutoff(self):
        e=flame_entry(contour=((0,40),(30,30),(45,10)))
        self.assertEqual(contour_range(e,0),40);self.assertAlmostEqual(contour_range(e,15),35);self.assertAlmostEqual(contour_range(e,37.5),20);self.assertEqual(contour_range(e,45.01),0)
    def test_single_detector_open_slice_exact_sector(self):
        # Detector on the slice plane, axis +X, cone 45 deg, range 10: covered area = quarter disc (pi*100/4).
        r,_=run((0,-10,-1),(10,10,1),flame_setup(spacing=.1),[det('D',(0,0,0))],{'E':flame_entry()})
        self.assertAlmostEqual(r['fractions']['1ooN'],(math.pi*100/4)/200,delta=.005)
        self.assertAlmostEqual(r['fractions']['0ooN']+r['fractions']['1ooN'],1.)
    def test_single_detector_open_volume_exact_cone_sector(self):
        setup=flame_setup(spacing=.25,mode='VOLUME',ref=2)
        r,_=run((0,-10,-10),(10,10,10),setup,[det('D',(0,0,0))],{'E':flame_entry()})
        exact=2*math.pi/3*1000*(1-math.cos(math.pi/4))/4000
        self.assertAlmostEqual(r['fractions']['1ooN'],exact,delta=.004);self.assertEqual(r['convergence']['status'],'CONVERGED')
    def test_obstruction_shadow_exact(self):
        # Wall x 4..4.2, y 0..10 shadows every point beyond it with y>0. Shadowed area = half sector - triangle(0,0)(4,0)(4,4).
        sc=scene(('W',(4,0,-1),(4.2,10,1)))
        open_,_=run((0,-10,-1),(10,10,1),flame_setup(spacing=.05),[det('D',(0,0,0))],{'E':flame_entry()})
        shad,_=run((0,-10,-1),(10,10,1),flame_setup(spacing=.05),[det('D',(0,0,0))],{'E':flame_entry()},sc)
        self.assertAlmostEqual(shad['excluded_measure']['inside_obstruction'],2.0,delta=.06)
        covered_open=open_['fractions']['1ooN']*open_['eligible_measure'];covered=shad['fractions']['1ooN']*shad['eligible_measure']
        self.assertAlmostEqual(covered_open-covered,(math.pi*100/8)-8,delta=.35)
    def test_voting_two_facing_detectors_lens(self):
        lib={'E':flame_entry(contour=((0,10),(90,10)))}
        r,_=run((0,-10,-1),(10,10,1),flame_setup(spacing=.05),[det('A',(0,0,0)),det('B',(10,0,0),az=180.)],lib)
        lens=2*100*math.acos(.5)-5*math.sqrt(300)
        self.assertAlmostEqual(r['fractions']['2ooN'],lens/200,delta=.006)
        self.assertAlmostEqual(r['fractions']['1ooN'],(2*math.pi*100/2-lens)/200,delta=.006)
        self.assertEqual(r['fractions']['3ooN'],0.)
        self.assertAlmostEqual(r['per_detector_fraction']['A'],math.pi*50/200,delta=.006)
    def test_fov_limits_independent_of_contour(self):
        d=det('D',(0,0,0));d['frame']=detector_frame(0,0,0);e=flame_entry(contour=((0,10),(80,10)),fov=(60,180))
        self.assertTrue(flame_geometry_ok(d,e,(5,5*math.tan(math.radians(29)),0))[0]);self.assertFalse(flame_geometry_ok(d,e,(5,5*math.tan(math.radians(31)),0))[0])
        self.assertFalse(flame_geometry_ok(d,e,(-1,0,0))[0])
    def test_detector_frame_elevation_and_roll(self):
        f,r,u=detector_frame(90,-30,0);self.assertAlmostEqual(f[1],math.cos(math.radians(30)));self.assertAlmostEqual(f[2],-.5)
        f,r,u=detector_frame(0,-90,0);self.assertAlmostEqual(f[2],-1);self.assertAlmostEqual(abs(r[1]),1)
        _,r2,u2=detector_frame(0,0,90);self.assertAlmostEqual(r2[2],1)
    def test_inverse_square_fire_size_scaling(self):
        lib={'E':flame_entry(kw=100.)};a,_=run((0,-20,-1),(20,20,1),flame_setup(spacing=.1),[det('D',(0,0,0))],lib)
        b,_=run((0,-20,-1),(20,20,1),flame_setup(spacing=.1,scaling='INVERSE_SQUARE',kw=400.),[det('D',(0,0,0))],lib)
        self.assertAlmostEqual(b['fractions']['1ooN']/a['fractions']['1ooN'],4.,delta=.05)
    def test_extended_cylinder_target_partial_obstruction(self):
        # Wall (top 1.5 m) hides the two lower of four levels of a 2 m cylinder fire 8 m in front of the detector at z=2.
        sc=scene(('LOW',(4,-5,-1),(4.2,5,1.5)));geom={'type':'CYLINDER','diameter_m':.4,'height_m':2.0,'rings':4,'levels':4}
        lib={'E':flame_entry(contour=((0,30),(45,30)))}
        for need,expect in ((.5,1.),(.9,0.)):
            r,_=run((7.95,-.05,-.05),(8.05,.05,.05),flame_setup(spacing=.1,mode='VOLUME',geom=geom,need=need),[det('D',(0,0,2.0))],lib,sc)
            self.assertEqual(r['fractions']['1ooN'],expect,need)
        self.assertEqual(len(target_points((0,0,0),geom)),20)
    def test_excluded_component_volume_reported_and_non_obstructing(self):
        sc=scene(('W',(4,-10,-1),(4.2,10,1)));lib={'E':flame_entry()}
        r,_=run((0,-10,-1),(10,10,1),flame_setup(spacing=.1),[det('D',(0,0,0))],lib,sc,excluded=('W',))
        self.assertAlmostEqual(r['excluded_measure']['excluded_component'],4.0,delta=.11);self.assertAlmostEqual(r['fractions']['1ooN']*r['eligible_measure'],math.pi*25-0.2*8.2,delta=.6)
    def test_user_targets_compared_never_defaulted(self):
        r,_=run((0,-10,-1),(10,10,1),flame_setup(spacing=.5,targets={'1ooN':'0.30','2ooN':'NOT SUPPLIED'}),[det('D',(0,0,0))],{'E':flame_entry()})
        self.assertEqual(r['performance_targets']['1ooN']['status'],'MEETS USER TARGET');self.assertEqual(r['performance_targets']['2ooN']['status'],'NO USER TARGET');self.assertEqual(r['performance_targets']['3ooN']['status'],'NO USER TARGET')
        r,_=run((0,-10,-1),(10,10,1),flame_setup(spacing=.5,targets={'1ooN':'0.50'}),[det('D',(0,0,0))],{'E':flame_entry()})
        self.assertEqual(r['performance_targets']['1ooN']['status'],'BELOW USER TARGET')
    def test_deterministic(self):
        sc=scene(('W',(4,0,-1),(4.2,10,1)))
        a=run((0,-10,-1),(10,10,1),flame_setup(spacing=.5),[det('D',(0,0,0)),det('B',(10,0,0),az=180.)],{'E':flame_entry()},sc)
        b=run((0,-10,-1),(10,10,1),flame_setup(spacing=.5),[det('B',(10,0,0),az=180.),det('D',(0,0,0))],{'E':flame_entry()},sc)
        self.assertEqual(content_hash(a),content_hash(b))

class GasKnownAnswers(unittest.TestCase):
    def test_point_detector_sphere_cloud_volume(self):
        lib={'P':gas_entry('P','POINT_GAS',20.)}
        r,_=run((-5,-5,-5),(5,5,5),gas_setup({'shape':'SPHERE','diameter_m':5.},100.,['POINT_GAS'],spacing=.25,mode='VOLUME'),[det('G',(0,0,0),lib='P',kind='POINT_GAS')],lib)
        self.assertAlmostEqual(r['fractions']['1ooN'],4/3*math.pi*2.5**3/1000,delta=.002)
    def test_point_detector_below_threshold_cannot_alarm(self):
        lib={'P':gas_entry('P','POINT_GAS',20.)}
        r,_=run((-5,-5,-1),(5,5,1),gas_setup({'shape':'SPHERE','diameter_m':5.},10.,['POINT_GAS']),[det('G',(0,0,0),lib='P',kind='POINT_GAS')],lib)
        self.assertEqual(r['fractions']['1ooN'],0.);self.assertTrue(r['findings'])
    def test_ellipsoid_axes(self):
        lib={'P':gas_entry('P','POINT_GAS',20.)}
        r,_=run((-10,-10,-1),(10,10,1),gas_setup({'shape':'ELLIPSOID','axes_m':[10.,4.,2.]},100.,['POINT_GAS'],spacing=.1),[det('G',(0,0,0),lib='P',kind='POINT_GAS')],lib)
        self.assertAlmostEqual(r['fractions']['1ooN'],math.pi*5*2/400,delta=.003)
    def test_chord_length_exact(self):
        self.assertAlmostEqual(chord_length((-10,0,0),(10,0,0),(0,0,0),(2.5,2.5,2.5)),5.)
        self.assertAlmostEqual(chord_length((-10,1.5,0),(10,1.5,0),(0,0,0),(2.5,2.5,2.5)),4.)
        self.assertAlmostEqual(chord_length((0,0,0),(10,0,0),(0,0,0),(2.5,2.5,2.5)),2.5)
        self.assertEqual(chord_length((-10,3,0),(10,3,0),(0,0,0),(2.5,2.5,2.5)),0.)
    def test_open_path_band(self):
        lib={'O':gas_entry('O','OPEN_PATH',4.,{'min':1.,'max':100.})}
        # Beam y=0 well beyond zone ends; cloud 100 %LEL (1 LEL), D=5: detect when chord>=4 m -> |y|<=1.5
        r,_=run((-10,-10,-1),(10,10,1),gas_setup({'shape':'SPHERE','diameter_m':5.},100.,['OPEN_PATH'],spacing=.1),[det('O1',(-30,0,0),lib='O',kind='OPEN_PATH',receiver=(30,0,0))],lib)
        self.assertAlmostEqual(r['fractions']['1ooN'],3/20,delta=.006)
    def test_open_path_obstructed_or_too_long_is_inoperative(self):
        lib={'O':gas_entry('O','OPEN_PATH',1.,{'min':1.,'max':50.})}
        sc=scene(('W',(-.1,-1,-1),(.1,1,1)))
        r,_=run((-10,-10,-1),(10,10,1),gas_setup({'shape':'SPHERE','diameter_m':5.},100.,['OPEN_PATH'],spacing=.5),[det('O1',(-20,0,0),lib='O',kind='OPEN_PATH',receiver=(20,0,0))],lib,sc)
        self.assertEqual(r['fractions']['1ooN'],0.);self.assertTrue(any('obstructed' in f['text'] for f in r['findings']))
        r,_=run((-10,-10,-1),(10,10,1),gas_setup({'shape':'SPHERE','diameter_m':5.},100.,['OPEN_PATH'],spacing=.5),[det('O1',(-30,0,0),lib='O',kind='OPEN_PATH',receiver=(30,0,0))],lib)
        self.assertEqual(r['fractions']['1ooN'],0.);self.assertTrue(any('outside library path range' in f['text'] for f in r['findings']))

class Gate(unittest.TestCase):
    def test_refuses_without_complete_inputs(self):
        with self.assertRaises(EngineeringUnavailable):engineering_flame_coverage()
        with self.assertRaises(EngineeringUnavailable):engineering_gas_coverage(performance={'claimed':'approved'})
        good=dict(zone={'id':'Z','kind':'FIRE_ZONE','low':(0,0,0),'high':(1,1,1)},setup=flame_setup(spacing=.5,mode='VOLUME'),detectors=[det('D',(0,0,0))],library={'E':flame_entry()},scene=scene())
        for key,bad in (('library',{}),('detectors',[]),('setup',{'bad':1}),('detectors',[det('D',(0,0,0),kind='POINT_GAS')])):
            with self.assertRaises(EngineeringUnavailable,msg=key):engineering_flame_coverage(**{**good,key:bad})
        with self.assertRaises(EngineeringUnavailable):engineering_flame_coverage(**{**good,'setup':flame_setup(spacing=.5,mode='VOLUME',vote=2)})
        engineering_flame_coverage(**good)
    def test_library_contract_refuses_generic_or_incomplete(self):
        e=flame_entry()
        for mutate in (lambda p:p.update(contour=[[0,10]]),lambda p:p.update(contour=[[5,10],[10,5]]),lambda p:p['source'].update(data_status='APPROVED'),lambda p:p.update(fov=None),lambda p:p.update(alarm_threshold={'value':1,'units':'%LEL'})):
            p=__import__('json').loads(__import__('json').dumps(e));mutate(p)
            with self.assertRaises(ValueError):validate_entry(p)
