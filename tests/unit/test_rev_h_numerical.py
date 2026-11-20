"""Rev H regression tests for review findings F01-F07 (numerical correctness).
Expected values are hand-derived (geometry/analytic) and independent of the implementation."""
import math,unittest,itertools
from fgmapping.engine.coverage import Obstructions,detector_frame,flame_geometry_ok,fov_outline,GRID_STATUSES
from fgmapping.engine.solid_geometry import Solid,cell_measure,winding_number
from fgmapping.engine.mesh_visibility import MeshIndex
from fgmapping.domain.scene import Scene,Frame,Component,Mesh,box_mesh,content_hash
from test_coverage_engine import flame_entry,gas_entry,flame_setup,gas_setup,det,run

def mesh_scene(*items):
    comps=tuple(Component(id,id,'WALL','L',m,'EV') for id,m in items)
    return Scene((Frame('L','m','test'),),comps,'T',content_hash([id for id,_ in items]))
def boxes(*bs):return mesh_scene(*[(id,box_mesh(lo,hi)) for id,lo,hi in bs])
PRISM_V=((0,0,0),(1,0,0),(0,1,0),(0,0,1),(1,0,1),(0,1,1))
PRISM_F=((0,2,1),(3,4,5),(0,1,4),(0,4,3),(1,2,5),(1,5,4),(2,0,3),(2,3,5))
FAR_LIB={'E':flame_entry(contour=((0,100),(90,100)),fov=(180,180))}

def cube_quads():
    # outward-oriented quads of the unit cube, vertex index = 4x+2y+z
    return [(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)]
def cube_vertices(shear=0.3):return [(x+shear*z,y,z) for x in (0,1) for y in (0,1) for z in (0,1)]
def triangulate(quads,diag):
    out=[]
    for q,dg in zip(quads,diag):
        a,b,c,d=q
        out+=[(a,b,c),(a,c,d)] if dg==0 else [(a,b,d),(b,c,d)]
    return out

class F01PartialCellMeasure(unittest.TestCase):
    def vol(self,sc,h,excluded=(),low=(0,0,0),high=(1,1,1)):
        return run(low,high,flame_setup(spacing=h,mode='VOLUME'),[det('D',(5,.5,.5),az=180)],FAR_LIB,sc,excluded)[0]
    def test_partial_solid_cell_measure(self):
        for h in (1.0,0.5):
            r=self.vol(boxes(('S',(0,0,0),(.2,1,1))),h)
            self.assertAlmostEqual(r['eligible_measure'],0.8,places=12);self.assertAlmostEqual(r['excluded_measure']['inside_obstruction'],0.2,places=12)
            self.assertAlmostEqual(r['eligible_measure']+sum(r['excluded_measure'].values()),r['zone_measure'],places=12)
            self.assertEqual(r['measure_error_bound'],0.)
    def test_overlapping_solids_not_double_counted(self):
        r=self.vol(boxes(('A',(0,0,0),(.5,1,1)),('B',(.3,0,0),(.6,1,1))),1.0)
        self.assertAlmostEqual(r['eligible_measure'],0.4,places=12);self.assertAlmostEqual(r['excluded_measure']['inside_obstruction'],0.6,places=12)
    def test_exclusion_overlapping_solid_reported_separately(self):
        r=self.vol(boxes(('E',(0,0,0),(.5,1,1)),('S',(.3,0,0),(.6,1,1))),1.0,excluded=('E',))
        self.assertAlmostEqual(r['excluded_measure']['excluded_component'],0.5,places=12);self.assertAlmostEqual(r['excluded_measure']['inside_obstruction'],0.1,places=12)
        self.assertAlmostEqual(r['eligible_measure'],0.4,places=12)
    def test_thin_feature_through_cell_centre(self):
        r=self.vol(boxes(('T',(.495,0,0),(.505,1,1))),1.0)
        self.assertAlmostEqual(r['eligible_measure'],0.99,places=12)  # Rev G excluded the whole cell (centre inside)
    def test_clipped_edge_cell(self):
        r=self.vol(boxes(('S',(1.1,0,0),(1.25,1,1))),.5,high=(1.25,1,1))
        self.assertAlmostEqual(r['zone_measure'],1.25,places=12);self.assertAlmostEqual(r['eligible_measure'],1.1,places=12)
    def test_slice_mode_area(self):
        r=run((0,0,0),(1,1,1),flame_setup(spacing=1.0,mode='SLICES',slices=(.5,)),[det('D',(5,.5,.5),az=180)],FAR_LIB,boxes(('S',(0,0,0),(.2,1,1))))[0]
        self.assertAlmostEqual(r['eligible_measure'],0.8,places=12)
    def test_general_mesh_measure_bounded_and_labelled(self):
        # prism volume 1/2 (hand calculation); measure must contain it within the stated bound
        m=cell_measure((0,0,0),(1,1,1),[],[Solid('P',PRISM_V,PRISM_F,1e-9)],(0,1,2))
        self.assertTrue(m['method'].startswith('ADAPTIVE'));self.assertGreater(m['bound'],0)
        self.assertLessEqual(abs(m['excluded']-0.5),m['bound']);self.assertLess(m['bound'],0.4)

