from pathlib import Path
import sys,unittest
import numpy as np
import torch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'program'))
from nonautonomous_transport import (TimeGainCoilTransport,NativeTransport,CoilROM,
    TimeGainRepresentedField,inherit_second_order_cache,MoserChart)


class NonautonomousTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.base=CoilROM();cls.model=TimeGainCoilTransport(cls.base)
        cls.z=cls.base.initial_state(.01);cls.x=torch.as_tensor(cls.z)

    def test_actual_fullcoil_time_derivative_and_current_force(self):
        model=self.model;t=.0002;eps=1e-6
        fd=(model.field(self.z,t+eps)-model.field(self.z,t-eps))/(2*eps)
        analytical=np.r_[np.zeros(model.n),model.amplitude*model.frequency*np.cos(model.frequency*t)*model.drag_tensor(self.x,numeric=True).detach().numpy()]
        np.testing.assert_allclose(fd,analytical,rtol=2e-8,atol=1e-10)
        current=model.currents(t,self.z)
        np.testing.assert_allclose(model.field(self.z,t),self.base.field(self.z,current),rtol=2e-12,atol=1e-13)
        self.assertEqual(len(self.z),24)

    def test_second_coefficient_has_required_time_force_term(self):
        model=self.model
        autonomous=NativeTransport(self.base,force=model.drag_tensor,kind='fullcoil_collocated')
        correct=model.source_coefficient_function(2)(self.x)
        frozen=autonomous.source_coefficient_function(2)(self.x)
        expected=-.5*torch.cat((model.force_coefficient(self.x,1),torch.zeros(model.n)))
        np.testing.assert_allclose((correct-frozen).detach().numpy(),expected.detach().numpy(),rtol=2e-11,atol=1e-11)
        self.assertGreater(float(torch.linalg.vector_norm(expected)),.01)

    def test_zero_modulation_reuses_autonomous_coefficients(self):
        model=TimeGainCoilTransport(self.base,amplitude=0.)
        autonomous=NativeTransport(self.base,force=model.drag_tensor,kind='fullcoil_collocated')
        for order in (1,2):
            np.testing.assert_allclose(model.source_coefficient_function(order)(self.x).detach().numpy(),
                                       autonomous.source_coefficient_function(order)(self.x).detach().numpy(),rtol=2e-12,atol=2e-12)

    def test_represented_nonzero_time_Jacobian_and_transport(self):
        cache,_=inherit_second_order_cache(self.model)
        represented=TimeGainRepresentedField(self.model,cache,2);t=.0003
        direction=np.cos(np.arange(24)+.31);direction/=np.linalg.norm(direction)
        eps=2e-7
        difference=(represented(t,self.z+eps*direction)-represented(t,self.z-eps*direction))/(2*eps)
        jac=represented.jacobian(t,self.z)
        np.testing.assert_allclose(jac@direction,difference,rtol=2e-6,atol=1e-7)
        a=cache.data(self.z,t,2);f=represented(t,self.z)
        defect=a['Kt']+np.einsum('ijk,k->ij',a['DK'],f)+jac.T@a['K']+a['K']@jac
        self.assertLess(np.linalg.norm(defect,2),1e-9)

    def test_chart_rejects_outside_declared_ball(self):
        cache,_=inherit_second_order_cache(self.model)
        outside=self.z.copy();outside[0]+=.0021
        with self.assertRaisesRegex(ValueError,'left declared ball'):
            MoserChart(cache,2).map(outside,.0005)


if __name__=='__main__':unittest.main(verbosity=2)
