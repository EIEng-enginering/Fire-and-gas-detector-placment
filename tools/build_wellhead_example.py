"""Build the SYNTHETIC offshore wellhead module example study (Rev F).

ILLUSTRATIVE / SYNTHETIC ONLY. Not a real facility, not a design, no engineering
claim. Geometry and candidate detector locations are study-setup inputs only;
no surface mounting, detector field of view/response or coverage is inferred.
Engineering calculation remains BLOCKED.

Reproducible: inputs are generated deterministically into --inputs, then the
case is built FROM THOSE FILES through the application's own service paths:
  geometry  : Scene.from_dict(JSON) -> services.geometry.set_scene
  registers : services.bulk_import.prepare_bulk(CSV) -> preparation.apply_plan
  zones     : services.workspace.record_command (FIRE_ZONE / GAS_ZONE)
  basis     : services.basis.set_basis

Usage (from the source root, PYTHONPATH=src:.):
  python -B tools/build_wellhead_example.py --inputs examples/wellhead --case examples/SYNTHETIC_WELLHEAD_MODULE.fgcase
Existing destinations are refused (never overwritten).
"""
from __future__ import annotations
import argparse,csv,io,json,shutil,sys,tempfile
from pathlib import Path

EVIDENCE='SYN-WHM-GEOM-01'
ACTOR='AUTOMATION_ENGINE'
REVIEWER='SYNTHETIC_EXAMPLE_BUILDER'
CASE_NAME='SYNTHETIC Wellhead Module WHM-01 (illustrative example, not a real facility)'
# Levels (local Z, metres, top of steel). Illustrative platform elevations in the
# docs map local 0 to EL +24.0 m above LAT; that mapping is narrative only.
CELLAR=0.0;MEZZ=4.5;UPPER=9.0
WELLS=[(f'W{n:02d}',x,y) for n,(x,y) in enumerate([(x,y) for y in (7.0,12.0) for x in (9.0,12.0,15.0,18.0)],1)]

def _c(id,label,semantic,lo,hi,parent=None,role='NOT SUPPLIED'):
    return {'id':id,'label':label,'semantic':semantic,'low':[float(v) for v in lo],'high':[float(v) for v in hi],'parent_id':parent,'occlusion_role':role}

