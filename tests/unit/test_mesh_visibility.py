import random,unittest
from fgmapping.engine.mesh_visibility import segment_triangle,MeshIndex,finite_target_visible_fraction
from fgmapping.domain.scene import box_mesh
from tools.independent_triangle_oracle import exact_segment_triangle
class Visibility(unittest.TestCase):
    tri=((2,-1,-1),(2,1,-1),(2,0,1))
    def test_exact_rational_oracle_250(self):
        rng=random.Random(712)
        for _ in range(250):
            p=(4,rng.randint(-20,20)/4,rng.randint(-20,20)/4)
            self.assertEqual(segment_triangle((0,0,0),p,self.tri,1e-10),exact_segment_triangle((0,0,0),p,self.tri),p)
    def test_edge_endpoint(self):
        for p in ((2,0,0),(4,-2,-2)):
            self.assertTrue(segment_triangle((0,0,0),p,self.tri,1e-10))
    def test_coplanar_refused(self):
        with self.assertRaises(ValueError):segment_triangle((2,0,0),(2,1,0),self.tri,1e-10)
    def test_boundary_tolerances(self):
        for eps in (1e-6,1e-8,1e-10):
            self.assertTrue(segment_triangle((0,0,0),(4,0,0),self.tri,eps))
            self.assertFalse(segment_triangle((0,0,0),(4,9,0),self.tri,eps))
    def test_bvh_vs_box_constructive(self):
        index=MeshIndex(box_mesh((2,-1,-1),(3,1,1)),1e-9)
        self.assertTrue(index.blocked((0,0,0),(5,0,0)));self.assertFalse(index.blocked((0,0,0),(5,5,0)))
    def test_partial_finite_target(self):
        index=MeshIndex(box_mesh((2,-1,-1),(3,1,1)),1e-9)
        self.assertEqual(finite_target_visible_fraction((0,0,0),[((5,0,0),3),((5,5,0),1)],[index]),.25)
    def test_bad_tolerance(self):
        for eps in (0,-1,float('nan'),1):
            with self.assertRaises(ValueError):segment_triangle((0,0,0),(4,0,0),self.tri,eps)
