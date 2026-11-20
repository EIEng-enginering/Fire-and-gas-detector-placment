"""Rev H (F13, F18): ONE central detector/basis compatibility and pose validation used by the
readiness gate (services.coverage.gather), layout-option candidates
(services.scenario_coverage.options_envelope) and the direct engine APIs
(engine.detection.engineering_flame_coverage / engineering_gas_coverage).
Returns a list of blocker strings; an empty list means compatible."""
from __future__ import annotations
import math

def norm_text(s):return ' '.join(str(s).lower().split())

def _finite_xyz(v):
    return isinstance(v,(list,tuple)) and len(v)==3 and all(not isinstance(x,bool) and isinstance(x,(int,float)) and math.isfinite(x) for x in v)

def pose_blockers(det):
    """Finite position and explicit finite in-range orientation (FLAME requires orientation)."""
    out=[];id=str(det.get('id'))
    if not _finite_xyz(det.get('position')):out.append('POSE_POSITION_NOT_FINITE:'+id)
    for k,lim in (('azimuth',180),('elevation',90),('roll',180)):
        v=det.get(k,0.0)
        if v is None and k=='roll':continue
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not -lim<=v<=lim:out.append('POSE_%s_INVALID:%s' % (k.upper(),id))
    if det.get('detector_type')=='OPEN_PATH':
        r=det.get('receiver')
        if r is None:out.append('RECEIVER:'+id)
        elif not _finite_xyz(r):out.append('RECEIVER_NOT_FINITE:'+id)
        elif _finite_xyz(det.get('position')) and math.dist(r,det['position'])<=0:out.append('RECEIVER_COINCIDENT:'+id)
    elif det.get('receiver') is not None:out.append('RECEIVER_NOT_ALLOWED:'+id)
    return out

def basis_blockers(setup,entry,det):
    """Library entry vs zone basis (fuel / fire size / scaling for flame; gas and type for gas)."""
    out=[];id=str(det.get('id'))
    if entry.get('detector_type')!=det.get('detector_type'):return ['LIBRARY_TYPE_MISMATCH:'+id]
    if setup['method']=='FLAME_GEOGRAPHIC':
        f=setup['flame']
        if det.get('detector_type')!='FLAME':out.append('DETECTOR_TYPE_NOT_FLAME:'+id)
        if norm_text(entry['fuel_or_gas'])!=norm_text(f['fuel']):out.append('FUEL_MISMATCH:'+id+' library '+entry['fuel_or_gas']+' vs target '+f['fuel'])
        tf=entry.get('target_fire') or {}
        if not isinstance(tf.get('heat_release_kw'),(int,float)) or not tf['heat_release_kw']>0:out.append('LIBRARY_FIRE_SIZE_MISSING:'+id)
        elif f['fire_size_scaling']=='NONE' and abs(tf['heat_release_kw']-f['heat_release_kw'])>1e-9:out.append('FIRE_SIZE_MISMATCH:'+id+' (select INVERSE_SQUARE scaling explicitly or use a matching entry)')
        if not entry.get('contour') or not entry.get('fov'):out.append('LIBRARY_CONTOUR_OR_FOV_MISSING:'+id)
    else:
        g=setup['gas']
        if det.get('detector_type') not in g['detector_types']:out.append('DETECTOR_TYPE_NOT_IN_GAS_SETUP:'+id)
        if norm_text(entry['fuel_or_gas'])!=norm_text(g['gas']):out.append('GAS_MISMATCH:'+id+' library '+entry['fuel_or_gas']+' vs cloud '+g['gas'])
        if not entry.get('alarm_threshold'):out.append('LIBRARY_ALARM_THRESHOLD_MISSING:'+id)
        if det.get('detector_type')=='OPEN_PATH' and not entry.get('path_length_m'):out.append('LIBRARY_PATH_LENGTH_MISSING:'+id)
    return out

def detector_blockers(setup,entry,det):
    return pose_blockers(det)+basis_blockers(setup,entry,det)
