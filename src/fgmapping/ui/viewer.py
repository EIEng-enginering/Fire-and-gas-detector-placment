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
        self.coverage=None;self.fov=[];self.grid_bounds=(-5,-5,25,20)
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
            lo=[min(p[i] for p in pts) for i in range(2)];hi=[max(p[i] for p in pts) for i in range(2)]
            self.grid_bounds=(math.floor(lo[0])-5,math.floor(lo[1])-5,math.ceil(hi[0])+5,math.ceil(hi[1])+5)
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
        gx0,gy0,gx1,gy1=self.grid_bounds
        for i in range(int(gx0),int(gx1)+1,1):
            a,_=self.project((i,gy0,0));b,_=self.project((i,gy1,0));painter.drawLine(a,b)
        for i in range(int(gy0),int(gy1)+1,1):
            a,_=self.project((gx0,i,0));b,_=self.project((gx1,i,0));painter.drawLine(a,b)
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
        self.paint_fov(painter);self.paint_coverage(painter,t)
        painter.setPen(QColor(t['text']));painter.drawText(14,24,'LOCAL XYZ • metres • grid 1 m')
        if not self.coverage:painter.drawText(14,self.height()-16,'GEOMETRY DISPLAY • no coverage overlay selected')
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

    VOTE_COLOURS=('#d62728','#f2b400','#2ca02c','#145a32')
    def paint_coverage(self,painter,t):
        """Coverage heatmap overlay: cells of one plan slice coloured by detector votes."""
        c=self.coverage
        if not c:return
        h=c['spacing']/2;z=c['slice_z'];n=0
        painter.setPen(Qt.NoPen)
        for x,y,zz,w,votes in c['rows']:
            if abs(zz-z)>1e-6:continue
            k=min(len(votes),3);col=QColor(self.VOTE_COLOURS[k]);col.setAlpha(150);painter.setBrush(col)
            poly=QPolygonF([self.project((x+dx,y+dy,zz))[0] for dx,dy in ((-h,-h),(h,-h),(h,h),(-h,h))]);painter.drawPolygon(poly);n+=1
        y0=self.height()-16
        for i,(label,colour) in enumerate(zip(('0 votes','1 vote','2 votes','3+ votes'),self.VOTE_COLOURS)):
            painter.setBrush(QColor(colour));painter.setPen(QColor(t['border']));painter.drawRect(14+i*80,y0-30,12,12);painter.setPen(QColor(t['text']));painter.drawText(30+i*80,y0-19,label)
        painter.setPen(QColor(t['text']))
        painter.drawText(14,y0,c['legend']+' | slice z=%.2f m | %d cells' % (z,n))
        painter.drawText(14,42,'COVERAGE OVERLAY: '+c['title'])
    def paint_fov(self,painter):
        """Detector field-of-view wireframe from the assigned library contour (display only)."""
        for f in self.fov:
            pos=f['position'];fwd,right,up=f['frame'];pen=QPen(QColor('#c0392b' if f.get('selected') else '#e67e22'),1.4 if f.get('selected') else .9,Qt.SolidLine);painter.setPen(pen)
            rays=[]
            for k in range(24):
                a=2*math.pi*k/24;h=f['fov_h']/2*math.cos(a);v=f['fov_v']/2*math.sin(a)
                th,tv=math.tan(math.radians(min(h,89.9) if h>=0 else max(h,-89.9))),math.tan(math.radians(min(v,89.9) if v>=0 else max(v,-89.9)))
                d=tuple(fwd[i]+th*right[i]+tv*up[i] for i in range(3));n=math.sqrt(sum(x*x for x in d));d=tuple(x/n for x in d)
                off=math.degrees(math.acos(max(-1,min(1,sum(d[i]*fwd[i] for i in range(3))))));r=f['range'](off)
                rays.append(tuple(pos[i]+d[i]*r for i in range(3)))
            a,_=self.project(pos)
            for k,p in enumerate(rays):
                b,_=self.project(p)
                if k%6==0:painter.drawLine(a,b)
                c,_=self.project(rays[(k+1)%len(rays)]);painter.drawLine(b,c)
            end=tuple(pos[i]+fwd[i]*f['range'](0) for i in range(3));painter.drawLine(a,self.project(end)[0])
