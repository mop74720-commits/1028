"""S5-L01: new, explicitly budgeted 12-DOF learning experiment.

Three seeds, shared training/validation, frozen models before independent
test/OOD labels are generated. No historical checkpoint is reconstructed.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,platform,time
from pathlib import Path
import sys
import numpy as np
import scipy
from scipy.optimize import root
import torch
from learning_models import (RodROM,labels,make_model,predict,real_parameter_count,
                             polynomial_design,S2)

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'stage5/results/learning'
KINDS=('analytic_mechanical4','complex_hidden','spd_complex')
SEEDS=(51001,51002,51003)
AMP=.08


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def rel(x,y):return float(np.linalg.norm(x)/max(np.linalg.norm(y),1e-30))


def load_split(raw,name):return {k:raw[name+'_'+k] for k in ('x','h_res','g_res','q_raw','tip_m')}


def metrics(h,g,data,scale,rom):
    errx=g-data['g_res'];errz=errx*scale
    truthx=data['g_res']+AMP**2*data['x'];truthz=truthx*scale
    e=h-data['h_res'];n=rom.n
    return dict(energy_rmse_dimensionless=float(np.sqrt(np.mean(e**2))),
        energy_rmse_J=float(rom.E0*np.sqrt(np.mean(e**2))),
        normalized_x_gradient_relative_l2=rel(errx,truthx),
        canonical_gradient_and_tau_field_relative_l2=rel(errz,truthz),
        canonical_residual_gradient_relative_l2=rel(errz,data['g_res']*scale),
        canonical_gradient_max_sample_error=float(np.max(np.linalg.norm(errz,axis=1))),
        configuration_velocity_relative_l2=rel(errz[:,n:],truthz[:,n:]),
        momentum_field_relative_l2=rel(errz[:,:n],truthz[:,:n]),
        physical_time_phase_field_rmse=float(rom.omega0*np.sqrt(np.mean(errz**2))),
        raw_ritz_velocity_relative_l2=rel(errz[:,n:]@rom.Sq.numpy().T,truthz[:,n:]@rom.Sq.numpy().T),
        warning='Empirical norms on specified synthetic samples; not uniform or complex-domain bounds.')


def training_record(kind,seed,rom,train,valid,scale,hscale,gscale,steps):
    lr=.001 if kind=='analytic_mechanical4' else .003
    net=make_model(kind,12,AMP,hscale,seed)
    initial={k:v.detach().clone() for k,v in net.named_parameters()}
    opt=torch.optim.Adam(net.parameters(),lr=lr)
    rng=np.random.default_rng(seed);history=[];best=float('inf');beststate=None;beststep=None
    d=torch.tensor(scale);start=time.perf_counter()
    for step in range(1,steps+1):
        idx=rng.integers(0,len(train['x']),128)
        x=torch.tensor(train['x'][idx],requires_grad=True)
        h=net(x);g=torch.autograd.grad(h.sum(),x,create_graph=True)[0]
        loss=(((g-torch.tensor(train['g_res'][idx]))*d)/gscale).square().mean()+.15*((h-torch.tensor(train['h_res'][idx]))/hscale).square().mean()
        if not torch.isfinite(loss):raise FloatingPointError(f'{kind}/{seed} nonfinite loss at {step}')
        opt.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(net.parameters(),10.);opt.step()
        row=dict(step=step,training_batch_loss=float(loss.detach()))
        if step==1 or step%50==0 or step==steps:
            vh,vg=predict(net,valid['x']);metric=rel((vg-valid['g_res'])*scale,valid['g_res']*scale)
            row['validation_canonical_residual_gradient_relative_l2']=metric
            row['elapsed_s']=time.perf_counter()-start
            if metric<best:
                best=metric;beststep=step;beststate={k:v.detach().clone() for k,v in net.state_dict().items()}
            if step%200==0:print(json.dumps(dict(kind=kind,seed=seed,step=step,validation=metric,wall_s=row['elapsed_s'])),flush=True)
        history.append(row)
    laststate={k:v.detach().clone() for k,v in net.state_dict().items()}
    net.load_state_dict(beststate)
    checkpoint=OUT/f'S5_L01_{kind}_seed{seed}.pt'
    payload=dict(experiment='S5-L01',kind=kind,n=12,amplitude=AMP,output_scale=hscale,
                 seed=seed,best_step=beststep,state_dict=beststate,last_state_dict=laststate,
                 target='original geometric ROM, ideal static axial bias; not full-coil-bias plant')
    torch.save(payload,checkpoint)
    changes={}
    for name,p in net.named_parameters():
        delta=p.detach()-initial[name]
        changes[name]=dict(real_norm=float(torch.linalg.norm(delta.real)),
            imaginary_norm=float(torch.linalg.norm(delta.imag)) if delta.is_complex() else None)
    # Convex readout training is not claimed to have reached least-squares optimality.
    net.zero_grad(set_to_none=True);objective=0.
    for start_i in range(0,len(train['x']),128):
        xx=torch.tensor(train['x'][start_i:start_i+128],requires_grad=True)
        hh=net(xx);gg=torch.autograd.grad(hh.sum(),xx,create_graph=True)[0]
        weight=len(xx)/len(train['x'])
        loss=weight*((((gg-torch.tensor(train['g_res'][start_i:start_i+128]))*d)/gscale).square().mean()+.15*((hh-torch.tensor(train['h_res'][start_i:start_i+128]))/hscale).square().mean())
        loss.backward();objective+=float(loss.detach())
    stationarity=float(np.sqrt(sum(float(torch.sum(p.grad.abs()**2)) for p in net.parameters())))
    record=dict(kind=kind,seed=seed,updates=steps,batch=128,learning_rate=lr,
                real_parameters=real_parameter_count(net),best_validation_step=beststep,
                best_validation_metric=best,training_seconds=time.perf_counter()-start,
                full_training_objective_at_selected=objective,objective_parameter_gradient_norm=stationarity,
                checkpoint=str(checkpoint.relative_to(ROOT)),checkpoint_sha256=sha(checkpoint),
                selected_parameter_updates=changes,history=history)
    (OUT/f'S5_L01_{kind}_seed{seed}_training.json').write_text(json.dumps(record,indent=2)+'\n')
    return record


def hpp_legendre(net,rom,data,scale,indices):
    n=rom.n;d=torch.tensor(scale);rows=[]
    for index in indices:
        x=torch.tensor(data['x'][index]);z=x/d;q=z[:n];p=z[n:]
        def energy(momentum):
            xx=torch.cat([q,momentum])*d
            return .5*AMP**2*xx.square().sum()+net(xx[None,:])[0]
        def gradient(momentum):
            mom=momentum.detach().clone().requires_grad_(True)
            return torch.autograd.grad(energy(mom),mom)[0]
        a=torch.autograd.functional.hessian(energy,p).detach().numpy()
        eig,vec=np.linalg.eigh(a)
        rawq=(rom.Sq@q)[None,:]
        mass,_=rom.mechanics(rawq)
        scaled=(rom.omega0**2/rom.E0)*(rom.Sq.T@mass[0]@rom.Sq)
        truth=torch.linalg.inv(scaled).detach().numpy()
        target=truth@p.numpy()
        evaluations=[0]
        def fun(mom):
            evaluations[0]+=1
            return gradient(torch.tensor(mom)).detach().numpy()-target
        def jac(mom):return torch.autograd.functional.hessian(energy,torch.tensor(mom)).detach().numpy()
        inversion=root(fun,p.numpy(),jac=jac,method='hybr',options={'xtol':1e-10,'maxfev':120})
        residual=float(np.linalg.norm(fun(inversion.x)))
        direction=torch.tensor(vec[:,0]);eps=2e-5/max(float(torch.linalg.norm(d[n:]*direction)),1.)
        fd=float((energy(p+eps*direction)-2*energy(p)+energy(p-eps*direction))/eps**2)
        row=dict(sample_index=int(index),minimum_eigenvalue=float(eig[0]),maximum_eigenvalue=float(eig[-1]),
            singular_condition=float(np.linalg.cond(a)),relative_Hpp_error=float(np.linalg.norm(a-truth)/np.linalg.norm(truth)),
            minimum_direction_centered_energy_second_difference=fd,finite_difference_step=eps,
            root_success=bool(inversion.success),root_message=str(inversion.message),root_function_evaluations=evaluations[0],
            root_residual=residual,inverse_momentum_error=float(np.linalg.norm(inversion.x-p.numpy())),
            relative_inverse_momentum_error=rel(inversion.x-p.numpy(),p.numpy()),
            recovered_momentum=inversion.x.tolist(),true_momentum=p.numpy().tolist())
        rows.append(row)
    return dict(sample_count=len(rows),rows=rows,
        negative_or_zero_Hpp_count=sum(r['minimum_eigenvalue']<=0 for r in rows),
        minimum_Hpp_eigenvalue=min(r['minimum_eigenvalue'] for r in rows),
        maximum_condition=max(r['singular_condition'] for r in rows),
        maximum_relative_Hpp_error=max(r['relative_Hpp_error'] for r in rows),
        successful_truth_velocity_roots=sum(r['root_success'] and r['root_residual']<1e-8 for r in rows),
        warning='Eight prespecified samples only. Root initialized at true momentum; this is a local best-case inverse test. Successful inverse need not be the true physical momentum or prove SPD/global invertibility.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--steps',type=int,default=1200);parser.add_argument('--evaluate-only',action='store_true');args=parser.parse_args()
    torch.set_default_dtype(torch.float64);torch.set_num_threads(1);torch.set_num_interop_threads(1)
    OUT.mkdir(parents=True,exist_ok=True);start=time.perf_counter();rom=RodROM()
    data_path=OUT/'S5_L01_training_data.npz'
    if not data_path.exists():
        rng=np.random.default_rng(51001)
        train=labels(rom,rng.uniform(-1,1,(1024,24)),AMP)
        valid=labels(rom,rng.uniform(-1,1,(256,24)),AMP)
        np.savez_compressed(data_path,**{'train_'+k:v for k,v in train.items()},**{'valid_'+k:v for k,v in valid.items()})
    raw=np.load(data_path);train=load_split(raw,'train');valid=load_split(raw,'valid')
    scale=np.sqrt(np.r_[rom.nu.numpy(),rom.nu.numpy()])/AMP
    hscale=max(float(np.std(train['h_res'])),1e-7)
    gscale=max(float(np.sqrt(np.mean((train['g_res']*scale)**2))),1e-7)
    sources=[Path(__file__),Path(__file__).with_name('learning_models.py')]+[S2/name for name in ['rod_rom.py','run_learning.py','train_spd_complex.py']]
    source_hash={str(p.relative_to(ROOT)):sha(p) for p in sources}
    protocol=dict(experiment='S5-L01',timestamp_utc=now(),training_data_sha256=sha(data_path),
        target='same 12-DOF,20-cell variable-mass Kirchhoff ROM with ideal axial bias; excludes full-coil bias and fluid/contact',
        amplitude=AMP,train=1024,validation=256,test=512,OOD=256,seeds=SEEDS,steps=args.steps,
        loss='mean((D*(grad_x hres_pred-grad_x hres_true))/global_train_rms_grad_z_res)^2 + 0.15*mean((hres_pred-hres_true)/train_std_hres)^2',
        scales=dict(hscale=hscale,gscale_z=gscale,coordinate_D=scale.tolist()),
        algorithms='Adam with same batches/update count; polynomial lr=.001, networks=.003 fixed after training/validation-only timing pilot. Validation selects frozen checkpoint every50 updates; test/OOD labels generated after all nine models frozen.',
        analytic_scope='complete degree3/4 momentum-quadratic mechanical residual,8749 parameters; no p^4; not exact full dictionary least-squares optimum',
        source_sha256=source_hash,environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,torch=torch.__version__,threads=1,platform=platform.platform()))
    if not args.evaluate_only:
        if (OUT/'S5_L01_protocol.json').exists():raise RuntimeError('Existing experiment protocol: use --evaluate-only; do not silently retrain frozen records.')
        (OUT/'S5_L01_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
        records=[]
        for kind in KINDS:
            for seed in SEEDS:records.append(training_record(kind,seed,rom,train,valid,scale,hscale,gscale,args.steps))
        # The archived 48-feature readout is a deliberately smaller historical comparator.
        values,design=polynomial_design(train['x'],rom.n)
        matrix=np.vstack(((design*scale[None,:,None]).reshape(-1,48)/(gscale*np.sqrt(len(train['x'])*24)),
                          np.sqrt(.15)*values/(hscale*np.sqrt(len(train['x'])))))
        target=np.r_[(train['g_res']*scale).reshape(-1)/(gscale*np.sqrt(len(train['x'])*24)),
                     np.sqrt(.15)*train['h_res']/(hscale*np.sqrt(len(train['x'])))]
        coefficients=np.linalg.lstsq(matrix,target,rcond=1e-12)[0]
        np.save(OUT/'S5_L01_legacy48_coefficients.npy',coefficients)
        freeze=dict(timestamp_utc=now(),records=[{k:r[k] for k in ('kind','seed','checkpoint','checkpoint_sha256','best_validation_step')} for r in records],
                    source_sha256=source_hash,legacy48_sha256=sha(OUT/'S5_L01_legacy48_coefficients.npy'),
                    test_and_OOD_labels_generated=False)
        (OUT/'S5_L01_freeze_before_test.json').write_text(json.dumps(freeze,indent=2)+'\n')
    else:
        protocol=json.loads((OUT/'S5_L01_protocol.json').read_text())
        records=[json.loads((OUT/f'S5_L01_{kind}_seed{seed}_training.json').read_text()) for kind in KINDS for seed in SEEDS]
    freeze=json.loads((OUT/'S5_L01_freeze_before_test.json').read_text())
    for r in freeze['records']:
        if sha(ROOT/r['checkpoint'])!=r['checkpoint_sha256']:raise RuntimeError('Frozen checkpoint changed')
    evaluation=OUT/'S5_L01_independent_evaluation_data.npz'
    if evaluation.exists():
        ee=np.load(evaluation);sets={name:load_split(ee,name) for name in ('test','OOD')}
    else:
        rng=np.random.default_rng(510990)
        sets={'test':labels(rom,rng.uniform(-1,1,(512,24)),AMP),
              'OOD':labels(rom,rng.uniform(-1.5,1.5,(256,24)),AMP)}
        np.savez_compressed(evaluation,**{name+'_'+k:v for name,data in sets.items() for k,v in data.items()})
    indices={'test':[0,73,146,219,292,365,438,511],'OOD':[0,36,72,108,144,180,216,255]}
    predictions={};report=[]
    for record in records:
        kind=record['kind'];seed=record['seed'];net=make_model(kind,12,AMP,hscale,seed)
        state=torch.load(ROOT/record['checkpoint'],map_location='cpu',weights_only=False);net.load_state_dict(state['state_dict'])
        row={k:record[k] for k in ('kind','seed','real_parameters','best_validation_step','best_validation_metric','training_seconds','full_training_objective_at_selected','objective_parameter_gradient_norm')}
        for name,data in sets.items():
            h,g=predict(net,data['x']);row[name]=metrics(h,g,data,scale,rom)
            row[name]['Hpp_Legendre']=hpp_legendre(net,rom,data,scale,indices[name])
            predictions[f'{kind}_{seed}_{name}_hres']=h;predictions[f'{kind}_{seed}_{name}_gres_x']=g
        report.append(row);print(json.dumps(dict(stage='evaluated',kind=kind,seed=seed,test=row['test']['canonical_gradient_and_tau_field_relative_l2'],OOD=row['OOD']['canonical_gradient_and_tau_field_relative_l2'])),flush=True)
    baseline=[];coef=np.load(OUT/'S5_L01_legacy48_coefficients.npy')
    for kind in ('quadratic_prior','legacy48_readout'):
        row=dict(kind=kind,real_parameters=0 if kind=='quadratic_prior' else 48)
        for name,data in sets.items():
            if kind=='quadratic_prior':h=np.zeros(len(data['x']));g=np.zeros_like(data['x'])
            else:
                values,design=polynomial_design(data['x'],12);h=values@coef;g=design@coef
            row[name]=metrics(h,g,data,scale,rom)
            predictions[f'{kind}_{name}_hres']=h;predictions[f'{kind}_{name}_gres_x']=g
        baseline.append(row)
    np.savez_compressed(OUT/'S5_L01_predictions.npz',**predictions)
    result=dict(experiment='S5-L01',status='executed',protocol=protocol,model_metadata=rom.metadata(),
        frozen_before_labels=freeze['timestamp_utc'],evaluation_data_sha256=sha(evaluation),
        models=report,baselines=baseline,evaluation_indices=indices,wall_seconds_this_invocation=time.perf_counter()-start,
        limits=['new experiment; no old missing checkpoints recreated','capacity and optimization budgets declared, not identical function classes','no complex-domain uniform error or KAM certificate','Hpp/inversion checks finite independent subset','field labels are original ideal-axial-bias geometry; full-coil control projection is a separate diagnostic'])
    (OUT/'S5_L01_results.json').write_text(json.dumps(result,indent=2)+'\n')
    fields=['kind','seed','real_parameters','split','canonical_field_relative_l2','energy_rmse_J','Hpp_nonpositive_count','Hpp_min','Hpp_max_condition','inverse_max_relative_error']
    with (OUT/'S5_L01_metrics.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for model in report:
            for split in sets:
                a=model[split];b=a['Hpp_Legendre']
                writer.writerow(dict(kind=model['kind'],seed=model['seed'],real_parameters=model['real_parameters'],split=split,
                    canonical_field_relative_l2=a['canonical_gradient_and_tau_field_relative_l2'],energy_rmse_J=a['energy_rmse_J'],
                    Hpp_nonpositive_count=b['negative_or_zero_Hpp_count'],Hpp_min=b['minimum_Hpp_eigenvalue'],Hpp_max_condition=b['maximum_condition'],
                    inverse_max_relative_error=max(r['relative_inverse_momentum_error'] for r in b['rows'])))
    print(json.dumps(dict(status='complete',wall_seconds=result['wall_seconds_this_invocation'])),flush=True)


if __name__=='__main__':main()
