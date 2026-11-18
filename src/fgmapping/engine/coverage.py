"""CE-03/CE-04/CE-05 geographic coverage engine (Rev G, owner-approved 18 Nov 2026).

Pure Python, deterministic, no Qt. ENGINEER-REVIEWED RESULTS - NOT INDEPENDENTLY
CERTIFIED. Results depend entirely on the detector library data, zones, target
fire / design cloud and geometry supplied by the user.

Flame geographic method FG-FLAME-GEO/1.0
  * The zone AABB is discretised into cells of the user grid spacing (VOLUME) or
    into plan cells at user elevations (SLICES). Boundary cells are clipped to the
    zone and weighted by their actual clipped volume/area.
  * Cells whose centre lies inside an obstructing solid are excluded (fire cannot
    sit inside steel) and reported as excluded volume; cells inside basis-excluded
    components are excluded and reported separately.
  * A target fire is placed with its base at each cell centre: POINT or a
    CYLINDER (diameter, height, rings x levels of sample points + centreline).
  * A detector responds to a target point when (a) it lies in front of the
    detector inside the horizontal and vertical field of view, (b) the distance
    does not exceed the library contour range at that off-axis angle (linear
    interpolation; 0 beyond the table), optionally scaled by sqrt(Q_target /
    Q_rated) when the user selects INVERSE_SQUARE fire-size scaling, and (c) the
    straight line of sight is not blocked by any obstructing mesh (CE-02 MV-1
    segment/triangle test with BVH; indeterminate grazing rays count as blocked).
    The detector responds to the fire when the visible fraction of target points
    is >= the user min_visible_fraction.
  * Votes = number of responding detectors. 0ooN/1ooN/2ooN/3ooN fractions are the
    weighted eligible volume with exactly 0 / at least 1 / 2 / 3 votes divided by
    the eligible volume. Optional grid-refinement convergence check.

Gas geographic method FG-GAS-GEO/1.0  (geographic design-cloud method; NOT dispersion)
  * Design cloud (sphere or ellipsoid, user diameter) centred at each cell centre
    with a user uniform concentration (%LEL).
  * Point detector detects when inside the cloud and cloud %LEL >= its alarm
    threshold. Open-path detector detects when (cloud %LEL/100) x chord length of
    the TX->RX beam through the cloud >= its LEL.m alarm threshold; an obstructed
    beam or a path outside the library min/max length makes it inoperative.
"""
from __future__ import annotations
import math
from fgmapping.domain.pose import direction
from fgmapping.domain.detector_library import contour_range
from fgmapping.engine.mesh_visibility import MeshIndex,segment_triangle
from fgmapping.engine.spatial import ObstacleIndex
from fgmapping.domain.scene import Mesh

METHOD_VERSION={'FLAME_GEOGRAPHIC':'FG-FLAME-GEO/1.0','GAS_GEOGRAPHIC':'FG-GAS-GEO/1.0'}
LABEL='Engineer-reviewed results - not independently certified'

class Cancelled(Exception):pass

def _sub(a,b):return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def _dot(a,b):return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def _norm(a):return math.sqrt(_dot(a,a))
def _unit(a):
    n=_norm(a);return (a[0]/n,a[1]/n,a[2]/n)

def detector_frame(azimuth,elevation,roll):
    """Forward/right/up unit vectors. Roll rotates right/up about forward."""
    f=direction(azimuth,elevation)
    r=_cross(f,(0.,0.,1.))
    if _norm(r)<1e-9:
        a=math.radians(azimuth);r=(math.sin(a),-math.cos(a),0.)
    r=_unit(r);u=_cross(r,f)
    if roll:
        c,s=math.cos(math.radians(roll)),math.sin(math.radians(roll))
        r,u=tuple(r[i]*c+u[i]*s for i in range(3)),tuple(u[i]*c-r[i]*s for i in range(3))
    return f,r,u

def flame_geometry_ok(det,entry,point,scale=1.0):
    """FOV + contour range test (no obstruction). Returns (ok, range_m, off_axis_deg)."""
    d=_sub(point,det['position']);dist=_norm(d)
    if dist<=1e-9:return False,dist,0.
    f,r,u=det['frame'];x=_dot(d,f)
    if x<=0:return False,dist,90.
    h=math.degrees(math.atan2(abs(_dot(d,r)),x));v=math.degrees(math.atan2(abs(_dot(d,u)),x))
    off=math.degrees(math.acos(max(-1.,min(1.,x/dist))))
    fov=entry['fov']
    if h>fov['horizontal_deg']/2+1e-12 or v>fov['vertical_deg']/2+1e-12:return False,dist,off
    return dist<=contour_range(entry,off)*scale+1e-12,dist,off

