"""Read the newly recomputed FE baseline and audit simulation domains.

This helper is diagnostic only. It does not change the inherited integration,
identification or control equations. All reported maxima are sampled numerical
values, not interval bounds or actuator calibration certificates.
"""
from pathlib import Path
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parent
PARAMETER_FILE = ROOT.parent / 'new_baseline.json'
BASELINE = json.loads(PARAMETER_FILE.read_text(encoding='utf-8'))
REDUCED = BASELINE['reduced']
AMPLITUDE_SCALE = 0.5


def scaled(values):
    return (AMPLITUDE_SCALE * np.asarray(values, dtype=float)).tolist()


def provenance():
    return {
        'parameter_file': str(PARAMETER_FILE),
        'parameter_sha256': hashlib.sha256(PARAMETER_FILE.read_bytes()).hexdigest(),
        'amplitude_scale_relative_to_archived_experiment': AMPLITUDE_SCALE,
        'amplitude_scaling_scope': 'all training/validation initial states, route-A test initial state, route-B reference and initial-offset states',
        'amplitude_scaling_origin': 'explicit experimental design for the softer literature-based beam; not a measured amplitude distribution',
        'beta_0p2_origin': 'artificial potential-residual stress test, not a measured material or robot parameter',
        'baseline_damping_design': 'zeta1=0.025, alpha=2*zeta1*omega0, gamma=alpha/omega0=0.05; a scenario, not measured damping',
        'nontransferable_old_results': 'previous frozen modes, learned fit, long-run values and KAM diagnostics/certificates are not imported',
        'state_error_definition': 'sqrt(mean_k ||actual_k-reference_k||_2^2); four balanced dimensionless phase coordinates; no extra division by four',
        'input_status': 'ideal independent local field and gradient commands; no device calibration, saturation or hardware implementation claim',
    }


def state_domain(states, A):
    states = np.asarray(states)
    phase = states[:, :4]
    theta = phase[:, :2] @ A.D
    report = {
        'sample_count': len(phase),
        'maximum_abs_phase_coordinate': np.max(np.abs(phase), axis=0).tolist(),
        'minimum_phase_coordinate': np.min(phase, axis=0).tolist(),
        'maximum_phase_coordinate': np.max(phase, axis=0).tolist(),
        'maximum_phase_pair_radius': np.max(np.sqrt(phase[:, :2]**2+phase[:, 2:]**2), axis=0).tolist(),
        'maximum_abs_tip_angle_rad': float(np.max(np.abs(theta))),
        'minimum_abs_cos_tip_angle': float(np.min(np.abs(np.cos(theta)))),
        'maximum_abs_tip_displacement_m': float(np.max(np.abs(phase[:, :2] @ A.ELL))),
        'maxima_status': 'sampled along numerical trajectory, not a continuous-time certified bound',
    }
    maps = BASELINE.get('sampled_modes')
    if maps is not None:
        d_x = np.asarray(maps['d_x'])
        ell_x = np.asarray(maps['ell_x_m'])
        slope = 0.
        displacement = 0.
        for left in range(0, len(phase), 512):
            x = phase[left:left+512, :2]
            slope = max(slope, float(np.max(np.abs(x @ d_x.T))))
            displacement = max(displacement, float(np.max(np.abs(x @ ell_x.T))))
        report['maximum_abs_beam_slope_spatial_grid'] = slope
        report['maximum_abs_beam_displacement_spatial_grid_m'] = displacement
        report['spatial_grid_count'] = len(maps['x_m'])
    return report


def physical_error_metrics(errors, A):
    errors = np.asarray(errors)
    tip = errors[:, :2] @ A.ELL
    angle = errors[:, :2] @ A.D
    return {
        'RMS_tip_displacement_error_m': float(np.sqrt(np.mean(tip**2))),
        'maximum_abs_tip_displacement_error_m': float(np.max(np.abs(tip))),
        'RMS_tip_angle_error_rad': float(np.sqrt(np.mean(angle**2))),
    }


def input_domain(states, A, control_function):
    """Check stored endpoints and the midpoints used by the midpoint solver."""
    maxima = np.zeros(5)
    reconstruction = 0.
    for batch in (states, (states[:-1]+states[1:])/2):
        for state in batch:
            z = state[:4]
            requested = control_function(state)
            applied, force, torque, by, gradient = A.physical_ports(z, requested)
            values = [abs(by), np.hypot(A.B0, by), abs(force)/A.MU,
                      abs(force), abs(A.MU*by*np.cos(A.D @ z[:2]))]
            maxima = np.maximum(maxima, values)
            reconstruction = max(reconstruction, float(np.linalg.norm(applied-requested)))
    return {
        'maximum_abs_By_T': float(maxima[0]),
        'maximum_total_local_field_T': float(maxima[1]),
        'total_local_field_formula': 'sqrt(B0^2 + By^2)',
        'maximum_local_gradient_spectral2_T_per_m': float(maxima[2]),
        'maximum_abs_tip_force_N': float(maxima[3]),
        'maximum_abs_added_By_torque_N_m': float(maxima[4]),
        'maximum_input_reconstruction_error': reconstruction,
        'sampled_sites': 'all stored endpoints and all adjacent state midpoints',
        'implementation_status': 'algebraic ideal local port realization; no coil design or device limit verified',
    }
