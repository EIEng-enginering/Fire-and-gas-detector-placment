"""Build examples/SYNTHETIC_WELLHEAD_COVERAGE.fgcase from the synthetic wellhead example (Rev G).

Applies the full coverage workflow: schema 4, starter library (EXAMPLE VALUES), explicit
library assignment for all 23 detectors, per-zone setups with EXAMPLE user targets, study
basis references, flame + geographic gas runs, a coverage report and heatmap figures.

ALL detector data are EXAMPLE VALUES - replace with manufacturer data before project use.
Engineer-reviewed results - not independently certified.
Usage: python tools/build_wellhead_coverage_example.py OUT_FOLDER [--grid 1.0]
"""
from __future__ import annotations
import argparse,json,shutil,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from fgmapping.services.case import CaseSession
from fgmapping.services import coverage as cov
from fgmapping.services import workspace as w
from fgmapping.services.basis import set_basis,readiness
ACTOR='EXAMPLE_ENGINEER';EV='SYN-WHM-COV-01'
FLAME_LIB='EX-FLAME-IR3-METHANE';POINT_LIB='EX-GAS-IR-POINT-METHANE';OP_LIB='EX-GAS-OPGD-METHANE'
TARGETS={'1ooN':'0.90','2ooN':'0.80'}   # EXAMPLE user-defined targets for illustration only
CRIT='EXAMPLE project performance targets (illustrative) - to be set and approved by the project engineer; not from any standard'

def flame_setup(zone,grid,refine):
    return {'contract':'fg-coverage-setup/1','zone_id':zone,'method':'FLAME_GEOGRAPHIC','grid_spacing_m':grid,'mode':'VOLUME','slice_elevations_m':[],'voting_required':2,'performance_targets':dict(TARGETS),
            'convergence':{'refinement':refine,'tolerance':'0.02'},'criterion_reference':CRIT,'standoff_m':0.05,'tolerance_m':1e-6,
            'flame':{'fuel':'methane','heat_release_kw':450.0,'fire_size_scaling':'NONE','target_geometry':{'type':'POINT'},'min_visible_fraction':1.0},'gas':None,
            'notes':'EXAMPLE: 450 kW methane jet/pool target matching the EXAMPLE library entry; point target at each cell'}
def gas_setup(zone,grid,refine):
    return {'contract':'fg-coverage-setup/1','zone_id':zone,'method':'GAS_GEOGRAPHIC','grid_spacing_m':grid,'mode':'VOLUME','slice_elevations_m':[],'voting_required':2,'performance_targets':dict(TARGETS),
            'convergence':{'refinement':refine,'tolerance':'0.02'},'criterion_reference':CRIT,'standoff_m':0.0,'tolerance_m':1e-6,'flame':None,
            'gas':{'gas':'methane','cloud':{'shape':'SPHERE','diameter_m':5.0},'cloud_concentration_pct_lel':100.0,'detector_types':['POINT_GAS','OPEN_PATH']},
            'notes':'EXAMPLE geographic design cloud: 5 m diameter sphere at 100 %LEL (user choice, not dispersion)'}

def example_scenarios():
    sys.path.insert(0,str(ROOT/'tools'));from build_wellhead_example import WELLS
    src='EXAMPLE VALUE - illustrative frequency, not from a leak/ignition frequency study'
    sc=[]
    for id,x,y in WELLS:
        sc.append({'id':'SC-FIRE-'+id,'zone_id':'FZ-WELLBAY','location':[x+1.0,y,1.0],'frequency_per_year':'0.0005','frequency_source':src,'notes':'EXAMPLE wellhead fire beside tree '+id})
        sc.append({'id':'SC-GAS-'+id,'zone_id':'GZ-WELLBAY','location':[x,y+1.2,1.5],'frequency_per_year':'0.002','frequency_source':src,'notes':'EXAMPLE small leak at tree '+id})
    sc+= [{'id':'SC-FIRE-MF','zone_id':'FZ-MANIFOLD','location':[24.0,10.0,1.0],'frequency_per_year':'0.001','frequency_source':src,'notes':'EXAMPLE manifold fire'},
          {'id':'SC-GAS-MF-LARGE','zone_id':'GZ-MANIFOLD','location':[25.5,8.0,1.0],'frequency_per_year':'0.0002','frequency_source':src,'cloud':{'shape':'SPHERE','diameter_m':10.0},'notes':'EXAMPLE larger manifold release (10 m design cloud)'},
          {'id':'SC-FIRE-WL','zone_id':'FZ-WIRELINE','location':[3.5,9.5,1.0],'frequency_per_year':'0.0003','frequency_source':src,'notes':'EXAMPLE wireline area fire'}]
    return {'contract':'fg-coverage-scenarios/1','notes':'EXAMPLE scenario set - frequencies illustrative only','scenarios':sc}

