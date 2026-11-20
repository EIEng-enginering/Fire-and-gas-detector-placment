"""Rev H (F17): shared, bounded preflight for CSV/XLSX imports (library and register imports).
All checks run BEFORE the workbook is materialised: zip member count, total expanded size,
per-member compression ratio, declared sheet dimension; rows/columns are then streamed in
read-only mode with hard caps. CSV headers must be unique."""
from __future__ import annotations
import io,re,zipfile
DIM=re.compile(rb'<(?:\w+:)?dimension[^>]*\bref="([A-Z]+)?(\d+)?(?::([A-Z]+)(\d+))?"')

def _col(letters):
    n=0
    for ch in letters.decode() if isinstance(letters,bytes) else letters:n=n*26+(ord(ch)-64)
    return n

def xlsx_preflight(raw,max_expanded=32_000_000,max_members=200,max_ratio=200,max_rows=2001,max_cols=64):
    try:z=zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as exc:raise ValueError('XLSX is not a valid zip container') from exc
    with z:
        infos=z.infolist()
        if len(infos)>max_members:raise ValueError('Workbook member bound exceeded (%d > %d)' % (len(infos),max_members))
        if sum(i.file_size for i in infos)>max_expanded:raise ValueError('Workbook expanded-size bound exceeded')
        for i in infos:
            if i.file_size>1_000_000 and i.compress_size and i.file_size/i.compress_size>max_ratio:raise ValueError('Workbook member compression ratio bound exceeded: '+i.filename)
        for i in infos:
            if i.filename.startswith('xl/worksheets/') and i.filename.endswith('.xml'):
                with z.open(i) as f:head=f.read(8192)
                m=DIM.search(head)
                if m and m.group(4):
                    if int(m.group(4))>max_rows or _col(m.group(3))>max_cols:raise ValueError('Workbook declared dimension exceeds row/column bound')
    return True

def stream_rows(sheet,max_rows,max_cols):
    out=[]
    for n,cells in enumerate(sheet.iter_rows(),1):
        if n>max_rows:raise ValueError('Workbook exceeds row bound (%d)' % max_rows)
        cells=list(cells)
        if len(cells)>max_cols:raise ValueError('Workbook exceeds column bound (%d)' % max_cols)
        out.append(cells)
    return out

def unique_headers(headers):
    h=[str(x).strip() for x in headers]
    if len(h)!=len(set(h)):raise ValueError('Duplicate column headers are refused: '+', '.join(sorted({x for x in h if h.count(x)>1})))
    return h
