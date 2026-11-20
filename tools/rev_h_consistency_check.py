"""Rev H cross-format consistency audit of the wellhead example.
SQLite stored results <-> report JSON <-> SUMMARY JSON <-> XLSX <-> DOCX <-> PDF <-> PNG manifest
<-> README/EXAMPLE doc tables. Read-only. Usage: rev_h_consistency_check.py ROOT"""
import sys,json,hashlib,sqlite3,re
from pathlib import Path
from fractions import Fraction
ROOT=Path(sys.argv[1]).resolve();sys.path[:0]=[str(ROOT/'src')]
from fgmapping.services.coverage_report import summary_rows
from openpyxl import load_workbook
from docx import Document
from pypdf import PdfReader
ex=ROOT/'examples/wellhead_coverage';rep=ex/'WELLHEAD_COVERAGE_REPORT';out={};ok=True
def chk(name,cond,detail=None):
    global ok;ok&=bool(cond);out[name]={'pass':bool(cond),**({'detail':detail} if detail is not None else {})}
snap=json.loads((rep/'WELLHEAD_COVERAGE_REPORT.json').read_text());summ=json.loads((ex/'WELLHEAD_COVERAGE_SUMMARY.json').read_text())
con=sqlite3.connect(ex/'SYNTHETIC_WELLHEAD_COVERAGE.fgcase')
db={r[0]:(json.loads(r[1]),r[2],r[3],r[4]) for r in con.execute("select zone_id,result_json,input_hash,label,status from coverage_run where kind in ('FIRE_ZONE','GAS_ZONE')")}
bad=[]
for z in snap['zones']:
    r,ih,label,st=db[z['zone_id']];s=summ['zones'][z['zone_id']]
    if z['result']['fractions']!=r['fractions'] or z['input_hash']!=ih:bad.append(z['zone_id']+' report-vs-sqlite')
    if hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest() and abs(s['eligible_m3']-r['eligible_measure'])>0:bad.append(z['zone_id']+' summary eligible')
    for k in ('0ooN','1ooN','2ooN'):
        if s[k]!=r['fractions'][k]:bad.append(z['zone_id']+' summary '+k)
    if 'UNREVIEWED' not in label or z['lifecycle']!='COMPUTED - UNREVIEWED':bad.append(z['zone_id']+' lifecycle')
chk('sqlite_report_summary_values',not bad,bad)
rows=summary_rows(snap)
wb=load_workbook(rep/'WELLHEAD_COVERAGE_REPORT.xlsx');xl=[list(r) for r in wb['Summary'].values]
formulas=[(ws.title,c.coordinate) for ws in wb for row in ws.iter_rows() for c in row if c.data_type=='f']
chk('xlsx_summary_rows_exact',all(any(x[:len(r)]==list(r) for x in xl) for r in rows))
chk('xlsx_no_formula_cells',not formulas,formulas[:5])
doc=Document(rep/'WELLHEAD_COVERAGE_REPORT.docx');word=[[c.text for c in row.cells] for row in doc.tables[0].rows][1:]
idx=[0,2,3,4,5,6,8,9,10,11,12,13,14,15]
chk('docx_summary_rows_exact',len(word)==len(rows) and all([str(r[i]) for i in idx]==w for r,w in zip(rows,word)))
pdf=''.join(''.join(p.extract_text().split()) for p in PdfReader(rep/'WELLHEAD_COVERAGE_REPORT.pdf').pages)
chk('pdf_values_present',all(''.join(str(r[i]).split()) in pdf for r in rows for i in (0,6,8,9,10)))
chk('pdf_lifecycle_label','COMPUTED-UNREVIEWED' in pdf and 'Engineer-reviewed' not in pdf)
man=json.loads((rep/'MANIFEST.json').read_text());mb=[n for n,v in man['files'].items() if hashlib.sha256((rep/n).read_bytes()).hexdigest()!=v['sha256']]
chk('report_manifest_sha256',not mb,mb)
fig=[f for f in snap['figures'] if hashlib.sha256(__import__('base64').b64decode(f['png_base64'])).hexdigest()!=f['png_sha256']]
chk('figure_png_hashes',not fig and len(snap['figures'])==18,len(snap['figures']))
sc=summ['studies']['scenarios']['overall']['frequency_weighted_detected_fraction']
chk('scenario_fraction_independent_52_215',Fraction(sc).limit_denominator(10**6)==Fraction(52,215),sc)
op=summ['studies']['options'];chk('options_common_resolution',abs(float(op['existing_layout_2ooN'])-summ['zones']['FZ-MANIFOLD']['2ooN'])<1e-12,[op['existing_layout_2ooN'],summ['zones']['FZ-MANIFOLD']['2ooN']])
docbad=[]
for p in ('REVIEW_README.md','docs/EXAMPLE_WELLHEAD_MODULE.md'):
    t=(ROOT/p).read_text()
    for z,s in summ['zones'].items():
        m=re.search(r'\| %s \| (FG-[A-Z]+-GEO/[0-9.]+) \| ([0-9.]+) \| ([0-9.]+) %% \| ([0-9.]+) %% \| ([0-9.]+) %% \|' % z,t)
        if not m or m.group(1)!=s['method'] or m.group(2)!='%.1f' % s['eligible_m3'] or [m.group(i) for i in (3,4,5)]!=['%.1f' % (100*s[k]) for k in ('0ooN','1ooN','2ooN')]:docbad.append(p+' '+z)
chk('readme_and_example_doc_tables',not docbad,docbad)
ug=(ROOT/'USER_GUIDE.md').read_text();chk('user_guide_lifecycle_text','COMPUTED - UNREVIEWED' in ug and 'engineer-reviewed and not' not in ug)
print(json.dumps({'all_pass':ok,'checks':out},indent=1));sys.exit(0 if ok else 1)
