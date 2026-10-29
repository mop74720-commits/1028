"""Full-coil power-port feedback on the inherited three-dimensional Cosserat rod.

Only stage5 outputs are written. The prescribed flow, rigid-wall contact,
friction, microgravity benchmark and full SO(3)/shear/stretch dynamics are
inherited unmodified. No learned weights or arbitrary modal forces are used.
"""
from pathlib import Path
import os
import sys
import numpy as np
from scipy.optimize import minimize, Bounds

sys.dont_write_bytecode = True
os.environ.setdefault('NUMBA_CACHE_DIR', '/tmp/1028-stage5-rod-numba')
os.environ.setdefault('MPLCONFIGDIR', '/tmp/1028-stage5-rod-mpl')
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'stage3/source_inputs/starter/stage2/program/rod3d'
sys.path.insert(0, str(SOURCE))
import model as base
import run_biot_savart as bs
import run_biot_savart_constrained as guard

OUTPUT = ROOT/'stage5/results/rod_transfer'
OUTPUT.mkdir(parents=True, exist_ok=True)
guard.OUT = OUTPUT


def current_power_port(rod, env):
    """y_j in W/A, with spatial nodal force and material-frame couple power."""
    port = np.zeros(12)
    for j in range(12):
        current = np.eye(12)[j]
        force, torque, _ = bs.magnetic_loads(
            rod.position_collection, rod.director_collection,
            env.dipole_body, env.dipole_alpha,
            env.wire, env.dl, current, env.prefactor)
        port[j] = np.sum(force*rod.velocity_collection)+np.sum(torque*rod.omega_collection)
    return port


class CurrentSpaceAllocator(guard.TubeConstrainedAllocator):
    """Euclidean projection in actual coil currents, not affine field space."""
    def __init__(self, config):
        super().__init__(config)
        self.feasibility_repairs = 0
        self.repair_log = []

    def project(self, requested_current, time_s):
        dt = max(0., float(time_s)-self.last_time)
        if dt == 0.:
            return self.currents.copy(), 0., True
        bound = self.config['current_bound_A']
        cap = self.config['slew_bound_A_s']*dt
        lo = np.maximum(-bound, self.currents-cap)
        hi = np.minimum(bound, self.currents+cap)
        target = np.asarray(requested_current)
        result = minimize(lambda x: .5*np.dot(x-target, x-target), self.currents,
                          jac=lambda x: x-target, method='SLSQP', bounds=Bounds(lo, hi),
                          constraints=[dict(type='ineq', fun=self.constraints,
                                            jac=self.constraint_jac)],
                          options=dict(ftol=1e-11, maxiter=100, disp=False))
        self.solves += 1
        if not result.success:
            self.nonconverged += 1
        candidate = np.clip(result.x, lo, hi)
        # SLSQP sometimes returns a finite, almost feasible candidate with a
        # directional-derivative status. Replacing an entire control interval
        # by the old current then amplifies a tiny solver perturbation into a
        # discontinuous actuation change. Restore feasibility analytically on
        # the segment from the previous feasible endpoint; do not relax bounds.
        alpha = 1.
        if np.isfinite(candidate).all():
            direction = candidate-self.currents
            a = np.einsum('a,pab,b->p', direction, self.S, direction)
            b = 2*np.einsum('a,pab,b->p', self.currents, self.S, direction)
            c = np.einsum('a,pab,b->p', self.currents, self.S, self.currents)-(1.-1e-12)
            for aa, bb, cc in zip(a, b, c):
                if aa+bb+cc > 0.:
                    if aa > 1e-30:
                        root = (-bb+np.sqrt(max(0., bb*bb-4*aa*cc)))/(2*aa)
                    elif bb > 0.:
                        root = -cc/bb
                    else:
                        root = 0.
                    alpha = min(alpha, max(0., root)*(1.-1e-10))
            if alpha < 1.:
                candidate = self.currents+alpha*direction
                self.feasibility_repairs += 1
                self.repair_log.append(dict(time_s=float(time_s), segment_fraction=float(alpha),
                                           current_correction_norm_A=float((1-alpha)*np.linalg.norm(direction))))
        violation = (max(0., -float(self.constraints(candidate).min()),
                         float(np.max(lo-candidate)), float(np.max(candidate-hi)))
                     if np.isfinite(candidate).all() else float('inf'))
        if violation > 1e-10:
            candidate = self.currents.copy()
            self.fallbacks += 1
        self.max_constraint_violation = max(
            self.max_constraint_violation, max(0., -float(self.constraints(candidate).min())))
        self.currents = candidate
        self.last_time = float(time_s)
        return candidate.copy(), float(np.linalg.norm(candidate-target)), bool(result.success)


