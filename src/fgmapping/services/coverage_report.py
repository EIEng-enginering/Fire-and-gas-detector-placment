"""M6 coverage report: JSON / Excel / Word / PDF with method, inputs, hashes and heatmap figures.

Label on every output: 'Engineer-reviewed results - not independently certified'.
Outputs are written to a NEW folder; nothing is overwritten.
"""
from __future__ import annotations
import hashlib,io,json
from pathlib import Path
from fgmapping.domain.scene import canonical,content_hash
from fgmapping.services import coverage as cov
from fgmapping.services import workspace as w
from fgmapping.services.case import utc_now
LABEL='Engineer-reviewed results - not independently certified'
DISCLAIMER=('Results depend entirely on the detector library data, zones, target fire / design cloud and geometry entered by the user. '
            'Library entries marked EXAMPLE VALUES must be replaced by verified manufacturer data before project use. '
            'No independent certification and no standards conformity (ISA-TR84.00.07, DNV-RP-A102, ISO 13702) is claimed. '
            'Geographic gas results use a fixed design cloud and are not dispersion results. Detector coverage is not FGS effectiveness, availability or risk reduction.')

def pct(v):return '-' if v is None else '%.1f %%' % (100*v)

def coverage_snapshot(session,px_per_m=20,max_slices=3):
    from fgmapping.services.heatmap import run_figures
    from fgmapping.services.findings import study_findings
    from fgmapping.services.geometry import get_scene
    cov.require_coverage(session)
    scene=get_scene(session);zones=[];figures=[];library={};detectors={}
    for z,run in sorted(cov.latest_runs(session).items()):
        res=json.loads(run['result_json']);env=json.loads(run['input_json'])
        library.update(env['library'])
        for d in env['detectors']:detectors[d['id']]=d
        zones.append({'zone_id':z,'run_id':run['id'],'state':cov.run_currency(session,run),'utc':run['utc'],'actor':run['actor'],'input_hash':run['input_hash'],'result':res,
                      'setup':env['setup'],'zone':env['zone'],'scene_sha256':env['scene_sha256'],'implementation_sha256':env['implementation_sha256'],'software_version':env['software_version'],'excluded_component_ids':env['excluded_component_ids']})
        for f in run_figures(session,run,px_per_m,max_slices):
            import base64;figures.append({**{k:v for k,v in f.items() if k!='png'},'png_base64':base64.b64encode(f['png']).decode(),'png_sha256':hashlib.sha256(f['png']).hexdigest()})
    from fgmapping.services import scenario_coverage as scs
    studies=[{'run_id':r['id'],'method':r['method'],'method_version':r['method_version'],'zone_id':r['zone_id'],'state':scs.study_run_currency(session,r),'utc':r['utc'],'actor':r['actor'],'input_hash':r['input_hash'],'result':json.loads(r['result_json'])} for r in scs.study_runs(session)]
    for st in studies:
        if st['method']=='LAYOUT_OPTIONS':library.update(json.loads(next(r for r in scs.study_runs(session) if r['id']==st['run_id'])['input_json'])['candidate_library'])
    example=sorted(k for k,e in library.items() if e['source']['data_status'].startswith('EXAMPLE'))
    findings=[f for f in study_findings(session) if f['id'].startswith(('COVERAGE-','LIBRARY-'))]
    snap={'report':'fg-coverage-report/1','label':LABEL,'disclaimer':DISCLAIMER,'case':session.name(),'software_version':__import__('fgmapping').__version__,'generated_utc':utc_now(),
          'scene_sha256':scene.sha256 if scene else None,'example_library_entries':example,'zones':zones,'detectors':[detectors[k] for k in sorted(detectors)],'library':[library[k] for k in sorted(library)],
          'findings':findings,'studies':studies,'figures':figures,'method_document':'docs/REV_G_COVERAGE_METHOD.md'}
    snap['content_sha256']=content_hash({k:v for k,v in snap.items() if k not in ('generated_utc',)})
    return snap