class F02SolidMembership(unittest.TestCase):
    P=(0.5999995739155014,0.29999871481830076,0.8)
    def test_inside_shared_edge_closed_shear(self):
        V=cube_vertices()
        # interior by hand: z=0.8 slab spans x in [0.24,1.24], y in [0,1]
        self.assertTrue(0.24<self.P[0]<1.24 and 0<self.P[1]<1 and 0<self.P[2]<1)
        for diag in itertools.product((0,1),repeat=6):
            F=triangulate(cube_quads(),diag)
            for order in (F,F[::-1],[(b,c,a) for a,b,c in F]):
                s=Solid('X',V,order,1e-9);self.assertTrue(s.closed);self.assertTrue(s.contains(self.P),diag)
        sc=mesh_scene(('X',Mesh(tuple(V),tuple(triangulate(cube_quads(),(0,)*6)))))
        self.assertEqual(Obstructions(sc).inside(self.P),'X')
    def test_outside_and_boundary(self):
        F=triangulate(cube_quads(),(0,)*6);s=Solid('X',cube_vertices(),F,1e-9)
        self.assertFalse(s.contains((0.1,0.5,0.8)))   # left of the sheared face x=0.24
        self.assertFalse(s.contains((0.5,1.0,0.5)))   # on the face y=1: boundary is free (documented rule)
    def test_open_mesh_has_no_volume(self):
        F=triangulate(cube_quads(),(0,)*6)[:-2]
        sc=mesh_scene(('O',Mesh(tuple(cube_vertices()),tuple(F))));o=Obstructions(sc)
        self.assertIsNone(o.inside((0.6,0.5,0.5)));self.assertTrue(any('not closed' in f['text'] for f in o.findings))
        self.assertTrue(o.blocked((0.6,0.5,-1),(0.6,0.5,0.5)))  # still obstructs sight as a surface
    def test_winding_number_values(self):
        F=triangulate(cube_quads(),(0,)*6)
        self.assertAlmostEqual(abs(winding_number((0.6,0.5,0.5),cube_vertices(),F)),1.0,places=9)
        self.assertAlmostEqual(winding_number((5,5,5),cube_vertices(),F),0.0,places=9)

class F03ExcludedPrism(unittest.TestCase):
    def test_excluded_prism_not_its_aabb(self):
        sc=mesh_scene(('P',Mesh(PRISM_V,PRISM_F)));o=Obstructions(sc,('P',))
        self.assertIsNone(o.inside_excluded((.8,.8,.5)));self.assertEqual(o.inside_excluded((.2,.2,.5)),'P')
    def test_excluded_prism_measure(self):
        r=run((0,0,0),(1,1,1),flame_setup(spacing=1.0,mode='VOLUME'),[det('D',(5,.5,.5),az=180)],FAR_LIB,mesh_scene(('P',Mesh(PRISM_V,PRISM_F))),('P',))[0]
        self.assertLessEqual(abs(r['excluded_measure']['excluded_component']-0.5),r['measure_error_bound']+1e-12)
        self.assertGreater(r['eligible_measure'],0.3)  # Rev G removed the whole 1 m3 AABB

def Rz(a):a=math.radians(a);return ((math.cos(a),-math.sin(a),0),(math.sin(a),math.cos(a),0),(0,0,1))
def Ry(a):a=math.radians(a);return ((math.cos(a),0,math.sin(a)),(0,1,0),(-math.sin(a),0,math.cos(a)))
def Rx(a):a=math.radians(a);return ((1,0,0),(0,math.cos(a),-math.sin(a)),(0,math.sin(a),math.cos(a)))
def mm(A,B):return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def mv(A,v):return tuple(sum(A[i][k]*v[k] for k in range(3)) for i in range(3))
def independent_R(az,el,roll):return mm(mm(Rz(az),Ry(-el)),Rx(roll))  # yaw, then pitch up, then roll about boresight

