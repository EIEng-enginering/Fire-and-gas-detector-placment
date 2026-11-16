"""Measured sparse-scene broadphase and bounded import preview; synthetic only."""
import time,json,tempfile,csv,io
from pathlib import Path
from unittest.mock import patch
from fgmapping.domain.scene import Frame,Scene,Component,box_mesh
from fgmapping.engine.inspection import inspect_target
from fgmapping.engine.mesh_visibility import MeshIndex
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry
from fgmapping.services.bulk_import import HEADERS,prepare_bulk
from fgmapping.services.preparation import state_hash
ROOT=Path(__file__).resolve().parents[1]
components=tuple(Component('B'+str(i),'Synthetic sparse box','EQUIPMENT','F',box_mesh((2,20+2*i,0),(3,21+2*i,1)),'E') for i in range(256));scene=Scene((Frame('F','m','Synthetic benchmark'),),components,'SYNTHETIC','0'*64);target={'center_m':[4,0,0],'u':[0,1,0],'v':[0,0,1],'width_m':2,'height_m':2,'nx':16,'ny':16};runs=[];outputs=[];original=MeshIndex.blocked
for enabled in (False,True):
 calls=[]
 def spy(index,a,b):calls.append(1);return original(index,a,b)
 start=time.perf_counter()
 with patch.object(MeshIndex,'blocked',spy):result=inspect_target(scene,[0,0,0],[c.id for c in components],target,1e-8,broadphase=enabled)
 runs.append({'indexed':enabled,'seconds_including_index_build':time.perf_counter()-start,'mesh_queries':len(calls)});outputs.append(result)
assert outputs[0]==outputs[1];assert outputs[1]['visibility_fraction']==1.;assert runs[1]['mesh_queries']==0 and runs[0]['mesh_queries']==256*256
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);case=create_case(root/'s.fgcase','SYNTHETIC 2000 IMPORT')
 with CaseSession(case,root/'r') as s:
  enable_geometry(s,'AUTOMATION_ENGINE');s.add_evidence('E','SYNTHETIC','Synthetic benchmark rows','A','generated','AUTOMATION_ENGINE');out=io.StringIO();wr=csv.DictWriter(out,fieldnames=HEADERS);wr.writeheader()
  for i in range(2000):wr.writerow({**{k:'' for k in HEADERS},'data_class':'SYNTHETIC','action':'CREATE','kind':'DETECTOR','id':'SYN-'+str(i),'evidence_id':'E','detector_type':'FLAME','x':i,'y':0,'z':3,'azimuth':0,'elevation':0,'roll':0})
  raw=out.getvalue().encode();before=state_hash(s);start=time.perf_counter();plan=prepare_bulk(s,raw,'CSV');elapsed=time.perf_counter()-start;assert state_hash(s)==before;assert json.loads(plan.summary_json)['count']==2000
  bulk={'rows':2000,'bytes':len(raw),'preview_seconds':elapsed,'case_unchanged':True}
record={'qualification':'UNVERIFIED SOFTWARE BENCHMARK ONLY','platform':'Linux; Windows NOT RUN','sparse_scene':{'obstacles':256,'rays':256,'outputs_identical':True,'independent_geometric_expected_clear_fraction':1.,'runs':runs},'bulk_import':bulk,'limits':'One synthetic sparse scene; timings are observations, not general speed or Windows performance guarantees'}
(ROOT/'TEST_RESULTS/REV_E_BENCHMARKS.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
