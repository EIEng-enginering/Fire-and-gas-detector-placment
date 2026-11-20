"""M6 coverage report: JSON / Excel / Word / PDF with method, inputs, hashes and heatmap figures.

Rev H: every output carries the run lifecycle state (COMPUTED - UNREVIEWED unless an engineer
review record exists, F12), the used library entries with content hashes and EXAMPLE status
per run (F09/F22; distinct library versions are never merged by ID), figures drawn from each
run's own stored scene with STALE banners (F09), literal-text Excel cells (F11), validated
contained output names with staged exclusive creation (F10) and readable layouts (F21).
"""
from __future__ import annotations
import hashlib,io,json
from pathlib import Path
from fgmapping.domain.scene import canonical,content_hash
from fgmapping.services import coverage as cov
from fgmapping.services import lifecycle
from fgmapping.services import workspace as w
from fgmapping.services.case import utc_now
from fgmapping.services.safe_paths import StagedFolder,validate_name
LABEL='COMPUTED - UNREVIEWED development results - not independently verified'
DISCLAIMER=('Results depend entirely on the detector library data, zones, target fire / design cloud and geometry entered by the user. '
            'Library entries marked EXAMPLE VALUES must be replaced by verified manufacturer data before project use. '
            'No independent certification and no standards conformity (ISA-TR84.00.07, DNV-RP-A102, ISO 13702) is claimed. '
            'Coverage fractions are sampled-cell fractions (one representative free point per grid cell, weighted by exact or bounded free measure). '
            'Geographic gas results use a fixed design cloud and are not dispersion results. Detector coverage is not FGS effectiveness, availability or risk reduction.')

def pct(v):return '-' if v is None else '%.1f %%' % (100*v)

def _lib_refs(lib,run_id):
    return [{'id':k,'sha256':content_hash(v),'data_status':v['source']['data_status'],'example':v['source']['data_status'].startswith('EXAMPLE'),'run_id':run_id} for k,v in sorted(lib.items())]

