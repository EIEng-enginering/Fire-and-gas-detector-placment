"""Virtual cached worksheet. No database writes or calculations in Qt model."""
from PySide6.QtCore import QAbstractTableModel,Qt
from PySide6.QtGui import QFont,QColor
from fgmapping.theme import THEMES
class RegisterModel(QAbstractTableModel):
    def __init__(self,headers=(),rows=(),parent=None):
        super().__init__(parent);self.headers=tuple(headers);self.rows=tuple(rows);self.theme='grey';self.copied=set();self.follow_id=None
    def replace(self,headers,rows):
        self.beginResetModel();self.headers=tuple(headers);self.rows=tuple(rows);self.copied.clear();self.endResetModel()
    def rowCount(self,parent=None):return 0 if parent and parent.isValid() else len(self.rows)
    def columnCount(self,parent=None):return 0 if parent and parent.isValid() else len(self.headers)
    def data(self,index,role=Qt.DisplayRole):
        if not index.isValid() or not 0<=index.row()<len(self.rows):return None
        if role==Qt.DisplayRole:
            value=self.rows[index.row()][index.column()]
            return 'NOT SUPPLIED' if value is None else str(value)
        if role==Qt.UserRole:return self.rows[index.row()][index.column()]
        if role==Qt.BackgroundRole and (index.row(),index.column()) in self.copied:return QColor('#233a57' if self.theme=='dark' else '#dce9fd')
        if role==Qt.BackgroundRole and self.follow_id is not None and str(self.rows[index.row()][0])==self.follow_id:return QColor('#594814' if self.theme=='dark' else '#edd78c')
        if role==Qt.FontRole:return QFont('Segoe UI',15)
        if role==Qt.BackgroundRole:return QColor(THEMES[self.theme]['alternate' if index.row()%2 else 'cells'])
    def headerData(self,section,orientation,role=Qt.DisplayRole):
        if role==Qt.DisplayRole:
            if orientation==Qt.Horizontal:return self.headers[section] if 0<=section<len(self.headers) else None
            return str(section+1)
        if role==Qt.FontRole:return QFont('Segoe UI',14)
