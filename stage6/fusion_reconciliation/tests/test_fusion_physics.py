"""Independent geometric and actual magnetic-power tests; no frozen writes."""
from pathlib import Path
import sys
import unittest
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'program'))
from fusion_physics import CoilROM, PowerCurrentAllocator, clearance_coefficient, mechanical_energy, power_port


class PhysicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = CoilROM()  # actual full 20-cell, 24-dimensional ROM

    def test_3d_clearance_bound_for_actual_embedding(self):
        m = self.model
        rng = np.random.default_rng(1025)
        coefficient = clearance_coefficient(m.rom.L, float(m.rom.bending.min()))
        for amplitude in [.02, .1, .4, 1.]:
            q = rng.normal(size=12)*amplitude
            _, elastic, positions, frames, _ = m.rom.mechanics(m.tensor(q)[None, :], field=m.zero_field, return_geometry=True)
            rest = np.zeros_like(positions[0].numpy())
            rest[:, 2] = np.linspace(0, m.rom.L, m.rom.elements+1)
            maximum = np.linalg.norm(positions[0].numpy()-rest, axis=1).max()
            self.assertLessEqual(maximum**2, coefficient*float(elastic[0])*(1+1e-12))
            self.assertLess(np.linalg.norm((frames.transpose(-1,-2)@frames-torch.eye(3)).numpy()), 1e-12)

    def test_stretch_shear_cannot_be_omitted(self):
        # Straight shear r(s)=(epsilon*s,0,s), D=I has zero curvature.
        length, shear, eps = .1, 2., .03
        energy = .5*shear*length*eps**2
        displacement = length*abs(eps)
        self.assertGreater(displacement, 0.)
        self.assertAlmostEqual(displacement**2, (2*length/shear)*energy)
        self.assertGreaterEqual(clearance_coefficient(length, 1e3, shear)*energy, displacement**2)

    def test_signed_coil_hamiltonian_is_not_clearance_energy(self):
        m = self.model
        z = m.initial_state(.01)
        self.assertGreater(mechanical_energy(m, z), 0.)
        self.assertLess(m.hamiltonian(z, m.bias_currents), 0.)

    def test_true_coil_power_and_allocation(self):
        m = self.model
        z = m.initial_state(.01)
        y, velocity = power_port(m, z)
        currents = .2*np.sin(np.arange(m.current_channels)+.5)
        gamma = .17
        f = m.field(z, currents, gamma=gamma)
        gradient = torch.func.grad(lambda x:m.hamiltonian_tensor(x, torch.zeros(m.current_channels)))(m.tensor(z)).numpy()
        self.assertLess(abs(gradient@f-(y@currents-gamma*velocity@z[m.n:])), 2e-13)
        # Loose field/box restrictions make the sole active constraint a
        # half-space, so there is an independent analytic projection oracle.
        allocator = PowerCurrentAllocator(m, field_bound_T=1., gradient_bound_T_per_m=100.)
        requested = .03*y/np.linalg.norm(y)
        upper = .2*(y@requested)
        got, record = allocator.allocate_power(z, requested, np.zeros(12), 1., upper)
        expected = requested-(y@requested-upper)*y/(y@y)
        self.assertLess(np.linalg.norm(got-expected), 2e-8)
        self.assertLessEqual(record['allocated_power_dE0_dtau']-upper, 1e-12)

    def test_slew_can_destroy_zero_input_feasibility(self):
        m = self.model
        z = m.initial_state(.01)
        y, _ = power_port(m, z)
        previous = .05*np.sign(y)
        cap = m.coil_config['slew_bound_A_s']*1e-7
        self.assertGreater(y@previous-cap*np.sum(abs(y)), 0.)
        allocator = PowerCurrentAllocator(m, field_bound_T=1., gradient_bound_T_per_m=100.)
        with self.assertRaisesRegex(RuntimeError, 'Power/current allocation'):
            allocator.allocate_power(z, previous, previous, 1e-7, 0.)


if __name__ == '__main__':
    unittest.main()
