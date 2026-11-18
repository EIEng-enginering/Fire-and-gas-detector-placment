"""Plan-slice coverage heatmap images (PNG via Pillow) for reports and review.

Display of stored results only; colours by detector votes. Engineer-reviewed
results - not independently certified.
"""
from __future__ import annotations
import io,json
VOTE_RGB=((214,39,40),(242,180,0),(44,160,44),(20,90,50))
VOTE_LABELS=('0 votes','1 vote','2 votes','3+ votes')

def _font(size):
    from PIL import ImageFont
    try:return ImageFont.load_default(size=size)
    except TypeError:return ImageFont.load_default()

def slice_levels(samples):return sorted({round(r[2],6) for r in samples['rows']})

def render_slice(result,samples,slice_z,scene=None,detectors=(),px_per_m=24,title=None,example=False):
    """Return PNG bytes of one plan slice: cells by votes, obstruction footprints cut by the slice, detectors."""
    from PIL import Image,ImageDraw
    rows=[r for r in samples['rows'] if abs(r[2]-slice_z)<1e-6]
    zone=result.get('zone_bounds')
    h=result['grid_spacing_m']/2
    xs=[r[0] for r in rows] or [0];ys=[r[1] for r in rows] or [0]
    lo=[min(xs)-h,min(ys)-h];hi=[max(xs)+h,max(ys)+h]
    if zone:lo=[min(lo[0],zone[0][0]),min(lo[1],zone[0][1])];hi=[max(hi[0],zone[1][0]),max(hi[1],zone[1][1])]
    for d in detectors:lo=[min(lo[0],d['position'][0]-1),min(lo[1],d['position'][1]-1)];hi=[max(hi[0],d['position'][0]+1),max(hi[1],d['position'][1]+1)]
    margin=60;top=70;legend=70
    W=int((hi[0]-lo[0])*px_per_m)+2*margin;H=int((hi[1]-lo[1])*px_per_m)+top+legend+margin
    img=Image.new('RGB',(W,H),(255,255,255));g=ImageDraw.Draw(img)
    def P(x,y):return (margin+(x-lo[0])*px_per_m,top+(hi[1]-y)*px_per_m)
    for x,y,z,w,votes in rows:
        a=P(x-h,y+h);b=P(x+h,y-h);g.rectangle([a,b],fill=VOTE_RGB[min(len(votes),3)])
    if scene is not None:
        for c in scene.components:
            if c.occlusion_role=='NON_OBSTRUCTING_ANNOTATION' or c.semantic=='DETECTOR':continue
            f=scene.frame(c.frame_id);v=[f.world(p) for p in c.mesh.vertices]
            zl,zh=min(p[2] for p in v),max(p[2] for p in v)
            if not zl<=slice_z<=zh:continue
            x0,x1=min(p[0] for p in v),max(p[0] for p in v);y0,y1=min(p[1] for p in v),max(p[1] for p in v)
            if x1<lo[0] or x0>hi[0] or y1<lo[1] or y0>hi[1]:continue
            g.rectangle([P(max(x0,lo[0]),min(y1,hi[1])),P(min(x1,hi[0]),max(y0,lo[1]))],fill=(90,90,90),outline=(40,40,40))
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
    g.text((margin,32),'1ooN %s   2ooN %s   3ooN %s   (whole zone, %s)' % tuple(['-' if fr[k] is None else '%.1f %%' % (100*fr[k]) for k in ('1ooN','2ooN','3ooN')]+[result['mode'].lower()]),fill=(0,0,0),font=f)
    g.text((margin,48),'Engineer-reviewed results - not independently certified'+('  |  EXAMPLE LIBRARY VALUES - not for design' if example else ''),fill=(176,58,46) if example else (0,0,0),font=f)
    ly=H-legend+5
    for i,(rgb,label) in enumerate(zip(VOTE_RGB,VOTE_LABELS)):
        x=margin+i*110;g.rectangle([x,ly,x+14,ly+14],fill=rgb,outline=(0,0,0));g.text((x+20,ly),label,fill=(0,0,0),font=f)
    g.rectangle([margin+440,ly,margin+454,ly+14],fill=(90,90,90));g.text((margin+460,ly),'solid cut by slice (excluded)',fill=(0,0,0),font=f)
    out=io.BytesIO();img.save(out,format='PNG',optimize=False);return out.getvalue()

def run_figures(session,run,px_per_m=24,max_slices=4):
    """PNG figures for a stored coverage run: up to max_slices plan slices."""
    from fgmapping.services.geometry import get_scene
    res=json.loads(run['result_json']);samples=json.loads(run['samples_json']);env=json.loads(run['input_json'])
    res=dict(res,zone_bounds=(env['zone']['low'],env['zone']['high']))
    levels=slice_levels(samples)
    if len(levels)>max_slices:
        step=(len(levels)-1)/(max_slices-1);levels=[levels[round(i*step)] for i in range(max_slices)]
    example=any(x.startswith('EXAMPLE_LIBRARY_VALUES') for x in res.get('review',[]))
    scene=get_scene(session)
    out=[]
    for z in levels:
        out.append({'zone_id':res['zone_id'],'slice_z':z,'png':render_slice(res,samples,z,scene,env['detectors'],px_per_m,example=example),
                    'description':'%s plan slice at z = %.2f m: cells coloured by number of detectors responding (%s, grid %.2f m). %s' % (res['zone_id'],z,res['method_version'],res['grid_spacing_m'],'EXAMPLE library values - not for design. ' if example else '')+'Engineer-reviewed results - not independently certified.'})
    return out
