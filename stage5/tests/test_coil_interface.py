"""Meaningful regression tests for full energy, physical ports and feedback AD."""
from pathlib import Path
import sys
import unittest
import numpy as np
import torch

sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'program'))
from coil_rom import CoilROM
from coil_control import CurrentAllocator,ramp_current
from coil_field import basis


class CoilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=CoilROM();cls.z=cls.m.initial_state();cls.i=cls.m.bias_currents.copy()

    def test_field_and_analytic_gradient_maxwell(self):
        m=self.m
        x=torch.tensor([[.001,-.0005,.096],[.0013,.0007,.099]])
        b,g=m.field_basis_tensor(x,gradient=True)
        np.testing.assert_allclose(b.numpy(),basis(x.numpy(),m.coil_config),rtol=2e-12,atol=1e-17)
        dg=torch.func.jacrev(lambda p:m.field_basis_tensor(p[None,:])[0])(x[0]).permute(0,2,1)
        np.testing.assert_allclose(g[0].numpy(),dg.numpy(),rtol=2e-12,atol=1e-16)
        self.assertLess(float(torch.max(torch.abs(torch.einsum('paaj->pj',g)))),1e-12)
        self.assertLess(float(torch.max(torch.abs(g-g.transpose(1,2)))),1e-12)

    def test_energy_port_and_bias_counted_once(self):
        m=self.m;z=torch.tensor(self.z);i=torch.tensor(self.i)
        f=m.field_tensor(z,i);f0=m.field_tensor(z,torch.zeros_like(i))
        port=m.current_port_tensor(z[:m.n])
        np.testing.assert_allclose((f-f0)[m.n:].numpy(),(port@i).numpy(),rtol=2e-11,atol=2e-12)
        np.testing.assert_allclose((f-f0)[:m.n].numpy(),0,atol=1e-14)
        self.assertAlmostEqual(float(m.hamiltonian_tensor(z,i)-m.hamiltonian_tensor(z,torch.zeros_like(i))),float(m.coil_potential_tensor(z[:m.n],i)),places=12)
        d=np.cos(np.arange(m.n)+.2);d/=np.linalg.norm(d);eps=1e-6
        vp=float(m.coil_potential_tensor(z[:m.n]+eps*torch.tensor(d),i))
        vm=float(m.coil_potential_tensor(z[:m.n]-eps*torch.tensor(d),i))
        self.assertLess(abs((vp-vm)/(2*eps)+d@port.numpy()@self.i),2e-8)

    def test_feedback_partial_then_chain_rule(self):
        m=self.m;z=torch.tensor(self.z)
        current=m.collocated_current_tensor(z)
        physical=m.field_tensor(z,current)
        wrong=m.J_tensor@torch.func.grad(lambda x:m.hamiltonian_tensor(x,m.collocated_current_tensor(x)))(z)
        self.assertGreater(float(torch.linalg.vector_norm(physical-wrong)),1e-6)
        jac=m.feedback_jacobian(self.z)
        direction=np.cos(np.arange(2*m.n)+.3);direction/=np.linalg.norm(direction)
        eps=2e-6
        fd=(m.feedback_field(self.z+eps*direction)-m.feedback_field(self.z-eps*direction))/(2*eps)
        np.testing.assert_allclose(jac@direction,fd,rtol=2e-6,atol=2e-7)
        baseline_grad=torch.func.grad(lambda x:m.hamiltonian_tensor(x,m.bias_currents_tensor))(z)
        power=float(baseline_grad@(physical-m.field_tensor(z,m.bias_currents_tensor)))
        port_velocity=m.current_port_tensor(z[:m.n]).T@baseline_grad[m.n:]
        self.assertAlmostEqual(power,-m.collocated_gain*float(port_velocity@port_velocity),places=11)
        self.assertLessEqual(power,1e-14)

    def test_current_bounds_and_continuous_ramp(self):
        m=self.m;alloc=CurrentAllocator(m);seconds=1e-4
        requested=self.i+np.linspace(-3.,3.,m.current_channels)
        target,report=alloc.allocate(self.z[:m.n],requested,self.i,seconds)
        self.assertLessEqual(np.max(abs(target)),2.+1e-12)
        self.assertLessEqual(report['maximum_planned_slew_A_s'],20.+1e-8)
        tau=seconds*m.rom.omega0
        np.testing.assert_array_equal(ramp_current(self.i,target,0,0,tau),self.i)
        np.testing.assert_allclose(ramp_current(self.i,target,tau,0,tau),target,atol=1e-15)
        self.assertLessEqual(report['constraint_violation'],1e-9)

    def test_force_space_allocation_reports_unreachable_target(self):
        m=self.m;alloc=CurrentAllocator(m)
        desired=.2*self.z[m.n:]
        current,report=alloc.allocate_force(self.z[:m.n],desired,self.i,1e-4)
        residual=m.current_port(self.z[:m.n])@(current-self.i)-desired
        self.assertAlmostEqual(float(np.linalg.norm(residual)),report['constrained_force_residual'],places=12)
        self.assertGreater(report['orthogonal_unreachable_residual'],1e-6)
        self.assertLessEqual(report['orthogonal_unreachable_residual'],report['constrained_force_residual']+1e-10)
        self.assertLess(report['rank'],m.n)

    def test_mixed_higher_feedback_derivative(self):
        m=self.m;z=m.tensor(self.z)
        d=torch.cos(torch.arange(z.numel(),dtype=z.dtype)+.37);d/=torch.linalg.vector_norm(d)
        higher=torch.func.jvp(torch.func.jacrev(m.feedback_field_tensor),(z,),(d,))[1].numpy()
        eps=1e-6
        finite=(m.feedback_jacobian(self.z+eps*d.numpy())-m.feedback_jacobian(self.z-eps*d.numpy()))/(2*eps)
        self.assertLess(np.linalg.norm(higher-finite)/np.linalg.norm(higher),2e-6)


if __name__=='__main__':
    unittest.main(verbosity=2)
