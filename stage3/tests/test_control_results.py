"""Check generated physical-control evidence after the documented experiments."""
from pathlib import Path
import hashlib
import json
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

class ControlEvidenceTests(unittest.TestCase):
    def test_new_learning_labels_and_actuator_limits(self):
        result=json.loads((ROOT/'results/control_learning/learning_results.json').read_text())
        source=ROOT/'program/control_learning.py'
        self.assertEqual(result['source_sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
        data=np.load(ROOT/'results/control_learning/learning_data_and_trajectories.npz')
        self.assertEqual(data['train_states'].shape,(8,24))
        self.assertEqual(data['heldout_states'].shape,(8,24))
        self.assertFalse(np.array_equal(data['train_states'],data['heldout_states']))
        self.assertLess(result['scores']['heldout']['force_relative_l2'],1e-10)
        self.assertLess(result['actuator_limits']['affine_workspace_upper_bound_T'],.005)
        self.assertLess(result['uncancelled_actual_magnetic_force_norm'],1e-10)

    def test_full_coil_virtual_work_and_constraints(self):
        result=json.loads((ROOT/'results/control/full_coil_force_audit.json').read_text())
        source=ROOT/'program/control_coil_force.py'
        self.assertEqual(result['source_sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
        for record in result['records']:
            audit=record['independent_virtual_work']
            self.assertLess(audit['affine_virtual_work_vs_Gm_difference'],1e-10)
            self.assertLess(audit['full_force_virtual_work_vs_energy_gradient_difference'],1e-7)
            self.assertLess(audit['origin_gradient_reconstruction_error_T_per_m'],1e-8)
        for stress in result['constraint_stress']:
            self.assertLessEqual(stress['bounded_limits']['affine_workspace_upper_bound_T'],.005+1e-14)
            self.assertLessEqual(stress['bounded_limits']['gradient_frobenius_T_per_m'],.03+1e-14)
        coil=json.loads((ROOT/'results/control/control_results.json').read_text())['coil_allocation']
        self.assertLessEqual(coil['maximum_current_A'],2.+1e-12)
        self.assertLessEqual(coil['maximum_sample_difference_slew_A_s'],20.+1e-10)

if __name__=='__main__':unittest.main()
