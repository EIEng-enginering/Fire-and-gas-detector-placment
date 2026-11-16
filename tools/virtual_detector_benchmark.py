"""Actual Rev C detector worksheet with 10,000 cached rows; Linux offscreen only."""
import os,time,json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from fgmapping.ui.main import MainWindow
app=QApplication([]);w=MainWindow();t=time.perf_counter()
rows=[(f'SYN-FD-{i:05d}','FLAME',float(i%100),float(i//100),3.,'SYN-E','CANDIDATE') for i in range(10000)]
w.table.set_rows(('Tag','Type','X (m)','Y (m)','Z (m)','Evidence','Review'),rows);w.show();app.processEvents();first=time.perf_counter()-t
assert w.table.rowCount()==10000
start=time.perf_counter();w.table.filter('SYN-FD-09999');app.processEvents();assert w.table.rowCount()==1;assert w.table.item(0,0).text()=='SYN-FD-09999';filter_seconds=time.perf_counter()-start
w.table.filter('');app.processEvents();assert w.table.rowCount()==10000
print(json.dumps({'rows':10000,'main_detector_view':'WorksheetView / QTableView virtual model','first_paint_seconds':first,'single_id_filter_seconds':filter_seconds,'platform':app.platformName(),'Windows':'NOT RUN'}));w.close()
