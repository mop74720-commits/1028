"""Export only completed, independently checked transport evidence to the ledger.

This does not run experiments, fit missing results, or upgrade a theorem from
numerical tolerances. It refuses partial main runs and keeps all prior manifests.
"""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'stage5/results/ledgers/transport_final_updates.json'

def read(path):
    return json.loads((ROOT/path).read_text())

def main():
    synthetic='stage5/results/transport/synthetic/inverse_verified.json'
    coil='stage5/results/transport/fullcoil_collocated/inverse_verified.json'
    domain='stage5/results/transport/inverse_verified_jsonfixed_domains.json'
    power='stage5/results/transport/inverse_verified_comparison.json'
    tangent='stage5/results/transport/inverse_verified_tangents.json'
    reference_bridge='stage5/results/transport/inverse_verified_reference_bridge.json'
    sd,cd,dd=map(read,(synthetic,coil,domain))
    if sd['status']!='completed' or len(sd['rows'])!=9:
        raise ValueError('synthetic three-order/three-grid run is incomplete')
    if cd['status']!='completed' or len(cd['rows'])!=6:
        raise ValueError('same full-coil closed-loop two-order/three-grid run is incomplete')
    if dd['status']!='completed' or len(dd['probes'])!=27:
        raise ValueError('domain probes incomplete')
    if sd['initial_state']!=cd['initial_state'] or sd['duration_tau']!=cd['duration_tau']:
        raise ValueError('declared common initial condition/window changed')
    power_data=read(power)
    if power_data['status']!='completed' or len(power_data['physical_power_rows'])!=6:
        raise ValueError('same-field power and Ku comparison incomplete')
    if max(row['field_difference_2'] for row in power_data['same_field_verification'])>1e-12:
        raise ValueError('graph and direct full-coil modules do not represent the same declared original field')
    read(tangent)
    if read(reference_bridge)['status']!='completed':
        raise ValueError('cross-version same-field reference comparison incomplete')
    for model in ('synthetic','fullcoil'):
        if read(f'stage5/results/transport/backend_validation_{model}_inverse.json')['status']!='completed':
            raise ValueError('independent derivative/gauge verification incomplete')
    sampled='stage5/results/closed_loop/sampled_warmfix/matched_initial_bias/sampled_jacobian.json'
    comparison='stage5/results/closed_loop/sampled_warmfix/matched_initial_bias/version_comparison.json'
    sm,comparison_data=read(sampled),read(comparison)
    if sm['status']!='completed' or comparison_data['status']!='actual_new_allocator_map_recomputed_and_compared':
        raise ValueError('current-source sampled map comparison incomplete')
    if not all(row['original_initial_state_and_protocol_identical'] for row in comparison_data['rows']):
        raise ValueError('sampled old/new protocols not strictly matched')
    proof='stage5/proofs/birkhoff_transport.md; stage5/proofs/corrected_mathematics.md'
    code='stage5/program/transport_native.py; stage5/program/transport_cache.py; stage5/program/moser_chart.py'
    evidence='; '.join((synthetic,coil,domain,power,tangent,reference_bridge,
        'stage5/results/tests/latest.json',
        'stage5/results/transport/backend_validation_synthetic_inverse.json',
        'stage5/results/transport/backend_validation_fullcoil_inverse.json',
        'stage5/results/high_derivatives/transport.json'))
    common_missing=('当前只为固定原点/半径.002的自治光滑局部构造；空间缓存、时间截断和数值图仍有独立误差。'
                    '非自治脉动血流/接触、跨窗口重展开过渡、统一解析域/逆界、全物理误差和新KAM尚未完成。')
    rows={}
    def update(ids,**fields):
        for key in ids.split():rows.setdefault(key,{}).update(fields)
    update('B05 B06 B07 B20 B21 B22',stage5_source_code=code,
        stage5_proof=proof,stage5_evidence=evidence,
        stage5_generalization_proved='conditional_local：局部定理及有限实际样本；不宣称任意场全域构造',
        stage5_missing=common_missing,stage5_next_action=common_missing)
    update('B05',stage5_status='实际非比例24D场的一至三阶输运及同全coil闭环一至二阶实现并运行',
        stage5_full_derivation_inherited='yes_conditional：非自治幂递推恢复；实际自治raw a1–a3及source-gauge关系独立验证',
        stage5_algorithm_reused='yes_and_extended：真实变量质量ROM复用，高阶输运与空间jet缓存新增',
        stage5_verified_on_3d='yes_limited：9+6网格及独立原场/表示场参考；不是任意生理负载推广')
    update('B06',stage5_status='齐次一形式与有源规范的关系实际验证；截断不交换的末项保留',
        stage5_full_derivation_inherited='yes：sigma输运、a=a_prime−d sigma、B变化及有限截断末项完整推导',
        stage5_algorithm_reused='yes：raw a1/a2/a3与b_j−d sigma_j真实AD对照，源规范推进',
        stage5_verified_on_3d='yes_limited：前三阶系数关系与原场表示误差分别记录；不是规范消除全部误差')
    update('B07',stage5_status='真实24D Moser辅助流、逆图、状态/时间敏感度进入同场图中点',
        stage5_full_derivation_inherited='yes_local：辅助场、非退化充分界、逆图及chi_t完整恢复',
        stage5_algorithm_reused='yes_and_extended：继承Moser理论机制，24D高阶缓存/敏感度新增实现',
        stage5_verified_on_3d='yes_limited：插值lambda、逆复合、时间项、图容差细化及离域失败真实运行')
    update('B20',stage5_status='结构匹配、原场表示、空间缓存、参考误差和积分误差在同ROM分开测量',
        stage5_full_derivation_inherited='yes_conditional：K闭性与表示场相容、原场残差及变换场切线完整推导',
        stage5_algorithm_reused='yes：原f保持完整M，推进f_a与原f不混称',
        stage5_verified_on_3d='yes_limited：图匹配近机器精度不消除表示误差平台；r3总误差未必小于r2')
    update('B21',stage5_status='27域探测保存四次真实离域失败和两次预期域外拒绝；完整成本保存',
        stage5_full_derivation_inherited='yes_conditional：缓存球的充分留域/非退化界；浮点系数不是区间证书',
        stage5_algorithm_reused='yes：没有每步重置一形式或免费调用未知精确流',
        stage5_verified_on_3d='yes_negative：高阶固定时间展开未扩展为全局方法，离域明确拒绝')
    update('B22',stage5_status='共点磁反馈不保K0；同一真实闭环构造近似Ku并与普通中点分别比较',
        stage5_full_derivation_inherited='yes_conditional：完整反馈Jacobian及Ku表示场构造；原场相容有非零残差',
        stage5_algorithm_reused='yes：相同full-coil端口/物理偏导与反馈复合，图法推进近似表示场',
        stage5_verified_on_3d='yes_limited：真实24D同闭环/同Ku对照、磁功率和表示误差额外做功分别测量；不是受限36D采样映射的辛证明')
    update('B17',stage5_status='普通中点原场约二阶，与同full-coil场Ku图法实际比较；Ku近似场误差另报',
        stage5_evidence=evidence+'; stage5/results/closed_loop/results.json',
        stage5_missing='图法针对表示场二阶，原场仍有截断平台；没有性能优越性或长期留域证明')
    update('B23',stage5_evidence=evidence+'; stage5/results/closed_loop/results.json',
        stage5_missing='条件性有限时间界恢复；统一L/留域/图逆常数及真实流体接触/模型/分配误差尚未认证')
    update('B26 O026',stage5_evidence='stage5/results/closed_loop/independent_checks.json; '+sampled+'; '+comparison,
        stage5_status='真实磁Uk与完整反馈Jacobian进入中点；修复allocator后匹配36D初态重新审计',
        stage5_verified_on_3d='yes_limited：完整24D反馈和带电流记忆36D采样映射；非同一个结构定理',
        stage5_missing='活动集/电流记忆/秩亏与接触不满足普通24D辛/KAM条件；新力分配方向差分误差最高1.99e−6，不能将warmstart修复当Jacobian光滑/条件改善证明；旧严格初态比较失败保留')
    update('O018',stage5_status='原不相容候选明确拒收；实际非比例/真实磁闭环以局部相容表示场接入',
        stage5_proof=proof,stage5_source_code=code,stage5_evidence=evidence,
        stage5_verified_on_3d='yes_limited：原场残差明确非零，闭性/图匹配与原场精度分别报告',
        stage5_missing=common_missing)
    update('O022',stage5_status='原32固定初端链式修正及真实时变Moser图显式时间项均实现',
        stage5_proof=proof,stage5_source_code=code+'; stage5/program/corrected_identities.py#fixed_endpoint_rhs',
        stage5_evidence=evidence,stage5_verified_on_3d='yes_limited：rho_t/chi_t与混合状态时间敏感度真实积分',
        stage5_missing='本轮实际g来自Moser表示场；任意阶24D完整生成递推和共同解析域仍未完成')
    update('O027 B02',stage5_proof=proof,stage5_evidence=evidence,
        stage5_verified_on_3d='yes_limited：K=d a闭性及缓存球内非退化充分界/数值条件数；非全物理域证书',
        stage5_missing='二形式闭性不推出全域非退化；浮点域界未作有向舍入认证')
    rows['B12']=dict(rows['O022'])
    repaired={}
    for eid in ('E06','E07','E08','E09','E10','E12','E13'):
        repaired[eid]=dict(execution_evidence='stage5/results/corrected_identities/latest.json; '+evidence,
            remaining_or_missing=common_missing,
            stage5_verified_on_3d='yes_limited：完整24D局部图/真实闭环已实算；表示场与原场不等同',
            stage5_generalization_proved='conditional_local：完整数学修正与明确范围；不是全局物理/KAM推广')
    repaired['E06']['adopted_by_stage5_modules']='transport_native/cache实际构造闭二形式及对应B/f_a；原场逼近残差独立记录。错误原候选继续拒收。'
    repaired['E07'].update(adopted_by_stage5_modules='联合端点逆/横截/一般初始规范helper已验；24D Moser图/逆图/敏感度实际求解，局部条件数不冒称统一域认证。',
        source_code='stage5/program/corrected_identities.py#endpoint_gradient_jacobian; stage5/program/corrected_identities.py#reconstruct_flow_jacobian; stage5/program/corrected_identities.py#radial_generator_potential',
        tests='stage5/tests/test_corrected_identities.py#test_E07_endpoint_compatibility_transversality_not_Hessian_inverse; stage5/tests/test_corrected_identities.py#test_nonzero_initial_generator_gauge_and_endpoint_compatibility')
    repaired['E08'].update(adopted_by_stage5_modules='固定w生成递推和Central4已修正；实际高阶one-form输运系数进入ROM，但它们不是任意阶生成函数系数。',
        remaining_or_missing='一形式输运已高阶实算；一般24D生成函数高阶递推/截断重构的统一解析域与可控成本仍未完成。')
    repaired['E09']['adopted_by_stage5_modules']='fixed_endpoint_rhs修正原32；moser_chart积分rho_t与混合时间敏感度，实际g含完整显式时间项。'
    repaired['E10']['adopted_by_stage5_modules']='原非梯度阻尼候选拒收；原场改为局部Birkhoff表示场后采用合法图中点，原场残差不能省略。'
    repaired['E12']['adopted_by_stage5_modules']='实际cache K=K0+Dbᵀ−Db及图结构缺陷统一K0=-J/二形式半因子；独立闭性和非退化责任。'
    repaired['E13']['adopted_by_stage5_modules']='完整原f、B、a_t与K符号一致；原场e_B和表示场相容分别计算，保守/比例精确分支另作真实ROM回归。'
    for fields in repaired.values():
        if 'adopted_by_stage5_modules' in fields:
            fields['stage5_algorithm_reused']=fields['adopted_by_stage5_modules']
    # Keep the explicit next action synchronized with each revised missing
    # responsibility; do not retain an earlier "awaiting run" after it ran.
    previous={}
    for name in ('stable_branch_updates.json','learning_and_proof_updates.json'):
        for key,fields in read('stage5/results/ledgers/'+name)['inheritance'].items():
            previous.setdefault(key,{}).update(fields)
    for key,fields in rows.items():previous.setdefault(key,{}).update(fields)
    for key,fields in previous.items():
        if 'stage5_missing' in fields:
            rows.setdefault(key,{})['stage5_next_action']=fields['stage5_missing']
    manifest=dict(note='只引用完成的新inverse_backend运行；旧AD、离域、序列化、allocator和初态严格比较失败均保留。没有把P0局部验收等同整个第五阶段或完整机器人完成。',
                  inheritance=rows,repairs=repaired)
    serialized=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    if OUT.exists() and OUT.read_bytes()!=serialized:
        prior=OUT.read_bytes();digest=hashlib.sha256(prior).hexdigest()
        OUT.with_name('transport_final_updates_prior_'+digest[:12]+'.json').write_bytes(prior)
    OUT.write_bytes(serialized)
    print(json.dumps(dict(output=str(OUT.relative_to(ROOT)),updated_rows=len(rows),updated_repairs=len(repaired)),ensure_ascii=False))

if __name__=='__main__':main()