def geometry_spec():
    c=[]
    # Decks
    c.append(_c('CD-PLATE','Cellar deck plate (synthetic, TOS EL local 0.0)','DECK',(0,0,CELLAR-.3),(30,20,CELLAR)))
    for i,(y0,y1) in enumerate(((4.6,6.2),(8.6,10.6),(13.4,15.0))):
        c.append(_c(f'MZ-GRATE-{i+1}',f'Wellhead/mezzanine deck grating strip {i+1} (EL local +4.5)','GRATING',(7.4,y0,MEZZ-.05),(19.6,y1,MEZZ)))
    c.append(_c('MZ-GRATE-4','Mezzanine walkway to manifold (grating)','GRATING',(19.6,4.6,MEZZ-.05),(22.5,15.0,MEZZ)))
    # Upper (weather) deck plate with an intervention hatch strip over the well rows
    c.append(_c('UD-PLATE-S','Upper deck plate south (EL local +9.0)','DECK',(0,0,UPPER),(30,5.8,UPPER+.3)))
    c.append(_c('UD-PLATE-N','Upper deck plate north','DECK',(0,13.2,UPPER),(30,20,UPPER+.3)))
    c.append(_c('UD-PLATE-W','Upper deck plate west of hatch','DECK',(0,5.8,UPPER),(7.8,13.2,UPPER+.3)))
    c.append(_c('UD-PLATE-E','Upper deck plate east of hatch','DECK',(19.2,5.8,UPPER),(30,13.2,UPPER+.3)))
    # Primary structure: 8 columns, perimeter and transverse beams at upper deck
    for i,x in enumerate((0.0,10.0,20.0,30.0)):
        for j,y in enumerate((0.0,20.0)):
            x0=min(max(x-.3,0),29.4);y0=min(max(y-.3,0),19.4)
            c.append(_c(f'COL-{"ABCD"[i]}{j+1}',f'Main column {"ABCD"[i]}{j+1} (synthetic 0.6 m box envelope)','STRUCTURE',(x0,y0,CELLAR-1.5),(x0+.6,y0+.6,UPPER)))
    c.append(_c('BM-S','Primary beam south (gridline 1)','STRUCTURE',(0,0,UPPER-1.0),(30,.5,UPPER)))
    c.append(_c('BM-N','Primary beam north (gridline 2)','STRUCTURE',(0,19.5,UPPER-1.0),(30,20,UPPER)))
    for i,x in enumerate((0.0,10.0,20.0,30.0)):
        x0=min(max(x-.25,0),29.5)
        c.append(_c(f'BM-T{"ABCD"[i]}',f'Transverse beam gridline {"ABCD"[i]}','STRUCTURE',(x0,.5,UPPER-1.0),(x0+.5,19.5,UPPER)))
    c.append(_c('BM-MZ-W','Mezzanine support beam west','STRUCTURE',(7.2,4.6,MEZZ-.6),(7.4,15.0,MEZZ-.05)))
    c.append(_c('BM-MZ-E','Mezzanine support beam east','STRUCTURE',(22.5,4.6,MEZZ-.6),(22.7,15.0,MEZZ-.05)))
    # Boundaries: blast/fire walls north and west; south and east open (handrails only)
    c.append(_c('BW-NORTH','Blast/fire wall north (synthetic rating NOT SUPPLIED)','WALL',(0,19.7,CELLAR),(30,20,UPPER)))
    c.append(_c('BW-WEST','Blast/fire wall west (synthetic rating NOT SUPPLIED)','WALL',(0,0,CELLAR),(.3,19.7,UPPER)))
    c.append(_c('HR-SOUTH','Handrail south open side (1.1 m envelope)','STRUCTURE',(.3,0,CELLAR),(30,.05,CELLAR+1.1)))
    c.append(_c('HR-EAST','Handrail east open side (1.1 m envelope)','STRUCTURE',(29.95,.05,CELLAR),(30,19.7,CELLAR+1.1)))
    # Wells: wellhead, Xmas tree, tree cap, wing valve, choke, flowline riser + run
    for id,x,y in WELLS:
        c.append(_c(f'{id}-WH',f'Well slot {id} wellhead body','EQUIPMENT',(x-.45,y-.45,CELLAR),(x+.45,y+.45,CELLAR+1.3)))
        c.append(_c(f'{id}-XT',f'Well slot {id} Xmas tree body','EQUIPMENT',(x-.3,y-.3,CELLAR+1.3),(x+.3,y+.3,CELLAR+3.6),parent=f'{id}-WH'))
        c.append(_c(f'{id}-CAP',f'Well slot {id} tree cap','EQUIPMENT',(x-.2,y-.2,CELLAR+3.6),(x+.2,y+.2,CELLAR+3.9),parent=f'{id}-XT'))
        c.append(_c(f'{id}-WV',f'Well slot {id} production wing valve','EQUIPMENT',(x+.3,y-.2,CELLAR+2.4),(x+.8,y+.2,CELLAR+2.9),parent=f'{id}-XT'))
        c.append(_c(f'{id}-CH',f'Well slot {id} production choke','EQUIPMENT',(x+.8,y-.25,CELLAR+2.35),(x+1.2,y+.25,CELLAR+2.95),parent=f'{id}-XT'))
        c.append(_c(f'{id}-FL-R',f'Well slot {id} flowline riser (6 in nominal envelope)','PIPE',(x+1.2,y-.1,CELLAR+2.55),(x+1.4,y+.1,CELLAR+6.0)))
        c.append(_c(f'{id}-FL-H',f'Well slot {id} flowline run to manifold','PIPE',(x+1.4,y-.1,CELLAR+5.8),(23.8,y+.1,CELLAR+6.0)))
    # Production/test manifold, headers, drop legs
    c.append(_c('MF-SKID','Production/test manifold skid envelope','EQUIPMENT',(23.5,4.0,CELLAR),(27.5,16.0,CELLAR+.6)))
    for id,x in (('HDR-PROD','24.5'),('HDR-TEST','26.5')):
        x=float(x);c.append(_c(id,('Production' if id=='HDR-PROD' else 'Test')+' header (10 in nominal envelope)','PIPE',(x-.15,4.5,CELLAR+1.6),(x+.15,15.5,CELLAR+1.9),parent='MF-SKID'))
    for id,x,y in WELLS:
        c.append(_c(f'{id}-DROP',f'Well slot {id} flowline drop leg to manifold','PIPE',(23.8,y-.1,CELLAR+1.9),(24.0,y+.1,CELLAR+6.0)))
        c.append(_c(f'{id}-MV',f'Well slot {id} manifold diverter valve','EQUIPMENT',(24.0,y-.25,CELLAR+1.5),(26.6,y+.25,CELLAR+2.0),parent='MF-SKID'))
    c.append(_c('HDR-EXPORT','Production header outlet to process (synthetic)','PIPE',(24.35,15.5,CELLAR+1.6),(24.65,19.7,CELLAR+1.9),parent='HDR-PROD'))
    c.append(_c('TS-INLET','Test header outlet to test separator (off-module)','PIPE',(26.35,15.5,CELLAR+1.6),(26.65,19.7,CELLAR+1.9),parent='HDR-TEST'))
    # Wireline / well intervention area (west bay) and temporary pressure control envelope over W01
    c.append(_c('WL-UNIT','Wireline unit skid envelope (temporary)','EQUIPMENT',(1.5,6.0,CELLAR),(5.0,9.0,CELLAR+2.6)))
    c.append(_c('WL-PCE','Wireline power pack / control cabin envelope','EQUIPMENT',(1.5,10.0,CELLAR),(4.0,12.5,CELLAR+2.4)))
    c.append(_c('WL-LUB','Intervention lubricator / PCE envelope above W01 (temporary)','EQUIPMENT',(8.75,6.75,CELLAR+3.9),(9.25,7.25,UPPER+3.0),parent='W01-CAP'))
    c.append(_c('WL-LAYDOWN','Intervention laydown area marker (non-obstructing)','AREA_MARKER',(1.0,13.5,CELLAR),(6.5,18.5,CELLAR+.02),role='NON_OBSTRUCTING_ANNOTATION'))
    # Escape routes (non-obstructing floor markers) and stairs
    c.append(_c('ER-SOUTH','Primary escape route south walkway (1.2 m wide marker)','ESCAPE_ROUTE',(.5,.4,CELLAR),(29.5,1.6,CELLAR+.02),role='NON_OBSTRUCTING_ANNOTATION'))
    c.append(_c('ER-EAST','Primary escape route east walkway (1.2 m wide marker)','ESCAPE_ROUTE',(28.2,1.6,CELLAR),(29.4,19.4,CELLAR+.02),role='NON_OBSTRUCTING_ANNOTATION'))
    c.append(_c('ER-WELLBAY','Secondary escape route between well rows','ESCAPE_ROUTE',(7.0,9.0,CELLAR),(23.0,10.2,CELLAR+.02),role='NON_OBSTRUCTING_ANNOTATION'))
    c.append(_c('ER-MZ','Mezzanine escape route marker','ESCAPE_ROUTE',(19.8,4.8,MEZZ),(22.3,14.8,MEZZ+.02),role='NON_OBSTRUCTING_ANNOTATION'))
    c.append(_c('ST-MZ','Stair cellar deck to mezzanine (envelope)','STRUCTURE',(20.5,1.7,CELLAR),(22.5,4.5,MEZZ)))
    c.append(_c('ST-UD','Stair mezzanine to upper deck (envelope)','STRUCTURE',(27.6,16.0,CELLAR),(29.4,19.4,UPPER)))
    return c

