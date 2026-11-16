"""Independent constructive half-target benchmark at multiple sample resolutions."""
import json,time
from fgmapping.domain.scene import Mesh
from fgmapping.engine.mesh_visibility import MeshIndex,finite_target_visible_fraction
mesh=Mesh(((2,0,-10),(2,10,-10),(2,10,10),(2,0,10)),((0,1,2),(0,2,3)))
rows=[]
for n in (4,8,16,32):
    samples=[((4,-1+(i+.5)*2/n,-1+(j+.5)*2/n),4/(n*n)) for i in range(n) for j in range(n)]
    start=time.perf_counter();fraction=finite_target_visible_fraction((0,0,0),samples,[MeshIndex(mesh,1e-9)])
    assert fraction==.5
    rows.append({'n_per_axis':n,'samples':n*n,'visible_fraction':fraction,'constructive_exact_area_fraction':.5,'absolute_error':abs(fraction-.5),'seconds':time.perf_counter()-start})
print(json.dumps({'method':'MV-1 SYNTHETIC geometry only','qualification':'UNVERIFIED','benchmark':'Opaque planar wall covers positive-Y half of square target at x=4; rays cross plane x=2','tolerance_m':1e-9,'results':rows},indent=2))
