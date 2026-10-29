"""Validate cross-file provenance and collect reviewable control diagnostics."""
from pathlib import Path
import hashlib
import json
import math
import numpy as np

ROOT = Path(__file__).resolve().parent


def main():
    a=json.loads((ROOT/'minimal_control_results.json').read_text())
    b=json.loads((ROOT/'route_b_shared_results.json').read_text())
    s=json.loads((ROOT/'damping_sensitivity_results.json').read_text())
    assert a['status']==b['status']=='all assertions passed'
    assert s['status']=='all scenarios completed'
    current_hash=hashlib.sha256((ROOT.parent/'new_baseline.json').read_bytes()).hexdigest()
    run_hashes=[x['new_baseline_provenance']['parameter_sha256'] for x in (a,b,s)]
    current=json.loads((ROOT.parent/'new_baseline.json').read_text())
    reduced=current['reduced']
    for output_key,source_key in [('nu','nu'),('d','d'),('ell_m','ell_m'),
                                 ('omega0_rad_s','omega0_rad_s'),('E0_J','E0_J'),
                                 ('dipole_A_m2','mu_A_m2'),('B0_T','B0_T')]:
        assert np.array_equal(np.asarray(a['parameters'][output_key]),np.asarray(reduced[source_key]))
    assert a['parameters']==b['parameters']
    annotation_update=None
    if any(h!=current_hash for h in run_hashes):
        record_path=ROOT.parent/'source_annotation_update.json'
        annotation_update=json.loads(record_path.read_text())
        assert annotation_update['new_file_sha256']==current_hash
        assert all(h==annotation_update['old_file_sha256'] for h in run_hashes)
        for section,digest in annotation_update['unchanged_canonical_section_sha256'].items():
            actual=hashlib.sha256(json.dumps(current[section],sort_keys=True,separators=(',',':')).encode()).hexdigest()
            assert actual==digest
    assert a['identification']['train_initials']==b['shared_identification']['training_initials']==s['training_initials']
    assert a['identification']['validation_initials']==b['shared_identification']['validation_initials']==s['validation_initials']
    assert np.max(np.abs(b['shared_identification']['difference_from_route_a_fit']))<1e-13
    def compact_a(x):
        return {k:x[k] for k in ['RMS_target_state_error','maximum_abs_tip_angle_rad',
                                'physical_target_errors','input_domain','state_domain']}
    def compact_b(x):
        keys=['RMS_state_error_independent_reference','second_half_RMS_state_error_independent_reference',
              'second_half_RMS_state_error_synchronous_reference','final_state_error_synchronous_reference',
              'physical_errors_independent_reference','input_domain','state_domain']
        return {k:x[k] for k in keys}
    input_reports=[]
    domain_reports=[]
    scenario_rows=[]
    for rows in [a['comparison']['groups'],b['tracking']['groups']]:
        for x in rows.values():
            input_reports.append(x['input_domain']); domain_reports.append(x['state_domain'])
    for key in ['training_trajectory_domains','validation_trajectory_domains']:
        domain_reports.extend(a['identification'][key])
    for case in s['scenarios']:
        assert abs(case['gamma_true']-2*case['zeta1_scenario'])<1e-15
        assert abs(case['alpha_s_inv']-case['gamma_true']*a['parameters']['omega0_rad_s'])<1e-14
        for key in ['training_trajectory_domains','validation_trajectory_domains']:
            domain_reports.extend(case['identification'][key])
        for key in ['route_a','route_b']:
            for x in case[key].values():
                input_reports.append(x['input_domain']); domain_reports.append(x['state_domain'])
        scenario_rows.append({
            'zeta1':case['zeta1_scenario'],'gamma':case['gamma_true'],'alpha_s_inv':case['alpha_s_inv'],
            'beta_hat':case['identification']['beta_hat'],'gamma_hat':case['identification']['gamma_hat'],
            'lambda_min_normalized_Gram':case['identification']['lambda_min_normalized_Gram'],
            'route_a_RMS':{k:v['RMS_target_state_error'] for k,v in case['route_a'].items()},
            'route_b_RMS_independent':{k:v['RMS_state_error_independent_reference'] for k,v in case['route_b'].items()},
            'route_b_second_half_RMS_independent':{k:v['second_half_RMS_state_error_independent_reference'] for k,v in case['route_b'].items()},
            'route_b_second_half_RMS_synchronous':{k:v['second_half_RMS_state_error_synchronous_reference'] for k,v in case['route_b'].items()},
            'route_a_learned_inputs':case['route_a']['learned']['input_domain'],
            'route_b_learned_inputs':case['route_b']['learned_tracking']['input_domain'],
        })
    for x in input_reports:
        assert abs(x['maximum_total_local_field_T']-math.hypot(a['parameters']['B0_T'],x['maximum_abs_By_T']))<1e-14
        assert x['maximum_input_reconstruction_error']<1e-12
    output={
        'scope':'Reviewed new-baseline minimal synthetic route-A/B tests; not a full CHNN benchmark or KAM certificate.',
        'all_cross_file_checks_passed':True,
        'parameter_sha256':current_hash,
        'parameter_sha256_at_actual_runs':dict(zip(['route_a','route_b','damping_sensitivity'],run_hashes)),
        'post_run_source_annotation_update':annotation_update,
        'parameters':a['parameters'],
        'identification':{
            'beta_hat':a['identification']['beta_hat'],'gamma_hat':a['identification']['gamma_hat'],
            'A_B_fit_difference':b['shared_identification']['difference_from_route_a_fit'],
            'training_RMSE':a['identification']['training_RMSE'],
            'validation_RMSE':a['identification']['validation_RMSE'],
            'lambda_min_normalized_Gram':b['shared_identification']['lambda_min_normalized_Gram'],
            'raw_design_condition2':b['shared_identification']['raw_design_condition2'],
            'column_scaled_design_condition2':b['shared_identification']['column_scaled_design_condition2'],
            'independent_rigorous_epsilonI_available':False,
        },
        'main_duration_tau':20.,'main_duration_seconds':a['comparison']['duration_seconds'],
        'main_midpoint_step_tau':.001,
        'route_a':{k:compact_a(v) for k,v in a['comparison']['groups'].items()},
        'route_b_prediction':b['prediction'],
        'route_b':{k:compact_b(v) for k,v in b['tracking']['groups'].items()},
        'damping_scenarios':scenario_rows,
        'all_run_domain_maxima':{
            'maximum_abs_tip_angle_rad':max(x['maximum_abs_tip_angle_rad'] for x in domain_reports),
            'maximum_abs_tip_angle_deg':math.degrees(max(x['maximum_abs_tip_angle_rad'] for x in domain_reports)),
            'maximum_abs_beam_slope_spatial_grid':max(x['maximum_abs_beam_slope_spatial_grid'] for x in domain_reports),
            'minimum_abs_cos_tip_angle':min(x['minimum_abs_cos_tip_angle'] for x in domain_reports),
            'maximum_abs_By_T':max(x['maximum_abs_By_T'] for x in input_reports),
            'maximum_total_local_field_T':max(x['maximum_total_local_field_T'] for x in input_reports),
            'maximum_local_gradient_spectral2_T_per_m':max(x['maximum_local_gradient_spectral2_T_per_m'] for x in input_reports),
            'maximum_input_reconstruction_error':max(x['maximum_input_reconstruction_error'] for x in input_reports),
            'status':'sampled time trajectories; 257 spatial grid points; all endpoints and actual integration midpoints for command diagnostics',
        },
        'verification':{
            'A_RK4_reference_refinement_maximum':a['reference_validation']['maximum_refinement_state_difference'],
            'A_final_observed_midpoint_order':a['oracle_midpoint_convergence'][-1]['observed_order'],
            'B_RK4_reference_refinement_maximum':b['numerical_checks']['reference_RK4_maximum_difference'],
            'B_oracle_linear_Cayley_defect':b['numerical_checks']['oracle_linear_error_Cayley_comparison_maximum'],
            'B_reference_midpoint_error_ratio_halving_step':b['numerical_checks']['reference_midpoint_error_ratio_on_halving_step'],
        },
        'interpretation_limits':[
            'beta=0.2 and all damping ratios are declared artificial scenarios, not measured physical values.',
            'E and density are approximate literature reference values; core size and geometry are design inputs.',
            'Every damping case refits the noiseless synthetic observations; this does not establish robustness to unknown damping, noise, or unmodeled features.',
            'At zero true damping, the unchanged unconstrained least-squares fit can return a minute negative gamma from numerical error; do not report this as negative measured material damping.',
            'Comparable learned/oracle errors are dominated by common midpoint phase error; a slightly smaller learned number is not superior control.',
            'Independent and synchronous references must remain distinct; the final synchronous tracking error cannot substitute for error to the continuous reference.',
            'Commands are local ideal field/gradient demands only, not tested coils, actuators or operating limits.',
            'No energy governor or saturation is implemented. Sampled displacement below a comparison clearance is not proof of an energy-cap safety condition.',
            'Old frozen KAM quantities are not transferable. These computations do not provide a new analytic-domain error bound, remainder threshold or KAM certificate.',
        ],
    }
    (ROOT/'control_audit_summary.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
    print(json.dumps({'status':'summary checks passed',
                      'domain_maxima':output['all_run_domain_maxima'],
                      'scenario_count':len(scenario_rows)},indent=2))


if __name__=='__main__':
    main()
