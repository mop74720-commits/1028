"""Hand-reviewed mathematical assessments joined to deterministic source IDs.
Rules are limited to the six fully read files, not generic automatic validation.
"""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'stage6/fusion_reconciliation'
INDEX=json.loads((OUT/'results/manuscript_index.json').read_text())
oldroot=ROOT/'stage3/source_inputs/v10/v10_framework_20261028'
OMML='stage4/audit/source_omml/original1025_indexed.json#'
C='stage3/source_inputs/birkhoff/一般Birkhoff_两个核心连接与验证.md'
P='stage5/proofs/'
G='stage5/program/'
S6='stage6/fusion_reconciliation/'

# Each tuple has one reviewed formula's actual mathematical role, a coherent
# proof family and its specific limitation. English and Chinese were read in full.
notes={
'structure':{
5:('Birkhoff定义与变分符号','form','Da行列约定需固定；不是任意B与a可独立指定'),
13:('闭性与时间相容','form','闭性本身不保证非退化；需另验detK'),
23:('齐次一形式输运及B=a·f','transport','一般局部存在；stage5实际采用等价有源规范后截断，二者有限截断不相同'),
31:('逐分量表示恒等式','transport','此处代入号正确；有限阶残差不能直接置零'),
42:('比例动量阻尼精确提升','weighted','仅统一比例动量阻尼；M(q)允许但必须保留Hq全部导数'),
56:('相容Darboux/Moser图匹配','chart','插值非退化及留域需验证；数值匹配误差独立报告'),
61:('端点二形式差拉回','endpoint','局部端点可逆不足，必须匹配两端二形式'),
66:('Theorem A局部生成势命题','endpoint','需横截及单连通局部域；不要求生成Hessian可逆'),
69:('负端点向生成坐标横截','endpoint','初始非退化仅给短时，不是全局窗口保证'),
80:('原30中央端点记号','endpoint','一般时变K须先分别应用两端合法图'),
87:('中央投影Jacobian','endpoint','h=0时T0可逆但生成Hessian=0，反驳原无谓N逆条件'),
93:('完整时间中点生成函数','generator','必须评价显式t_m；不能从保留一个项直接认定阶数'),
101:('常质量比例阻尼加权格式','weighted','两条显式常质量公式不能直接用于变质量，实际算法用完整H'),
108:('指数共形与时间二形式','weighted','理想隐式映射，普通阻尼中点通常不同'),
117:('时间依赖图场','chart','χ_t项不可省；K0g梯度性要求原场输运相容'),
125:('两端相容图复合中点','chart','中点非一般非线性坐标不变，图选择会影响轨迹误差'),
131:('理想Birkhoff图法二形式保持','chartdefect','只能针对定义的被表示场；有限图/求解误差须分项'),
142:('原35/36同场完整变质量中点','midpoint','几何惯性、非自治时间与反馈都在同一未知中点'),
153:('原36非交换左解','matrix','仅常M/C/K支；反馈依赖中点时仍为隐式'),
168:('旧平衡坐标有效质量/阻尼','oldmodal','仅旧两模态坐标归一化；不能把N^-1当新ROM常质量'),
181:('中央生成映射定义','central','单值S和局部唯一隐式分支'),
185:('自治保守中点','central','一般反馈不可假称Hamiltonian中点'),
189:('Cayley形式实际隐式Jacobian','central','Newton矩阵非奇异并保留全Hessian'),
194:('中央映射单值exact primitive','exact','理想精确根的结论，不是浮点迭代程序exactness'),
201:('完整非可分Central4','central4','仅自治Hamiltonian；不能省质量混合导数或先推进后补控制'),
208:('实际一般闭环中点','midpoint','残余阻尼允许有限时间二阶，不赋予辛性'),
219:('h0/h*/hhat/hc四能量','objects','仅声明的纯势学习误差模型；未知质量/接触需另列'),
229:('旧两模态受迫耗散plant','objects','它是回归基准，不是三维机器人主场'),
241:('能量/阻尼联合积分辨识','learning','需全轨迹划分、积分缺陷和Gram激励；三维完整网络并非同一线性设计'),
260:('方向一理想广义力残差补偿','control','该U需实际可达；完整线圈秩与约束残差不可抹去'),
264:('补偿后残余保守与阻尼分裂','control','δγ=0和可实现梯度才进入普通Hamiltonian/KAM分支')},
'supp_general_birkhoff':{
7:('特征线一形式与切线逆','transport','用于局部存在证明，不能当免费物理精确流算法'),
15:('逆切线二形式拉回','transport','局部非退化继承自可逆S，不证明全域'),
21:('二形式输运PDE','form','对近似a定义的fa成立，对原f必须测残差'),
29:('变分原理与形式自伴','variational','Euler-Lagrange微分算子自伴，物理Df不必对称'),
41:('B=H固定空间规范','gauge','必须同步加gradσ；不减少原场表示误差、不造成能量守恒'),
56:('完整非自治时间系数卷积递推','transport','含阶乘系数约定正确；stage5只有自治计算，本轮另接κ(t)'),
64:('变质量机械场第一输运系数','transport','a1q=Vq−Tq−Qnc，a1p=−Hp，保留惯性'),
78:('Moser插值及辅助向量场','chart','全λ非退化、辅助流与逆留域必须另验'),
89:('Moser拉回导数恒等式','chart','i_vω=−Kv符号正确；辅助流不是物理流'),
101:('图场保存固定二形式','chart','需要时间依赖图的全导数'),
105:('星形域径向图Hamiltonian','chart','K0g闭且径向线段留域；路径积分本身不使任意g可积'),
114:('实际图端点块Jacobian','endpoint','T+与T−在不同时间状态评价'),
121:('完整端点结构匹配块式','endpoint','EᵀT0=K0与T0ᵀE=−K0符号相容'),
133:('两种中央规范生成势关系','generator','w=T0wB仅是合法记号变换，不换物理力'),
137:('中央生成梯度恢复Hamilton方程','generator','E T0=−J，负生成势给正向流'),
143:('理想图法链式结构保持','chartdefect','内部映射/链式法则理想精确；实际补D1全部项'),
156:('同K控制的Lie导数判据','control','Kv_u局部梯度且实际输入可达；共点耗能不自动满足'),
175:('图逼近误差定义','chartdefect','需含χ_t与逆图的共同域范数，不能只给位置匹配'),
182:('二形式图匹配残差','chartdefect','仅结构误差，不能代替原场e_B'),
192:('截断形式与标量定义','transport','定义新的fa，非自动原场精确表示'),
197:('原场/图/积分/代数误差总预算','convergence','有限时间常数、留域和每步残差积累分别承担'),
209:('理想内部映射下端点缺陷传播','chartdefect','公式条件正确；实际增加内部辛缺陷与逆图链式缺陷')},
'supp_structure':{
5:('Birkhoff闭性/时间相容复核','form','保持负J约定一致'),
15:('逆相流拉回存在构造','transport','是存在表示，不是可免费调用高维流'),
22:('比例阻尼表示代回','weighted','统一α(t)允许变质量但非自治提升不等于KAM'),
30:('加权结构与指数共形','weighted','有限精度解要单独测缺陷'),
42:('原30辅助常矩阵','endpoint','T0与E尺寸2n，端点联合变换4n'),
49:('原30完整联合端点矩阵','endpoint','矩阵块序与原31联合逆一致'),
55:('端点Pfaff一形式及外微分','endpoint','先验证适配，再以投影得局部标量'),
66:('流图像中央横截','endpoint','h=0合法；无需生成梯度可逆'),
85:('Newton逆与精确切映射','central','当地逆条件；实际反馈Jacobian不可冻结'),
102:('非交换消元的q中点式','matrix','从qdot=M^-1p导出，乘法顺序固定'),
106:('原36非交换动量左解','matrix','K M^-1与M^-1 K不能互换'),
117:('变质量几何惯性','midpoint','向量项−pᵀ∂M^-1p/2，不能藏入标量分母'),
129:('Cayley辛性代数','central','I±C可交换因同C多项式；与一般M/K交换无关'),
134:('单值中央exact primitive证明','exact','成立于单值S和隐式分支，保留完整一形式证明'),
142:('原点极坐标周期原函数','exact','这里显式周期函数正确，不能误套旧I0管图错误'),
153:('真实时间中点与端点平均Taylor式','central4','两种中点不能混同'),
162:('消去真实中点后的三阶修正','central4','系数−2(fprime)^2 f正确'),
169:('Q=fᵀHessianH f的全导数','central4','包括三阶张量和全混合导数'),
180:('谐振子Central4相位','central4','相位五阶局部缺陷不是能量/相位精确'),
194:('旧余弦磁势Central4显式增量','oldcentral','仅旧separable单特征，三维用完整H AD而非抄公式'),
203:('旧磁势增量全部Jacobian块','oldcentral','跨模态项保留；不可用于新非可分质量直接代参'),
221:('非精确隐式根残差界','convergence','hL/2<1还需域映回自身'),
226:('稳定性加权代数残差累积','convergence','η_j是增量残差，不是训练/观测误差'),
238:('Central4有限时间误差','convergence','全局h4需单步η=O(h5)及高阶有界'),
254:('独立复变量实能量解析延拓','complex','冻结共轭系数全纯；不能用非全纯实部直接延拓'),
261:('归一化复动力学与功率','complex','ζ=(X+iY)/sqrt2，力项i f/sqrt2；一般力不必有耗散势'),
274:('变质量平衡线性正则归一化','normalform','A=M^-1/2 E Ω^-1/2保证正则；非线性作用还需正规形'),
284:('三次消元对四阶的完整贡献','normalform','H4+.5{H3,W3}，不能仅平均H4；新模型保留共振核'),
290:('旧两模态余弦四次多项式','oldnormal','仅旧H3=0偶势模型，不替代三维动量耦合项'),
300:('旧双角平均四次正规形','oldnormal','非共振场合的动作平均，新1:1有额外核项'),
308:('旧有限四阶同调生成函数','oldnormal','有限k·ν不为零不等于全阶Diophantine'),
316:('余弦原尾项显式上界','oldnormal','完整变换余项另含Lie项和域图常数'),
328:('积分观测物理缺陷','learning','端点/重构/求积/类外力必须留在误差'),
343:('设计矩阵扰动进入总缺陷','learning','先验系数界和实际导出设计矩阵需独立给出'),
349:('Gram到系数的确定性不等式','learning','无需最优拟合但需λ下界；不能从低训练loss反推出'),
362:('完整35四次方向解析特征','features','完整旧四实变量基；融合稿新单系数只取其子类'),
376:('完整特征与阻尼联合积分设计','features','4L窗口归一化36未知；一般速度Rayleigh时可能不再线性'),
392:('动量学习参考真实加速度','reference','需Hpp可逆的Legendre反解与独立物理力估计'),
408:('周期混合映射生成函数','kam','需exact-symplectic与混合投影；有限Newton误差不够'),
420:('复作用域twist双边界','kam','旧A逆常数不能迁移新12维'),
428:('离散KAM规范化小量阈值','kam','G_h/h、τD>n+1、离散除数与域都不可省；仍条件性'),
442:('有限幅值嵌入流缺陷','kam','小采样缺陷无解析条带/逆/小量认证；保留旧对象')}
}
# Family metadata gives precise common derivation anchors; individual rows above
# retain distinct formula roles, hypotheses and scope limits.
meta={
'form':('p1113/m0499;p1114/m0500;p1120/m0505;p1125/m0509', 'corrected_mathematics.md:110–151','corrected_identities.py:142–168; transport_cache.py:83–119','stage5/results/transport/fullcoil_collocated/inverse_verified.json','完整条件推导及24D局部采样验证','是：同一ROM，有限窗口','是：局部恒等式；否：整个机器人全局结构'),
 'transport':('p0848/m0364;p1113–p1120','birkhoff_transport.md:5–102','transport_native.py:77–129; transport_cache.py:1–119','stage5/results/transport/synthetic/inverse_verified.json; stage5/results/transport/fullcoil_collocated/inverse_verified.json','已实施自治r3/r2及空间缓存；非自治卷积本轮补入','是：特定光滑分支','条件性局部理论，统一解析域/全载荷未证'),
 'weighted':('p0961/m0427;p0986/m0434','integrators_full_coil.md:106–123','../stage3/program/rom_integrators.py:80–92','stage3/results/integrators/integrators.json','精确比例阻尼图证明与既有变质量回归保留','是：比例阻尼合法基准','是：所声明比例分支，非任意血流'),
 'chart':('p0862–p0879;p0910/m0400','birkhoff_transport.md:104–149','moser_chart.py:22–113','stage5/results/transport/fullcoil_collocated/inverse_verified.json','实际24D Moser/逆图/时间项已继承','是：近似形式及受限局部域','条件性图存在；非全域或精确原场'),
 'endpoint':('p0867/m0377;p0878/m0390;p0910/m0400;p0920/m0408;p1204','corrected_mathematics.md:153–235','corrected_identities.py:171–244','stage5/results/corrected_identities/latest.json','完整端点适配/横截/初值/反向重构已恢复','是：24D端点矩阵与实际图，非全场假设','条件局部定理完整；真实全载荷前提未全验'),
 'generator':('p0888/m0399;p0931/m0417;p0961/m0427;p1213/m0565','corrected_mathematics.md:237–298','corrected_identities.py:240–292','stage5/results/corrected_identities/latest.json','固定w PDE及标量递推在stage5比融合稿引用更详细','部分：保守Central4，通用高维递推未完成','条件局部解析定理；实际共同域待证'),
 'midpoint':('p0986/m0434;p1003/m0442;p1220/m0570','integrators_full_coil.md:39–61','../stage3/program/rom_integrators.py:62; closed_loop.py:113–176','stage5/results/closed_loop/results.json; stage5/results/closed_loop/verification.json','已接完整线圈同场反馈与实际Jacobian','是：真实fullcoil闭环','光滑条件有限时间结论，非切换全局证明'),
 'matrix':('p1003/m0442;p1070/m0470;p1220/m0570','corrected_mathematics.md:353–367','corrected_identities.py:248–262','stage5/results/corrected_identities/latest.json','正确左解直接继承，旧错误矩阵次序有反例','不适用：常矩阵回归，ROM用完整残差','是：明确常系数代数，非变质量闭式'),
 'central':('p0910/m0400;p0961/m0427','integrators_full_coil.md:39–104','../stage3/program/rom_integrators.py:15–78','stage5/results/closed_loop/results.json; stage5/results/closed_loop/verification.json','理想中心生成/隐式Jacobian已入同一保守ROM','是：固定全线圈保守分支','条件性局部exact映射，不是有限迭代程序'),
 'central4':('p0881–p0888;p1213/m0565','integrators_full_coil.md:63–104','../stage3/program/rom_integrators.py:15–60','stage5/results/closed_loop/results.json; stage5/results/closed_loop/verification.json','完整非可分修正直接复用，未降级回旧磁势单项','是：实际完整线圈H','条件自治四阶；统一解析域KAM未证'),
 'exact':('p1113–p1167（原稿仅二形式，单值原函数由旧成果补足）','corrected_mathematics.md:369–406; integrators_full_coil.md:63–104','corrected_identities.py:303; ../stage3/program/rom_integrators.py:15–60','stage5/results/corrected_identities/latest.json','完整中央原函数保留且旧I0管图问题已修正','是：理想24D中心映射；数值只近似','是：条件单值/同伦命题；非新KAM证书'),
 'convergence':('p0986/m0434;p1003/m0442;p1082–p1106','integrators_full_coil.md:125–151; birkhoff_transport.md:141–149','transport_cache.py:83–130; ../stage3/program/rom_integrators.py:30–78','stage5/results/transport/fullcoil_collocated/inverse_verified.json','完整有限时间误差责任已恢复，参数常数仍条件性','是：实际误差/阶数数值，无区间常数','条件局部定理，非无限时间或KAM'),
 'control':('p1082–p1091;p0842/m0359','coil_energy_ports.md:37–107; integrators_full_coil.md:5–61','coil_rom.py; transport_native.py:138–151','stage5/results/transport/fullcoil_collocated/inverse_verified.json','实际电流共点控制/残差已实施；理想势补偿未自动可达','是：fullcoil受限与光滑分支区分','条件同K判据；实际闭环需构造Ku'),
 'objects':('p0506–p0520;p0842/m0359','chnn_kam_restored.md:29–81','learning_models.py:23–61; learning_coil_reachability.py','stage5/results/learning/S5_L01_results.json; stage5/results/learning/S5_L02_coil_reachability.json','保留旧四能量概念，但新三维模型/误差对象不同','部分：新训练与可达残差，无旧证书迁移','否：完整闭环学习统一推广未证'),
 'learning':('p0506–p0520;p0560–p0598','chnn_kam_restored.md:53–108','learning_models.py:23–61; run_learning_research.py','stage5/results/learning/S5_L01_results.json','确定性误差推导已恢复；新三维积分Gram与复域常数未闭合','部分：真实域训练测试；未验证本式全部常数','条件误差定理，3D假设未全验'),
 'features':('p0348–p0362;p0506–p0520','chnn_kam_restored.md:29–81','learning_models.py:23–61','stage5/results/learning/S5_L01_results.json','旧35完整特征保留；三维8749机械字典不是同一35模型','部分：新三模型公平训练；旧基对象不同','模型类代数正确，3D统一误差界未证'),
 'complex':('p0351;p0567;p0591','corrected_mathematics.md:54–108; chnn_kam_restored.md:5–51','corrected_identities.py:97–125; learning_models.py:43','stage5/results/learning/S5_L01_independent_checks.json','归一化/Wirtinger/Rayleigh修正进入新实现','是：三维实域梯度测试；复域半径未认证','条件复化构造正确，无统一复学习界'),
 'normalform':('p0435–p0520','chnn_kam_restored.md:110–158','resonance_research.py; resonance_normalform_pair.py','stage5/results/resonance/S5_R03_pair_reduction.json','保留三次消元并实际计算第一共振对/全12括号通道','是：新ROM部分共振计算','部分代数/浮点候选；全12维twist未证'),
 'reference':('p0506–p0520;p1082–p1106','chnn_kam_restored.md:191–204','learning_postprocess.py; learning_coil_reachability.py','stage5/results/learning/S5_L02_coil_reachability.json','历史完整动量参考公式保留，第五阶段未做其真实三维跟踪','第五阶段未完成；本轮新reference程序另给证据','需Legendre域与可达性，不能理想全驱动'),
 'kam':('p0506–p0520;p1106','chnn_kam_restored.md:160–189','resonance_research.py; resonance_normalform_pair.py','stage5/results/resonance/S5_R04_partial_scope.json','完整旧条件路线恢复；没有宣称新三维证书','否：全3D KAM未认证','条件性定理，实际新域/小量/除数未验'),
 'oldmodal':('p0285–p0305','chnn_kam_restored.md:5–27','../stage3/program/rom_bridge.py','stage3/results/integrators/integrators.json','旧两模态归一化独立保留；新M(q)另算','不直接适用新ROM常质量','是：旧坐标代数，非新模型降阶证明'),
 'oldcentral':('p0881–p0888（高阶生成路线；专门余弦式为旧v10补充）','integrators_full_coil.md:63–104','../stage3/program/rom_integrators.py:15–60','stage5/results/closed_loop/results.json; stage5/results/closed_loop/verification.json','不重用不适用的专式；重用通用Central4算法','新ROM使用完整H导数','是：旧磁势专式；新非可分通用式另证'),
 'oldnormal':('p0435–p0520','chnn_kam_restored.md:110–175','resonance_research.py; resonance_normalform_pair.py','stage5/results/resonance/S5_R03_pair_reduction.json','旧非共振余弦成果保留，新1:1不能套双角平均','否：该旧专式不用于新ROM','旧代数/条件论证成立，3D无直接迁移'),
}
meta['gauge']=('p0848/m0364;p0851/m0366','birkhoff_transport.md:57–61','transport_cache.py:83–130','stage5/results/transport/fullcoil_collocated/inverse_verified.json','stage5有源规范存在；物理H规范此前未实算，本轮补齐','本轮新24D独立计算','是：光滑规范恒等式，不消除表示误差')
meta['variational']=('p1113/m0499;p1114/m0500;p1120/m0505','corrected_mathematics.md:110–151','corrected_identities.py:142–168','stage5/results/corrected_identities/latest.json','变分原理已恢复；完整微分算子本轮实际检查','本轮新24D off-shell检查','是：闭性与相容下形式自伴，不是Df对称')
meta['chartdefect']=('p0862–p0879;p1003/m0442','birkhoff_transport.md:104–149','moser_chart.py:39–113; transport_cache.py:83–130','stage5/results/transport/fullcoil_collocated/inverse_verified.json','已有图/原场误差分离，本轮补完整缺陷分解','是：既有积分，本轮新导数分解','理想条件恒等式；数值额外缺陷不能删除')

