"""Detector catalogue (library) contract fg-detector-library/1  (Rev G, owner-approved).

Each entry is the engineer-supplied performance basis for one detector model at
one sensitivity setting. Coverage runs use ONLY the entry explicitly assigned to a
detector (F03): there is no default/generic cone. Results depend entirely on the
data entered here. Entries flagged EXAMPLE VALUES must be replaced by verified
manufacturer data before project use.

Flame entries carry a range-vs-off-axis-angle contour table: rows of
(off_axis_deg, range_m) with off_axis_deg strictly increasing from 0. Range at
intermediate angles is linearly interpolated; beyond the last row (or outside the
horizontal/vertical field of view) the detector does not respond.
"""
from __future__ import annotations
import csv,io,json,math
from fgmapping.domain.scene import canonical,content_hash

CONTRACT='fg-detector-library/1'
TYPES=('FLAME','POINT_GAS','OPEN_PATH')
DATA_STATUS=('EXAMPLE VALUES - replace with manufacturer data','DATASHEET - to be verified','MANUFACTURER DATA - verified by engineer','USER DATA - to be verified')
KEYS={'contract','id','manufacturer','model','detector_type','technology','fuel_or_gas','target_fire','sensitivity_setting','fov','contour','alarm_threshold','path_length_m','mounting','source','notes'}
CSV_HEADERS=('id','manufacturer','model','detector_type','technology','fuel_or_gas','target_fire_description','target_fire_kw','target_fire_area_m2','sensitivity_setting','fov_horizontal_deg','fov_vertical_deg','contour','alarm_threshold','alarm_threshold_units','path_min_m','path_max_m','mounting','source_title','source_revision','source_page','data_status','notes')

def _text(v,name,required=True):
    if not isinstance(v,str) or (required and not v.strip()):raise ValueError('Library field '+name+' must be explicit text')
    return v
def _num(v,name,low=None,high=None,positive=False):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError('Library field '+name+' must be a finite number')
    if positive and v<=0 or low is not None and v<low or high is not None and v>high:raise ValueError('Library field '+name+' out of range')
    return float(v)

def validate_entry(p):
    if not isinstance(p,dict) or set(p)!=KEYS or p['contract']!=CONTRACT:raise ValueError('Closed detector library contract fg-detector-library/1 required')
    for k in ('id','manufacturer','model','technology','fuel_or_gas','sensitivity_setting','mounting'):_text(p[k],k)
    _text(p['notes'],'notes',False)
    if p['detector_type'] not in TYPES:raise ValueError('Library detector_type must be FLAME, POINT_GAS or OPEN_PATH')
    s=p['source']
    if not isinstance(s,dict) or set(s)!={'title','revision','page','data_status'}:raise ValueError('Library source title/revision/page/data_status required')
    for k in ('title','revision','page'):_text(s[k],'source.'+k)
    if s['data_status'] not in DATA_STATUS:raise ValueError('Library data_status must be one of: '+'; '.join(DATA_STATUS))
    t=p['detector_type']
    if t=='FLAME':
        tf=p['target_fire']
        if not isinstance(tf,dict) or set(tf)!={'description','heat_release_kw','area_m2'}:raise ValueError('Flame entry target_fire description/heat_release_kw/area_m2 required')
        _text(tf['description'],'target_fire.description');_num(tf['heat_release_kw'],'target_fire.heat_release_kw',positive=True)
        if tf['area_m2'] is not None:_num(tf['area_m2'],'target_fire.area_m2',positive=True)
        fov=p['fov']
        if not isinstance(fov,dict) or set(fov)!={'horizontal_deg','vertical_deg'}:raise ValueError('Flame entry FOV horizontal/vertical required')
        for k in fov:_num(fov[k],'fov.'+k,positive=True,high=180)
        c=p['contour']
        if not isinstance(c,list) or not 2<=len(c)<=181:raise ValueError('Flame entry needs a contour table of 2..181 (off_axis_deg, range_m) rows; no generic cone is substituted')
        last=-1
        for r in c:
            if not isinstance(r,list) or len(r)!=2:raise ValueError('Contour rows are [off_axis_deg, range_m]')
            a=_num(r[0],'contour angle',0,90);_num(r[1],'contour range',0,1000)
            if a<=last:raise ValueError('Contour angles must increase strictly')
            last=a
        if c[0][0]!=0:raise ValueError('Contour table must start at 0 degrees off-axis')
        if c[0][1]<=0:raise ValueError('On-axis contour range must be positive')
        if p['alarm_threshold'] is not None or p['path_length_m'] is not None:raise ValueError('Flame entry has no gas threshold/path length')
    else:
        if p['target_fire'] is not None or p['fov'] is not None or p['contour'] is not None:raise ValueError('Gas entry has no flame target/FOV/contour')
        th=p['alarm_threshold'];units='%LEL' if t=='POINT_GAS' else 'LEL.m'
        if not isinstance(th,dict) or set(th)!={'value','units'} or th['units']!=units:raise ValueError(t+' alarm_threshold {value, units:'+units+'} required')
        _num(th['value'],'alarm_threshold.value',positive=True,high=100 if t=='POINT_GAS' else 1000)
        pl=p['path_length_m']
        if t=='POINT_GAS':
            if pl is not None:raise ValueError('Point gas entry has no path length')
        else:
            if not isinstance(pl,dict) or set(pl)!={'min','max'}:raise ValueError('Open-path entry path_length_m {min,max} required')
            if _num(pl['min'],'path min',0)>=_num(pl['max'],'path max',positive=True):raise ValueError('Open-path min path must be below max')
    return json.loads(canonical(p))

