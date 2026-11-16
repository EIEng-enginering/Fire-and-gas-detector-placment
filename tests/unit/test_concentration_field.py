import math,unittest
from fgmapping.engine.concentration import *
class Fields(unittest.TestCase):
 def payload(self):
  axis=[0,2];time=[0,4];values=[10+2*x+3*y+4*z+5*t for t in time for z in axis for y in axis for x in axis]
  return {'contract':'fg-synthetic-field/1','data_class':'SYNTHETIC','axes_units':'m','concentration_units':'ppm','time_units':'s','layout':'t,z,y,x','x':axis,'y':axis,'z':axis,'times_s':time,'ppm':values,'source_sha256':'0'*64,'revision':'SYN-A','evidence_locator':'Synthetic analytic affine field'}
 def test_trilinear_time_affine_known_answer(self):
  f=ConcentrationField.from_dict(self.payload());self.assertAlmostEqual(f.sample((.3,.7,1.1),1.5),24.6)
  self.assertEqual(f.sample((2,2,2),4),48)
 def test_affine_beam_independent_integral(self):
  f=ConcentrationField.from_dict(self.payload());a=(0,0,0);b=(2,2,2)
  # Along segment C is affine; exact integral is chord length times endpoint mean.
  expected=math.sqrt(12)*(20+38)/2
  for n in (2,4,8,16):self.assertAlmostEqual(f.beam_integral(a,b,2,n)['ppm_m'],expected,places=10)
 def test_no_extrapolation(self):
  f=ConcentrationField.from_dict(self.payload())
  for p,t in (((-1,0,0),1),((1,1,1),5)):
   with self.assertRaises(ValueError):f.sample(p,t)
 def test_contract_and_bad_arrays(self):
  for key,value in [('axes_units','ft'),('data_class','PROJECT_BASIS'),('x',[0,0]),('ppm',[0]),('source_sha256','unknown')]:
   p=self.payload();p[key]=value
   with self.assertRaises(ValueError):ConcentrationField.from_dict(p)
 def test_invalid_numerics(self):
  p=self.payload();p['ppm'][0]=float('nan')
  with self.assertRaises(ValueError):ConcentrationField.from_dict(p)
  f=ConcentrationField.from_dict(self.payload())
  with self.assertRaises(ValueError):f.beam_integral((0,0,0),(1,1,1),1,3)
 def test_step_response_known_answer(self):
  self.assertAlmostEqual(first_order_step_response(0,100,5,5),100*(1-1/math.e),places=12)
  self.assertEqual(first_order_step_response(30,100,5,0),30)
  with self.assertRaises(ValueError):first_order_step_response(0,100,0,5)

 def test_overflow_is_refused(self):
  p=self.payload();p['ppm']=[1e308]*16;f=ConcentrationField.from_dict(p)
  with self.assertRaises(ValueError):f.beam_integral((0,0,0),(2,2,2),1,2)
