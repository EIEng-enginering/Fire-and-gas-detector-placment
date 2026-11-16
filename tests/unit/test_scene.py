import json,math,unittest
from dataclasses import replace
from fgmapping.domain.scene import Frame,Mesh,Scene,box_mesh,synthetic_scene
from fgmapping.services.mesh_import import parse_mesh
class SceneTests(unittest.TestCase):
    def test_units(self):
        self.assertEqual(Frame('F','mm','SYN').world((1000,2000,3000)),(1,2,3))
        self.assertEqual(Frame('F','ft','SYN').world((1,0,0)),(.3048,0,0))
    def test_rotated_scaled_translated_exact(self):
        f=Frame('F','mm','SYN',matrix=((0,-2,0,10),(3,0,0,20),(0,0,4,30),(0,0,0,1)))
        self.assertEqual(f.world((1000,2000,3000)),(6,23,42));self.assertEqual(f.local((6,23,42)),(1000,2000,3000))
    def test_roundtrip_angles(self):
        for angle in (0,30,90,180):
            a=math.radians(angle);c,s=math.cos(a),math.sin(a)
            f=Frame('F','cm','SYN',matrix=((c,-s,0,2),(s,c,0,-3),(0,0,1,7),(0,0,0,1)))
            for p in ((0,0,0),(1,2,3),(-100,33,7)):
                for x,y in zip(f.local(f.world(p)),p):self.assertAlmostEqual(x,y,places=10)
    def test_bad_frame(self):
        for units,hand in (('', 'RIGHT'),('yards','RIGHT'),('m','LEFT')):
            with self.assertRaises(ValueError):Frame('F',units,'SYN',hand)
    def test_bad_transforms(self):
        for m in (((-1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1)),((1,1,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1)),((0,0,0,0),)*4,((float('nan'),0,0,0),)*4):
            with self.assertRaises(ValueError):Frame('F','m','SYN',matrix=m)
    def test_bad_coordinates(self):
        for v in ((float('inf'),0,0),(1e10,0,0),(1,2),(True,0,0)):
            with self.assertRaises(ValueError):Frame('F','m','SYN').world(v)
    def test_exact_json_roundtrip(self):
        s=synthetic_scene();r=Scene.from_dict(json.loads(json.dumps(s.to_dict())))
        self.assertEqual(s,r);self.assertEqual(s.sha256,r.sha256);self.assertEqual(len(s.components),13)
    def test_duplicate_and_missing_source(self):
        s=synthetic_scene()
        for kw in ({'components':s.components+(s.components[0],)},{'source_sha256':''},{'data_class':'PROJECT_BASIS'},{'components':(replace(s.components[0],frame_id='MISSING'),)}):
            with self.assertRaises(ValueError):replace(s,**kw)
    def test_cycle(self):
        s=synthetic_scene();a=replace(s.components[0],parent_id=s.components[1].id);b=replace(s.components[1],parent_id=a.id)
        with self.assertRaises(ValueError):replace(s,components=(a,b))
    def test_closed_mesh(self):
        d=box_mesh((0,0,0),(1,1,1)).diagnostics()
        for k in ('boundary_edges','nonmanifold_edges','duplicate_faces','inconsistent_winding_edges'):self.assertEqual(d[k],0,k)
        self.assertEqual(d['self_intersection'],'NOT EVALUATED')
    def test_bad_mesh(self):
        for v,f in ((((0,0,0),(1,0,0),(2,0,0)),((0,1,2),)),(((0,0,0),(1,0,0),(0,1,0)),((0,1,9),))):
            with self.assertRaises(ValueError):Mesh(v,f)
    def test_open_duplicate(self):
        m=Mesh(((0,0,0),(1,0,0),(0,1,0)),((0,1,2),))
        self.assertEqual(m.diagnostics()['boundary_edges'],3);self.assertEqual(Mesh(m.vertices,m.faces*2).diagnostics()['duplicate_faces'],1)
    def test_obj_units_and_hash(self):
        raw=b'v 0 0 0\nv 1000 0 0\nv 0 1000 0\nf 1 2 3\n';f=Frame('F','mm','SYN')
        r=parse_mesh(raw,'.obj',f);self.assertEqual(r['mesh']['vertices'][1],(1,0,0));self.assertEqual(r,parse_mesh(raw,'.obj',f))
    def test_stl(self):
        raw=b'solid s\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid s'
        self.assertEqual(len(parse_mesh(raw,'.stl',Frame('F','m','SYN'))['mesh']['faces']),1)
    def test_hostile(self):
        for raw,fmt in ((b'x'*4000001,'.obj'),(b'mtllib remote.mtl','.obj'),(b'\x00\xff','.stl'),(b'hello','.step'),(b'v nan 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3','.obj'),(b'v 0 0 0\nf 0 1 2','.obj')):
            with self.assertRaises((ValueError,UnicodeError)):parse_mesh(raw,fmt,Frame('F','m','SYN'))
