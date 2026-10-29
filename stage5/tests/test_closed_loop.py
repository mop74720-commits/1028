"""Independent directional and power checks for the realized implicit feedback."""
from pathlib import Path
import json
import sys
import unittest
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'stage5/program'))
from coil_rom import CoilROM
from closed_loop import ClosedLoop, implicit_midpoint, step, TOLERANCE


class ClosedLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=CoilROM()
        cls.z=cls.model.initial_state(.01)
        cls.feedback=ClosedLoop(cls.model,'collocated')
        cls.conservative=ClosedLoop(cls.model,'conservative')
        cls.records={}
        rng=np.random.default_rng(51029)
        cls.direction=rng.normal(size=24);cls.direction/=np.linalg.norm(cls.direction)

    def test_full_feedback_jacobian_not_frozen_current(self):
        z=self.z;v=self.direction;eps=1e-6;loop=self.feedback
        full=loop.jacobian(z)
        finite=(loop.field(0,z+eps*v)-loop.field(0,z-eps*v))/(2*eps)
        relative=np.linalg.norm(finite-full@v)/np.linalg.norm(full@v)
        frozen=self.model.jacobian(z,currents=loop.current_command(z))
        omitted=np.linalg.norm(full-frozen,2)
        self.assertLess(relative,2e-6)
        self.assertGreater(omitted,1e-5)
        self.records['feedback_jacobian']=dict(directional_relative_error=relative,
            omitted_current_chain_rule_norm=omitted,finite_difference_epsilon=eps)

    def test_magnetic_and_mechanical_power(self):
        data=self.feedback.energy_and_power(self.z)
        self.assertLess(abs(data['fixed_bias_power_identity_residual']),1e-11)
        self.assertLess(abs(data['mechanical_power_identity_residual']),1e-11)
        self.assertLess(abs(data['incremental_magnetic_power']-data['collocated_expected_power']),1e-11)
        self.assertLess(data['incremental_magnetic_power'],0.)
        self.records['power']=data

    def test_feedback_is_inside_same_implicit_residual(self):
        h=.000125;z=self.z;loop=self.feedback
        y,D,info=implicit_midpoint(loop,z,h)
        middle=(z+y)/2
        i_mid=loop.current_command(middle)
        explicit_physical=self.model.field(middle,currents=i_mid)
        residual=y-z-h*explicit_physical
        self.assertLessEqual(np.linalg.norm(residual,np.inf),TOLERANCE)
        no_feedback,_D,_info=implicit_midpoint(self.conservative,z,h)
        after_step=no_feedback+h*(loop.field(0,z)-self.conservative.field(0,z))
        incorrect=np.linalg.norm(after_step-z-h*loop.field(0,(z+after_step)/2),np.inf)
        self.assertGreater(incorrect,20*TOLERANCE)
        defect=np.linalg.norm(D.T@loop.K0@D-loop.K0,2)
        self.assertGreater(defect,1e-9)
        self.records['implicit_feedback']=dict(true_residual_inf=float(np.linalg.norm(residual,np.inf)),
            post_step_control_residual_inf=float(incorrect),canonical_defect=float(defect),solver=info)

    def test_solved_map_tangent_direction(self):
        z=self.z;h=.000125;eps=1e-6;v=self.direction
        _,D,_=implicit_midpoint(self.feedback,z,h)
        plus,_,_=implicit_midpoint(self.feedback,z+eps*v,h)
        minus,_,_=implicit_midpoint(self.feedback,z-eps*v,h)
        finite=(plus-minus)/(2*eps)
        relative=np.linalg.norm(finite-D@v)/np.linalg.norm(D@v)
        self.assertLess(relative,2e-6)
        self.records['actual_solved_map_directional_error']=float(relative)

    def test_legal_structure_and_illegal_method_rejected(self):
        h=.000125;z=self.z
        _,D,_=step(self.conservative,z,h,'midpoint')
        defect=np.linalg.norm(D.T@self.model.K0@D-self.model.K0,2)
        proportional=ClosedLoop(self.model,'proportional')
        _,W,_=step(proportional,z,h,'weighted_midpoint')
        weighted=np.linalg.norm(W.T@self.model.K0@W-np.exp(-proportional.gamma*h)*self.model.K0,2)
        self.assertLess(defect,1e-11)
        self.assertLess(weighted,1e-11)
        with self.assertRaises(ValueError):step(self.feedback,z,h,'weighted_midpoint')
        with self.assertRaises(ValueError):step(self.feedback,z,h,'central4')
        self.records['legal_structure']=dict(midpoint_defect=float(defect),weighted_defect=float(weighted))

    @classmethod
    def tearDownClass(cls):
        out=ROOT/'stage5/results/closed_loop';out.mkdir(parents=True,exist_ok=True)
        (out/'independent_checks.json').write_text(json.dumps(cls.records,indent=2)+'\n')


if __name__=='__main__':unittest.main(verbosity=2)
