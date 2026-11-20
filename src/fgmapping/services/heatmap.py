"""Plan-slice coverage heatmap images (PNG via Pillow) for reports and review.

Display of stored results only; colours by detector votes. COMPUTED - UNREVIEWED development
results - not independently certified.
"""
from __future__ import annotations
import io,json
from fgmapping.domain.scene import content_hash
VOTE_RGB=((214,39,40),(242,180,0),(44,160,44),(20,90,50))
VOTE_LABELS=('0 votes','1 vote','2 votes','3+ votes')
from fgmapping.engine.coverage import LABEL

def _font(size):
    from PIL import ImageFont
    try:return ImageFont.load_default(size=size)
    except TypeError:return ImageFont.load_default()

def slice_levels(samples):return sorted({round(r[2],6) for r in samples['rows']})

def _slice_segments(verts,faces,z):
    """Exact intersection segments of a triangle mesh with the plane Z=z."""
    segs=[]
    for f in faces:
        t=[verts[i] for i in f];d=[p[2]-z for p in t];pts=[]
        for i in range(3):
            a,b=t[i],t[(i+1)%3];da,db=d[i],d[(i+1)%3]
            if da==0:pts.append((a[0],a[1]))
            if da*db<0:u=da/(da-db);pts.append((a[0]+u*(b[0]-a[0]),a[1]+u*(b[1]-a[1])))
        pts=list(dict.fromkeys(pts))
        if len(pts)>=2:segs.append((pts[0],pts[-1]))
    return segs

