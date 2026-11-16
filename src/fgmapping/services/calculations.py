"""Persist reproducible synthetic numerical exercises, never qualified results."""
from fgmapping.domain.scene import content_hash,canonical
from fgmapping.engine.detection import synthetic_weighted_votes,UniformDesignCloud
from fgmapping.errors import CaseError

def run_synthetic(session,id,method,inputs,actor):
    if not id.strip():raise CaseError('IDENTITY','Run ID required')
    if method=='SYNTHETIC_VOTES/1':result=synthetic_weighted_votes(inputs['rows'],inputs['required_votes'])
    elif method=='SYNTHETIC_UNIFORM_PATH/1':
        cloud=UniformDesignCloud(tuple(inputs['low']),tuple(inputs['high']),inputs['ppm'],inputs['basis'])
        result={'ppm_m':cloud.path_integral_ppm_m(inputs['start'],inputs['end']),'metric':'SYNTHETIC uniform cloud integral / not gas coverage','qualification':'UNVERIFIED'}
    elif method=='SYNTHETIC_FIELD_PATH/1':
        from fgmapping.engine.concentration import ConcentrationField
        field=ConcentrationField.from_dict(inputs['field'])
        result=field.beam_integral(inputs['start'],inputs['end'],inputs['time_s'],inputs['subdivisions'])
    else:raise CaseError('METHOD','Only named synthetic exercise methods are implemented')
    scene=session.con.execute('SELECT sha256 FROM geometry_scene WHERE id=1').fetchone()
    from pathlib import Path
    import hashlib
    from fgmapping import __version__
    root=Path(__file__).resolve().parents[1]
    paths=['engine/detection.py','engine/concentration.py','domain/scene.py','services/calculations.py']
    fingerprints={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in paths}
    envelope={'method':method,'inputs':inputs,'scene_hash':scene[0] if scene else None,'software_version':__version__,'implementation_files':fingerprints,'implementation_sha256':content_hash(fingerprints)}
    with session.con:
        session.con.execute('INSERT INTO calculation_run(id,input_hash,method,result_json,calculation_status,input_json) VALUES(?,?,?,?,?,?)',(id,content_hash(envelope),method,canonical(result),'COMPUTED_SYNTHETIC',canonical(envelope)))
        session._log(actor,'RUN_SYNTHETIC',{'id':id,'input_hash':content_hash(envelope),'method':method},{'retain':'Run history retained; edits mark stale'})
    session._dirty=True
    return result
