"""Rev F: dense synthetic lattice — broadphase equals brute force and an independent oracle."""
import unittest
from tools.rev_f_dense_benchmark import run
class DenseScene(unittest.TestCase):
    def test_dense_lattice_matches_independent_oracle(self):
        record,ok=run();c=record['checks']
        self.assertTrue(c['brute_force_equals_broadphase'])
        self.assertEqual(c['oracle_mismatches'],0,record['first_mismatches'])
        self.assertEqual(c['indeterminate_samples'],0)
        self.assertTrue(c['non_trivial_mix']);self.assertTrue(c['broadphase_reduced_queries'])
        self.assertEqual(record['qualification'],'UNVERIFIED SOFTWARE BENCHMARK ONLY');self.assertTrue(ok)