def contour_range(entry,off_axis_deg):
    """Linear interpolation of the supplied contour; 0 beyond the table."""
    c=entry['contour']
    if off_axis_deg<0:raise ValueError('Off-axis angle is nonnegative')
    if off_axis_deg>c[-1][0]:return 0.
    for (a0,r0),(a1,r1) in zip(c,c[1:]):
        if a0<=off_axis_deg<=a1:return r0+(r1-r0)*(off_axis_deg-a0)/(a1-a0)
    return float(c[0][1])

def _f(v,name):
    try:return float(v)
    except (TypeError,ValueError):raise ValueError('Numeric library cell required: '+name)

def entry_from_row(r):
    """CSV/XLSX row (CSV_HEADERS) -> validated entry. Contour cell: '0:60;15:55;30:45'."""
    if set(r)!=set(CSV_HEADERS):raise ValueError('Library sheet headers must be exactly: '+','.join(CSV_HEADERS))
    t=r['detector_type'].strip()
    flame=t=='FLAME'
    contour=None
    if flame:
        contour=[]
        for part in r['contour'].split(';'):
            if not part.strip():continue
            a,_,b=part.partition(':');contour.append([_f(a,'contour angle'),_f(b,'contour range')])
    blank=lambda k:not str(r[k]).strip()
    p={'contract':CONTRACT,'id':r['id'].strip(),'manufacturer':r['manufacturer'],'model':r['model'],'detector_type':t,'technology':r['technology'],'fuel_or_gas':r['fuel_or_gas'],
       'target_fire':{'description':r['target_fire_description'],'heat_release_kw':_f(r['target_fire_kw'],'target_fire_kw'),'area_m2':None if blank('target_fire_area_m2') else _f(r['target_fire_area_m2'],'area')} if flame else None,
       'sensitivity_setting':r['sensitivity_setting'],'fov':{'horizontal_deg':_f(r['fov_horizontal_deg'],'fov h'),'vertical_deg':_f(r['fov_vertical_deg'],'fov v')} if flame else None,
       'contour':contour,'alarm_threshold':None if flame else {'value':_f(r['alarm_threshold'],'alarm_threshold'),'units':r['alarm_threshold_units'].strip()},
       'path_length_m':{'min':_f(r['path_min_m'],'path min'),'max':_f(r['path_max_m'],'path max')} if t=='OPEN_PATH' else None,
       'mounting':r['mounting'],'source':{'title':r['source_title'],'revision':r['source_revision'],'page':r['source_page'],'data_status':r['data_status'].strip()},'notes':r['notes']}
    return validate_entry(p)

