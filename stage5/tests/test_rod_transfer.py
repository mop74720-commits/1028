"""Independent energy/power and constraint checks for the Cosserat transfer."""
from pathlib import Path
import sys
import unittest
import json
import time
import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'stage5/program'))
import rod_transfer_control as transfer


class TestRodTransfer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.started = time.perf_counter()
        transfer.configure(95590.3224538941)
        cls.cfg = transfer.base.load_config(transfer.SOURCE/'config_position_feedback.json')
        _, cls.rod, cls.env = transfer.base.make_model(cls.cfg, 32, 2, coil=True)
        rng = np.random.default_rng(102505)
        cls.rod.velocity_collection[:] = rng.normal(scale=.002, size=cls.rod.velocity_collection.shape)
        cls.rod.omega_collection[:] = rng.normal(scale=.2, size=cls.rod.omega_collection.shape)
        cls.rod.velocity_collection[:, 0] = 0.
        cls.rod.omega_collection[:, 0] = 0.
        cls.currents = np.linspace(-.7, .9, 12)
        cls.result = {}

    def test_power_port_matches_fixed_current_energy_derivative(self):
        rod, env = self.rod, self.env
        y = transfer.current_power_port(rod, env)
        r0, d0 = rod.position_collection.copy(), rod.director_collection.copy()
        def energy(eps):
            r = r0+eps*rod.velocity_collection
            d = np.stack([Rotation.from_rotvec(-eps*rod.omega_collection[:, j]).as_matrix()@d0[:, :, j]
                          for j in range(d0.shape[2])], axis=2)
            return transfer.bs.magnetic_loads(r, d, env.dipole_body, env.dipole_alpha,
                                             env.wire, env.dl, self.currents, env.prefactor)[2]
        exact_power = float(y@self.currents)
        steps = [1e-4, 5e-5, 2.5e-5]
        derivative = [-(energy(e)-energy(-e))/(2*e) for e in steps]
        relative = abs(derivative[-1]-exact_power)/max(abs(exact_power), 1e-15)
        self.assertLess(relative, 2e-7)
        self.result['joint_translation_rotation_virtual_work'] = dict(
            exact_current_port_power_W=exact_power, eps_s=steps,
            energy_directional_power_W=derivative, relative_error=relative,
            tolerance=2e-7, coordinates='spatial translation and exp(-eps*omega_body) applied to material directors')

    def test_ideal_feedback_power_and_unavoidable_constraint_residual(self):
        y = transfer.current_power_port(self.rod, self.env)
        gain = 95590.3224538941
        delta = -gain*y
        identity = float(y@delta+gain*(y@y))
        self.assertLess(abs(identity), 1e-20)
        self.assertLessEqual(y@delta, 0.)
        # A deliberately infeasible target tests actual current constraints.
        target, residual, success = self.env.allocator.project(np.linspace(-10., 10., 12), .002)
        self.assertLessEqual(float(np.max(np.abs(target))), .04+1e-8)
        self.assertGreater(residual, 1.)
        self.assertGreaterEqual(float(self.env.allocator.constraints(target).min()), -1e-8)
        self.result['ideal_damping_and_constraints'] = dict(
            ideal_power_W=float(y@delta), identity_error_W=identity,
            actual_max_current_A=float(np.max(np.abs(target))),
            projection_residual_A=residual, optimizer_success=success,
            minimum_sampled_constraint_margin=float(self.env.allocator.constraints(target).min()),
            tolerance=1e-8,
            scope='Unconstrained damping identity plus constrained infeasible-target residual; not a sampled closed-loop passivity theorem')

    @classmethod
    def tearDownClass(cls):
        cls.result.update(status='independently_executed', command='rod Python -m unittest discover -s stage5/tests -p test_rod_transfer.py -v',
                          elapsed_s=time.perf_counter()-cls.started, python=sys.version)
        (ROOT/'stage5/results/rod_transfer/operator_tests.json').write_text(json.dumps(cls.result, indent=2)+'\n')


if __name__ == '__main__':
    unittest.main()
