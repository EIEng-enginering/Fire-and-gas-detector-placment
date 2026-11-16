import math
import unittest
from fgmapping.engine.geometry import Box,DemoDetector,line_hits_box,illustrative_point_visible,illustrative_vote_count,illustrative_coverage
from tools.independent_geometry_oracle import independent_segment_box_intersection,independent_cone_check

class GeometryPrototypes(unittest.TestCase):
    def setUp(self):
        self.box=Box((2.,-1.,-1.),(4.,1.,1.))
        self.detector=DemoDetector('SYN-FD-01',(0.,0.,0.),(1.,0.,0.),10.,45.)

    def test_center_ray_occluded(self):
        target=(6.,0.,0.)
        self.assertEqual(line_hits_box((0.,0.,0.),target,self.box),True)
        self.assertFalse(illustrative_point_visible(self.detector,target,[self.box]))

    def test_clear_ray(self):
        target=(6.,5.,0.)
        ref=independent_segment_box_intersection((0.,0.,0.),target,self.box.low,self.box.high)
        self.assertEqual(line_hits_box((0.,0.,0.),target,self.box),ref)
        self.assertFalse(ref)

    def test_grazing_is_blocked(self):
        self.assertTrue(line_hits_box((0.,1.,0.),(6.,1.,0.),self.box))

    def test_parallel_miss(self):
        self.assertFalse(line_hits_box((0.,2.,0.),(6.,2.,0.),self.box))

    def test_inside_start_is_blocked(self):
        self.assertTrue(line_hits_box((3.,0.,0.),(8.,0.,0.),self.box))

    def test_cone_reference(self):
        points=[(6.,0.,0.),(5.,5.,0.),(1.,5.,0.),(11.,0.,0.),(-3.,0.,0.)]
        for p in points:
            self.assertEqual(illustrative_point_visible(self.detector,p,[]),independent_cone_check(self.detector.position,self.detector.direction,p,10.,45.),str(p))

    def test_one_and_two_out_of_two(self):
        a=self.detector
        b=DemoDetector('SYN-FD-02',(0.,0.,0.),(1.,0.,0.),10.,45.)
        points=[((1.,0.,0.),1.),((-1.,0.,0.),1.)]
        self.assertEqual(illustrative_vote_count([a,b],(1.,0.,0.),[]),2)
        self.assertAlmostEqual(illustrative_coverage([a,b],points,[],1),.5)
        self.assertAlmostEqual(illustrative_coverage([a,b],points,[],2),.5)
        self.assertEqual(illustrative_coverage([a],points,[],2),0.)

    def test_weighted_fraction(self):
        samples=[((1.,0.,0.),3.),((-1.,0.,0.),1.)]
        self.assertAlmostEqual(illustrative_coverage([self.detector],samples,[],1),.75)

    def test_bad_inputs_rejected(self):
        with self.assertRaises(ValueError):Box((1.,0.,0.),(0.,2.,2.))
        with self.assertRaises(ValueError):DemoDetector('X',(0.,0.,0.),(0.,0.,0.),1.,30.)
        with self.assertRaises(ValueError):DemoDetector('X',(0.,0.,0.),(1.,0.,0.),float('nan'),30.)
        with self.assertRaises(ValueError):line_hits_box((float('nan'),0.,0.),(1.,0.,0.),self.box)
        with self.assertRaises(ValueError):illustrative_coverage([self.detector],[((1.,0.,0.),0.)],[],1)

if __name__=='__main__':unittest.main()
