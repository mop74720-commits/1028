"""Independent identities for the local first-order Birkhoff/ROM connection.

These checks differentiate the original a.f definition, rather than assuming
the implementation's simplified gauge Hamiltonian is correct.
"""
from pathlib import Path
import json
import sys
import unittest

import numpy as np
import torch

STAGE3=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(STAGE3/'program'))
from rom_bridge import ROMBridge
from birkhoff_rom import LocalBirkhoffROM


class BirkhoffROMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge=ROMBridge()
        cls.model=LocalBirkhoffROM(cls.bridge)
        cls.z=cls.bridge.initial_state(.025)
        cls.x=torch.tensor(cls.z)
        cls.t=.003
        cls.records={}

    def original_field_tensor(self,x):
        return self.bridge.field_tensor(x)-torch.cat((torch.zeros_like(x[:12]),self.model.rate_tensor*x[12:]))

    def test_first_transport_coefficient_directly(self):
        x=self.x;m=self.model
        f=self.original_field_tensor(x)
        df=torch.func.jacrev(self.original_field_tensor)(x)
        a0=m.a0_tensor(x)
        da0=torch.func.jacrev(m.a0_tensor)(x)
        definition=-da0@f-df.T@a0
        implemented=m.oneform_tensor(x,1.)-a0
        error=float(torch.linalg.vector_norm(definition-implemented))
        self.assertLess(error,1e-10)
        self.records['first_transport_coefficient_identity_error']=error

    def test_direct_potential_gauge_and_representation_identity(self):
        x=self.x;m=self.model;t=self.t
        direct_B=lambda y:torch.dot(m.oneform_tensor(y,t),self.original_field_tensor(y))
        direct_gauge_B=lambda y:direct_B(y)+m.F_tensor(y)
        direct_scalar=direct_gauge_B(x)
        direct_gradient=torch.func.grad(direct_gauge_B)(x).detach().numpy()
        native_scalar=m.gauge_hamiltonian(x.clone().requires_grad_(True),t)
        scalar_error=abs(float(direct_scalar-native_scalar))
        gradient_error=np.linalg.norm(direct_gradient-m.gauge_gradient(self.z,t))
        self.assertLess(scalar_error,1e-12)
        self.assertLess(gradient_error,1e-9)

        a=m.oneform_tensor(x,t)
        a1=m.oneform_tensor(x,1.)-m.a0_tensor(x)
        da=torch.func.jacrev(lambda y:m.oneform_tensor(y,t))(x)
        f=self.original_field_tensor(x)
        df=torch.func.jacrev(self.original_field_tensor)(x)
        grad_B=torch.func.grad(direct_B)(x)
        exterior=da.T-da
        residual=exterior@f-grad_B-a1
        transport=a1+da@f+df.T@a
        pde_error=float(torch.linalg.vector_norm(residual+transport))
        k_error=np.linalg.norm(exterior.detach().numpy()-m.K(t),2)
        self.assertLess(pde_error,1e-9)
        self.assertLess(k_error,1e-10)
        gauged_residual=m.K(t)@m.original_field(self.z)-direct_gradient-np.r_[m.rates*self.z[12:],np.zeros(12)]
        gauge_invariance_error=np.linalg.norm(gauged_residual-residual.detach().numpy())
        self.assertLess(gauge_invariance_error,1e-9)
        self.records['direct_gauge']={'scalar_error':scalar_error,'gradient_error':gradient_error,
                                     'PDE_representation_sign_identity_error':pde_error,
                                     'oneform_exterior_derivative_error':k_error,
                                     'representation_gauge_invariance_error':gauge_invariance_error,
                                     'nonzero_representation_residual':float(torch.linalg.vector_norm(residual))}

    def test_chart_field_and_error_separation(self):
        m=self.model;z=self.z;t=self.t
        D=m.chart_jacobian(t)
        y=m.chart(z,t)
        fa=m.approximate_field(t,z)
        time_chart=np.r_[np.zeros(12),m.rates*z[12:]]
        transformed=D@fa+time_chart
        chart_error=np.linalg.norm(transformed-m.chart_field(t,y))
        match_error=np.linalg.norm(D.T@m.K0@D-m.K(t),2)
        self.assertLess(chart_error,1e-12)
        self.assertLess(match_error,1e-12)
        self.assertLess(np.linalg.norm(m.inverse_chart(y,t)-z),1e-14)
        self.assertLess(np.linalg.norm(m.approximate_field(0,z)-m.original_field(z)),1e-11)
        d1=m.diagnostics(z,t);d2=m.diagnostics(z,2*t)
        self.assertGreater(d1['original_field_error_2'],1e-6)
        self.assertLess(d1['original_field_error_2'],d1['inverse_K_residual_bound']*(1+1e-12))
        residual_ratio=d2['representation_residual_2']/d1['representation_residual_2']
        transport_ratio=d2['original_transport_compatibility_2']/d1['original_transport_compatibility_2']
        self.assertAlmostEqual(residual_ratio,2.,places=8)
        self.assertAlmostEqual(transport_ratio,2.,places=7)
        self.records['chart']={'transformed_field_identity_error':chart_error,'matching_error':match_error,
                               'representation_residual_doubling_ratio':residual_ratio,
                               'transport_compatibility_doubling_ratio':transport_ratio,
                               'at_t':d1,'at_2t':d2}

    def test_nondegeneracy_domain_rejected(self):
        with self.assertRaises(ValueError):
            self.model.weights(-1/max(self.model.rates))

    @classmethod
    def tearDownClass(cls):
        out=STAGE3/'results/birkhoff_identity_checks.json'
        out.write_text(json.dumps({'dimension':24,'time':cls.t,'diagnostics':cls.records,
                                   'scope':'direct AD identities and sampled diagnostics; no physical exact flow used'},indent=2)+'\n')


if __name__=='__main__':unittest.main(verbosity=2)
