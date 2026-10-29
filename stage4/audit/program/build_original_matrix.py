"""Rebuild the original-DOCX slice of the inheritance matrix, without old writes."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / 'matrix_parts' / 'original.csv'
S2 = 'stage3/source_inputs/starter/stage2/'
V10 = 'stage3/source_inputs/v10/v10_framework_20261028/english/sections/'
OM = 'stage4/audit/source_omml/original1025_reading.txt:'
REVIEW = 'stage4/audit/source_omml/stage1review_reading.txt:'
HEAD = ['id','item_kind','original_location','mathematical_item','old_v10',
        'general_birkhoff','stage2','stage3','latest_manuscript_or_notes',
        'source_code','evidence','material_exists','mentioned_in_latest',
        'full_derivation_inherited','algorithm_reused','verified_on_3d',
        'generalization_proved','proof_status','defect','repair','priority']
rows=[]

def add(kind, paragraph, math, item, old, second, latest, code, evidence,
        derivation, reuse, verified, proof, defect, repair, priority='P1', general='不适用'):
    i=len(rows)+1
    rows.append(dict(zip(HEAD,[f'O{i:03d}',kind,
        f'推理草稿5月1025.docx original1025-p{paragraph:04d}/{math}; {OM}{paragraph}',
        item,old,general,second,latest,latest,code,evidence,
        '是：原DOCX原生OMML及所列阶段文件',
        '有相关短述；完整性以本行后续状态为准' if latest!='未见第三阶段实现/正文' else '否',
        derivation,reuse,verified,
        '否：未证明完整三维目标的统一推广',proof,defect,repair,priority])))

add('原始目标',23,'m0014–0036','三维磁机器人与血流接触微重力的同一问题',
    V10+'mechanics.tex:52',S2+'report/stage2_complete.md:417',
    'stage3/notes/theory.md:210',S2+'program/rod3d/',S2+'report/stage2_complete.md:836',
    '第二阶段完整框架保留；第三阶段只完成局部ROM桥接','复用三维ROM；未统一完整环境',
    '第二阶段有规定流刚性壁三维计算；第三阶段未完成新控制转移','目标与已实现中间层有界',
    '完整FSI、柔性壁、生理标定未完成','保留完整模型职责和功率接口；不以ROM取代最终物理模型','P0')
add('运动学',14,'m0005–0006','r_s=v t与不可伸长/伸长率定义',
    V10+'mechanics.tex:1',S2+'report/stage2_complete.md:421',
    'stage3/notes/theory.md:5',S2+'program/learning/rod_rom.py:68',REVIEW+'274',
    '第一阶段和第二阶段已修正；第三阶段清楚声明Kirchhoff约束','是：SO(3)几何ROM',
    '有限配置数值核验；不是一般伸长剪切ROM','条件性几何恒等式',
    '原稿v=1与v=1+ε无条件并列','区分一般Cosserat ν与Kirchhoff ν=e3','P0')
add('平衡方程',59,'m0037','三维角动量、陀螺项和弯扭刚度',
    V10+'mechanics.tex:115',S2+'report/stage2_complete.md:421',
    'stage3/notes/theory.md:5',S2+'program/learning/rod_rom.py:68',REVIEW+'279',
    '第二阶段保留完整平转动；ROM包含转动惯量','复用几何和惯量','有三维数值；未证明全PDE误差',
    '固定参考惯量等假设下成立','原稿扭转刚度EI3及位置/应变符号混用','统一体/空间坐标；扭转采用GJ_t')
add('载荷公式',35,'m0021','Maxwell应力积分及磁力矩',
    V10+'mechanics.tex:1',S2+'report/stage2_complete.md:449',
    'stage3/notes/control.md:5','stage3/program/rom_bridge.py:91',REVIEW+'296',
    '第一阶段完整面积分/磁能推导；第三阶段只采用局部磁能端口','是：同一磁能求导','局部场与完整线圈分别数值检查',
    '固定硬磁偶极近似条件性成立','原稿线积分未声明单位长度或二维约化；力矩不能遗漏','统一磁能与虚功，明确积分测度和材料假设')
add('载荷公式',40,'m0024','Morison相对加速度与二次拖曳',
    V10+'mechanics.tex:52',S2+'report/stage2_complete.md:485',
    'stage3/notes/materials_and_scope.md:76',S2+'program/rod3d/',REVIEW+'311',
    '第一阶段有修正推导；第二阶段规定流层；第三阶段未接入该实际场','仅复跑历史杆程序；无ROM-Birkhoff血流耦合',
    '历史规定脉动流；未验证附加质量/双向FSI','原式量纲错误；修正式为条件模型',
    'r_tt减V_f速度；拖曳宽度缺失；移项遗漏流速项','用流体物质加速度和相对速度，核验Re/Womersley/堵塞比','P0')
add('载荷公式',49,'m0031','Hertz型接触与Coulomb摩擦的实值性',
    '旧平面基准不含壁接触',S2+'report/stage2_complete.md:517',
    'stage3/notes/theory.md:210',S2+'program/rod3d/',REVIEW+'325',
    '第一阶段有间隙/功率修正；第二阶段实现罚接触；第三阶段Birkhoff未涵盖','历史程序保留；未纳入实际ROM图',
    '第二阶段数值；没有完整柔性壁理论','原式在活动区可非实；平滑罚接触是中间模型',
    'd≤d0且n=1.5时(d-d0)^n一般不是实数','δ=(d0-d)+并配合法向定义；摩擦取接触相对速度','P0')
add('边界条件',26,'m0016；p0056/m0036','零重力与残余微重力边界',
    V10+'mechanics.tex:52',S2+'report/stage2_complete.md:533',
    'stage3/notes/materials_and_scope.md:76',S2+'program/rod3d/',REVIEW+'334',
    '第一阶段完整参考系与边界讨论；后续有合成工况','未继承真实生理标定，因为原本不存在',
    '合成残余加速度工况；无实测标定','仅条件建模','置g=0不能推导空间站血流参数','保留实测加速度、入口波形、壁顺应性待输入状态')
add('模型约化',92,'m0056','原(8)中心线四阶梁PDE的对象限制',
    V10+'mechanics.tex:123',S2+'report/stage2_complete.md:539',
    'stage3/notes/theory.md:5',S2+'program/learning/rod_rom.py:68',REVIEW+'431',
    '正确修正为受限梁验证；新三维模型从几何重新建立','不复用错误姿态消元','三维弯扭ROM存在；无梁→一般Cosserat推广证明',
    '原无条件推导不成立','姿态、扭转、转动惯量被无条件消掉','保留三维变分模型；梁只作具有附加假设的独立回归','P0')
add('弱式算法',115,'m0074–0085','原(10)Galerkin残差、两次分部积分和边界功',
    V10+'mechanics.tex:147',S2+'report/stage2_complete.md:539',
    'stage3/notes/theory.md:5',S2+'program/learning/rod_rom.py:68',REVIEW+'424',
    '第二阶段有三维虚功框架；第三阶段短述复用模型','是：几何Ritz；不是原梁弱式直接推广',
    'ROM几何核验；未完成空间误差定理','条件性离散推导','原中心线弱式不足以保留旋转/自然边界','同时投影平动和旋转虚功；注明约束与插值正则性')
add('Hamiltonian公式',150,'m0097–0100','正则动量p=M(q)qdot与变质量Hamiltonian',
    V10+'mechanics.tex:35',S2+'program/learning/rod_rom.py:113',
    'stage3/notes/theory.md:5','stage3/program/rom_bridge.py:48','stage3/results/rom_bridge.json',
    '有效公式和几何惯性完整继承到新ROM','是：动态M(q)及自动微分',
    '是：三维12自由度；仍是有限数值检查','正定M与正确坐标下可证明',
    '不能把线性归一化M0或求解预条件矩阵当作物理M(q)','保留每次求值M及全部∂M项','P0')
add('势能条件',156,'m0104','V=∫K(q)q dq的可积性',
    V10+'mechanics.tex:20',S2+'report/stage2_complete.md:539',
    'stage3/notes/theory.md:34','stage3/program/rom_bridge.py:48',REVIEW+'460',
    '第一阶段明确修正；后续从杆能量求梯度','是：先势能后广义力','是：ROM采用能量定义',
    '原无条件积分错误；修正可证明','K(q)对称并不足以使K(q)q是梯度','核验力Jacobian对称或直接变分离散势能')
add('功率恒等式',171,'m0116','原(12)Hamiltonian功率与显式时间项',
    V10+'mechanics.tex:162',S2+'report/stage2_complete.md:563',
    'stage3/notes/control.md:5','stage3/program/control_experiments.py:135','stage3/results/control/control_results.json',
    '第一阶段补H_t和界面通量；第三阶段测试有限窗口功率','是：实际磁输入功率','ROM有数值残差；全耦合账未完成',
    '自治式条件成立；非自治需补项','受迫流体/移动壁不能全部当单调机械耗散','统一dH/dt=H_t+vᵀQ并保存开放边界功率')
add('Poisson公式',276,'m0169–0170','z=(q,p)下J和Hamiltonian梯度次序',
    V10+'mechanics.tex:40',S2+'report/stage2_complete.md:539',
    'stage3/notes/theory.md:5','stage3/program/rom_bridge.py:61',REVIEW+'110',
    '后续正确使用(q,p)梯度；原错误未传播','是：J gradH','是：ROM场核验',
    '原局部笔误已可最小修正','原将(H_p,H_q)与(H_q,H_p)混写；∇z与∇H混写','统一变量顺序并用谐振子检查符号')
add('Metriplectic构造',288,'m0176–0184','机械耗散与能量熵双退化',
    '旧主基准以机械耗散/端口为主',S2+'report/stage2_complete.md:1939',
    'stage3/notes/materials_and_scope.md:32',S2+'program/metriplectic_candidate.py:16','stage3/results/baseline/metriplectic_candidate.json',
    '第一阶段M1–M4和第二阶段内能坐标等价构造保留；第三阶段仅复跑','是：旧候选代码复算',
    '32个真实ROM状态历史核验；无完整热机器人','候选括号代数可证明；物理闭合待做',
    '机械H下降与对同一H施加耗散退化不能同时成立','加入内能/熵状态并保留端口；不虚构热参数')
add('复坐标公式',350,'m0194–0206','原(17)–(21)复坐标及Wirtinger归一化',
    V10+'mechanics.tex:259',S2+'report/stage2_complete.md:1473',
    'stage3/notes/control.md:67',S2+'program/learning/rod_rom.py:113',REVIEW+'117',
    '第一阶段修正；第二阶段完整复网络继承；第三阶段标量基准不等于完整网络','ROM缩放复用；完整网络本轮未训练',
    '第二阶段完整网络历史结果；第三阶段无公平重训','正确坐标恒等式可证明',
    'ξ=(q+ip)/√2却用1/2导数导致动力学系数错误','正则尺度化；对应导数1/√2及ξdot=-iH_barξ+iQ/√2','P0')
add('学习损失',591,'m0284–0289','能量损失、Hamiltonian导数损失与预测器',
    V10+'supp_structure.tex:356',S2+'report/stage2_complete.md:1487',
    'stage3/notes/control.md:67','stage3/program/control_learning.py','stage3/results/control_learning/learning_results.json',
    '第二阶段有完整网络与失败；第三阶段只学习单个磁势系数','完整网络算法未接入第三阶段实验',
    '标量残差有ROM实验；完整网络训练数据未在轻包恢复','原强制机械能恒定损失错误',
    'L_energy擅自Hdot=0；L_H导数ξ与预测barξ不一致','以真实向量场和功率残差训练；保留全复网络与解析基公平比较','P0')
add('复分析定理',741,'m0327–0343（含前后证明）','CR充分性及实Hamiltonian的复延拓',
    V10+'supp_structure.tex:246',S2+'report/stage2_complete.md:1533',
    'stage3/notes/theory.md:210','未见第三阶段完整网络实现',REVIEW+'147',
    '正确定理可保留；前文推导错误需要校勘','不适用','没有新复域认证',
    'C1+CR定理成立；原证明局部代数错误','p738 f′=u_x+i u_x；分段激活不自动满足解析KAM','改为u_x+i v_x；独立指定ξ与共轭的复延拓域')
add('一般表示',848,'m0364–0366','原非保守F1=p+时间积分的相容性',
    V10+'supp_structure.tex:1',S2+'notes/route_a.md:41',
    'stage3/notes/theory.md:51','stage3/program/birkhoff_rom.py:30','stage3/results/birkhoff_identity_checks.json',
    '一般材料与第二阶段已修正；第三阶段实现一个局部特例','复用输运思想，非完整一般Moser程序',
    '是：实际ROM特殊阻尼；未验证任意血流接触','原构造交叉偏导不相容','要求F1,p=1却令F1,t含p；B动能也混写Mq',
    '由相容输运构造a,B并独立量化原场误差','P0','stage3/source_inputs/birkhoff/一般Birkhoff_两个核心连接与验证.md')
add('定理',862,'m0377–0391；附证p1179–1206','Theorem A端点匹配、横截性及局部生成函数',
    V10+'supp_structure.tex:36',S2+'report/stage2_complete.md:966',
    'stage3/notes/theory.md:185','stage3/program/birkhoff_rom.py:56',REVIEW+'211',
    '第二阶段保留详细推导；第三阶段压缩成前提摘要','仅特殊显式图；未实现通用端点重构',
    '特殊图数值核验；未完成一般3D定理推广','补足端点适配和局部条件后成立',
    'N必须可逆与φ唯一均错误；D符号在陈述/证明冲突','横截Jacobian可逆；φ模时间常数；统一Kf=∇B+a_t','P0',
    'stage3/source_inputs/birkhoff/一般Birkhoff_两个核心连接与验证.md')
add('定理',881,'m0393–0399；p1213/m0565','Theorem B固定生成坐标的解析递推',
    V10+'supp_structure.tex:147',S2+'report/stage2_complete.md:966',
    'stage3/notes/theory.md:185','stage3/program/rom_integrators.py:15',REVIEW+'214',
    '第二阶段详细推导；第三阶段只有Central4专式和一阶输运','Central4公式复用；通用B递推未实现',
    '保守Central4在ROM运行；通用递推未验证','局部解析且梯度条件成立时有效',
    '前文k系数偏位；末附证明已自行改成k+1，不能遗漏','保留p1213正确公式，明确Dt和端点重构','P0',
    'stage3/source_inputs/birkhoff/一般Birkhoff_两个核心连接与验证.md')
add('公式30–31',910,'m0400；p0920/m0408','中心差分端点变换和逆变换',
    V10+'supp_structure.tex:36',S2+'notes/route_a.md:41',
    'stage3/notes/theory.md:185','stage3/program/rom_integrators.py:62',REVIEW+'156',
    '旧补充与第二阶段有矩阵；第三阶段默认中点实现而未展开原端点矩阵','是：正则中点；非任意K图','保守ROM分支运行',
    '线性代数成立；结构适配另有前提','线性中心变换不自动匹配时变K','保留原矩阵并逐端点核验拉回恒等式','P0')
add('公式32',931,'m0417–0418','初端固定时w和what的时间导数',
    V10+'supp_structure.tex:36',S2+'notes/route_a.md:41',
    'stage3/notes/theory.md:185','stage3/program/rom_integrators.py:62',REVIEW+'162',
    '第二阶段修正；第三阶段仅原则摘要','未实现通用A/B递推','无一般三维端点递推验证',
    '原式分量与符号错误','把w和what分量互换，混入双端点同时移动导数','固定z_-；wdot=(qplusdot/2,-pplusdot/2)','P0')
add('公式33–34',961,'m0427；p0963/m0429','一阶生成梯度与端点重构',
    V10+'supp_structure.tex:1',S2+'notes/route_a.md:41',
    'stage3/notes/theory.md:185','stage3/program/rom_integrators.py:62',REVIEW+'165',
    '有效中心生成关系保留；错误阻尼候选已否定','保守中点复用；一般梯度投影未实现','保守ROM验证',
    '有真实梯度及合法图才成立','阻尼候选Jacobian一般非对称；o(2)未定义','分别检验梯度可积性、结构匹配和截断阶','P0')
add('公式35–36',986,'m0434；p1003/m0442；p1220/m0570','变质量中点与常矩阵消元次序',
    V10+'supp_structure.tex:94',S2+'results/route_a/original36_linear_identity.json',
    'stage3/notes/integrators.md:5','stage3/program/rom_integrators.py:62','stage3/results/integrators/integrators.json',
    '正确矩阵与几何惯性继承，第三阶段直接解24维非线性残差','是：原36修正算法','是：同一12自由度ROM实验',
    '条件性二阶；耗散时非通常辛','原逐元素分式与动量行列约定错误；误称一阶保辛','采用左乘(I+E)^-1及完整中点评价；分别检查耗散结构','P0')
add('高阶算法',1040,'m0445–0456','原二阶生成展开与Central4恢复',
    V10+'supp_structure.tex:147',S2+'report/stage2_complete.md:1010',
    'stage3/notes/integrators.md:27','stage3/program/rom_integrators.py:15','stage3/results/integrators/integrators.json',
    '非可分Central4有效推导继承；原错误Dt不继承','是：完整H自动微分实现','是：ROM阶数实验；不是所有载荷下四阶',
    '自治光滑保守分支条件性四阶','固定生成变量与物理轨道导数混用；高阶不自动结构保持','保留hH+h^3 fᵀH″f/24的完整推导和隐式分支条件')
add('控制算法',1082,'m0482–0487','原Uk的内部控制、状态增量和生成函数控制',
    V10+'controlled_analysis.tex',S2+'report/stage2_complete.md:1026',
    'stage3/notes/control.md:5','stage3/program/control_experiments.py:54','stage3/results/control/point_audit.json',
    '物理可达性由第二阶段到第三阶段实质推进；全生成函数控制未完成','是：真实磁Gm分配','是：ROM控制、秩与残差；未统一高维杆转移',
    '实际闭环须逐一重审结构','任意24维增量不等于磁执行器可施加','从Qm=Gm u定义控制并保留不可达残差与功率','P0')
add('结构公式',1125,'m0509；p1156/m0530','二形式Ω的1/2因子、闭性与局部恰当',
    V10+'supp_structure.tex:1',S2+'report/stage2_complete.md:946',
    'stage3/notes/theory.md:51','stage3/program/birkhoff_rom.py:52','stage3/results/birkhoff_identity_checks.json',
    '正确K矩阵与规范关系继承；原重复定义需统一','是：特殊K及图恒等式','是：局部特殊阻尼样本','d²=0机制成立；原二形式归一化不一致',
    'Ω=ΣKij dzi∧dzj实际等于2dα而前文声称dα；闭不全局恰当','统一Ω=½ΣKij dzi∧dzj并声明局部/星形域','P0',
    'stage3/source_inputs/birkhoff/一般Birkhoff_两个核心连接与验证.md')
add('KAM条件',508,'m0242；p1074–1078/m0475–0479','连续Diophantine、离散步长共振与twist',
    V10+'kam.tex:57',S2+'report/stage2_complete.md:396',
    'stage3/notes/theory.md:210','未见第三阶段共振正规形程序',
    S2+'report/stage2_complete.md:396（历史频谱记载）；stage4/audit/results/chnn_checks/checks.json#/checks/actual_3d_model（本轮新算频谱，不追溯升级起点证据；轻量包缺少历史results/learning/rom_metadata.json）',
    '旧KAM与第二阶段1:1共振结论保留为历史；第三阶段未恢复完整证明','无新3D证明算法；旧基准仅复跑现有部分',
    '历史报告有1:1共振；本轮新算频谱独立重现；没有新三维KAM证书','条件性理论；新模型待证',
    '极坐标/FFT/闭相图不是KAM证明；旧非共振证书不能迁移','保留旧对象，研究共振正规形或合法对称性约化及新解析域','P0')

conditional_generalizations={
 'O002':'条件性：SO(3)运动学恒等式；Kirchhoff约束不推广成可伸长剪切模型',
 'O003':'条件性：固定参考截面惯量的三维平衡；一般截面演化需另加项',
 'O010':'是：正定M(q)的有限维Legendre/几何惯性公式任意维成立；PDE降阶误差未证',
 'O011':'是：局部梯度可积性判据；任意给定K(q)q不自动满足',
 'O012':'是：所定义有限维Hamiltonian及实际端口的功率恒等式；全FSI未实现',
 'O013':'是：固定(q,p)约定下正则Hamiltonian代数；不等于任意耗散场辛',
 'O014':'条件性：对称半正定C与正温度下任意维候选括号成立；真实热闭合未证',
 'O015':'是：正则尺度化后的复坐标恒等式；不自动产生学习或KAM证书',
 'O017':'是：C1加CR局部全纯定理；训练网络满足复域条件未证',
 'O019':'条件性：给定合法K及端点适配/横截条件的局部定理；实际全载荷ROM未验证',
 'O020':'条件性：合法解析生成PDE的局部递推；一般ROM高阶实现未完成',
 'O021':'是：线性端点坐标代数；对任意时变K的结构适配未证',
 'O024':'条件性：光滑有限维ODE中点二阶及保守分支辛性；跨接触分支未证',
 'O025':'条件性：光滑自治Hamiltonian中央生成式四阶；耗散接触不能照搬',
 'O027':'是：统一1/2约定下K=da的局部闭性；全局恰当性需拓扑条件',
}
for row in rows:
    if row['id'] in conditional_generalizations:
        row['generalization_proved']=conditional_generalizations[row['id']]

OUT.parent.mkdir(parents=True,exist_ok=True)
with OUT.open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=HEAD);writer.writeheader();writer.writerows(rows)
print(f'{OUT.relative_to(ROOT)}: {len(rows)} rows, {len(HEAD)} columns')
