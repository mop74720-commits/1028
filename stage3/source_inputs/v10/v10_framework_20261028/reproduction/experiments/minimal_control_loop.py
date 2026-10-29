"""Reproducible two-mode synthetic control closure; requires NumPy only.

Run: python minimal_control_loop.py
Outputs: minimal_control_results.json and minimal_control_loop.svg.
This is NOT physical identification, hardware validation, CHNN training or KAM
certification. beta=0.2 is an explicitly artificial model-error stress test.
The coupled nominal magnetic potential V0 is retained as the control target.
"""
from pathlib import Path
import json
import time
from types import SimpleNamespace
import numpy as np
from baseline_config import REDUCED, scaled, provenance, state_domain, input_domain, physical_error_metrics

ROOT = Path(__file__).resolve().parent
NU = np.asarray(REDUCED['nu'], dtype=float)
N = np.diag(NU)
D = np.asarray(REDUCED['d'], dtype=float)
ELL = np.asarray(REDUCED['ell_m'], dtype=float)
OMEGA0 = float(REDUCED['omega0_rad_s'])
ALPHA = 0.05 * OMEGA0  # explicit zeta1=0.025 damping scenario
GAMMA = ALPHA / OMEGA0
BETA = 0.2  # artificial model-error stress test, not measured
E0 = float(REDUCED['E0_J'])
MU = float(REDUCED['mu_A_m2'])
B0 = float(REDUCED['B0_T'])
IDENTIFICATION_DOMAINS = []
DS = np.sqrt(E0 / (OMEGA0**2 * NU))
LAMBDA = E0 / DS
TIP_B, TIP_T = ELL / DS, D / DS
AMAG = np.column_stack((TIP_B, TIP_T))
J = np.block([[np.zeros((2, 2)), np.eye(2)], [-np.eye(2), np.zeros((2, 2))]])


def magnetic(z):
    theta = D @ z[:2]
    return D * (np.sin(theta) - theta)


def h0(z):
    theta = z[..., :2] @ D
    return .5 * np.sum(NU * (z[..., :2]**2 + z[..., 2:]**2), axis=-1) + 1 - np.cos(theta) - .5 * theta**2


def field(z, beta=BETA, gamma=GAMMA):
    return np.r_[NU*z[2:], -NU*z[:2] - (1+beta)*magnetic(z) - gamma*z[2:]]


def rk4(fun, initial, duration, step):
    count = int(round(duration/step))
    assert abs(count*step-duration) < 1e-12
    states = np.empty((count+1, len(initial)))
    states[0] = initial
    for i in range(count):
        z = states[i]
        k1 = fun(z); k2 = fun(z+.5*step*k1)
        k3 = fun(z+.5*step*k2); k4 = fun(z+step*k3)
        states[i+1] = z + step*(k1+2*k2+2*k3+k4)/6
    return states


def simpson(values, step):
    assert (len(values)-1) % 2 == 0
    return step/3 * (values[0] + values[-1] + 4*values[1:-1:2].sum(axis=0) + 2*values[2:-1:2].sum(axis=0))


def identification_rows(initials):
    rows, labels = [], []
    dt, obs_dt, window = .0005, .002, .04
    for initial in initials:
        trajectory = rk4(field, np.array(initial), 4., dt)
        IDENTIFICATION_DOMAINS.append(state_domain(trajectory, audit_model()))
        states = trajectory[::int(round(obs_dt/dt))]
        width = int(round(window/obs_dt))
        for left in range(0, len(states)-width, width):
            s = states[left:left+width+1]
            theta = s[:, :2] @ D
            dg = (np.sin(theta)-theta)[:, None] * D
            vgrad = s[:, :2]*NU + dg
            a = np.column_stack((-simpson(dg, obs_dt), -simpson(s[:, 2:], obs_dt)))
            b = s[-1, 2:]-s[0, 2:] + simpson(vgrad, obs_dt)
            rows.extend(a); labels.extend(b)
    return np.array(rows), np.array(labels)


