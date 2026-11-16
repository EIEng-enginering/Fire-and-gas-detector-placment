"""Immutable local source return builder with recursive source/archive audit.

This is a development pack, not public release or engineering qualification.
"""
from __future__ import annotations
import argparse,hashlib,io,json,re,sqlite3,tempfile,zipfile
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PREFIXES={'src','docs','contracts','tools','tests','examples','TEST_RESULTS','screenshots','OUTPUT_SAMPLES','ORIGINAL_ARCHIVES'}
FILES={'README_START_HERE.md','README.md','USER_GUIDE.md','HOW_TO_RUN.md','PROJECT_STATE.md','OPEN_ISSUES.md','CHANGELOG.md','REPORT.md','DEVIATIONS.md','requirements-lock.txt','requirements-reports.txt','pyproject.toml','setup.ps1','run.ps1','RUN_LOCAL.ps1','FILE_MAP.md','NEXT_WORK_PROMPT.txt','SOURCE_FILES.json','PACK_SCAN.json','SHA256SUMS.txt'}
PATTERNS=[r'\bsk-[a-zA-Z0-9_-]{20,}',r'\bghp_[a-zA-Z0-9]{25,}',r'AKIA[0-9A-Z]{16}',r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',r'(?i)authorization\s*:\s*bearer\s+[a-zA-Z0-9._-]{15,}']
TEXT={'.py','.md','.txt','.json','.toml','.ps1','.sql','.csv'}
BINARY={'.zip','.fgcase','.png','.pdf','.docx','.xlsx'}

def sha(raw):return hashlib.sha256(raw).hexdigest()
# Owner-supplied predecessor exceeds the ordinary file bound. Only these exact
# preserved bytes are permitted as an exception, not arbitrary large inputs.
PINNED_PREDECESSOR={'ORIGINAL_ARCHIVES/FG_MAPPING_RETURN_REV_D_20261116.zip':'e85590a6bb32e2366edf45e693112b509e2bdec1e72a7107a9a0375e8e4ff964'}
def scan(name,raw,depth=0):
    suffix=Path(name).suffix.lower()
    if len(raw)>50_000_000 and not (len(raw)<=64_000_000 and PINNED_PREDECESSOR.get(name)==sha(raw)):raise ValueError('File exceeds pack budget: '+name)
    if suffix in TEXT:
        text=raw.decode('utf8')
        if any(re.search(p,text) for p in PATTERNS):raise ValueError('Credential-like pattern: '+name)
    elif suffix not in BINARY:raise ValueError('Unapproved file type: '+name)
    if suffix=='.csv':
        import csv
        rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        if not rows or any(r.get('data_class')!='SYNTHETIC' for r in rows):raise ValueError('CSV must declare SYNTHETIC rows: '+name)
    if suffix=='.fgcase':
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'audit.sqlite';p.write_bytes(raw)
            with closing(sqlite3.connect(p)) as con, con:
                if con.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Case integrity: '+name)
                if not con.execute('SELECT name FROM case_info').fetchone()[0].startswith('SYNTHETIC'):raise ValueError('Case not labelled synthetic: '+name)
                if con.execute("SELECT count(*) FROM evidence WHERE data_class!='SYNTHETIC'").fetchone()[0]:raise ValueError('Non-synthetic evidence: '+name)
    if suffix=='.zip' and depth<3:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if z.testzip():raise ValueError('Nested ZIP CRC: '+name)
            if sum(i.file_size for i in z.infolist())>100_000_000:raise ValueError('Nested ZIP expanded-size budget')
            for member in z.infolist():
                if member.is_dir():continue
                parts=Path(member.filename).parts
                if '..' in parts or Path(member.filename).is_absolute():raise ValueError('Archive traversal path')
                scan(name+'!'+member.filename,z.read(member),depth+1)

def build(target):
    target=Path(target).resolve()
    if target.exists():raise ValueError('Return ZIP already exists; use a fresh revision name')
    items=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(ROOT)
        if '__pycache__' in rel.parts or p.suffix=='.pyc' or p.name.endswith('.writer.lock'):continue
        if len(rel.parts)==1 and rel.name in FILES or rel.parts[0] in PREFIXES:
            raw=p.read_bytes();scan(rel.as_posix(),raw);items.append((rel.as_posix(),raw))
    scanlog={'status':'PASS','scope':'Explicit path/type allowlist, recursive supplied ZIP CRC/secret scan, synthetic SQLite evidence classes, file-size budgets','files_scanned':len(items),'client_data':'No client input used; only supplied provenance archives and generated synthetic files','qualification':'Not engineering qualification','git_actions':'NONE'}
    (ROOT/'PACK_SCAN.json').write_text(json.dumps(scanlog,indent=2)+'\n')
    items=[(n,b) for n,b in items if n not in ('SHA256SUMS.txt','PACK_SCAN.json')]+[('PACK_SCAN.json',(ROOT/'PACK_SCAN.json').read_bytes())]
    manifest=''.join(sha(raw)+'  '+name+'\n' for name,raw in sorted(items))
    (ROOT/'SHA256SUMS.txt').write_text(manifest)
    items.append(('SHA256SUMS.txt',manifest.encode()))
    with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for name,raw in sorted(items):z.writestr(name,raw)
    with zipfile.ZipFile(target) as z:
        if z.testzip():raise ValueError('Return archive CRC failure')
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            expected,name=line.split('  ',1)
            if sha(z.read(name))!=expected:raise ValueError('Return archive hash mismatch: '+name)
    return {'path':str(target),'files':len(items),'bytes':target.stat().st_size,'sha256':sha(target.read_bytes()),'crc':'PASS','all_file_hashes':'PASS'}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('target');args=parser.parse_args();print(json.dumps(build(args.target),indent=2))
