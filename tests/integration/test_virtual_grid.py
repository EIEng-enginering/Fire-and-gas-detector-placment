import os,subprocess,sys,unittest
class VirtualGrid(unittest.TestCase):
 def test_roles_numeric_sort_copy_and_follow(self):
  code='''from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from fgmapping.ui.worksheet import WorksheetView
app=QApplication([]);v=WorksheetView(('ID','X'));v.set_rows(('ID','X'),[('SYN-A',20.),('SYN-B',3.)]);v.show();app.processEvents()
for role in (Qt.DisplayRole,Qt.UserRole,Qt.BackgroundRole,Qt.FontRole):
 for i in range(2):v.cache.headerData(i,Qt.Horizontal,role);v.cache.data(v.cache.index(0,i),role)
v.sortByColumn(1,Qt.AscendingOrder);app.processEvents();assert v.item(0,0).text()=='SYN-B'
v.setCurrentIndex(v.proxy.index(0,1));QTest.keyClick(v,Qt.Key_C,Qt.ControlModifier);assert QApplication.clipboard().text()=='3.0';assert v.cache.copied
v.set_follow(True);assert v.cache.follow_id=='SYN-B';v.setColumnHidden(1,True);assert v.isColumnHidden(1);v.close()
'''
  r=subprocess.run([sys.executable,'-B','-c',code],env=dict(os.environ,QT_QPA_PLATFORM='offscreen'),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20)
  self.assertEqual(r.returncode,0,r.stdout);self.assertNotIn('Traceback',r.stdout)
