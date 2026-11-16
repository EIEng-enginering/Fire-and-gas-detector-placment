"""Virtual worksheet view, cached filter/sort, clipboard copy and paste request.

All mutation belongs to services; this view only emits user-intent signals.
"""
from PySide6.QtCore import Qt,QSortFilterProxyModel,Signal
from PySide6.QtGui import QKeySequence,QColor
from PySide6.QtWidgets import QTableView,QApplication,QAbstractItemView,QMenu
from fgmapping.ui.register_model import RegisterModel
class TextItem:
 def __init__(self,value):self.value=value
 def text(self):return str(self.value)
class WorksheetView(QTableView):
 cellClicked=Signal(int,int)
 pasteRequested=Signal(str,int,int)
 notice=Signal(str)
 def __init__(self,headers=(),parent=None):
  super().__init__(parent);self.cache=RegisterModel(headers,());self.proxy=QSortFilterProxyModel(self)
  self.proxy.setSourceModel(self.cache);self.proxy.setSortRole(Qt.UserRole);self.proxy.setFilterKeyColumn(-1);self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive);self.setModel(self.proxy)
  self.setSortingEnabled(True);self.sortByColumn(0,Qt.AscendingOrder)
  self.setSelectionMode(QAbstractItemView.ExtendedSelection);self.setSelectionBehavior(QAbstractItemView.SelectItems)
  self.setEditTriggers(QAbstractItemView.NoEditTriggers);self.clicked.connect(lambda index:self.cellClicked.emit(index.row(),index.column()))
  self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu);self.horizontalHeader().customContextMenuRequested.connect(self.columns_menu)
  self.horizontalHeader().setDefaultSectionSize(135);self.verticalHeader().setDefaultSectionSize(34)
 def set_rows(self,headers,rows):self.cache.replace(headers,rows)
 def rowCount(self):return self.proxy.rowCount()
 def currentRow(self):return self.currentIndex().row()
 def setRowCount(self,n):
  if n!=0:raise ValueError('Use set_rows for virtual worksheet data')
  self.cache.replace(self.cache.headers,())
 def item(self,row,col):return TextItem(self.proxy.data(self.proxy.index(row,col)) or '')
 def filter(self,text):self.proxy.setFilterFixedString(text)
 def select_id(self,id):
  for row in range(self.rowCount()):
   if self.item(row,0).text()==id:self.selectRow(row);self.scrollTo(self.proxy.index(row,0));return True
  return False
 def columns_menu(self,point):
  menu=QMenu(self)
  for col,title in enumerate(self.cache.headers):
   action=menu.addAction(title);action.setCheckable(True);action.setChecked(not self.isColumnHidden(col));action.toggled.connect(lambda checked,c=col:self.setColumnHidden(c,not checked))
  follow=menu.addAction('Follow selected row');follow.setCheckable(True);follow.setChecked(self.cache.follow_id is not None)
  follow.toggled.connect(lambda checked:self.set_follow(checked));menu.exec(self.horizontalHeader().mapToGlobal(point))
 def set_follow(self,enabled):
  self.cache.follow_id=self.item(self.currentRow(),0).text() if enabled and self.currentRow()>=0 else None;self.viewport().update()
 def keyPressEvent(self,event):
  if event.matches(QKeySequence.Copy):
   indexes=self.selectedIndexes()
   if not indexes:return
   r0=min(i.row() for i in indexes);r1=max(i.row() for i in indexes);c0=min(i.column() for i in indexes);c1=max(i.column() for i in indexes)
   if (r1-r0+1)*(c1-c0+1)>50000:self.notice.emit('Copy exceeds 50,000-cell development budget');return
   selected={(i.row(),i.column()) for i in indexes}
   text='\n'.join('\t'.join(self.item(r,c).text() if (r,c) in selected else '' for c in range(c0,c1+1)) for r in range(r0,r1+1))
   QApplication.clipboard().setText(text)
   self.cache.copied={(self.proxy.mapToSource(i).row(),self.proxy.mapToSource(i).column()) for i in indexes};self.viewport().update();self.notice.emit(f'Copied {len(indexes)} cells');return
  if event.matches(QKeySequence.Paste):
   index=self.currentIndex()
   if index.isValid():self.pasteRequested.emit(QApplication.clipboard().text(),index.row(),index.column())
   return
  if event.matches(QKeySequence.Cut):self.notice.emit('Cut refused: mandatory engineering fields cannot be cleared. Use Copy or the explicit remove command.');return
  super().keyPressEvent(event)
