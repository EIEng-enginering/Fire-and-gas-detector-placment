"""Rev H solid membership and cell free-measure (fixes F01, F02, F03).

Membership rules (documented, deterministic):
  * Axis-aligned box components (8 vertices = AABB corners): a point is INSIDE when it is
    strictly inside the box by more than the tolerance eps on every axis. Points on, or within
    eps of, a face are BOUNDARY and treated as free (not inside).
  * General meshes: the mesh must be topologically closed (no boundary or non-manifold edges,
    no duplicate faces, consistent winding). Membership uses the generalised winding number
    (sum of triangle solid angles / 4 pi; Van Oosterom & Strackee), which is independent of
    triangle order and of how a face is triangulated, and has no shared-edge double counting.
    INSIDE when |w| > 0.5 and the point is farther than eps from every triangle; points within
    eps of the surface are BOUNDARY (free). Open/non-manifold meshes enclose no volume: they
    still obstruct line of sight as surfaces but never exclude volume (reported as a finding).
Cell measure:
  * Only box solids overlap the cell: EXACT union measure of the clipped boxes (coordinate
    compression; overlapping solids are never double counted). Solid and exclusion parts are
    separated exactly: excluded = |cell n E|, obstruction = |cell n (S u E)| - |cell n E|.
  * Any general mesh overlaps the cell: stratified k^d sub-cell midpoint classification with a
    RIGOROUS error bound = total measure of sub-cells touched by a solid boundary (triangle
    AABB overlap or partial box overlap). Untouched sub-cells are wholly inside or outside a
    closed solid, so their classification is exact.
"""
from __future__ import annotations
import math
from itertools import product

def _sub(a,b):return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def _dot(a,b):return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def _len(a):return math.sqrt(_dot(a,a))

def mesh_topology(vertices,faces):
    from collections import Counter
    edges=Counter();dirs=Counter();fs=Counter()
    for f in faces:
        fs[tuple(sorted(f))]+=1
        for x,y in ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])):edges[tuple(sorted((x,y)))]+=1;dirs[x,y]+=1
    d={'boundary_edges':sum(n==1 for n in edges.values()),'nonmanifold_edges':sum(n>2 for n in edges.values()),'duplicate_faces':sum(n-1 for n in fs.values()),
       'inconsistent_winding_edges':sum(1 for (a,b),n in edges.items() if n==2 and (dirs[a,b]==2 or dirs[b,a]==2))}
    d['closed']=not any(d.values());return d

def point_triangle_distance(p,a,b,c):
    """Exact Euclidean distance from p to triangle abc (Ericson, Real-Time Collision Detection 5.1.5)."""
    ab=_sub(b,a);ac=_sub(c,a);ap=_sub(p,a);d1=_dot(ab,ap);d2=_dot(ac,ap)
    if d1<=0 and d2<=0:return _len(ap)
    bp=_sub(p,b);d3=_dot(ab,bp);d4=_dot(ac,bp)
    if d3>=0 and d4<=d3:return _len(bp)
    vc=d1*d4-d3*d2
    if vc<=0 and d1>=0 and d3<=0:
        v=d1/(d1-d3);return _len(_sub(p,(a[0]+v*ab[0],a[1]+v*ab[1],a[2]+v*ab[2])))
    cp=_sub(p,c);d5=_dot(ab,cp);d6=_dot(ac,cp)
    if d6>=0 and d5<=d6:return _len(cp)
    vb=d5*d2-d1*d6
    if vb<=0 and d2>=0 and d6<=0:
        w=d2/(d2-d6);return _len(_sub(p,(a[0]+w*ac[0],a[1]+w*ac[1],a[2]+w*ac[2])))
    va=d3*d6-d5*d4
    if va<=0 and (d4-d3)>=0 and (d5-d6)>=0:
        w=(d4-d3)/((d4-d3)+(d5-d6));return _len(_sub(p,(b[0]+w*(c[0]-b[0]),b[1]+w*(c[1]-b[1]),b[2]+w*(c[2]-b[2]))))
    den=1/(va+vb+vc);v=vb*den;w=vc*den
    return _len(_sub(p,(a[0]+ab[0]*v+ac[0]*w,a[1]+ab[1]*v+ac[1]*w,a[2]+ab[2]*v+ac[2]*w)))

def winding_number(p,vertices,faces):
    total=0.
    for f in faces:
        a=_sub(vertices[f[0]],p);b=_sub(vertices[f[1]],p);c=_sub(vertices[f[2]],p)
        la,lb,lc=_len(a),_len(b),_len(c)
        num=_dot(a,_cross(b,c));den=la*lb*lc+_dot(a,b)*lc+_dot(a,c)*lb+_dot(b,c)*la
        total+=2*math.atan2(num,den)
    return total/(4*math.pi)

