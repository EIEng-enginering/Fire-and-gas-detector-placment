import unittest
from fgmapping.domain.scene import Scene,Frame,Component,Mesh,box_mesh
from fgmapping.engine.inspection import inspect_target,target_samples
class TargetInspection(unittest.TestCase):
 def target(self,n=4):return {'center_m':(4,0,0),'u':(0,1,0),'v':(0,0,1),'width_m':2,'height_m':2,'nx':n,'ny':n}
 def scene(self,mesh):return Scene((Frame('F','m','SYN'),),(Component('W','Synthetic wall','WALL','F',mesh,'SYN-E'),),'A','0'*64)
 def test_half_square_independent_area_oracle(self):
  scene=self.scene(Mesh(((2,0,-10),(2,10,-10),(2,10,10),(2,0,10)),((0,1,2),(0,2,3))))
  for n in (4,8,16):
   r=inspect_target(scene,(0,0,0),['W'],self.target(n),1e-9);self.assertEqual(r['visibility_fraction'],.5);self.assertEqual(r['target_area_m2'],4);self.assertEqual(r['blocked_area_m2'],2)
 def test_clear_field_and_total_area_conservation(self):
  s=self.scene(box_mesh((10,10,10),(11,11,11)));r=inspect_target(s,(0,0,0),[],self.target(),1e-9)
  self.assertEqual(r['visibility_fraction'],1);self.assertEqual(sum(r[k] for k in ('clear_area_m2','blocked_area_m2','indeterminate_area_m2')),r['target_area_m2'])
 def test_coplanar_uncertainty_not_removed_from_denominator(self):
  s=self.scene(Mesh(((0,-10,-10),(0,10,-10),(0,0,10)),((0,1,2),)));t={**self.target(),'center_m':(0,1,0),'u':(0,1,0),'v':(0,0,1)}
  r=inspect_target(s,(0,0,0),['W'],t,1e-9);self.assertIsNone(r['visibility_fraction']);self.assertEqual(r['visibility_lower_bound'],0);self.assertEqual(r['visibility_upper_bound'],1)
 def test_inside_closed_box_never_declared_clear(self):
  s=self.scene(box_mesh((-5,-5,-5),(5,5,5)));r=inspect_target(s,(0,0,0),['W'],self.target(),1e-9);self.assertEqual(r['clear_area_m2'],0);self.assertEqual(r['indeterminate_area_m2'],4)
 def test_bad_axes_and_sampling(self):
  for change in ({'u':(0,2,0)},{'v':(0,1,0)},{'nx':0},{'nx':10000}):
   with self.assertRaises(ValueError):target_samples({**self.target(),**change})
 def test_no_obstacles_does_not_bypass_tolerance_validation(self):
  s=self.scene(box_mesh((10,10,10),(11,11,11)))
  with self.assertRaises(ValueError):inspect_target(s,(0,0,0),[],self.target(),0)
 def test_zero_length_rays_remain_indeterminate(self):
  s=self.scene(box_mesh((10,10,10),(11,11,11)));t={**self.target(),'nx':1,'ny':1}
  r=inspect_target(s,(4,0,0),[],t,1e-8);self.assertIsNone(r['visibility_fraction']);self.assertEqual(r['indeterminate_area_m2'],4)
