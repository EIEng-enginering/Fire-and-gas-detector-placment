"""Pre-registered constructive target and source-frame benchmarks, no physics."""
import json,time,math
from fgmapping.domain.scene import Frame,Scene,Component,Mesh,box_mesh
from fgmapping.domain.mounting import mount_pose
from fgmapping.engine.inspection import inspect_target
mesh=Mesh(((2,0,-10),(2,10,-10),(2,10,10),(2,0,10)),((0,1,2),(0,2,3)))
scene=Scene((Frame('F','m','SYNTHETIC'),),(Component('W','Synthetic half-target wall','WALL','F',mesh,'SYN-E'),),'A','0'*64)
rows=[]
for n in (4,8,16,32):
 t={'center_m':[4,0,0],'u':[0,1,0],'v':[0,0,1],'width_m':2,'height_m':2,'nx':n,'ny':n};start=time.perf_counter();r=inspect_target(scene,(0,0,0),['W'],t,1e-9)
 assert r['visibility_fraction']==.5 and r['indeterminate_area_m2']==0
 rows.append({'samples':n*n,'area_m2':r['target_area_m2'],'geometric_fraction':r['visibility_fraction'],'independent_constructive_half_area_fraction':.5,'absolute_error':0,'seconds':time.perf_counter()-start})
f=Frame('ROT','mm','SYNTHETIC',matrix=((0,-2,0,10),(3,0,0,20),(0,0,4,30),(0,0,0,1)));component=Component('CAD','Synthetic source box','EQUIPMENT','ROT',box_mesh((0,0,0),(4000,4000,4000)),'SYN-E');s=Scene((f,),(component,),'A','0'*64)
p=mount_pose(s,'CAD',(1000,2000,3000),(1,2,3),(0,0,0));assert p['position']==(4,24,45)
print(json.dumps({'label':'GEOMETRIC AND COORDINATE SOFTWARE VERIFICATION ONLY','qualification':'UNVERIFIED','target_benchmarks':rows,'mount_known_answer':{'actual_position_m':p['position'],'independent_constructive_expected_m':[4,24,45],'source_anchor_mm':[1000,2000,3000],'physical_offset_m':[1,2,3]}},indent=2))
