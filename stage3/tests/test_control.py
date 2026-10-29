"""Physical-port/control checks; no replacement of the scientific model."""
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'program'))
from control_experiments import ROMBridge,MagneticControl,bounded_increment,field_limits

class ControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge=ROMBridge();cls.control=MagneticControl(cls.bridge)
        cls.z=cls.bridge.initial_state();cls.g=cls.bridge.magnetic_map(cls.z[:12]);cls.v=cls.bridge.field(cls.z)[:12]

    def test_collocated_power_and_full_force(self):
        u,_=self.control.command(self.z,'collocated_damping',g=self.g,velocity=self.v)
        force=self.g@u
        expected=-self.control.collocated_gain*np.linalg.norm((self.g*self.control.port_scale).T@self.v)**2
        self.assertAlmostEqual(float(self.v@force),float(expected),places=13)
        self.assertLessEqual(float(self.v@force),0.)
        base=self.bridge.field(self.z,gamma=.2)
        actual=self.bridge.field(self.z,gamma=.2,u=u)
        np.testing.assert_allclose(actual-base,np.r_[np.zeros(12),force],atol=2e-12,rtol=1e-9)

    def test_field_bounds_preserve_bias_and_maxwell(self):
        for u in (np.ones(8)*100.,np.array([0.,0.,-.2,4.,3.,-8.,2.,1.]),np.zeros(8)):
            output,factor=bounded_increment(self.bridge,u);limits=field_limits(self.bridge,output)
            self.assertGreaterEqual(factor,0.);self.assertLessEqual(factor,1.)
            self.assertLessEqual(limits['affine_workspace_upper_bound_T'],.005+1e-14)
            self.assertLessEqual(limits['gradient_frobenius_T_per_m'],.03+1e-14)
            self.assertAlmostEqual(limits['divergence'],0.,places=14)
            self.assertEqual(limits['curl_defect'],0.)

    def test_projected_cancellation_does_not_invent_unreachable_force(self):
        u,_=self.control.command(self.z,'projected_damping_compensation',g=self.g)
        desired=.2*self.z[12:];reachable=self.g@u
        self.assertGreater(np.linalg.norm(reachable-desired),1e-7)
        weighted=self.g*self.control.port_scale
        reference=weighted@np.linalg.pinv(weighted,rcond=self.control.rcond)@desired
        np.testing.assert_allclose(reachable,reference,atol=1e-12,rtol=1e-9)
        self.assertLess(np.linalg.norm(reachable-desired),np.linalg.norm(desired))

if __name__=='__main__':unittest.main()
