"""Rev F dense-scene broadphase benchmark with an independent oracle (synthetic only).

Dense 3-D lattice of small closed boxes between a synthetic origin and target.
Checks (1) brute-force and broadphase engine outputs are identical and (2) every
sample state equals an independent closed segment/box half-space clipping oracle
(tools/independent_geometry_oracle.py, which does not import the engine).
Geometric demonstration only: no detector response, coverage or speed guarantee.
"""
import json,platform,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fgmapping.domain.scene import Frame,Scene,Component,box_mesh
from fgmapping.engine.inspection import inspect_target,target_samples
from fgmapping.engine.mesh_visibility import MeshIndex
from tools.independent_geometry_oracle import independent_segment_box_intersection
def run():
    H=0.2;boxes=[]
    for ix,x in enumerate((5.,7.,9.,11.,13.,15.)):
     for iy in range(6):
      for iz in range(6):
       y=-3.137+1.093*iy+0.071*ix;z=-2.911+1.057*iz-0.043*ix
       boxes.append(((x-H,y-H,z-H),(x+H,y+H,z+H)))
    components=tuple(Component(f'L{i:03d}','Synthetic dense lattice box','EQUIPMENT','F',box_mesh(lo,hi),'E') for i,(lo,hi) in enumerate(boxes))
    scene=Scene((Frame('F','m','Synthetic dense benchmark'),),components,'SYNTHETIC','0'*64)
    origin=[0.,0.,0.];target={'center_m':[20.,0.,0.],'u':[0.,1.,0.],'v':[0.,0.,1.],'width_m':8.,'height_m':8.,'nx':24,'ny':24}
    oracle={}
    for sid,p,w in target_samples(target):
     oracle[sid]='BLOCKED' if any(independent_segment_box_intersection(origin,p,lo,hi) for lo,hi in boxes) else 'CLEAR'
    runs=[];outputs=[];original=MeshIndex.blocked
    for enabled in (False,True):
     calls=[]
     def spy(index,a,b):calls.append(1);return original(index,a,b)
     start=time.perf_counter()
     with patch.object(MeshIndex,'blocked',spy):result=inspect_target(scene,origin,[c.id for c in components],target,1e-8,broadphase=enabled)
     runs.append({'indexed':enabled,'seconds_including_index_build':round(time.perf_counter()-start,4),'mesh_queries':len(calls)});outputs.append(result)
    engine={s['sample_id']:s['state'] for s in outputs[1]['samples']}
    mismatch=[k for k in oracle if oracle[k]!=engine[k]]
    blocked=sum(1 for v in oracle.values() if v=='BLOCKED')
    checks={'brute_force_equals_broadphase':outputs[0]==outputs[1],'oracle_mismatches':len(mismatch),'indeterminate_samples':sum(1 for v in engine.values() if v=='INDETERMINATE'),'oracle_blocked':blocked,'oracle_clear':len(oracle)-blocked,'non_trivial_mix':0<blocked<len(oracle),'broadphase_reduced_queries':runs[1]['mesh_queries']<runs[0]['mesh_queries']}
    ok=checks['brute_force_equals_broadphase'] and not mismatch and checks['indeterminate_samples']==0 and checks['non_trivial_mix'] and checks['broadphase_reduced_queries']
    record={'qualification':'UNVERIFIED SOFTWARE BENCHMARK ONLY','host':{'platform':sys.platform,'python':sys.version.split()[0],'machine':platform.machine()},'scene':{'obstacles':len(boxes),'rays':len(oracle),'layout':'6x6x6 lattice of 0.4 m closed boxes, x=5..15 m; origin at 0, target plane x=20 m 8x8 m'},'runs':runs,'checks':checks,'first_mismatches':mismatch[:10],'status':'PASS' if ok else 'FAIL','limits':'One synthetic dense lattice; timings are host observations, not a general speed guarantee; geometric intersection only, not detector physics or coverage'}
    return record,ok

if __name__=='__main__':
    record,ok=run()
    out=ROOT/'TEST_RESULTS'/('REV_F_DENSE_BENCHMARK_'+sys.platform+'.json');out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');print(json.dumps(record,indent=2))
    raise SystemExit(0 if ok else 1)
