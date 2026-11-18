"""WP07 development register reports from one normalized synthetic snapshot.

No engineering coverage conclusions or approval signatures are generated. Writers
are optional dependencies and fail explicitly if absent. Output folder must be new.
QA compares every serialized row across XLSX/DOCX/PDF and detects corrupt outputs.
"""
from __future__ import annotations
import hashlib,json,re,zipfile
from pathlib import Path
from fgmapping.domain.scene import canonical,content_hash
from fgmapping.services.geometry import get_scene
from fgmapping.services.registers import records

def normalized_snapshot(session):
    base=session.snapshot();scene=get_scene(session)
    if any(e['data_class']!='SYNTHETIC' for e in base['evidence']):raise ValueError('Development exporter accepts synthetic evidence only')
    data={'detectors':base['detectors'],'evidence':base['evidence'],'components':[],'records':[],'calculation_runs':[],'geometry_sources':[]}
    if scene:
        for c in scene.components:
            data['components'].append({'id':c.id,'label':c.label,'semantic':c.semantic,'frame_id':c.frame_id,'source_units':scene.frame(c.frame_id).units,'mesh_sha256':c.mesh.sha256,'evidence_id':c.evidence_id,'qualification':'UNVERIFIED'})
    if session.con.execute('PRAGMA user_version').fetchone()[0]>=2:
        details={r[0]:r[1:] for r in session.con.execute('SELECT detector_id,azimuth,elevation,roll,manufacturer,model,sensitivity FROM detector_details')}
        for d in data['detectors']:
            extra=details.get(d['id'],(None,None,None,'NOT SUPPLIED','NOT SUPPLIED','NOT SUPPLIED'))
            d.update(dict(zip(('azimuth_deg','elevation_deg','roll_deg','manufacturer','model','sensitivity'),extra)))
        data['records']=records(session)
        from fgmapping.services.findings import study_findings
        data['findings']=study_findings(session)
        data['calculation_runs']=[dict(zip(('id','input_hash','method','result_json','calculation_status','qualification_status','review_status','input_json'),r)) for r in session.con.execute('SELECT * FROM calculation_run ORDER BY id')]
        data['geometry_sources']=[dict(zip(('source_sha256','size_bytes','format','frame_json','manifest_json','evidence_id'),r)) for r in session.con.execute('SELECT source_sha256,length(raw_bytes),format,frame_json,manifest_json,evidence_id FROM geometry_attachment ORDER BY source_sha256')]
    extra={}
    if session.con.execute('PRAGMA user_version').fetchone()[0]>=3:
        from fgmapping.services import workspace as w
        from fgmapping.services.basis import readiness
        from fgmapping.domain.mounting import component_fingerprint
        from fgmapping.services.mounts import mount_status
        def table_rows(table):
            columns=w.TABLES[table]
            return [dict(zip(columns,r)) for r in session.con.execute('SELECT '+','.join(columns)+' FROM '+table+' ORDER BY '+columns[0])]
        data['mounts']=[]
        for r in table_rows('detector_mount'):
            data['mounts'].append({'id':r['detector_id'],**{k:v for k,v in r.items() if k!='detector_id'},'source_state':mount_status(session,r)})
        data['study_basis']=table_rows('study_basis')
        data['performance_preparation']=[];assets=[]
        for r in table_rows('performance_dataset'):
            p=json.loads(r['payload_json']);assets.append({'id':r['id'],'raw_text':r['raw_text'],'import_sha256':r['import_sha256']})
            data['performance_preparation'].append({'id':r['id'],'manufacturer':p['manufacturer'],'model':p['model'],'revision':p['revision'],'sensitivity':p['sensitivity'],'source':p['source'],'conditions':p['conditions'],'units':p['units'],'samples':p['samples'],'import_sha256':r['import_sha256'],'status':r['status'],'qualification':'UNVERIFIED'})
        data['performance_links']=[{'id':r['detector_id'],**{k:v for k,v in r.items() if k!='detector_id'}} for r in table_rows('detector_performance_link')]
        data['preparation_reviews']=[]
        for review in table_rows('preparation_review'):
            table={'PERFORMANCE':'performance_dataset','BASIS':'study_basis','MOUNT':'detector_mount'}[review['subject_kind']]
            current=w.row(session,table,review['subject_id'])
            state='SUBJECT_MISSING' if current is None else 'CURRENT_DRAFT_SUBJECT' if content_hash(current)==review['subject_hash'] else 'STALE_DRAFT_SUBJECT'
            data['preparation_reviews'].append({**review,'subject_state':state,'qualification':'UNVERIFIED'})
        calculation_artifacts=data['calculation_runs']
        data['calculation_runs']=[]
        for run in calculation_artifacts:
            envelope=json.loads(run['input_json']);result=json.loads(run['result_json'])
            summary={k:v for k,v in result.items() if k!='samples'}
            if 'samples' in result:summary['sample_count']=len(result['samples'])
            data['calculation_runs'].append({'id':run['id'],'input_hash':run['input_hash'],'method':run['method'],'calculation_status':run['calculation_status'],'qualification_status':run['qualification_status'],'review_status':run['review_status'],'software_version':envelope.get('software_version','NOT SUPPLIED'),'implementation_sha256':envelope.get('implementation_sha256','NOT SUPPLIED'),'result_summary_json':canonical(summary),'full_artifact_reference':'calculation_artifacts/'+run['id'],'result_artifact_sha256':content_hash(result)})
        extra={'readiness':readiness(session),'performance_source_assets':assets,'calculation_artifacts':calculation_artifacts,'software_version':__import__('fgmapping').__version__}
    result={'snapshot_version':'fg-report/2' if extra else 'fg-report/1','status':'DEVELOPMENT BUILD','qualification_status':'UNVERIFIED','review_status':'CANDIDATE','data_class':'SYNTHETIC',
            'case':base['case'],'scene_hash':None if scene is None else scene.sha256,'scene':None if scene is None else scene.to_dict(),'datasets':data,'ledger':base['ledger'],
            'limitations':['No engineering detector coverage results','No independent engineering qualification','Windows acceptance pending','Snapshot geometry is synthetic envelope data']}
    result.update(extra)
    if session.con.execute('PRAGMA user_version').fetchone()[0]>=4:
        from fgmapping.services import coverage as cov
        runs=[]
        for z,r in sorted(cov.latest_runs(session).items()):
            res=json.loads(r['result_json']);runs.append({'id':r['id'],'zone_id':z,'method_version':r['method_version'],'state':cov.run_currency(session,r),'input_hash':r['input_hash'],'fractions':res['fractions'],'voting_required':res['voting_required'],'label':r['label']})
        data['coverage_runs']=runs
        result['limitations'][0]='Coverage results (where present) are engineer-reviewed - not independently certified, and depend on the detector library data entered' if runs else 'No coverage run stored in this case'
    sources=[];decisions=[];assets=[]
    for event in base['ledger']:
        if event['command']!='RETAIN_PREPARATION_SOURCE':continue
        p=json.loads(event['forward_json']);summary=p['summary'];key='SOURCE-'+str(event['event_id']);assets.append({'id':key,**p})
        sources.append({'id':key,'kind':p['kind'],'source_sha256':p['source_sha256'],'format':p['format'],'actor':event['actor'],'utc':event['utc'],'review_rationale':p['review_rationale'],'register_rows':summary.get('count',0),'changed_components':len(summary.get('components',[])),'history_status':'RETAINED SOURCE REVIEW; current entity state must be inspected','qualification':'UNVERIFIED'})
        for d in summary.get('mount_decisions',[]):decisions.append({'id':key+'/'+d['detector_id'],**d,'source_review_id':key,'actor':event['actor'],'utc':event['utc'],'qualification':'UNVERIFIED'})
    if sources:
        data['source_preparation_history']=sources;data['mount_revision_decisions']=decisions;result['preparation_source_assets']=assets
    if 'readiness' in result:
        items=[]
        for axis in ('missing','blocking','engineering_blockers'):
            for i,message in enumerate(result['readiness'][axis]):items.append({'id':axis.upper()+'-'+str(i+1),'axis':axis,'message':message,'status':'OPEN','qualification':'UNVERIFIED'})
        data['unresolved_inputs']=items
    return json.loads(canonical(result))

