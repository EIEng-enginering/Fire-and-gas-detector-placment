"""CE-03/CE-04/CE-05 geographic coverage engine (Rev H, repairs of review findings F01-F07).

Pure Python, deterministic, no Qt. COMPUTED - UNREVIEWED RESULTS - NOT INDEPENDENTLY
VERIFIED. Results depend entirely on the detector library data, zones, target
fire / design cloud and geometry supplied by the user. Full method and tolerances:
docs/METHOD_AND_TOLERANCES_REV_H.md.

Flame geographic method FG-FLAME-GEO/1.1
  * The zone AABB is discretised into cells of the user grid spacing (VOLUME) or into
    plan cells at user elevations (SLICES); boundary cells are clipped to the zone and
    their clipped bounds are stored (F20).
  * Each cell contributes its FREE measure = cell measure - |cell n (solids u exclusions)|:
    exact for axis-aligned box solids (union, no double counting), adaptive bisection with
    a rigorous error bound for other closed meshes (F01). Solid membership uses exact box
    tests or the generalised winding number of a topologically closed mesh (F02); basis
    exclusions use the real mesh, not its AABB (F03). Open meshes exclude no volume.
  * Detection is evaluated at ONE representative free point per cell (centre when free,
    else the nearest free sub-sample): a sampled-cell fraction (F14).
  * A detector responds to a target point when (a) it lies inside the rectangular FOV of the
    detector's local frame = columns of domain.mounting.rotation(az, el, roll) (F04), (b) the
    distance does not exceed the contour range at the off-axis angle (linear interpolation;
    0 beyond the table), optionally scaled by sqrt(Q_target/Q_rated) under explicit
    INVERSE_SQUARE scaling, and (c) the straight sight line FROM THE DETECTOR is not blocked;
    only the detector's own declared mount component is ignored within the standoff radius
    (F05). Indeterminate (coplanar/grazing within eps) rays count as blocked; the scene
    broadphase is inflated by eps so it agrees with the mesh test (F06).
  * Votes = number of responding detectors; 0ooN is exactly 0 votes, kooN is >= k votes.
  * Optional two-grid check reported as GRID AGREEMENT / DISAGREEMENT / UNRESOLVED FEATURE /
    NOT EVALUABLE - never as convergence or an error bound (F07).

Gas geographic method FG-GAS-GEO/1.1  (geographic design-cloud method; NOT dispersion)
  * Design cloud (sphere or ellipsoid) centred at each cell's representative point with a
    user uniform concentration (%LEL).
  * Point detector detects when inside the cloud and cloud %LEL >= its alarm threshold.
    Open-path detector detects when (cloud %LEL/100) x chord length of the TX->RX beam
    through the cloud >= its LEL.m alarm threshold; an obstructed beam (TX/RX own mounts
    ignored only within the standoff), a beam not longer than twice the standoff, or a path
    outside the library min/max length makes it inoperative.
"""
from __future__ import annotations
import math
from fgmapping.domain.pose import direction
from fgmapping.domain.mounting import rotation
from fgmapping.engine.solid_geometry import Solid,cell_measure
from fgmapping.domain.detector_library import contour_range
from fgmapping.engine.mesh_visibility import MeshIndex,segment_triangle
from fgmapping.engine.spatial import ObstacleIndex
from fgmapping.domain.scene import Mesh

METHOD_VERSION={'FLAME_GEOGRAPHIC':'FG-FLAME-GEO/1.1','GAS_GEOGRAPHIC':'FG-GAS-GEO/1.1'}  # Rev H: partial-cell measure, membership, orientation, LOS standoff, grid check
LABEL='COMPUTED - UNREVIEWED development results - not independently verified'

class Cancelled(Exception):pass

def _sub(a,b):return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def _dot(a,b):return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def _norm(a):return math.sqrt(_dot(a,a))
def _unit(a):
    n=_norm(a);return (a[0]/n,a[1]/n,a[2]/n)

def detector_frame(azimuth,elevation,roll):
    """(forward, left, up) unit vectors = the columns of domain.mounting.rotation(az, el, roll).
    Rev H (F04): single right-handed convention shared with mounting, the viewer FOV overlay and
    layout options: local X = boresight, local Y = left, local Z = up; roll is a right-handed
    rotation about the boresight. Horizontal FOV angle is measured in the local X-Y plane and
    vertical FOV angle in the local X-Z plane."""
    R=rotation(float(azimuth),float(elevation),float(roll or 0.))
    return tuple(tuple(R[i][j] for i in range(3)) for j in range(3))

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

