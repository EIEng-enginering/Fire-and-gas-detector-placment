"""Rev G M5 known-answer tests: scenario coverage aggregation and candidate layout options."""
import unittest
from fgmapping.domain.coverage_setup import validate_setup
from fgmapping.engine.scenario_coverage import scenario_coverage,layout_options
from fgmapping.engine.optimisation import enumerate_layouts,SyntheticMount
from tests.unit.test_coverage_engine import flame_entry,gas_entry,flame_setup,gas_setup,det,scene

def env(setup,dets,lib,low=(0,0,0),high=(10,10,0),zone='Z'):
    s=validate_setup(dict(setup,zone_id=zone))
    return {'setup':s,'detectors':dets,'library':lib,'excluded_component_ids':[],'method_version':'FG-FLAME-GEO/1.0' if s['method']=='FLAME_GEOGRAPHIC' else 'FG-GAS-GEO/1.0',
            'zone':{'id':zone,'kind':'FIRE_ZONE','low':list(low),'high':list(high)}}

class ScenarioCoverage(unittest.TestCase):
    def test_frequency_weighted_fraction_exact(self):
        lib={'E':flame_entry(fov=(90,90))};e=env(flame_setup(),[det('F',[0.,0.,0.],az=0.)],lib)
        sc=scene(('WALL',(6,-1,-1),(6.5,1,1)))
        p={'scenarios':[{'id':'A','zone_id':'Z','location':[5.,0.,0.],'frequency_per_year':'0.003','frequency_source':'user'},
                        {'id':'B','zone_id':'Z','location':[-5.,0.,0.],'frequency_per_year':'0.001','frequency_source':'user'},
                        {'id':'C','zone_id':'Z','location':[8.,0.,0.],'frequency_per_year':'0.001','frequency_source':'user'}]}
        r=scenario_coverage({'Z':e},sc,p)
        self.assertEqual(r['overall']['frequency_weighted_detected_fraction'],'0.6')
        self.assertEqual([s['detected'] for s in r['scenarios']],[True,False,False]);self.assertEqual(r['overall']['total_frequency_per_year'],'0.005')
        self.assertIn('risk reduction',r['not_calculated'])
    def test_scenario_inside_solid_is_not_detected_and_flagged(self):
        lib={'E':flame_entry()};e=env(flame_setup(),[det('F',[0.,0.,0.])],lib)
        r=scenario_coverage({'Z':e},scene(('B',(4,-1,-1),(6,1,1))),{'scenarios':[{'id':'A','zone_id':'Z','location':[5.,0.,0.],'frequency_per_year':'1','frequency_source':'u'}]})
        self.assertFalse(r['scenarios'][0]['detected']);self.assertTrue(r['findings'])
    def test_gas_cloud_override(self):
        lib={'P':gas_entry('P','POINT_GAS',20.)}
        e=env(gas_setup({'shape':'SPHERE','diameter_m':2.},100.,['POINT_GAS']),[det('G',[0.,0.,0.],lib='P',kind='POINT_GAS')],lib)
        base={'id':'A','zone_id':'Z','location':[2.,0.,0.],'frequency_per_year':'1','frequency_source':'u'}
        self.assertFalse(scenario_coverage({'Z':e},scene(),{'scenarios':[base]})['scenarios'][0]['detected'])
        self.assertTrue(scenario_coverage({'Z':e},scene(),{'scenarios':[dict(base,cloud={'shape':'SPHERE','diameter_m':5.})]})['scenarios'][0]['detected'])

class LayoutOptions(unittest.TestCase):
    def setUp(self):
        self.lib={'E':flame_entry(contour=((0,100),(45,100)),fov=(90,90))}
        self.cands=[dict(id='C1',detector_type='FLAME',position=[0.,0.,0.],azimuth=45.,elevation=0.,roll=0.,library_id='E',receiver=None,cost='1',feasible=True,maintainable=True),
                    dict(id='C2',detector_type='FLAME',position=[10.,10.,0.],azimuth=-135.,elevation=0.,roll=0.,library_id='E',receiver=None,cost='2',feasible=True,maintainable=True),
                    dict(id='C3',detector_type='FLAME',position=[0.,0.,0.],azimuth=-135.,elevation=0.,roll=0.,library_id='E',receiver=None,cost='0.5',feasible=True,maintainable=True),
                    dict(id='C4',detector_type='FLAME',position=[0.,0.,0.],azimuth=45.,elevation=0.,roll=0.,library_id='E',receiver=None,cost='0',feasible=False,maintainable=True)]
    def payload(self,existing,maxd=2):
        return {'zone_id':'Z','include_existing':existing,'max_detectors':maxd,'required_votes':2,'grid_spacing_m':1.0,'candidates':self.cands,'_library':self.lib}
    def test_pareto_known_answer_candidates_only(self):
        e=env(flame_setup(spacing=1.,vote=2),[],self.lib);r=layout_options(e,scene(),self.payload(False))
        self.assertEqual(r['candidate_visible_samples'],{'C1':100,'C2':100,'C3':0,'C4':100})
        self.assertEqual([(p['mount_ids'],p['fraction'],p['cost']) for p in r['pareto']],[(['C1','C2'],'1','3'),([],'0','0')])
        self.assertTrue(r['status'].startswith('PROPOSALS ONLY'))
    def test_existing_layout_votes_are_credited(self):
        e=env(flame_setup(spacing=1.,vote=2),[det('X',[0.,0.,0.],az=45.)],self.lib);r=layout_options(e,scene(),self.payload(True,1))
        self.assertEqual(r['existing_layout_fraction'],'0');self.assertEqual(r['pareto'][0]['mount_ids'],['C1']);self.assertEqual(r['pareto'][0]['fraction'],'1')
    def test_enumerate_default_unchanged_and_base_votes_validated(self):
        m=[SyntheticMount('A',frozenset({'s1'}),'1',True,True)]
        self.assertEqual(enumerate_layouts(m,{'s1':'1','s2':'1'},1,1)['pareto'][0]['fraction'],'0.5')
        self.assertEqual(enumerate_layouts(m,{'s1':'1','s2':'1'},1,1,{'s2':1})['pareto'][0]['fraction'],'1')
        with self.assertRaises(ValueError):enumerate_layouts(m,{'s1':'1'},1,1,{'zz':1})
