"""Guard against silently accepting the installed torch mixed-solve AD defect."""
from pathlib import Path
import sys
import unittest
import torch

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'stage5/program'))
from verify_high_derivatives import repeated,permutation_defect


class HighDerivativeGuard(unittest.TestCase):
    def test_known_solve_failure_is_detected_not_symmetrized_away(self):
        f=lambda x:.5*x[1:2]@torch.linalg.solve((1+x[0]**2).reshape(1,1),x[1:2])
        zero=torch.zeros(2,dtype=torch.float64)
        mixed=repeated(f,'RFFF')(zero);reverse=repeated(f,'RRRR')(zero)
        self.assertGreater(float(torch.max(abs(mixed-reverse))),1.)
        self.assertGreater(permutation_defect(mixed),1.)
        self.assertAlmostEqual(float(reverse[1,1,0,0]),-2.,places=12)

    def test_inverse_and_pure_reverse_match_analytic_division(self):
        f=lambda x:.5*x[1:2]@torch.linalg.inv((1+x[0]+x[0]**2).reshape(1,1))@x[1:2]
        exact=lambda x:.5*x[1]**2/(1+x[0]+x[0]**2)
        point=torch.tensor([.2,.3],dtype=torch.float64)
        for order in (2,3,4):
            actual=repeated(f,'R'+'F'*(order-1))(point)
            reference=repeated(exact,'R'*order)(point)
            self.assertLess(float(torch.max(abs(actual-reference))),1e-12)


if __name__=='__main__':unittest.main(verbosity=2)