def coverage_snapshot(session,px_per_m=20,max_slices=3):
    from fgmapping.services.heatmap import run_figures
    from fgmapping.services.findings import study_findings
    from fgmapping.services.geometry import get_scene
    cov.require_coverage(session)
    scene=get_scene(session);zones=[];figures=[];versions={};detectors={}
    def add_lib(lib,run_id):
        for k,v in lib.items():
            key=(k,content_hash(v));versions.setdefault(key,{'entry':v,'used_by':[]})['used_by'].append(run_id)
        return _lib_refs(lib,run_id)
    for z,run in sorted(cov.latest_runs(session).items()):
        res=json.loads(run['result_json']);env=json.loads(run['input_json']);state=lifecycle.run_state(session,run)
        refs=add_lib(env['library'],run['id'])
        for d in env['detectors']:
            key=(d['id'],content_hash(d));detectors.setdefault(key,dict(d,used_by_runs=[],zones=[]))
            detectors[key]['used_by_runs'].append(run['id']);detectors[key]['zones'].append(z)
        zones.append({'zone_id':z,'run_id':run['id'],'state':state['currency'],'lifecycle':state['lifecycle'],'status_label':state['label'],'review':state['review'],'utc':run['utc'],'actor':run['actor'],'input_hash':run['input_hash'],'result_sha256':lifecycle.result_hash(run),'result':res,
                      'library_used':refs,'example_library_used':[r['id'] for r in refs if r['example']],
                      'setup':env['setup'],'zone':env['zone'],'scene_sha256':env['scene_sha256'],'implementation_sha256':env['implementation_sha256'],'software_version':env['software_version'],'excluded_component_ids':env['excluded_component_ids'],
                      'sensitivity':env.get('sensitivity',{'enabled':False,'range_factors':[]})})
        for f in run_figures(session,run,px_per_m,max_slices,currency=state['currency']):
            import base64;figures.append({**{k:v for k,v in f.items() if k!='png'},'run_id':run['id'],'lifecycle':state['lifecycle'],'library_used':refs,'png_base64':base64.b64encode(f['png']).decode(),'png_sha256':hashlib.sha256(f['png']).hexdigest()})
    from fgmapping.services import scenario_coverage as scs
    studies=[]
    for r in scs.study_runs(session):
        env=json.loads(r['input_json']);state=lifecycle.run_state(session,r)
        libs={}
        for zenv in (env.get('zones') or {}).values():libs.update({k:v for k,v in zenv['library'].items()})
        if env.get('zone'):libs.update(env['zone']['library'])
        refs=add_lib(libs,r['id'])
        crefs=add_lib(env.get('candidate_library') or {},r['id']) if r['method']=='LAYOUT_OPTIONS' else []
        studies.append({'run_id':r['id'],'method':r['method'],'method_version':r['method_version'],'zone_id':r['zone_id'],'state':state['currency'],'lifecycle':state['lifecycle'],'status_label':state['label'],'utc':r['utc'],'actor':r['actor'],'input_hash':r['input_hash'],
                        'result':json.loads(r['result_json']),'library_used':refs,'candidate_library_used':crefs,'example_library_used':sorted({x['id'] for x in refs+crefs if x['example']})})
    library=[dict(v['entry'],content_sha256=k[1],used_by_runs=sorted(set(v['used_by']))) for k,v in sorted(versions.items())]
    example=sorted({e['id'] for e in library if e['source']['data_status'].startswith('EXAMPLE')})
    findings=[f for f in study_findings(session) if f['id'].startswith(('COVERAGE-','LIBRARY-'))]
    states=sorted({z['lifecycle'] for z in zones}|{st['lifecycle'] for st in studies})
    overall='DEVELOPMENT - '+(' / '.join(states) if states else 'NO RUNS')+' - not independently verified'
    snap={'report':'fg-coverage-report/2','label':LABEL,'review_status':overall,'disclaimer':DISCLAIMER,'case':session.name(),'software_version':__import__('fgmapping').__version__,'generated_utc':utc_now(),
          'scene_sha256':scene.sha256 if scene else None,'example_library_entries':example,'zones':zones,'detectors':[detectors[k] for k in sorted(detectors)],'library':library,
          'findings':findings,'studies':studies,'figures':figures,'method_document':'docs/METHOD_AND_TOLERANCES_REV_H.md'}
    snap['content_sha256']=content_hash({k:v for k,v in snap.items() if k not in ('generated_utc',)})
    return snap

def summary_rows(snap):
    out=[]
    for z in snap['zones']:
        r=z['result'];fr=r['fractions']
        out.append([z['zone_id'],r['zone_kind'],r['method_version'],z['state'],z['lifecycle'],'%.3f m %s' % (r['grid_spacing_m'],r['mode'].lower()),'%.2f %s' % (r['eligible_measure'],r['measure_unit']),'%.2f' % sum(r['excluded_measure'].values()),pct(fr['0ooN']),pct(fr['1ooN']),pct(fr['2ooN']),pct(fr['3ooN']),
                    '%dooN %s' % (r['voting_required'],pct(r['required_voting_fraction'])),'; '.join('%s %s: %s' % (k,v['target'],v['status']) for k,v in r['performance_targets'].items() if v['target']!='NOT SUPPLIED') or 'no user targets',
                    r['convergence']['status'],', '.join(z['example_library_used']) or 'none',z['run_id'],z['input_hash'][:16]])
    return out
SUMMARY_HEAD=['Zone','Kind','Method','Currency','Lifecycle','Grid','Eligible','Excluded','0ooN','1ooN','2ooN','3ooN','Voting','User targets','Grid check','EXAMPLE library','Run','Input hash']

