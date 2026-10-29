"""Independent frozen-output audit; no retraining or continuum/KAM certificate.

Reports the distinction between normalized input gradients and canonical
Hamiltonian vector fields, raw Ritz strain velocities, and finite-sample H_PP.
Only evaluation_summary.json files in the requested output folders are written.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import itertools
import json
import time
import numpy as np
import torch
from rod_rom import RodROM
import run_learning as revised


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative(error, truth):
    denominator=float(np.linalg.norm(truth))
    return float(np.linalg.norm(error)/denominator) if denominator else None


def grad_metrics(prediction, data, amplitude, scale, sq, omega0, energy_scale):
    true_x=data['g_res']+amplitude**2*data['x']
    error_x=prediction-data['g_res']
    true_z=true_x*scale
    error_z=error_x*scale
    n=len(scale)//2
    true_velocity=omega0*(true_z[:,n:]@sq.T)
    velocity_error=omega0*(error_z[:,n:]@sq.T)
    return {
        'normalized_x_gradient_relative_l2':relative(error_x,true_x),
        'normalized_x_residual_gradient_relative_l2':relative(error_x,data['g_res']),
        'canonical_z_gradient_and_tau_vector_field_relative_l2':relative(error_z,true_z),
        'canonical_tau_vector_field_component_rmse':float(np.sqrt(np.mean(error_z**2))),
        'physical_time_z_vector_field_component_rmse_per_s':float(omega0*np.sqrt(np.mean(error_z**2))),
        'raw_ritz_generalized_velocity_relative_l2':relative(velocity_error,true_velocity),
        'raw_ritz_generalized_velocity_component_rmse_per_s':float(np.sqrt(np.mean(velocity_error**2))),
        'true_raw_ritz_generalized_velocity_component_rms_per_s':float(np.sqrt(np.mean(true_velocity**2))),
        'true_raw_ritz_generalized_velocity_component_max_per_s':float(np.max(np.abs(true_velocity))),
        'normalization': 'x=D z, D=diag(sqrt(nu),sqrt(nu))/amplitude; grad_z=D grad_x; z_prime=J grad_z; dq_raw/dt=omega0 Sq grad_P h',
        'raw_velocity_scope':'12 Ritz curvature-amplitude rates, not pointwise centerline velocity, clinical measurement error, or closed-loop tracking error',
    }


def row_set(array):
    return {np.ascontiguousarray(row).tobytes() for row in array}


def split_checks(sets):
    rows={name:row_set(data['x']) for name,data in sets.items()}
    return {
        'duplicate_rows_within_split':{name:len(sets[name]['x'])-len(rows[name]) for name in sets},
        'exact_row_intersection_counts':{a+'__'+b:len(rows[a]&rows[b]) for a,b in itertools.combinations(sets,2)},
        'scope':'Exact row duplicates only. Does not undo adaptive model design after inspecting earlier test results.',
    }


def pole_diagnostics(net,x):
    def one(xb):
        xi=torch.complex(xb[:,:net.n],xb[:,net.n:])/np.sqrt(2)
        first=net.l1(torch.cat([xi,xi.conj()],1))
        second=net.l2(torch.tanh(first))
        return first,second
    result=[]
    with torch.no_grad():
        xx=torch.tensor(x)
        pairs=[one(xx),one(torch.cat([xx[:,:net.n],-xx[:,net.n:]],1))]
        for layer in range(2):
            values=torch.cat([a[layer].flatten() for a in pairs])
            nearest=np.pi*(torch.round(values.imag/np.pi-.5)+.5)
            distance=torch.sqrt(values.real**2+(values.imag-nearest)**2)
            tanh=torch.tanh(values)
            result.append({
                'layer':layer+1,
                'min_distance_to_complex_tanh_pole':float(distance.min()),
                'max_abs_tanh':float(torch.abs(tanh).max()),
                'max_abs_tanh_derivative':float(torch.abs(1-tanh*tanh).max()),
            })
    return result


def hpp_audit(model, module, net, coeff, x, amplitude, indices):
    scale=torch.sqrt(torch.cat([model.nu,model.nu]))/amplitude
    z=torch.tensor(x[indices])/scale
    n=model.n
    with torch.no_grad():
        rawq=z[:,:n]@model.Sq.T
        mass,_=model.mechanics(rawq)
        scaled=(model.omega0**2/model.E0)*(model.Sq.T@mass@model.Sq)
        true_hpp=torch.linalg.inv(scaled)
    minimum={'truth':torch.linalg.eigvalsh(true_hpp)[:,0].tolist(),
             'linear':[float(model.nu.min())]*len(indices),'analytic':[],'complex':[]}
    coeff_t=torch.tensor(coeff)
    for state in z:
        Q=state[:n].detach()
        for name in ['analytic','complex']:
            def energy(P):
                zz=torch.cat([Q,P])[None,:]
                xx=zz*scale
                if name=='analytic': residual=(module.polynomial_features(xx,n)*coeff_t).sum(-1)
                else: residual=net(xx)
                return (model.linear_energy(zz)+residual)[0]
            hessian=torch.autograd.functional.hessian(energy,state[n:]).detach()
            minimum[name].append(float(torch.linalg.eigvalsh(.5*(hessian+hessian.T))[0]))
    negative_cross_checks={}
    for name in ['analytic','complex']:
        worst=int(np.argmin(minimum[name]))
        if minimum[name][worst]>=0:continue
        state=z[worst];Q=state[:n].detach();P=state[n:].detach()
        def energy_direction(pp):
            zz=torch.cat([Q,pp])[None,:];xx=zz*scale
            if name=='analytic':residual=(module.polynomial_features(xx,n)*coeff_t).sum(-1)
            else:residual=net(xx)
            return (model.linear_energy(zz)+residual)[0]
        hessian=torch.autograd.functional.hessian(energy_direction,P).detach()
        eigenvalue,eigenvector=torch.linalg.eigh(.5*(hessian+hessian.T))
        direction=eigenvector[:,0]
        step=.001/float(torch.max(torch.abs(direction*scale[n:])))
        derivatives=[]
        with torch.no_grad():
            center=energy_direction(P)
            for eps in [step,step/2,step/4]:
                fd=(energy_direction(P+eps*direction)-2*center+energy_direction(P-eps*direction))/eps**2
                derivatives.append({'step_in_canonical_P':eps,'centered_second_difference':float(fd)})
        negative_cross_checks[name]={
            'original_split_index':int(indices[worst]),
            'autodiff_eigenvalue':float(eigenvalue[0]),
            'centered_energy_differences':derivatives,
            'scope':'A negative finite-difference curvature corroborates this sampled counterexample; it is not an interval arithmetic proof.',
        }
    return {
        'sample_indices':indices.tolist(),
        'sample_count':len(indices),
        'object':'canonical momentum Hessian H_PP of dimensionless energy at fixed Q',
        'minimum_eigenvalues_by_sample':minimum,
        'negative_curvature_cross_checks':negative_cross_checks,
        'summary':{name:{'minimum':min(vals),'maximum':max(vals),'nonpositive_sample_count':sum(v<=0 for v in vals)} for name,vals in minimum.items()},
        'limitation':'Finite floating-point samples. Positive samples do not prove global convexity, positive learned mass, or well-defined Legendre inversion throughout a domain.',
    }


def audit_feedforward(folder,model):
    root=folder/'feedforward'
    if not (root/'truth.npz').exists():return None
    truth_file=np.load(root/'truth.npz')
    required_truth=truth_file['force_required']
    weights=1/np.sqrt(model.nu.numpy())
    records={}
    for name in ['linear','analytic','complex','truth']:
        path=root/f'{name}.npz';data=np.load(path)
        forces=[]
        for start in range(0,len(required_truth),128):
            q=torch.tensor(data['q_raw_ref'][start:start+128],requires_grad=True)
            field=torch.tensor(data['u_ff'][start:start+128])
            _,potential=model.mechanics(q,field=field)
            _,bias_potential=model.mechanics(q)
            force=-torch.autograd.grad((potential-bias_potential).sum(),q)[0]@model.Sq/model.E0
            forces.append(force.detach().numpy())
        actual=np.concatenate(forces)
        own=np.linalg.norm((actual-data['force_required'])*weights,axis=1)
        common_error=(actual-required_truth)*weights
        model_error=(data['force_required']-required_truth)*weights
        u=data['u_ff'];time=data['time_s']
        G=np.array([[u[:,3],u[:,5],u[:,6]],[u[:,5],u[:,4],u[:,7]],[u[:,6],u[:,7],-u[:,3]-u[:,4]]]).transpose(2,0,1)
        gnorm=np.linalg.norm(G,axis=(1,2))
        workspace=np.linalg.norm(u[:,:3],axis=1)+model.config['magnet']['workspace_radius_m']*gnorm
        records[name]={
            'npz_sha256':sha(path),
            'own_residual_norm_max_difference_from_saved':float(np.max(np.abs(own-data['force_residual_norm']))),
            'common_truth_force_residual_relative_l2':relative(common_error,required_truth*weights),
            'common_truth_force_residual_rms':float(np.sqrt(np.mean(np.sum(common_error**2,axis=1)))),
            'required_force_model_error_relative_to_truth':relative(model_error,required_truth*weights),
            'max_gradient_frobenius_T_per_m':float(gnorm.max()),
            'max_workspace_field_bound_T':float(workspace.max()),
            'component_max_absolute_field_or_gradient_rate_per_s':np.max(np.abs(np.diff(u,axis=0)/np.diff(time)[:,None]),axis=0).tolist(),
            'fixed_bias_preserved':bool(np.array_equal(u[:,2],np.full(len(u),model.config['magnet']['bias_z_T']))),
            'max_reference_tip_z_shortening_m':float(np.max(data['target'][:,2]-data['tip_reference'][:,2])),
        }
    return {'method':'Independent force = -grad_Q[(V(q,B)-V(q,B_bias))/E0]; all methods compared with the same exact-ROM required force',
            'row_weights':'1/sqrt(nu)',
            'records':records,
            'scope':'Reference-trajectory local source-free fields; no calibrated coil currents, slew constraints, full-Cosserat tracking certification, or closed-loop stability proof.'}


def audit(folder, model, hpp_samples):
    started=time.perf_counter()
    summary=json.loads((folder/'learning_summary.json').read_text())
    amp=float(summary['amplitude']);n=model.n
    raw=np.load(folder/'learning_data.npz')
    sets={name:{key:raw[name+'_'+key] for key in ['x','h_res','g_res','q_raw','tip_m']} for name in ['train','validation','test','ood']}
    initial='initial_meromorphic' in folder.name
    if initial:
        spec=importlib.util.spec_from_file_location('audited_initial_learning',Path(__file__).with_name('run_learning_initial.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    else: module=revised
    scale=np.sqrt(np.r_[model.nu.numpy(),model.nu.numpy()])/amp
    sq=model.Sq.numpy()
    coeff=np.load(folder/'analytic_coefficients.npy')
    checkpoint_results=[]
    base={}
    rng=np.random.default_rng(91025)
    sampled={name:np.sort(rng.choice(len(sets[name]['x']),size=min(hpp_samples,len(sets[name]['x'])),replace=False)) for name in ['test','ood']}
    label_indices=sampled['test']
    rederived=module.labels(model,sets['test']['x'][label_indices],amp)
    source_label_check={key:float(np.max(np.abs(rederived[key]-sets['test'][key][label_indices]))) for key in ['h_res','g_res','q_raw','tip_m']}
    for name in ['test','ood']:
        data=sets[name]
        values,design=module.polynomial_design(data['x'],n)
        poly_gradient=np.einsum('bdf,f->bd',design,coeff)
        base[name]={}
        for variant,g,h in [('linear',np.zeros_like(data['g_res']),np.zeros(len(values))),('analytic',poly_gradient,values@coeff)]:
            base[name][variant]=grad_metrics(g,data,amp,scale,sq,model.omega0,model.E0)
            base[name][variant]['physical_energy_rmse_J']=float(model.E0*np.sqrt(np.mean((h-data['h_res'])**2)))
    for record in summary['complex_network']:
        checkpoint_path=folder/f"complex_seed{record['seed']}.pt"
        checkpoint=torch.load(checkpoint_path,map_location='cpu',weights_only=False)
        if float(checkpoint['amplitude'])!=amp: raise ValueError('Checkpoint/data amplitude mismatch')
        net=module.ComplexResidual(n,checkpoint['width'],checkpoint['output_scale'])
        net.load_state_dict(checkpoint['state_dict']);net.eval()
        result={'seed':record['seed'],'checkpoint_sha256':sha(checkpoint_path),
                'real_trainable_parameters':sum(2*p.numel() for p in net.parameters()),'splits':{},'hpp':{}}
        for name in ['test','ood']:
            data=sets[name]
            ph,pg=module.network_prediction(net,data['x'])
            result['splits'][name]=grad_metrics(pg,data,amp,scale,sq,model.omega0,model.E0)
            result['splits'][name]['physical_energy_rmse_J']=float(model.E0*np.sqrt(np.mean((ph-data['h_res'])**2)))
            old_name='test' if name=='test' else 'out_of_domain'
            result['splits'][name]['gradient_relative_l2_difference_from_training_summary']=abs(result['splits'][name]['normalized_x_gradient_relative_l2']-record[old_name]['gradient_relative_l2'])
            result['hpp'][name]=hpp_audit(model,module,net,coeff,data['x'],amp,sampled[name])
            if initial:result['splits'][name]['complex_tanh_pole_diagnostics']=pole_diagnostics(net,data['x'])
        checkpoint_results.append(result)
    source=Path(__file__).resolve().parent
    result={
        'scope':'Independent frozen-checkpoint inference, deterministic normalization audit, exact data-overlap check and finite momentum-Hessian diagnostics; no retraining',
        'model':'12 configuration DoF/24 phase-dimensional Kirchhoff strain Ritz; not the full Cosserat rod, no KAM certification',
        'amplitude':amp,'data_sha256':sha(folder/'learning_data.npz'),
        'data_sha_matches_learning_summary':sha(folder/'learning_data.npz')==summary['data_sha256'],
        'config_sha256':sha(source.parent/'rod3d/config.json'),
        'source_sha256':{name:sha(source/name) for name in ['rod_rom.py','run_learning.py','run_learning_initial.py','evaluate_models.py']},
        'split_overlap':split_checks(sets),
        'label_recomputation_indices':label_indices.tolist(),
        'label_recomputation_max_absolute_differences':source_label_check,
        'baselines':base,'complex_checkpoints':checkpoint_results,
        'feedforward_common_truth_audit':audit_feedforward(folder,model),
        'elapsed_seconds':time.perf_counter()-started,
        'interpretation_limits':[
            'x is an energy-balanced normalization, not canonical: its Poisson matrix is D J D.',
            'The 48-feature linear fit and 7104-real-parameter network have different capacity and loss functions; this is not a real-versus-complex representation experiment.',
            'Test/OOD inspection during earlier architecture development makes reused samples exploratory, even though optimization uses training and checkpoint choice uses validation only.',
            'A positive finite H_PP sample is not a uniform positivity, inverse-map, convergence, or KAM proof.',
        ],
    }
    (folder/'evaluation_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'folder':str(folder),'elapsed_seconds':result['elapsed_seconds'],
                      'data_hash_ok':result['data_sha_matches_learning_summary'],
                      'label_check':source_label_check,
                      'canonical_test_errors':[r['splits']['test']['canonical_z_gradient_and_tau_vector_field_relative_l2'] for r in checkpoint_results],
                      'velocity_test_errors':[r['splits']['test']['raw_ritz_generalized_velocity_relative_l2'] for r in checkpoint_results],
                      'hpp_test_min':[r['hpp']['test']['summary']['complex']['minimum'] for r in checkpoint_results]}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--folders',nargs='+',type=Path,default=[Path('stage2/results/learning_initial_meromorphic'),Path('stage2/results/learning'),Path('stage2/results/learning_stress')])
    parser.add_argument('--hpp-samples',type=int,default=12)
    args=parser.parse_args()
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    model=RodROM()
    for folder in args.folders:audit(folder,model,args.hpp_samples)