def physical_ports(z, control):
    theta = D @ z[:2]
    cosine, sine = np.cos(theta), np.sin(theta)
    assert abs(cosine) > .9, 'Port formula approached its angle singularity.'
    bias = E0*(theta-sine)
    force, torque = np.linalg.solve(AMAG, LAMBDA*control + TIP_T*bias)
    by = (torque-bias)/(MU*cosine)
    gradient = force/MU * np.array([[-sine, cosine], [cosine, sine]])
    dipole = MU*np.array([cosine, sine])
    applied_force = (gradient @ dipole)[1]
    applied_control = (TIP_B*applied_force + TIP_T*MU*by*cosine)/LAMBDA
    return applied_control, float(force), float(torque), float(by), gradient


def audit_model():
    return SimpleNamespace(D=D, ELL=ELL, MU=MU, B0=B0, physical_ports=physical_ports)


def closed_field(z, bhat, ghat):
    requested = ghat*z[2:] + bhat*magnetic(z)
    applied = physical_ports(z, requested)[0]
    return field(z) + np.r_[np.zeros(2), applied]


def closed_jacobian(z, bhat, ghat):
    hessian = N + (1+BETA-bhat)*(np.cos(D@z[:2])-1)*np.outer(D, D)
    return np.block([[np.zeros((2, 2)), N], [-hessian, (ghat-GAMMA)*np.eye(2)]])


def midpoint(initial, duration, step, bhat, ghat, measure_structure=False):
    count = int(round(duration/step)); states = np.empty((count+1, 4)); states[0] = initial
    residual_max = 0.; iterations_max = 0; structure_max = 0.
    for i in range(count):
        old = states[i]; new = old+step*closed_field(old, bhat, ghat)
        for iteration in range(12):
            mid = (old+new)/2
            residual = new-old-step*closed_field(mid, bhat, ghat)
            rn = np.linalg.norm(residual, np.inf)
            if rn <= 2e-14:
                break
            jac = np.eye(4)-step/2*closed_jacobian(mid, bhat, ghat)
            new -= np.linalg.solve(jac, residual)
        else:
            raise RuntimeError('Newton failed to converge')
        states[i+1] = new
        residual_max = max(residual_max, float(rn)); iterations_max = max(iterations_max, iteration)
        if measure_structure:
            a = step/2*closed_jacobian((old+new)/2, bhat, ghat)
            tangent = np.linalg.solve(np.eye(4)-a, np.eye(4)+a)
            structure_max = max(structure_max, float(np.linalg.norm(tangent.T@J@tangent-J, 2)))
    return states, {'maximum_Newton_residual_infinity_norm': residual_max,
                    'maximum_Newton_corrections': iterations_max,
                    'maximum_ideal_Cayley_symplectic_defect_spectral2': structure_max if measure_structure else None}