def summary_rows(snap):
    out=[]
    for z in snap['zones']:
        r=z['result'];fr=r['fractions']
        out.append([z['zone_id'],r['zone_kind'],r['method_version'],z['state'],'%.2f %s' % (r['eligible_measure'],r['measure_unit']),'%.2f' % sum(r['excluded_measure'].values()),pct(fr['0ooN']),pct(fr['1ooN']),pct(fr['2ooN']),pct(fr['3ooN']),
                    '%dooN %s' % (r['voting_required'],pct(r['required_voting_fraction'])),'; '.join('%s %s: %s' % (k,v['target'],v['status']) for k,v in r['performance_targets'].items() if v['target']!='NOT SUPPLIED') or 'no user targets',
                    r['convergence']['status'],z['run_id'],z['input_hash'][:16]])
    return out
SUMMARY_HEAD=['Zone','Kind','Method','State','Eligible','Excluded','0ooN','1ooN','2ooN','3ooN','Voting','User targets','Convergence','Run','Input hash']

def setup_text(s):
    if s['method']=='FLAME_GEOGRAPHIC':
        f=s['flame'];g=f['target_geometry']
        tg='point' if g['type']=='POINT' else 'cylinder D %.2f m x H %.2f m (%d x %d points)' % (g['diameter_m'],g['height_m'],g['rings']+1,g['levels'])
        return 'Target fire: %s %.0f kW, %s, min visible fraction %.2f, fire-size scaling %s' % (f['fuel'],f['heat_release_kw'],tg,f['min_visible_fraction'],f['fire_size_scaling'])
    gs=s['gas'];c=gs['cloud']
    return 'Design cloud: %s %s, %.0f %%LEL, detectors %s' % (gs['gas'],'sphere D %.1f m' % c['diameter_m'] if c['shape']=='SPHERE' else 'ellipsoid %s m' % c['axes_m'],gs['cloud_concentration_pct_lel'],'/'.join(gs['detector_types']))

