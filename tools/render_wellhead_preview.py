"""Render isometric/plan preview PNGs of a stored .fgcase scene (matplotlib; tool-only).

Reads geometry, candidate detector positions and zones FROM THE CASE through the
application services. Display only: detector symbols show stated candidate
positions/orientations, NOT field of view, response or coverage.
matplotlib is an optional tool dependency, not an application requirement.
Usage: python -B tools/render_wellhead_preview.py CASE.fgcase OUT_PREFIX
Refuses to overwrite existing PNGs.
"""
import sys,tempfile,shutil,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection,Line3DCollection
from fgmapping.services.case import CaseSession
from fgmapping.services.geometry import get_scene
from fgmapping.services import workspace as w
COLORS={'DECK':'#a1afb5','EQUIPMENT':'#6c9baf','WALL':'#b89c79','PIPE':'#7fa985','GRATING':'#c7d3c4','STRUCTURE':'#7d858c','ESCAPE_ROUTE':'#3cb44b','AREA_MARKER':'#f0c419','DETECTOR':'#d49938'}
DET={'FLAME':('#d62728','^'),'POINT_GAS':('#1f77b4','o'),'OPEN_PATH':('#9467bd','s')}
def load(case):
    with tempfile.TemporaryDirectory() as tmp:
        copy=Path(tmp)/'view.fgcase';shutil.copyfile(case,copy)
        with CaseSession(copy,Path(tmp)/'rt') as s:
            scene=get_scene(s);dets=w.detector_rows(s);details={d['id']:w.row(s,'detector_details',d['id']) for d in dets}
            ann=w.display_annotations(s);name=s.name()
            recs=[dict(zip(('id','kind','payload'),r)) for r in s.con.execute("SELECT id,kind,payload_json FROM engineering_record WHERE id LIKE '%-RX'")]
    return scene,dets,details,ann,name,recs
def draw(ax,scene,dets,details,ann,hide=(),zones=True,recs=()):
    import json
    pos={d['id']:(d['x'],d['y'],d['z']) for d in dets}
    for c in scene.components:
        if c.id in hide:continue
        f=scene.frame(c.frame_id);v=[f.world(p) for p in c.mesh.vertices]
        tris=[[v[i] for i in face] for face in c.mesh.faces]
        alpha={'WALL':.55,'DECK':.35,'GRATING':.45,'ESCAPE_ROUTE':.9,'AREA_MARKER':.8}.get(c.semantic,.95)
        ax.add_collection3d(Poly3DCollection(tris,facecolor=COLORS.get(c.semantic,'#95a2b3'),edgecolor='none',alpha=alpha))
    if zones:
        for z in ann['zones']:
            (x,y,zz),(X,Y,Z)=z['low'],z['high'];col='#ff7f0e' if z['kind']=='FIRE_ZONE' else '#17becf'
            corners=[(x,y,zz),(X,y,zz),(X,Y,zz),(x,Y,zz),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)];edges=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
            ax.add_collection3d(Line3DCollection([[corners[a],corners[b]] for a,b in edges],colors=col,linewidths=.7,linestyles='dashed'))
    for d in dets:
        col,m=DET.get(d['detector_type'],('k','x'));ax.scatter([d['x']],[d['y']],[d['z']],c=col,marker=m,s=70,depthshade=False,edgecolors='k',linewidths=.6,zorder=10)
        det=details[d['id']];a,e=math.radians(det['azimuth']),math.radians(det['elevation'])
        if d['detector_type']=='FLAME':pass
        if d['detector_type']=='FLAME':ax.plot([d['x'],d['x']+1.6*math.cos(e)*math.cos(a)],[d['y'],d['y']+1.6*math.cos(e)*math.sin(a)],[d['z'],d['z']+1.6*math.sin(e)],c=col,lw=1.2,zorder=10)
def _rx(ax,recs,pos):
    import json
    for r in recs:
        p=json.loads(r['payload']);tx=r['id'][:-3];x,y,z=p['position']
        ax.scatter([x],[y],[z],c='#9467bd',marker='D',s=40,depthshade=False,edgecolors='k',linewidths=.5,zorder=10)
        if tx in pos:a=pos[tx];ax.plot([a[0],x],[a[1],y],[a[2],z],c='#9467bd',lw=.9,ls=':',zorder=9)
def finish(ax,title):
    ax.set_xlim(0,30);ax.set_ylim(0,20);ax.set_zlim(-1.5,12.5);ax.set_box_aspect((30,20,14))
    ax.set_xlabel('X east (m)');ax.set_ylabel('Y north (m)');ax.set_zlabel('Z up (m)');ax.set_title(title,fontsize=9)
def legend(fig):
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    h=[Line2D([],[],marker=m,color=c,ls='',markeredgecolor='k',label=t.replace('_',' ')+' (candidate)') for t,(c,m) in DET.items()]
    h+=[Patch(color=COLORS[k],label=k.title().replace('_',' ')) for k in ('DECK','GRATING','STRUCTURE','WALL','EQUIPMENT','PIPE','ESCAPE_ROUTE','AREA_MARKER')]
    h+=[Line2D([],[],marker='D',color='#9467bd',ls=':',markeredgecolor='k',label='Open-path RX position (pairing line only)')]
    h+=[Line2D([],[],color='#ff7f0e',ls='--',label='Fire zone'),Line2D([],[],color='#17becf',ls='--',label='Gas zone')]
    fig.legend(handles=h,loc='lower center',ncol=7,fontsize=7,frameon=False)
def main(case,prefix):
    scene,dets,details,ann,name,recs=load(case);outs=[]
    upper=[c.id for c in scene.components if c.id.startswith('UD-') or c.id.startswith('BM-') and not c.id.startswith('BM-MZ')]
    banner='SYNTHETIC / ILLUSTRATIVE - not a real facility - geometry and candidate inputs only - NO detector coverage (engineering calculation BLOCKED)'
    views=[('_ISO.png','Isometric from south-east (open sides)',-60,28,(),True),('_ISO_CUTAWAY.png','Isometric cut-away: upper deck and beams hidden, zones shown',-60,32,upper,True),('_ISO_NW.png','Isometric from north-west (blast/fire walls)',125,25,upper,False),('_PLAN.png','Plan view (upper deck hidden)',-90,90,upper,False)]
    for suffix,title,az,el,hide,zones in views:
        out=Path(prefix+suffix)
        if out.exists():raise SystemExit('Refusing to overwrite '+str(out))
        fig=plt.figure(figsize=(13,9),dpi=110);ax=fig.add_subplot(111,projection='3d');ax.computed_zorder=False;draw(ax,scene,dets,details,ann,hide,zones);_rx(ax,recs,{d['id']:(d['x'],d['y'],d['z']) for d in dets});ax.view_init(elev=el,azim=az);finish(ax,name+'\n'+title)
        fig.text(.5,.985,banner,ha='center',fontsize=8,color='#b00000');legend(fig);fig.subplots_adjust(left=0,right=1,top=.92,bottom=.08);fig.savefig(out);plt.close(fig);outs.append(str(out))
    print('\n'.join(outs))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
