"""Finite rectangular-target surface obstruction diagnostic; NOT flame coverage.

Conservative bounds retain indeterminate rays in the denominator. Endpoint
containment in a closed candidate mesh's AABB is flagged indeterminate when no
surface crossing is found; this is not a general point-in-solid classifier.
"""
import math
from fgmapping.domain.scene import vector,content_hash
from fgmapping.engine.mesh_visibility import MeshIndex,tolerance

def target_samples(target):
 if set(target)!={'center_m','u','v','width_m','height_m','nx','ny'}:raise ValueError('Closed explicit rectangle target definition required')
 center=vector(target['center_m']);u=vector(target['u']);v=vector(target['v'])
 if abs(sum(x*x for x in u)-1)>1e-10 or abs(sum(x*x for x in v)-1)>1e-10 or abs(sum(x*y for x,y in zip(u,v)))>1e-10:raise ValueError('Explicit orthonormal rectangle axes required')
 w,h=target['width_m'],target['height_m'];nx,ny=target['nx'],target['ny']
 if type(w) not in (int,float) or type(h) not in (int,float) or not math.isfinite(w) or not math.isfinite(h) or min(w,h)<=0:raise ValueError('Positive finite target dimensions required')
 if type(nx) is not int or type(ny) is not int or min(nx,ny)<1 or nx*ny>4096:raise ValueError('Explicit sampling counts, at most 4096 cells required')
 area=w*h/(nx*ny)
 if not math.isfinite(area) or area<=0:raise ValueError('Invalid numerical sample area')
 samples=[]
 for j in range(ny):
  for i in range(nx):
   a=((i+.5)/nx-.5)*w;b=((j+.5)/ny-.5)*h
   samples.append((f'T-{j:03d}-{i:03d}',vector(tuple(center[k]+a*u[k]+b*v[k] for k in range(3))),area))
 return samples

def inspect_target(scene,origin,obstacle_ids,target,tolerance_m,*,broadphase=True):
 tolerance(tolerance_m)
 origin=vector(origin);ids=tuple(sorted(obstacle_ids))
 if len(ids)!=len(set(ids)):raise ValueError('Duplicate obstacle selection')
 byid={c.id:c for c in scene.components};indexes=[]
 for id in ids:
  if id not in byid:raise ValueError('Selected obstruction component missing')
  c=byid[id]
  if c.semantic=='DETECTOR':raise ValueError('Detector display markers cannot be selected as engineering obstructions')
  f=scene.frame(c.frame_id)
  from fgmapping.domain.scene import Mesh
  mesh=Mesh(tuple(f.world(p) for p in c.mesh.vertices),c.mesh.faces);index=MeshIndex(mesh,tolerance_m)
  low=tuple(min(p[k] for p in mesh.vertices) for k in range(3));high=tuple(max(p[k] for p in mesh.vertices) for k in range(3));d=mesh.diagnostics()
  closed=d['boundary_edges']==0 and d['nonmanifold_edges']==0
  indexes.append((id,index,low,high,closed))
 from fgmapping.engine.spatial import ObstacleIndex
 spatial=ObstacleIndex([(tuple(x-tolerance_m for x in low),tuple(x+tolerance_m for x in high)) for name,index,low,high,closed in indexes]) if broadphase else None
 samples=target_samples(target);results=[];areas={'CLEAR':[],'BLOCKED':[],'INDETERMINATE':[]}
 for id,p,weight in samples:
  blockers=[];uncertain=['ZERO_LENGTH_OR_SUB_TOLERANCE_RAY'] if math.dist(origin,p)<=tolerance_m else []
  candidates=spatial.candidates(origin,p) if spatial is not None else range(len(indexes))
  for candidate in candidates:
   name,index,low,high,closed=indexes[candidate]
   try:
    hit=index.blocked(origin,p)
    if hit:blockers.append(name)
    elif closed and any(all(a<=x<=b for a,x,b in zip(low,q,high)) for q in (origin,p)):uncertain.append(name+': endpoint containment not resolved')
   except ValueError as exc:
    if 'Coplanar' not in str(exc):raise
    uncertain.append(name+': coplanar surface contact')
  state='BLOCKED' if blockers else 'INDETERMINATE' if uncertain else 'CLEAR'
  areas[state].append(weight);results.append({'sample_id':id,'position_m':p,'area_m2':weight,'state':state,'blockers':blockers,'uncertainty':uncertain})
 total=math.fsum(weight for id,p,weight in samples);sums={k:math.fsum(v) for k,v in areas.items()}
 return {'method':'GEOMETRIC_TARGET_INSPECTION/1','label':'GEOMETRIC DEMONSTRATION / NOT DETECTOR COVERAGE','qualification':'UNVERIFIED','scene_hash':scene.sha256,'origin_m':origin,'obstacle_ids':ids,'tolerance_m':tolerance_m,'target_area_m2':total,'clear_area_m2':sums['CLEAR'],'blocked_area_m2':sums['BLOCKED'],'indeterminate_area_m2':sums['INDETERMINATE'],'visibility_fraction':None if sums['INDETERMINATE'] else sums['CLEAR']/total,'visibility_lower_bound':sums['CLEAR']/total,'visibility_upper_bound':(sums['CLEAR']+sums['INDETERMINATE'])/total,'samples':results,'limitations':['Surface intersections only; no detector response/radiation/attenuation','Closed-AABB endpoint ambiguity is conservatively retained','Self-intersections/material roles are not qualified']}
