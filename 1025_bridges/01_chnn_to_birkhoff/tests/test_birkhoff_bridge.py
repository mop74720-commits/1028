"""Independent minimal mathematical and numerical checks of bridge01."""
from pathlib import Path
import sys,unittest
import numpy as np
import torch

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'program'))
from bridge_interface import (ROOT,ROMBridge,LearnedIdealBase,GeneralHamiltonianTransport,
    fit_network_cache,LearnedRepresentedField,independent_pair_diagnostics)
from run_bridge import exact_cache_domain


class QuarticBase:
    n=1
    J=np.array([[0.,1.],[-1.,0.]])
    def hamiltonian_tensor(self,z):return .5*(z*z).sum()+.3*z[1]**4


class BirkhoffBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_default_dtype(torch.float64);torch.set_num_threads(1)
        cls.physical=ROMBridge();cls.learned=LearnedIdealBase(cls.physical)
        cls.native=GeneralHamiltonianTransport(cls.learned)
        cls.center=np.load(ROOT/'stage5/results/transport/synthetic/cache_r3_q2_inverse_3c8879dd39a6.npz')['center']
        cls.cache=fit_network_cache(cls.native,cls.center)

    def test_quartic_counterexample_and_general_coefficient(self):
        n=GeneralHamiltonianTransport(QuarticBase(),kind='conservative')
        z=torch.tensor([.2,.4]);actual=n.a1(z)
        expected=torch.tensor([z[0],-z[1]-12*.3*z[1]**3])
        np.testing.assert_allclose(actual,expected,atol=2e-15,rtol=2e-15)
        wrong=torch.tensor([z[0],-z[1]-4*.3*z[1]**3])
        self.assertGreater(float(torch.linalg.vector_norm(actual-wrong)),.1)
        np.testing.assert_allclose(actual,-n.lie_oneform(n.a0,z),atol=2e-15)
        # No nonconservative load: exact source gauge has no truncation at all.
        np.testing.assert_array_equal(n.source_coefficient_function(2)(z),np.zeros(2))

    def test_source_coefficient_on_hand_nonlinear_force(self):
        force=lambda z:-(1+z[:1]**2)*z[1:]
        n=GeneralHamiltonianTransport(QuarticBase(),force=force)
        z=torch.tensor([.2,.4]);q,p=z;velocity=p+4*.3*p**3;pdot=-q-(1+q*q)*p
        expected=-.5*torch.stack((2*q*p*velocity+(1+q*q)*pdot,(1+12*.3*p*p)*(1+q*q)*p))
        np.testing.assert_allclose(n.source_coefficient_function(2)(z),expected,rtol=2e-14,atol=2e-14)

    def test_real_network_preserved_no_mass_reconstruction(self):
        x=torch.tensor(self.center)
        self.assertEqual(self.native.ad_backend,'original')
        self.assertFalse(hasattr(self.learned,'mass_tensor'))
        self.assertEqual(float(self.native.high_order_hamiltonian(x)),float(self.learned.hamiltonian_tensor(x)))
        # Guard the second possible bug: exposing the physical M must still not
        # make the arbitrary-H adapter reconstruct a quadratic momentum energy.
        self.learned.mass_tensor=self.physical.mass_tensor
        try:self.assertEqual(float(self.native.high_order_hamiltonian(x)),float(self.learned.hamiltonian_tensor(x)))
        finally:del self.learned.mass_tensor

    def test_signed_error_split_and_structure_are_distinct(self):
        d=independent_pair_diagnostics(self.native,self.physical,self.cache,self.center,.0005,2)
        self.assertLess(d['split_identity_defect'],2e-12)
        self.assertLess(d['direct_vs_inherited_eB'],2e-12)
        self.assertLess(d['represented_compatibility_max'],2e-9)
        self.assertLess(d['closure_max'],2e-12)
        self.assertGreater(d['learning_field_error_norm'],1e-4)
        self.assertGreater(d['e_B_norm'],1e-7)
        self.assertGreater(d['original_learned_transport_defect'],1e-5)
        self.assertLessEqual(d['true_field_pair_residual_norm'],d['residual_bound']+1e-12)
        self.assertLessEqual(d['represented_to_true_field_error_norm'],d['field_bound']+1e-12)

    def test_actual_represented_jacobian_independent_difference(self):
        f=LearnedRepresentedField(self.native,self.cache,2);z=self.center;t=.0005
        v=np.sin(np.arange(24)+.7);v/=np.linalg.norm(v)
        h=1e-7;finite=(f(t,z+h*v)-f(t,z-h*v))/(2*h)
        np.testing.assert_allclose(f.jacobian(t,z)@v,finite,atol=2e-7,rtol=2e-7)

    def test_cache_has_explicit_nondegenerate_domain(self):
        bound=exact_cache_domain(self.cache)
        self.assertTrue(bound['nondegenerate'])
        self.assertGreater(bound['minimum_singular_lower'],.99)
        for sign in [-1,1]:
            z=self.center+sign*.002*np.cos(np.arange(24))
            actual=self.cache.data(z,.0005,2)['K']
            self.assertGreater(np.linalg.svd(actual,compute_uv=False)[-1],bound['minimum_singular_lower'])


if __name__=='__main__':unittest.main()
