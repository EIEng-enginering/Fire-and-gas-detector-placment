# ADAPTED COPY for Rev H: only the IMPLEMENTATION tuple lookup (removed in Rev H) is replaced by
# services.fingerprint closures. All probe constructions and analytic expectations unchanged.
"""Independent Rev G review probes. Read-only source; synthetic data only.
Expected answers below are analytic constructions, not outputs from another engine run.
"""
import sys,json,math,hashlib,tempfile,shutil,sqlite3
from pathlib import Path
from unittest.mock import patch
ROOT=Path(sys.argv[1]).resolve();sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from fgmapping.engine.coverage import *
from fgmapping.domain.scene import Scene,Frame,Component,Mesh,box_mesh,content_hash
from fgmapping.domain.mounting import rotation
from fgmapping.engine.mesh_visibility import MeshIndex
from tests.unit.test_coverage_engine import flame_entry,flame_setup,gas_entry,gas_setup,det
out={}
def sc(*components):return Scene((Frame('F','m','SYNTHETIC REVIEW'),),tuple(components),'SYNTHETIC REVIEW','0'*64)
def box(id,lo,hi):return Component(id,id,'WALL','F',box_mesh(lo,hi),'E')
def zone(low,high):return {'id':'Z','kind':'FIRE_ZONE','low':low,'high':high}
def run(lo,hi,setup,dets,lib,scene=None,exclude=()):return zone_coverage(zone(lo,hi),setup,dets,lib,Obstructions(scene,exclude,setup['tolerance_m']))
e=flame_entry(contour=((0,100),(90,100)),fov=(180,180));lib={'E':e}
# Independent case1: every point has x>0 and distance<100m, so entire empty box is detected.
r,_=run((1,-1,-1),(3,1,1),flame_setup(spacing=.3,mode='VOLUME'),[det('D',(0,0,0))],lib)
out['empty_box']={'expected_volume':8,'actual_volume':r['eligible_measure'],'expected_1ooN':1,'actual_1ooN':r['fractions']['1ooN']}
# Independent case2: wall at x=1 and y>=0 shadows all positive-y rays; plate is outside target zone.
r,_=run((2,-1,-1),(4,1,1),flame_setup(spacing=.25,mode='VOLUME'),[det('D',(0,0,0))],lib,sc(box('W',(1,0,-10),(1.01,10,10))))
out['half_shadow']={'expected_volume':8,'actual_volume':r['eligible_measure'],'expected_1ooN':.5,'actual_1ooN':r['fractions']['1ooN']}
# A full unit box minus a 0.2-thick slab has true free volume0.8. Neither midpoint grid sees slab.
s=flame_setup(spacing=1,mode='VOLUME',ref=2)
r,_=run((0,0,0),(1,1,1),s,[det('D',(2,.5,.5),az=180)],lib,sc(box('S',(0,0,0),(.2,1,1))))
out['partial_solid_volume']={'expected_eligible':.8,'actual_eligible':r['eligible_measure'],'actual_excluded':r['excluded_measure'],'convergence':r['convergence']}
# Quarter disk sector of radius0.28 wholly within the unit plan zone => pi R²/4.
s=flame_setup(spacing=1,mode='SLICES',slices=(0,),ref=2);small={'E':flame_entry(contour=((0,.28),(45,.28)),fov=(180,180))}
r,_=run((0,-.5,-1),(1,.5,1),s,[det('D',(0,0,0))],small)
out['false_convergence']={'analytic_1ooN':math.pi*.28**2/4,'actual_1ooN':r['fractions']['1ooN'],'convergence':r['convergence']}
# Declared exclusion is a thin right triangle extruded in Z; point(.8,.8,.5) is outside it but inside AABB.
verts=((0,0,0),(1,0,0),(0,1,0),(0,0,1),(1,0,1),(0,1,1));faces=((0,2,1),(3,4,5),(0,1,4),(0,4,3),(1,2,5),(1,5,4),(2,0,3),(2,3,5));tri=Component('T','T','WALL','F',Mesh(verts,faces),'E');obs=Obstructions(sc(tri),['T'])
out['excluded_AABB']={'point':[.8,.8,.5],'analytic_inside':False,'actual_excluded_component':obs.inside_excluded((.8,.8,.5))}
# A sheared cube is closed. Ray exit lands exactly on diagonal shared by two top triangles.
mesh=box_mesh((0,0,0),(1,1,1));shear=Mesh(tuple((x+.3*z,y,z) for x,y,z in mesh.vertices),mesh.faces);obs=Obstructions(sc(Component('S','S','WALL','F',shear,'E')));dz=1e4*.5773502691896258;delta=(dz+.0123,dz+.0371,dz);point=tuple(t-.2*d/dz for t,d in zip((.8,.5,1),delta))
out['inside_shared_triangle_edge']={'point':point,'analytic_inside':True,'actual_inside':obs.inside(point),'closed_mesh_diagnostics':shear.diagnostics()}
# Coarse scene broadphase must not discard hits accepted by its own epsilon-aware mesh BVH.
obs=Obstructions(sc(box('B',(1,-1,-1),(1.01,1,1))),eps=1e-6);a=(0,1+5e-7,0);b=(2,1+5e-7,0)
out['epsilon_broadphase']={'mesh_blocked':obs.items[0]['index'].blocked(a,b),'scene_blocked':obs.blocked(a,b),'offset_outside_edge':5e-7,'tolerance':1e-6}
# Convention check vs independently defined right-handed Rx(30): local (10,5,0) -> world.
c=math.cos(math.pi/6);s=math.sin(math.pi/6);p=(10,5*c,5*s);d={**det('D',(0,0,0)),'roll':30,'frame':detector_frame(0,0,30)};el=flame_entry(contour=((0,100),(90,100)),fov=(60,20))
out['roll_convention']={'world_point':p,'analytic_local_horizontal_deg':math.degrees(math.atan(.5)),'analytic_local_vertical_deg':0,'expected_detected_for_right_hand_Rx':True,'actual_geometry_ok':flame_geometry_ok(d,el,p)[0],'mount_rotation_Rx30':rotation(0,0,30)}
# Standoff must not erase an unrelated front obstruction.
s=flame_setup(spacing=.2,mode='VOLUME');s['standoff_m']=.5
r,_=run((1,-.2,-.2),(2,.2,.2),s,[det('D',(-.2,0,0))],lib,sc(box('W',(0,-10,-10),(.1,10,10))))
out['standoff_skips_wall']={'analytic_LOS_1ooN':0,'actual_1ooN':r['fractions']['1ooN'],'standoff_m':.5,'wall_x':[0,.1],'detector_x':-.2}
# Offset sphere beam: R=2.5,b=1.5 => length2 sqrt(6.25-2.25)=4, at40%LEL reading1.6LEL.m.
ch=chord_length((-10,1.5,0),(10,1.5,0),(0,0,0),(2.5,2.5,2.5))
out['sphere_offset_chord']={'analytic_chord_m':4.,'actual_chord_m':ch,'analytic_at_40pct_LEL_LELm':1.6,'actual_LELm':.4*ch}
# Both grids wholly within a solid have undefined fractions; convergence must be UNEVALUABLE.
r,_=run((0,0,0),(1,1,1),flame_setup(spacing=1,mode='VOLUME',ref=2),[det('D',(-2,0,0))],lib,sc(box('S',(-1,-1,-1),(2,2,2))))
out['empty_denominator_convergence']={'eligible':r['eligible_measure'],'fractions':r['fractions'],'actual_convergence':r['convergence']['status'],'expected_convergence':'UNEVALUABLE / NO ELIGIBLE MEASURE'}
# Missing engine module fingerprints: changing scenario logic is not covered by scenario envelope hash.
from fgmapping.services.case import CaseSession
from fgmapping.services import coverage as cov,scenario_coverage as studies,workspace as w
from fgmapping.domain.scene import content_hash
case=ROOT/'examples/wellhead_coverage/SYNTHETIC_WELLHEAD_COVERAGE.fgcase'
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'s.fgcase';shutil.copyfile(case,p)
 with CaseSession(p,Path(tmp)/'r') as sess:
  rr=cov.latest_runs(sess);out['shipped_currency']={z:cov.run_currency(sess,row) for z,row in rr.items()}
  st=studies.study_runs(sess);from fgmapping.services.fingerprint import fingerprint as _fp;IMPL_S=set(_fp('SCENARIO_COVERAGE')[0]);IMPL_O=set(_fp('LAYOUT_OPTIONS')[0]);out['missing_study_source_hashes']={'listed_coverage_files':sorted(_fp('ZONE_COVERAGE')[0]),'scenario_module_present':'engine/scenario_coverage.py' in IMPL_S,'aggregate_present':'engine/scenarios.py' in IMPL_S,'options_present':'engine/optimisation.py' in IMPL_O,'study_states':{v['method']:studies.study_run_currency(sess,v) for v in st}}
  env,review,scene=cov.prepare_run(sess,'FZ-MANIFOLD','REVIEW-CHECK')
  # sensitivity output toggle has no representation in prepared envelope.
  out['sensitivity_not_hashed']={'envelope_keys':list(env),'has_sensitivity':any('sensitiv' in k for k in env)}
# Formula injection is confined to an isolated output workbook, never external URLs.
from fgmapping.services.coverage_report import _xlsx
from openpyxl import load_workbook
snap=json.loads((ROOT/'examples/wellhead_coverage/WELLHEAD_COVERAGE_REPORT/WELLHEAD_COVERAGE_REPORT.json').read_text());snap['library'][0]['source']['title']='=1+1'
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'formula.xlsx';_xlsx(snap,p);wb=load_workbook(p,data_only=False);cells=[{'sheet':ws.title,'cell':c.coordinate,'type':c.data_type,'value':c.value} for ws in wb for row in ws for c in row if c.data_type=='f'];wb.close();out['coverage_xlsx_formula_injection']=cells
print(json.dumps(out,indent=2))
