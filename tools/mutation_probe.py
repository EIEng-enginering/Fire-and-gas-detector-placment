"""Prove the geometry tests detect a deliberately broken implementation."""
from __future__ import annotations
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as d:
    d=Path(d)
    shutil.copytree(ROOT/'src'/'fgmapping',d/'fgmapping')
    p=d/'fgmapping'/'engine'/'geometry.py'
    old=p.read_text(encoding='utf8')
    target='return not any(line_hits_box(detector.position,target,b) for b in obstacles)'
    assert target in old,'Expected mutation site missing'
    p.write_text(old.replace(target,'return any(line_hits_box(detector.position,target,b) for b in obstacles)'),encoding='utf8')
    env=dict(os.environ,PYTHONPATH=str(d)+os.pathsep+str(ROOT),PYTHONDONTWRITEBYTECODE='1')
    cmd=[sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'tests'/'unit'),'-p','test_geometry.py','-v']
    r=subprocess.run(cmd,env=env,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    run=sorted(p for p in (ROOT/'TEST_RESULTS').iterdir() if p.is_dir() and p.name[:8].isdigit() and 'T' in p.name)[-1]
    (run/'MUTATION_PROBE.txt').write_text('Mutant: inverted the obstruction-visibility predicate\nCommand: '+' '.join(cmd)+'\nExit: '+str(r.returncode)+'\n'+r.stdout,encoding='utf8')
    print('Mutation detected:',r.returncode!=0)
    print('Failing test names:')
    for line in r.stdout.splitlines():
        if 'FAIL:' in line or 'FAIL (' in line:print(line)
    if r.returncode==0:raise SystemExit('ERROR: mutant survived')