def scene_payload():
    from fgmapping.domain.scene import Frame,Scene,Component,box_mesh,content_hash
    from dataclasses import asdict
    spec=geometry_spec()
    frame=Frame('WHM_LOCAL','m','SYNTHETIC wellhead module WHM-01 local origin at SW corner, cellar deck top of steel; X east, Y north, Z up. Illustrative only')
    comps=tuple(Component(s['id'],s['label'],s['semantic'],'WHM_LOCAL',box_mesh(s['low'],s['high']),EVIDENCE,s['parent_id'],s['occlusion_role']) for s in spec)
    scene=Scene((frame,),comps,'SYNTHETIC WHM-01 rev A (generated)',content_hash(spec))
    return scene.to_dict()

DETECTORS=[
 # id, type, x,y,z, azimuth, elevation  -- candidate positions only, not mounted/qualified
 ('FD-101','FLAME',0.9,0.9,7.5,45,-35),('FD-102','FLAME',29.1,0.9,7.5,135,-35),('FD-103','FLAME',0.9,19.1,7.5,-45,-35),('FD-104','FLAME',29.1,19.1,7.5,-135,-35),
 ('FD-105','FLAME',10.6,0.9,8.0,90,-45),('FD-106','FLAME',20.6,19.1,8.0,-90,-45),('FD-107','FLAME',7.6,10.0,4.0,0,-20),('FD-108','FLAME',27.8,10.0,4.2,180,-25),
 ('GD-101','POINT_GAS',8.0,6.0,0.6,0,0),('GD-102','POINT_GAS',13.5,6.0,0.6,0,0),('GD-103','POINT_GAS',19.0,6.0,0.6,0,0),('GD-104','POINT_GAS',8.0,13.0,0.6,0,0),
 ('GD-105','POINT_GAS',13.5,13.0,0.6,0,0),('GD-106','POINT_GAS',19.0,13.0,0.6,0,0),('GD-107','POINT_GAS',22.8,6.0,1.0,0,0),('GD-108','POINT_GAS',22.8,14.0,1.0,0,0),
 ('GD-109','POINT_GAS',28.0,10.0,1.0,0,0),('GD-110','POINT_GAS',5.5,7.5,0.6,0,0),('GD-111','POINT_GAS',13.5,9.6,5.0,0,0),('GD-112','POINT_GAS',21.0,10.0,5.0,0,0),
 ('GD-OP-01','OPEN_PATH',1.0,2.0,1.5,0,0),('GD-OP-02','OPEN_PATH',28.5,2.5,1.5,90,0),('GD-OP-03','OPEN_PATH',7.0,9.6,2.0,0,0)]
