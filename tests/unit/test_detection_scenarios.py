import unittest
from decimal import Decimal
from fgmapping.engine.detection import *
from fgmapping.engine.scenarios import SyntheticScenario,aggregate
from fgmapping.engine.optimisation import SyntheticMount,enumerate_layouts
class Detection(unittest.TestCase):
    def test_missing_physics_always_refused(self):
        for fn in (engineering_flame_coverage,engineering_gas_coverage):
            for kw in ({},{'performance':{'claimed':'approved'},'basis':{'claimed':'approved'},'field':{}}):
                with self.assertRaises(EngineeringUnavailable):fn(**kw)
    def test_voting_denominators(self):
        rows=[('A',3,[True,False]),('B',1,[True,True])]
        self.assertEqual(synthetic_weighted_votes(rows,1)['fraction'],1)
        self.assertEqual(synthetic_weighted_votes(rows,2)['fraction'],.25)
        self.assertEqual(synthetic_weighted_votes(rows,3)['fraction'],0)
    def test_bad_votes(self):
        for rows,k in (([],1),([('A',0,[True])],1),([('A',1,[1])],1),([('A',1,[True])],True)):
            with self.assertRaises(ValueError):synthetic_weighted_votes(rows,k)
    def test_gas_point_boundary(self):
        c=UniformDesignCloud((0,0,0),(2,3,4),100,'SYNTHETIC analytic construct')
        self.assertEqual(c.concentration((0,0,0)),100);self.assertEqual(c.concentration((-1,0,0)),0)
        self.assertTrue(synthetic_threshold(100,100,'ppm'))
    def test_gas_integral_known_answer(self):
        c=UniformDesignCloud((0,0,0),(2,3,4),100,'SYNTHETIC analytic construct')
        # Independent chord: x in [0,2], c=100 ppm, length=2m -> 200 ppm*m.
        self.assertEqual(c.path_integral_ppm_m((-5,1,1),(5,1,1)),200)
        self.assertEqual(c.path_integral_ppm_m((5,1,1),(-5,1,1)),200)
        self.assertEqual(c.path_integral_ppm_m((-5,4,1),(5,4,1)),0)
    def test_thin_and_diagonal_cloud(self):
        import math
        c=UniformDesignCloud((0,0,0),(1,1,1),10,'SYNTHETIC')
        self.assertAlmostEqual(c.path_integral_ppm_m((-1,-1,-1),(2,2,2)),10*math.sqrt(3))
        c=UniformDesignCloud((0,0,0),(.0001,1,1),100,'SYNTHETIC')
        self.assertAlmostEqual(c.path_integral_ppm_m((-1,.5,.5),(1,.5,.5)),.01)
    def test_bad_gas_inputs(self):
        with self.assertRaises(ValueError):synthetic_threshold(1,1,'LEL*m')
        with self.assertRaises(ValueError):UniformDesignCloud((0,0,0),(1,1,1),-1,'SYN')
        with self.assertRaises(ValueError):UniformDesignCloud((0,0,0),(1,1,1),1,'SYN').path_integral_ppm_m((0,0,0),(0,0,0))
class Scenarios(unittest.TestCase):
    def rows(self):return [SyntheticScenario('A','0.1','1','SYN-F1','SYN-R1','2','3'),SyntheticScenario('B','0.3','0','SYN-F2','SYN-R2','4','3')]
    def test_exact_decimal_vs_independent_fraction(self):
        from fractions import Fraction
        r=aggregate(self.rows());expected=(Fraction(1,10)*1+Fraction(3,10)*0)/(Fraction(1,10)+Fraction(3,10))
        self.assertEqual(Decimal(r['frequency_weighted_detection_fraction']),Decimal(expected.numerator)/Decimal(expected.denominator))
        self.assertEqual(r['unweighted_mean_detection_probability'],'0.5');self.assertEqual(r['risk_reduction'],'NOT CALCULATED')
    def test_missing_time_does_not_become_zero(self):
        r=aggregate([SyntheticScenario('A','1','1','SYN','SYN')]);self.assertEqual(r['timely_frequency_weighted_detection_fraction'],'NOT SUPPLIED')
    def test_bad_scenarios(self):
        for rows in ([],self.rows()*2,[SyntheticScenario('A','0','1','SYN','SYN')],[SyntheticScenario('A',.1,'1','SYN','SYN')],[SyntheticScenario('A','1','2','SYN','SYN')]):
            with self.assertRaises(ValueError):aggregate(rows)
class Optimisation(unittest.TestCase):
    def test_exhaustive_known_optimum_and_baseline_immutable(self):
        m=(SyntheticMount('A',frozenset({'x'}),'2',True,True),SyntheticMount('B',frozenset({'y'}),'3',True,True),SyntheticMount('C',frozenset({'x','y'}),'1',False,True))
        r=enumerate_layouts(m,{'x':'3','y':'1'},2,1)
        self.assertEqual(r['enumerated'],4);self.assertEqual(r['pareto'][0]['mount_ids'],['A','B']);self.assertEqual(r['pareto'][0]['fraction'],'1')
        self.assertEqual(m[2].feasible,False)
    def test_two_votes_unachievable(self):
        m=[SyntheticMount('A',frozenset({'x'}),'1',True,True)]
        self.assertTrue(all(Decimal(r['fraction'])==0 for r in enumerate_layouts(m,{'x':'1'},1,2)['pareto']))
