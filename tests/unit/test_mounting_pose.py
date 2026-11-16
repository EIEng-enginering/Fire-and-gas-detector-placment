import math,unittest
from dataclasses import replace
from fgmapping.domain.scene import Frame,Scene,Component,box_mesh,synthetic_scene
from fgmapping.domain.mounting import mount_pose,rotation,angles,multiply
class MountPose(unittest.TestCase):
 def scene(self):
  f=Frame('ROT','mm','SYN',matrix=((0,-2,0,10),(3,0,0,20),(0,0,4,30),(0,0,0,1)))
  c=Component('CAD-V','Synthetic vessel','EQUIPMENT','ROT',box_mesh((0,0,0),(4000,4000,4000)),'SYN-E')
  return Scene((f,),(c,),'SYN-A','0'*64)
 def test_known_scaled_anchor_and_unscaled_metre_offset(self):
  r=mount_pose(self.scene(),'CAD-V',(1000,2000,3000),(1,2,3),(0,0,0))
  self.assertEqual(r['anchor_world'],(6,23,42));self.assertEqual(r['position'],(4,24,45))
  for x,y in zip(r['orientation_world'],(90,0,0)):self.assertAlmostEqual(x,y,places=10)
 def test_full_roll_and_gimbal_rotation_roundtrip(self):
  for a,e,r in ((30,20,40),(-140,-30,-80),(13,90,50),(-10,-90,60)):
   m=rotation(a,e,r);reconstructed=rotation(*angles(m))
   for row1,row2 in zip(m,reconstructed):
    for x,y in zip(row1,row2):self.assertAlmostEqual(x,y,places=10)
 def test_direction_known_90_degree_local_mount(self):
  r=mount_pose(self.scene(),'CAD-V',(0,0,0),(0,0,0),(90,0,0))
  # Frame rotates +X to +Y; local +Y therefore points world -X.
  self.assertAlmostEqual(r['rotation_world'][0][0],-1,places=10)
  self.assertAlmostEqual(r['rotation_world'][1][0],0,places=10)
 def test_unknown_component_and_bad_angles(self):
  for component,angles0 in [('MISSING',(0,0,0)),('CAD-V',(0,100,0))]:
   with self.assertRaises(ValueError):mount_pose(self.scene(),component,(0,0,0),(0,0,0),angles0)
 def test_source_change_changes_fingerprint(self):
  s=self.scene();a=mount_pose(s,'CAD-V',(0,0,0),(0,0,0),(0,0,0));changed=replace(s,frames=(replace(s.frames[0],matrix=((0,-2,0,11),(3,0,0,20),(0,0,4,30),(0,0,0,1))),))
  b=mount_pose(changed,'CAD-V',(0,0,0),(0,0,0),(0,0,0));self.assertNotEqual(a['component_fingerprint'],b['component_fingerprint'])
