"""Refit and rerun short route-A/B tests for explicitly chosen damping scenarios.

Run after minimal_control_loop.py and route_b_shared_data.py. Each zeta1 value
regenerates its own six synthetic trajectories and refits beta/gamma; it never
reuses the old package fit. These are sensitivity scenarios, not confidence
intervals, material measurements or KAM certificates. beta=0.2 stays artificial.
"""
from pathlib import Path
import json
import time
import numpy as np

import minimal_control_loop as A
import route_b_shared_data as B
from baseline_config import scaled, provenance, state_domain

ROOT = Path(__file__).resolve().parent
ZETAS = [0., .01, .025, .05, .1]
TRAIN = scaled([[.18,.14,.05,-.04],[-.15,.20,.02,.05],
                [.22,-.12,-.03,.06],[.10,.24,.04,-.02]])
VALIDATION = scaled([[-.19,.11,.06,.01],[.13,-.21,-.04,.03]])
INITIAL = np.array(scaled([.18,.16,.03,-.02]))
PERTURBATION = np.array(scaled([.009,.008,0.,0.]))
DURATION, STEP, REF_STEP = 10., .002, .00025


def set_damping_scenario(zeta1):
    # The inherited field() captures gamma in its default arguments. Updating
    # both the global and that default keeps data, plant and Jacobian consistent.
    A.GAMMA = 2*zeta1
    A.ALPHA = A.GAMMA*A.OMEGA0
    A.field.__defaults__ = (A.BETA, A.GAMMA)
    A.IDENTIFICATION_DOMAINS.clear()
    B.A = A  # Route B uses this case's new true plant and newly fitted values.


def fit_case():
    design, labels = A.identification_rows(TRAIN)
    validation_design, validation_labels = A.identification_rows(VALIDATION)
    column_scale = np.linalg.norm(design, axis=0)
    fitted = np.linalg.lstsq(design/column_scale, labels, rcond=None)[0]/column_scale
    gram = design.T @ design / len(labels)
    lam = float(np.linalg.eigvalsh(gram)[0])
    truth = np.array([A.BETA, A.GAMMA])
    residual = float(np.sqrt(np.mean((design@fitted-labels)**2)))
    defect = float(np.sqrt(np.mean((design@truth-labels)**2)))
    bound = (residual+defect)/np.sqrt(lam)
    error = float(np.linalg.norm(fitted-truth))
    assert np.linalg.matrix_rank(design)==2 and lam>0
    assert error <= bound*(1+1e-10)
    return fitted, {
        'beta_hat': float(fitted[0]), 'gamma_hat': float(fitted[1]),
        'true_parameters': truth.tolist(),
        'actual_coefficient_error_synthetic_truth_only': error,
        'training_RMSE': residual,
        'validation_RMSE': float(np.sqrt(np.mean((validation_design@fitted-validation_labels)**2))),
        'normalized_Gram': gram.tolist(), 'lambda_min_normalized_Gram': lam,
        'raw_design_condition2': float(np.linalg.cond(design)),
        'column_scaled_design_condition2': float(np.linalg.cond(design/column_scale)),
        'epsilonI_truth_diagnostic_only': defect,
        'coefficient_bound_truth_diagnostic_only': float(bound),
        'independent_rigorous_epsilonI_available': False,
        'fit_method': 'unchanged column-scaled unconstrained two-scalar least squares',
        'training_scalar_rows': len(labels),
        'training_trajectory_domains': A.IDENTIFICATION_DOMAINS[:len(TRAIN)],
        'validation_trajectory_domains': A.IDENTIFICATION_DOMAINS[len(TRAIN):],
        'test_data_used_for_fit': False,
    }


def check_group(report):
    assert report['input_domain']['maximum_input_reconstruction_error'] < 1e-12
    assert report['state_domain']['minimum_abs_cos_tip_angle'] > .9
    for value in report['state_domain']['maximum_abs_phase_coordinate']:
        assert np.isfinite(value)


