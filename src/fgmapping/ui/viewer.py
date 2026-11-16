"""CPU Qt 3D mesh viewer. Display only; never an engineering visibility engine.

Painter's algorithm has intersecting-face depth limitations. No claim of CAD
rendering qualification. Qt software display avoids an added GPU/VTK dependency.
"""
from __future__ import annotations
import math
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QPolygonF
from PySide6.QtWidgets import QWidget
from fgmapping.theme import THEMES

class MeshViewer(QWidget):
    selected=Signal(str)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.inspection_result=None;self.annotations={'placements':[],'zones':[]};self.scene=None;self.hidden=set();self.selection=None;self.theme='grey'
        self.yaw=-35.;self.pitch=30.;self.scale=24.;self.pan=[0.,0.];self.center=(10,6,2)
        self.perspective=False;self.polygons=[];self.last=None;self.dragged=False
        self.setMinimumSize(440,360);self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip('Left drag: orbit • Right drag: pan • Wheel: zoom • Click: select')
    def set_scene(self,scene):
        self.scene=scene;self.hidden.clear();self.selection=None;self.fit();self.update()
    def fit(self):
        if self.scene and self.scene.components:
            pts=[self.scene.frame(c.frame_id).world(p) for c in self.scene.components for p in c.mesh.vertices]
            self.center=tuple((min(p[i] for p in pts)+max(p[i] for p in pts))/2 for i in range(3))
            extent=max(max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3))
            self.scale=min(max(self.width(),440),max(self.height(),360))*.65/max(extent,1)
        self.pan=[0.,0.];self.update()
    def camera(self,name):
        self.perspective=name=='Perspective'
        self.yaw,self.pitch={'Top':(0,90),'Front':(0,0),'Side':(90,0),'Isometric':(-35,30),'Perspective':(-35,30)}[name]
        self.update()
    def state(self):return {k:(list(getattr(self,k)) if k in ('pan','center') else getattr(self,k)) for k in ('yaw','pitch','scale','pan','center','perspective')}
    def restore(self,state):
        for key in ('yaw','pitch','scale'):
            value=state.get(key)
            if isinstance(value,(int,float)) and math.isfinite(value):setattr(self,key,value)
        self.scale=max(.01,min(10000,self.scale))
        for key,n in (('pan',2),('center',3)):
            value=state.get(key)
            if isinstance(value,(list,tuple)) and len(value)==n and all(isinstance(x,(float,int)) and math.isfinite(x) for x in value):setattr(self,key,list(value))
        self.perspective=bool(state.get('perspective',False));self.update()
    def project(self,p):
        x,y,z=(p[i]-self.center[i] for i in range(3)); a,b=math.radians(self.yaw),math.radians(self.pitch)
        u=math.cos(a)*x-math.sin(a)*y; v=math.sin(a)*x+math.cos(a)*y
        h=math.cos(b)*z-math.sin(b)*v; depth=math.sin(b)*z+math.cos(b)*v
        factor=60/max(5,60-depth) if self.perspective else 1
        return QPointF(self.width()/2+self.pan[0]+u*self.scale*factor,self.height()/2+self.pan[1]-h*self.scale*factor),depth
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.Antialiasing)
        t=THEMES[self.theme];painter.fillRect(self.rect(),QColor(t['cells']))
        painter.setPen(QPen(QColor(t['alternate']),1))
        for i in range(-5,26,1):
            a,_=self.project((i,-5,0));b,_=self.project((i,20,0));painter.drawLine(a,b)
        for i in range(-5,21,1):
            a,_=self.project((-5,i,0));b,_=self.project((25,i,0));painter.drawLine(a,b)
        polys=[]
        colors={'DECK':'#a1afb5','EQUIPMENT':'#6c9baf','WALL':'#b89c79','PIPE':'#8ca891','GRATING':'#a6b9a9','DETECTOR':'#d49938'}
        if self.scene:
            for c in self.scene.components:
                if c.id in self.hidden:continue
                points=[self.project(self.scene.frame(c.frame_id).world(p)) for p in c.mesh.vertices]
                for face in c.mesh.faces:
                    poly=QPolygonF([points[i][0] for i in face]);depth=sum(points[i][1] for i in face)/3
                    polys.append((depth,c.id,poly,colors.get(c.semantic,'#95a2b3')))
        polys.sort(key=lambda x:x[0]);self.polygons=polys
        for depth,id,poly,color in polys:
            painter.setBrush(QColor('#ffd579' if id==self.selection else color))
            painter.setPen(QPen(QColor(t['accent'] if id==self.selection else t['border']),2 if id==self.selection else .7))
            painter.drawPolygon(poly)
        # Wire zones and stored orientation arrows are annotations, never coverage.
        for zone in self.annotations['zones']:
            low,high=zone['low'],zone['high']
            corners=[(x,y,z) for x in (low[0],high[0]) for y in (low[1],high[1]) for z in (low[2],high[2])]
            painter.setPen(QPen(QColor(t['accent'] if zone['id']==self.selection else '#b07a24' if zone['kind']=='FIRE_ZONE' else '#4b87aa'),2,Qt.DashLine))
            for i in range(8):
                for bit in (1,2,4):
                    j=i^bit
                    if i<j:painter.drawLine(self.project(corners[i])[0],self.project(corners[j])[0])
            painter.drawText(self.project(high)[0],zone['id'])
        for detector in self.annotations['placements']:
            if detector['id'] in self.hidden or detector['direction'] is None:continue
            start=detector['position'];end=tuple(start[i]+1.5*detector['direction'][i] for i in range(3))
            a,_=self.project(start);b,_=self.project(end);painter.setPen(QPen(QColor(t['accent']),2));painter.drawLine(a,b)
            painter.drawEllipse(b,3,3);painter.drawText(b,detector['id']+' orientation')
        if self.inspection_result:
            colors={'CLEAR':'#087b76','BLOCKED':'#9a4b24','INDETERMINATE':'#8b52aa'}
            for sample in self.inspection_result['samples']:
                point,_=self.project(sample['position_m']);color=QColor(colors[sample['state']]);painter.setBrush(color);painter.setPen(color);painter.drawEllipse(point,3,3)
            painter.setPen(QColor(t['text']));painter.drawText(14,44,'GEOMETRY ONLY: teal clear / brown blocked / purple indeterminate')
        painter.setPen(QColor(t['text']));painter.drawText(14,24,'LOCAL XYZ • metres • grid 1 m')
        painter.drawText(14,self.height()-16,'UNVERIFIED DISPLAY • NO ENGINEERING DETECTOR COVERAGE')
        # World-linked axis triad, translated to lower left.
        origin,_=self.project((0,0,0))
        for point,label,color in (((2,0,0),'X','#b63434'),((0,2,0),'Y','#2d733c'),((0,0,2),'Z','#3456b6')):
            end,_=self.project(point);start=QPointF(55,self.height()-78)
            stop=start+(end-origin)/max(self.scale,1)*20
            painter.setPen(QPen(QColor(color),2));painter.drawLine(start,stop);painter.drawText(stop,label)
    def mousePressEvent(self,event):self.last=event.position();self.dragged=False
    def mouseMoveEvent(self,event):
        if self.last is None:return
        diff=event.position()-self.last
        if abs(diff.x())+abs(diff.y())>1:self.dragged=True
        if event.buttons() & Qt.LeftButton:
            self.yaw+=diff.x()*.5;self.pitch=max(-89,min(90,self.pitch+diff.y()*.5))
        elif event.buttons() & Qt.RightButton:self.pan[0]+=diff.x();self.pan[1]+=diff.y()
        self.last=event.position();self.update()
    def mouseReleaseEvent(self,event):
        if not self.dragged and event.button()==Qt.LeftButton:
            for _,id,poly,_ in reversed(self.polygons):
                if poly.containsPoint(event.position(),Qt.OddEvenFill):
                    self.selection=id;self.selected.emit(id);self.update();break
        self.last=None
    def wheelEvent(self,event):
        self.scale=max(.01,min(10000,self.scale*1.15**(event.angleDelta().y()/120)));self.update()
