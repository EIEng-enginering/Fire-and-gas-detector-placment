"""Run distinct test suites as separate child processes; capture evidence."""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
run_name=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out=ROOT/'TEST_RESULTS'/run_name
out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,PYTHONPATH=str(ROOT/'src')+os.pathsep+str(ROOT),PYTHONDONTWRITEBYTECODE='1')
all_good=True
for suite in ['unit','integration','acceptance']:
    cmd=[sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'tests'/suite),'-v']
    r=subprocess.run(cmd,env=env,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/f'{suite}.txt').write_text('COMMAND: '+' '.join(cmd)+'\n'+r.stdout+'\nEXIT: '+str(r.returncode)+'\n',encoding='utf8')
    print(suite, 'PASS' if r.returncode==0 else 'FAIL', 'code',r.returncode)
    print(r.stdout[-1200:])
    all_good=all_good and r.returncode==0
(out/'RUN_MANIFEST.txt').write_text('Host: '+sys.platform+'\nPython: '+sys.version+'\nVerified Windows Qt? NO\nAll tests pass: '+str(all_good)+'\n',encoding='utf8')
print('EVIDENCE_DIR:',out)
raise SystemExit(0 if all_good else 1)