class TransferredEnvironment(bs.FullCoilEnvironment):
    """Sampled full-coil collocated current feedback plus inherited tracking.

    i_req=i_ff-kappa*y, kappa in A^2/W. Tube constraints and slew are imposed on
    target currents, then actual currents ramp continuously. Thus ideal
    instantaneous damping is a reference identity, not a claim about the
    constrained, delayed controller's instantaneous incremental power.
    """
    instances = []
    gain_A2_per_W = 0.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allocator = CurrentSpaceAllocator(self.allocator.config)
        self.ramp_start = np.zeros(12)
        self.ramp_target = np.zeros(12)
        self.ramp_time = 0.
        self.ramp_log = []
        self.feedback_log = []
        self.last_port = np.zeros(12)
        self.last_ff = np.zeros(12)
        self.instances.append(self)

    def evaluate(self, rod, time):
        theta = np.clip((float(time)-self.ramp_time)/self.control_period, 0., 1.)
        self.currents = (1-theta)*self.ramp_start+theta*self.ramp_target
        self.held_u = self.allocator.A@self.currents
        return super().evaluate(rod, time)

    def apply_forces(self, system, time=0.):
        rod = system
        index = int(np.floor((float(time)+1e-12)/self.control_period))
        if index > self.control_index:
            control_time = index*self.control_period
            _, requested_field, _, _ = self.desired_command(rod, float(time))
            # This nominal feedforward/position law is explicitly inherited
            # from S2; full-coil feedback and actual force evaluation are new.
            design = self.allocator.A/self.allocator.scale[:, None]
            ff = np.linalg.lstsq(np.vstack([design, 1e-3*np.eye(12)]),
                                np.r_[requested_field/self.allocator.scale, np.zeros(12)],
                                rcond=None)[0]
            port = current_power_port(rod, self)
            requested_current = ff-self.gain_A2_per_W*port
            start = self.ramp_target.copy()
            target, residual, success = self.allocator.project(requested_current, control_time)
            self.ramp_start, self.ramp_target, self.ramp_time = start, target, control_time
            self.last_ff, self.last_port = ff, port
            self.ramp_log.append(np.r_[control_time, control_time+self.control_period, start, target])
            self.coil_log.append(np.r_[control_time, requested_field, self.allocator.A@start, start])
            self.feedback_log.append(dict(
                time_s=control_time, power_port_W_per_A=port.tolist(),
                nominal_current_A=ff.tolist(), requested_current_A=requested_current.tolist(),
                target_current_A=target.tolist(), current_projection_residual_A=residual,
                ideal_incremental_power_W=float(-self.gain_A2_per_W*np.dot(port, port)),
                projected_incremental_power_W=float(np.dot(port, target-ff)),
                current_start_incremental_power_W=float(np.dot(port, start-ff)),
                optimizer_success=success))
            self.control_index = index
        self.last = self.evaluate(rod, time)
        self.before_v, self.before_w = rod.velocity_collection.copy(), rod.omega_collection.copy()
        rod.external_forces += self.last[0].sum(axis=0)
        rod.external_torques += self.last[1].sum(axis=0)


def configure(gain):
    TransferredEnvironment.gain_A2_per_W = float(gain)
    base.Environment = TransferredEnvironment
    base.metrics_snapshot = bs.full_snapshot


def constraint_summary(env):
    ramps = np.asarray(env.ramp_log)
    slopes = (ramps[:, 14:26]-ramps[:, 2:14])/(ramps[:, 1]-ramps[:, 0])[:, None]
    continuity = float(np.max(np.abs(ramps[1:, 2:14]-ramps[:-1, 14:26]))) if len(ramps)>1 else 0.
    result = dict(env.allocator.audit)
    result.update(actual_current_amplitude_max_A=float(np.max(np.abs(ramps[:, 2:26]))),
                  actual_current_slew_max_A_per_s=float(np.max(np.abs(slopes))),
                  continuity_defect_A=continuity, allocation_calls=env.allocator.solves,
                  optimizer_nonconverged=env.allocator.nonconverged,
                  fallback_count=env.allocator.fallbacks,
                  analytic_feasibility_repairs=env.allocator.feasibility_repairs,
                  feasibility_repair_log=env.allocator.repair_log,
                  maximum_sampled_constraint_violation=env.allocator.max_constraint_violation,
                  collocated_gain_A2_per_W=env.gain_A2_per_W,
                  law='i_req=i_ff-kappa*y, y_j=F_j.v+tau_j.omega in W/A',
                  allocation_scope='SLSQP candidate plus exact quadratic segment feasibility repair. Nonconverged but feasible candidates are recorded, not called certified optimizers.',
                  instantaneous_dissipation_scope='Only unconstrained zero-delay increment -kappa*y has guaranteed nonpositive power. Projection about nonzero nominal current and ramp delay may violate that incremental inequality.',
                  continuous_constraint_scope='Current segments connect feasible endpoints; convex field/gradient norms remain feasible at the fixed tube sample points, not everywhere in the moving lumen.')
    assert result['actual_current_amplitude_max_A'] <= 2.+1e-8
    assert result['actual_current_slew_max_A_per_s'] <= 20.+1e-8
    assert continuity < 1e-12
    return result
