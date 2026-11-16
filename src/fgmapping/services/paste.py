"""Bounded TSV preview parser. Actual edits use workspace's atomic command."""
import csv,io,math
from fgmapping.errors import CaseError

def detector_paste_preview(visible_rows,text,start_row,start_col):
 if len(text)>1_000_000:raise CaseError('PASTE','Clipboard exceeds 1 MB development budget')
 matrix=list(csv.reader(io.StringIO(text),delimiter='\t'))
 if not matrix or not matrix[0] or len(matrix)>10000:raise CaseError('PASTE','Empty paste or row budget exceeded')
 width=len(matrix[0])
 if any(len(r)!=width for r in matrix):raise CaseError('PASTE','Paste must be rectangular')
 columns={1:'detector_type',2:'x',3:'y',4:'z'}
 if start_row<0 or start_row+len(matrix)>len(visible_rows) or any(c not in columns for c in range(start_col,start_col+width)):raise CaseError('PASTE','Paste may edit existing Type and XYZ columns only; IDs/evidence/review remain protected')
 patches=[];preview=[]
 for offset,values in enumerate(matrix):
  source=visible_rows[start_row+offset];patch={'id':source['id']}
  for delta,value in enumerate(values):
   field=columns[start_col+delta]
   if field=='detector_type':
    converted=value.strip()
    if converted not in ('FLAME','POINT_GAS','OPEN_PATH','ULTRASONIC'):raise CaseError('TYPE','Pasted detector type is not recognised')
   else:
    try:converted=float(value)
    except ValueError as exc:raise CaseError('COORDINATE','Pasted XYZ must be numeric') from exc
    if not math.isfinite(converted) or abs(converted)>1e7:raise CaseError('COORDINATE','Pasted coordinates outside development numerical domain')
   patch[field]=converted;preview.append((source['id'],field,str(source[field]),str(converted)))
  patches.append(patch)
 return patches,preview