def export_coverage_report(session,folder,name):
    folder=Path(folder);dest=folder/name
    if dest.exists():raise ValueError('Report folder already exists; outputs are never overwritten')
    snap=coverage_snapshot(session)
    if not snap['zones']:raise ValueError('No coverage runs stored')
    dest.mkdir(parents=True)
    (dest/(name+'.json')).write_bytes((json.dumps(snap,indent=1,sort_keys=True)+'\n').encode('utf8'))
    import base64
    figs=[]
    for i,f in enumerate(snap['figures']):
        p=dest/('FIG_%02d_%s_z%.2f.png' % (i+1,f['zone_id'],f['slice_z']));p.write_bytes(base64.b64decode(f['png_base64']));figs.append((p,f))
    _xlsx(snap,dest/(name+'.xlsx'));_docx(snap,figs,dest/(name+'.docx'));_pdf(snap,figs,dest/(name+'.pdf'))
    manifest={p.name:{'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(dest.iterdir()) if p.is_file()}
    (dest/'MANIFEST.json').write_text(json.dumps({'label':LABEL,'content_sha256':snap['content_sha256'],'files':manifest},indent=2))
    return {'folder':str(dest),'files':sorted(str(dest/n) for n in manifest)+[str(dest/'MANIFEST.json')],'content_sha256':snap['content_sha256']}

def _xlsx(snap,path):
    from openpyxl import Workbook
    from openpyxl.styles import Font,PatternFill
    wb=Workbook();ws=wb.active;ws.title='Summary'
    ws.append([snap['label']]);ws['A1'].font=Font(bold=True,color='B03A2E')
    ws.append([snap['disclaimer']]);ws.append(['Case',snap['case']]);ws.append(['Software',snap['software_version']]);ws.append(['Scene SHA-256',snap['scene_sha256']]);ws.append(['Report content SHA-256',snap['content_sha256']])
    if snap['example_library_entries']:ws.append(['WARNING','EXAMPLE library values used: '+', '.join(snap['example_library_entries'])+' - not for project design'])
    ws.append([]);ws.append(SUMMARY_HEAD)
    for c in ws[ws.max_row]:c.font=Font(bold=True)
    for r in summary_rows(snap):ws.append(r)
    s=wb.create_sheet('Zone setups');s.append(['Zone','Method','Grid (m)','Mode','Slices','Voting','Targets','Convergence','Criterion reference','Target / cloud','Excluded components','Zone low','Zone high'])
    for z in snap['zones']:
        st=z['setup'];s.append([z['zone_id'],st['method'],st['grid_spacing_m'],st['mode'],json.dumps(st['slice_elevations_m']),st['voting_required'],json.dumps(st['performance_targets']),json.dumps(st['convergence']),st['criterion_reference'],setup_text(st),', '.join(z['excluded_component_ids']),json.dumps(z['zone']['low']),json.dumps(z['zone']['high'])])
    s=wb.create_sheet('Detectors');s.append(['ID','Type','X','Y','Z','Azimuth','Elevation','Roll','Library entry','Receiver'])
    for d in snap['detectors']:s.append([d['id'],d['detector_type'],*d['position'],d['azimuth'],d['elevation'],d['roll'],d['library_id'],json.dumps(d['receiver'])])
    s=wb.create_sheet('Library used');s.append(['ID','Type','Technology','Fuel/gas','Rated fire kW','FOV H','FOV V','Contour deg:m','Threshold','Path m','Data status','Source','Revision','Page'])
    for e in snap['library']:
        s.append([e['id'],e['detector_type'],e['technology'],e['fuel_or_gas'],(e['target_fire'] or {}).get('heat_release_kw'),(e['fov'] or {}).get('horizontal_deg'),(e['fov'] or {}).get('vertical_deg'),';'.join('%g:%g' % tuple(r) for r in (e['contour'] or [])),
                  '' if not e['alarm_threshold'] else '%g %s' % (e['alarm_threshold']['value'],e['alarm_threshold']['units']),json.dumps(e['path_length_m']),e['source']['data_status'],e['source']['title'],e['source']['revision'],e['source']['page']])
        if e['source']['data_status'].startswith('EXAMPLE'):
            for c in s[s.max_row]:c.font=Font(color='B03A2E')
    s=wb.create_sheet('Per detector');s.append(['Zone','Detector','Fraction of eligible measure'])
    for z in snap['zones']:
        for d,v in z['result']['per_detector_fraction'].items():s.append([z['zone_id'],d,v])
    s=wb.create_sheet('Findings');s.append(['ID','Object','Severity','Message'])
    for f in snap['findings']:s.append([f['id'],f['object_id'],f['severity'],f['message']])
    s=wb.create_sheet('Scenario studies');s.append(['Run','Method','State','Zone(s)','Item','Detected / fraction','Votes / cost','Detail'])
    for st in snap['studies']:
        r=st['result']
        if st['method']=='SCENARIO_COVERAGE':
            s.append([st['run_id'],st['method_version'],st['state'],st['zone_id'],'OVERALL',r['overall']['frequency_weighted_detected_fraction'],'','frequency-weighted detected fraction (user frequencies)'])
            for x in r['scenarios']:s.append([st['run_id'],'','',x['zone_id'],x['id'],str(x['detected']),x['votes'],x['frequency_per_year']+' /yr; '+x['frequency_source']])
        else:
            s.append([st['run_id'],st['method_version'],st['state'],st['zone_id'],'EXISTING',r['existing_layout_fraction'],'',r['status']])
            for a in r['pareto']:s.append([st['run_id'],'','',st['zone_id'],'+'.join(a['mount_ids']) or '(none)',a['fraction'],a['cost'],'Pareto proposal'])
    s=wb.create_sheet('Hashes');s.append(['Zone','Run','Input hash','Implementation SHA-256','Scene SHA-256','Software'])
    for z in snap['zones']:s.append([z['zone_id'],z['run_id'],z['input_hash'],z['implementation_sha256'],z['scene_sha256'],z['software_version']])
    for st in snap['studies']:s.append([st['zone_id'],st['run_id'],st['input_hash'],st['method_version'],'',''])
    for f in snap['figures']:s.append(['figure',f['zone_id'],'z=%.2f' % f['slice_z'],f['png_sha256'],'',''])
    wb.save(path)

def study_lines(snap):
    out=[]
    for st in snap['studies']:
        r=st['result']
        if st['method']=='SCENARIO_COVERAGE':
            out.append('%s (%s, %s): %d user scenarios; frequency-weighted detected fraction %s (total %s /yr). By zone: %s. Not risk reduction, availability or SIL credit.' % (st['run_id'],st['method_version'],st['state'],r['scenario_count'],r['overall']['frequency_weighted_detected_fraction'],r['overall']['total_frequency_per_year'],'; '.join('%s %s' % (z,v['frequency_weighted_detected_fraction']) for z,v in r['by_zone'].items())))
        else:
            best='; '.join('%s -> %s (cost %s)' % ('+'.join(a['mount_ids']) or 'no addition',a['fraction'],a['cost']) for a in r['pareto'][:4])
            out.append('%s (%s, %s) zone %s, %dooN: existing layout %s; Pareto proposals: %s. PROPOSALS ONLY - baseline unchanged.' % (st['run_id'],st['method_version'],st['state'],st['zone_id'],r['required_votes'],r['existing_layout_fraction'],best))
    return out

def _docx(snap,figs,path):
    from docx import Document
    from docx.shared import Inches,RGBColor,Pt
    doc=Document();doc.add_heading('Fire and gas detector coverage report',0)
    p=doc.add_paragraph();r=p.add_run(snap['label']);r.bold=True;r.font.color.rgb=RGBColor(0xB0,0x3A,0x2E)
    doc.add_paragraph(snap['disclaimer'])
    if snap['example_library_entries']:
        p=doc.add_paragraph();r=p.add_run('WARNING: EXAMPLE library values used ('+', '.join(snap['example_library_entries'])+'). These results illustrate the workflow only and must not be used for design.');r.bold=True;r.font.color.rgb=RGBColor(0xB0,0x3A,0x2E)
    doc.add_paragraph('Case: %s | Software %s | Scene SHA-256 %s | Report content SHA-256 %s' % (snap['case'],snap['software_version'],snap['scene_sha256'],snap['content_sha256']))
    doc.add_heading('Method',1)
    doc.add_paragraph('Flame: FG-FLAME-GEO/1.0 geographic coverage. The zone is discretised into volume-weighted cells. A target fire (point or extended cylinder) is placed at each cell. A detector responds when the target is inside its library field of view and contour range and is in line of sight through the 3D geometry. Votes per cell give the 0ooN/1ooN/2ooN/3ooN weighted fractions. Gas: FG-GAS-GEO/1.0 geographic design-cloud method (not dispersion), using point detectors inside the cloud and open-path LEL.m path integrals. Full method: '+snap['method_document']+'.')
    doc.add_heading('Results by zone',1)
    head=['Zone','Method','State','Eligible','0ooN','1ooN','2ooN','3ooN','Voting','User targets','Convergence']
    t=doc.add_table(rows=1,cols=len(head));t.style='Table Grid'
    for i,h in enumerate(head):t.rows[0].cells[i].text=h
    for r in summary_rows(snap):
        vals=[r[0],r[2],r[3],r[4],r[6],r[7],r[8],r[9],r[10],r[11],r[12]];cells=t.add_row().cells
        for i,v in enumerate(vals):cells[i].text=str(v)
    for row in t.rows:
        for c in row.cells:
            for par in c.paragraphs:
                for run in par.runs:run.font.size=Pt(7.5)
    doc.add_heading('Zone inputs',1)
    for z in snap['zones']:
        st=z['setup'];doc.add_paragraph('%s: grid %.2f m %s, voting %dooN, %s. Criterion: %s. Run %s, input hash %s.' % (z['zone_id'],st['grid_spacing_m'],st['mode'],st['voting_required'],setup_text(st),st['criterion_reference'],z['run_id'],z['input_hash']),style='List Bullet')
    doc.add_heading('Detectors and library entries used',1)
    for d in snap['detectors']:doc.add_paragraph('%s %s at (%.2f, %.2f, %.2f) az %.1f el %.1f -> %s%s' % (d['id'],d['detector_type'],*d['position'],d['azimuth'],d['elevation'],d['library_id'],'' if not d['receiver'] else ' receiver (%.2f, %.2f, %.2f)' % tuple(d['receiver'])),style='List Bullet')
    for e in snap['library']:doc.add_paragraph('%s: %s %s, %s; data status: %s; source %s rev %s p.%s' % (e['id'],e['detector_type'],e['technology'],e['fuel_or_gas'],e['source']['data_status'],e['source']['title'],e['source']['revision'],e['source']['page']),style='List Bullet')
    if snap['studies']:
        doc.add_heading('Scenario coverage and layout options',1)
        for line in study_lines(snap):doc.add_paragraph(line,style='List Bullet')
    doc.add_heading('Heatmaps',1)
    for p,f in figs:
        doc.add_picture(str(p),width=Inches(6.3));doc.add_paragraph(f['description'])
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
    small=ParagraphStyle('small',fontName='FGSans',fontSize=7,leading=8.5);warn=ParagraphStyle('warn',parent=st['BodyText'],textColor=colors.HexColor('#B03A2E'),fontName='FGSansBold')
    story=[Paragraph('Fire and gas detector coverage report',st['Title']),Paragraph(escape(snap['label']),warn),Paragraph(escape(snap['disclaimer']),st['BodyText'])]
    if snap['example_library_entries']:story.append(Paragraph(escape('WARNING: EXAMPLE library values used ('+', '.join(snap['example_library_entries'])+') - illustrative only, not for design.'),warn))
    story+= [Paragraph(escape('Case: %s | Software %s | Scene SHA-256 %s | Report content SHA-256 %s' % (snap['case'],snap['software_version'],snap['scene_sha256'],snap['content_sha256'])),small),Spacer(1,8),Paragraph('Results by zone',st['Heading1'])]
    head=['Zone','Method','State','Eligible','0ooN','1ooN','2ooN','3ooN','Voting','User targets','Convergence']
    data=[[Paragraph(h,small) for h in head]]+[[Paragraph(escape(str(v)),small) for v in (r[0],r[2],r[3],r[4],r[6],r[7],r[8],r[9],r[10],r[11],r[12])] for r in summary_rows(snap)]
    t=Table(data,repeatRows=1,colWidths=[48,62,40,52,34,34,34,34,52,100,70]);t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.3,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8e8e8')),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story+=[t,Spacer(1,8),Paragraph('Zone inputs',st['Heading1'])]
    for z in snap['zones']:
        s=z['setup'];story.append(Paragraph(escape('%s: grid %.2f m %s, voting %dooN, %s. Criterion: %s. Run %s, input hash %s.' % (z['zone_id'],s['grid_spacing_m'],s['mode'],s['voting_required'],setup_text(s),s['criterion_reference'],z['run_id'],z['input_hash'])),small))
    story.append(Paragraph('Library entries used',st['Heading1']))
    for e in snap['library']:story.append(Paragraph(escape('%s: %s %s, %s; data status: %s; source %s rev %s p.%s' % (e['id'],e['detector_type'],e['technology'],e['fuel_or_gas'],e['source']['data_status'],e['source']['title'],e['source']['revision'],e['source']['page'])),small))
    if snap['studies']:
        story.append(Paragraph('Scenario coverage and layout options',st['Heading1']))
        for line in study_lines(snap):story.append(Paragraph(escape(line),small))
    story.append(Paragraph('Heatmaps',st['Heading1']))
    from PIL import Image as PILImage
    for p,f in figs:
        with PILImage.open(p) as im:wd,ht=im.size
        wpt=480;story.append(KeepTogether([RLImage(str(p),width=wpt,height=wpt*ht/wd),Paragraph(escape(f['description']),small),Spacer(1,8)]))
    story.append(Paragraph('Findings',st['Heading1']))
    for f in snap['findings'] or [{'id':'-','severity':'-','message':'No coverage findings'}]:story.append(Paragraph(escape('%s [%s] %s' % (f['id'],f['severity'],f['message'])),small))
    def footer(c,d):c.saveState();c.setFont('FGSans',7);c.drawString(40,20,LABEL+' | '+snap['case']+' | page %d' % d.page);c.restoreState()
    SimpleDocTemplate(str(path),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=40,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