def entry_to_row(p):
    p=validate_entry(p);tf=p['target_fire'] or {};fov=p['fov'] or {};th=p['alarm_threshold'] or {};pl=p['path_length_m'] or {}
    g=lambda d,k:'' if d.get(k) is None else repr(d[k]) if isinstance(d[k],float) else str(d[k])
    return {'id':p['id'],'manufacturer':p['manufacturer'],'model':p['model'],'detector_type':p['detector_type'],'technology':p['technology'],'fuel_or_gas':p['fuel_or_gas'],
            'target_fire_description':tf.get('description',''),'target_fire_kw':g(tf,'heat_release_kw'),'target_fire_area_m2':g(tf,'area_m2'),'sensitivity_setting':p['sensitivity_setting'],
            'fov_horizontal_deg':g(fov,'horizontal_deg'),'fov_vertical_deg':g(fov,'vertical_deg'),'contour':';'.join(f'{a:g}:{b:g}' for a,b in (p['contour'] or [])),
            'alarm_threshold':g(th,'value'),'alarm_threshold_units':th.get('units',''),'path_min_m':g(pl,'min'),'path_max_m':g(pl,'max'),'mounting':p['mounting'],
            'source_title':p['source']['title'],'source_revision':p['source']['revision'],'source_page':p['source']['page'],'data_status':p['source']['data_status'],'notes':p['notes']}

def parse_library(raw,fmt):
    """CSV or XLSX (single sheet 'Library', literal values only) -> list of entries."""
    if len(raw)>8_000_000:raise ValueError('Library file exceeds 8 MB budget')
    from fgmapping.domain.import_guards import xlsx_preflight,stream_rows,unique_headers
    if fmt=='CSV':
        text=raw.decode('utf-8-sig',errors='strict');reader=csv.reader(io.StringIO(text,newline=''),strict=True)
        try:head=unique_headers(next(reader))
        except StopIteration:raise ValueError('Empty library CSV')
        if set(head)!=set(CSV_HEADERS) or len(head)!=len(CSV_HEADERS):raise ValueError('Library CSV headers must be exactly: '+','.join(CSV_HEADERS))
        rows=[]
        for n,v in enumerate(reader,2):
            if n>5001:raise ValueError('Library CSV exceeds 5000 data rows')
            if not any(x.strip() for x in v):continue
            if len(v)!=len(head):raise ValueError('Column count mismatch at library CSV row %d' % n)
            rows.append(dict(zip(head,v)))
    elif fmt=='XLSX':
        from openpyxl import load_workbook
        xlsx_preflight(raw,max_rows=5001,max_cols=len(CSV_HEADERS))
        wb=load_workbook(io.BytesIO(raw),read_only=True,data_only=False,keep_links=False)
        try:
            if wb.sheetnames!=['Library']:raise ValueError("Library workbook must contain exactly one sheet named 'Library'")
            cells=stream_rows(wb['Library'],5001,len(CSV_HEADERS))
            if any(c.data_type in ('f','e') for row in cells for c in row):raise ValueError('Formulas are not accepted in library sheets')
            values=[[c.value for c in row] for row in cells]
        finally:wb.close()
        if not values:raise ValueError('Empty library sheet')
        head=unique_headers(['' if v is None else v for v in values[0]])
        if head!=list(CSV_HEADERS):raise ValueError('Library XLSX headers must be exactly: '+','.join(CSV_HEADERS))
        rows=[]
        for v in values[1:]:
            if all(x is None or str(x).strip()=='' for x in v):continue
            if any(isinstance(x,str) and x.startswith('=') for x in v):raise ValueError('Formulas are not accepted in library sheets')
            rows.append({h:('' if x is None else repr(x) if isinstance(x,float) else str(x)) for h,x in zip(head,v)})
    else:raise ValueError('Library format must be CSV or XLSX')
    entries=[entry_from_row(r) for r in rows]
    if not entries or len({e['id'] for e in entries})!=len(entries):raise ValueError('Nonempty library with unique IDs required')
    return entries

def write_csv(entries):
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=CSV_HEADERS,lineterminator='\n');w.writeheader()
    for e in entries:w.writerow(entry_to_row(e))
    return out.getvalue().encode('utf8')

def entry_hash(p):return content_hash(validate_entry(p))