OPEN_PATH_RECEIVERS=[('GD-OP-01-RX',29.0,2.0,1.5,'GD-OP-01'),('GD-OP-02-RX',28.5,18.5,1.5,'GD-OP-02'),('GD-OP-03-RX',22.8,9.6,2.0,'GD-OP-03')]

def register_rows():
    from fgmapping.services.bulk_import import HEADERS
    rows=[]
    for id,t,x,y,z,az,el in DETECTORS:
        rows.append({'data_class':'SYNTHETIC','action':'CREATE','kind':'DETECTOR','id':id,'evidence_id':EVIDENCE,'detector_type':t,'x':x,'y':y,'z':z,'azimuth':az,'elevation':el,'roll':0,'manufacturer':'NOT SUPPLIED','model':'NOT SUPPLIED','sensitivity':'NOT SUPPLIED'})
    for id,x,y in WELLS:
        rows.append({'data_class':'SYNTHETIC','action':'CREATE','kind':'EQUIPMENT','id':f'EQ-{id}','evidence_id':EVIDENCE,'x':x,'y':y,'z':0.65,'equipment_type':f'Synthetic well slot {id} wellhead and Xmas tree (illustrative)','geometry_component_id':f'{id}-WH'})
    for id,desc,comp,(x,y,z) in [('EQ-MF','Synthetic production/test manifold','MF-SKID',(25.5,10.0,0.3)),('EQ-HDR-PROD','Synthetic production header','HDR-PROD',(24.5,10.0,1.75)),('EQ-HDR-TEST','Synthetic test header','HDR-TEST',(26.5,10.0,1.75)),('EQ-WL-UNIT','Synthetic wireline unit (temporary intervention equipment)','WL-UNIT',(3.25,7.5,1.3)),('EQ-WL-PCE','Synthetic wireline power pack / control cabin','WL-PCE',(2.75,11.25,1.2)),('EQ-WL-LUB','Synthetic lubricator / pressure control envelope over W01','WL-LUB',(9.0,7.0,8.0))]:
        rows.append({'data_class':'SYNTHETIC','action':'CREATE','kind':'EQUIPMENT','id':id,'evidence_id':EVIDENCE,'x':x,'y':y,'z':z,'equipment_type':desc,'geometry_component_id':comp})
    for id,x,y,z,tx in OPEN_PATH_RECEIVERS:
        rows.append({'data_class':'SYNTHETIC','action':'CREATE','kind':'EQUIPMENT','id':id,'evidence_id':EVIDENCE,'x':x,'y':y,'z':z,'equipment_type':f'Synthetic open-path receiver/reflector position paired with transmitter {tx} (candidate; beam path not modelled)','geometry_component_id':''})
    return HEADERS,[{**{k:'' for k in HEADERS},**{k:str(v) for k,v in r.items()}} for r in rows]

