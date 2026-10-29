"""Fresh, frozen-model confirmation set. No fitting or checkpoint selection.

The manifest and copies of every evaluated weight/coefficient file are written
before any confirmation samples are generated. Old test/OOD metrics remain
development-stage exploratory evaluations. Newly trained model families may
use these data only after recording their own frozen identity, without tuning.
"""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import time
import numpy as np
import torch
from rod_rom import RodROM
import run_learning_trained_source as trained
from evaluate_models import grad_metrics,hpp_audit,row_set


HERE=Path(__file__).resolve().parent
STAGE2=HERE.parents[1]
OUT=STAGE2/'results/learning_confirmation'
PROTOCOL={
    'sampling_seed':20261030,
    'sampling_order':['main:test','main:ood','stress:test','stress:ood'],
    'test_count_per_amplitude':2048,'ood_count_per_amplitude':1024,
    'test_normalized_halfwidth':1.0,'ood_normalized_halfwidth':1.5,
    'amplitudes':{'main':0.08,'stress':0.35},
    'checkpoint_seeds':[1025,1026,1027],
    'hessian_sample_seed':20261031,'hessian_samples_per_split':12,
    'fitting_or_checkpoint_selection':False,
}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()


def freeze():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest_path=OUT/'freeze_manifest.json'
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text())
        if manifest['protocol']!=PROTOCOL:raise ValueError('Frozen confirmation protocol differs; not overwriting')
        for item in manifest['files']:
            if sha(OUT/item['frozen_relative_path'])!=item['sha256']:
                raise ValueError('Frozen input hash mismatch: '+item['frozen_relative_path'])
        return manifest
    if list(OUT.glob('*/confirmation_data.npz')):
        raise ValueError('Confirmation data already exist without a pre-data freeze manifest')
    inputs=[]
    for group,source in [('main','learning'),('stress','learning_stress')]:
        for name in ['analytic_coefficients.npy','rom_matrices.npz','learning_summary.json']+[f'complex_seed{s}.pt' for s in PROTOCOL['checkpoint_seeds']]:
            inputs.append((STAGE2/'results'/source/name,Path('frozen/models')/group/name))
    for name in ['rod_rom.py','run_learning_trained_source.py','evaluate_models.py','run_confirmation.py']:
        inputs.append((HERE/name,Path('frozen/source')/name))
    inputs.append((HERE.parent/'rod3d/config.json',Path('frozen/config.json')))
    files=[]
    for source,relative in inputs:
        target=OUT/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        files.append({'original_path':str(source),'frozen_relative_path':str(relative),'sha256':sha(target),'bytes':target.stat().st_size})
    manifest={
        'frozen_utc_before_data_generation':now(),
        'confirmation_data_present_when_freezing':False,
        'protocol':PROTOCOL,'files':files,
        'model_scope':'12 configuration DoF / 24 phase dimensions, conservative variable-mass Kirchhoff strain Ritz; not full Cosserat-fluid-contact truth',
        'rule':'No architecture, hyperparameter or checkpoint tuning against these samples; evaluate every frozen revised seed and both frozen baselines.',
        'earlier_test_status':'development-stage exploratory test/OOD; not this new confirmation set',
        'external_model_rule':'Additional families must record their frozen checkpoint identities before opening confirmation labels/results, then evaluate without tuning.',
    }
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'stage':'manifest_frozen_before_data','path':str(manifest_path),'sha256':sha(manifest_path),'utc':manifest['frozen_utc_before_data_generation']}),flush=True)
    return manifest