def display_value(value):
    if value is None:return 'NOT SUPPLIED'
    if isinstance(value,str):return value
    return canonical(value)

def report_rows(snapshot):
    return [(name,row['id'] if 'id' in row else row['source_sha256'],canonical(row)) for name,rows in snapshot['datasets'].items() for row in rows]

def audit_pairs(row):
    pairs=[]
    for key,value in sorted(row.items()):
        text=display_value(value)
        if len(text)<=1000:pairs.append((key,text))
        else:
            chunks=[text[i:i+1000] for i in range(0,len(text),1000)]
            pairs.extend((key+' ['+str(i+1)+'/'+str(len(chunks))+']',part) for i,part in enumerate(chunks))
    return pairs

def detector_schedule(snapshot):
    return [[d['id'],d['detector_type'],d['x'],d['y'],d['z'],d['evidence_id']] for d in snapshot['datasets']['detectors']]

def overview_lines(snapshot):
    data=snapshot['datasets'];lines=['Study: '+snapshot['case']['name'],f"Register counts: {len(data['detectors'])} detectors, {len(data.get('records',[]))} equipment/zone records, {len(data['components'])} geometry components."]
    if 'readiness' in snapshot:
        r=snapshot['readiness'];lines+=['Input readiness: '+r['input_status']+'. Engineering calculation status: '+r['engineering_calculation_status']+'.','Missing input items: '+str(len(r['missing']))+'. Blocking input items: '+str(len(r['blocking']))+'.','Engineering method blockers: '+'; '.join(r['engineering_blockers'])+'.']
    for basis in data.get('study_basis',[]):
        p=json.loads(basis['payload_json']);lines+=['Design basis revision: '+p['revision']+'. Study type: '+p['study_type']+'. Required votes: '+str(p['voting'])+'.','Target definition: '+p['target_description']+'. Fuel or gas: '+p['fuel_or_gas']+'.','Criterion reference: '+p['criterion_reference']+'. Supplied target fraction: '+str(p['target_fraction'])+'.','Uncertainty reference: '+p['uncertainty_reference']+'.']
    lines.append('Preparation findings: '+str(len(data.get('findings',[])))+'. All records remain candidate; this report does not establish detector coverage or acceptance.')
    if snapshot.get('comparison'):lines.append('Revision comparison: '+str(len(snapshot['comparison']['changes']))+' changes from snapshot '+snapshot['comparison']['previous_snapshot_hash']+'.')
    if data.get('source_preparation_history'):lines.append('Retained source reviews: '+str(len(data['source_preparation_history']))+'. Revision mount decisions: '+str(len(data.get('mount_revision_decisions',[])))+'. History records do not imply that changes remain applied.')
    return lines

