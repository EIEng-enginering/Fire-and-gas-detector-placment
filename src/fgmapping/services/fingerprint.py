"""Rev H (F08): method implementation fingerprints from the FULL transitive import closure of
the method entry modules (static AST scan of fgmapping imports, including function-level
imports). Paths are relative to src/fgmapping with '/' separators; contents are LF-normalised
before SHA-256, so the fingerprint is independent of machine paths and checkout line endings.
The fingerprint is a hash of source files only (never of stored results), so it is not circular."""
from __future__ import annotations
import ast,hashlib
from pathlib import Path
from fgmapping.domain.scene import content_hash
SRC=Path(__file__).resolve().parents[1]
ENTRY={'ZONE_COVERAGE':('engine/coverage.py','engine/detection.py','services/coverage.py'),
       'SCENARIO_COVERAGE':('engine/coverage.py','engine/detection.py','services/coverage.py','engine/scenario_coverage.py','engine/scenarios.py','services/scenario_coverage.py'),
       'LAYOUT_OPTIONS':('engine/coverage.py','engine/detection.py','services/coverage.py','engine/scenario_coverage.py','engine/optimisation.py','services/scenario_coverage.py')}

def _module_file(root,name):
    parts=name.split('.')
    if parts[0]!='fgmapping':return None
    p=root.joinpath(*parts[1:])
    for c in (p.with_suffix('.py'),p/'__init__.py'):
        if c.is_file():return c
    return None

def dependency_closure(entries,root=SRC):
    root=Path(root);todo=[root/e for e in entries]+[root/'__init__.py'];seen=set()
    while todo:
        f=todo.pop()
        if f in seen or not f.is_file():continue
        seen.add(f)
        pkg=['fgmapping']+list(f.relative_to(root).parent.parts)
        for node in ast.walk(ast.parse(f.read_bytes())):
            names=[]
            if isinstance(node,ast.Import):names=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                base=node.module or ''
                if node.level:base='.'.join(pkg[:len(pkg)-node.level+1]+([base] if base else []))
                names=[base]+[base+'.'+a.name for a in node.names]
            for n in names:
                m=_module_file(root,n)
                if m:todo.append(m)
                # parent packages are executed on import
                for k in range(2,len(n.split('.'))):
                    pm=_module_file(root,'.'.join(n.split('.')[:k]))
                    if pm:todo.append(pm)
    return sorted(p.relative_to(root).as_posix() for p in seen)

def file_hashes(method,root=SRC):
    root=Path(root)
    return {n:hashlib.sha256((root/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for n in dependency_closure(ENTRY[method],root)}

def fingerprint(method,root=SRC):
    files=file_hashes(method,root);return files,content_hash(files)