def example_options():
    c=lambda id,x,y,z,az,el:{'id':id,'detector_type':'FLAME','position':[x,y,z],'azimuth':az,'elevation':el,'roll':0.0,'library_id':FLAME_LIB,'receiver':None,'cost':'1','feasible':True,'maintainable':True,'notes':'EXAMPLE candidate'}
    return {'contract':'fg-coverage-options/1','zone_id':'FZ-MANIFOLD','include_existing':True,'max_detectors':2,'required_votes':2,'grid_spacing_m':1.0,'notes':'EXAMPLE candidates to raise 2ooN in FZ-MANIFOLD; proposals only',
            'candidates':[c('CAND-MF-1',22.9,3.7,4.3,60.,-30.),c('CAND-MF-2',27.9,16.3,4.3,-120.,-30.),c('CAND-MF-3',22.9,16.3,4.3,-60.,-30.),c('CAND-MF-4',27.9,3.7,4.3,120.,-30.)]}

def build(out,grid=1.0,refine=1,progress=print,studies=True):
    out=Path(out);case=out/'SYNTHETIC_WELLHEAD_COVERAGE.fgcase'
    if case.exists():raise SystemExit('Refusing to overwrite '+str(case))
    out.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'examples/SYNTHETIC_WELLHEAD_MODULE.fgcase',case)
    rt=tempfile.TemporaryDirectory();s=CaseSession(case,Path(rt.name)/'runtime')
    try:
        cov.enable_coverage(s,ACTOR)
        s.add_evidence(EV,'SYNTHETIC','Rev G example coverage inputs: EXAMPLE library values and EXAMPLE targets','A','Generated by tools/build_wellhead_coverage_example.py',ACTOR)
        lib=ROOT/'examples/library/STARTER_DETECTOR_LIBRARY_EXAMPLE_VALUES.csv'
        cov.import_library(s,lib.read_bytes(),'CSV',ACTOR)
        for d in w.detector_rows(s):
            if d['detector_type']=='FLAME':cov.assign_library(s,d['id'],FLAME_LIB,EV,ACTOR)
            elif d['detector_type']=='POINT_GAS':cov.assign_library(s,d['id'],POINT_LIB,EV,ACTOR)
            else:cov.assign_library(s,d['id'],OP_LIB,EV,ACTOR,receiver={'record_id':d['id']+'-RX'})
        b=json.loads(w.row(s,'study_basis','STUDY')['payload_json'])
        b.update({'criterion_reference':'Per-zone coverage setups (EXAMPLE targets 1ooN 0.90 / 2ooN 0.80, illustrative only)','fuel_or_gas':'methane (EXAMPLE)',
                  'target_description':'Flame: 450 kW methane fire point target (EXAMPLE). Gas: 5 m diameter spherical design cloud at 100 %LEL (EXAMPLE, geographic)'})
        set_basis(s,b,EV,ACTOR)
        for z in cov.zones(s):
            cov.set_zone_setup(s,(flame_setup if z['kind']=='FIRE_ZONE' else gas_setup)(z['id'],grid,refine),EV,ACTOR)
        r=readiness(s)
        if r['engineering_calculation_status']!='READY':raise SystemExit('Not ready: '+json.dumps(r['engineering_blockers']))
        t=time.time();res=cov.run_all(s,'WHM-COV-A',ACTOR);progress('runs %.1f s' % (time.time()-t))
        s.save();study={}
        if studies:
            from fgmapping.services import scenario_coverage as sc
            (out/'WELLHEAD_EXAMPLE_SCENARIOS.json').write_text(json.dumps(example_scenarios(),indent=1));(out/'WELLHEAD_EXAMPLE_OPTIONS.json').write_text(json.dumps(example_options(),indent=1))
            r1=sc.run_scenarios(s,example_scenarios(),'WHM-SCN-A',ACTOR);r2=sc.run_options(s,example_options(),'WHM-OPT-A',ACTOR);s.save()
            study={'scenarios':{'overall':r1['overall'],'by_zone':r1['by_zone']},'options':{'existing_layout_2ooN':r2['existing_layout_fraction'],'pareto':r2['pareto'][:5]}}
        summary={z:{'method':v['method_version'],'1ooN':v['fractions']['1ooN'],'2ooN':v['fractions']['2ooN'],'0ooN':v['fractions']['0ooN'],'targets':{k:x['status'] for k,x in v['performance_targets'].items()},'convergence':v['convergence']['status'],'eligible_m3':v['eligible_measure'],'excluded_m3':v['excluded_measure']} for z,v in res.items()}
        (out/'WELLHEAD_COVERAGE_SUMMARY.json').write_text(json.dumps({'note':'EXAMPLE library values and EXAMPLE targets - illustrative only, not for design. Engineer-reviewed results - not independently certified.','grid_m':grid,'zones':summary,'studies':study},indent=1))
        from fgmapping.services.coverage_report import export_coverage_report
        rep=export_coverage_report(s,out,'WELLHEAD_COVERAGE_REPORT');s.save()
        return case,summary,rep
    finally:
        s.close();rt.cleanup()
        for extra in out.glob('*.writer.lock'):extra.unlink()

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out');a.add_argument('--grid',type=float,default=1.0);a.add_argument('--refine',type=int,default=1);n=a.parse_args()
    case,summary,rep=build(n.out,n.grid,n.refine)
    print(case);print(json.dumps(summary,indent=1));print(rep['folder'])