def metrics(states, target, step, bhat, ghat):
    errors = np.linalg.norm(states-target, axis=1)
    energies = h0(states)
    control = []; bys = []; gradients = []; forces = []; reconstruct = []; physical_reconstruct = []; vectorfield_errors = []
    for z in states:
        u = ghat*z[2:]+bhat*magnetic(z)
        applied, force, torque, by, grad = physical_ports(z, u)
        control.append(np.linalg.norm(u)); bys.append(abs(by)); forces.append(abs(force))
        gradients.append(np.linalg.norm(grad, 2)); reconstruct.append(np.linalg.norm(applied-u))
        physical_reconstruct.append(np.linalg.norm(LAMBDA*(applied-u)))
        vectorfield_errors.append(np.linalg.norm((bhat-BETA)*magnetic(z)+(ghat-GAMMA)*z[2:]))
    control = np.array(control)
    return {'RMS_target_state_error': float(np.sqrt(np.mean(errors**2))),
            'maximum_target_state_error': float(np.max(errors)),
            'endpoint_target_state_error': float(errors[-1]),
            'maximum_nominal_energy_drift': float(np.max(np.abs(energies-energies[0]))),
            'relative_maximum_nominal_energy_drift': float(np.max(np.abs(energies-energies[0]))/abs(energies[0])),
            'RMS_control_norm': float(np.sqrt(np.mean(control**2))),
            'integral_control_norm_squared': float(step*(.5*control[0]**2+np.sum(control[1:-1]**2)+.5*control[-1]**2)),
            'maximum_abs_By_T': float(max(bys)), 'maximum_gradient_spectral2_T_per_m': float(max(gradients)),
            'maximum_abs_tip_force_N': float(max(forces)),
            'maximum_input_reconstruction_error': float(max(reconstruct)),
            'maximum_Lambda_U_reconstruction_error': float(max(physical_reconstruct)),
            'RMS_continuous_vectorfield_mismatch_to_V0': float(np.sqrt(np.mean(np.array(vectorfield_errors)**2))),
            'maximum_abs_tip_angle_rad': float(np.max(np.abs(states[:, :2]@D))),
            'physical_target_errors': physical_error_metrics(states-target, audit_model()),
            'state_domain': state_domain(states, audit_model()),
            'input_domain': input_domain(states, audit_model(), lambda z: ghat*z[2:]+bhat*magnetic(z))}


def dimension_check():
    records=[]
    for n in (1,2,4):
        m=np.diag(1+np.arange(n)/5)+.12*np.ones((n,n)); k=np.diag(1+np.arange(n))+.05*np.ones((n,n))
        c=.2*m; mi=np.linalg.solve(m,np.eye(n)); step=.04
        z=np.arange(1,2*n+1)*.01; q,p=z[:n],z[n:]
        e=step**2/4*k@mi+step/2*c@mi
        pn=np.linalg.solve(np.eye(n)+e,(np.eye(n)-e)@p-step*k@q)
        qn=q+step/2*mi@(p+pn)
        a=np.block([[np.zeros((n,n)),mi],[-k,-c@mi]])
        full=np.linalg.solve(np.eye(2*n)-step*a/2,(np.eye(2*n)+step*a/2)@z)
        defect=float(np.linalg.norm(np.r_[qn,pn]-full))
        assert defect<1e-12
        records.append({'n':n,'mass_matrix_shape':[n,n],'phase_Jacobian_shape':[2*n,2*n],
                        'matrix_elimination_error_Euclidean':defect})
    return records


