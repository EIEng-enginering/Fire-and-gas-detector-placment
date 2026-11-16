import unittest
from fgmapping.services.paste import detector_paste_preview
from fgmapping.errors import CaseError
class Paste(unittest.TestCase):
 def rows(self):return [{'id':'B','detector_type':'FLAME','x':0,'y':1,'z':2},{'id':'A','detector_type':'POINT_GAS','x':3,'y':4,'z':5}]
 def test_visible_order_and_numeric_preview(self):
  patches,preview=detector_paste_preview(self.rows(),'10\t11\n20\t21',0,2)
  self.assertEqual(patches,[{'id':'B','x':10.,'y':11.},{'id':'A','x':20.,'y':21.}]);self.assertEqual(len(preview),4)
 def test_protected_columns_bounds_and_malformed(self):
  for text,row,col in [('X',0,0),('X',0,5),('1\t2\n3',0,2),('1\n2\n3',0,2),('nan',0,2),('inf',0,2),('abc',0,2),('NO_TYPE',0,1)]:
   with self.assertRaises(CaseError):detector_paste_preview(self.rows(),text,row,col)