def setup_text(s):
    if s['method']=='FLAME_GEOGRAPHIC':
        f=s['flame'];g=f['target_geometry']
        tg='point' if g['type']=='POINT' else 'cylinder D %.2f m x H %.2f m (%d x %d points)' % (g['diameter_m'],g['height_m'],g['rings']+1,g['levels'])
        return 'Target fire: %s %.0f kW, %s, min sampled-point visible fraction %.2f (equal-weight target sample points, not projected flame area or radiometric response), fire-size scaling %s' % (f['fuel'],f['heat_release_kw'],tg,f['min_visible_fraction'],f['fire_size_scaling'])
    gs=s['gas'];c=gs['cloud']
    return 'Design cloud: %s %s, %.0f %%LEL, detectors %s' % (gs['gas'],'sphere D %.1f m' % c['diameter_m'] if c['shape']=='SPHERE' else 'ellipsoid %s m' % c['axes_m'],gs['cloud_concentration_pct_lel'],'/'.join(gs['detector_types']))

def export_coverage_report(session,folder,name):
    validate_name(name)  # F10: refuse before any write
    snap=coverage_snapshot(session)
    if not snap['zones']:raise ValueError('No coverage runs stored')
    st=StagedFolder(folder,name)
    try:
        st.write_bytes(name+'.json',(json.dumps(snap,indent=1,sort_keys=True)+'\n').encode('utf8'))
        import base64
        figs=[]
        for i,f in enumerate(snap['figures']):
            fn='FIG_%02d_%s_z%.2f.png' % (i+1,f['zone_id'],f['slice_z']);st.write_bytes(fn,base64.b64decode(f['png_base64']));figs.append((st.path(fn),f))
        for ext,fn in (('xlsx',_xlsx),('docx',_docx),('pdf',_pdf)):
            buf=io.BytesIO()
            if ext=='xlsx':fn(snap,buf)
            else:fn(snap,figs,buf)
            st.write_bytes(name+'.'+ext,buf.getvalue())
        manifest={p.name:{'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(st.stage.iterdir()) if p.is_file()}
        st.write_bytes('MANIFEST.json',json.dumps({'label':LABEL,'review_status':snap['review_status'],'content_sha256':snap['content_sha256'],'files':manifest},indent=2).encode('utf8'))
        dest=st.publish()
    except BaseException:
        st.abort();raise
    return {'folder':str(dest),'files':sorted(str(dest/n) for n in manifest)+[str(dest/'MANIFEST.json')],'content_sha256':snap['content_sha256']}

def _append(ws,row,bold=False,red=False):
    """F11: every str value is written as a literal string cell (never a formula)."""
    from openpyxl.styles import Font,Alignment
    ws.append([None if v is None else v for v in row])
    for c in ws[ws.max_row]:
        if isinstance(c.value,str):c.data_type='s'
        c.alignment=Alignment(wrap_text=True,vertical='top')
        if bold or red:c.font=Font(bold=bold,color='B03A2E' if red else None)
    return ws.max_row

def _sheet(wb,title,head,widths):
    from openpyxl.worksheet.page import PageMargins
    ws=wb.create_sheet(title) if wb.worksheets[0].title!='Sheet' else wb.worksheets[0]
    ws.title=title;_append(ws,head,bold=True);ws.freeze_panes='A2';ws.print_title_rows='1:1'
    ws.page_setup.orientation='landscape';ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0;ws.sheet_properties.pageSetUpPr.fitToPage=True;ws.page_margins=PageMargins(left=.4,right=.4,top=.5,bottom=.5)
    from openpyxl.utils import get_column_letter
    for i,wd in enumerate(widths):ws.column_dimensions[get_column_letter(i+1)].width=wd
    return ws

def _xlsx(snap,path):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter
    wb=Workbook();ws=wb.active;ws.title='Summary'
    _append(ws,[snap['label']],bold=True,red=True);_append(ws,['Review status',snap['review_status']],bold=True,red=True)
    _append(ws,[snap['disclaimer']]);_append(ws,['Case',snap['case']]);_append(ws,['Software',snap['software_version']]);_append(ws,['Scene SHA-256',snap['scene_sha256']]);_append(ws,['Report content SHA-256',snap['content_sha256']])
    if snap['example_library_entries']:_append(ws,['WARNING','EXAMPLE library values used: '+', '.join(snap['example_library_entries'])+' - not for project design'],red=True)
    # F21: preamble text spans the table width (merged) so it does not wrap in a narrow column
    last=get_column_letter(len(SUMMARY_HEAD))
    for r in range(1,ws.max_row+1):
        vals=[c.value for c in ws[r] if c.value is not None];first='A' if len(vals)==1 else 'B'
        ws.merge_cells('%s%d:%s%d' % (first,r,last,r));ws.row_dimensions[r].height=max(15,15*(1+len(str(vals[-1]))//190))
    _append(ws,[]);hr=_append(ws,SUMMARY_HEAD,bold=True)
    for r in summary_rows(snap):
        n=_append(ws,r)
    ws.print_title_rows='%d:%d' % (hr,hr);ws.page_setup.orientation='landscape';ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0;ws.sheet_properties.pageSetUpPr.fitToPage=True
    from openpyxl.utils import get_column_letter
    for i,wd in enumerate([16,10,18,10,20,12,14,10,8,8,8,8,12,26,26,22,22,18]):ws.column_dimensions[get_column_letter(i+1)].width=wd
    ws.column_dimensions['A'].width=24
    s=_sheet(wb,'Zone setups',['Zone','Run','Lifecycle','Method','Grid (m)','Mode','Slices','Voting','Targets','Grid check setting','Sensitivity','Criterion reference','Target / cloud','Excluded components','Zone low','Zone high'],[16,22,20,18,9,9,12,8,22,22,16,26,40,22,16,16])
    for z in snap['zones']:
        st=z['setup'];_append(s,[z['zone_id'],z['run_id'],z['lifecycle'],st['method'],st['grid_spacing_m'],st['mode'],json.dumps(st['slice_elevations_m']),st['voting_required'],json.dumps(st['performance_targets']),json.dumps(st['convergence']),json.dumps(z['sensitivity']),st['criterion_reference'],setup_text(st),', '.join(z['excluded_component_ids']),json.dumps(z['zone']['low']),json.dumps(z['zone']['high'])])
    s=_sheet(wb,'Detectors',['ID','Used by runs','Zones','Type','X','Y','Z','Azimuth','Elevation','Roll','Library entry','Library SHA-256','EXAMPLE','Mount component','Receiver'],[14,22,14,10,8,8,8,9,9,8,22,20,9,16,22])
    refs={(r['run_id'],r['id']):r for z in snap['zones'] for r in z['library_used']}
    for d in snap['detectors']:
        ref=refs.get((d['used_by_runs'][0],d['library_id']),{})
        n=_append(s,[d['id'],', '.join(d['used_by_runs']),', '.join(d['zones']),d['detector_type'],*d['position'],d['azimuth'],d['elevation'],d['roll'],d['library_id'],ref.get('sha256','')[:16],'EXAMPLE' if ref.get('example') else '',d.get('mount_component_id') or '',json.dumps(d['receiver'])],red=bool(ref.get('example')))
        for c in s[n][4:10]:c.number_format='0.000'
    s=_sheet(wb,'Library used',['ID','Content SHA-256','Used by runs','Type','Technology','Fuel/gas','Rated fire kW','FOV H','FOV V','Contour deg:m','Threshold','Path m','Data status','Source','Revision','Page'],[22,20,30,10,10,10,9,7,7,26,12,16,30,30,9,7])
    for e in snap['library']:
        _append(s,[e['id'],e['content_sha256'][:16],', '.join(e['used_by_runs']),e['detector_type'],e['technology'],e['fuel_or_gas'],(e['target_fire'] or {}).get('heat_release_kw'),(e['fov'] or {}).get('horizontal_deg'),(e['fov'] or {}).get('vertical_deg'),';'.join('%g:%g' % tuple(r) for r in (e['contour'] or [])),
                  '' if not e['alarm_threshold'] else '%g %s' % (e['alarm_threshold']['value'],e['alarm_threshold']['units']),json.dumps(e['path_length_m']),e['source']['data_status'],e['source']['title'],e['source']['revision'],e['source']['page']],red=e['source']['data_status'].startswith('EXAMPLE'))
    s=_sheet(wb,'Per detector',['Zone','Run','Lifecycle','Detector','Sampled-cell fraction of eligible measure','EXAMPLE library in run'],[16,22,20,14,20,30])
    for z in snap['zones']:
        for d,v in z['result']['per_detector_fraction'].items():
            n=_append(s,[z['zone_id'],z['run_id'],z['lifecycle'],d,v,', '.join(z['example_library_used'])]);s.cell(n,5).number_format='0.0000'
    s=_sheet(wb,'Findings',['ID','Object','Severity','Message'],[30,18,10,100])
    for f in snap['findings']:_append(s,[f['id'],f['object_id'],f['severity'],f['message']])
    s=_sheet(wb,'Scenario studies',['Run','Method','Currency','Lifecycle','Zone(s)','Item','Detected / fraction','Votes / cost','Grid / basis','EXAMPLE library','Detail'],[22,16,9,20,18,18,16,10,30,26,50])
    for st in snap['studies']:
        r=st['result'];ex=', '.join(st['example_library_used']) or 'none'
        if st['method']=='SCENARIO_COVERAGE':
            _append(s,[st['run_id'],st['method_version'],st['state'],st['lifecycle'],st['zone_id'],'OVERALL',r['overall']['frequency_weighted_detected_fraction'],'','point tests at user scenario locations',ex,'frequency-weighted detected fraction (user frequencies)'])
            for x in r['scenarios']:_append(s,[st['run_id'],'','','',x['zone_id'],x['id'],str(x['detected']),x['votes'],'',ex,x['frequency_per_year']+' /yr; '+x['frequency_source']])
        else:
            basis='grid %s m %s, eligible %s %s; zone run grid %s m' % (r.get('grid_spacing_m'),r.get('mode','?'),'%.2f' % r['eligible_measure'] if r.get('eligible_measure') is not None else '?',r.get('measure_unit',''),r.get('zone_run_grid_spacing_m','?'))
            _append(s,[st['run_id'],st['method_version'],st['state'],st['lifecycle'],st['zone_id'],'EXISTING',r['existing_layout_fraction'],'',basis,ex,r['status']+'. '+r.get('resolution_note','')])
            for a in r['pareto']:_append(s,[st['run_id'],'','','',st['zone_id'],'+'.join(a['mount_ids']) or '(none)',a['fraction'],a['cost'],basis,ex,'Pareto proposal'])
    s=_sheet(wb,'Hashes',['Zone / item','Run','Input hash','Result / implementation SHA-256','Scene SHA-256','Software'],[18,22,66,66,66,10])
    for z in snap['zones']:_append(s,[z['zone_id'],z['run_id'],z['input_hash'],z['implementation_sha256'],z['scene_sha256'],z['software_version']])
    for z in snap['zones']:_append(s,['result '+z['zone_id'],z['run_id'],'',z['result_sha256'],'',''])
    for st in snap['studies']:_append(s,[st['zone_id'],st['run_id'],st['input_hash'],st['method_version'],'',''])
    for f in snap['figures']:_append(s,['figure '+f['zone_id'],f['run_id'],'z=%.2f' % f['slice_z'],f['png_sha256'],'',''])
    wb.save(path)

def study_lines(snap):
    out=[]
    for st in snap['studies']:
        r=st['result'];ex=' EXAMPLE library values used: '+', '.join(st['example_library_used'])+'.' if st['example_library_used'] else ''
        if st['method']=='SCENARIO_COVERAGE':
            out.append('%s (%s, %s, %s): %d user scenarios; frequency-weighted detected fraction %s (total %s /yr). By zone: %s. Not risk reduction, availability or SIL credit.%s' % (st['run_id'],st['method_version'],st['state'],st['lifecycle'],r['scenario_count'],r['overall']['frequency_weighted_detected_fraction'],r['overall']['total_frequency_per_year'],'; '.join('%s %s' % (z,v['frequency_weighted_detected_fraction']) for z,v in r['by_zone'].items()),ex))
        else:
            best='; '.join('%s -> %s (cost %s)' % ('+'.join(a['mount_ids']) or 'no addition',a['fraction'],a['cost']) for a in r['pareto'][:4])
            basis=' Options grid %s m %s, eligible %s %s (zone run grid %s m). %s' % (r.get('grid_spacing_m'),r.get('mode','?'),'%.2f' % r['eligible_measure'] if r.get('eligible_measure') is not None else '?',r.get('measure_unit',''),r.get('zone_run_grid_spacing_m','?'),r.get('resolution_note',''))
            out.append('%s (%s, %s, %s) zone %s, %dooN: existing layout %s; Pareto proposals: %s. PROPOSALS ONLY - baseline unchanged.%s%s' % (st['run_id'],st['method_version'],st['state'],st['lifecycle'],st['zone_id'],r['required_votes'],r['existing_layout_fraction'],best,basis,ex))
    return out

METHOD_TEXT=('Flame: FG-FLAME-GEO/1.1 geographic coverage. The zone is discretised into grid cells clipped to the zone; each cell contributes its free measure '
    '(exact for axis-aligned box solids, rigorously bounded for other closed meshes; solids and basis exclusions reported separately). Detection is evaluated at one representative '
    'free point per cell (sampled-cell fraction). A detector responds when the target is inside its library field of view (local frame of the mount rotation) and contour range and '
    'is in line of sight from the detector through the 3D geometry (only the detector\'s own declared mount component is ignored within the standoff radius). '
    'Gas: FG-GAS-GEO/1.1 geographic design-cloud method (not dispersion), using point detectors inside the cloud and open-path LEL.m path integrals. '
    'A two-grid check is reported as GRID AGREEMENT / DISAGREEMENT / UNRESOLVED FEATURE / NOT EVALUABLE; it is not an error bound or proof of convergence.')

def _figure_size(path,max_w_in,max_h_in):
    from PIL import Image as PILImage
    with PILImage.open(path) as im:wd,ht=im.size
    k=min(max_w_in/wd,max_h_in/ht);return wd*k,ht*k

def _docx(snap,figs,path):
    from docx import Document
    from docx.shared import Inches,RGBColor,Pt
    from docx.enum.section import WD_ORIENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    doc=Document();sec=doc.sections[0]
    sec.orientation=WD_ORIENT.LANDSCAPE;sec.page_width,sec.page_height=sec.page_height,sec.page_width
    for m in ('left_margin','right_margin','top_margin','bottom_margin'):setattr(sec,m,Inches(.6))
    st=doc.styles['Normal'];st.font.size=Pt(9)
    sec.header.paragraphs[0].text=snap['review_status']+' | '+snap['case']
    sec.footer.paragraphs[0].text=LABEL
    doc.add_heading('Fire and gas detector coverage report',0)
    p=doc.add_paragraph();r=p.add_run(snap['label']);r.bold=True;r.font.color.rgb=RGBColor(0xB0,0x3A,0x2E)
    p=doc.add_paragraph();r=p.add_run('Review status: '+snap['review_status']);r.bold=True
    doc.add_paragraph(snap['disclaimer'])
    if snap['example_library_entries']:
        p=doc.add_paragraph();r=p.add_run('WARNING: EXAMPLE library values used ('+', '.join(snap['example_library_entries'])+'). These results illustrate the workflow only and must not be used for design.');r.bold=True;r.font.color.rgb=RGBColor(0xB0,0x3A,0x2E)
    doc.add_paragraph('Case: %s | Software %s | Scene SHA-256 %s | Report content SHA-256 %s' % (snap['case'],snap['software_version'],snap['scene_sha256'],snap['content_sha256']))
    doc.add_heading('Method',1);doc.add_paragraph(METHOD_TEXT+' Full method: '+snap['method_document']+'.')
    doc.add_heading('Results by zone',1)
    idx=[0,2,3,4,5,6,8,9,10,11,12,13,14,15];head=[SUMMARY_HEAD[i] for i in idx]
    widths=[1.0,0.9,0.6,1.05,0.6,0.75,0.5,0.5,0.5,0.5,0.6,1.0,0.85,0.75]
    t=doc.add_table(rows=1,cols=len(head));t.style='Table Grid';t.autofit=False
    trPr=t.rows[0]._tr.get_or_add_trPr();el=OxmlElement('w:tblHeader');el.set(qn('w:val'),'true');trPr.append(el)  # repeat header row
    for i,h in enumerate(head):t.rows[0].cells[i].text=h
    for r in summary_rows(snap):
        cells=t.add_row().cells
        for i,k in enumerate(idx):cells[i].text=str(r[k])
    for i,col in enumerate(t.columns):col.width=Inches(widths[i])  # tblGrid widths (honoured by Word and LibreOffice)
    for row in t.rows:
        for i,c in enumerate(row.cells):
            c.width=Inches(widths[i])
            for par in c.paragraphs:
                for run in par.runs:run.font.size=Pt(7)
    for c in t.rows[0].cells:
        for par in c.paragraphs:
            for run in par.runs:run.bold=True
    doc.add_heading('Zone inputs',1)
    for z in snap['zones']:
        s=z['setup'];doc.add_paragraph('%s [%s, %s]: grid %.2f m %s, voting %dooN, %s. Criterion: %s. Sensitivity %s. Run %s, input hash %s.' % (z['zone_id'],z['state'],z['lifecycle'],s['grid_spacing_m'],s['mode'],s['voting_required'],setup_text(s),s['criterion_reference'],'on '+str(z['sensitivity']['range_factors']) if z['sensitivity']['enabled'] else 'off',z['run_id'],z['input_hash']),style='List Bullet')
    doc.add_heading('Detectors and library entries used',1)
    for d in snap['detectors']:doc.add_paragraph('%s (zones %s) %s at (%.2f, %.2f, %.2f) az %.1f el %.1f roll %.1f -> %s%s' % (d['id'],', '.join(d['zones']),d['detector_type'],*d['position'],d['azimuth'],d['elevation'],d['roll'],d['library_id'],'' if not d['receiver'] else ' receiver (%.2f, %.2f, %.2f)' % tuple(d['receiver'])),style='List Bullet')
    for e in snap['library']:doc.add_paragraph('%s [sha256 %s, used by %s]: %s %s, %s; data status: %s; source %s rev %s p.%s' % (e['id'],e['content_sha256'][:16],', '.join(e['used_by_runs']),e['detector_type'],e['technology'],e['fuel_or_gas'],e['source']['data_status'],e['source']['title'],e['source']['revision'],e['source']['page']),style='List Bullet')
    if snap['studies']:
        doc.add_heading('Scenario coverage and layout options',1)
        for line in study_lines(snap):doc.add_paragraph(line,style='List Bullet')
    doc.add_heading('Heatmaps',1)
    for p,f in figs:
        wi,hi=_figure_size(p,9.5,5.6);doc.add_picture(str(p),width=Inches(wi),height=Inches(hi));doc.add_paragraph(f['description'])
    doc.add_heading('Findings',1)
    for f in snap['findings'] or [{'id':'-','severity':'-','message':'No coverage findings'}]:doc.add_paragraph('%s [%s] %s' % (f['id'],f['severity'],f['message']),style='List Bullet')
    doc.save(path)

def _pdf(snap,figs,path):
    import reportlab
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image as RLImage,Table,TableStyle,KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4,landscape
    from xml.sax.saxutils import escape
    root=Path(reportlab.__file__).parent/'fonts'
    for n,f in [('FGSans','Vera.ttf'),('FGSansBold','VeraBd.ttf')]:
        if n not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(n,str(root/f)))
    st=getSampleStyleSheet()
    for s in st.byName.values():s.fontName='FGSansBold' if 'Heading' in s.name or s.name=='Title' else 'FGSans'
    small=ParagraphStyle('small',fontName='FGSans',fontSize=7,leading=8.5,wordWrap='CJK');cell=ParagraphStyle('cell',fontName='FGSans',fontSize=6.5,leading=7.8,wordWrap='CJK')
    warn=ParagraphStyle('warn',parent=st['BodyText'],textColor=colors.HexColor('#B03A2E'),fontName='FGSansBold')
    story=[Paragraph('Fire and gas detector coverage report',st['Title']),Paragraph(escape(snap['label']),warn),Paragraph(escape('Review status: '+snap['review_status']),warn),Paragraph(escape(snap['disclaimer']),st['BodyText'])]
    if snap['example_library_entries']:story.append(Paragraph(escape('WARNING: EXAMPLE library values used ('+', '.join(snap['example_library_entries'])+') - illustrative only, not for design.'),warn))
    story+= [Paragraph(escape('Case: %s | Software %s | Scene SHA-256 %s | Report content SHA-256 %s' % (snap['case'],snap['software_version'],snap['scene_sha256'],snap['content_sha256'])),small),Spacer(1,6),
             Paragraph('Method',st['Heading1']),Paragraph(escape(METHOD_TEXT),small),Paragraph('Results by zone',st['Heading1'])]
    idx=[0,2,3,4,5,6,8,9,10,11,12,13,14,15];head=[SUMMARY_HEAD[i] for i in idx]
    data=[[Paragraph('<b>%s</b>' % escape(h),cell) for h in head]]+[[Paragraph(escape(str(r[k])),cell) for k in idx] for r in summary_rows(snap)]
    widths=[60,56,52,60,44,52,38,38,38,38,44,74,70,62]  # 726 pt fits landscape A4 (842 - 2x40 margins)
    t=Table(data,repeatRows=1,colWidths=widths);t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.3,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8e8e8')),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story+=[t,Spacer(1,8),Paragraph('Zone inputs',st['Heading1'])]
    for z in snap['zones']:
        s=z['setup'];story.append(Paragraph(escape('%s [%s, %s]: grid %.2f m %s, voting %dooN, %s. Criterion: %s. Sensitivity %s. Run %s, input hash %s.' % (z['zone_id'],z['state'],z['lifecycle'],s['grid_spacing_m'],s['mode'],s['voting_required'],setup_text(s),s['criterion_reference'],'on '+str(z['sensitivity']['range_factors']) if z['sensitivity']['enabled'] else 'off',z['run_id'],z['input_hash'])),small))
    story.append(Paragraph('Library entries used',st['Heading1']))
    for e in snap['library']:story.append(Paragraph(escape('%s [sha256 %s, used by %s]: %s %s, %s; data status: %s; source %s rev %s p.%s' % (e['id'],e['content_sha256'][:16],', '.join(e['used_by_runs']),e['detector_type'],e['technology'],e['fuel_or_gas'],e['source']['data_status'],e['source']['title'],e['source']['revision'],e['source']['page'])),small))
    if snap['studies']:
        story.append(Paragraph('Scenario coverage and layout options',st['Heading1']))
        for line in study_lines(snap):story.append(Paragraph(escape(line),small))
    story.append(Paragraph('Heatmaps',st['Heading1']))
    W,H=landscape(A4);fw,fh=W-80,H-80-60
    for p,f in figs:
        wi,hi=_figure_size(p,fw,fh-40);story.append(KeepTogether([RLImage(str(p),width=wi,height=hi),Paragraph(escape(f['description']),small),Spacer(1,8)]))
    story.append(Paragraph('Findings',st['Heading1']))
    for f in snap['findings'] or [{'id':'-','severity':'-','message':'No coverage findings'}]:story.append(Paragraph(escape('%s [%s] %s' % (f['id'],f['severity'],f['message'])),small))
    def footer(c,d):c.saveState();c.setFont('FGSans',7);c.drawString(40,20,(snap['review_status']+' | '+snap['case'])[:150]+' | page %d' % d.page);c.restoreState()
    SimpleDocTemplate(path,pagesize=landscape(A4),leftMargin=40,rightMargin=40,topMargin=40,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
