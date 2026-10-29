"""Independent identities for the source-gauge cache and Moser sensitivities."""
from pathlib import Path
import sys,unittest
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'program'))
from transport_native import NativeTransport
from transport_cache import OneFormCache,CachedRepresentedField
from moser_chart import MoserChart

torch.set_default_dtype(torch.float64)
torch.set_num_threads(1)


class VariableMassTest:
    n=2
    J=np.block([[np.zeros((2,2)),np.eye(2)],[-np.eye(2),np.zeros((2,2))]])
    K0=-J
    def hamiltonian_tensor(self,z):
        q,p=z[:2],z[2:]
        return .5*torch.sum((1+q*q)*p*p)+.5*torch.sum(q*q)+.1*(q[0]+q[1])**4
    def field(self,z):return self.J@torch.func.grad(self.hamiltonian_tensor)(torch.tensor(z)).detach().numpy()
    def jacobian(self,z):return self.J@torch.func.hessian(self.hamiltonian_tensor)(torch.tensor(z)).detach().numpy()
    def metadata(self):return dict(model='nonseparable variable-mass polynomial unit test; not the 3D robot')


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=NativeTransport(base=VariableMassTest())
        cls.z=np.array([.012,-.008,.001,-.0012])
        cls.cache=OneFormCache.fit(cls.model,cls.z,maximum_order=3,quadratic_through=2)

    def test_source_gauge_exact_center_residual_orders(self):
        t=.01
        for r in (1,2,3):
            field=CachedRepresentedField(self.model,self.cache,r)
            _,a=field.evaluate(t,self.z,True);_,b=field.evaluate(t/2,self.z,True)
            self.assertLess(abs(np.log2(a['representation_residual_2']/b['representation_residual_2'])-r),2e-8)
            self.assertLess(a['closure_max_component'],1e-14)

    def test_moser_inverse_time_and_state_sensitivities(self):
        chart=MoserChart(self.cache,3,max_step=.125,domain_radius=.02,rtol=3e-13,atol=3e-15)
        t=.02
        report=chart.diagnostics(self.z,t)
        self.assertLess(report['chart_matching_2'],2e-12)
        self.assertLess(report['inverse_composition_error_2'],2e-13)
        self.assertLess(report['time_inverse_error_2'],2e-12)
        self.assertTrue(report['chi']['sufficient_stay_in_ball'])
        y,R,wt,_=chart.map(self.z,t)
        eps=1e-6
        fd=(chart.map(self.z,t+eps,sensitivities=False)[0]-chart.map(self.z,t-eps,sensitivities=False)[0])/(2*eps)
        self.assertLess(np.linalg.norm(fd-wt),2e-10)

    def test_transformed_full_jacobian_including_moser_second_variation(self):
        chart=MoserChart(self.cache,3,domain_radius=.02,rtol=3e-13,atol=3e-15)
        represented=CachedRepresentedField(self.model,self.cache,3)
        t=.02;A,_=chart.transformed_jacobian(t,self.z,represented)
        eps=2e-7
        fd=np.column_stack([(chart.transformed_field(t,self.z+eps*e,represented)-chart.transformed_field(t,self.z-eps*e,represented))/(2*eps) for e in np.eye(4)])
        self.assertLess(np.linalg.norm(A-fd,2),2e-8)
        self.assertLess(np.linalg.norm(A.T@self.cache.K0+self.cache.K0@A,2),2e-11)

    def test_conservative_source_gauge_zero_coefficients(self):
        native=NativeTransport(base=VariableMassTest(),kind='conservative')
        for k in (1,2,3):
            self.assertLess(float(torch.linalg.vector_norm(native.source_coefficient_function(k)(torch.tensor(self.z)))),1e-15)


if __name__=='__main__':unittest.main(verbosity=2)