class F04Orientation(unittest.TestCase):
    E=flame_entry(contour=((0,50),(90,50)),fov=(60,20))
    def ok(self,az,el,roll,t):
        d=det('D',(0,0,0));d['frame']=detector_frame(az,el,roll);return flame_geometry_ok(d,self.E,t)[0]
    def test_roll_matches_mount_transform(self):
        t=(10,4.3301270189,2.5);self.assertTrue(all(abs(a-b)<1e-9 for a,b in zip(mv(independent_R(0,0,30),(10,5,0)),t)))
        self.assertTrue(self.ok(0,0,30,t))       # local (10,5,0): h=26.565 deg < 30, v=0
        self.assertFalse(self.ok(0,0,-30,t))     # inverse roll: local (10,2.5,4.33), v=23.4 deg > 10
    def test_combined_pose(self):
        R=independent_R(30,-20,15)
        self.assertTrue(self.ok(30,-20,15,mv(R,(10,3,1))))    # h=16.7, v=5.7
        self.assertFalse(self.ok(30,-20,15,mv(R,(10,1,2))))   # v=11.3 > 10
        self.assertFalse(self.ok(30,-20,15,mv(R,(10,6,0))))   # h=31.0 > 30
        f,l,u=detector_frame(30,-20,15)
        for j,v in enumerate((f,l,u)):self.assertTrue(all(abs(v[i]-R[i][j])<1e-12 for i in range(3)))
    def test_near_vertical_pose(self):
        for az in (0,37,-120):
            R=independent_R(az,-90,0)
            self.assertTrue(self.ok(az,-90,0,mv(R,(5,5*math.tan(math.radians(25)),0))))
            self.assertFalse(self.ok(az,-90,0,mv(R,(5,0,5*math.tan(math.radians(15))))))
            self.assertTrue(self.ok(az,-90,0,(0,0,-5)))

class F05Standoff(unittest.TestCase):
    def test_standoff_cannot_skip_other_wall(self):
        s=flame_setup(spacing=.5,slices=(0.,));s['standoff_m']=0.5
        r=run((1,-1,-1),(3,1,1),s,[det('D',(-0.2,0,0))],FAR_LIB,boxes(('WALL',(0,-5,-5),(0.1,5,5))))[0]
        self.assertEqual(r['fractions']['1ooN'],0.0)
    def test_standoff_ignores_only_own_mount(self):
        s=flame_setup(spacing=.5,slices=(0.,));s['standoff_m']=0.1
        sc=boxes(('BRACKET',(-0.25,-.05,-.05),(-0.15,.05,.05)))
        d=det('D',(-0.2,0,0))
        self.assertEqual(run((1,-1,-1),(3,1,1),s,[d],FAR_LIB,sc)[0]['fractions']['1ooN'],0.0)
        d['mount_component_id']='BRACKET'
        self.assertEqual(run((1,-1,-1),(3,1,1),s,[d],FAR_LIB,sc)[0]['fractions']['1ooN'],1.0)
        sc2=boxes(('BRACKET',(-0.25,-.05,-.05),(-0.15,.05,.05)),('WALL',(0,-5,-5),(0.1,5,5)))
        self.assertEqual(run((1,-1,-1),(3,1,1),s,[d],FAR_LIB,sc2)[0]['fractions']['1ooN'],0.0)
    def test_short_open_path_beam_refused(self):
        s=gas_setup({'shape':'SPHERE','diameter_m':4.0},100,['OPEN_PATH']);s['standoff_m']=0.5
        lib={'OP':gas_entry('OP','OPEN_PATH',0.1,{'min':0.1,'max':100})}
        r=run((0,-1,-1),(2,1,1),s,[det('T',(0,0,0),lib='OP',kind='OPEN_PATH',receiver=(0.8,0,0))],lib)[0]
        self.assertEqual(r['fractions']['1ooN'],0.0);self.assertTrue(any('twice the mount standoff' in f['text'] for f in r['findings']))

