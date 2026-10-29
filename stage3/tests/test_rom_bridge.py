"""Independent numerical checks of the connection to the actual 12-DOF ROM."""
from pathlib import Path
import hashlib
import json
import sys
import time
import unittest

import numpy as np
import torch

STAGE3 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE3/'program'))
from rom_bridge import ROMBridge, SOURCE


class ROMBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = ROMBridge()
        cls.z = cls.model.initial_state(.08)
        cls.direction = np.random.default_rng(31028).normal(size=24)
        cls.direction /= np.linalg.norm(cls.direction)
        cls.records = {}

    def test_full_geometry_hamiltonian(self):
        m=self.model; z=self.z
        inherited=float(m.rom.hamiltonian(torch.tensor(z)[None,:])[0])
        self.assertEqual(m.n,12)
        self.assertEqual(m.rom.elements,20)
        self.assertAlmostEqual(m.hamiltonian(z),inherited,places=14)
        mass=m.mass(z[:12]); mass0=m.mass(np.zeros(12))
        eig=np.linalg.eigvalsh(mass)
        variation=np.linalg.norm(mass-mass0)/np.linalg.norm(mass0)
        self.assertGreater(variation,1e-6)
        self.assertGreater(eig.min(),0)
        self.records['mass']={'relative_variation_from_equilibrium':variation,
                              'minimum_scaled_mass_eigenvalue':eig.min(),
                              'scaled_mass_condition':np.linalg.cond(mass)}

    def test_hamiltonian_directional_derivative(self):
        m=self.model; z=self.z; v=self.direction; eps=2e-6
        gradient=-m.J@m.field(z)
        finite=(m.hamiltonian(z+eps*v)-m.hamiltonian(z-eps*v))/(2*eps)
        error=abs(finite-gradient@v)
        self.assertLess(error,2e-7)
        self.records['Hamiltonian_directional_absolute_error']=error

    def test_field_jacobian_and_form_compatibility(self):
        m=self.model; z=self.z; v=self.direction; eps=2e-6; gamma=.13
        start=time.perf_counter(); f=m.field(z,gamma); field_seconds=time.perf_counter()-start
        start=time.perf_counter(); jac=m.jacobian(z,gamma); jac_seconds=time.perf_counter()-start
        finite=(m.field(z+eps*v,gamma)-m.field(z-eps*v,gamma))/(2*eps)
        relative=np.linalg.norm(finite-jac@v)/np.linalg.norm(jac@v)
        defect=np.linalg.norm(jac.T@m.K0+m.K0@jac+gamma*m.K0,2)
        self.assertLess(relative,2e-6)
        self.assertLess(defect,2e-8)
        self.records['Jacobian']={'directional_relative_error':relative,
                                 'proportional_drag_transport_identity_defect':defect,
                                 'field_seconds':field_seconds,'Jacobian_seconds':jac_seconds}

    def test_geometric_inertia_is_not_frozen(self):
        m=self.model; z=torch.tensor(self.z,requires_grad=True)
        p=z[12:]; mass=m.mass_tensor(z[:12]); velocity=torch.linalg.solve(mass,p)
        kinetic=.5*p@velocity
        geometric=torch.autograd.grad(kinetic,z)[0][:12].detach().numpy()
        self.assertGreater(np.linalg.norm(geometric),1e-6)
        self.records['kinetic_configuration_gradient_norm']=float(np.linalg.norm(geometric))

    def test_magnetic_force_and_virtual_power(self):
        m=self.model; z=self.z
        u=np.array([1.1e-4,-1.3e-4,.4e-4,.003,-.002,.001,.004,-.003])
        start=time.perf_counter(); gm=m.magnetic_map(z[:12]); elapsed=time.perf_counter()-start
        delta=m.field(z,u=u)-m.field(z)
        force=gm@u
        error=np.linalg.norm(force-delta[12:])
        self.assertLess(error,1e-10)
        self.assertLess(np.linalg.norm(delta[:12]),1e-12)
        v=self.direction[:12]; eps=2e-6
        potential=lambda Q:float(m.magnetic_potential_features_tensor(torch.tensor(Q)).detach().numpy()@u)
        finite=-(potential(z[:12]+eps*v)-potential(z[:12]-eps*v))/(2*eps)
        work_error=abs(finite-force@v)
        self.assertLess(work_error,1e-8)
        gradient=np.array([[u[3],u[5],u[6]],[u[5],u[4],u[7]],[u[6],u[7],-u[3]-u[4]]])
        self.assertEqual(np.trace(gradient),0.)
        self.assertEqual(np.linalg.norm(gradient-gradient.T),0.)
        self.records['magnetic']={'map_shape':list(gm.shape),'force_identity_error':error,
                                 'virtual_power_absolute_error':work_error,'map_seconds':elapsed,
                                 'singular_values_unscaled_SI_columns':np.linalg.svd(gm,compute_uv=False).tolist()}

    def test_differentiable_tensor_api(self):
        m=self.model; z=torch.tensor(self.z); direction=torch.tensor(self.direction)
        field=m.field_tensor(z)
        self.assertLess(np.linalg.norm(field.detach().numpy()-m.field(self.z)),1e-12)
        _,jvp=torch.func.jvp(m.field_tensor,(z,),(direction,))
        self.assertLess(np.linalg.norm(jvp.detach().numpy()-m.jacobian(self.z)@self.direction),1e-8)

    @classmethod
    def tearDownClass(cls):
        report={'metadata':cls.model.metadata(), 'diagnostics':cls.records,
                'source_sha256':hashlib.sha256((SOURCE/'rod_rom.py').read_bytes()).hexdigest(),
                'initial_state':cls.z.tolist(),
                'scope':'12/24-dimensional smooth Kirchhoff ROM bridge; no new fluid/contact closure or KAM certificate'}
        out=STAGE3/'results/rom_bridge.json';out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    unittest.main(verbosity=2)
