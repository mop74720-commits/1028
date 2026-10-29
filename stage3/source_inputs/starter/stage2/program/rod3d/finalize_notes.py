"""Insert completed numerical evidence into the human-readable research note."""
from pathlib import Path
import csv
import json
import os
import platform
import numpy as np

ROOT=Path(__file__).resolve().parent
RESULTS=ROOT.parents[1]/'results'/'rod3d'
NOTE=ROOT.parents[1]/'notes'/'rod3d.md'


def main():
    analysis=json.loads((RESULTS/'analysis.json').read_text())
    summaries={s['case']:s for s in analysis['summaries']}
    lines=['## 9. 已完成的实际计算结果','',
           r'以下均由保存的原始轨迹计算；主跟踪窗口为 $t\in[0.5,2]\,\mathrm s$，目标是同一三维尖端位置，误差包含轴向几何缩短。不同分支的工程限制与模型层级不得混在一起解释。','',
           '| 分支 | 段数 | 步长/μs | 尖端RMSE/mm | 能量—外功归一残差 | 耗时/s |','|---|---:|---:|---:|---:|---:|']
    controls=[('uncontrolled_n32_h10us','无磁控制'),('feedforward_n32_h10us','静态顺应度前馈'),('position_feedback_n32_h10us','前馈＋位置反馈'),('position_feedback_n64_h5us','前馈＋位置反馈'),('womersley_position_feedback_n32_h10us','同流量局部Womersley'),('coil_allocated_n32_h10us','仿射线圈模型'),('full_biot_savart_coils_n32_h10us','完整线圈场，原点分配'),('full_biot_savart_coils_n64_h5us','完整线圈场，原点分配'),('full_biot_savart_tube_constrained_n32_h10us','完整场，管状域采样约束，ZOH'),('full_biot_savart_tube_constrained_ramped_n32_h10us','完整场，采样约束，连续电流斜坡')]
    for name,label in controls:
        s=summaries[name]
        lines.append(f"| {label} | {s['n_elements']} | {s['dt_s']*1e6:g} | {s['tip_rmse_after_ramp_m']*1e3:.6f} | {s['energy_work_residual_scaled']:.3e} | {s['wall_time_s']:.2f} |")
    lines+=['','完整线圈原点分配在数值上有小能量—外功残差，但违反工程场界并表现出显著控制模型失配；因此不能把该列当作已满足场约束的实现。最终受约束连续斜坡支路通过所检查的约束，但跟踪精度仍低于理想场。该性能差距是本轮发现，不删去。','',
            '### 9.1 学习前馈向真实三维杆的转移','',
            '| 前馈模型 | 32段RMSE/mm | 64段RMSE/mm | 64段最大接触穿透/μm |','|---|---:|---:|---:|']
    for model,label in [('linear','线性ROM'),('analytic','解析残差字典'),('complex','可训练复网络'),('truth','精确低维ROM函数')]:
        a=summaries[f'learned_{model}_n32_h10us'];b=summaries[f'learned_{model}_n64_h5us']
        lines.append(f"| {label} | {a['tip_rmse_after_ramp_m']*1e3:.6f} | {b['tip_rmse_after_ramp_m']*1e3:.6f} | {b['max_contact_penetration_m']*1e6:.3f} |")
    lines+=['','复网络优于这次解析残差字典，但没有优于线性ROM或精确低维函数。不能据此宣布“神经网络必然提升控制”。线性与精确低维结果接近，说明此小变形目标下非线性修正并未成为决定性收益。所有四类前馈均受到同一物理场输入和同一位置反馈约束；这里只验证理想场下的跨模型转移，没有把这些结果冒充实际线圈实现的误差。','',
            '### 9.2 网格、步长与保守扭转','',
            '| 细化对象 | 相邻差1 | 相邻差2 | 观察阶 |','|---|---:|---:|---:|']
    for key,label,scale,unit in [('space','平滑工况16→32→64段',1e6,'μm'),('time','32段10→5→2.5μs',1e9,'nm'),('contact_space','接触工况16→32→64段',1e6,'μm')]:
        g=analysis[key];errors=[x['centerline_space_time_rms_difference_m']*scale for x in g['pairs']]
        lines.append(f"| {label} | {errors[0]:.6f} {unit} | {errors[1]:.6f} {unit} | {g['observed_successive_difference_order']:.5f} |")
    lines+=['',r'相邻差为中心线在时间及参考弧长上的RMS差，并非与精确PDE解的误差。完整开放工况实际显示约一阶时间收敛，不能套用无耗散Verlet的二阶标签。空间误差明显大于所测时间误差。能量—外功归一残差在10/5/2.5μs之间约保持 $2.88\times10^{-6}$；它小但没有继续随步长收缩，不能据此声称精确能量守恒。','',
            '| 纯扭转步长/μs | 保存时刻最大相对能量缺陷 | 保存时刻最大SO(3)正交缺陷 |','|---|---:|---:|']
    for v in analysis['conservative_torsion']['values']:
        lines.append(f"| {v['dt_s']*1e6:g} | {v['max_relative_energy_defect']:.6e} | {v['max_SO3_defect']:.3e} |")
    orders=analysis['conservative_torsion']['orders']
    lines += ['',f"纯扭转能量缺陷的相邻观察阶为 {orders[0]:.4f}、{orders[1]:.4f}。这是受限保守诊断，不能扩展为整个流—接触—反馈系统的辛性或KAM证明。扭转/多频激励日志中的通用tip_error列不作为跟踪性能指标。",'',
              '### 9.3 接触与罚刚度敏感性','',
              '| 工况 | 段数 | 罚系数 | 最大求积点穿透/μm | 最大总法向力/μN |','|---|---:|---:|---:|---:|']
    for name in ['contact_stress_n16_h5us','contact_stress_n32_h5us','contact_stress_n64_h5us','contact_penalty_20000_n64_h5us','contact_penalty_200000_n64_h5us']:
        s=summaries[name];cfg=json.loads((RESULTS/name/'parameters.json').read_text());stiff=cfg['lumen']['contact_penalty_N_per_m_power_2p5']
        lines.append(f"| 不可行目标压力测试 | {s['n_elements']} | {stiff:g} | {s['max_contact_penetration_m']*1e6:.3f} | {s['max_total_contact_normal_N']*1e6:.3f} |")
    contact=np.genfromtxt(RESULTS/'contact_stress_n64_h5us'/'diagnostics.csv',delimiter=',',names=True)
    lines+=['',f"64段基础接触算例中，保存时刻接触耗散功率最大值为 {contact['power_contact_dissipative_W'].max():.3e} W，Coulomb上界数值超量最大为 {contact['friction_inequality_excess_N'].max():.3e} N；流体机械功率范围为 [{contact['power_flow_W'].min():.3e},{contact['power_flow_W'].max():.3e}] W。接触耗散与流体供能已被区分。提高罚刚度减小穿透，但未建立严格硬不穿透条件。",'',
            '### 9.4 工程密度/耗散率敏感性','',
            '| 密度/(kg/m³) | 耗散率/s⁻¹ | 32段RMSE/mm |','|---:|---:|---:|']
    for name in ['density_1200_n32_h10us','position_feedback_n32_h10us','density_2400_n32_h10us','damping_1_n32_h10us','damping_4_n32_h10us']:
        s=summaries[name];lines.append(f"| {s['density_kg_m3']:g} | {s['damping_rate_s_inv']:g} | {s['tip_rmse_after_ramp_m']*1e3:.6f} |")
    lines+=['','这些差异量化了缺少实测密度/耗散数据的影响，不把工程取值升级为实测材料参数。','',
            '### 9.5 完整线圈约束的最终可核查结果','']
    c=analysis['continuous_slew_coil_constraints']
    lines += [f"最终连续电流支路的每线圈幅值最大 {c['actual_current_amplitude_max_A']:.9g} A，几乎处处的电流斜率最大 {c['actual_continuous_current_slew_max_A_per_s']:.12g} A/s，电流连接点不连续缺陷为 {c['current_continuity_defect_A']:.3e} A。{c['allocation_calls']} 次受约束分配全部收敛，无可行电流回退；归一化采样约束数值超量最大 {c['maximum_normalized_sampled_constraint_violation']:.3e}。",'',
              f"在 {c['actual_node_checks']} 个控制检查时刻，实际杆节点场峰值 {c['max_actual_node_B_T']*1e3:.6f} mT、梯度范数峰值 {c['max_actual_node_G_frobenius_T_per_m']:.8f} T/m；分别低于5 mT、0.03 T/m。实际节点距精确圆导线最小 {c['min_actual_node_distance_to_exact_wire_m']*1e3:.5f} mm。387个工作域采样点距导线最小5.87 mm；整个指定管状域到导线的保守几何距离下界4.49 mm。该几何界保证所定义管状域不包含线圈导线，但不把离散场幅值检查升级为连续空间全域场界。",'',
              'ZOH支路只有相邻样本电流差商的20 A/s约束；其电流跳变不能具有有限连续时间导数。最终斜坡支路用连续分段线性电流替代ZOH，因而真正满足几乎处处的速率界。由于磁场和梯度关于电流线性、范数约束集合凸，两个可行电流端点间的整条线段在每一个固定空间采样点仍可行。这是对执行器采样场约束的明确推导，不是对机械积分器辛性的声明。','',
              '### 9.6 相同流量的Womersley改进','']
    w=analysis['womersley_profile'];d=analysis['flow_closure_difference']
    lines += [f"Womersley数为 {w['alpha']:.8f}。4097点径向查表的壁面速度为零，截面流量积分最大绝对误差为 {w['volume_flow_max_absolute_error_m3_s']:.3e} m³/s；复形状插值最大相对误差 {w['table_relative_max_complex_shape_error']:.3e}，独立径向有限差分代入直管谐波动量方程的相对残差 {w['finite_difference_straight_tube_NS_relative_residual']:.3e}。中心振荡相对平均流量相位为 {w['center_harmonic_phase_relative_to_mean_rad']:.6f} rad。",'',
              f"保持完全相同的流量波形和机械/控制参数后，中心线时空RMS变化为 {d['centerline_space_time_rms_difference_m']*1e6:.6f} μm，尖端时间RMS位置变化为 {d['tip_time_rms_difference_m']*1e6:.6f} μm。该算例跟踪RMSE变化小，并不证明瞬时抛物线在其他频率、管径或目标下均充分准确。映射到弯管切向仍是局部近似，流体压力、附加质量和双向FSI仍未由此补齐。"]
    cpu='unknown'
    for line in Path('/proc/cpuinfo').read_text().splitlines():
        if line.startswith('model name'):cpu=line.split(':',1)[1].strip();break
    hardware=dict(cpu_model=cpu,machine=platform.machine(),platform=platform.platform(),logical_cpu_count_reported=os.cpu_count(),
                  affinity_cpu_count=len(os.sched_getaffinity(0)),
                  timing_caveat='Shared container, concurrent independent cases and JIT/cache warm-up; wall times are audit data, not a controlled speed comparison',
                  main_import_policy='model.py sets OMP_NUM_THREADS=1 before importing NumPy; same-order final probe reports NumPy OpenBLAS1 and SciPy OpenBLAS1',
                  full_coil_original_policy='run_biot_savart.py imports NumPy before the OMP setting; exact historical pool size was not recorded per case. Same-order final probe reports9/1, which is not substituted for the historical unknown size.',
                  constrained_final_policy='OPENBLAS_NUM_THREADS=1, MKL_NUM_THREADS=1, OMP_NUM_THREADS=1 explicitly before imports; final probe reports1/1',
                  constrained_first_record='First completed run observed17 process threads and took130.749s; preserved separately. Final fixed-thread repeat took65.351s and reproduced tracking to roundoff.')
    Path(RESULTS/'runtime_context.json').write_text(json.dumps(hardware,indent=2))
    lines += ['','### 9.7 计算环境与耗时解释','',f"硬件报告为 {cpu}，{platform.machine()}；Python及依赖精确版本见每案environment.json。主套件、学习转移与Womersley按导入顺序在NumPy前设置OMP_NUM_THREADS=1，终局复查NumPy/SciPy OpenBLAS均为1线程。原始完整Biot–Savart脚本在设置OMP前导入NumPy，历史每次线程池大小未逐案记录，不能事后编造；相同导入顺序的终局复查为9/1线程，仅作环境诊断。最终受约束ZOH及连续斜坡显式固定两套BLAS均为1线程。",'',
              '表内耗时包含当次初始化、必要JIT与并行任务竞争，不是受控硬件性能排行榜。首次受约束计算观察到17个进程线程，耗时130.749 s；随后固定BLAS单线程复算耗时65.351 s，跟踪结果在舍入范围一致。首次完整结果作为执行记录保留，未作为额外独立科学样本计数。完整说明见runtime_context.json。','',
              '本轮形成的是可复算的分层研究平台和多项明确的正、负结果。完整双向FSI、插入边界、患者/空间站数据校准、真实线圈硬件带宽热设计，以及带控制非光滑全系统的稳定性、结构保持与KAM定理仍需分别完成，不能由当前数值结果代替证明。']
    text=NOTE.read_text();a=text.index('<!-- COMPUTED_RESULTS_BEGIN -->');b=text.index('<!-- COMPUTED_RESULTS_END -->')
    text=text[:a]+'<!-- COMPUTED_RESULTS_BEGIN -->\n\n'+'\n'.join(lines)+'\n\n'+text[b:]
    NOTE.write_text(text)
    with (RESULTS/'timings.csv').open('w',newline='') as file:
        writer=csv.writer(file);writer.writerow(['case','wall_time_s','blas_policy','hardware'])
        for s in summaries.values():
            policy='explicit1/1' if 'tube_constrained' in s['case'] else ('historical_pool_size_not_recorded' if s['case'].startswith('full_biot_savart_coils') else 'OMP1_before_NumPy; final same-order probe1/1')
            writer.writerow([s['case'],s['wall_time_s'],policy,cpu])
    print('Final computed tables written to '+str(NOTE))


if __name__=='__main__':main()
