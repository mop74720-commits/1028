"""Independent gauge/endpoint/operator tests; physical ROM checks run separately."""
from pathlib import Path
import sys, unittest
import numpy as np
import sympy as sp
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'program'))
from fusion_theory import PhysicalHamiltonianGauge, chart_defect_decomposition, formal_self_adjoint_defect
from transport_native import NativeTransport
from transport_cache import OneFormCache, CachedRepresentedField

torch.set_default_dtype(torch.float64)
torch.set_num_threads(1)


class NonseparableBenchmark:
    n=2
    J=np.block([[np.zeros((2,2)),np.eye(2)],[-np.eye(2),np.zeros((2,2))]])
    K0=-J
    def hamiltonian_tensor(self,z):
        q,p=z[:2],z[2:]
        return .5*torch.sum((1+q*q)*p*p)+.5*torch.sum(q*q)+.1*(q[0]+q[1])**4
    def field(self,z):return self.J@torch.func.grad(self.hamiltonian_tensor)(torch.tensor(z)).detach().numpy()
    def jacobian(self,z):return self.J@torch.func.hessian(self.hamiltonian_tensor)(torch.tensor(z)).detach().numpy()


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=NativeTransport(base=NonseparableBenchmark())
        cls.z=np.array([.012,-.008,.001,-.0012])
        cls.cache=OneFormCache.fit(cls.native,cls.z,maximum_order=2,quadratic_through=2)
        cls.gauge=PhysicalHamiltonianGauge(cls.native,cls.cache,2)

    def test_fixed_position_time_integral_and_spatial_gradient(self):
        x=torch.tensor(self.z);t=.02;eps=1e-6
        sigma=lambda z,tt:float(self.gauge.sigma_tensor(torch.tensor(z),tt).detach())
        timefd=(sigma(self.z,t+eps)-sigma(self.z,t-eps))/(2*eps)
        scalar_difference=float((self.gauge.source_scalar_tensor(x,t)-self.native.high_order_hamiltonian(x)).detach())
        self.assertAlmostEqual(timefd,scalar_difference,delta=1e-13)
        fd=np.array([(sigma(self.z+eps*e,t)-sigma(self.z-eps*e,t))/(2*eps) for e in np.eye(4)])
        gradient=self.gauge.gradient_sigma_tensor(x,t).detach().numpy()
        np.testing.assert_allclose(fd,gradient,atol=1e-11,rtol=1e-7)

    def test_H_gauge_preserves_form_and_field_but_not_energy(self):
        r=self.gauge.diagnostics(self.z,.02)
        self.assertLess(r['rhs_gauge_defect'],2e-15)
        self.assertLess(r['raw_gauge_hessian_antisymmetry'],2e-15)
        np.testing.assert_allclose(r['gauged_K'],self.cache.data(self.z,.02,2)['K'],atol=2e-15)
        reference=CachedRepresentedField(self.native,self.cache,2)(.02,self.z)
        np.testing.assert_allclose(r['represented_field'],reference,atol=2e-15)
        self.assertGreater(abs(r['represented_H_rate']),1e-8)
        self.assertGreater(r['original_field_error'],1e-8)
        self.assertGreater(np.linalg.norm(r['wrong_unchanged_oneform_field']-reference),1e-5)

    def test_complete_chart_defect_identity_with_internal_and_inverse_errors(self):
        rng=np.random.default_rng(6201);d=6;n=3
        K0=np.block([[np.zeros((n,n)),-np.eye(n)],[np.eye(n),np.zeros((n,n))]])
        Tm=np.eye(d)+.03*rng.normal(size=(d,d));Tp=np.eye(d)+.03*rng.normal(size=(d,d))
        internal=np.eye(d)+.02*rng.normal(size=(d,d))
        Km=K0+.002*(Tp-Tp.T);Kp=K0+.003*(Tm-Tm.T)
        physical=np.linalg.solve(Tp,internal@Tm)+.001*rng.normal(size=(d,d))
        r=chart_defect_decomposition(K0,Km,Kp,Tm,Tp,internal,physical)
        self.assertLess(r['decomposition_residual'],2e-15)
        self.assertGreater(np.linalg.norm(r['observed']-r['endpoint_term'],2),1e-3)
        self.assertGreater(np.linalg.norm(r['observed']-r['endpoint_term']-r['internal_term'],2),1e-3)

    def test_variational_operator_not_physical_Jacobian_symmetry(self):
        q,p,t,vq,vp=sp.symbols('q p t vq vp',real=True)
        z=sp.Matrix([q,p]);a=sp.Matrix([sp.exp(t)*p+q*p*p/10,q*q/5]);B=(q*q+p*p)/2
        Da=a.jacobian(z);K=Da.T-Da;b=sp.Matrix([sp.diff(B,x) for x in z])+a.diff(t)
        velocity=sp.Matrix([vq,vp]);C=sp.Matrix(2,2,lambda i,j:sum(sp.diff(K[i,k],z[j])*velocity[k] for k in range(2))-sp.diff(b[i],z[j]))
        dotK=K.diff(t)+sum((K.diff(z[k])*velocity[k] for k in range(2)),sp.zeros(2))
        self.assertEqual(sp.simplify(C-C.T-dotK),sp.zeros(2))
        values={q:.3,p:.2,t:.1,vq:.7,vp:-.4}
        DK=np.array([[[float(sp.diff(K[i,j],z[k]).subs(values)) for k in range(2)] for j in range(2)] for i in range(2)])
        defect=formal_self_adjoint_defect(np.array(K.diff(t).subs(values),float),DK,np.array(b.jacobian(z).subs(values),float),np.array([.7,-.4]))
        self.assertLess(np.linalg.norm(defect),1e-15)
        Df=np.array((K.inv()*b).jacobian(z).subs(values),float)
        self.assertGreater(np.linalg.norm(Df-Df.T),1.)


if __name__=='__main__':unittest.main(verbosity=2)
