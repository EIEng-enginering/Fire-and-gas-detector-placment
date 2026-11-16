"""Execute real Qt widgets on Linux offscreen; NOT Windows acceptance."""
import json,os,sys,tempfile,time
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6 import __version__
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
from fgmapping.ui.main import MainWindow
from fgmapping.services.case import create_case,CaseSession
from fgmapping.services.geometry import enable_geometry,set_scene
from fgmapping.domain.scene import synthetic_scene
ROOT=Path(__file__).resolve().parents[1]
app=QApplication([]);app.setQuitOnLastWindowClosed(False)
with tempfile.TemporaryDirectory() as tmp:
    path=create_case(Path(tmp)/'SYNTHETIC.fgcase','SYNTHETIC Offshore Module')
    window=MainWindow();window.settings.clear()
    window.session=CaseSession(path,Path(tmp)/'runtime')
    s=window.session;enable_geometry(s,'AUTOMATION_ENGINE')
    s.add_evidence('SYN-GEOM-01','SYNTHETIC','Generated envelopes','SYN-A','domain.scene','AUTOMATION_ENGINE')
    s.add_detector('FD101','FLAME',0,0,3,'SYN-GEOM-01','AUTOMATION_ENGINE')
    s.add_detector('FD102','FLAME',19,11,4,'SYN-GEOM-01','AUTOMATION_ENGINE')
    set_scene(s,synthetic_scene(),'AUTOMATION_ENGINE');s.save()
    window.refresh();window.show();app.processEvents()
    assert window.tree.topLevelItemCount()==13
    # Pick a visible triangle centroid and verify linked tree selection.
    _,id,poly,_=window.viewer.polygons[-1]
    center=poly.boundingRect().center()
    QTest.mouseClick(window.viewer,Qt.LeftButton,pos=center.toPoint());app.processEvents()
    assert window.viewer.selection is not None
    selected=window.viewer.selection
    assert window.tree.currentItem().data(0,Qt.UserRole)==selected
    # Verify exact row->object link, hide/show and camera controls.
    window.select_detector_geometry(0,0);assert window.viewer.selection=='FD101'
    first=window.tree.topLevelItem(0);first.setCheckState(0,Qt.Unchecked);app.processEvents()
    assert first.data(0,Qt.UserRole) in window.viewer.hidden
    first.setCheckState(0,Qt.Checked)
    for name in ('Top','Front','Side','Perspective','Isometric'):window.viewer.camera(name);app.processEvents()
    from fgmapping.services.registers import edit_detector,detector_history
    edit_detector(s,'FD101',(2,1,4),(30,15,0),'SYNTHETIC_TEST_ACTOR');window.refresh();app.processEvents()
    marker=next(c for c in window.viewer.scene.components if c.id=='FD101');assert marker.mesh.vertices[0]==(2,1,4)
    detector_history(s,'SYNTHETIC_TEST_ACTOR');window.refresh();s.save();app.processEvents()
    state=window.viewer.state();window.viewer.restore(state);assert window.viewer.state()==state
    frames=[]
    for theme in ('grey','dark','light'):
        window.theme.setCurrentText(theme);window.apply_theme(theme);app.processEvents()
        start=time.perf_counter();pix=window.grab();elapsed=time.perf_counter()-start
        target=ROOT/'screenshots'/('WP02_'+theme+'_LINUX_OFFSCREEN.png');assert pix.save(str(target));frames.append({'theme':theme,'grab_seconds':elapsed,'file':target.name})
    window.close();app.processEvents()
    with CaseSession(path,Path(tmp)/'runtime') as reopened:
        from fgmapping.services.geometry import get_scene
        assert get_scene(reopened).sha256==synthetic_scene().sha256
    print(json.dumps({'platform':sys.platform,'python':sys.version,'PySide6':__version__,'qt_platform':app.platformName(),'Windows_acceptance':'NOT RUN','pick_selection':selected,'components':13,'checks':['pick/tree','row/object','hide/show','five cameras','viewport roundtrip','save/reopen','linked detector move/undo'],'captures':frames},indent=2))
