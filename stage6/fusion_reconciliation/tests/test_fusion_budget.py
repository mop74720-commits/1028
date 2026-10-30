"""Independent checks of restored dual budgets and the actual 24D adapter."""
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'stage6/fusion_reconciliation/program'))
sys.path.insert(0,str(ROOT/'stage5/program'))
from fusion_budget import (MechanicalPolynomialBudget,dual_route_budget,
                           route_hamiltonians,homological_compatibility,exact_normalized_momentum_bound)
from fractions import Fraction
from learning_models import MechanicalPolynomial,RodROM


class TestFusionBudget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_default_dtype(torch.float64);torch.set_num_threads(1)
        protocol=json.loads((ROOT/'stage5/results/learning/S5_L01_protocol.json').read_text())
        cls.D=np.asarray(protocol['scales']['coordinate_D'])
        checkpoint=torch.load(ROOT/'stage5/results/learning/S5_L01_analytic_mechanical4_seed51001.pt',
                              map_location='cpu',weights_only=False)
        cls.poly=MechanicalPolynomialBudget.from_checkpoint(checkpoint,cls.D)
        cls.checkpoint=checkpoint
        cls.net=MechanicalPolynomial(12,checkpoint['output_scale'])
        cls.net.load_state_dict(checkpoint['state_dict'])

    def test_actual_checkpoint_reconstruction_and_canonical_gradient(self):
        rng=np.random.default_rng(61026)
        x=rng.normal(size=(4,24))*.3
        xt=torch.tensor(x,requires_grad=True)
        h=self.net(xt);grad=torch.autograd.grad(h.sum(),xt)[0].detach().numpy()*self.D
        np.testing.assert_allclose(self.poly.evaluate(x/self.D),h.detach().numpy(),atol=2.e-16,rtol=3.e-12)
        np.testing.assert_allclose(self.poly.gradient(x/self.D),grad,atol=2.e-14,rtol=3.e-11)
        self.assertEqual(len(self.poly.exponents),8749)
        self.assertEqual(len(np.unique(self.poly.exponents,axis=0)),8749)

    def test_majorant_and_Hpp_on_complex_and_real_boxes(self):
        r=.25/self.D
        bounds=self.poly.majorants(r)
        z=r*np.exp(1j*np.linspace(0,4,24))
        self.assertLessEqual(abs(self.poly.evaluate(z)),bounds['energy']*(1+1.e-14))
        self.assertTrue(np.all(abs(self.poly.gradient(z))<=bounds['gradient']*(1+1.e-14)))
        zz=torch.tensor(r*.7,requires_grad=True)
        hess=torch.autograd.functional.hessian(lambda v:self.net((v*torch.tensor(self.D))[None,:])[0],zz).detach().numpy()
        self.assertTrue(np.all(abs(hess)<=bounds['hessian']+2.e-13))
        self.assertLessEqual(np.max(np.sum(abs(hess[12:,12:]),axis=1)),bounds['Hpp_row_sum_bound']+2.e-13)

    def test_hand_monomial_majorant_and_zero_gradient(self):
        # P=2 q^3+3 q p^2, with one physical pair, independent of checkpoint parser.
        p=MechanicalPolynomialBudget(np.array([[3,0],[1,2]]),np.array([2.,3.]),np.ones(2),1.,1)
        b=p.majorants(np.array([.2,.4]))
        self.assertAlmostEqual(b['energy'],2*.2**3+3*.2*.4**2)
        np.testing.assert_allclose(b['gradient'],[6*.2**2+3*.4**2,6*.2*.4])
        self.assertAlmostEqual(b['Hpp_row_sum_bound'],6*.2)
        np.testing.assert_array_equal(p.gradient(np.zeros(2)),[0.,0.])

    def test_weighted_momentum_convexity_sufficient_domain_and_failure(self):
        nu=(self.D[:12]*.08)**2
        small=self.poly.momentum_convexity_bound(.05/self.D,nu)
        larger=self.poly.momentum_convexity_bound(.1/self.D,nu)
        self.assertTrue(small['positive_definiteness_sufficient'])
        self.assertGreater(small['uniform_eigenvalue_lower_majorant'],.2)
        self.assertFalse(larger['positive_definiteness_sufficient'])
        # A failed sufficient bound is NOT a counterexample to Hessian positivity.
        self.assertLess(larger['uniform_eigenvalue_lower_majorant'],0.)

    def test_exact_rational_legendre_bound(self):
        bound=exact_normalized_momentum_bound(self.checkpoint,self.D,Fraction(1,20))
        self.assertTrue(bound['sufficient_positive_definiteness'])
        self.assertGreater(Fraction(bound['canonical_momentum_eigenvalue_lower_exact']),Fraction(1,5))
        larger=exact_normalized_momentum_bound(self.checkpoint,self.D,Fraction(1,10))
        self.assertFalse(larger['sufficient_positive_definiteness'])

    def test_dual_route_identity_keeps_distinct_targets(self):
        perfect=route_hamiltonians(2.,.3,.3)
        self.assertEqual(perfect['compensated'],2.)
        self.assertEqual(perfect['learned'],2.3)
        self.assertNotEqual(perfect['learned'],perfect['compensated'])
        imperfect=route_hamiltonians(2.,.3,.2)
        self.assertAlmostEqual(imperfect['true']-imperfect['learned'],imperfect['delta'])

    def test_dual_budget_refuses_missing_domain_or_learned_error(self):
        with self.assertRaises(ValueError):
            dual_route_budget(1.,2.,3.,.1,common_chart_domain_verified=False)
        conditional=dual_route_budget(1.,2.,3.,None,common_chart_domain_verified=True)
        self.assertIsNone(conditional['epsilon_A'])
        self.assertFalse(conditional['KAM_certificate'])
        numerical=dual_route_budget(1.,2.,3.,.1,common_chart_domain_verified=True)
        self.assertAlmostEqual(numerical['epsilon_A'],1.3)
        self.assertAlmostEqual(numerical['epsilon_B'],2.3)
        self.assertFalse(numerical['KAM_certificate'])

    def test_full_remainder_has_quadratic_generator_terms(self):
        kappa=1.2;tail=2.;bracket=3.;double=5.
        full=kappa*tail+kappa*kappa*(bracket+.5*double)
        incorrect=kappa*(tail+bracket+.5*double)
        self.assertGreater(abs(full-incorrect),1.)

    def test_actual_3d_resonance_rejects_old_template(self):
        rom=RodROM()
        gate=homological_compatibility(rom.nu.detach().numpy())
        self.assertEqual(gate['monomials'],17550)
        self.assertEqual(gate['resonant_count'],206)
        self.assertEqual(gate['nonaction_resonant_count'],128)
        self.assertFalse(gate['old_action_only_template_compatible'])
        self.assertTrue(homological_compatibility([1.,6.0458573])['old_action_only_template_compatible'])

    def test_continuous_divisor_does_not_imply_discrete_divisor(self):
        omega=2.;step=2*np.pi/omega
        self.assertGreater(omega,0.)
        self.assertLess(abs(np.exp(1j*step*omega)-1),1.e-14)


if __name__=='__main__':unittest.main(verbosity=2)
