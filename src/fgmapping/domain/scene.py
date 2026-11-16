"""WP02 candidate coordinate/mesh contract v1. SI output, explicit source frame.

Numerical domain: abs(coordinates) <= 1e7 m, scale in [1e-9,1e9].
These are development resource/numerical bounds, not engineering criteria.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import Counter
import hashlib
import json
import math

IDENTITY = ((1.,0.,0.,0.), (0.,1.,0.,0.), (0.,0.,1.,0.), (0.,0.,0.,1.))
UNITS = {'m':1., 'mm':.001, 'cm':.01, 'ft':.3048}

def vector(v):
    if len(v) != 3 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or abs(x)>1e7 for x in v):
        raise ValueError('Expected three finite coordinates within development bounds')
    return tuple(float(x) for x in v)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)

def content_hash(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

@dataclass(frozen=True)
class Frame:
    id: str
    units: str
    datum: str
    handedness: str = 'RIGHT'
    matrix: tuple = IDENTITY

    def __post_init__(self):
        if not self.id.strip() or not self.datum.strip() or self.units not in UNITS:
            raise ValueError('Explicit frame ID, units and datum required')
        if self.handedness != 'RIGHT':
            raise ValueError('Left-handed frames require an explicit reviewed conversion; not supported')
        m=tuple(tuple(float(x) for x in row) for row in self.matrix)
        if len(m)!=4 or any(len(r)!=4 for r in m) or any(not math.isfinite(x) for r in m for x in r):
            raise ValueError('Finite 4x4 transform required')
        if m[3] != (0.,0.,0.,1.): raise ValueError('Affine transform required')
        cols=[tuple(m[i][j] for i in range(3)) for j in range(3)]
        lengths=[math.sqrt(sum(x*x for x in c)) for c in cols]
        if any(not 1e-9<=s<=1e9 for s in lengths): raise ValueError('Singular/extreme transform')
        for i in range(3):
            for j in range(i):
                if abs(sum(cols[i][k]*cols[j][k] for k in range(3)))>1e-10*lengths[i]*lengths[j]:
                    raise ValueError('Shear is unsupported')
        a,b,c=cols
        det=a[0]*(b[1]*c[2]-b[2]*c[1])-b[0]*(a[1]*c[2]-a[2]*c[1])+c[0]*(a[1]*b[2]-a[2]*b[1])
        if det<=0: raise ValueError('Mirrored/left-handed transform refused')
        object.__setattr__(self,'matrix',m)
        vector(tuple(m[i][3] for i in range(3)))

    def world(self,p):
        p=vector(p); scale=UNITS[self.units]; m=self.matrix
        return vector(tuple(sum(m[i][j]*p[j]*scale for j in range(3))+m[i][3] for i in range(3)))

    def local(self,p):
        p=vector(p); m=self.matrix
        # Inverse of orthogonal (possibly nonuniformly scaled) columns.
        return vector(tuple(sum(m[i][j]*(p[i]-m[i][3]) for i in range(3))/sum(m[i][j]**2 for i in range(3))/UNITS[self.units] for j in range(3)))

@dataclass(frozen=True)
class Mesh:
    vertices: tuple
    faces: tuple

    def __post_init__(self):
        if not 3<=len(self.vertices)<=100000 or not 1<=len(self.faces)<=200000:
            raise ValueError('Mesh exceeds development vertex/face budget or is empty')
        verts=tuple(vector(v) for v in self.vertices)
        faces=tuple(tuple(f) for f in self.faces)
        for f in faces:
            if len(f)!=3 or any(type(i) is not int or not 0<=i<len(verts) for i in f) or len(set(f))!=3:
                raise ValueError('Invalid triangle indices')
            a,b,c=(verts[i] for i in f)
            u=tuple(b[i]-a[i] for i in range(3)); v=tuple(c[i]-a[i] for i in range(3))
            cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            if sum(x*x for x in cross)<=1e-24: raise ValueError('Zero/near-zero area triangle')
        object.__setattr__(self,'vertices',verts); object.__setattr__(self,'faces',faces)

    def diagnostics(self):
        edges=Counter(); directions=Counter(); faces=Counter()
        for a,b,c in self.faces:
            faces[tuple(sorted((a,b,c)))]+=1
            for x,y in ((a,b),(b,c),(c,a)):
                edges[tuple(sorted((x,y)))]+=1; directions[x,y]+=1
        return {'boundary_edges':sum(n==1 for n in edges.values()),
                'nonmanifold_edges':sum(n>2 for n in edges.values()),
                'duplicate_faces':sum(n-1 for n in faces.values()),
                'inconsistent_winding_edges':sum(n==2 and (directions[a,b]==2 or directions[b,a]==2) for (a,b),n in edges.items()),
                'self_intersection':'NOT EVALUATED', 'qualification':'UNVERIFIED'}

    @property
    def sha256(self): return content_hash(asdict(self))

@dataclass(frozen=True)
class Component:
    id: str
    label: str
    semantic: str
    frame_id: str
    mesh: Mesh
    evidence_id: str
    parent_id: str|None = None
    occlusion_role: str = 'NOT SUPPLIED'

@dataclass(frozen=True)
class Scene:
    frames: tuple[Frame,...]
    components: tuple[Component,...]
    source_revision: str
    source_sha256: str
    data_class: str = 'SYNTHETIC'

    def __post_init__(self):
        if self.data_class!='SYNTHETIC': raise ValueError('Candidate workspace accepts synthetic data only')
        ids=[x.id for x in self.components]; fids=[f.id for f in self.frames]
        if len(ids)!=len(set(ids)) or len(fids)!=len(set(fids)): raise ValueError('Duplicate persistent ID')
        if not self.source_revision.strip() or len(self.source_sha256)!=64 or any(c not in '0123456789abcdef' for c in self.source_sha256):
            raise ValueError('Source revision and SHA256 required')
        byid={c.id:c for c in self.components}
        for c in self.components:
            if not c.id.strip() or not c.evidence_id.strip() or c.frame_id not in fids or c.parent_id is not None and c.parent_id not in byid:
                raise ValueError('Missing identity, evidence, frame or parent')
            seen={c.id}; parent=c.parent_id
            while parent is not None:
                if parent in seen: raise ValueError('Component hierarchy cycle')
                seen.add(parent); parent=byid[parent].parent_id
            for p in c.mesh.vertices: self.frame(c.frame_id).world(p)

    def frame(self,id): return next(f for f in self.frames if f.id==id)
    def to_dict(self): return asdict(self)
    @property
    def sha256(self): return content_hash(self.to_dict())
    @classmethod
    def from_dict(cls,d):
        return cls(tuple(Frame(**f) for f in d['frames']),tuple(Component(**{**c,'mesh':Mesh(**c['mesh'])}) for c in d['components']),d['source_revision'],d['source_sha256'],d['data_class'])

def box_mesh(low,high):
    lo=vector(low); hi=vector(high)
    if any(a>=b for a,b in zip(lo,hi)): raise ValueError('Ordered bounds required')
    x,y,z=lo; X,Y,Z=hi
    return Mesh(((x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)),
                ((0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)))

def synthetic_scene():
    specs=[('DECK','Deck','DECK',(-1,-1,-.4),(21,13,0)),
           ('V101','Vessel 101 envelope','EQUIPMENT',(3,3,0),(6,6,5)),
           ('V102','Vessel 102 envelope','EQUIPMENT',(12,6,0),(16,10,4)),
           ('WALL','Module wall','WALL',(9,0,0),(9.3,8,6)),
           ('PIPE','Pipe envelope','PIPE',(1,10,2),(19,10.4,2.4)),
           ('FD101','Detector position 101','DETECTOR',(0,0,3),(0.4,.4,3.4)),
           ('FD102','Detector position 102','DETECTOR',(19,11,4),(19.4,11.4,4.4))]
    for i in range(6): specs.append((f'GRATE{i}',f'Grating strip {i}','GRATING',(i*1.2,11,.1),(i*1.2+.2,12,.2)))
    comps=tuple(Component(id,label,kind,'LOCAL',box_mesh(lo,hi),'SYN-GEOM-01') for id,label,kind,lo,hi in specs)
    return Scene((Frame('LOCAL','m','SYNTHETIC local origin; X east, Y north, Z up'),),comps,'SYN-A',content_hash(specs))
