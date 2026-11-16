import math,random,unittest
from unittest.mock import patch
from fgmapping.engine.spatial import ObstacleIndex
from fgmapping.engine.inspection import inspect_target
from fgmapping.engine.mesh_visibility import MeshIndex
from fgmapping.domain.scene import Scene,Frame,Component,Mesh,box_mesh

def independent_slab(start,end,low,high):
 lo,hi=0.,1.
 for a,b,l,h in zip(start,end,low,high):
  if a==b:
   if a<l or a>h:return False
  else:
   t0,t1=(l-a)/(b-a),(h-a)/(b-a);lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1))
   if lo>hi:return False
 return True
class SceneBroadphase(unittest.TestCase):
 def test_candidates_match_independent_slab_oracle(self):
  rng=random.Random(1241);bounds=[]
  for i in range(100):
   low=tuple(rng.uniform(-20,20) for k in range(3));bounds.append((low,tuple(x+rng.uniform(.1,3) for x in low)))
  tree=ObstacleIndex(bounds)
  for n in range(200):
   a=tuple(rng.uniform(-30,30) for k in range(3));b=tuple(rng.uniform(-30,30) for k in range(3));self.assertEqual(tree.candidates(a,b),tuple(i for i,(low,high) in enumerate(bounds) if independent_slab(a,b,low,high)))
 def test_rotated_target_two_obstacles_constructive_union_oracle(self):
  c=math.sqrt(.5)
  def point(x,u,v):return (x,c*(u-v),c*(u+v))
  # At x=2 ray coordinates are half target coordinates. First obstacle
  # covers U<0; second covers V<0. Independent union area is 3/4.
  components=[]
  for id,(u0,u1,v0,v1) in [('A',(-.5,0,-.5,.5)),('B',(-.5,.5,-.5,0))]:
   vertices=tuple(point(2,u,v) for u,v in [(u0,v0),(u1,v0),(u1,v1),(u0,v1)]);components.append(Component(id,id,'WALL','F',Mesh(vertices,((0,1,2),(0,2,3))),'E'))
  scene=Scene((Frame('F','m','SYNTHETIC'),),tuple(components),'SYNTHETIC','0'*64)
  target={'center_m':[4,0,0],'u':[0,c,c],'v':[0,-c,c],'width_m':2,'height_m':2,'nx':16,'ny':16}
  actual=inspect_target(scene,[0,0,0],['B','A'],target,1e-8);self.assertAlmostEqual(actual['visibility_fraction'],.25)
  for sample in actual['samples']:
   x,y,z=sample['position_m'];u=c*(y+z);v=c*(z-y);expected='BLOCKED' if u<0 or v<0 else 'CLEAR';self.assertEqual(sample['state'],expected)
  self.assertEqual(actual,inspect_target(scene,[0,0,0],['A','B'],target,1e-8,broadphase=False))
 def test_sparse_scene_reduces_mesh_queries_without_result_change(self):
  comps=tuple(Component(str(i),str(i),'EQUIPMENT','F',box_mesh((2,20+i*2,0),(3,21+i*2,1)),'E') for i in range(64));scene=Scene((Frame('F','m','SYNTHETIC'),),comps,'SYNTHETIC','0'*64);target={'center_m':[4,0,0],'u':[0,1,0],'v':[0,0,1],'width_m':2,'height_m':2,'nx':8,'ny':8};calls=[];original=MeshIndex.blocked
  def spy(index,a,b):calls.append(1);return original(index,a,b)
  with patch.object(MeshIndex,'blocked',spy):
   indexed=inspect_target(scene,[0,0,0],[c.id for c in comps],target,1e-8);fast=len(calls);calls.clear();linear=inspect_target(scene,[0,0,0],[c.id for c in comps],target,1e-8,broadphase=False);slow=len(calls)
  self.assertEqual(indexed,linear);self.assertEqual(fast,0);self.assertEqual(slow,64*64)
 def test_coplanar_and_endpoint_ambiguity_preserved(self):
  scene=Scene((Frame('F','m','SYNTHETIC'),),(Component('B','B','WALL','F',box_mesh((-2,-2,-2),(2,2,2)),'E'),),'SYNTHETIC','0'*64);target={'center_m':[0,0,0],'u':[0,1,0],'v':[0,0,1],'width_m':1,'height_m':1,'nx':2,'ny':2}
  a=inspect_target(scene,[0,0,0],['B'],target,1e-8);self.assertEqual(a,inspect_target(scene,[0,0,0],['B'],target,1e-8,broadphase=False));self.assertEqual(a['visibility_lower_bound'],0);self.assertEqual(a['visibility_upper_bound'],1)
