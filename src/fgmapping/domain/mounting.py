"""Source anchor plus SI offset in orthonormal component-frame axes.

Scale/unit conversion applies to the source anchor. Physical metre offsets and
mount orientation use normalized frame columns; scale is not applied twice.
Azimuth +X toward +Y; elevation above XY; roll about detector boresight X.
"""
import math
from fgmapping.domain.scene import vector,content_hash

def multiply(a,b):return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def rotation(azimuth,elevation,roll):
 if any(not math.isfinite(v) for v in (azimuth,elevation,roll)) or not -180<=azimuth<=180 or not -90<=elevation<=90 or not -180<=roll<=180:raise ValueError('Explicit finite mount angles within supported domain required')
 a,e,r=map(math.radians,(azimuth,elevation,roll));ca,sa,ce,se,cr,sr=math.cos(a),math.sin(a),math.cos(e),math.sin(e),math.cos(r),math.sin(r)
 return ((ca*ce,-ca*se*sr-sa*cr,-ca*se*cr+sa*sr),(sa*ce,-sa*se*sr+ca*cr,-sa*se*cr-ca*sr),(se,ce*sr,ce*cr))
def angles(matrix):
 elevation=math.asin(max(-1,min(1,matrix[2][0])))
 if abs(math.cos(elevation))<1e-10:azimuth=math.atan2(-matrix[0][1],matrix[1][1]);roll=0.
 else:azimuth=math.atan2(matrix[1][0],matrix[0][0]);roll=math.atan2(matrix[2][1],matrix[2][2])
 return tuple(math.degrees(v) for v in (azimuth,elevation,roll))
def component_fingerprint(scene,component):
 return content_hash({'frame':scene.frame(component.frame_id).__dict__,'component':{'id':component.id,'mesh':component.mesh.sha256}})
def mount_pose(scene,component_id,anchor_local,offset_m,orientation_local):
 anchor=vector(anchor_local);offset=vector(offset_m);orient=vector(orientation_local)
 component=next((c for c in scene.components if c.id==component_id),None)
 if component is None:raise ValueError('Explicit mount component not found')
 if component.semantic=='DETECTOR':raise ValueError('Mount must reference facility geometry, not a detector display marker')
 frame=scene.frame(component.frame_id);m=frame.matrix
 lengths=[math.sqrt(sum(m[i][j]**2 for i in range(3))) for j in range(3)]
 basis=tuple(tuple(m[i][j]/lengths[j] for j in range(3)) for i in range(3))
 base=frame.world(anchor);position=vector(tuple(base[i]+sum(basis[i][j]*offset[j] for j in range(3)) for i in range(3)))
 world_rotation=multiply(basis,rotation(*orient));world_angles=angles(world_rotation)
 return {'position':position,'orientation_world':world_angles,'rotation_world':world_rotation,'component_fingerprint':component_fingerprint(scene,component),'anchor_world':base,'offset_units':'m','anchor_units':frame.units}
