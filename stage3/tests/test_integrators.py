"""Independent derivative/sign/structure checks for stage3 integrators."""
import sys
from pathlib import Path
import unittest
import numpy as np
import torch
from scipy.linalg import expm
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'program'))
from rom_bridge import ROMBridge
from rom_integrators import (central_increment, central_increment_jacobian,
                             central_scalar, central4, midpoint, weighted_midpoint,
                             TOLERANCE)


class QuadraticNonseparable:
    """Independent full q-p coupled quadratic reference with an exact matrix flow."""
    def __init__(self):
        self.n=2
        self.J=np.block([[np.zeros((2,2)),np.eye(2)],[-np.eye(2),np.zeros((2,2))]])
        self.K0=-self.J
        B=np.array([[1.,.2,.1,-.07],[.03,1.4,.04,.15],[.1,.0,1.2,.25],[.05,-.12,.13,1.1]])
        self.H=B.T@B
        self.A=self.J@self.H
    def hamiltonian_tensor(self,z):
        return .5*z@torch.tensor(self.H)@z
    def field(self,z,gamma=0):
        return self.A@z-np.r_[np.zeros(2),gamma*z[2:]]
    def jacobian(self,z,gamma=0):
        return self.A-np.diag([0,0,gamma,gamma])


class IntegratorChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=ROMBridge()
        cls.z=cls.model.initial_state()

    def test_nonseparable_central_sign_and_order(self):
        model=QuadraticNonseparable();z=np.array([.13,-.08,.04,.02]);errors=[]
        for h in [.16,.08,.04]:
            increment=central_increment(model,z,h)
            np.testing.assert_allclose(increment,(h*model.A-h**3*(model.A@model.A@model.A)/12)@z,rtol=1e-12,atol=1e-14)
            states=z.copy()
            for _ in range(round(.32/h)):
                states,_,_=central4(model,states,h)
            errors.append(np.linalg.norm(states-expm(.32*model.A)@z))
        self.assertAlmostEqual(np.log2(errors[-2]/errors[-1]),4,delta=.03)

    def test_true_rom_central_gradient_direction(self):
        h=.001;z=self.z.copy();direction=np.cos(np.arange(len(z)));direction/=np.linalg.norm(direction)
        grad=-self.model.J@central_increment(self.model,z,h)
        eps=2e-6
        def value(x):
            return float(central_scalar(self.model,torch.tensor(x,requires_grad=True),h).detach())
        derivative=(value(z+eps*direction)-value(z-eps*direction))/(2*eps)
        self.assertLess(abs(derivative-grad@direction),3e-9)

    def test_true_rom_central_ideal_tangent_is_hamiltonian(self):
        A=central_increment_jacobian(self.model,self.z,.001)
        self.assertLess(np.linalg.norm(A.T@self.model.K0+self.model.K0@A,2),1e-10)

    def test_true_rom_midpoint_residual_and_symplecticity(self):
        new,D,s=midpoint(self.model,self.z,.001,diagnostics=True)
        r=new-self.z-.001*self.model.field((new+self.z)/2)
        self.assertLessEqual(np.linalg.norm(r,np.inf),TOLERANCE)
        self.assertLess(np.linalg.norm(D.T@self.model.K0@D-self.model.K0,2),1e-11)

    def test_true_rom_weighted_is_conformal(self):
        gamma=.2;h=.001
        new,D,s=weighted_midpoint(self.model,self.z,h,gamma,True)
        factor=np.exp(-gamma*h)
        self.assertLess(np.linalg.norm(D.T@self.model.K0@D-factor*self.model.K0,2),1e-11)
        self.assertGreater(np.linalg.norm(new-self.z),0)


if __name__=='__main__':unittest.main(verbosity=2)