ZONES=[
 ('FZ-WELLBAY','FIRE_ZONE',(7.0,4.0,0.0),(20.5,15.5,9.0),'Synthetic fire zone: wellbay (8 slots, cellar to upper deck)'),
 ('FZ-MANIFOLD','FIRE_ZONE',(22.8,3.5,0.0),(28.0,16.5,4.5),'Synthetic fire zone: production/test manifold'),
 ('FZ-WIRELINE','FIRE_ZONE',(1.0,5.5,0.0),(6.5,13.0,4.0),'Synthetic fire zone: wireline / well intervention area'),
 ('GZ-WELLBAY','GAS_ZONE',(7.0,4.0,0.0),(20.5,15.5,9.0),'Synthetic gas zone: wellbay'),
 ('GZ-MANIFOLD','GAS_ZONE',(22.8,3.5,0.0),(28.0,16.5,4.5),'Synthetic gas zone: manifold'),
 ('GZ-MODULE','GAS_ZONE',(0.3,0.0,0.0),(30.0,19.7,9.0),'Synthetic gas zone: whole module volume below upper deck')]

def zones_payload():
    return {'contract':'fg-wellhead-example-zones/1','data_class':'SYNTHETIC','zones':[{'id':i,'kind':k,'payload':{'low':list(lo),'high':list(hi),'units':'m','description':d}} for i,k,lo,hi,d in ZONES]}

def basis_payload():
    return {'contract':'fg-study-basis/1','revision':'SYN-WHM-A','study_type':'BOTH','coordinate_reference':'WHM_LOCAL synthetic frame (m); X east, Y north, Z up; cellar deck TOS = 0','target_description':'NOT SUPPLIED - illustrative example; no fire/gas scenario or target defined','fuel_or_gas':'NOT SUPPLIED','voting':2,'criterion_reference':'NOT SUPPLIED','target_fraction':'NOT SUPPLIED','exclusions':[{'component_id':c,'reason':'Non-obstructing floor/area marker annotation','evidence_id':EVIDENCE} for c in ('ER-SOUTH','ER-EAST','ER-WELLBAY','ER-MZ','WL-LAYDOWN')],'uncertainty_reference':'NOT SUPPLIED'}

FILES={'geometry':'SYNTHETIC_WELLHEAD_GEOMETRY.json','csv':'SYNTHETIC_WELLHEAD_REGISTER.csv','xlsx':'SYNTHETIC_WELLHEAD_REGISTER.xlsx','zones':'SYNTHETIC_WELLHEAD_ZONES.json','basis':'SYNTHETIC_WELLHEAD_BASIS.json'}