class Obstructions:
    """Obstructing solids for line of sight. Components declared
    NON_OBSTRUCTING_ANNOTATION, DETECTOR markers and basis-excluded components do not
    obstruct. Undeclared components obstruct (conservative)."""
    def __init__(self,scene,excluded_ids=(),eps=1e-6):
        self.eps=eps;self.indeterminate=0;self.items=[];self.excluded=[];excluded=set(excluded_ids)
        for c in (scene.components if scene else ()):
            frame=scene.frame(c.frame_id);verts=tuple(frame.world(p) for p in c.mesh.vertices)
            lo=tuple(min(p[k] for p in verts) for k in range(3));hi=tuple(max(p[k] for p in verts) for k in range(3))
            if c.id in excluded:self.excluded.append((c.id,lo,hi));continue
            if c.occlusion_role=='NON_OBSTRUCTING_ANNOTATION' or c.semantic=='DETECTOR':continue
            corners={(x,y,z) for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])}
            mesh=Mesh(verts,c.mesh.faces)
            self.items.append({'id':c.id,'low':lo,'high':hi,'mesh':mesh,'index':MeshIndex(mesh,eps),'is_box':len(verts)==8 and set(verts)==corners})
        self.index=ObstacleIndex([(i['low'],i['high']) for i in self.items])
        self.ids=tuple(i['id'] for i in self.items)
    def blocked(self,a,b):
        for k in self.index.candidates(a,b):
            try:
                if self.items[k]['index'].blocked(a,b):return True
            except ValueError:
                self.indeterminate+=1;return True
        return False
    def _inside_item(self,it,p):
        lo,hi=it['low'],it['high']
        if not all(lo[k]<=p[k]<=hi[k] for k in range(3)):return False
        if it['is_box']:return True
        far=(p[0]+1e4*0.5773502691896258+0.0123,p[1]+1e4*0.5773502691896258+0.0371,p[2]+1e4*0.5773502691896258)
        n=0;m=it['mesh']
        for f in m.faces:
            try:
                if segment_triangle(p,far,tuple(m.vertices[i] for i in f),self.eps):n+=1
            except ValueError:return True
        return n%2==1
    def inside(self,p):
        return next((it['id'] for it in self.items if self._inside_item(it,p)),None)
    def inside_excluded(self,p):
        return next((id for id,lo,hi in self.excluded if all(lo[k]<=p[k]<=hi[k] for k in range(3))),None)

def _axis_cells(lo,hi,h):
    out=[];a=lo
    while a<hi-1e-12:
        b=min(a+h,hi);out.append(((a+b)/2,b-a));a=b
    return out

def discretise(low,high,spacing,mode,slices=()):
    """Return [(point, weight)] with weights = clipped cell volume (m3) or area (m2)."""
    xs=_axis_cells(low[0],high[0],spacing);ys=_axis_cells(low[1],high[1],spacing)
    if mode=='VOLUME':
        zs=_axis_cells(low[2],high[2],spacing)
        return [((x,y,z),wx*wy*wz) for z,wz in zs for y,wy in ys for x,wx in xs]
    out=[]
    for z in sorted(slices):
        if not low[2]<=z<=high[2]:raise ValueError('Slice elevation %.3f outside zone' % z)
        out+=[((x,y,float(z)),wx*wy) for y,wy in ys for x,wx in xs]
    return out

def target_points(base,geometry):
    if geometry['type']=='POINT':return [base]
    r=geometry['diameter_m']/2;H=geometry['height_m'];pts=[]
    for k in range(geometry['levels']):
        z=base[2]+H*(k+.5)/geometry['levels'];pts.append((base[0],base[1],z))
        for j in range(geometry['rings']):
            a=2*math.pi*j/geometry['rings'];pts.append((base[0]+r*math.cos(a),base[1]+r*math.sin(a),z))
    return pts

def _prepare_detectors(detectors,entries):
    out=[]
    for d in sorted(detectors,key=lambda d:d['id']):
        e=entries[d['library_id']]
        out.append({**d,'position':tuple(float(v) for v in d['position']),'frame':detector_frame(d['azimuth'],d['elevation'],d.get('roll',0.)),'entry':e})
    return out

def _classify(samples,obs):
    eligible=[];excl={'inside_obstruction':0.,'excluded_component':0.};count={'inside_obstruction':0,'excluded_component':0}
    for p,w in samples:
        if obs.inside_excluded(p):excl['excluded_component']+=w;count['excluded_component']+=1
        elif obs.inside(p):excl['inside_obstruction']+=w;count['inside_obstruction']+=1
        else:eligible.append((p,w))
    return eligible,excl,count

