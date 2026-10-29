"""Route B: recompute the shared fit, learned prediction and reference tracking.

Requires NumPy and the adjacent, unchanged minimal_control_loop.py. Writes only
route_b_shared_results.json. This is a noiseless synthetic two-parameter test,
not a KAM certificate, general CHNN benchmark or hardware experiment.
"""
from pathlib import Path
import importlib.util
import json
import sys
import time
import numpy as np
from baseline_config import scaled, provenance, state_domain, input_domain, physical_error_metrics

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('route_a_shared', ROOT/'minimal_control_loop.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
NINV = np.diag(1/A.NU)
I2, Z2 = np.eye(2), np.zeros((2, 2))
KP, KD = 1., 2.
TRAIN = scaled([[.18,.14,.05,-.04],[-.15,.20,.02,.05],[.22,-.12,-.03,.06],[.10,.24,.04,-.02]])
VALIDATION = scaled([[-.19,.11,.06,.01],[.13,-.21,-.04,.03]])


def grad(z, beta):
    return A.NU*z[:2] + (1+beta)*A.magnetic(z)


def hessian(z, beta):
    return A.N + (1+beta)*(np.cos(A.D@z[:2])-1)*np.outer(A.D,A.D)


def learned_control(z, ref, beta_hat, gamma_hat):
    # Only fitted parameters and observed/reference states enter this controller.
    ex, ey = z[:2]-ref[:2], z[2:]-ref[2:]
    return gamma_hat*z[2:] + grad(z,beta_hat)-grad(ref,beta_hat)-KP*NINV@ex-KD*ey


def oracle_control(z, ref, beta_hat):
    # Explicit privileged-model benchmark; the reference remains the learned one.
    ex, ey = z[:2]-ref[:2], z[2:]-ref[2:]
    return A.GAMMA*z[2:] + grad(z,A.BETA)-grad(ref,beta_hat)-KP*NINV@ex-KD*ey


def command(name, z, ref, bhat, ghat):
    if name=='passive': return np.zeros(2)
    if name=='damping_only': return ghat*z[2:]
    if name=='learned_tracking': return learned_control(z,ref,bhat,ghat)
    if name=='oracle_tracking': return oracle_control(z,ref,bhat)
    raise ValueError(name)


def augmented_field(state, name, bhat, ghat):
    z,ref=state[:4],state[4:]
    requested=command(name,z,ref,bhat,ghat)
    applied=A.physical_ports(z,requested)[0]
    plant=A.field(z)+np.r_[np.zeros(2),applied]
    reference=A.field(ref,bhat,0.)
    return np.r_[plant,reference]


def augmented_jacobian(state, name, bhat, ghat):
    z,ref=state[:4],state[4:]
    htrue,hhatref=hessian(z,A.BETA),hessian(ref,bhat)
    plant_x=-htrue; plant_y=-A.GAMMA*I2
    cross=np.zeros((4,4))
    if name=='damping_only':
        plant_y=-(A.GAMMA-ghat)*I2
    elif name in ('learned_tracking','oracle_tracking'):
        beta_used=bhat if name=='learned_tracking' else A.BETA
        gamma_used=ghat if name=='learned_tracking' else A.GAMMA
        plant_x=-htrue+hessian(z,beta_used)-KP*NINV
        plant_y=-(A.GAMMA-gamma_used+KD)*I2
        cross[2:,:2]=-hhatref+KP*NINV
        cross[2:,2:]=KD*I2
    plant=np.block([[Z2,A.N],[plant_x,plant_y]])
    reference=np.block([[Z2,A.N],[-hhatref,Z2]])
    return np.block([[plant,cross],[np.zeros((4,4)),reference]])


def integrate_midpoint(initial, duration, dt, name, bhat, ghat):
    steps=int(round(duration/dt)); states=np.empty((steps+1,8)); states[0]=initial
    max_residual=0.; max_iterations=0; identity=np.eye(8)
    for i in range(steps):
        old=states[i]; new=old+dt*augmented_field(old,name,bhat,ghat)
        for it in range(12):
            mid=(old+new)/2
            residual=new-old-dt*augmented_field(mid,name,bhat,ghat)
            rn=float(np.linalg.norm(residual,np.inf))
            if rn<=2e-14: break
            new-=np.linalg.solve(identity-dt/2*augmented_jacobian(mid,name,bhat,ghat),residual)
        else: raise RuntimeError('Augmented midpoint Newton failed')
        states[i+1]=new; max_residual=max(max_residual,rn); max_iterations=max(max_iterations,it)
    return states,{'maximum_Newton_increment_residual_inf':max_residual,'maximum_Newton_corrections':max_iterations}


def rms(values):
    return float(np.sqrt(np.mean(np.sum(values*values,axis=1))))


def tracking_metrics(states, independent_ref, name, bhat, ghat, dt):
    z,ref=states[:,:4],states[:,4:]
    errors=z-independent_ref; synchronous=z-ref; half=(len(z)-1)//2
    ports=[]; forces=[]; powers=[]; reconstruction=[]; equation=[]
    for state in states:
        zz,rr=state[:4],state[4:]
        u=command(name,zz,rr,bhat,ghat)
        applied,force,torque,by,g=A.physical_ports(zz,u)
        ports.append([abs(by),np.linalg.norm(g,2),np.linalg.norm(u)])
        reconstruction.append([np.linalg.norm(applied-u),np.linalg.norm(A.LAMBDA*(applied-u))])
        if name in ('learned_tracking','oracle_tracking'):
            effective_db=A.BETA-bhat if name=='learned_tracking' else 0.
            effective_dg=A.GAMMA-ghat if name=='learned_tracking' else 0.
            forcing=-A.NU*(effective_db*A.magnetic(zz)+effective_dg*zz[2:])
            ff=augmented_field(state,name,bhat,ghat)
            identity=A.NU*(ff[2:4]-ff[6:8])+KD*A.NU*(zz[2:]-rr[2:])+KP*(zz[:2]-rr[:2])
            equation.append(np.linalg.norm(identity-forcing)); forces.append(np.linalg.norm(forcing))
    ports=np.array(ports); reconstruction=np.array(reconstruction)
    effort=ports[:,2]**2
    return {'RMS_state_error_independent_reference':rms(errors),
            'second_half_RMS_state_error_independent_reference':rms(errors[half:]),
            'initial_state_error':float(np.linalg.norm(errors[0])),
            'final_state_error_independent_reference':float(np.linalg.norm(errors[-1])),
            'RMS_state_error_synchronous_midpoint_reference':rms(synchronous),
            'second_half_RMS_state_error_synchronous_reference':rms(synchronous[half:]),
            'final_state_error_synchronous_reference':float(np.linalg.norm(synchronous[-1])),
            'maximum_reference_midpoint_error_vs_RK4':float(np.max(np.linalg.norm(ref-independent_ref,axis=1))),
            'peak_abs_By_T':float(np.max(ports[:,0])),'peak_gradient_spectral2_T_per_m':float(np.max(ports[:,1])),
            'RMS_control_norm':float(np.sqrt(np.mean(effort))),
            'integral_control_norm_squared':float(dt*(.5*effort[0]+effort[1:-1].sum()+.5*effort[-1])),
            'maximum_input_reconstruction_error':float(np.max(reconstruction[:,0])),
            'maximum_Lambda_U_reconstruction_error':float(np.max(reconstruction[:,1])),
            'maximum_tracking_equation_identity_defect':float(max(equation)) if equation else None,
            'maximum_residual_forcing_norm':float(max(forces)) if forces else None,
            'RMS_residual_forcing_norm':float(np.sqrt(np.mean(np.array(forces)**2))) if forces else None,
            'physical_errors_independent_reference':physical_error_metrics(errors,A),
            'physical_errors_synchronous_reference':physical_error_metrics(synchronous,A),
            'state_domain':state_domain(z,A),
            'reference_state_domain':state_domain(ref,A),
            'input_domain':input_domain(states,A,lambda st:command(name,st[:4],st[4:],bhat,ghat))}


def main():
    started=time.perf_counter()
    previous=json.loads((ROOT/'minimal_control_results.json').read_text(encoding='utf-8'))
    # Actual regeneration: do not copy a stored fit or use test trajectories.
    design,labels=A.identification_rows(TRAIN)
    validation_design,validation_labels=A.identification_rows(VALIDATION)
    scales=np.linalg.norm(design,axis=0)
    fitted=np.linalg.lstsq(design/scales,labels,rcond=None)[0]/scales
    bhat,ghat=map(float,fitted)
    previous_fit=np.array([previous['identification']['beta_hat'],previous['identification']['gamma_hat']])
    assert np.max(np.abs(fitted-previous_fit))<1e-13
    assert TRAIN==previous['identification']['train_initials'] and VALIDATION==previous['identification']['validation_initials']
    denominator=len(labels)  # 2L=800 scalar observations for L=400 two-vector windows.
    gram=design.T@design/denominator
    lambda_min=float(np.linalg.eigvalsh(gram)[0]); assert lambda_min>0
    residual=rms((design@fitted-labels)[:,None])
    true_parameters=np.array([A.BETA,A.GAMMA])
    epsilon_truth_diagnostic=rms((design@true_parameters-labels)[:,None])
    bound_diagnostic=(residual+epsilon_truth_diagnostic)/np.sqrt(lambda_min)
    true_coefficient_error=float(np.linalg.norm(fitted-true_parameters))
    assert true_coefficient_error<=bound_diagnostic*(1+1e-10)
    print('Shared fit recomputed:',fitted,flush=True)
    ref0=np.array(scaled([.18,.16,.03,-.02])); perturbation=np.array(scaled([.009,.008,0.,0.]))
    duration=20.; dt=.001; init=np.r_[ref0+perturbation,ref0]
    ref_coarse=A.rk4(lambda z:A.field(z,bhat,0.),ref0,duration,.0005)
    ref_fine=A.rk4(lambda z:A.field(z,bhat,0.),ref0,duration,.00025)
    reference_refinement=float(np.max(np.linalg.norm(ref_coarse-ref_fine[::2],axis=1)))
    assert reference_refinement<1e-8
    true_flow=A.rk4(lambda z:A.field(z,A.BETA,0.),ref0,duration,.00025)
    nominal_flow=A.rk4(lambda z:A.field(z,0.,0.),ref0,duration,.00025)
    true_flow_coarse=A.rk4(lambda z:A.field(z,A.BETA,0.),ref0,duration,.0005)
    true_refinement=float(np.max(np.linalg.norm(true_flow_coarse-true_flow[::2],axis=1)))
    prediction={'initial_state':ref0.tolist(),'duration_tau':duration,'RK4_step':.00025,
                'nominal_h0_RMS_state_error_vs_hstar':rms(nominal_flow-true_flow),
                'learned_hhat_RMS_state_error_vs_hstar':rms(ref_fine-true_flow),
                'nominal_h0_final_error_vs_hstar':float(np.linalg.norm(nominal_flow[-1]-true_flow[-1])),
                'learned_hhat_final_error_vs_hstar':float(np.linalg.norm(ref_fine[-1]-true_flow[-1])),
                'hstar_reference_refinement_maximum':true_refinement,
                'hhat_reference_refinement_maximum':reference_refinement}
    assert prediction['learned_hhat_RMS_state_error_vs_hstar']<prediction['nominal_h0_RMS_state_error_vs_hstar']
    target=ref_fine[::4]; reports={}; learned_states=None; reference_states=None
    for name in ('passive','damping_only','learned_tracking','oracle_tracking'):
        states,solver=integrate_midpoint(init,duration,dt,name,bhat,ghat)
        reports[name]={**tracking_metrics(states,target,name,bhat,ghat,dt),**solver}
        if name=='learned_tracking': learned_states=states
        if reference_states is None: reference_states=states[:,4:]
        else: assert np.max(np.abs(states[:,4:]-reference_states))<1e-12
        print(name,reports[name]['RMS_state_error_independent_reference'],reports[name]['second_half_RMS_state_error_independent_reference'],flush=True)
    assert reports['learned_tracking']['RMS_state_error_independent_reference']<reports['damping_only']['RMS_state_error_independent_reference']
    for name,row in reports.items():
        assert row['maximum_input_reconstruction_error']<1e-12
        if row['maximum_tracking_equation_identity_defect'] is not None:
            assert row['maximum_tracking_equation_identity_defect']<1e-12
    # The final group is the oracle: its four-dimensional error system is linear.
    oracle_error=states[:,:4]-states[:,4:]
    error_matrix=np.block([[Z2,A.N],[-KP*NINV,-KD*I2]])
    error_cayley=np.linalg.solve(np.eye(4)-dt*error_matrix/2,np.eye(4)+dt*error_matrix/2)
    linear_error=np.empty_like(oracle_error); linear_error[0]=oracle_error[0]
    for i in range(len(linear_error)-1): linear_error[i+1]=error_cayley@linear_error[i]
    oracle_cayley_defect=float(np.max(np.linalg.norm(oracle_error-linear_error,axis=1)))
    assert oracle_cayley_defect<1e-12
    times=np.arange(len(linear_error))*dt
    ex0=oracle_error[0,:2]
    continuous_error=np.column_stack(((1+times[:,None])*np.exp(-times[:,None])*ex0,
                                      -times[:,None]*np.exp(-times[:,None])*(ex0/A.NU)))
    linear_discretization_error=float(np.max(np.linalg.norm(linear_error-continuous_error,axis=1)))
    refined,refined_solver=integrate_midpoint(init,duration,dt/2,'learned_tracking',bhat,ghat)
    refined_metrics=tracking_metrics(refined,ref_fine[::2],'learned_tracking',bhat,ghat,dt/2)
    actual_refinement=float(np.max(np.linalg.norm(learned_states[:,:4]-refined[::2,:4],axis=1)))
    ratio=reports['learned_tracking']['maximum_reference_midpoint_error_vs_RK4']/refined_metrics['maximum_reference_midpoint_error_vs_RK4']
    assert 3.9<ratio<4.1
    # Verify the analytic 8x8 Newton derivative separately by centered differences.
    test=init+.001*np.arange(8); eps=1e-6
    numerical=np.column_stack([(augmented_field(test+eps*np.eye(8)[i],'learned_tracking',bhat,ghat)-augmented_field(test-eps*np.eye(8)[i],'learned_tracking',bhat,ghat))/(2*eps) for i in range(8)])
    jacobian_defect=float(np.max(np.abs(numerical-augmented_jacobian(test,'learned_tracking',bhat,ghat))))
    assert jacobian_defect<1e-7
    d1,d2=A.D; kappa_star=1+A.BETA
    twist=-kappa_star*np.array([[d1**4/8,d1*d1*d2*d2/4],[d1*d1*d2*d2/4,d2**4/8]])
    result={'scope':'Route B on the newly regenerated identical noiseless six-trajectory synthetic data used by new-baseline route A; no KAM certificate or hardware claim.',
            'new_baseline_provenance':provenance(),
            'parameters':previous['parameters'],
            'shared_identification':{'regenerated_not_copied':True,'training_initials':TRAIN,'validation_initials':VALIDATION,
                'training_trajectory_domains':A.IDENTIFICATION_DOMAINS[:len(TRAIN)],
                'validation_trajectory_domains':A.IDENTIFICATION_DOMAINS[len(TRAIN):len(TRAIN)+len(VALIDATION)],
                'duration_each_tau':4.,'data_RK4_step':.0005,'observation_step':.002,'window_length':.04,
                'training_windows_L':denominator//2,'training_scalar_rows_2L':denominator,'validation_scalar_rows':len(validation_labels),
                'beta_hat':bhat,'gamma_hat':ghat,'difference_from_route_a_fit':(fitted-previous_fit).tolist(),
                'training_rI_RMSE':residual,'validation_RMSE':rms((validation_design@fitted-validation_labels)[:,None]),
                'normalized_joint_Gram_AtransA_over_2L':gram.tolist(),'lambda_min_normalized_Gram':lambda_min,
                'raw_design_condition2':float(np.linalg.cond(design)),'column_scaled_design_condition2':float(np.linalg.cond(design/scales)),
                'coefficient_bound_multiplier_1_over_sqrt_lambda_min':float(1/np.sqrt(lambda_min)),
                'conditional_bound_formula':'||theta_hat-theta_star||_2 <= (rI + epsilonI)/sqrt(lambda_min(G)); G=A^T A/(2L)',
                'independent_rigorous_epsilonI_available':False,
                'epsilonI_using_synthetic_truth_diagnostic_only':epsilon_truth_diagnostic,
                'coefficient_bound_expression_using_truth_diagnostic_only':float(bound_diagnostic),
                'actual_coefficient_error_using_synthetic_truth':true_coefficient_error,
                'warning':'Known synthetic truth yields an a posteriori numerical diagnostic, not an independent interval/quadrature bound or KAM certificate.',
                'test_data_used_for_fit':False},
            'prediction':prediction,
            'tracking':{'frozen_reference':'conservative hhat=h0+beta_hat*g',
                'actual_plant':'hstar=h0+0.2*g with gamma_true damping',
                'reference_initial_state':ref0.tolist(),'actual_initial_state':(ref0+perturbation).tolist(),
                'artificial_initial_state_offset':perturbation.tolist(),'offset_origin':'5% of each reference position coordinate; no momentum offset; synthetic design only',
                'omega_c':1.,'zeta':1.,'kappa_p':KP,'kappa_d':KD,'gain_origin':'omega_c=nu1=1, zeta=1 critical damping in the ideal error equation',
                'duration_tau':duration,'duration_seconds':duration/A.OMEGA0,'step_tau':dt,'samples_per_group':len(target),
                'controller_reads_true_beta':{'passive':False,'damping_only':False,'learned_tracking':False,'oracle_tracking':True},
                'same_frozen_midpoint_reference_all_groups':True,'all_inputs_pass_through_shared_magnetic_ports':True,
                'RMS_definition':'sqrt(mean_k ||actual_k-reference_k||_2^2); no extra division by four coordinates',
                'second_half_definition':'tau in [10,20], including both endpoints',
                'groups':reports},
            'numerical_checks':{'reference_RK4_steps':[.0005,.00025],'reference_RK4_maximum_difference':reference_refinement,
                'oracle_linear_error_Cayley_comparison_maximum':oracle_cayley_defect,
                'oracle_linear_error_Cayley_vs_continuous_exact_maximum':linear_discretization_error,
                'oracle_continuous_error_formula':'eX=(1+tau)*exp(-tau)*eX0; eY=-tau*exp(-tau)*N^-1*eX0',
                'learned_tracking_midpoint_steps':[dt,dt/2],'maximum_actual_state_difference_at_common_times':actual_refinement,
                'reference_midpoint_error_ratio_on_halving_step':float(ratio),
                'learned_tracking_refined_metrics':refined_metrics,'learned_tracking_refined_solver':refined_solver,
                'analytic_augmented_Jacobian_finite_difference_maximum_error':jacobian_defect},
            'twist_diagnostic':{'kappa_star':kappa_star,'A_star_fourth_order':twist.tolist(),
                'determinant':float(np.linalg.det(twist)),'singular_values':np.linalg.svd(twist,compute_uv=False).tolist(),
                'scope':'Fourth-order normal-form twist at the origin only; finite-domain remainder and KAM threshold unverified.'},
            'limits':['PD tracking is dissipative and nonautonomous through a frozen reference. No symplectic or KAM claim is made for this tracking loop.',
                'hhat is a learned predictive target; it differs from route A nominal h0 target. Both use the same true plant and shared fitted coefficients.',
                'Reference and actual state are integrated as an augmented eight-dimensional midpoint system. Independent RK4 comparisons expose its phase error.',
                'No sensor noise, clipping, actuator calibration, higher modes, or finite-domain analytic KAM error certification is included.',
                'Only the oracle benchmark reads true beta and gamma in its controller; plant simulation and diagnostic checks necessarily know the synthetic truth.'],
            'elapsed_seconds':time.perf_counter()-started,'status':'all assertions passed'}
    (ROOT/'route_b_shared_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'prediction':prediction,'elapsed_seconds':result['elapsed_seconds']},indent=2),flush=True)


if __name__=='__main__':
    main()
