"""Deterministic scene-level AABB broadphase; never classifies physical response."""
from dataclasses import dataclass
from fgmapping.engine.geometry import Box,line_hits_box
@dataclass(frozen=True)
class SpatialNode:
 box:Box
 ids:tuple=()
 children:tuple=()
class ObstacleIndex:
 def __init__(self,bounds):
  self.bounds=tuple(bounds)
  def build(ids):
   low=tuple(min(self.bounds[i][0][k] for i in ids) for k in range(3));high=tuple(max(self.bounds[i][1][k] for i in ids) for k in range(3));box=Box(low,high)
   if len(ids)<=4:return SpatialNode(box,tuple(ids))
   axis=max(range(3),key=lambda k:high[k]-low[k]);ids=sorted(ids,key=lambda i:(self.bounds[i][0][axis]+self.bounds[i][1][axis],i));mid=len(ids)//2
   return SpatialNode(box,children=(build(ids[:mid]),build(ids[mid:])))
  self.root=build(list(range(len(bounds)))) if bounds else None
 def candidates(self,start,end):
  found=[]
  def visit(n):
   if n is None or not line_hits_box(start,end,n.box,eps=1e-15):return
   for i in n.ids:
    if line_hits_box(start,end,Box(*self.bounds[i]),eps=1e-15):found.append(i)
   for child in n.children:visit(child)
  visit(self.root);return tuple(sorted(found))
