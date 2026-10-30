"""Reviewer-authored per-formula decisions; bilingual display expressions checked."""
from pathlib import Path
import csv,json,re
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'stage6/fusion_reconciliation'
S5='stage5/proofs/';S6='stage6/fusion_reconciliation/'
# id within chapter, fourth-stage anchor, verdict, concrete inherited responsibility.
CONTROL={
5:('B16','同未知中点实际反馈','Correct for the stated two-mode potential and exact force realization; variable mass requires the full Hamiltonian gradient, not replacement of N by M(q)^-1 in only one equation.','integrators_full_coil.md:39','stage5/program/closed_loop.py:113'),
17:('B22','力与离散增量','U_A is force and h(0,U_A) is its phase increment. The formula is not a 24D actuator map.','integrators_full_coil.md:16','stage5/program/coil_rom.py:131'),
23:('B17','合法比例阻尼加权式','Correct only for constant proportional momentum damping; no exact-exponential claim for ordinary midpoint or collocated full-coil feedback.','integrators_full_coil.md:106','stage5/program/closed_loop.py:155'),
36:('B22','同K控制闭性判据','Correct locally on simply connected domain at each fixed time: d(K G a_u)=0 is necessary and sufficient while retaining the one-form; actual reachability remains separate.','integrators_full_coil.md:55','stage5/program/closed_loop.py:100'),
46:('B19','补偿后理想映射结构命题','Correct conditional theorem: local unique branch plus genuinely conservative residual; nonzero constant residual damping uses weighted scheme. No floating-point exactness claim.','integrators_full_coil.md:94','stage5/program/closed_loop.py:155'),
49:('B17','共形因子','Weighted exact implicit map has exp(-delta_gamma h); ordinary damped midpoint has a different rational factor.','integrators_full_coil.md:106','stage5/program/closed_loop.py:155'),
58:('B19','恰当辛原函数','The explicit primitive Pbar*dQ-S on a single-valued central branch establishes exactness. Angle-domain periodicity is an additional requirement.','integrators_full_coil.md:94','stage3/program/rom_integrators.py:15'),
67:('B22','实际力误差功率','Correct for stated constant-N Hamiltonian; in full ROM replace N Y by actual H_P, and use realized G_coil i.','integrators_full_coil.md:24','stage5/program/coil_rom.py:150'),
79:('B23','完整增量残差','Correct residual norm of actual time-dependent closed loop; Newton correction is not the residual, and 24D infinity-to-Euclidean factor is sqrt(24).','integrators_full_coil.md:125','stage5/program/closed_loop.py:113'),
88:('B23','有限时间收敛命题','Conditional proof is valid with common smooth domain, derivative/Lipschitz bounds, self-mapping margin and hL/2<1. No certified full-vascular constants supplied.','integrators_full_coil.md:125','stage5/program/closed_loop.py:113'),
92:('B23','误差单步递推','Subtract exact-solution midpoint local defect O(h^3), apply one fixed norm Lipschitz bound at average endpoints; coefficient order is correct.','integrators_full_coil.md:125','stage5/program/closed_loop.py:113'),
100:('B23','求解误差累积','Correct h^2+eta/h for uniformly bounded increment residuals; fixed absolute tolerance does not guarantee arbitrarily fine asymptotic order.','integrators_full_coil.md:125','stage5/program/closed_loop.py:113'),
111:('B23','递推证明中间不等式','Triangle inequality and hL/2(e_next+e_now) are correct; constant must cover time derivatives for nonautonomous f.','integrators_full_coil.md:125','stage5/program/closed_loop.py:113'),
126:('B20','双参考误差分离','Valid triangle inequality. Same-field integration error and original/nominal model gap answer distinct questions.','birkhoff_transport.md:141','stage5/program/run_transport_experiments.py:174'),
133:('B23','Gronwall模型差','Valid under common-domain sup field error rho and Lipschitz bound L; L=0 limit rho*t. Point samples do not certify these uniform constants.','birkhoff_transport.md:147','stage5/program/run_transport_experiments.py:174')}
EXPERIMENT={
26:('B17','G1/G2两模态场','Exact stated full-cosine two-mode diagnostic; not the 12-configuration-variable ROM. Existing data were not transferred as 3D evidence.','stage5/program/closed_loop.py:38','integrators_full_coil.md:5','reproduction/general_birkhoff_experiments/magnetic.py:15'),
45:('B17','比例阻尼独立图场','Correct time derivative of P=exp(gamma*t)Y; direct chart and weighted formula independently agree. Full variable-mass canonical lift is already inherited in stage5.','stage5/program/closed_loop.py:155','integrators_full_coil.md:106','reproduction/general_birkhoff_experiments/magnetic.py:71'),
74:('B07','G3点正则变换','Cotangent lift P=DQ^-T p preserves P dQ=p dq; domain excludes 1+0.15q1=0. Explicit known conjugacy is data of this artificial 4D test.','stage5/program/moser_chart.py:36','birkhoff_transport.md:104','reproduction/general_birkhoff_experiments/synthetic.py:25'),
83:('B20','G3机械矩阵','Specified dimensionless positive mechanical matrices, not catheter material values. M(q)=DQ^T M0 DQ genuinely varies but is an artificial conjugate model.','stage5/program/coil_rom.py:114','birkhoff_transport.md:5','reproduction/general_birkhoff_experiments/synthetic.py:15'),
100:('B20','G3已知线性共轭场','Canonical cotangent lift converts the declared variable-mass model to A_s exactly; full H_q derivatives retained by symbolic mechanical expression. The true 3D ROM has no supplied A_s conjugacy.','stage5/program/coil_rom.py:114','birkhoff_transport.md:63','reproduction/general_birkhoff_experiments/synthetic.py:54'),
115:('B07','G3指定二形式和平方根图','K=e^-AtT K0 e^-At is exact for known A; real principal square root needs the selected branch, checked numerically. Exponentials are required paid construction inputs, not a general 3D transport solution.','stage5/program/moser_chart.py:19','birkhoff_transport.md:104','reproduction/general_birkhoff_experiments/synthetic.py:81'),
129:('B17','G3非自治图Cayley更新','Uses L=Tdot*T^-1+T A T^-1 with Sylvester-derived Tdot, then Cayley midpoint. It does not use exp(Ah) as the numerical state step. Stage5 numerical Moser is a distinct reusable construction for 24D.','stage5/program/run_transport_experiments.py:62','birkhoff_transport.md:123','reproduction/general_birkhoff_experiments/synthetic.py:91'),
146:('B22','G3理想全驱动补偿','The ideal 2D generalized force is algebraically correct and gives the declared C_d,K_s+K_p. No magnetic reachability, coil constraints or learned decoder are included.','stage5/program/coil_rom.py:150','coil_energy_ports.md:1','reproduction/general_birkhoff_experiments/synthetic.py:247'),
197:('B20','G1-G3完整细网格表','Independent stage6 rerun checks all 56 grid rows; endpoint errors agree within 4.96e-17. The tables verify declared 4D models only, not new 3D physical conclusions.','stage5/program/run_transport_experiments.py:174','birkhoff_transport.md:141','reproduction/general_birkhoff_experiments/run_all.py:14'),
224:('B07','G3冷暖成本表','Cold chart setup includes 2Ns+1 exp/sqrt and Ns Sylvester solves; warm timings explicitly reuse cache. Numbers are implementation timings, not universal speed theorem or free exact-flow oracle.','stage5/program/run_transport_experiments.py:174','birkhoff_transport.md:63','reproduction/general_birkhoff_experiments/common.py:125')}

