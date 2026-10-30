"""Curated per-formula reconciliation, keyed to the shared exact source index.

The mathematical assessments below are manually specified; indexing a formula
does not certify it. EN/ZH labels were compared directly before sharing rows.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE='stage6/fusion_reconciliation/'
S5='stage5/proofs/chnn_kam_restored.md'
S4='stage4/audit/full_inheritance_matrix.csv'
O='stage4/audit/source_omml/original1025_indexed.json:'
OLD='stage4/audit/external_v10/sections/'
F='stage3/source_inputs/v10/v10_framework_20261028/english/sections/'

# label -> topic, original anchor, old exact evidence, stage4 ids, proof/code/result,
# mathematical assessment, actual stage5 inheritance, new action, outstanding.
entries={}
def add(label,topic,original,old,ids,proof,code,result,verdict,inheritance,action,remaining,kind):
    entries[label]=dict(topic=topic,original_1025=O+original,old_v10=old,stage4=S4+':'+ids,
                       stage5_proof=proof,stage5_code=code,stage5_results=result,
                       fusion_verdict=verdict,stage5_inheritance=inheritance,
                       stage6_action=action,remaining=remaining,kind=kind)

closed='stage5/program/closed_loop.py:113–178'
closed_result='stage5/results/closed_loop/results.json; stage5/results/closed_loop/verification.json'
learning='stage5/program/learning_models.py:23–40; stage5/program/run_learning_research.py:32–144'
learnresult='stage5/results/learning/S5_L01_protocol.json; stage5/results/learning/S5_L01_analytic_mechanical4_seed51001.pt'
budget='results/budgets/original_budget_recomputed.json'
newbudget='program/fusion_budget.py:17–104; results/budgets/actual_3d_majorants.json'
resonance='stage5/program/resonance_research.py:20–45'
resresult='stage5/results/resonance/S5_R01_results.json; stage5/results/resonance/S5_R02_results.json'

for label,topic,note in [
 ('num:matrix-data','人工常矩阵回归定义','人工M,K不交换；额外非比例Cg没有共同指数权重声明。'),
 ('num:matrix-benchmark','中点消元、加权结构、Central4阶数表','阶数/结构属于分别声明的保守与阻尼对象，不能跨对象合并。')]:
 add(label,topic,'p1037–1070',F+'analysis.tex:'+label,'CK23','stage5/proofs/corrected_mathematics.md:300–367; stage5/proofs/integrators_full_coil.md:39–104',closed,closed_result,note,'原36矩阵次序与非可分算法已进入真实3D full-coil；未把人工矩阵视作物理参数。','保留回归对象；历史复算由history_reproduction记录。','人工常矩阵结果不度量新ROM的空间/模态误差。','regression')
add('num:scales','更新后的2模态物理尺度','p0348–0362;p1082–1110',F+'analysis.tex:num:scales','CK10','stage5/notes/unified_model_contract.md','stage3/program/rom_bridge.py:4–17','stage5/results/learning/S5_L01_protocol.json',
    '这是新参数两模态梁，ν2=6.04585730；不是旧固定v10ν2≈6.152117504，更不是12模态ROM。','三维正则尺度另行建立并进入学习与full-coil，未沿用该数值。','读取实际ROM ν和S5 D并数值核对缩放，保存actual_3d_homological_gate.json。','三种模型参数和证书不可交换。','identity')
add('num:feature-gradient','单余弦势特征梯度','p0560–0598',F+'structure.tex:165–187','CK29',S5+':29–80',learning,learnresult,
    'd(sin(d·X)−d·X)是完整余弦尾项的正确梯度。','S5-L01的8749项机械字典与全复网络超过单系数实验；不删该回归。','复算原算法输入；新字典规范梯度与Torch独立对照。','单势系数不代表完整CHNN；多项式没有余弦全尾项。','feature')
add('num:feature','单参数合成残差定义','p0560–0598',OLD+'core_analysis.tex:70–140; '+F+'analysis.tex:num:feature','CK04,CK29',S5+':29–51',learning,learnresult,
    'β*=.2明确是合成压力设定；只有势系数和阻尼两参数。','S5-L01三个模型各三种子实际新训练；不称旧权重复现。','保留该历史低维算法，不取代真实24D checkpoint。','完整网络的复域误差与可达学习控制仍未认证。','feature')
add('num:regression','状态积分回归和归一化','p0506–0520;p0560–0598',OLD+'integral_comsol_to_kam.tex:14–72','CK16',S5+':53–81',learning,learnresult,
    '积分平衡符号正确；求积、端点、观测误差必须计入独立缺陷。','确定性积分/梯度误差证明恢复；S5训练采用真实ROM梯度标签，不是该历史积分数据。','原预算按原数据复算；缺误差的预算接口返回conditional。','新字典积分Gram与独立动态缺陷未计算。','gram')
add('num:fitted-values','β/γ冻结拟合值','p0560–0598',F+'analysis.tex:num:fitted-values','CK16,CK20',S5+':53–81',learning,learnresult,
    'βhat=.200003368491、γhat=.04999999998680是两模态数据；真值差不是独立误差认证。','未移植两个系数到新空间杆；S5有独立多种子checkpoint。','原route_budget输入SHA和结果重算；不以其估计新3D系数误差。','观测缺陷无严格界，不能用缩放后条件数替代Gram下界。','regression')
add('num:a-table','四控制组同一初态的恢复误差','p1082–1110',OLD+'s_path.tex:1–146; '+F+'analysis.tex:num:a-table','CK27,CK29','stage5/proofs/integrators_full_coil.md:5–61','stage5/program/coil_control.py:13–122','stage5/results/coil/closed_loop_summary.json',
    '学习组与oracle都含相同中点相位误差；轻微误差抵消不证学习胜过真值。','S5真实线圈端口、不可达残差和闭环积分已更进一步。','保留原表不把原二维可逆端口迁移为12维全驱动。','完整CHNN受约束full-coil闭环和全杆比较未打通。','regression')
add('num:nonlinear-order','同一完整余弦H的二/四阶收敛','p1037–1070',OLD+'core_derivation.tex:138–207; '+F+'analysis.tex:num:nonlinear-order','CK23','stage5/proofs/integrators_full_coil.md:63–104',closed,closed_result,
    'Central4使用完整S=hH+h³fᵀH″f/24；只对自治保守对象有该四阶结论。','相同非可分算法已经接入真实full-coil保守ROM。','保留原阶数回归；同场结构证明由fusion_theory分工核验。','受限/阻尼闭环不能继承该四阶辛性结论。','integrator')
for label,topic in [('num:fixed-error-field','固定非零模型误差的实际闭环'),('num:closed-convergence','向实际场收敛与标称误差平台')]:
 add(label,topic,'p1037–1110',F+'analysis.tex:'+label,'CK23,CK29','stage5/proofs/integrators_full_coil.md:125–145',closed,closed_result,
     'δβ=.02,δγ=.01给同一非保守实际场；步长下降不消除名义模型误差。','S5把表示、图、积分、分配和Newton误差分开，已继承该责任。','保留误差平台负结果；本轮dual_route接口不接受把拟合残差当解析误差。','新全杆与ROM间统一场误差常数仍缺。','integrator')

for label,topic,detail in [
 ('kam:gram','归一化积分Gram与残差','Gram与残差、独立观测误差必须使用相同n L_I归一化。'),
 ('kam:integral-bound','确定性参数误差界','奇异值下界和三角不等式证明成立，不要求iid或最优优化器。'),
 ('kam:feature-bounds','复杂域有限字典范数','BF和B∇F按实际函数类与坐标定义；维数变化要重新计算。'),
 ('kam:analytic-error','系数界到真实Hamiltonian误差','类外余项不可省；实域有限测试误差不等于复解析范数。')]:
 add(label,topic,'p0506–0520;p0560–0598',OLD+'theorem_bridge.tex:180–264; '+OLD+'integral_comsol_to_kam.tex:14–128','CK15,CK16',S5+':53–81',learning,learnresult,
     detail,'S5已完整恢复通用证明，但未计算8749特征的复域常数/Gram证书。','新程序实际计算8749项的BF、能量/梯度/Hessian主控；缺真实误差保持null。','新Gram下界、观测缺陷、真实ROM复域与类外余项未完成。','gram' if label in ('kam:gram','kam:integral-bound') else 'feature')
add('kam:complex-energy','独立ζχ的正确全余弦复化','p0350/m0194;p0351/m0195;p0357/m0200;p0658–0660',OLD+'core_derivation.tex:69–101','CK01,CK08,CK10',S5+':5–51',learning,learnresult,
    'ζ,χ在延拓中独立；真实能量不是只对ζ全纯，不能扩展时继续取实际共轭/real。','S5正确规范、split-tanh双变量延拓已恢复；全网络域未证。','新字典以24个独立复化实坐标求界，与正则D缩放一致。','全复隐藏网络各层极点裕量及统一误差仍缺。','feature')
add('kam:homological','四次非共振同调方程','p0435–0508',OLD+'unified_kam.tex:143–177','CK18,CK25',S5+':110–158',resonance,resresult,
    '在融合2模态四阶非共振前提下正确；对新4对1:1不可用action平均替代共振核。','S5已保留H3消元和全部12通道的第一对限制计算。','实际ROM重新枚举17550项、128非动作共振，旧模板明确reject。','全12维共振NF/约化/余项未完成。','resonance')
add('kam:magnetic-twist','κ特定的正规形、完整余项与twist','p0435–0520',OLD+'unified_kam.tex:23–177','CK18,CK25',S5+':110–176',resonance,resresult,
    '原余弦twist代数有效且可不定；每κ单独图/余项，不能移植其det到3D。','旧twist证明和新第一对候选分别保存；尚无新全维twist。','原脚本有理恒等式及两套twist复算；三维模板门槛单独拒绝。','实际3D完整twist和解析余项缺失。','normalform')
add('kam:closed-budget','保守补偿扰动预算','p0506–0520;p1082–1110',F+'kam.tex:kam:closed-budget; '+OLD+'unified_kam.tex:143–177','CK18,CK24,CK29',S5+':160–176','stage5/program/closed_loop.py:38–110',closed_result,
    'ε包含原始NF余项和学习残差；完美学习不消除标称余项。','S5保留条件KAM及实际闭环边界，缺双图可执行预算。','dual_route_budget以独立R_A/R_B及共同域门槛补接。','真实full-coil可达保守补偿与两图未完成。','dual')
for label,topic,detail in [
 ('kam:implicit-branch','精确隐式映射局部解析分支','1/2 sup||J S″||<1是加上留域条件后的充分条件；Newton样本残差不替代它。'),
 ('kam:map-closeness','同坐标共轭映射与积分误差','先在原坐标离散再共轭，非线性图后中点通常不同；误差含Δε与Δ^(p+1)。'),
 ('kam:map-generator-budget','离散生成扰动按步长归一化','GΔ/Δ≤C3ε+C4Δ^p；步长下降不消除学习误差。')]:
 add(label,topic,'p1037–1078',F+'kam.tex:'+label+'; '+F+'supp_structure.tex:396–445','CK23,CK24','stage5/proofs/integrators_full_coil.md:63–135',closed,closed_result,
     detail,'保守full-coil的理想exact原函数/局部逆/有限时间界已继承；未给3D KAM C3,C4。','结构分工补核一般生成机制；预算分工保留各路线独立常数。','新复域sup和C3/C4、定理阈值未求值。','integrator')
add('kam:map-divisors','全整数离散小除数','p0508/m0242;p1074–1078',F+'kam.tex:113–184','CK24',S5+':160–176',resonance,resresult,
    'e^(iΔkω)−1可因2π倍频为零；连续非共振或有限扫描都不足。','S5已完整区分连续/离散除数。','加入ω=2,Δ=π直接反例并实跑。','新12维全整数Diophantine条件尚无认证。','kam')
for label,topic in [('kam:map-theorem','条件性离散Cantor环面定理'),('kam:twist-bounds-unlabelled','频率映射上下twist界'),('kam:map-smallness','包含iota、Theta的离散小量条件')]:
 add(label,topic,'p0505/m0240;p0508/m0242;p1074–1078',F+'kam.tex:151–184; '+F+'supp_structure.tex:396–445','CK18,CK24',S5+':160–176','未有三维KAM认证实现；已有stage5/program/resonance_research.py:27–45',resresult,
     '保守、exact、解析、留域、twist、离散除数、频率边界和指定阈值全为条件；原稿没有完成其数值认证。','S5恢复条件及旧证书对象，明确无新3D KAM。','复算两模态局部预算而拒绝3D非共振套用；不伪造阈值。','缺新12维约化、解析域、twist、全整数除数和阈值；外部定理常数本轮未重证。','kam')

for label,topic,detail in [
 ('ri:hamiltonians','双路线Hamiltonian及误差符号','完美学习仍分别得到h0和h*；加/减δR必须区分。'),
 ('ri:budgets','双图和两套扰动预算','κ=1和κ*=1.2须分别构造图；仅图像同域才共用BF b。'),
 ('ri:discrete-budgets','两路线独立的离散常数','C3^A,C4^A和C3^B,C4^B未必相同；跟踪阻尼不能混入保守参考。')]:
 add(label,topic,'p0506–0520;p0560–0598;p1082–1110',F+'kam.tex:kam:closed-budget; '+OLD+'unified_kam.tex:143–177','CK15,CK18,CK24,CK29',S5+':53–81,160–176','stage5/program/closed_loop.py:38–110; '+learning,closed_result+'; '+learnresult,
     detail,'S5未把此融合稿独立两图完整预算做成执行接口。','新route_hamiltonians/dual_route_budget复用正确公式并拒绝缺共域、缺独立误差。','新两张3D正规形图及其真实磁实现/余项仍未完成。','dual')

for label,topic,detail in [
 ('sr:majorant','复多圆盘系数主控','逐单项式三角不等式成立，浮点评价不自动向外取整。'),
 ('sr:flow-bounds','辅助W流速度及Jacobian界','在整段不离开域前提下，m位移、exp(ell)变分及逆变分界成立。'),
 ('sr:chosen-domain','正作用量复域','Imin=1e−4大于rhoI=2.5e−5，避免平方根分支零点。'),
 ('sr:polar-bound','极坐标像半径','用复cos/sin界cosh条带给rin=.02131936。'),
 ('sr:polar-derivatives','图及局部逆导数','逆角图只局部，周期角的全局拓扑不由Jacobian界消除。'),
 ('sr:integral-expansion','Taylor积分恒等式','对真实辅助流积分完整括号，非截断Lie多项式。'),
 ('sr:full-remainder','包含全部高阶复合的正规形余项','完整尾项加单括号/双括号积分；不存在漏掉高Lie项的问题。'),
 ('sr:remainder-bound','κ和κ²的完整余项主控','两个括号项为κ²，不能把κ=1总余项简单线性缩放。'),
 ('sr:shared-residual-bound','共享余弦特征主控','正项级数避免cosh−1−s²/2抵消；共域条件独立必要。'),
 ('sr:budget-table','两套预算和twist主控表','均为原2模态点模型普通浮点评价，不是新3D或KAM区间证书。'),
 ('sr:evaluated-budgets','已评价系数加条件bβ的预算','真值差代入只诊断；缺独立误差则不能把epsilon写成已证数值。')]:
 old=OLD+'unified_kam.tex:23–177; '+F+'supp_structure.tex:267–320'
 code=learning if label=='sr:majorant' else resonance
 proof=S5+(':53–81' if label in ('sr:majorant','sr:shared-residual-bound') else ':110–176')
 action='原normal_form_budgets.py原输入隔离实跑；全部12项量对照通过。'
 kind='normalform'
 if label=='sr:majorant':
  action+=' 24D全8749项复域能量/梯度/Hessian界及精确有理Legendre域已新增。';kind='feature'
 if label=='sr:remainder-bound':action+=' κ²最小反例进入测试。'
 if label in ('sr:shared-residual-bound','sr:evaluated-budgets'):action+=' 缺bβ的接口输出conditional而不是伪造数值。';kind='dual'
 add(label,topic,'p0435–0520;p0560–0598',old,'CK15,CK18,CK24',proof,code,learnresult+'; '+resresult,
     detail,'S5保留完整Lie余项证明义务和共振候选，但未执行融合的两套局部主控程序。',action,
     '2模态辅助图不覆盖主控制初态；真实3D两图/余项/学习误差界与KAM阈值仍缺。',kind)


def main():
    inventory=json.loads((ROOT/BASE/'results/manuscript_index.json').read_text())
    names={'analysis.tex','kam.tex','route_interfaces.tex','supp_route_budgets.tex','route_budget_table.tex','route_budget_main_values.tex'}
    rows=[]
    for unit in inventory['review_units']:
        if Path(unit['source']).name not in names:continue
        label=unit['labels'][0] if unit['labels'] else 'kam:twist-bounds-unlabelled'
        if label not in entries:raise KeyError((unit['id'],label))
        row=entries[label].copy();kind=row.pop('kind')
        row.update(id=unit['id'],source=unit['source'],line_start=unit['line_start'],
                   general_birkhoff='stage3/source_inputs/birkhoff/一般Birkhoff_两个核心连接与验证.md:438–446：局部时变Birkhoff表示不产生KAM证书；该边界适用，非本式的数值证据',
                   new_code=BASE+('program/fusion_budget.py:17–104,113–148' if kind=='feature' else 'program/fusion_budget.py:106–196'),
                   tests=BASE+'tests/test_fusion_budget.py',
                   evidence=BASE+budget+'; '+BASE+'results/budgets/actual_3d_majorants.json; '+BASE+'results/budgets/actual_3d_homological_gate.json',
                   material_exists='是，ZIP完整性/逐项hash已核验',mentioned='是；阶段5对应具体证明见stage5_proof',
                   derivation_inherited=('通用误差/坐标证明已恢复；本式新维数常数未在S5计算' if kind in ('gram','feature') else
                                         '条件与对象分别保留；两路线详细预算本轮补回' if kind in ('dual','normalform') else
                                         '对应条件证明在S5恢复，未证明新3D KAM' if kind=='kam' else
                                         '已恢复适用证明或模型定义，原数值仍限原对象'),
                   algorithm_reused=('是，本轮读取已有3D checkpoint并复用字典' if kind=='feature' else
                                     '原2模态预算脚本原样复跑；新3D公式只部分接入' if kind in ('normalform','dual') else
                                     '真实3D共振枚举复核' if kind=='resonance' else
                                     '3D隐式积分已有S5复用；本轮保留回归' if kind=='integrator' else
                                     '不适用或未达到可执行KAM证明，不能以索引代替'),
                   verified_on_3d=('本轮全8749系数/梯度/主控与局部Legendre实算；不含真实误差认证' if kind=='feature' else
                                   '本轮实际12模态非动作共振反向验证：旧模板不适用' if kind=='resonance' else
                                   'S5同场真实线圈积分有证据；本式2模态数值不迁移' if kind=='integrator' else
                                   '未完成本式的新3D完整预算/KAM条件核验'),
                   generalization_proved=('系数三角主控/局部机械Legendre对24变量成立；真实学习误差和KAM未证' if kind=='feature' else
                                          '条件性一般代数/误差责任；未证明新3D KAM或全部物理闭环'),
                   review_note=('已逐式比较中英文同标签数学内容；对应英文 '+unit['source'].replace('chinese/','english/')+':'+label+'. '
                                '源位置相对于ZIP独立解压根。新计算/历史回归/条件定理按字段分开；非整个章节自动完成。'))
        if unit['source'].endswith('analysis.tex'):
            files={
                'num:matrix-data':'framework_experiments/matrix_structure_results.json',
                'num:matrix-benchmark':'framework_experiments/matrix_structure_results.json',
                'num:scales':'baseline_reverification.json',
                'num:feature-gradient':'experiments/minimal_control_results.json',
                'num:feature':'experiments/minimal_control_results.json',
                'num:regression':'experiments/minimal_control_results.json',
                'num:fitted-values':'experiments/minimal_control_results.json',
                'num:a-table':'experiments/minimal_control_results.json',
                'num:nonlinear-order':'framework_experiments/nonlinear_weighted_results.json',
                'num:fixed-error-field':'framework_experiments/closed_loop_convergence_results.json',
                'num:closed-convergence':'framework_experiments/closed_loop_convergence_results.json'}
            row['evidence']=BASE+'results/history/fusion_original_reproduction/'+files[label]+'; '+row['stage5_results']
        if label=='kam:complex-energy':
            row['evidence']+='; '+BASE+'results/budgets/original_omml_learning_kam_checks.json'
        rows.append(row)
    assert len(rows)==80,(len(rows),len(entries))
    target=ROOT/BASE/'annotations/kam.json';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(dict(reviewer_scope='EN+ZH analysis/kam/route_interfaces/supp_route_budgets/route_budget_table/route_budget_main_values; 80 indexed units',rows=rows),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
