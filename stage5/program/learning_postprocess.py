"""Read-only model/data verification and figures for frozen S5-L01 runs."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from learning_models import RodROM,labels,S2

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'stage5/results/learning'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    torch.set_default_dtype(torch.float64);torch.set_num_threads(1);torch.set_num_interop_threads(1)
    research=json.loads((OUT/'S5_L01_results.json').read_text());protocol=research['protocol']
    rom=RodROM();raw=np.load(OUT/'S5_L01_training_data.npz')
    recomputed=labels(rom,raw['train_x'][:8],protocol['amplitude'])
    check=dict(energy_max_abs_difference=float(np.max(abs(recomputed['h_res']-raw['train_h_res'][:8]))),
               gradient_max_abs_difference=float(np.max(abs(recomputed['g_res']-raw['train_g_res'][:8]))),
               coordinate_dimension=24,physical_model='same12DOF20cell geometric ROM, original ideal axial bias')
    if check['energy_max_abs_difference']>1e-12 or check['gradient_max_abs_difference']>1e-10:
        raise RuntimeError('Frozen training labels no longer match the declared physical model')
    source_checks={name:sha(ROOT/name)==value for name,value in protocol['source_sha256'].items()}
    if not all(source_checks.values()):raise RuntimeError('Training source changed after protocol freeze')
    freeze=json.loads((OUT/'S5_L01_freeze_before_test.json').read_text())
    checkpoint_checks={r['checkpoint']:sha(ROOT/r['checkpoint'])==r['checkpoint_sha256'] for r in freeze['records']}
    if not all(checkpoint_checks.values()):raise RuntimeError('Frozen checkpoint changed')
    inverse=[];negative=[]
    for m in research['models']:
        for split in ('test','OOD'):
            rows=m[split]['Hpp_Legendre']['rows']
            inverse.append(dict(kind=m['kind'],seed=m['seed'],split=split,
                solver_success_flag_count=sum(r['root_success'] for r in rows),
                residual_below_1e8_count=sum(r['root_residual']<1e-8 for r in rows),
                largest_equation_residual=max(r['root_residual'] for r in rows),
                note='Residual convergence and scipy success flag are distinct. A non-success progress flag at machine residual is not loss of mathematical invertibility; physical momentum error remains a separate quantity.'))
            for row in rows:
                if row['minimum_eigenvalue']<0:
                    negative.append(dict(kind=m['kind'],seed=m['seed'],split=split,index=row['sample_index'],
                        Hpp_minimum_eigenvalue=row['minimum_eigenvalue'],
                        independent_energy_second_difference=row['minimum_direction_centered_energy_second_difference'],
                        negative_sign_confirmed=row['minimum_direction_centered_energy_second_difference']<0))
    result=dict(experiment='S5-L01-independent-checks',status='executed_pass',label_recomputation=check,
        source_hash_matches=source_checks,checkpoint_hash_matches=checkpoint_checks,
        config_sha256=sha(S2.parent/'rod3d/config.json'),
        inverse_diagnostics=inverse,negative_Hpp_examples=negative,
        all_negative_signs_confirmed=all(r['negative_sign_confirmed'] for r in negative),
        formal_SPD_scope='For finite real L with positive exponential diagonal, H_PP=Dnu LL^T Dnu is SPD. Uniform conditioning/physical accuracy not inferred.')
    (OUT/'S5_L01_independent_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,axs=plt.subplots(1,3,figsize=(13,3.7),layout='constrained')
    colors={'analytic_mechanical4':'#8c564b','complex_hidden':'#1f77b4','spd_complex':'#2ca02c'}
    names={'analytic_mechanical4':'Mechanical polynomial (8749)','complex_hidden':'Complex hidden (7104)','spd_complex':'SPD complex (13440)'}
    for m in research['models']:
        history=json.loads((OUT/f"S5_L01_{m['kind']}_seed{m['seed']}_training.json").read_text())['history']
        samples=[x for x in history if 'validation_canonical_residual_gradient_relative_l2' in x]
        axs[0].semilogy([x['step'] for x in samples],[x['validation_canonical_residual_gradient_relative_l2'] for x in samples],color=colors[m['kind']],alpha=.65,label=names[m['kind']] if m['seed']==51001 else None)
    axs[0].set(xlabel='Adam updates',ylabel='Validation residual-field relative L2',title='Frozen-checkpoint selection');axs[0].legend(fontsize=7)
    for j,kind in enumerate(colors):
        models=[m for m in research['models'] if m['kind']==kind]
        for offset,split,marker in [(-.13,'test','o'),(.13,'OOD','x')]:
            values=[m[split]['canonical_gradient_and_tau_field_relative_l2'] for m in models]
            axs[1].scatter(np.full(3,j+offset),values,color=colors[kind],marker=marker,label=split if j==0 else None)
        for m in models:
            points=[x['minimum_eigenvalue'] for split in ('test','OOD') for x in m[split]['Hpp_Legendre']['rows']]
            axs[2].scatter(np.full(len(points),j)+np.linspace(-.12,.12,len(points)),points,s=12,alpha=.5,color=colors[kind])
    axs[1].set_xticks(range(3),['Polynomial','Complex','SPD']);axs[1].set(ylabel='Independent total-field relative L2',title='Three seeds; unequal model classes');axs[1].legend()
    axs[2].set_xticks(range(3),['Polynomial','Complex','SPD']);axs[2].axhline(0,color='black',linewidth=.7);axs[2].set_yscale('symlog',linthresh=.1);axs[2].set(ylabel='Smallest H_PP eigenvalue',title='8 test + 8 OOD points per seed')
    for ax in axs:ax.grid(alpha=.2)
    fig.savefig(OUT/'S5_L01_learning_structure.png',dpi=180);fig.savefig(OUT/'S5_L01_learning_structure.pdf');plt.close(fig)
    print(json.dumps(dict(status=result['status'],label_recomputation=check,negative_points=len(negative),all_negative_signs_confirmed=result['all_negative_signs_confirmed']),indent=2))


if __name__=='__main__':main()