newscopes={
'gauge':('实施固定z的B=H规范并验证不改变fa和原场残差','program/fusion_theory.py:15–81','tests/test_fusion_theory.py','results/theory/S6_THEORY02/results.json#gauge'),
'variational':('实现微分算子形式自伴检验及Df不对称反例','program/fusion_theory.py:112–121','tests/test_fusion_theory.py','results/theory/S6_THEORY02/results.json#formal_operator'),
'chartdefect':('补齐内部辛缺陷与逆图链式缺陷的恒等式','program/fusion_theory.py:84–109','tests/test_fusion_theory.py','results/theory/S6_THEORY02/results.json#chart')}

rows=[];chapters=[]
for short,byline in notes.items():
    fname=short+'.tex'
    english=[u for u in INDEX['review_units'] if u['source']=='english/sections/'+fname]
    chinese=[u for u in INDEX['review_units'] if u['source']=='chinese/sections/'+fname]
    assert len(english)==len(chinese)==len(byline),(short,len(english),len(chinese),len(byline))
    for en,zh in zip(english,chinese):
        assert en['labels']==zh['labels'],(en['id'],zh['id'])
        title,category,limit=byline[en['line_start']]
        origin,proof,code,res,inherit,verified,general=meta[category]
        for unit,other in [(en,zh),(zh,en)]:
            # Exact old formula-label anchor where preserved; general supplement
            # did not exist there, so use original separate-material location.
            old=oldroot/unit['source']
            anchors=[]
            if old.exists():
                lines=old.read_text().splitlines()
                for label in unit['labels']:
                    anchors += [str(old.relative_to(ROOT))+':'+str(i+1)+'#'+label for i,l in enumerate(lines) if '\\label{'+label+'}' in l]
                if not anchors:
                    normalized=lambda s:re.sub(r'\s+','',s)
                    target=normalized(unit['tex'])
                    alltext=old.read_text()
                    # Unnumbered formulas retain a precise section source even
                    # when multilingual prose differs; avoid inventing labels.
                    if target in normalized(alltext):
                        anchors=[str(old.relative_to(ROOT))+':'+str(max(1,unit['line_start']-(2 if short=='supp_structure' and unit['line_start']>35 else 0)))+' (same displayed equation)']
                    else:anchors=[str(old.relative_to(ROOT))+' (对应论证，显示式未逐字匹配；见本行新稿锚点)']
            else:anchors=['旧v10独立文件未含此补充；一般材料 '+C+':39–269']
            stage6action='直接继承正确既有推导/算法；不改冻结来源'
            newcode='不新增重复算法';tests='stage5/tests/test_corrected_identities.py (只覆盖本行相应恒等式，完整继承/实际实验由stage5_results单列)'
            evidence=res
            if category in newscopes:
                stage6action,newcode,tests,evidence=newscopes[category]
                newcode=S6+newcode;tests=S6+tests;evidence=S6+evidence
            if category=='transport' and en['line_start']==56 and short=='supp_general_birkhoff':
                stage6action='直接实现完整线圈κ(t)非自治卷积源规范，不重复自治算法';newcode=S6+'program/nonautonomous_transport.py';tests=S6+'tests/test_nonautonomous_transport.py';evidence=S6+'results/algorithms/time_gain_r2_completed.json'
            if category=='reference':
                stage6action='本轮以真实三维学习参考与线圈端口连接，详独立history模块';newcode=S6+'program/learned_reference_tracking.py';tests='由本轮history专题的实际实验校验，非本条宣称新理论';evidence=S6+'results/history/S6_T01/results.json'
            row=dict(id=unit['id'],source=unit['source'],line_start=unit['line_start'],line_end=unit['line_end'],labels=unit['labels'],topic=title,
                original_1025=OMML+origin,old_v10='; '.join(anchors),general_birkhoff=C+(':'+{'transport':'39–148','gauge':'125–148','chart':'152–237','endpoint':'183–220','generator':'222–269','control':'271–333','chartdefect':'335–480','variational':'39–148','form':'39–94'}.get(category,'1–36（路线接口，非该专门公式证明）')),
                stage4='stage4/audit/birkhoff_full_audit.md'+('#2–7' if category not in ['kam','learning','features','complex','normalform','oldnormal','reference'] else '; stage4/audit/chnn_kam_inheritance.md'),
                stage5_code='; '.join((G+z.strip()).replace('stage5/program/../stage3','stage3') for z in code.split(';')),
                stage5_proof='; '.join(P+z.strip() for z in proof.split(';')),stage5_results=res,
                fusion_verdict='本条显示式在声明的局部/模型假设下成立；'+limit,
                stage5_inheritance=inherit,stage6_action=stage6action,new_code=newcode,tests=tests,evidence=evidence,remaining=limit,
                material_exists='是：ZIP CRC/SHA核验及原生TeX完整阅读',mentioned='是：显示式及相邻证明已读',derivation_inherited=inherit,
                algorithm_reused=('不适用：纯条件定理/模型专式' if category in ['oldmodal','oldnormal','kam'] else '是或部分，具体函数见stage5_code；未将公式存在当实算'),verified_on_3d=verified,generalization_proved=general,
                review_note='独立数学核对；中英对应 '+other['id']+' 已比较，结论共享；本条 '+title+'。不把条件性定理/历史对象/局部采样相互替代。')
            rows.append(row)
    chapters += [dict(source=lang+'/sections/'+fname,full_text_read=True,scope='完整正文、证明、公式及条件语句，不仅搜索label',counterpart='chinese' if lang=='english' else 'english') for lang in ['english','chinese']]
assert len(rows)==190
(OUT/'annotations/theory.json').write_text(json.dumps(dict(reviewer_scope='Birkhoff / A-B / original30–36 / Central4 / related supplement mathematics',chapters=chapters,rows=rows),ensure_ascii=False,indent=2)+'\n')
print('WROTE',len(rows))
