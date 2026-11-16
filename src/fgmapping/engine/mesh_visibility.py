"""WP04 candidate numerical visibility; NOT flame response or coverage.

Method MV-1: segment/plane intersection, oriented edge halfspaces; BVH broadphase.
Closed edges/contact block. Coplanar ray/face is explicitly indeterminate and
refused rather than assumed clear. abs metre tolerance is a required argument.
No self-intersection/watertightness qualification is inferred from this method.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from fgmapping.domain.scene import Mesh,vector
from fgmapping.engine.geometry import Box,line_hits_box

def sub(a,b):return tuple(a[i]-b[i] for i in range(3))
def dot(a,b):return sum(a[i]*b[i] for i in range(3))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(v):return math.sqrt(dot(v,v))
def tolerance(eps):
    if not math.isfinite(eps) or not 0<eps<=.001:raise ValueError('Explicit tolerance in (0,0.001] metres required')

def segment_triangle(start,end,triangle,eps):
    tolerance(eps);start=vector(start);end=vector(end)
    if len(triangle)!=3:raise ValueError('Triangle requires three vertices')
    a,b,c=(vector(p) for p in triangle);n=cross(sub(b,a),sub(c,a));length=norm(n)
    if length<=1e-12:raise ValueError('Degenerate triangle')
    n=tuple(x/length for x in n)
    ds=dot(n,sub(start,a));de=dot(n,sub(end,a))
    if abs(ds)<=eps and abs(de)<=eps:raise ValueError('Coplanar segment: visibility indeterminate')
    if ds>eps and de>eps or ds<-eps and de<-eps:return False
    denominator=ds-de
    if denominator==0:return False
    t=ds/denominator;segment_length=norm(sub(end,start))
    param_eps=eps/max(segment_length,eps)
    if t < -param_eps or t>1+param_eps:return False
    t=max(0,min(1,t));p=tuple(start[i]+t*(end[i]-start[i]) for i in range(3))
    for x,y in ((a,b),(b,c),(c,a)):
        if dot(n,cross(sub(y,x),sub(p,x))) < -eps*norm(sub(y,x)):return False
    return True

@dataclass
class Node:
    box: Box
    faces: tuple = ()
    children: tuple = ()

class MeshIndex:
    def __init__(self,mesh:Mesh,eps:float):
        tolerance(eps);self.mesh=mesh;self.eps=eps
        def build(ids):
            points=[mesh.vertices[i] for f in ids for i in mesh.faces[f]]
            low=tuple(min(p[i] for p in points)-eps for i in range(3));high=tuple(max(p[i] for p in points)+eps for i in range(3))
            box=Box(low,high)
            if len(ids)<=8:return Node(box,tuple(ids))
            axis=max(range(3),key=lambda i:high[i]-low[i])
            ids=sorted(ids,key=lambda j:(sum(mesh.vertices[k][axis] for k in mesh.faces[j]),j));mid=len(ids)//2
            return Node(box,children=(build(ids[:mid]),build(ids[mid:])))
        self.root=build(list(range(len(mesh.faces))))
    def blocked(self,start,end):
        start=vector(start);end=vector(end)
        def visit(node):
            if not line_hits_box(start,end,node.box,eps=1e-15):return False
            for id in node.faces:
                if segment_triangle(start,end,tuple(self.mesh.vertices[i] for i in self.mesh.faces[id]),self.eps):return True
            return any(visit(c) for c in node.children)
        return visit(self.root)

def finite_target_visible_fraction(origin,targets,indexes):
    """Weighted visibility of explicitly supplied target samples; no radiation model."""
    origin=vector(origin);targets=tuple(targets);indexes=tuple(indexes)
    if not targets or any(not math.isfinite(w) or w<=0 for p,w in targets):raise ValueError('Positive target weights required')
    values=[]
    for p,w in targets:
        p=vector(p)
        values.append((w,not any(i.blocked(origin,p) for i in indexes)))
    return math.fsum(w for w,visible in values if visible)/math.fsum(w for w,_ in values)