def evaluate(group,amplitude,sets,model,data_path,manifest):
    source=OUT/'frozen/models'/group
    old=json.loads((source/'learning_summary.json').read_text())
    if old['amplitude']!=amplitude:raise ValueError('Frozen source amplitude mismatch')
    with np.load(source/'rom_matrices.npz') as m:
        for key,current in {'M0':model.M0.numpy(),'K0':model.K0,'Sq':model.Sq.numpy(),'Sp':model.Sp.numpy()}.items():
            if not np.array_equal(m[key],current):raise ValueError('Frozen chart differs from confirmation generator: '+key)
    coefficient=np.load(source/'analytic_coefficients.npy')
    scale=np.sqrt(np.r_[model.nu.numpy(),model.nu.numpy()])/amplitude
    hpp_rng=np.random.default_rng(PROTOCOL['hessian_sample_seed']+(0 if group=='main' else 1))
    indices={split:np.sort(hpp_rng.choice(len(sets[split]['x']),PROTOCOL['hessian_samples_per_split'],replace=False)) for split in ['test','ood']}
    results={'baselines':{},'complex_checkpoints':[]}
    for split,data in sets.items():
        values,design=trained.polynomial_design(data['x'],model.n)
        results['baselines'][split]={}
        for name,h,g in [('linear',np.zeros(len(values)),np.zeros_like(data['g_res'])),
                         ('analytic',values@coefficient,np.einsum('bdf,f->bd',design,coefficient))]:
            metrics=grad_metrics(g,data,amplitude,scale,model.Sq.numpy(),model.omega0,model.E0)
            metrics['dimensionless_energy_rmse']=float(np.sqrt(np.mean((h-data['h_res'])**2)))
            metrics['physical_energy_rmse_J']=model.E0*metrics['dimensionless_energy_rmse']
            results['baselines'][split][name]=metrics
    for seed in PROTOCOL['checkpoint_seeds']:
        checkpoint_path=source/f'complex_seed{seed}.pt'
        state=torch.load(checkpoint_path,map_location='cpu',weights_only=False)
        if state['amplitude']!=amplitude:raise ValueError('Checkpoint amplitude mismatch')
        net=trained.ComplexResidual(state['n'],state['width'],state['output_scale'])
        net.load_state_dict(state['state_dict']);net.eval()
        row={'seed':seed,'checkpoint_sha256':sha(checkpoint_path),'real_parameter_count':sum(2*p.numel() for p in net.parameters()),'splits':{},'hpp':{}}
        for split,data in sets.items():
            h,g=trained.network_prediction(net,data['x'])
            metrics=grad_metrics(g,data,amplitude,scale,model.Sq.numpy(),model.omega0,model.E0)
            metrics['dimensionless_energy_rmse']=float(np.sqrt(np.mean((h-data['h_res'])**2)))
            metrics['physical_energy_rmse_J']=model.E0*metrics['dimensionless_energy_rmse']
            row['splits'][split]=metrics
            row['hpp'][split]=hpp_audit(model,trained,net,coefficient,data['x'],amplitude,indices[split])
        results['complex_checkpoints'].append(row)
    old_source=STAGE2/'results'/('learning' if group=='main' else 'learning_stress')/'learning_data.npz'
    old_data=np.load(old_source)
    previous_rows={name:row_set(old_data[name+'_x']) for name in ['train','validation','test','ood']}
    duplicate_counts={split:{oldname:len(row_set(data['x'])&rows) for oldname,rows in previous_rows.items()} for split,data in sets.items()}
    result={
        'status':'frozen-model independent confirmation; no tuning performed',
        'amplitude':amplitude,'group':group,'protocol':PROTOCOL,
        'freeze_manifest_sha256':sha(OUT/'freeze_manifest.json'),
        'frozen_utc':manifest['frozen_utc_before_data_generation'],'evaluation_completed_utc':now(),
        'confirmation_data_sha256':sha(data_path),
        'exact_row_intersections_with_development_data':duplicate_counts,
        'exact_test_ood_intersection':len(row_set(sets['test']['x'])&row_set(sets['ood']['x'])),
        'normalization':'x=D z; x is not canonical; reported gradient metrics label x and z separately',
        'scope':'Independent synthetic full-phase states labeled by the same 12-DoF conservative ROM, not physical observations or a full-Cosserat validation',
        'capacity_comparison':'48 fixed polynomial coefficients versus 7104 real trainable parameters; not a controlled real-versus-complex comparison',
        'hpp_limitation':'12 finite floating-point test and OOD samples per checkpoint, not uniform positive-mass certification',
        **results,
    }
    (OUT/group/'confirmation_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'group':group,'data_sha256':result['confirmation_data_sha256'],
        'x_test_errors':[r['splits']['test']['normalized_x_gradient_relative_l2'] for r in results['complex_checkpoints']],
        'z_test_errors':[r['splits']['test']['canonical_z_gradient_and_tau_vector_field_relative_l2'] for r in results['complex_checkpoints']],
        'hpp_test_min':[r['hpp']['test']['summary']['complex']['minimum'] for r in results['complex_checkpoints']]}),flush=True)
    return result


def main():
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    start=time.perf_counter();manifest=freeze()
    model=RodROM(config_path=OUT/'frozen/config.json')
    rng=np.random.default_rng(PROTOCOL['sampling_seed'])
    all_results={}
    for group,amp in PROTOCOL['amplitudes'].items():
        destination=OUT/group;destination.mkdir(exist_ok=True)
        data_path=destination/'confirmation_data.npz'
        dataset_manifest=destination/'dataset_manifest.json'
        xs={split:rng.uniform(-extent,extent,size=(count,2*model.n)) for split,count,extent in [('test',2048,1.),('ood',1024,1.5)]}
        if data_path.exists():
            saved_manifest=json.loads(dataset_manifest.read_text())
            if sha(data_path)!=saved_manifest['data_sha256']:raise ValueError('Confirmation data changed after generation')
            data=np.load(data_path)
            sets={split:{key:data[split+'_'+key] for key in ['x','h_res','g_res','q_raw','tip_m']} for split in xs}
            for split in xs:
                if not np.array_equal(sets[split]['x'],xs[split]):raise ValueError('Confirmation coordinates differ from frozen seed/protocol')
        else:
            sets={split:trained.labels(model,x,amp) for split,x in xs.items()}
            np.savez_compressed(data_path,**{split+'_'+key:value for split,data in sets.items() for key,value in data.items()})
            record={'generated_utc':now(),'amplitude':amp,'data_sha256':sha(data_path),'freeze_manifest_sha256':sha(OUT/'freeze_manifest.json'),
                    'phase_dimension':2*model.n,'split_counts':{name:len(data['x']) for name,data in sets.items()},
                    'sampling_seed':PROTOCOL['sampling_seed'],'sampling_order':PROTOCOL['sampling_order'],
                    'no_training_or_model_selection':True}
            dataset_manifest.write_text(json.dumps(record,indent=2)+'\n')
        all_results[group]=evaluate(group,amp,sets,model,data_path,manifest)
    completion={'completed_utc':now(),'elapsed_seconds':time.perf_counter()-start,'freeze_manifest_sha256':sha(OUT/'freeze_manifest.json'),
                'groups':{g:{'amplitude':r['amplitude'],'data_sha256':r['confirmation_data_sha256'],'summary':str(OUT/g/'confirmation_summary.json')} for g,r in all_results.items()},
                'source_checkpoint_selection_or_retraining':False}
    (OUT/'completion.json').write_text(json.dumps(completion,indent=2)+'\n')
    print(json.dumps(completion,indent=2),flush=True)


if __name__=='__main__':main()