def fov_outline(position,frame,entry,scale=1.0,per_side=8):
    """Rev H (F19): boundary of the engine's own flame acceptance region (rectangular FOV in
    the local frame + contour range at the true off-axis angle, 0 beyond the last table angle;
    no clamping). Returns world points around the FOV rectangle perimeter at the contour range.
    Every returned point satisfies flame_geometry_ok at (1 - 1e-9) of its range."""
    H=math.radians(entry['fov']['horizontal_deg']/2);V=math.radians(entry['fov']['vertical_deg']/2)
    f,l,u=frame;corners=[(H,V),(-H,V),(-H,-V),(H,-V)];pts=[]
    for (h0,v0),(h1,v1) in zip(corners,corners[1:]+corners[:1]):
        for k in range(per_side):
            t=k/per_side;h=h0+(h1-h0)*t;v=v0+(v1-v0)*t
            th=math.tan(min(abs(h),math.radians(89.9)))*(1 if h>=0 else -1);tv=math.tan(min(abs(v),math.radians(89.9)))*(1 if v>=0 else -1)
            d=_unit(tuple(f[i]+th*l[i]+tv*u[i] for i in range(3)))
            off=math.degrees(math.acos(max(-1.,min(1.,_dot(d,f)))))
            r=contour_range(entry,off)*scale
            pts.append(tuple(position[i]+d[i]*r for i in range(3)))
    return pts

class Obstructions:
    """Obstructing solids for line of sight and volume exclusion. Components declared
    NON_OBSTRUCTING_ANNOTATION, DETECTOR markers and basis-excluded components do not
    obstruct. Undeclared components obstruct (conservative).
    Rev H: broadphase bounds are inflated by eps so the scene test agrees with the
    eps-tolerant mesh test (F06); membership uses engine.solid_geometry (F02/F03);
    open (non-closed) meshes obstruct sight but exclude no volume (reported)."""
    def __init__(self,scene,excluded_ids=(),eps=1e-6):
        self.eps=eps;self.indeterminate=0;self.items=[];self.excluded=[];self.solids=[];self.excluded_solids=[];self.findings=[];excluded=set(excluded_ids)
        for c in (scene.components if scene else ()):
            frame=scene.frame(c.frame_id);verts=tuple(frame.world(p) for p in c.mesh.vertices)
            solid=Solid(c.id,verts,c.mesh.faces,eps)
            if c.id in excluded:
                self.excluded.append((c.id,solid.low,solid.high));self.excluded_solids.append(solid)
                if not solid.closed:self.findings.append({'severity':'BLOCKING','component':c.id,'text':'Basis-excluded component mesh is not closed (%s); it cannot define an excluded volume' % {k:v for k,v in solid.topology.items() if k!='closed'}})
                continue
            if c.occlusion_role=='NON_OBSTRUCTING_ANNOTATION' or c.semantic=='DETECTOR':continue
            if not solid.closed:self.findings.append({'severity':'REVIEW','component':c.id,'text':'Obstruction mesh is not closed (%s); it obstructs line of sight as a surface but excludes no volume' % {k:v for k,v in solid.topology.items() if k!='closed'}})
            mesh=Mesh(verts,c.mesh.faces)
            self.items.append({'id':c.id,'low':solid.low,'high':solid.high,'mesh':mesh,'index':MeshIndex(mesh,eps),'is_box':solid.is_box,'solid':solid});self.solids.append(solid)
        e=eps
        self.index=ObstacleIndex([(tuple(v-e for v in i['low']),tuple(v+e for v in i['high'])) for i in self.items])
        self.ids=tuple(i['id'] for i in self.items)
    def blocked(self,a,b,ignore=None):
        """True when segment a->b meets an obstruction. ignore=[(component_id, radius, at_start)]
        ignores hits on that one component (a detector/receiver's own mount) only within radius
        of the start (at_start) or end of the segment."""
        L=_norm(_sub(b,a))
        for k in self.index.candidates(a,b):
            it=self.items[k];t0,t1=0.,L
            for cid,radius,at_start in (ignore or ()):
                if cid==it['id'] and radius>0:
                    if at_start:t0=max(t0,radius)
                    else:t1=min(t1,L-radius)
            if t1<=t0:continue
            if t0>0 or t1<L:
                u=_unit(_sub(b,a));s=tuple(a[j]+u[j]*t0 for j in range(3));t=tuple(a[j]+u[j]*t1 for j in range(3))
            else:s,t=a,b
            try:
                if it['index'].blocked(s,t):return True
            except ValueError:
                self.indeterminate+=1;return True
        return False
    def inside(self,p):
        return next((s.id for s in self.solids if s.contains(p)),None)
    def inside_excluded(self,p):
        return next((s.id for s in self.excluded_solids if s.contains(p)),None)

