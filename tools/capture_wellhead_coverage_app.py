"""Open the SYNTHETIC wellhead COVERAGE example in the real application window and capture
heatmap / FOV / results-table screenshots. Works on a temporary COPY (the example is never
written). EXAMPLE library values - not for design. Engineer-reviewed results - not independently certified.
Usage: python -B tools/capture_wellhead_coverage_app.py CASE.fgcase OUT_PREFIX [--show SECONDS]
On Windows leave QT_QPA_PLATFORM unset to use the real 'windows' platform.
"""
import sys,json,shutil,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from fgmapping.ui.main import MainWindow
from fgmapping.services.case import CaseSession
from fgmapping.services.basis import readiness
from fgmapping.services import coverage as cov
case=Path(sys.argv[1]).resolve();prefix=sys.argv[2];show=float(sys.argv[sys.argv.index('--show')+1]) if '--show' in sys.argv else 0
app=QApplication([])
def save(widget,name,outs):
    out=Path(f'{prefix}_{name}.png')
    if out.exists():raise SystemExit('Refusing to overwrite '+str(out))
    app.processEvents();assert widget.grab().save(str(out));outs.append(str(out))
with tempfile.TemporaryDirectory() as tmp:
    copy=Path(tmp)/'wellhead_coverage_view.fgcase';shutil.copyfile(case,copy)
    w=MainWindow();w.settings.clear();w.session=CaseSession(copy,Path(tmp)/'runtime');s=w.session
    gate=readiness(s)['engineering_calculation_status'];runs=cov.latest_runs(s)
    w.resize(1500,950);w.refresh();w.show();app.processEvents();outs=[]
    from fgmapping.services.geometry import get_scene
    upper={c.id for c in get_scene(s).components if c.id.startswith('UD-') or (c.id.startswith('BM-') and not c.id.startswith('BM-MZ'))}
    w.viewer.hidden=set(upper);w.theme.setCurrentText('light')
    for zone,z,view in (('FZ-WELLBAY',4.25,'Top'),('FZ-WELLBAY',4.25,'Isometric'),('FZ-MANIFOLD',2.25,'Top'),('GZ-WELLBAY',0.25,'Top'),('GZ-MODULE',0.25,'Isometric')):
        w.show_heatmap(runs[zone],z);w.viewer.camera(view);w.viewer.fit();save(w,f'{zone}_z{z:.2f}_{view}',outs)
    w.clear_overlay();w.toggle_fov();w.viewer.camera('Isometric');w.viewer.fit();save(w,'FLAME_FOV_Isometric',outs);w.toggle_fov()
    def grab_dialog():
        d=app.activeModalWidget()
        if d is None:QTimer.singleShot(100,grab_dialog);return
        save(d,'RESULTS_TABLE',outs);d.reject()
    QTimer.singleShot(300,grab_dialog);w.results_dialog()
    if show:
        w.show_heatmap(runs['FZ-WELLBAY'],4.25);w.viewer.camera('Isometric');w.viewer.fit();w.raise_();w.activateWindow()
        QTimer.singleShot(int(show*1000),app.quit);app.exec()
    w.close();app.processEvents();s.close(discard_unsaved=True)
print(json.dumps({'platform':sys.platform,'Qt_platform':app.platformName(),'case':case.name,'engineering_calculation_status':gate,'runs':sorted(runs),'screenshots':outs}))
