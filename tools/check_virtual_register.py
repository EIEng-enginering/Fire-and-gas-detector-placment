"""Linux offscreen cached-table resource check. No Windows responsiveness claim."""
import os,time,json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QTableView
from fgmapping.ui.register_model import RegisterModel
app=QApplication([]);t=time.perf_counter()
model=RegisterModel(('ID','Kind','Status'),[(f'SYN-{i}','EQUIPMENT','CANDIDATE') for i in range(10000)])
view=QTableView();view.setModel(model);view.resize(700,450);view.show();app.processEvents()
assert model.rowCount()==10000
for i in (0,4999,9999):assert model.data(model.index(i,0))==f'SYN-{i}'
print(json.dumps({'rows':10000,'create_and_first_paint_seconds':time.perf_counter()-t,'qt_platform':app.platformName(),'Windows_acceptance':'NOT RUN'}))
view.close()
