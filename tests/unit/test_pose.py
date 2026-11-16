import math,unittest
from fgmapping.domain.pose import direction
class Pose(unittest.TestCase):
 def test_known_axes(self):
  for a,e,expected in ((0,0,(1,0,0)),(90,0,(0,1,0)),(0,90,(0,0,1)),(180,0,(-1,0,0))):
   for x,y in zip(direction(a,e),expected):self.assertAlmostEqual(x,y,places=12)
 def test_unit_length_and_invalid(self):
  self.assertAlmostEqual(sum(x*x for x in direction(34,-23)),1,places=12)
  with self.assertRaises(ValueError):direction(0,91)

 def test_uniform_integral_overflow_refused(self):
  from fgmapping.engine.detection import UniformDesignCloud
  cloud=UniformDesignCloud((0,0,0),(10,10,10),1e308,'SYNTHETIC stress case')
  with self.assertRaises(ValueError):cloud.path_integral_ppm_m((0,1,1),(10,1,1))