class Solid:
    """One component as a volume-bearing solid (or a zero-volume surface if not closed)."""
    def __init__(self,id,vertices,faces,eps):
        self.id=id;self.vertices=tuple(vertices);self.faces=tuple(faces);self.eps=eps
        self.low=tuple(min(p[k] for p in self.vertices) for k in range(3));self.high=tuple(max(p[k] for p in self.vertices) for k in range(3))
        corners={(x,y,z) for x in (self.low[0],self.high[0]) for y in (self.low[1],self.high[1]) for z in (self.low[2],self.high[2])}
        self.is_box=len(self.vertices)==8 and set(self.vertices)==corners and all(self.high[k]-self.low[k]>0 for k in range(3))
        self.topology=mesh_topology(self.vertices,self.faces);self.closed=self.is_box or self.topology['closed']
        self.tri_boxes=[(tuple(min(self.vertices[i][k] for i in f) for k in range(3)),tuple(max(self.vertices[i][k] for i in f) for k in range(3))) for f in self.faces]
    def contains(self,p):
        e=self.eps
        if not self.closed:return False
        if self.is_box:return all(self.low[k]+e<p[k]<self.high[k]-e for k in range(3))
        if not all(self.low[k]<p[k]<self.high[k] for k in range(3)):return False
        for f in self.faces:
            if point_triangle_distance(p,*(self.vertices[i] for i in f))<=e:return False
        return abs(winding_number(p,self.vertices,self.faces))>0.5

def _overlap(lo,hi,slo,shi,dims):
    return all(min(hi[k],shi[k])-max(lo[k],slo[k])>0 for k in dims)

def box_union_measure(boxes,lo,hi,dims):
    """Exact measure of the union of axis-aligned boxes clipped to [lo,hi] over the axes dims."""
    clipped=[]
    for blo,bhi in boxes:
        c=[(max(lo[k],blo[k]),min(hi[k],bhi[k])) for k in dims]
        if all(b>a for a,b in c):clipped.append(c)
    if not clipped:return 0.
    coords=[sorted({lo[k],hi[k]}|{c[i][j] for c in clipped for j in (0,1)}) for i,k in enumerate(dims)]
    total=0.
    for idx in product(*[range(len(cs)-1) for cs in coords]):
        mid=[(coords[i][j]+coords[i][j+1])/2 for i,j in enumerate(idx)]
        if any(all(c[i][0]<mid[i]<c[i][1] for i in range(len(dims))) for c in clipped):
            m=1.
            for i,j in enumerate(idx):m*=coords[i][j+1]-coords[i][j]
            total+=m
    return total

def tri_box_overlap(lo,hi,tri,pad=0.):
    """Exact separating-axis test (Akenine-Moller 2001) between a triangle and a closed AABB."""
    c=tuple((lo[k]+hi[k])/2 for k in range(3));h=tuple((hi[k]-lo[k])/2+pad for k in range(3))
    v=[_sub(t,c) for t in tri];e=[_sub(v[1],v[0]),_sub(v[2],v[1]),_sub(v[0],v[2])]
    for k in range(3):
        if min(x[k] for x in v)>h[k] or max(x[k] for x in v)<-h[k]:return False
    n=_cross(e[0],e[1]);r=sum(h[k]*abs(n[k]) for k in range(3))
    if abs(_dot(n,v[0]))>r:return False
    for ed in e:
        for k in range(3):
            ax=[0.,0.,0.];ax[k]=1.;a=_cross(ax,ed)
            if _dot(a,a)<1e-30:continue
            ps=[_dot(a,x) for x in v];r=sum(h[j]*abs(a[j]) for j in range(3))
            if min(ps)>r or max(ps)<-r:return False
    return True

def tri_rect_overlap(lo,hi,z,tri):
    """Does the triangle meet the rectangle [lo,hi] (x,y) on the plane Z=z?"""
    d=[t[2]-z for t in tri]
    if max(d)<0 or min(d)>0:return False
    if max(abs(x) for x in d)<1e-15:
        return all(min(hi[k],max(t[k] for t in tri))-max(lo[k],min(t[k] for t in tri))>=0 for k in (0,1))
    pts=[]
    for i in range(3):
        a,b=tri[i],tri[(i+1)%3];da,db=d[i],d[(i+1)%3]
        if da==0:pts.append((a[0],a[1]))
        if da*db<0:t=da/(da-db);pts.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
    if not pts:return False
    (x0,y0),(x1,y1)=pts[0],pts[-1];t0,t1=0.,1.;dx,dy=x1-x0,y1-y0
    for pp,q in ((-dx,x0-lo[0]),(dx,hi[0]-x0),(-dy,y0-lo[1]),(dy,hi[1]-y0)):
        if pp==0:
            if q<0:return False
        else:
            t=q/pp
            if pp<0:t0=max(t0,t)
            else:t1=min(t1,t)
    return t0<=t1