def _fractions(rows,ids):
    tot=math.fsum(w for _,w,_ in rows)
    if tot<=0:return {'0ooN':None,'1ooN':None,'2ooN':None,'3ooN':None},{i:None for i in ids},tot
    fr={'0ooN':math.fsum(w for _,w,v in rows if len(v)==0)/tot}
    for k in (1,2,3):fr[f'{k}ooN']=math.fsum(w for _,w,v in rows if len(v)>=k)/tot
    per={ids[i]:math.fsum(w for _,w,v in rows if i in v)/tot for i in range(len(ids))}
    return fr,per,tot

def _flame_votes(eligible,dets,setup,obs,cancel=None,progress=None,scale_override=1.0):
    f=setup['flame'];geom=f['target_geometry'];need=f['min_visible_fraction'];stand=setup['standoff_m']
    scales=[]
    for d in dets:
        s=1.0
        if f['fire_size_scaling']=='INVERSE_SQUARE':s=math.sqrt(f['heat_release_kw']/d['entry']['target_fire']['heat_release_kw'])
        scales.append(s*scale_override)
    reach=[max(r for _,r in d['entry']['contour'])*s for d,s in zip(dets,scales)]
    extent=0. if geom['type']=='POINT' else math.hypot(geom['diameter_m']/2,geom['height_m'])
    rows=[]
    for n,(p,w) in enumerate(eligible):
        if cancel and cancel():raise Cancelled()
        if progress and n%200==0:progress(n,len(eligible))
        pts=target_points(p,geom);votes=[]
        for i,d in enumerate(dets):
            if _norm(_sub(p,d['position']))>reach[i]+extent+1e-9:continue
            seen=0
            for t in pts:
                ok,dist,_=flame_geometry_ok(d,d['entry'],t,scales[i])
                if not ok:continue
                u=_unit(_sub(t,d['position']));start=tuple(d['position'][k]+u[k]*min(stand,dist/2) for k in range(3))
                if not obs.blocked(start,t):seen+=1
            if seen and seen/len(pts)>=need-1e-12:votes.append(i)
        rows.append((p,w,votes))
    return rows

def _ellipsoid_semi(cloud):
    if cloud['shape']=='SPHERE':r=cloud['diameter_m']/2;return (r,r,r)
    return tuple(a/2 for a in cloud['axes_m'])

def chord_length(a,b,centre,semi):
    """Length of segment a->b inside the axis-aligned ellipsoid (exact)."""
    q0=tuple((a[k]-centre[k])/semi[k] for k in range(3));q1=tuple((b[k]-centre[k])/semi[k] for k in range(3))
    d=_sub(q1,q0);A=_dot(d,d);B=2*_dot(q0,d);C=_dot(q0,q0)-1
    if A==0:return 0.
    disc=B*B-4*A*C
    if disc<=0:return 0.
    s=math.sqrt(disc);t1=max(0.,(-B-s)/(2*A));t2=min(1.,(-B+s)/(2*A))
    return max(0.,t2-t1)*_norm(_sub(b,a))

def _gas_votes(eligible,dets,setup,obs,cancel=None,progress=None,findings=None):
    g=setup['gas'];semi=_ellipsoid_semi(g['cloud']);conc=g['cloud_concentration_pct_lel']
    active=[]
    for i,d in enumerate(dets):
        e=d['entry']
        if e['detector_type']=='POINT_GAS':
            if conc<e['alarm_threshold']['value']:findings.append({'severity':'REVIEW','detector':d['id'],'text':'Design cloud concentration below point detector alarm threshold; detector cannot alarm in this method'})
            active.append(i)
        else:
            rx=d['receiver'];L=_norm(_sub(rx,d['position']))
            if not e['path_length_m']['min']<=L<=e['path_length_m']['max']:
                findings.append({'severity':'BLOCKING','detector':d['id'],'text':'Beam length %.2f m outside library path range; detector treated inoperative' % L});continue
            u=_unit(_sub(rx,d['position']));st=setup['standoff_m']
            if obs.blocked(tuple(d['position'][k]+u[k]*st for k in range(3)),tuple(rx[k]-u[k]*st for k in range(3))):
                findings.append({'severity':'BLOCKING','detector':d['id'],'text':'Open-path beam obstructed by geometry; detector treated inoperative'});continue
            active.append(i)
    rows=[]
    for n,(c,w) in enumerate(eligible):
        if cancel and cancel():raise Cancelled()
        if progress and n%500==0:progress(n,len(eligible))
        votes=[]
        for i in active:
            d=dets[i];e=d['entry'];p=d['position']
            if e['detector_type']=='POINT_GAS':
                if conc>=e['alarm_threshold']['value'] and sum(((p[k]-c[k])/semi[k])**2 for k in range(3))<=1+1e-12:votes.append(i)
            else:
                if conc/100.*chord_length(p,d['receiver'],c,semi)>=e['alarm_threshold']['value']-1e-12:votes.append(i)
        rows.append((c,w,votes))
    return rows

