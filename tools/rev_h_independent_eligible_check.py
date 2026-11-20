"""Rev H independent check of stored eligible (free) volumes for the wellhead example.

Does NOT import fgmapping. Reads each stored coverage_run's zone, excluded ids and the
run's own scene snapshot, and computes
  free = |zone| - |zone ∩ (union of obstructing boxes ∪ excluded boxes)|
exactly with Fractions by a separate slab-sweep implementation (x slabs, then y
interval union per z-slab), plus a seeded Monte Carlo sanity estimate.
Only valid for scenes made of axis-aligned boxes (asserted). Synthetic example only.
"""
import sqlite3,json,sys,random
from fractions import Fraction as F
def boxes_of(snap,excluded):
    out=[]
    for c in snap['components']:
        if c['id'] not in excluded and (c['occlusion_role']=='NON_OBSTRUCTING_ANNOTATION' or c['semantic']=='DETECTOR'):continue
        v=c['mesh']['vertices'];xs=sorted({p[0] for p in v});ys=sorted({p[1] for p in v});zs=sorted({p[2] for p in v})
        assert len(v)==8 and len(xs)==len(ys)==len(zs)==2,'non-box component '+c['id']
        out.append(tuple(F(str(a)) for a in (xs[0],ys[0],zs[0],xs[1],ys[1],zs[1])))
    return out
def clip(b,lo,hi):
    c=(max(b[0],lo[0]),max(b[1],lo[1]),max(b[2],lo[2]),min(b[3],hi[0]),min(b[4],hi[1]),min(b[5],hi[2]))
    return c if c[0]<c[3] and c[1]<c[4] and c[2]<c[5] else None
def union_len(iv):
    tot=F(0);cur=None
    for a,b in sorted(iv):
        if cur is None or a>cur[1]:
            if cur:tot+=cur[1]-cur[0]
            cur=[a,b]
        else:cur[1]=max(cur[1],b)
    return tot+(cur[1]-cur[0] if cur else 0)
def union_volume(bs):
    xs=sorted({b[0] for b in bs}|{b[3] for b in bs});vol=F(0)
    for x0,x1 in zip(xs,xs[1:]):
        act=[b for b in bs if b[0]<=x0 and b[3]>=x1]
        zs=sorted({b[2] for b in act}|{b[5] for b in act});area=F(0)
        for z0,z1 in zip(zs,zs[1:]):
            area+=(z1-z0)*union_len([(b[1],b[4]) for b in act if b[2]<=z0 and b[5]>=z1])
        vol+=(x1-x0)*area
    return vol
def main(case,mc=200000):
    con=sqlite3.connect(case);rows=[]
    for rid,zone_id,inp,res,smp in con.execute("select id,zone_id,input_json,result_json,samples_json from coverage_run where kind in ('FIRE_ZONE','GAS_ZONE') order by id"):
        inp=json.loads(inp);res=json.loads(res);snap=json.loads(smp)['scene_snapshot'];z=inp['zone']
        if inp['setup'].get('mode','VOLUME')!='VOLUME' and res.get('measure_unit','m3')!='m3':continue
        lo=[F(str(a)) for a in z['low']];hi=[F(str(a)) for a in z['high']]
        bs=[c for c in (clip(b,lo,hi) for b in boxes_of(snap,set(inp['excluded_component_ids']))) if c]
        zv=(hi[0]-lo[0])*(hi[1]-lo[1])*(hi[2]-lo[2]);free=zv-union_volume(bs)
        rnd=random.Random(20261120);fb=[tuple(float(t) for t in b) for b in bs];hit=0
        for _ in range(mc):
            p=[rnd.uniform(float(lo[i]),float(hi[i])) for i in range(3)]
            hit+=any(b[0]<=p[0]<=b[3] and b[1]<=p[1]<=b[4] and b[2]<=p[2]<=b[5] for b in fb)
        stored=res['eligible_measure'];rows.append({'run':rid,'zone':zone_id,'zone_volume':float(zv),'independent_free_exact':float(free),'stored_eligible':stored,'abs_diff':abs(stored-float(free)),'stored_bound':res.get('measure_error_bound'),'monte_carlo_free':float(zv)*(1-hit/mc),'mc_samples':mc})
    return rows
if __name__=='__main__':
    r=main(sys.argv[1],int(sys.argv[2]) if len(sys.argv)>2 else 200000);print(json.dumps(r,indent=1))
    sys.exit(0 if all(x['abs_diff']<=1e-6*max(1,x['zone_volume']) for x in r) else 1)