def presentation_sheets(snapshot):
    sheets={}
    if 'readiness' in snapshot:
        r=snapshot['readiness'];rows=[['Readiness axis','Status'],['Input preparation',r['input_status']],['Engineering calculation',r['engineering_calculation_status']],['Qualification',r['qualification']]]
        rows += [['Missing input',x] for x in r['missing']]+[['Blocking input',x] for x in r['blocking']]+[['Method blocker',x] for x in r['engineering_blockers']]
        sheets['Readiness summary']=rows
    mounts=snapshot['datasets'].get('mounts',[])
    if mounts:sheets['Mount schedule']=[['Detector','Facility component','Source anchor','Offset m','Local orientation deg','Source state']]+[[m['id'],m['component_id'],m['anchor_local_json'],m['offset_m_json'],m['orientation_local_json'],m['source_state']] for m in mounts]
    perf=snapshot['datasets'].get('performance_preparation',[])
    if perf:sheets['Performance catalogue']=[['Dataset','Manufacturer','Model','Revision','Sensitivity','Qualification']]+[[p['id'],p['manufacturer'],p['model'],p['revision'],p['sensitivity'],p['qualification']] for p in perf]
    return sheets

def write_reports(snapshot,destination):
    from openpyxl import Workbook
    from openpyxl.styles import Font,PatternFill,Alignment
    from docx import Document
    from docx.shared import Inches,Pt,RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether,Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from xml.sax.saxutils import escape
    if snapshot.get('data_class')!='SYNTHETIC':raise ValueError('Synthetic snapshot required')
    dest=Path(destination)
    if dest.exists():raise ValueError('New output directory required; existing outputs are never overwritten')
    dest.mkdir(parents=True)
    sha=content_hash(snapshot);rows=report_rows(snapshot)
    (dest/'12_STUDY_DATA.json').write_text(json.dumps(snapshot,indent=2,allow_nan=False)+'\n')
    wb=Workbook();ws=wb.active;ws.title='Study'
    for row in [('Fire and gas synthetic register report',),('Status',snapshot['status']),('Qualification',snapshot['qualification_status']),('Review',snapshot['review_status']),('Snapshot SHA256',sha),('Scope','Register export only. No detector coverage calculated.')]:ws.append(row)
    ws.column_dimensions['A'].width=30;ws.column_dimensions['B'].width=90
    for name,dataset in snapshot['datasets'].items():
        sheet=wb.create_sheet(name[:31]);sheet.append(['ID','Canonical snapshot row']+(['X (m)','Y (m)','Z (m)'] if name=='detectors' else []))
        for row in dataset:
            id=row.get('id',row.get('source_sha256'));sheet.append([id,canonical(row)]+([row['x'],row['y'],row['z']] if name=='detectors' else []))
        sheet.freeze_panes='B2';sheet.auto_filter.ref=sheet.dimensions
        sheet.column_dimensions['A'].width=25;sheet.column_dimensions['B'].width=120
        if name=='detectors':
            for col in ('C','D','E'):sheet.column_dimensions[col].width=14
        for cell in sheet[1]:cell.font=Font(name='Calibri',size=11,bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='284B55')
        for row in sheet.iter_rows(min_row=2):
            sheet.row_dimensions[row[0].row].height=max(32,15*(len(str(row[1].value))//115+1))
            for cell in row:cell.font=Font(name='Calibri',size=11);cell.alignment=Alignment(vertical='top',wrap_text=True)
    # Force textual identifiers/JSON to text, never spreadsheet formulas.
    for sheet in wb:
        for row in sheet:
            for cell in row:
                if isinstance(cell.value,str):cell.data_type='s'
    schedule_sheet=wb.create_sheet('Detector schedule')
    schedule_sheet.append(['Detector','Type','X m','Y m','Z m','Evidence'])
    for row in detector_schedule(snapshot):schedule_sheet.append(row)
    for col,width in zip(('A','B','C','D','E','F'),(25,18,15,15,15,30)):schedule_sheet.column_dimensions[col].width=width
    schedule_sheet.freeze_panes='C2';schedule_sheet.auto_filter.ref=schedule_sheet.dimensions
    for row in schedule_sheet:
        for cell in row:
            if isinstance(cell.value,str):cell.data_type='s'
            cell.font=Font(name='Calibri',size=11,bold=cell.row==1);cell.alignment=Alignment(wrap_text=True,vertical='top')
    for name,values in presentation_sheets(snapshot).items():
        sheet=wb.create_sheet(name)
        for values_row in values:sheet.append(values_row)
        sheet.freeze_panes='B2'
        for col in ('A','B','C','D','E','F'):sheet.column_dimensions[col].width=28
        for row in sheet:
            for cell in row:
                if isinstance(cell.value,str):cell.data_type='s'
                cell.font=Font(name='Calibri',size=11,bold=cell.row==1);cell.alignment=Alignment(wrap_text=True,vertical='top')
            sheet.row_dimensions[row[0].row].height=42
    for sheet in wb:
        for row in sheet:
            for cell in row:
                if isinstance(cell.value,str):cell.data_type='s'
    wb.save(dest/'Registers.xlsx')
    doc=Document();section=doc.sections[0];section.top_margin=Inches(.7);section.bottom_margin=Inches(.7)
    section.left_margin=Inches(.7);section.right_margin=Inches(.7)
    normal=doc.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(10)
    for name in ('Title','Heading 1','Heading 2'):
        doc.styles[name].font.color.rgb=RGBColor(0,0,0)
    doc.add_heading('Fire and gas synthetic register report',0)
    doc.add_paragraph('This report records the synthetic facility model and candidate detector register. No engineering detector coverage has been calculated.')
    doc.add_paragraph('DEVELOPMENT BUILD | UNVERIFIED | CANDIDATE')
    doc.add_paragraph('Snapshot SHA256 '+sha)
    for line in overview_lines(snapshot):doc.add_paragraph(line)
    schedule=detector_schedule(snapshot)
    if schedule:
        doc.add_heading('Detector schedule',1)
        st=doc.add_table(rows=1,cols=6);st.style='Light Shading Accent 1'
        for cell,value in zip(st.rows[0].cells,('Detector','Type','X m','Y m','Z m','Evidence')):cell.text=value
        for row in schedule:
            for cell,value in zip(st.add_row().cells,row):cell.text=str(value)
        doc.add_paragraph()
    mounts=snapshot['datasets'].get('mounts',[])
    if mounts:
        doc.add_heading('Candidate mounting schedule',1)
        mt=doc.add_table(rows=1,cols=4);mt.style='Light Shading Accent 1'
        for cell,value in zip(mt.rows[0].cells,('Detector','Facility component','Offset (m)','Source state')):cell.text=value
        for m in mounts:
            for cell,value in zip(mt.add_row().cells,(m['id'],m['component_id'],m['offset_m_json'],m['source_state'])):cell.text=str(value)
        doc.add_paragraph('Full source anchors, local orientation, evidence and fingerprints follow in the mount audit records.')
    import base64,io
    for figure in snapshot.get('figures',[]):
        raw=base64.b64decode(figure['png_base64'],validate=True)
        if hashlib.sha256(raw).hexdigest()!=figure['sha256']:raise ValueError('Figure hash mismatch')
        doc.add_picture(io.BytesIO(raw),width=Inches(6.8));doc.add_paragraph(figure['description'])
    for style in doc.styles:
        if style.type==1 and style.element.pPr is not None:
            for border in list(style.element.pPr.findall(qn('w:pBdr'))):style.element.pPr.remove(border)
    for name,dataset in snapshot['datasets'].items():
        doc.add_heading(name.replace('_',' ').capitalize(),1)
        if not dataset:doc.add_paragraph('No records supplied.');continue
        for row in dataset:
            identifier=row.get('id',row.get('source_sha256','Record'))
            doc.add_heading(str(identifier),2)
            table=doc.add_table(rows=1,cols=2);table.autofit=False
            table.columns[0].width=Inches(1.65);table.columns[1].width=Inches(5.45)
            table.cell(0,0).text='Field';table.cell(0,1).text='Value'
            pairs=audit_pairs(row)
            for key,value in pairs:
                cells=table.add_row().cells;cells[0].text=key;cells[1].text=value
            for i,tr in enumerate(table.rows):
                props=tr._tr.get_or_add_trPr();props.append(OxmlElement('w:cantSplit'))
                if i==0:props.append(OxmlElement('w:tblHeader'))
                for cell in tr.cells:
                    tcpr=cell._tc.get_or_add_tcPr();borders=OxmlElement('w:tcBorders')
                    for edge in ('top','left','bottom','right'):
                        el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');borders.append(el)
                    tcpr.append(borders)
                    if i==0:
                        fill=OxmlElement('w:shd');fill.set(qn('w:fill'),'E4EBEE');tcpr.append(fill)
                    for para in cell.paragraphs:
                        para.paragraph_format.space_before=Pt(3);para.paragraph_format.space_after=Pt(3)
                        para.paragraph_format.keep_with_next=(i<len(table.rows)-1) if len(pairs)<=14 and sum(len(v) for k,v in pairs)<3000 else i==0
                        for run in para.runs:run.font.size=Pt(9);run.bold=i==0
            doc.add_paragraph()
    doc.add_heading('Engineering limitations',1)
    for item in snapshot['limitations']:doc.add_paragraph(item)
    doc.save(dest/'Study.docx')
    # Embed the report dependency's bundled fonts: PDF appearance must not
    # depend on a reader's substitution for the standard Helvetica fonts.
    import reportlab
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font_root=Path(reportlab.__file__).parent/'fonts'
    for name,filename in [('FGSans','Vera.ttf'),('FGSansBold','VeraBd.ttf'),('FGSansItalic','VeraIt.ttf'),('FGSansBoldItalic','VeraBI.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(name,str(font_root/filename)))
    pdfmetrics.registerFontFamily('FGSans',normal='FGSans',bold='FGSansBold',italic='FGSansItalic',boldItalic='FGSansBoldItalic')
    styles=getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName='FGSansBold' if 'Heading' in style.name or style.name=='Title' else 'FGSans'
    styles.add(ParagraphStyle('Row',fontName='FGSans',fontSize=9,leading=12,spaceAfter=5,splitLongWords=True))
    story=[Paragraph('Fire and gas synthetic register report',styles['Title']),Paragraph('This report records the facility model and detector register. '+('Coverage runs are listed in the coverage_runs dataset (engineer-reviewed - not independently certified); see the separate coverage report.' if snapshot['datasets'].get('coverage_runs') else 'No engineering detector coverage has been calculated.'),styles['BodyText']),Spacer(1,10),Paragraph('DEVELOPMENT BUILD | UNVERIFIED | CANDIDATE',styles['BodyText']),Spacer(1,10),Paragraph('Snapshot SHA256 '+sha,styles['Row'])]
    for line in overview_lines(snapshot):story.extend([Paragraph(escape(line),styles['BodyText']),Spacer(1,7)])
    for figure in snapshot.get('figures',[]):
        raw=base64.b64decode(figure['png_base64'],validate=True)
        from PIL import Image as PILImage
        with PILImage.open(io.BytesIO(raw)) as im:w,h=im.size
        story.extend([KeepTogether([RLImage(io.BytesIO(raw),width=480,height=480*h/w),Paragraph(escape(figure['description']),styles['BodyText'])]),Spacer(1,12)])
    for name,dataset in snapshot['datasets'].items():
        heading=Paragraph(name.replace('_',' ').capitalize(),styles['Heading1'])
        if not dataset:story.append(KeepTogether([heading,Paragraph('No records supplied.',styles['BodyText'])]))
        for row_index,row in enumerate(dataset):
            block=([heading] if row_index==0 else [])+[Paragraph(escape(str(row.get('id',row.get('source_sha256','Record')))),styles['Heading2'])]
            for key,value in audit_pairs(row):
                block.append(Paragraph('<b>'+escape(key)+'</b>: '+escape(value),styles['Row']))
            block.append(Spacer(1,6));story.append(KeepTogether(block))
    story.append(Paragraph('Engineering limitations',styles['Heading1']))
    for item in snapshot['limitations']:story.append(Paragraph(escape(item),styles['BodyText']))
    SimpleDocTemplate(str(dest/'Study.pdf'),leftMargin=50,rightMargin=50,topMargin=45,bottomMargin=45).build(story)
    qa_reports(snapshot,dest)
    manifest={p.name:{'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(dest.iterdir()) if p.is_file()}
    (dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
    with zipfile.ZipFile(dest/'Study.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(dest.iterdir()):
            if p.name!='Study.zip':z.write(p,p.name)
    with zipfile.ZipFile(dest/'Study.zip') as z:
        if z.testzip():raise ValueError('Report ZIP CRC failed')
        for name,item in manifest.items():
            if hashlib.sha256(z.read(name)).hexdigest()!=item['sha256']:raise ValueError('Report ZIP hash mismatch')
    return {'snapshot_sha256':sha,'record_rows':sum(name not in ('findings','revision_changes') for name,id,value in rows),'finding_rows':len(snapshot['datasets'].get('findings',[])),'change_rows':len(snapshot['datasets'].get('revision_changes',[])),'files':[p.name for p in dest.iterdir()],'status':'DEVELOPMENT EXPORT / PARSER QA PASSED; visual QA separate'}

def qa_reports(snapshot,dest):
    from openpyxl import load_workbook
    from docx import Document
    from pypdf import PdfReader
    dest=Path(dest)
    saved=json.loads((dest/'12_STUDY_DATA.json').read_text())
    if saved!=snapshot:raise ValueError('Snapshot mismatch')
    wb=load_workbook(dest/'Registers.xlsx',data_only=False)
    for name,dataset in snapshot['datasets'].items():
        actual=list(wb[name[:31]].iter_rows(min_row=2,values_only=True))
        expected=[(r.get('id',r.get('source_sha256')),canonical(r),*([r['x'],r['y'],r['z']] if name=='detectors' else [])) for r in dataset]
        if actual!=expected:raise ValueError('XLSX rows/IDs/values mismatch: '+name)
    doc=Document(dest/'Study.docx')
    expected_rows=[row for name,rows in snapshot['datasets'].items() for row in rows]
    expected=[audit_pairs(row) for row in expected_rows]
    audit_tables=[table for table in doc.tables if [c.text for c in table.rows[0].cells]==['Field','Value']]
    actual=[[(r.cells[0].text,r.cells[1].text) for r in table.rows[1:]] for table in audit_tables]
    schedules=[table for table in doc.tables if [c.text for c in table.rows[0].cells]==['Detector','Type','X m','Y m','Z m','Evidence']]
    if detector_schedule(snapshot):
        if len(schedules)!=1 or [[c.text for c in r.cells] for r in schedules[0].rows[1:]]!=[[str(v) for v in row] for row in detector_schedule(snapshot)]:raise ValueError('DOCX detector schedule mismatch')
    if list(wb['Detector schedule'].iter_rows(min_row=2,values_only=True))!=[tuple(r) for r in detector_schedule(snapshot)]:raise ValueError('XLSX readable detector schedule mismatch')
    for name,values in presentation_sheets(snapshot).items():
        actual_values=list(wb[name].iter_rows(values_only=True))
        width=max(len(r) for r in values)
        expected_values=[tuple(list(r)+[None]*(width-len(r))) for r in values]
        if actual_values!=expected_values:raise ValueError('Readable worksheet mismatch: '+name)
    if actual!=expected:raise ValueError('DOCX fields/IDs/values mismatch')
    text=''.join(page.extract_text() for page in PdfReader(dest/'Study.pdf').pages)
    compact=lambda s:re.sub(r'\s+','',s)
    for row in expected_rows:
        joined=''.join(key+': '+value for key,value in audit_pairs(row))
        if compact(joined) not in compact(text):raise ValueError('PDF fields/ID/values mismatch: '+str(row.get('id')))

    prose=''.join(p.text for p in doc.paragraphs)
    for line in overview_lines(snapshot):
        if compact(line) not in compact(text) or line not in prose:raise ValueError('Study overview values mismatch')
    if content_hash(snapshot) not in compact(text):raise ValueError('PDF snapshot hash mismatch')
    (dest/'QA.json').write_text(json.dumps({'status':'PASS','json':'exact snapshot','xlsx':'all row IDs and values','docx':'all field names, IDs and values exact','pdf':'all field names, IDs and values modulo whitespace','record_rows':sum(len(rows) for name,rows in snapshot['datasets'].items() if name not in ('findings','revision_changes')),'finding_rows':len(snapshot['datasets'].get('findings',[])),'change_rows':len(snapshot['datasets'].get('revision_changes',[])),'all_export_rows':len(expected),'visual_QA':'SEPARATE REQUIRED STEP'},indent=2))
