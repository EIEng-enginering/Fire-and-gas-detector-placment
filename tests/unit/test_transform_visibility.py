import math,unittest
from fgmapping.engine.mesh_visibility import segment_triangle
class TransformedVisibility(unittest.TestCase):
    def test_scale_rotation_translation_preserves_constructive_hits(self):
        for scale in (.001,1,1000):
            for angle in (0,35,90,180):
                c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
                def move(p):return (100+scale*(c*p[0]-s*p[1]),-30+scale*(s*p[0]+c*p[1]),7+scale*p[2])
                tri=tuple(move(p) for p in ((2,-1,-1),(2,1,-1),(2,0,1)))
                self.assertTrue(segment_triangle(move((0,0,0)),move((4,0,0)),tri,1e-10))
                self.assertFalse(segment_triangle(move((0,0,0)),move((4,5,0)),tri,1e-10))
