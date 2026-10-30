import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import torch

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'program'))
from learned_reference_tracking import CoilROM,LearnedReference,tracking_request,identity_diagnostics,velocity_tensor,acceleration,CHECKPOINT


class TrackingConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plant=CoilROM();cls.ref=LearnedReference(cls.plant)

    def test_frozen_complete_complex_reference_and_chain_rule(self):
        p,r=self.plant,self.ref;z=p.initial_state(.03)
        d=np.random.default_rng(612).normal(size=24);d/=np.linalg.norm(d)
        eps=1e-6
        fd=float((r.hamiltonian_tensor(p.tensor(z+eps*d))-r.hamiltonian_tensor(p.tensor(z-eps*d)))/(2*eps))
        analytic=float((-p.J@r.field(z))@d)
        self.assertAlmostEqual(fd,analytic,delta=2e-7)
        self.assertTrue(any(v.is_complex() for v in r.net.parameters()))
        self.assertEqual(r.metadata['checkpoint_sha256'],hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest())

    def test_geometric_acceleration_by_independent_velocity_difference(self):
        p=self.plant;z=p.initial_state(.025);current=p.bias_currents.copy();current[0]+=.001
        field=p.field(z,current,.05);eps=2e-7/max(1.,np.linalg.norm(field))
        vp=velocity_tensor(p,p.tensor(z+eps*field)).detach().numpy()
        vm=velocity_tensor(p,p.tensor(z-eps*field)).detach().numpy()
        exact=acceleration(p,z,current,.05)
        self.assertLess(np.linalg.norm((vp-vm)/(2*eps)-exact)/max(1.,np.linalg.norm(exact)),2e-7)

    def test_actual_force_identity_and_constant_mass_counterexample(self):
        p,r=self.plant,self.ref;zr=p.initial_state(.08);z=zr.copy();z[:12]+=.002/np.sqrt(p.rom.nu.numpy())
        current=p.bias_currents.copy();current[1]+=.003
        diag=identity_diagnostics(p,r,z,zr,current,gamma=.05)
        self.assertLess(diag['identity_relative_residual'],2e-11)
        self.assertGreater(diag['force_residual_norm'],1e-4)
        self.assertGreater(diag['constant_mass_substitution_error'],1e-5)

    def test_recorded_actual_coil_run_is_bounded_but_not_exact_tracking(self):
        d=json.loads((BASE/'results/history/S6_T01/results.json').read_text());s=d['summary']
        self.assertLess(s['max_identity_residual'],2e-10)
        self.assertLessEqual(s['max_current_A'],2.+1e-10)
        self.assertLessEqual(s['max_planned_slew_A_s'],20.+1e-8)
        self.assertLessEqual(s['max_sampled_field_T'],.005)
        self.assertLessEqual(s['max_sampled_gradient_T_per_m'],.03)
        self.assertLess(s['max_sampled_power_residual'],1e-10)
        self.assertTrue(all(x['allocation']['rank']<12 for x in d['steps']))
        self.assertTrue(all(x['allocation']['constrained_force_residual']>1e-3 for x in d['steps']))
        self.assertGreater(s['final_actual_vs_ideal_force_oracle'],1e-8)

if __name__=='__main__':unittest.main(verbosity=2)