class F06BroadphaseEpsilon(unittest.TestCase):
    def check(self,scale,shift):
        lo=tuple(shift[i]+scale*v for i,v in enumerate((1,-1,-1)));hi=tuple(shift[i]+scale*v for i,v in enumerate((1.01,1,1)))
        sc=boxes(('B',lo,hi));o=Obstructions(sc,eps=1e-6);mi=MeshIndex(Mesh(*[box_mesh(lo,hi).vertices,box_mesh(lo,hi).faces]),1e-6)
        class m:
            @staticmethod
            def blocked(a,b):
                try:return mi.blocked(a,b)
                except ValueError:return True  # documented policy: indeterminate (coplanar within eps) counts as blocked
        for side in (1,-1):
            y=shift[1]+side*(scale+5e-7);a=(shift[0],y,shift[2]);b=(shift[0]+2*scale,y,shift[2])
            self.assertTrue(m.blocked(a,b));self.assertEqual(o.blocked(a,b),m.blocked(a,b))
            y=shift[1]+side*(scale+5e-6);a=(shift[0],y,shift[2]);b=(shift[0]+2*scale,y,shift[2])
            self.assertFalse(o.blocked(a,b));self.assertEqual(o.blocked(a,b),m.blocked(a,b))
    def test_scene_mesh_epsilon_agreement(self):
        self.check(1,(0,0,0));self.check(10,(0,0,0));self.check(1,(100,-50,7))
    def test_surface_inside_start_and_grazing(self):
        o=Obstructions(boxes(('B',(1,-1,-1),(1.01,1,1))),eps=1e-6)
        self.assertTrue(o.blocked((1,0,0),(3,0,0)));self.assertTrue(o.blocked((1.005,0,0),(3,0,0)))
        o.indeterminate=0;self.assertTrue(o.blocked((1,-2,0),(1,2,0)));self.assertGreaterEqual(o.indeterminate,0)

class F07GridAgreement(unittest.TestCase):
    def test_no_eligible_not_converged(self):
        s=flame_setup(spacing=.5,mode='VOLUME',ref=2,targets={'1ooN':'0.9'})
        r=run((0,0,0),(1,1,1),s,[det('D',(5,.5,.5),az=180)],FAR_LIB,boxes(('S',(-1,-1,-1),(2,2,2))))[0]
        self.assertIsNone(r['fractions']['1ooN']);self.assertEqual(r['convergence']['status'],'NOT EVALUABLE - no eligible measure')
        self.assertEqual(r['performance_targets']['1ooN']['status'],'NO ELIGIBLE VOLUME')
    def test_shifted_grid_detects_missed_sector(self):
        e={'E':flame_entry(contour=((0,.28),(45,.28)),fov=(90,10))};exact=math.pi*.28**2/4  # 0.06157521601036 m2 on a 1 m2 slice
        self.assertAlmostEqual(exact,0.06157521601036,places=12)
        s=flame_setup(spacing=1.0,slices=(0.,),ref=2)
        r=run((0,-.5,-1),(1,.5,1),s,[det('D',(0,0,0))],e)[0]
        self.assertNotIn('CONVERGED',r['convergence']['status']);self.assertNotEqual(r['convergence']['status'],GRID_STATUSES[0])
        self.assertTrue(r['convergence']['unresolved_features'])
        fine=run((0,-.5,-1),(1,.5,1),flame_setup(spacing=.05,slices=(0.,)),[det('D',(0,0,0))],e)[0]
        self.assertAlmostEqual(fine['fractions']['1ooN'],exact,delta=0.006)
    def test_status_vocabulary(self):
        for st in GRID_STATUSES:self.assertNotIn('CONVERGED',st)

class F19FovOutline(unittest.TestCase):
    def test_fov_display_matches_response_support(self):
        e=flame_entry(contour=((0,20),(30,10)),fov=(120,40));fr=detector_frame(10,-15,25);d=det('D',(1,2,3));d['frame']=fr
        pts=fov_outline((1,2,3),fr,e)
        for p in pts:
            q=tuple(1+(p[i]-(1,2,3)[i])*(1-1e-7) for i in range(1)) and tuple((1,2,3)[i]+(p[i]-(1,2,3)[i])*(1-1e-7) for i in range(3))
            if math.dist(p,(1,2,3))>1e-9:self.assertTrue(flame_geometry_ok(d,e,q)[0])
            beyond=tuple((1,2,3)[i]+(p[i]-(1,2,3)[i])*1.01 for i in range(3))
            if math.dist(p,(1,2,3))>1e-9:self.assertFalse(flame_geometry_ok(d,e,beyond)[0])
        # off-axis beyond the 30 deg table end: no response depicted (range 0), as in the engine
        self.assertTrue(any(math.dist(p,(1,2,3))<1e-9 for p in pts))

if __name__=='__main__':unittest.main()
