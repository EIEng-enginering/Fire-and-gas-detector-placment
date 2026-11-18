"""Write the Rev G starter detector library (CSV + XLSX).

ALL ENTRIES ARE EXAMPLE VALUES - replace with manufacturer data. They are generic,
illustrative performance shapes (no manufacturer is named or implied) so that the
coverage workflow can be exercised end to end. They are NOT datasheet values and
must not be used for project design.
Usage: python -B tools/build_starter_library.py OUT_DIR   (refuses to overwrite)
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from fgmapping.domain.detector_library import CONTRACT,validate_entry,write_csv,entry_to_row,CSV_HEADERS
EX='EXAMPLE VALUES - replace with manufacturer data'
SRC={'title':'Rev G starter library - generic example values (no manufacturer source)','revision':'G-EX-1','page':'n/a','data_status':EX}
def flame(id,tech,fuel,desc,kw,area,fov,contour,sens):
    return {'contract':CONTRACT,'id':id,'manufacturer':'GENERIC (example)','model':id,'detector_type':'FLAME','technology':tech,'fuel_or_gas':fuel,
            'target_fire':{'description':desc,'heat_release_kw':kw,'area_m2':area},'sensitivity_setting':sens,'fov':{'horizontal_deg':fov[0],'vertical_deg':fov[1]},
            'contour':contour,'alarm_threshold':None,'path_length_m':None,'mounting':'Bracket mounted, tilted down; orientation from detector register','source':dict(SRC),
            'notes':'EXAMPLE VALUES - illustrative cone-of-vision shape only. Replace with the manufacturer range-vs-angle table for the selected sensitivity and fuel.'}
def gas(id,tech,gasname,kind,threshold,path=None):
    return {'contract':CONTRACT,'id':id,'manufacturer':'GENERIC (example)','model':id,'detector_type':kind,'technology':tech,'fuel_or_gas':gasname,'target_fire':None,
            'sensitivity_setting':'Low alarm','fov':None,'contour':None,'alarm_threshold':{'value':threshold,'units':'%LEL' if kind=='POINT_GAS' else 'LEL.m'},
            'path_length_m':path,'mounting':'Per register position','source':dict(SRC),'notes':'EXAMPLE VALUES - replace with manufacturer alarm set-point and path-length data.'}
ENTRIES=[
 flame('EX-FLAME-IR3-HEPTANE','Multi-spectrum IR (IR3)','n-heptane','0.1 m2 n-heptane pool fire (example rating)',450.0,0.1,(90.0,90.0),[[0,50],[15,47],[30,40],[45,28]],'High (example)'),
 flame('EX-FLAME-IR3-METHANE','Multi-spectrum IR (IR3)','methane','Methane jet fire, 0.5 m plume (example rating)',450.0,None,(90.0,90.0),[[0,30],[15,28],[30,24],[45,16]],'High (example)'),
 flame('EX-FLAME-UVIR-HEPTANE','UV/IR','n-heptane','0.1 m2 n-heptane pool fire (example rating)',450.0,0.1,(90.0,90.0),[[0,25],[15,23],[30,19],[45,12]],'Standard (example)'),
 flame('EX-FLAME-IR3-HEPTANE-WIDE','Multi-spectrum IR (IR3)','n-heptane','0.1 m2 n-heptane pool fire (example rating)',450.0,0.1,(100.0,100.0),[[0,40],[20,36],[35,28],[50,15]],'Standard (example)'),
 gas('EX-GAS-IR-POINT-METHANE','Infrared point','methane','POINT_GAS',20.0),
 gas('EX-GAS-CAT-POINT-METHANE','Catalytic point','methane','POINT_GAS',20.0),
 gas('EX-GAS-OPGD-METHANE','Open-path IR','methane','OPEN_PATH',1.0,{'min':5.0,'max':120.0}),
]
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    csvp=out/'STARTER_DETECTOR_LIBRARY_EXAMPLE_VALUES.csv';xp=out/'STARTER_DETECTOR_LIBRARY_EXAMPLE_VALUES.xlsx'
    for p in (csvp,xp):
        if p.exists():raise SystemExit('Refusing to overwrite '+str(p))
    entries=[validate_entry(e) for e in ENTRIES]
    csvp.write_bytes(write_csv(entries))
    from openpyxl import Workbook
    wb=Workbook();ws=wb.active;ws.title='Library';ws.append(list(CSV_HEADERS))
    for e in entries:ws.append([entry_to_row(e)[h] for h in CSV_HEADERS])
    wb.save(xp);return [str(csvp),str(xp)]
if __name__=='__main__':print(main(sys.argv[1] if len(sys.argv)>1 else 'examples/library'))
