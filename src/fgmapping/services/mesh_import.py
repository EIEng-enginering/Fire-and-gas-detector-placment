"""Bounded, offline mesh ingestion in a killable child. No external references.

Supports triangulated OBJ and ASCII STL only. STEP and binary STL fail explicitly.
Child-process isolation is NOT an OS security sandbox. Self-intersections remain
unevaluated and every imported mesh is UNVERIFIED.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from fgmapping.domain.scene import Frame, Mesh

MAX_BYTES=4_000_000

def parse_mesh(raw,format,frame):
    if len(raw)>MAX_BYTES: raise ValueError('Mesh exceeds 4 MB development input budget')
    text=raw.decode('utf-8',errors='strict'); vertices=[]; faces=[]
    if format=='.obj':
        for line in text.splitlines():
            fields=line.split()
            if not fields or fields[0].startswith('#'):continue
            if fields[0]=='v':
                if len(fields)!=4:raise ValueError('OBJ vertex must have XYZ only')
                vertices.append(tuple(float(x) for x in fields[1:]))
            elif fields[0]=='f':
                if len(fields)!=4:raise ValueError('Only triangulated OBJ faces are supported')
                face=[]
                for value in fields[1:]:
                    idx=int(value.split('/')[0])
                    if idx==0:raise ValueError('OBJ indices start at 1')
                    face.append(idx-1 if idx>0 else len(vertices)+idx)
                faces.append(tuple(face))
            elif fields[0] in ('mtllib','usemtl'):raise ValueError('OBJ external materials are unsupported')
            elif fields[0] not in ('o','g','s','vn','vt'):raise ValueError('Unsupported OBJ instruction')
    elif format=='.stl':
        if not text.lstrip().startswith('solid') or 'endsolid' not in text:raise ValueError('ASCII STL required; binary STL unsupported')
        index={}; current=[]; inside=False; normal=None; found=0
        for line in text.splitlines():
            f=line.split()
            if not f:continue
            if f[0]=='facet':
                if inside or len(f)!=5 or f[1]!='normal':raise ValueError('Malformed STL facet')
                normal=tuple(float(x) for x in f[2:]); inside=True; current=[]
                if any(not math.isfinite(x) for x in normal):raise ValueError('Nonfinite STL normal')
            elif f[0]=='vertex':
                if not inside or len(f)!=4:raise ValueError('Malformed STL vertex')
                v=tuple(float(x) for x in f[1:])
                if v not in index:index[v]=len(vertices);vertices.append(v)
                current.append(index[v])
            elif f[0]=='endfacet':
                if not inside or len(current)!=3:raise ValueError('STL facet must contain three vertices')
                faces.append(tuple(current));inside=False;found+=1
            elif f[0] not in ('solid','endsolid','outer','endloop'):raise ValueError('Unsupported STL syntax')
        if inside or not found:raise ValueError('Incomplete STL')
    else:raise ValueError('Supported formats: triangulated OBJ and ASCII STL; STEP not implemented')
    # Normalize once; original frame and bytes are retained by caller's manifest.
    mesh=Mesh(tuple(frame.world(p) for p in vertices),tuple(faces))
    return {'mesh':{'vertices':mesh.vertices,'faces':mesh.faces},'mesh_sha256':mesh.sha256,
            'source_sha256':hashlib.sha256(raw).hexdigest(),'diagnostics':mesh.diagnostics(),
            'frame':{'id':frame.id,'units':frame.units,'datum':frame.datum,'handedness':frame.handedness,'matrix':frame.matrix}}

class ImportJob:
    def __init__(self,path,frame,seconds=10):
        path=Path(path)
        if path.stat().st_size>MAX_BYTES:raise ValueError('Mesh exceeds 4 MB development input budget')
        if not 0<seconds<=60:raise ValueError('Worker timeout must be in (0,60] seconds')
        self.seconds=seconds
        self._stdout=tempfile.TemporaryFile();self._stderr=tempfile.TemporaryFile()
        self.process=subprocess.Popen([sys.executable,'-B','-m','fgmapping.services.mesh_import','--worker',str(path.resolve()),json.dumps(frame.__dict__)],stdout=self._stdout,stderr=self._stderr)
    def cancel(self):
        if self.process.poll() is None:self.process.kill()
        self.process.wait()
        self._stdout.close();self._stderr.close()
    def result(self):
        try:self.process.wait(timeout=self.seconds)
        except subprocess.TimeoutExpired:
            self.cancel();raise ValueError('Mesh import timed out; worker terminated')
        self._stdout.seek(0);self._stderr.seek(0)
        out=self._stdout.read(32_000_001);err=self._stderr.read(4000)
        self._stdout.close();self._stderr.close()
        if len(out)>32_000_000:raise ValueError('Worker output exceeded development budget')
        if self.process.returncode:raise ValueError('Mesh import refused: '+err.decode('utf8')[-1000:])
        return json.loads(out)

if __name__=='__main__':
    try:
        # Optional POSIX limits; Windows requires a future Job Object limit.
        if os.name=='posix':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
            resource.setrlimit(resource.RLIMIT_CPU,(10,10))
        path=Path(sys.argv[2]); frame=Frame(**json.loads(sys.argv[3]))
        with path.open('rb') as f:raw=f.read(MAX_BYTES+1)
        print(json.dumps(parse_mesh(raw,path.suffix.lower(),frame),allow_nan=False))
    except Exception as exc:
        print(str(exc),file=sys.stderr);sys.exit(2)
