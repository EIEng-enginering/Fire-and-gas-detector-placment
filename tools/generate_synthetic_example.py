"""Create a synthetic case and normalised JSON snapshot; no client data."""
from __future__ import annotations
from pathlib import Path
import json
import os
from fgmapping.services.case import create_case,CaseSession,digest
ROOT=Path(__file__).resolve().parents[1]
ex=ROOT/'examples'; ex.mkdir(exist_ok=True)
p=ex/'SYNTHETIC_Offshore_Module.fgcase'
if p.exists():p.unlink()
create_case(p,'SYNTHETIC Offshore Process Module')
with CaseSession(p,ex/'runtime') as s:
    s.add_evidence('SYN-DR-001','SYNTHETIC_LAYOUT','Fictitious module layout, not a real installation','A','SYNTHETIC IMAGE 1','SYNTHETIC_ENGINEER')
    s.add_detector('SYN-FD-101','FLAME',1.0,2.0,3.0,'SYN-DR-001','SYNTHETIC_ENGINEER')
    s.add_detector('SYN-FD-102','FLAME',8.0,4.0,3.0,'SYN-DR-001','SYNTHETIC_ENGINEER')
    s.save()
with CaseSession(p,ex/'runtime') as s:
    snap=s.snapshot()
(ex/'SYNTHETIC_NORMALISED_SNAPSHOT.json').write_text(json.dumps(snap,indent=2)+'\n',encoding='utf8')
(ex/'SYNTHETIC_MANIFEST.json').write_text(json.dumps({'case_sha256':digest(p),'snapshot_sha256':digest(ex/'SYNTHETIC_NORMALISED_SNAPSHOT.json'),'status':'DEVELOPMENT BUILD'},indent=2),encoding='utf8')
print('Created',p)