def render_slice(result,samples,slice_z,scene=None,detectors=(),px_per_m=24,title=None,example=False,excluded_ids=(),stale=False,libraries=()):
    """Return PNG bytes of one plan slice. Rev H (F20): each cell is drawn with its stored
    zone-clipped bounds; box solids cut by the slice are drawn exactly (grey), general meshes are
    drawn as their exact slice-cut outline (dark lines) with the AABB envelope projection only as
    a dashed schematic outline; basis-excluded components are hatched blue. STALE runs carry a
    prominent banner (F09)."""
    from PIL import Image,ImageDraw
    rows=[r for r in samples['rows'] if abs(r[2]-slice_z)<1e-6]
    zone=result.get('zone_bounds')
    h=result['grid_spacing_m']/2
    def cell_rect(r):
        if len(r)>6 and r[5] is not None:return r[5][0],r[5][1],r[6][0],r[6][1]
        x0,y0,x1,y1=r[0]-h,r[1]-h,r[0]+h,r[1]+h
        if zone:x0,y0,x1,y1=max(x0,zone[0][0]),max(y0,zone[0][1]),min(x1,zone[1][0]),min(y1,zone[1][1])
        return x0,y0,x1,y1
    rects=[cell_rect(r) for r in rows]
    lo=[min([q[0] for q in rects] or [0]),min([q[1] for q in rects] or [0])];hi=[max([q[2] for q in rects] or [0]),max([q[3] for q in rects] or [0])]
    if zone:lo=[min(lo[0],zone[0][0]),min(lo[1],zone[0][1])];hi=[max(hi[0],zone[1][0]),max(hi[1],zone[1][1])]
    for d in detectors:lo=[min(lo[0],d['position'][0]-1),min(lo[1],d['position'][1]-1)];hi=[max(hi[0],d['position'][0]+1),max(hi[1],d['position'][1]+1)]
    margin=60;top=70+(16 if libraries else 0)+(22 if stale else 0);legend=88
    W=max(int((hi[0]-lo[0])*px_per_m)+2*margin,760);H=int((hi[1]-lo[1])*px_per_m)+top+legend+margin
    img=Image.new('RGB',(W,H),(255,255,255));g=ImageDraw.Draw(img)
    def P(x,y):return (margin+(x-lo[0])*px_per_m,top+(hi[1]-y)*px_per_m)
    for r,(x0,y0,x1,y1) in zip(rows,rects):
        g.rectangle([P(x0,y1),P(x1,y0)],fill=VOTE_RGB[min(len(r[4]),3)])
    excluded_ids=set(excluded_ids)
    if scene is not None:
        for c in scene.components:
            if c.occlusion_role=='NON_OBSTRUCTING_ANNOTATION' or c.semantic=='DETECTOR':continue
            f=scene.frame(c.frame_id);v=[f.world(p) for p in c.mesh.vertices]
            zl,zh=min(p[2] for p in v),max(p[2] for p in v)
            if not zl<=slice_z<=zh:continue
            x0,x1=min(p[0] for p in v),max(p[0] for p in v);y0,y1=min(p[1] for p in v),max(p[1] for p in v)
            if x1<lo[0] or x0>hi[0] or y1<lo[1] or y0>hi[1]:continue
            corners={(a,b,cz) for a in (x0,x1) for b in (y0,y1) for cz in (zl,zh)}
            is_box=len(v)==8 and set(v)==corners
            excl=c.id in excluded_ids
            if is_box:
                if not zl<slice_z<zh:continue
                box=[P(max(x0,lo[0]),min(y1,hi[1])),P(min(x1,hi[0]),max(y0,lo[1]))]
                if excl:
                    g.rectangle(box,fill=(200,215,240),outline=(30,70,160),width=2)
                    (ax,ay),(bx,by)=box
                    for k in range(int(-(by-ay)),int(bx-ax),8):
                        x_a=ax+max(k,0);y_a=ay+max(-k,0);n=min(bx-x_a,by-y_a)
                        if n>0:g.line([(x_a,y_a),(x_a+n,y_a+n)],fill=(30,70,160))
                else:g.rectangle(box,fill=(90,90,90),outline=(40,40,40))
            else:
                g.rectangle([P(x0,y1),P(x1,y0)],outline=(120,120,120))
                for (ax,ay),(bx,by) in _slice_segments(v,c.mesh.faces,slice_z):g.line([P(ax,ay),P(bx,by)],fill=(30,70,160) if excl else (20,20,20),width=3)
    if zone:g.rectangle([P(zone[0][0],zone[1][1]),P(zone[1][0],zone[0][1])],outline=(0,0,0),width=2)
    f=_font(11)
    for d in detectors:
        x,y=P(d['position'][0],d['position'][1]);r=5
        if d['detector_type']=='FLAME':g.polygon([(x,y-r-1),(x-r,y+r),(x+r,y+r)],fill=(255,255,255),outline=(0,0,0))
        else:g.ellipse([x-r,y-r,x+r,y+r],fill=(30,110,200) if d['detector_type']=='POINT_GAS' else (130,60,160),outline=(0,0,0))
        g.text((x+6,y-6),d['id'],fill=(0,0,0),font=f)
        if d.get('receiver'):
            rx,ry=P(d['receiver'][0],d['receiver'][1]);g.line([(x,y),(rx,ry)],fill=(130,60,160),width=1);g.rectangle([rx-4,ry-4,rx+4,ry+4],outline=(130,60,160))
    # scale bar and axes
    sx,sy=margin,H-margin+15;g.line([(sx,sy),(sx+5*px_per_m,sy)],fill=(0,0,0),width=2);g.text((sx,sy+4),'5 m',fill=(0,0,0),font=f)
    for gx in range(int(lo[0])+1,int(hi[0])+1):
        if gx%5==0:x,_=P(gx,lo[1]);g.text((x-6,top+(hi[1]-lo[1])*px_per_m+3),str(gx),fill=(80,80,80),font=f)
    for gy in range(int(lo[1])+1,int(hi[1])+1):
        if gy%5==0:_,y=P(lo[0],gy);g.text((margin-22,y-6),str(gy),fill=(80,80,80),font=f)
    tf=_font(14)
    g.text((margin,10),title or ('%s  %s  slice z = %.2f m' % (result['zone_id'],result['method_version'],slice_z)),fill=(0,0,0),font=tf)
    fr=result['fractions']
    g.text((margin,30),'1ooN %s   2ooN %s   3ooN %s   (whole zone, %s, grid %.3f m, eligible %.4g %s, sampled-cell fraction)' % tuple(['-' if fr[k] is None else '%.1f %%' % (100*fr[k]) for k in ('1ooN','2ooN','3ooN')]+[result['mode'].lower(),result['grid_spacing_m'],result.get('eligible_measure',float('nan')),result.get('measure_unit','')]),fill=(0,0,0),font=f)
    g.text((margin,46),(result.get('label') or LABEL)+('  |  EXAMPLE LIBRARY VALUES - not for design' if example else ''),fill=(176,58,46) if example else (0,0,0),font=f)
    if libraries:g.text((margin,62),'Library: '+'; '.join(libraries)[:180],fill=(60,60,60),font=f)
    if stale:
        g.rectangle([0,top-22,W,top-4],fill=(176,58,46));g.text((margin,top-19),'STALE RUN - inputs or method changed since this run; figure shows the run\'s own stored scene, not the current case',fill=(255,255,255),font=f)
    ly=H-legend+5
    for i,(rgb,label) in enumerate(zip(VOTE_RGB,VOTE_LABELS)):
        x=margin+i*110;g.rectangle([x,ly,x+14,ly+14],fill=rgb,outline=(0,0,0));g.text((x+20,ly),label,fill=(0,0,0),font=f)
    ly2=ly+22
    g.rectangle([margin,ly2,margin+14,ly2+14],fill=(90,90,90));g.text((margin+20,ly2),'box solid cut by slice (exact)',fill=(0,0,0),font=f)
    g.line([(margin+230,ly2+7),(margin+244,ly2+7)],fill=(20,20,20),width=3);g.text((margin+250,ly2),'mesh slice cut (exact)',fill=(0,0,0),font=f)
    g.rectangle([margin+420,ly2,margin+434,ly2+14],outline=(120,120,120));g.text((margin+440,ly2),'mesh AABB envelope (schematic)',fill=(0,0,0),font=f)
    g.rectangle([margin,ly2+22,margin+14,ly2+36],fill=(200,215,240),outline=(30,70,160));g.text((margin+20,ly2+22),'basis-excluded component',fill=(0,0,0),font=f)
    g.text((margin+230,ly2+22),'cells drawn at stored zone-clipped bounds; partial cells weighted by free measure',fill=(0,0,0),font=f)
    out=io.BytesIO();img.save(out,format='PNG',optimize=False);return out.getvalue()