def svg_plot(path, curves, step):
    colors=['#666666','#dc7928','#2a8e83','#375b9d']
    ymin,ymax=-10,0
    chunks=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="450" viewBox="0 0 900 450">',
            '<rect width="900" height="450" fill="white"/>',
            '<text x="70" y="26" font-family="sans-serif" font-size="18">Synthetic two-mode closure: error to coupled V0 target</text>',
            '<path d="M70 50V370H860" fill="none" stroke="black"/>']
    for p in (-9,-7,-5,-3,-1):
        y=370-(p-ymin)/(ymax-ymin)*320
        chunks.append(f'<text x="15" y="{y+4}" font-family="sans-serif" font-size="12">1e{p}</text><path d="M70 {y}H860" stroke="#ddd"/>')
    for idx,(name,values) in enumerate(curves.items()):
        indices=np.unique(np.r_[np.arange(0,len(values),max(1,len(values)//1000)),len(values)-1])
        pts=' '.join(f'{70+790*i/(len(values)-1):.2f},{370-320*(np.clip(np.log10(max(values[i],1e-10)),ymin,ymax)-ymin)/(ymax-ymin):.2f}' for i in indices)
        chunks.append(f'<polyline points="{pts}" fill="none" stroke="{colors[idx]}" stroke-width="1.5"/>')
        chunks.append(f'<text x="{70+idx*205}" y="405" fill="{colors[idx]}" font-family="sans-serif" font-size="12">{name}</text>')
    chunks.append(f'<text x="380" y="438" font-family="sans-serif" font-size="12">dimensionless time tau: 0 to {(len(values)-1)*step:g}; logarithmic error axis</text></svg>')
    path.write_text('\n'.join(chunks),encoding='utf-8')


def main():
    started=time.perf_counter()
    train=scaled([[.18,.14,.05,-.04],[-.15,.20,.02,.05],[.22,-.12,-.03,.06],[.10,.24,.04,-.02]])
    validation=scaled([[-.19,.11,.06,.01],[.13,-.21,-.04,.03]])
    a,y=identification_rows(train); av,yv=identification_rows(validation)
    column_scale=np.linalg.norm(a,axis=0)
    coefficient_scaled=np.linalg.lstsq(a/column_scale,y,rcond=None)[0]
    bhat,ghat=coefficient_scaled/column_scale
    assert np.linalg.matrix_rank(a)==2 and abs(bhat-BETA)<.01 and abs(ghat-GAMMA)<1e-4
    print('Integral fit:',bhat,ghat,flush=True)
    initial=np.array(scaled([.18,.16,.03,-.02])); duration=20.; comparison_step=.001
    reference_coarse=rk4(lambda z:field(z,0.,0.),initial,duration,.0005)
    reference_fine=rk4(lambda z:field(z,0.,0.),initial,duration,.00025)
    reference_difference=float(np.max(np.linalg.norm(reference_coarse-reference_fine[::2],axis=1)))
    assert reference_difference<1e-7
    target=reference_fine[::4]
    groups={'passive':(0.,0.),'damping_only':(0.,float(ghat)),
            'learned':(float(bhat),float(ghat)),'oracle':(BETA,GAMMA)}
    reports,curves={},{}
    for name,(bb,gg) in groups.items():
        states,solver=midpoint(initial,duration,comparison_step,bb,gg,name=='oracle')
        reports[name]={'beta_hat':bb,'gamma_hat':gg,**metrics(states,target,comparison_step,bb,gg),**solver}
        curves[name]=np.linalg.norm(states-target,axis=1)
        print(name,reports[name]['RMS_target_state_error'],flush=True)
    convergence=[]
    for step in (.04,.02,.01,.005):
        states,solver=midpoint(initial,duration,step,BETA,GAMMA,True)
        corresponding=reference_fine[::int(round(step/.00025))]
        error=float(np.max(np.linalg.norm(states-corresponding,axis=1)))
        convergence.append({'step':step,'maximum_state_error':error,'endpoint_state_error':float(np.linalg.norm(states[-1]-reference_fine[-1])),
                            'observed_order':None if not convergence else float(np.log2(convergence[-1]['maximum_state_error']/error)),**solver})
    assert abs(convergence[-1]['observed_order']-2)<.05
    assert reports['oracle']['maximum_ideal_Cayley_symplectic_defect_spectral2']<1e-12
    assert max(v['maximum_input_reconstruction_error'] for v in reports.values())<1e-12
    assert reports['learned']['RMS_target_state_error']<reports['damping_only']['RMS_target_state_error']
    scaled_port=AMAG/np.linalg.norm(AMAG,axis=0)
    output={'scope':'New literature-based FE baseline, artificial two-mode model-error stress test; not robot/hardware identification, neural-network training or KAM certification.',
            'new_baseline_provenance':provenance(),
            'parameters':{'nu':NU.tolist(),'d':D.tolist(),'ell_m':ELL.tolist(),'omega0_rad_s':OMEGA0,'gamma_true':GAMMA,'alpha_s_inv_scenario':ALPHA,'zeta1_scenario':0.025,
                          'beta_artificial_true':BETA,'E0_J':E0,'dipole_A_m2':MU,'B0_T':B0,'Ds':DS.tolist(),
                          'mass_matrix_dimensionless':np.diag(1/NU).tolist(),'mass_matrix_note':'M_eff=N^-1 in (X,Y,tau); modal mass I2 applies before balanced scaling.'},
            'identification':{'method':'Two-scalar integral least squares; Simpson quadrature; exact state observations, nonzero numerical integration residual.',
                              'train_initials':train,'validation_initials':validation,'duration_each':4.,
                              'training_trajectory_domains':IDENTIFICATION_DOMAINS[:len(train)],
                              'validation_trajectory_domains':IDENTIFICATION_DOMAINS[len(train):len(train)+len(validation)],'generator_RK4_step':.0005,
                              'observation_step':.002,'window_length':.04,'observations_per_trajectory':2001,
                              'training_windows':len(y)//2,'validation_windows':len(yv)//2,'training_scalar_rows':len(y),'validation_scalar_rows':len(yv),
                              'columns_order':['beta','gamma'],'Gram_matrix':(a.T@a).tolist(),'raw_design_cond2':float(np.linalg.cond(a)),
                              'column_scaled_design_cond2':float(np.linalg.cond(a/column_scale)),
                              'beta_hat':float(bhat),'gamma_hat':float(ghat),
                              'training_RMSE':float(np.sqrt(np.mean((a@np.array([bhat,ghat])-y)**2))),
                              'validation_RMSE':float(np.sqrt(np.mean((av@np.array([bhat,ghat])-yv)**2))),
                              'test_data_used_for_fit':False,'noise':'none; measurement noise and generalization beyond this family are untested'},
            'dimension_checks':dimension_check(),
            'comparison':{'initial_state':initial.tolist(),'duration_tau':duration,'duration_seconds':duration/OMEGA0,
                          'step_tau':comparison_step,'samples_per_group':len(target),'groups':reports},
            'reference_validation':{'method':'Independent explicit RK4 for conservative V0; no implicit solver or controller used.',
                                    'coarse_step':.0005,'fine_step':.00025,'maximum_refinement_state_difference':reference_difference},
            'oracle_midpoint_convergence':convergence,
            'physical_interface':{'A_mag':AMAG.tolist(),'raw_condition_number_not_unit_invariant':float(np.linalg.cond(AMAG)),
                                  'column_normalized_condition_number':float(np.linalg.cond(scaled_port)),
                                  'Lambda_diagonal':LAMBDA.tolist(),'minimum_abs_cos_theta_observed':float(min(np.cos(v['maximum_abs_tip_angle_rad']) for v in reports.values())),
                                  'source':'new_baseline.json: recomputed FE with literature-based material and designed N50 magnet core; no old frozen mode coefficients.',
                                  'assumption':'Two independently commanded local field and gradient ports, exact sensing and no saturation; only algebraic realization checked.',
                                  'all_groups_simulate_reconstructed_physical_control':True},
            'interpretation':['V0 retains its cross-mode cosine coupling; no new separable target is introduced.',
                              'Only oracle damping cancellation supports the ideal standard-symplectic claim. gamma_hat differs from gamma_true.',
                              'Cayley defects test the ideal implicitly defined map evaluated at solved midpoints, not exact symplecticity of floating-point code.',
                              'Energy drift refers to h0; no expression is labeled an exact nonlinear action.',
                              'Control efficacy here is closeness to the same conservative reference, not tracking attraction or hardware safety.',
                              'Noiseless two-parameter fitting does not establish general CHNN learning performance.'],
            'elapsed_seconds':time.perf_counter()-started,'status':'all assertions passed'}
    (ROOT/'minimal_control_results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    svg_plot(ROOT/'minimal_control_loop.svg',curves,comparison_step)
    print(json.dumps({'status':output['status'],'elapsed_seconds':output['elapsed_seconds'],'reference_refinement':reference_difference,
                      'last_observed_order':convergence[-1]['observed_order']},indent=2),flush=True)


if __name__=='__main__':
    main()