def main():
    started = time.perf_counter()
    full_a = json.loads((ROOT/'minimal_control_results.json').read_text())
    full_b = json.loads((ROOT/'route_b_shared_results.json').read_text())
    assert full_a['status']=='all assertions passed'
    assert full_b['status']=='all assertions passed'
    # Same h0 target for all route-A damping cases; independent RK4 solver.
    reference_a = A.rk4(lambda z:A.field(z,0.,0.), INITIAL, DURATION, REF_STEP)
    target_a = reference_a[::int(round(STEP/REF_STEP))]
    reports = []
    metadata = {
        'scope': 'Short newly regenerated synthetic sensitivity tests on both routes; not noise confidence intervals, hardware validation, general CHNN training or KAM certification.',
        'new_baseline_provenance': provenance(),
        'zeta1_scenarios': ZETAS,
        'damping_model': 'C=alpha*M_total; alpha=2*zeta1*omega0, gamma=2*zeta1; zeta_j=zeta1/nu_j',
        'duration_tau': DURATION, 'duration_seconds': DURATION/A.OMEGA0,
        'midpoint_step_tau': STEP, 'independent_reference_RK4_step_tau': REF_STEP,
        'training_initials': TRAIN, 'validation_initials': VALIDATION,
        'training_duration_each_tau': 4., 'training_RK4_step_tau': .0005,
        'observation_step_tau': .002, 'integral_window_tau': .04,
        'route_a_initial_state': INITIAL.tolist(),
        'route_b_reference_initial_state': INITIAL.tolist(),
        'route_b_initial_offset': PERTURBATION.tolist(),
        'fit_recomputed_for_every_scenario': True,
        'beta_artificial_true': A.BETA,
        'RMS_definition': 'sqrt(mean_k ||z_k-reference_k||_2^2), no extra division by four',
        'reference_objects': {'route_a':'nominal coupled conservative h0',
                              'route_b':'this scenario fitted conservative hhat; same hhat for passive, learned and oracle'},
        'second_half_tau_interval': [DURATION/2,DURATION],
        'numerical_checks_scope': 'Full reference refinement and order checks in the baseline runs; short scenarios reuse those algorithms and report solver/reconstruction identities, not an additional convergence study.',
    }
    for zeta1 in ZETAS:
        case_started = time.perf_counter()
        set_damping_scenario(zeta1)
        fitted, identification = fit_case()
        bhat,ghat = map(float,fitted)
        print('scenario zeta1=',zeta1,'fit=',fitted,flush=True)
        route_a = {}
        for name,bb,gg in [('passive',0.,0.),('learned',bhat,ghat),('oracle',A.BETA,A.GAMMA)]:
            states,solver=A.midpoint(INITIAL,DURATION,STEP,bb,gg,name=='oracle')
            report={**A.metrics(states,target_a,STEP,bb,gg),**solver}
            check_group(report)
            route_a[name]=report
        # Reuse this case's fit, but recompute the actual conservative learned
        # reference. This is a short tracking test, not the entire route-B audit.
        reference_b=A.rk4(lambda z:A.field(z,bhat,0.),INITIAL,DURATION,REF_STEP)
        target_b=reference_b[::int(round(STEP/REF_STEP))]
        init=np.r_[INITIAL+PERTURBATION,INITIAL]
        route_b={}
        for name in ['passive','learned_tracking','oracle_tracking']:
            states,solver=B.integrate_midpoint(init,DURATION,STEP,name,bhat,ghat)
            report={**B.tracking_metrics(states,target_b,name,bhat,ghat,STEP),**solver}
            check_group(report)
            identity=report['maximum_tracking_equation_identity_defect']
            if identity is not None: assert identity<1e-12
            route_b[name]=report
        case={
            'zeta1_scenario':zeta1,'gamma_true':A.GAMMA,'alpha_s_inv':A.ALPHA,
            'modal_damping_ratios':(zeta1/A.NU).tolist(),
            'identification':identification,'route_a':route_a,'route_b':route_b,
            'elapsed_seconds':time.perf_counter()-case_started,
        }
        reports.append(case)
        output={**metadata,'scenarios':reports,
                'status':'in progress' if len(reports)<len(ZETAS) else 'all scenarios completed',
                'elapsed_seconds':time.perf_counter()-started}
        (ROOT/'damping_sensitivity_results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
        print(json.dumps({'zeta1':zeta1,
            'route_a_RMS':{k:v['RMS_target_state_error'] for k,v in route_a.items()},
            'route_b_RMS':{k:v['RMS_state_error_independent_reference'] for k,v in route_b.items()},
            'elapsed_seconds':case['elapsed_seconds']},ensure_ascii=False),flush=True)
    print('All damping scenarios completed.',flush=True)


if __name__=='__main__':
    main()