def run_scene(run):
    """The run's own immutable scene snapshot (F09), verified against the run envelope hash.
    Returns None for legacy runs that did not store one (geometry is then NOT drawn)."""
    from fgmapping.domain.scene import Scene
    samples=json.loads(run['samples_json']);env=json.loads(run['input_json'])
    snap=samples.get('scene_snapshot')
    if snap is None:return None
    scene=Scene.from_dict(snap)
    if scene.sha256!=env['scene_sha256']:raise ValueError('Run scene snapshot hash does not match the run input envelope')
    return scene

def run_figures(session,run,px_per_m=24,max_slices=4,currency=None):
    """PNG figures for a stored coverage run drawn from the RUN'S OWN stored scene (F09)."""
    res=json.loads(run['result_json']);samples=json.loads(run['samples_json']);env=json.loads(run['input_json'])
    res=dict(res,zone_bounds=(env['zone']['low'],env['zone']['high']))
    levels=slice_levels(samples)
    if len(levels)>max_slices:
        step=(len(levels)-1)/(max_slices-1);levels=[levels[round(i*step)] for i in range(max_slices)]
    example=any(x.startswith('EXAMPLE_LIBRARY_VALUES') for x in res.get('review',[]))
    if currency is None:
        from fgmapping.services.coverage import run_currency
        currency=run_currency(session,run)
    stale=currency!='CURRENT'
    scene=run_scene(run)
    libs=['%s sha256 %s%s' % (k,content_hash(v)[:12],' EXAMPLE' if v['source']['data_status'].startswith('EXAMPLE') else '') for k,v in sorted(env['library'].items())]
    out=[]
    for z in levels:
        out.append({'zone_id':res['zone_id'],'slice_z':z,'stale':stale,'png':render_slice(res,samples,z,scene,env['detectors'],px_per_m,example=example,excluded_ids=env.get('excluded_component_ids',()),stale=stale,libraries=libs),
                    'description':('STALE RUN - ' if stale else '')+'%s plan slice at z = %.2f m: cells coloured by number of detectors responding (%s, grid %.2f m, sampled-cell fraction). %s' % (res['zone_id'],z,res['method_version'],res['grid_spacing_m'],'EXAMPLE library values - not for design. ' if example else '')+('' if scene else 'Run predates scene snapshots: geometry not drawn. ')+(res.get('label') or LABEL)+'.'})
    return out
