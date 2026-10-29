"""S5-L02: realizability of newly learned vector-field corrections.

Uses the actual full Biot--Savart current port. This is a pointwise allocation
diagnostic, not closed-loop compensation of the full-coil-bias physical plant.
The learned target remains S5-L01's ideal-axial-bias conservative ROM.
"""
from __future__ import annotations
import csv,hashlib,json,time
from pathlib import Path
import numpy as np
import torch
from coil_rom import CoilROM
from coil_control import CurrentAllocator

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'stage5/results/learning'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    torch.set_default_dtype(torch.float64);torch.set_num_threads(1);torch.set_num_interop_threads(1)
    start=time.perf_counter();model=CoilROM();allocator=CurrentAllocator(model)
    research=json.loads((OUT/'S5_L01_results.json').read_text())
    data=np.load(OUT/'S5_L01_independent_evaluation_data.npz')
    pred=np.load(OUT/'S5_L01_predictions.npz')
    scale=np.asarray(research['protocol']['scales']['coordinate_D'])
    source=[Path(__file__),Path(__file__).with_name('coil_rom.py'),Path(__file__).with_name('coil_control.py')]
    before={str(p.relative_to(ROOT)):sha(p) for p in source}
    rows=[];arrays={};scope=[];indices={'test':[0,146,292,511],'OOD':[0,72,144,255]}
    for split in indices:
        for index in indices[split]:
            z=data[split+'_x'][index]/scale;q=z[:12]
            port=model.current_port(q);singular=np.linalg.svd(port,compute_uv=False)
            pinv=np.linalg.pinv(port,rcond=1e-8)
            bias_info=model.physical_samples(q,model.bias_currents)
            scope.append(dict(split=split,index=index,bias_current_A=model.bias_currents.tolist(),
                bias_maximum_B_T=bias_info['maximum_B_T'],bias_maximum_G_T_per_m=bias_info['maximum_G_T_per_m'],
                bias_field_constraints_satisfied=bool(bias_info['maximum_B_T']<=allocator.field_bound and bias_info['maximum_G_T_per_m']<=allocator.gradient_bound)))
            for fitted in research['models']:
                kind=fitted['kind'];seed=fitted['seed']
                error=(pred[f'{kind}_{seed}_{split}_gres_x'][index]-data[split+'_g_res'][index])*scale
                # f_true-f_learned=(-error_P,+error_Q). Magnetic actuation changes Pdot only.
                desired=error[:12];uncontrollable=-error[12:]
                requested=model.bias_currents+pinv@desired
                unreachable=port@(requested-model.bias_currents)-desired
                row=dict(kind=kind,seed=seed,split=split,index=index,
                    correction_definition='f_true-f_learned=(-delta_grad_P,+delta_grad_Q)',
                    rank=int(np.sum(singular>singular[0]*1e-8)),rank_rcond=1e-8,
                    singular_values=singular.tolist(),required_force_norm=float(np.linalg.norm(desired)),
                    orthogonal_force_residual=float(np.linalg.norm(unreachable)),
                    unavoidable_configuration_field_error=float(np.linalg.norm(uncontrollable)),
                    total_field_error_before=float(np.linalg.norm(error)),
                    requested_peak_total_current_A=float(np.max(abs(requested))),
                    allocation_interval_s=.25,previous_total_current='preenergized bias; frozen decision-state allocation only')
                try:
                    current,record=allocator.allocate_force(q,desired,model.bias_currents,.25,rcond=1e-8)
                    achieved=port@(current-model.bias_currents);remaining=np.r_[uncontrollable,desired-achieved]
                    physical=model.physical_samples(q,current)
                    row.update(status='executed',allocation=record,
                        force_error_after=float(np.linalg.norm(desired-achieved)),
                        total_field_error_after=float(np.linalg.norm(remaining)),
                        peak_current_A=float(np.max(abs(current))),
                        maximum_B_T=physical['maximum_B_T'],maximum_G_T_per_m=physical['maximum_G_T_per_m'],
                        minimum_wire_distance_m=physical['minimum_distance_exact_wire_m'])
                    key=f'{kind}_{seed}_{split}_{index}'
                    arrays[key+'_current_A']=current;arrays[key+'_field_T']=physical['field_T'];arrays[key+'_gradient_T_per_m']=physical['gradient_T_per_m']
                except Exception as exc:
                    row.update(status='allocation_failed',failure=f'{type(exc).__name__}: {exc}')
                rows.append(row)
    after={str(p.relative_to(ROOT)):sha(p) for p in source}
    result=dict(experiment='S5-L02',status='executed_with_failures' if any(r['status']!='executed' for r in rows) else 'executed',
        target_difference='Same geometric M, coordinates and magnetization; S5-L01 H contains ideal axial bias while actual CoilROM contains full-coil bias. This test projects a learned-field error onto its genuine incremental current port; it does not identify those two Hamiltonians or claim a resulting closed-loop simulation.',
        constraints=dict(current_bound_A=model.coil_config['current_bound_A'],slew_bound_A_s=model.coil_config['slew_bound_A_s'],
            magnetic_point_field_bound_T=allocator.field_bound,magnetic_point_gradient_frobenius_bound_T_per_m=allocator.gradient_bound),
        bias_feasibility=scope,rows=rows,source_sha256_before=before,source_sha256_after=after,
        source_unchanged=before==after,learning_result_sha256=sha(OUT/'S5_L01_results.json'),
        limits=['magnetic input cannot cancel configuration-velocity error','static requested decision-state allocation over a declared0.25s window, not a dynamic sampled controller',
            'field/gradient limits checked only at actual magnetic integration points','rank tolerance defines a numerical effective image; not global controllability',
            'all optimizer failures retained; no infeasible current substituted as a success'],
        wall_seconds=time.perf_counter()-start)
    (OUT/'S5_L02_coil_reachability.json').write_text(json.dumps(result,indent=2)+'\n')
    np.savez_compressed(OUT/'S5_L02_allocated_currents_fields.npz',**arrays)
    fields=['kind','seed','split','index','status','rank','required_force_norm','orthogonal_force_residual','unavoidable_configuration_field_error','total_field_error_before','force_error_after','total_field_error_after','peak_current_A','maximum_B_T','maximum_G_T_per_m']
    with (OUT/'S5_L02_coil_reachability.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows({k:r.get(k) for k in fields} for r in rows)
    print(json.dumps(dict(status=result['status'],rows=len(rows),failures=sum(r['status']!='executed' for r in rows),source_unchanged=before==after,wall_seconds=result['wall_seconds']),indent=2))


if __name__=='__main__':main()
