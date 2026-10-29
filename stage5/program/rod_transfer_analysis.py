"""Summarize actual rod outputs, allocator failures and model differences."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'stage5/results/rod_transfer'


def main():
    execution = json.loads((OUT/'execution.json').read_text())
    result = dict(status='postprocessing_of_independently_executed_trajectories', cases=[],
                  refinement=json.loads((OUT/'refinement.json').read_text()),
                  failures_preserved='initial_allocator_failure/ contains the complete failed time-refinement batch; smoke_failed_api_execution.json preserves the repaired API failure.')
    for summary in execution['summaries']:
        case = OUT/summary['case']
        audit = json.loads((case/'current_constraint_audit.json').read_text())
        feedback = json.loads((case/'feedback_updates.json').read_text())
        repairs = {round(x['time_s'], 12): x for x in audit['feasibility_repair_log']}
        with np.load(case/'trajectory.npz') as data:
            flow_norm = np.linalg.norm(np.sum(data['force_flow'], axis=1), axis=1)
            initial_pen = float(data['contact_penetration_m'][0].max())
        losses, corrections = [], []
        previous = np.zeros(12)
        for item in feedback:
            target, requested = np.array(item['target_current_A']), np.array(item['requested_current_A'])
            repair = repairs.get(round(item['time_s'], 12))
            if repair and repair['segment_fraction']>0.:
                candidate = previous+(target-previous)/repair['segment_fraction']
                before = .5*float(np.dot(candidate-requested, candidate-requested))
                after = .5*float(np.dot(target-requested, target-requested))
                losses.append(after-before)
                corrections.append(repair['current_correction_norm_A'])
            previous = target
        record = dict(case=summary['case'], initial_penetration_m=initial_pen,
                      max_resultant_flow_force_N=float(flow_norm.max()),
                      min_ideal_incremental_power_W=min(x['ideal_incremental_power_W'] for x in feedback),
                      max_projected_incremental_power_W=max(x['projected_incremental_power_W'] for x in feedback),
                      max_ramp_start_incremental_power_W=max(x['current_start_incremental_power_W'] for x in feedback),
                      projection_nonconverged=audit['optimizer_nonconverged'],
                      fallback_count=audit['fallback_count'],
                      repair_count=audit['analytic_feasibility_repairs'],
                      largest_repair_current_norm_A=max(corrections, default=0.),
                      largest_repair_objective_change_A2=max(losses, default=0.),
                      feasibility_minimum_margin=-audit['maximum_sampled_constraint_violation'])
        result['cases'].append(record)
    matched = OUT/'matched/model_difference.json'
    if matched.exists():
        result['matched_ROM_Cosserat'] = json.loads(matched.read_text())
    (OUT/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')

    fig, axes = plt.subplots(2,2,figsize=(10,7),constrained_layout=True)
    for name,label in [('baseline_n32_h10us','Nominal, 32 segments'),
                       ('port_n32_h5us','Current-port feedback, 32'),
                       ('port_n64_h5us','Current-port feedback, 64')]:
        d=np.genfromtxt(OUT/name/'diagnostics.csv', delimiter=',', names=True)
        axes[0,0].plot(d['time_s'],d['tip_x_m']*1e3,label=label)
        axes[0,1].plot(d['time_s'],d['tip_y_m']*1e3,label=label)
        axes[1,0].plot(d['time_s'],d['tip_error_m']*1e3,label=label)
        residual=d['mechanical_energy_J']-d['mechanical_energy_J'][0]
        for key in ['magnetic','flow','contact_dissipative','residual_g','structural_damping']:
            residual-=d['work_'+key+'_J']
        axes[1,1].plot(d['time_s'],residual,label=label)
    axes[0,0].plot(d['time_s'],d['target_x_m']*1e3,'k--',label='Target')
    axes[0,1].plot(d['time_s'],d['target_y_m']*1e3,'k--',label='Target')
    labels=['Tip x / mm','Tip y / mm','3D tip error / mm','Mechanical energy - work / J']
    for ax,label in zip(axes.flat,labels):
        ax.set(xlabel='Physical time / s',ylabel=label);ax.grid(alpha=.25)
    axes[0,0].legend(fontsize=8)
    fig.savefig(OUT/'tracking_and_power.svg');plt.close(fig)

    fig,axes=plt.subplots(1,3,figsize=(12,3.5),constrained_layout=True)
    d=np.genfromtxt(OUT/'port_contact_n32_h5us/diagnostics.csv',delimiter=',',names=True)
    axes[0].plot(d['time_s'],d['max_quadrature_penetration_m']*1e6)
    axes[0].set(ylabel='Penetration / micrometre')
    axes[1].plot(d['time_s'],d['contact_normal_total_N']*1e6)
    axes[1].set(ylabel='Total normal contact / micronewton')
    for name,label in [('port_n32_h5us','Main lumen'),('port_contact_n32_h5us','Narrow-lumen stress')]:
        dd=np.genfromtxt(OUT/name/'diagnostics.csv',delimiter=',',names=True)
        axes[2].plot(dd['time_s'],dd['true_G_at_nodes_frobenius_max_T_per_m'],label=label)
    axes[2].axhline(.03,color='k',linestyle='--',label='Limit');axes[2].set(ylabel='Observed full-coil gradient / T m^-1')
    for ax in axes:
        ax.set_xlabel('Physical time / s');ax.grid(alpha=.25)
    axes[2].legend(fontsize=8)
    fig.savefig(OUT/'contact_and_field.svg');plt.close(fig)
    print(json.dumps(dict(cases=len(result['cases']),matched_reference=matched.exists(),status='passed')))


if __name__ == '__main__':
    main()
