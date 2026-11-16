import json,unittest
from fgmapping.domain.performance import parse_dataset,validate_dataset
from fgmapping.domain.study_basis import validate_basis
class PerformancePreparation(unittest.TestCase):
 def test_unsupported_or_missing_contract(self):
  for p in ({},{'contract':'x'},{'contract':'fg-performance-preparation/1','data_class':'PROJECT_BASIS'}):
   with self.assertRaises(ValueError):validate_dataset(p)
 def test_bounded_raw_source_and_corrupt_json(self):
  for raw in (b'x'*4000001,b'not json',b'\xff'):
   with self.assertRaises((ValueError,UnicodeError)):parse_dataset(raw)
 def test_no_default_study_basis(self):
  with self.assertRaises(ValueError):validate_basis({})