def cell_measure(lo,hi,solids,excluded,dims,depth=4):
    """Free measure of one cell. lo/hi: 3D bounds (for SLICES lo[2]==hi[2]==z and dims=(0,1)).
    Box-only overlap: exact union. Otherwise adaptive bisection (2^d children per level, up to
    `depth` levels) of sub-cells met by a solid boundary (exact triangle/box SAT test); untouched
    sub-cells are classified exactly by their centre; unresolved leaf sub-cells are classified by
    centre and their whole measure is added to the rigorous error bound.
    Returns dict(free, obstruction, excluded, method, bound, rep)."""
    full=1.
    for d in dims:full*=hi[d]-lo[d]
    centre=tuple((lo[d]+hi[d])/2 for d in range(3))
    zdim=2 not in dims
    def touches(s):
        if zdim and not (s.low[2]<lo[2]<s.high[2] if s.is_box else s.low[2]-s.eps<=lo[2]<=s.high[2]+s.eps):return False
        return _overlap(lo,hi,s.low,s.high,dims)
    S=[s for s in solids if s.closed and touches(s)];E=[s for s in excluded if s.closed and touches(s)]
    if not S and not E:return {'free':full,'obstruction':0.,'excluded':0.,'method':'EXACT','bound':0.,'rep':centre}
    allS=S+E
    inside=lambda p:any(s.contains(p) for s in allS)
    if all(s.is_box for s in allS):
        ue=box_union_measure([(s.low,s.high) for s in E],lo,hi,dims);ua=box_union_measure([(s.low,s.high) for s in allS],lo,hi,dims)
        res={'free':max(0.,full-ua),'obstruction':max(0.,ua-ue),'excluded':ue,'method':'EXACT_BOX_UNION','bound':0.}
    else:
        acc={'E':0.,'S':0.,'bound':0.}
        def boundary_in(slo,shi):
            for s in allS:
                if not all(min(shi[d],s.high[d])-max(slo[d],s.low[d])>=0 for d in dims):continue
                if s.is_box:
                    if not all(s.low[d]<=slo[d] and shi[d]<=s.high[d] for d in dims):return True
                    continue
                for f in s.faces:
                    tri=tuple(s.vertices[i] for i in f)
                    if (tri_rect_overlap(slo,shi,lo[2],tri) if zdim else tri_box_overlap(slo,shi,tri)):return True
            return False
        def visit(slo,shi,level):
            m=1.
            for d in dims:m*=shi[d]-slo[d]
            c=tuple((slo[d]+shi[d])/2 for d in range(3))
            touched=boundary_in(slo,shi)
            if touched and level<depth:
                for idx in product((0,1),repeat=len(dims)):
                    a=list(slo);b=list(shi)
                    for i,d in enumerate(dims):
                        if idx[i]:a[d]=c[d]
                        else:b[d]=c[d]
                    visit(tuple(a),tuple(b),level+1)
                return
            if any(s.contains(c) for s in E):acc['E']+=m
            elif any(s.contains(c) for s in S):acc['S']+=m
            if touched:acc['bound']+=m
        visit(tuple(lo),tuple(hi),0)
        res={'free':max(0.,full-acc['E']-acc['S']),'obstruction':acc['S'],'excluded':acc['E'],'method':'ADAPTIVE_BISECTION_DEPTH_%d' % depth,'bound':acc['bound']}
    if res['free']<=0:res['rep']=None;return res
    if not inside(centre):res['rep']=centre;return res
    best=None
    for kk in (4,8,16):
        for idx in product(range(kk),repeat=len(dims)):
            p=list(centre)
            for i,d in enumerate(dims):p[d]=lo[d]+(idx[i]+.5)*(hi[d]-lo[d])/kk
            p=tuple(p)
            if not inside(p):
                dist=sum((p[d]-centre[d])**2 for d in range(3))
                if best is None or (dist,p)<best:best=(dist,p)
        if best:break
    res['rep']=best[1] if best else None
    return res