def zone_coverage(zone,setup,detectors,entries,obs,cancel=None,progress=None,sensitivity=False):
    """Compute one zone. detectors: [{id,detector_type,position,azimuth,elevation,roll,library_id,receiver?}]."""
    method=setup['method'];findings=[]
    dets=_prepare_detectors(detectors,entries);ids=[d['id'] for d in dets]
    for d in dets:
        inside=obs.inside(d['position'])
        if inside:findings.append({'severity':'REVIEW','detector':d['id'],'text':'Detector position lies inside obstruction '+inside+'; check mounting standoff'})
    unit='m3' if setup['mode']=='VOLUME' else 'm2'
    def run(spacing,with_progress=True):
        samples=discretise(zone['low'],zone['high'],spacing,setup['mode'],setup['slice_elevations_m'])
        eligible,excl,count=_classify(samples,obs)
        if method=='FLAME_GEOGRAPHIC':rows=_flame_votes(eligible,dets,setup,obs,cancel,progress if with_progress else None)
        else:rows=_gas_votes(eligible,dets,setup,obs,cancel,progress if with_progress else None,findings if with_progress else [])
        return samples,rows,excl,count
    obs.indeterminate=0
    samples,rows,excl,count=run(setup['grid_spacing_m'])
    fr,per,tot=_fractions(rows,ids)
    req=setup['voting_required'];targets={}
    for k in ('1ooN','2ooN','3ooN'):
        t=setup['performance_targets'].get(k,'NOT SUPPLIED')
        if t=='NOT SUPPLIED':targets[k]={'target':'NOT SUPPLIED','achieved':fr[k],'status':'NO USER TARGET'}
        else:targets[k]={'target':t,'achieved':fr[k],'status':'NO ELIGIBLE VOLUME' if fr[k] is None else 'MEETS USER TARGET' if fr[k]>=float(t)-1e-12 else 'BELOW USER TARGET'}
    result={'zone_id':zone['id'],'zone_kind':zone['kind'],'method':method,'method_version':METHOD_VERSION[method],'label':LABEL,'mode':setup['mode'],'grid_spacing_m':setup['grid_spacing_m'],
            'measure_unit':unit,'zone_measure':math.fsum(w for _,w in samples),'eligible_measure':tot,'excluded_measure':excl,'excluded_samples':count,
            'sample_count':len(samples),'eligible_samples':len(rows),'detectors_considered':ids,'voting_required':req,'fractions':fr,'required_voting_fraction':fr[f'{req}ooN'],
            'performance_targets':targets,'per_detector_fraction':per,'indeterminate_rays':obs.indeterminate,'findings':findings}
    if setup['mode']=='SLICES':
        result['slices']={}
        for z in sorted(setup['slice_elevations_m']):
            sub=[r for r in rows if abs(r[0][2]-z)<1e-9];result['slices'][repr(float(z))]=_fractions(sub,ids)[0]
    ref=setup['convergence']['refinement']
    if ref>1:
        _,rows2,_,_=run(setup['grid_spacing_m']/ref,False);fr2,_,_=_fractions(rows2,ids)
        delta={k:(None if fr[k] is None or fr2[k] is None else abs(fr2[k]-fr[k])) for k in fr}
        worst=max((v for v in delta.values() if v is not None),default=0.)
        result['convergence']={'refined_spacing_m':setup['grid_spacing_m']/ref,'refined_fractions':fr2,'abs_delta':delta,'tolerance':setup['convergence']['tolerance'],
                               'status':'CONVERGED' if worst<=float(setup['convergence']['tolerance'])+1e-12 else 'NOT CONVERGED - refine grid'}
    else:result['convergence']={'status':'NOT CHECKED (refinement 1)'}
    if sensitivity and method=='FLAME_GEOGRAPHIC':
        sens={}
        for factor in (0.9,1.1):
            r2=_flame_votes([(p,w) for p,w,_ in rows],dets,setup,obs,cancel,None,factor);sens[repr(factor)]=_fractions(r2,ids)[0]
        result['sensitivity_range_factor']=sens
    samples_out={'detector_ids':ids,'rows':[[round(p[0],6),round(p[1],6),round(p[2],6),w,v] for p,w,v in rows]}
    return result,samples_out
