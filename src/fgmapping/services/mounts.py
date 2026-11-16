"""Explicit, undoable detector-to-facility component mounting proposals."""
import json
from fgmapping.services import workspace as w
from fgmapping.services.geometry import get_scene
from fgmapping.services.study_schema import require_study
from fgmapping.domain.mounting import mount_pose,component_fingerprint
from fgmapping.domain.scene import canonical
from fgmapping.errors import CaseError

def set_mount(session,detector_id,component_id,anchor_local,offset_m,orientation_local,evidence_id,actor):
 require_study(session);scene=get_scene(session)
 if scene is None:raise CaseError('GEOMETRY','Supply facility geometry first')
 detector=w.row(session,'detectors',detector_id)
 if detector is None:raise CaseError('MISSING','Detector not found')
 if w.row(session,'evidence',evidence_id) is None:raise CaseError('EVIDENCE','Mount source evidence required')
 pose=mount_pose(scene,component_id,anchor_local,offset_m,orientation_local)
 details=w.row(session,'detector_details',detector_id) or {}
 values={**detector,**{k:v for k,v in details.items() if k!='detector_id'},'x':pose['position'][0],'y':pose['position'][1],'z':pose['position'][2],**dict(zip(('azimuth','elevation','roll'),pose['orientation_world']))}
 changes=w.detector_plan(session,values,None,place_marker=True,mount_update=True)
 record={'detector_id':detector_id,'component_id':component_id,'anchor_local_json':canonical(anchor_local),'offset_m_json':canonical(offset_m),'orientation_local_json':canonical(orientation_local),'component_fingerprint':pose['component_fingerprint'],'evidence_id':evidence_id,'status':'CANDIDATE'}
 changes.append(w.change(session,'detector_mount',detector_id,record));w.execute(session,changes,actor,'Set explicit candidate mount '+detector_id+' on '+component_id)
 return pose

def detach_mount(session,detector_id,actor):
 require_study(session)
 if w.row(session,'detector_mount',detector_id) is None:raise CaseError('MISSING','No explicit mount to detach')
 w.execute(session,[w.change(session,'detector_mount',detector_id,None)],actor,'Detach mount; retain last candidate world coordinates '+detector_id)

def mount_status(session,record):
 scene=get_scene(session)
 component=None if scene is None else next((c for c in scene.components if c.id==record['component_id']),None)
 if component is None:return 'MISSING_COMPONENT'
 return 'CURRENT_SOURCE' if component_fingerprint(scene,component)==record['component_fingerprint'] else 'STALE_SOURCE'