def main():
    index=json.loads((BASE/'results/manuscript_index.json').read_text())['review_units']
    matrix={row['id']:row for row in csv.DictReader((ROOT/'stage4/audit/full_inheritance_matrix.csv').open(encoding='utf-8-sig'))}
    selected=[u for u in index if Path(u['source']).name in {'general_birkhoff_results.tex','supp_general_experiments.tex','controlled_analysis.tex'}]
    en=[u for u in selected if u['language']=='english'];zh=[u for u in selected if u['language']=='chinese'];assert len(en)==len(zh)==26
    rows=[]
    for a,b in zip(en,zh):
        chapter=Path(a['source']).name;line=a['line_start'];same=''.join(a['tex'].split())==''.join(b['tex'].split())
        if a['kind']=='display':assert same,(a['id'],b['id'])
        fusioncode='not-applicable: conditional mathematical proof'
        if chapter=='controlled_analysis.tex':
            mid,topic,verdict,proof,code=CONTROL[line]
            inherited='Full variable-mass proof and actual full-coil implementation already present in stage5; explicit-time implementation added here where relevant.'
            three='yes: existing stage5 24D branch; nonautonomous update additionally measured in stage6'
            generalized='conditional dimension-independent theorem; no uniform 3D vascular certificate'
            reuse='yes: stage5 implicit_midpoint, full feedback and exact central generator'
        elif chapter=='supp_general_experiments.tex':
            mid,topic,verdict,code,proof,fusioncode=EXPERIMENT[line]
            inherited='Historical special-case algorithm retained; corresponding 3D responsibility implemented by full geometry and numerical Moser, not by importing G3 known conjugacy.'
            three='no for this exact 4D test; separate stage5 and stage6 actual 24D evidence only'
            generalized='no: this formula/data does not prove general robot transfer'
            reuse='historical original algorithm rerun unchanged; 24D code reuses stage5 numerical Moser/cache'
        else:
            mid,topic,verdict,code,proof,fusioncode=EXPERIMENT[197]
            inherited='Representative comparison table retained and freshly reproduced; not silently relabeled as 3D evidence.'
            three='no: table is old two-mode/artificial 4D';generalized='no';reuse='yes: original G1-G3 scripts rerun unchanged'
        m=matrix[mid]
        for unit,counterpart in [(a,b),(b,a)]:
            row={k:unit[k] for k in ['id','source','line_start','line_end','labels','language']}
            row.update(topic=topic,original_1025=m['original_location'],old_v10=m['old_v10'],general_birkhoff=m['general_birkhoff'],stage4=f'stage4/audit/full_inheritance_matrix.csv#{mid}; '+m['evidence'],
                stage5_code=code,stage5_proof=S5+proof,stage5_results='stage5/results/closed_loop/results.json; stage5/results/transport/fullcoil_collocated/inverse_verified.json',
                fusion_verdict=verdict,stage5_inheritance=inherited,
                stage6_action='Preserve verified formula and original scope; independent G1-G3 replay, plus nonautonomous full-coil source-gauge recurrence and actual same-time midpoint/Moser bridge.',
                new_code=S6+'program/nonautonomous_transport.py:24; '+S6+'program/run_nonautonomous_experiment.py:15',
                tests=S6+'tests/test_nonautonomous_transport.py; '+S6+'results/algorithms/fusion_original/run_validation.json',
                evidence=S6+'results/algorithms/fusion_original/comparison.json; '+S6+'results/algorithms/time_gain_r2_completed.json; supplied-archive-member:'+fusioncode,
                remaining='No global time-chart transitions, arbitrary contact/FSI, actuator realization of ideal G3 force or new 3D KAM certificate. Full convergence constants require domain-wide validation.',
                review_note=f"Bilingual counterpart {counterpart['id']}: "+('displayed mathematical TeX identical after whitespace normalization; surrounding hypotheses read in both languages.' if same else 'statement/table numerical entries and surrounding hypotheses manually compared in both languages; prose differs by translation.'),
                material_exists='yes: SHA-verified supplied archive',mentioned='yes',derivation_inherited=('yes: dimension-independent proof preserved with stated conditions' if chapter=='controlled_analysis.tex' else 'preserved for historical test; not promoted to a 3D generalization'),algorithm_reused=reuse,verified_on_3d=three,generalization_proved=generalized)
            rows.append(row)
    folder=BASE/'annotations';folder.mkdir(exist_ok=True)
    (folder/'algorithms.json').write_text(json.dumps(dict(reviewer_scope='controlled_analysis, general_birkhoff_results, supp_general_experiments; all 52 English/Chinese indexed units',rows=rows),ensure_ascii=False,indent=2)+'\n')
    print(len(rows))
if __name__=='__main__':main()
