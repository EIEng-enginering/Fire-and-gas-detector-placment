"""Open the SYNTHETIC wellhead example in the real application window and capture screenshots.

Works on a temporary COPY of the case (the shipped example is never opened for
writing). Display only (CUTAWAY views hide the upper deck plates/beams in the viewer only; the case is unchanged); no calculation is run (engineering calculation BLOCKED).
Usage: python -B tools/capture_wellhead_app.py CASE.fgcase OUT_PREFIX
On Windows leave QT_QPA_PLATFORM unset to use the real 'windows' platform.
"""
import sys,json,shutil,tempfile
from pathlib import Path
from PySide6.QtWidgets import QApplication
from fgmapping.ui.main import MainWindow
from fgmapping.services.case import CaseSession
from fgmapping.services.basis import readiness
case=Path(sys.argv[1]).resolve();prefix=sys.argv[2]
app=QApplication([])
with tempfile.TemporaryDirectory() as tmp:
    copy=Path(tmp)/'wellhead_view.fgcase';shutil.copyfile(case,copy)
    w=MainWindow();w.settings.clear();w.session=CaseSession(copy,Path(tmp)/'runtime');s=w.session
    gate=readiness(s)['engineering_calculation_status']
    w.resize(1500,950);w.refresh();w.show();app.processEvents();outs=[]
    from fgmapping.services.geometry import get_scene
    upper={c.id for c in get_scene(s).components if c.id.startswith('UD-') or (c.id.startswith('BM-') and not c.id.startswith('BM-MZ'))}
    for theme,view,cut in (('light','Isometric',False),('light','Isometric',True),('dark','Isometric',True),('light','Top',True)):
        w.viewer.hidden=set(upper) if cut else set()
        out=Path(f'{prefix}_{theme}_{view}'+('_CUTAWAY' if cut else '')+'.png')
        if out.exists():raise SystemExit('Refusing to overwrite '+str(out))
        w.theme.setCurrentText(theme);w.viewer.camera(view);w.viewer.fit();app.processEvents();assert w.grab().save(str(out));outs.append(str(out))
    w.close();app.processEvents();s.close(discard_unsaved=True)
print(json.dumps({'platform':sys.platform,'Qt_platform':app.platformName(),'case':case.name,'engineering_calculation_status':gate,'screenshots':outs}))