def write_inputs(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    for name in FILES.values():
        if (folder/name).exists():raise SystemExit('Refusing to overwrite existing input: '+str(folder/name))
    (folder/FILES['geometry']).write_bytes((json.dumps({'contract':'fg-wellhead-example-geometry/1','data_class':'SYNTHETIC','note':'Illustrative synthetic geometry, not a real facility','scene':scene_payload()},indent=1,sort_keys=True)+'\n').encode('utf8'))
    headers,rows=register_rows();out=io.StringIO(newline='');wr=csv.DictWriter(out,fieldnames=headers,lineterminator='\n');wr.writeheader();wr.writerows(rows)
    (folder/FILES['csv']).write_bytes(out.getvalue().encode('utf8'))
    from openpyxl import Workbook
    book=Workbook();sheet=book.active;sheet.title='Registers';sheet.append(list(headers))
    for r in rows:sheet.append([r[k] for k in headers])
    for row in sheet.iter_rows():
        for cell in row:cell.data_type='s'
    book.save(folder/FILES['xlsx'])
    (folder/FILES['zones']).write_bytes((json.dumps(zones_payload(),indent=1,sort_keys=True)+'\n').encode('utf8'))
    (folder/FILES['basis']).write_bytes((json.dumps(basis_payload(),indent=1,sort_keys=True)+'\n').encode('utf8'))

def build_case(case_path,inputs):
    """Build the case from the input files; returns a summary dict."""
    from fgmapping.domain.scene import Scene
    from fgmapping.services.case import create_case,CaseSession
    from fgmapping.services.geometry import enable_geometry,set_scene,get_scene
    from fgmapping.services.study_schema import enable_study
    from fgmapping.services.bulk_import import prepare_bulk
    from fgmapping.services.preparation import apply_plan
    from fgmapping.services import workspace as w
    from fgmapping.services.basis import set_basis,readiness
    case_path=Path(case_path).resolve();inputs=Path(inputs)
    if case_path.exists():raise SystemExit('Refusing to overwrite existing case: '+str(case_path))
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);p=create_case(root/'whm.fgcase',CASE_NAME)
        with CaseSession(p,root/'runtime') as s:
            enable_geometry(s,ACTOR)
            s.add_evidence(EVIDENCE,'SYNTHETIC','Generated illustrative wellhead module geometry and candidate register; not a real facility','A','tools/build_wellhead_example.py',ACTOR)
            geo=json.loads((inputs/FILES['geometry']).read_text(encoding='utf8'))
            if geo.get('data_class')!='SYNTHETIC':raise ValueError('Synthetic geometry input required')
            set_scene(s,Scene.from_dict(geo['scene']),ACTOR);enable_study(s,ACTOR)
            plan=prepare_bulk(s,(inputs/FILES['csv']).read_bytes(),'CSV')
            apply_plan(s,plan,REVIEWER,'Synthetic illustrative example register applied by generator; candidate values only, no engineering acceptance')
            for z in json.loads((inputs/FILES['zones']).read_text(encoding='utf8'))['zones']:
                w.record_command(s,z['id'],z['kind'],z['payload'],EVIDENCE,ACTOR,create=True)
            set_basis(s,json.loads((inputs/FILES['basis']).read_text(encoding='utf8')),EVIDENCE,ACTOR)
            r=readiness(s)
            if r['engineering_calculation_status']!='BLOCKED':raise AssertionError('Engineering gate must remain BLOCKED')
            scene=get_scene(s);s.save()
            summary={'case':str(case_path),'scene_sha256':scene.sha256,'components':len(scene.components),'detectors':len(w.detector_rows(s)),
                     'records':dict(s.con.execute('SELECT kind,count(*) FROM engineering_record GROUP BY kind').fetchall()),
                     'readiness':{k:r[k] for k in ('input_status','engineering_calculation_status','qualification')}}
        case_path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,case_path)
    return summary

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--inputs',required=True);ap.add_argument('--case',required=True);a=ap.parse_args(argv)
    write_inputs(a.inputs);print(json.dumps(build_case(a.case,a.inputs),indent=2))

if __name__=='__main__':main()
