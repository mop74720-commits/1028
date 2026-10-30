"""Independent checks of the existing complex checkpoint, without training."""
from pathlib import Path
import sys
import unittest
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'1025_bridges/01_chnn_to_birkhoff/program'))
from check_frozen_network import FrozenIdealNetwork,DATA


class NetworkInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_default_dtype(torch.float64);torch.set_num_threads(1)
        cls.model=FrozenIdealNetwork();cls.data=np.load(DATA)

    def point(self,index):
        return torch.tensor(self.data['test_x'][index])/self.model.D

    def test_real_energy_canonical_chain_and_power(self):
        model=self.model;z=self.point(0)
        h=model.h(z);self.assertFalse(h.is_complex())
        x=(z*model.D).detach().requires_grad_(True)
        hx=.5*model.amplitude**2*x.square().sum()+model.net(x[None,:])[0]
        gx=torch.autograd.grad(hx,x)[0]
        gz=model.gradient(z)
        torch.testing.assert_close(gz,model.D*gx,atol=2e-13,rtol=2e-12)
        self.assertGreater(float(torch.linalg.vector_norm(gz-gx)),1.)
        self.assertLess(abs(float(torch.dot(gz,model.field(z)))),1e-12)

    def test_negative_hpp_does_not_destroy_canonical_phase_form(self):
        model=self.model;z=self.point(146)
        hess=torch.autograd.functional.hessian(model.h,z)
        self.assertLess(float(torch.linalg.eigvalsh(hess[12:,12:])[0]),-.06)
        self.assertTrue(bool(torch.isfinite(model.field(z)).all()))
        np.testing.assert_allclose((-model.J)@model.field(z),model.gradient(z),atol=1e-14,rtol=1e-14)
        np.testing.assert_allclose(np.linalg.svd(-model.J.numpy(),compute_uv=False),np.ones(24),atol=0,rtol=0)

    def test_general_a1_matches_lie_and_mechanical_shortcut_fails(self):
        model=self.model;z=self.point(146)
        field=lambda y:model.field(y)+torch.cat((torch.zeros(12),model.force(y)))
        f=field(z);a0=torch.cat((z[12:],torch.zeros(12)))
        lie=torch.cat((f[12:],torch.zeros(12)))+torch.func.jacrev(field,chunk_size=1)(z).T@a0
        correct=model.a1_general(z)
        self.assertLess(float(torch.linalg.vector_norm(correct+lie)),1e-10)
        self.assertGreater(float(torch.linalg.vector_norm(model.a1_mechanical(z)-correct)),1e-3)

    def test_independent_energy_gradient_and_fixed_origin_jet(self):
        model=self.model;z=self.point(292)
        v=torch.sin(torch.arange(24,dtype=torch.float64)+.3);v=v/torch.linalg.vector_norm(v)
        eps=1e-5/float(torch.linalg.vector_norm(model.D*v))
        difference=(model.h(z+eps*v)-model.h(z-eps*v))/(2*eps)
        self.assertLess(abs(float(difference-torch.dot(model.gradient(z),v))),2e-7)
        zero=torch.zeros(24)
        hessian=torch.autograd.functional.hessian(model.h,zero)
        torch.testing.assert_close(hessian,torch.diag(torch.cat((model.rom.nu,model.rom.nu))),atol=1e-13,rtol=2e-15)
        self.assertEqual(float(model.h(zero)),0.)

    def test_shared_canonical_drag_need_not_dissipate_learned_energy(self):
        model=self.model;z=self.point(180);force=model.force(z)
        truth_gradient=torch.func.grad(model.truth)(z)
        truth_power=torch.dot(truth_gradient[12:],force)
        learned_power=torch.dot(model.gradient(z)[12:],force)
        self.assertLess(float(truth_power),-1e-4)
        self.assertGreater(float(learned_power),1e-4)


if __name__=='__main__':unittest.main()
