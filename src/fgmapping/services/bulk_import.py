"""Explicit CREATE/UPDATE synthetic detector/equipment CSV or XLSX import."""
import csv,io,zipfile,math
from fgmapping.services.preparation import staging,make_plan
from fgmapping.services import workspace as w
from fgmapping.errors import CaseError
HEADERS=('data_class','action','kind','id','evidence_id','detector_type','x','y','z','azimuth','elevation','roll','manufacturer','model','sensitivity','equipment_type','geometry_component_id')

def parse_rows(raw,format):
 if not isinstance(raw,bytes) or not raw or len(raw)>4_000_000:raise CaseError('IMPORT_SIZE','Nonempty source bytes up to 4 MB required')
 if format=='CSV':
  try:values=list(csv.reader(io.StringIO(raw.decode('utf-8-sig')),strict=True))
  except (UnicodeError,csv.Error) as exc:raise CaseError('CSV','Strict UTF-8 CSV required') from exc
 elif format=='XLSX':
  from openpyxl import load_workbook
  try:
   from fgmapping.domain.import_guards import xlsx_preflight
   try:xlsx_preflight(raw,max_rows=2001,max_cols=len(HEADERS))
   except ValueError as exc:raise CaseError('XLSX_SIZE',str(exc)) from exc
   wb=load_workbook(io.BytesIO(raw),read_only=True,data_only=False,keep_links=False)
   try:
    if wb.sheetnames!=['Registers']:raise CaseError('XLSX','Exactly one sheet named Registers required')
    sheet=wb['Registers']
    if sheet.max_row>2001 or sheet.max_column>len(HEADERS):raise CaseError('IMPORT_ROWS','Workbook exceeds row/column bound')
    values=[]
    for cells in sheet.iter_rows():
     if any(c.data_type=='f' or c.data_type=='e' for c in cells):raise CaseError('XLSX_FORMULA','Formula and error cells are refused; supply literal values')
     values.append([c.value if c.value is not None else '' for c in cells])
   finally:wb.close()
  except CaseError:raise
  except Exception as exc:raise CaseError('XLSX','Workbook could not be parsed') from exc
 else:raise CaseError('IMPORT_FORMAT','Explicit CSV or XLSX required')
 if not 2<=len(values)<=2001:raise CaseError('IMPORT_ROWS','1..2000 explicit data rows required')
 headers=[str(x).strip() for x in values[0]]
 if len(headers)!=len(set(headers)) or set(headers)!=set(HEADERS):raise CaseError('IMPORT_HEADER','Closed unique header set required; use supplied template')
 rows=[];seen=set()
 for line,cells in enumerate(values[1:],2):
  if len(cells)!=len(headers):raise CaseError('IMPORT_ROW','Column count mismatch at row '+str(line))
  row={h:str(v).strip() for h,v in zip(headers,cells)}
  if row['data_class']!='SYNTHETIC' or row['action'] not in ('CREATE','UPDATE') or row['kind'] not in ('DETECTOR','EQUIPMENT'):raise CaseError('IMPORT_SCOPE','SYNTHETIC with explicit CREATE/UPDATE and DETECTOR/EQUIPMENT required at row '+str(line))
  if not row['id'] or row['id'] in seen:raise CaseError('IMPORT_DUPLICATE','Nonempty unique IDs required across the whole source at row '+str(line))
  if any(len(v)>2000 or any(ord(c)<32 for c in v) for v in row.values()):raise CaseError('IMPORT_CELL','Cell text bound/control-character violation')
  seen.add(row['id']);rows.append(row)
 return rows

def prepare_bulk(s,raw,format):
 rows=parse_rows(raw,format);stage=staging(s);summary=[]
 try:
  for n,r in enumerate(rows,2):
   evidence=w.row(stage,'evidence',r['evidence_id'])
   if evidence is None or evidence['data_class']!='SYNTHETIC':raise CaseError('EVIDENCE','Existing SYNTHETIC evidence required at source row '+str(n))
   try:position={k:float(r[k]) for k in ('x','y','z')}
   except ValueError as exc:raise CaseError('IMPORT_NUMBER','Explicit SI XYZ required at row '+str(n)) from exc
   if any(not math.isfinite(v) for v in position.values()):raise CaseError('IMPORT_NUMBER','Finite SI XYZ required')
   if r['kind']=='DETECTOR':
    if r['equipment_type'] or r['geometry_component_id']:raise CaseError('IMPORT_FIELDS','Equipment-only fields must be blank for detectors')
    try:angles={k:float(r[k]) for k in ('azimuth','elevation','roll')}
    except ValueError as exc:raise CaseError('IMPORT_NUMBER','Explicit detector orientation required') from exc
    values={**r,**position,**angles}
    changes=w.detector_plan(stage,values,None,create=r['action']=='CREATE',place_marker=False)
    with stage.con:w._apply(stage,changes)
   else:
    if any(r[k] for k in ('detector_type','azimuth','elevation','roll','manufacturer','model','sensitivity')):raise CaseError('IMPORT_FIELDS','Detector-only fields must be blank for equipment')
    if not r['equipment_type']:raise CaseError('IMPORT_FIELDS','Equipment type reference required')
    payload={'description':r['equipment_type'],'position':[position[k] for k in ('x','y','z')],'geometry_component_id':r['geometry_component_id']}
    w.record_command(stage,r['id'],'EQUIPMENT',payload,r['evidence_id'],'AUTOMATION_ENGINE',create=r['action']=='CREATE')
   summary.append({'source_row':n,'kind':r['kind'],'action':r['action'],'id':r['id'],'evidence_id':r['evidence_id']})
  return make_plan(s,stage,'BULK_REGISTER',raw,format,{'rows':summary,'count':len(summary),'units':'m / deg','qualification':'UNVERIFIED'})
 finally:stage.con.close()