def _axis_cells(lo,hi,h):
    out=[];a=lo
    while a<hi-1e-12:
        b=min(a+h,hi);out.append((a,b));a=b
    return out

def discretise_cells(low,high,spacing,mode,slices=()):
    """Return [(centre, weight, cell_low, cell_high)] of zone-clipped cells (F20: bounds kept).
    SLICES cells have cell_low[2]==cell_high[2]==slice elevation and weight = area."""
    xs=_axis_cells(low[0],high[0],spacing);ys=_axis_cells(low[1],high[1],spacing)
    out=[]
    if mode=='VOLUME':
        for z0,z1 in _axis_cells(low[2],high[2],spacing):
            for y0,y1 in ys:
                for x0,x1 in xs:out.append((((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0)*(y1-y0)*(z1-z0),(x0,y0,z0),(x1,y1,z1)))
        return out
    for z in sorted(slices):
        if not low[2]<=z<=high[2]:raise ValueError('Slice elevation %.3f outside zone' % z)
        z=float(z)
        for y0,y1 in ys:
            for x0,x1 in xs:out.append((((x0+x1)/2,(y0+y1)/2,z),(x1-x0)*(y1-y0),(x0,y0,z),(x1,y1,z)))
    return out

def discretise(low,high,spacing,mode,slices=()):
    """Return [(centre, weight)] with weights = clipped cell volume (m3) or area (m2)."""
    return [(c,w) for c,w,_,_ in discretise_cells(low,high,spacing,mode,slices)]

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

def _classify(cells,obs,mode='VOLUME'):
    """Rev H (F01): each cell contributes its exact (box solids) or rigorously bounded (general
    closed meshes) FREE measure = cell measure - |cell n (solids u exclusions)|; exclusions and
    obstruction volume are reported separately without double counting. The cell's detection is
    evaluated at one representative free point (cell centre when free, else the nearest free
    sub-sample point) - cell-level sampling, documented in METHOD_AND_TOLERANCES_REV_H.md.
    Returns eligible [(rep_point, free_measure)], excluded measures, counts, meta per eligible cell."""
    dims=(0,1,2) if mode=='VOLUME' else (0,1)
    eligible=[];meta=[];excl={'inside_obstruction':0.,'excluded_component':0.};count={'inside_obstruction':0,'excluded_component':0,'partial_cells':0,'approximate_cells':0,'unsampled_free_cells':0}
    bound=0.;unsampled=0.
    for cell in cells:
        if len(cell)==2:c,w=cell;lo=hi=None
        else:c,w,lo,hi=cell
        if lo is None:
            if obs.inside_excluded(c):excl['excluded_component']+=w;count['excluded_component']+=1
            elif obs.inside(c):excl['inside_obstruction']+=w;count['inside_obstruction']+=1
            else:eligible.append((c,w));meta.append({'centre':c,'bounds':None,'method':'POINT'})
            continue
        m=cell_measure(lo,hi,obs.solids,obs.excluded_solids,dims)
        excl['excluded_component']+=m['excluded'];excl['inside_obstruction']+=m['obstruction'];bound+=m['bound']
        if m['method'].startswith('ADAPTIVE'):count['approximate_cells']+=1
        if m['free']<=1e-15*max(w,1e-300):
            if m['excluded']>=m['obstruction']:count['excluded_component']+=1
            else:count['inside_obstruction']+=1
            continue
        if m['free']<w*(1-1e-12):count['partial_cells']+=1
        if m['rep'] is None:
            count['unsampled_free_cells']+=1;unsampled+=m['free'];continue
        eligible.append((m['rep'],m['free']));meta.append({'centre':c,'bounds':(lo,hi),'method':m['method']})
    excl['measure_error_bound']=bound;excl['unsampled_free_measure']=unsampled
    return eligible,excl,count,meta

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
    # Rev H (F05): sight lines always start AT the detector. The standoff only ignores hits on the
    # detector's own declared mount component within the standoff radius; any other geometry
    # between the detector and the target blocks (no blind zone is created).
    ign=[[(d['mount_component_id'],stand,True)] if d.get('mount_component_id') else None for d in dets]
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
                if not obs.blocked(d['position'],t,ignore=ign[i]):seen+=1
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
            st=setup['standoff_m']
            if L<=2*st+1e-12:
                findings.append({'severity':'BLOCKING','detector':d['id'],'text':'Beam length %.3f m not greater than twice the mount standoff; detector treated inoperative' % L});continue
            ign=[x for x in ((d.get('mount_component_id'),st,True),(d.get('receiver_mount_component_id'),st,False)) if x[0]]
            if obs.blocked(d['position'],rx,ignore=ign or None):
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

GRID_STATUSES=('GRID AGREEMENT (not an error bound)','GRID DISAGREEMENT - refine grid','UNRESOLVED FEATURE - refine grid','NOT EVALUABLE - no eligible measure','NOT CHECKED (refinement 1)')

def _grid_agreement(setup,dets,fr,tot,run,method):
    """Rev H (F07): a two-grid comparison is reported as GRID AGREEMENT/DISAGREEMENT, never as
    convergence or an error bound. No Richardson extrapolation is performed (no asymptotic
    order is established for this discontinuous indicator). A feature smaller than two coarse
    cells (detector reach, design cloud) is reported UNRESOLVED regardless of agreement."""
    ref=setup['convergence']['refinement'];h=setup['grid_spacing_m'];tol=float(setup['convergence']['tolerance'])
    if ref<=1:return {'status':GRID_STATUSES[4]}
    _,rows2,_,_,_=run(h/ref,False);fr2,_,tot2=_fractions(rows2,[d['id'] for d in dets])
    delta={k:(None if fr[k] is None or fr2[k] is None else abs(fr2[k]-fr[k])) for k in fr}
    out={'refined_spacing_m':h/ref,'refined_fractions':fr2,'abs_delta':delta,'tolerance':setup['convergence']['tolerance'],
         'eligible_measure':tot,'refined_eligible_measure':tot2,'eligible_measure_rel_delta':None if tot<=0 else abs(tot2-tot)/tot,
         'note':'Two-grid agreement check only; not an error bound and not proof of convergence. No Richardson extrapolation.'}
    unresolved=[]
    if method=='FLAME_GEOGRAPHIC':
        f=setup['flame']
        for d in dets:
            s=1.0
            if f['fire_size_scaling']=='INVERSE_SQUARE':s=math.sqrt(f['heat_release_kw']/d['entry']['target_fire']['heat_release_kw'])
            reach=max(r for _,r in d['entry']['contour'])*s
            if reach<2*h:unresolved.append('detector %s reach %.3f m < 2 x grid %.3f m' % (d['id'],reach,h))
    else:
        semi=_ellipsoid_semi(setup['gas']['cloud'])
        if 2*min(semi)<2*h:unresolved.append('design cloud minimum diameter %.3f m < 2 x grid %.3f m' % (2*min(semi),h))
    out['unresolved_features']=unresolved
    if tot<=0 or tot2<=0 or any(v is None for v in delta.values()):out['status']=GRID_STATUSES[3]
    elif unresolved:out['status']=GRID_STATUSES[2]
    else:
        worst=max(v for v in delta.values());out['worst_abs_delta']=worst
        out['status']=GRID_STATUSES[0] if worst<=tol+1e-12 and out['eligible_measure_rel_delta']<=tol+1e-12 else GRID_STATUSES[1]
    return out

def zone_coverage(zone,setup,detectors,entries,obs,cancel=None,progress=None,sensitivity=False):
    """Compute one zone. detectors: [{id,detector_type,position,azimuth,elevation,roll,library_id,receiver?}]."""
    method=setup['method'];findings=[]
    dets=_prepare_detectors(detectors,entries);ids=[d['id'] for d in dets]
    for d in dets:
        inside=obs.inside(d['position'])
        if inside:findings.append({'severity':'REVIEW','detector':d['id'],'text':'Detector position lies inside obstruction '+inside+'; check mounting standoff'})
    unit='m3' if setup['mode']=='VOLUME' else 'm2'
    def run(spacing,with_progress=True):
        samples=discretise_cells(zone['low'],zone['high'],spacing,setup['mode'],setup['slice_elevations_m'])
        eligible,excl,count,meta=_classify(samples,obs,setup['mode'])
        if method=='FLAME_GEOGRAPHIC':rows=_flame_votes(eligible,dets,setup,obs,cancel,progress if with_progress else None)
        else:rows=_gas_votes(eligible,dets,setup,obs,cancel,progress if with_progress else None,findings if with_progress else [])
        return samples,rows,excl,count,meta
    obs.indeterminate=0
    findings+=[dict(f) for f in obs.findings]
    samples,rows,excl,count,meta=run(setup['grid_spacing_m'])
    fr,per,tot=_fractions(rows,ids)
    req=setup['voting_required'];targets={}
    for k in ('1ooN','2ooN','3ooN'):
        t=setup['performance_targets'].get(k,'NOT SUPPLIED')
        if t=='NOT SUPPLIED':targets[k]={'target':'NOT SUPPLIED','achieved':fr[k],'status':'NO USER TARGET'}
        else:targets[k]={'target':t,'achieved':fr[k],'status':'NO ELIGIBLE VOLUME' if fr[k] is None else 'MEETS USER TARGET' if fr[k]>=float(t)-1e-12 else 'BELOW USER TARGET'}
    result={'zone_id':zone['id'],'zone_kind':zone['kind'],'method':method,'method_version':METHOD_VERSION[method],'label':LABEL,'mode':setup['mode'],'grid_spacing_m':setup['grid_spacing_m'],
            'measure_unit':unit,'zone_measure':math.fsum(c[1] for c in samples),'eligible_measure':tot,'excluded_measure':{k:excl[k] for k in ('inside_obstruction','excluded_component')},'excluded_samples':count,
            'measure_error_bound':excl['measure_error_bound'],'unsampled_free_measure':excl['unsampled_free_measure'],
            'measure_basis':'Exact free measure for axis-aligned box solids; adaptive bisection with rigorous bound for other closed meshes; detection sampled at one representative free point per cell (sampled-cell fraction)',
            'sample_count':len(samples),'eligible_samples':len(rows),'detectors_considered':ids,'voting_required':req,'fractions':fr,'required_voting_fraction':fr[f'{req}ooN'],
            'performance_targets':targets,'per_detector_fraction':per,'indeterminate_rays':obs.indeterminate,'findings':findings}
    if setup['mode']=='SLICES':
        result['slices']={}
        for z in sorted(setup['slice_elevations_m']):
            sub=[r for r,m in zip(rows,meta) if abs(m['centre'][2]-z)<1e-9];result['slices'][repr(float(z))]=_fractions(sub,ids)[0]
    result['convergence']=_grid_agreement(setup,dets,fr,tot,run,method)
    if sensitivity is True:sensitivity=(0.9,1.1)
    if sensitivity and method=='FLAME_GEOGRAPHIC':
        sens={}
        for factor in sensitivity:
            r2=_flame_votes([(p,w) for p,w,_ in rows],dets,setup,obs,cancel,None,factor);sens[repr(factor)]=_fractions(r2,ids)[0]
        result['sensitivity_range_factor']=sens
    samples_out={'detector_ids':ids,'row_format':['centre_x','centre_y','centre_z','free_measure','votes','cell_low','cell_high','rep_point'],
                 'rows':[[round(m['centre'][0],6),round(m['centre'][1],6),round(m['centre'][2],6),w,v,
                          None if m['bounds'] is None else [round(x,6) for x in m['bounds'][0]],None if m['bounds'] is None else [round(x,6) for x in m['bounds'][1]],
                          [round(x,6) for x in p]] for (p,w,v),m in zip(rows,meta)]}
    return result,samples_out
