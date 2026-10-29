"""Explicit evidence decisions for the 115 inherited rows; no bulk pass rule.

This creates an auditable update manifest, then update_inheritance.py preserves
the original 21 columns. The transport rows remain provisional until their
independent final evidence is incorporated. Historical results retain their
original model identity and are not recertified by new files or tests.
"""
from pathlib import Path
import csv
import json

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'stage5/results/ledgers/stable_branch_updates.json'
P='stage5/proofs/corrected_mathematics.md'
I='stage5/program/corrected_identities.py'
E='stage5/results/corrected_identities/latest.json'
CP='stage5/proofs/coil_energy_ports.md'
CC='stage5/program/coil_rom.py'
CE='stage5/results/coil/validation.json'
IP='stage5/proofs/integrators_full_coil.md'
IC='stage5/program/closed_loop.py'
IE='stage5/results/closed_loop/results.json; stage5/results/closed_loop/verification.json'
LC='stage5/program/learning_models.py; stage5/program/run_learning_research.py'
LE='stage5/results/learning/S5_L01_results.json; stage5/results/learning/S5_L01_freeze_before_test.json'
RP='stage5/proofs/rod_transfer.md'
RC='stage5/program/rod_transfer_control.py; stage5/program/run_rod_transfer.py'
RE='stage5/results/rod_transfer/analysis.json; stage5/results/rod_transfer/refinement.json'
NC='stage5/program/resonance_research.py; stage5/program/resonance_normalform_pair.py'
NE='stage5/results/resonance/S5_R01_results.json; stage5/results/resonance/S5_R02_results.json; stage5/results/resonance/S5_R02_forward_ad_failed_results.json'
NOMAN='阶段5仍为代码/证明/实验包，不是完整正式新论文'
rows={}

def put(ids,status,code,proof,evidence,missing,*,reuse='new_implementation：不是伪称原代码直接复用',verified='no：该项未在真实三维模型上独立完成',theory='conditional：仅所列假设内的推导，不是完整目标推广',derivation='partial：继承及修正范围见对应证明',mentioned='yes：所列证明/结果内明确论述'):
    for rid in ids.split():
        if rid in rows:raise ValueError(f'duplicate {rid}')
        rows[rid]=dict(stage5_status=status,
            stage5_material_exists='yes：所列新增源/结果实际存在' if code or evidence else 'historical_only：见保留的原21列精确来源',
            stage5_mentioned_in_latest=mentioned,
            stage5_full_derivation_inherited=derivation,
            stage5_algorithm_reused=reuse,stage5_verified_on_3d=verified,
            stage5_generalization_proved=theory,stage5_source_code=code,
            stage5_proof=proof,stage5_evidence=evidence,
            stage5_missing=missing,stage5_next_action=missing)

def old(ids,status,missing,*,proof='',evidence='',code=''):
    put(ids,status,code,proof,evidence,missing,reuse='no_new_reuse：历史有效内容及原始对象保留',
        verified='not_rerun：旧结果不冒称三维新验证',theory='no_new_generalization',
        derivation='historical_preserved：本轮未重新展开/推广该旧证明',
        mentioned='partial：继承账本保留；不是已融入完整新论文')

# Birkhoff: algebraic corrections and legitimate full-coil branches are settled;
# general transported charts are explicitly not upgraded by those branches.
put('B01','E06/E13变分符号恢复并独立核验',I+'#birkhoff_field',P,E,'一般真实反馈图输运验收另列',derivation='yes：R7–R9完整变分和符号证明')
put('B02','E12二形式半因子/闭性修正；不把闭性当非退化',I+'#twoform_evaluation',P,E,'实际全图非退化域与统一逆界仍需图证据',derivation='yes：R7与d²=0，非退化独立假设')
put('B03','E13负D与时间相容性分开实现',I+'#time_compatibility_defect',P,E,'任意闭环的兼容一形式不得由符号正确直接推出',derivation='yes：R8–R9完整符号链')
put('B04','E14加权体积修正，三自由度解析回归通过',I+'#transported_volume_ratio',P,E,'不是欧氏体积保持；高维实际图另验',derivation='yes：R10来自拉回二形式最高次幂')
for rid,title in [('B05','一般高阶一形式输运'),('B06','规范改变B但不消除表示误差'),('B07','Moser辅助积分与完整时间项'),('B20','一般真实24D图匹配与场误差分离'),('B21','一般图窗口/成本与长窗限制')]:
    put(rid,'pending：'+title+'等待最终独立输运证据',
        'stage5/program/transport_native.py; stage5/program/transport_cache.py; stage5/program/moser_chart.py',
        'stage5/proofs/birkhoff_transport.md','stage5/results/transport/prototype_r2_jac1.json',
        '只保存当前实现与原型；最终一般场/同共点场图验收和被拒高阶AD路径须单独更新',
        verified='pending：禁止用固定阻尼分支替代一般场',theory='conditional_local：不宣称全域构造')
put('B08','Theorem A端点相容/横截/双向局部证明恢复',I+'#endpoint_gradient_jacobian',P,E,'一般时变图实例的统一横截域待验；不能逆生成Hessian',verified='algebra_only：24D端点矩阵已验，不是完整3D闭环图',derivation='yes：A1–A3及反向证明')
put('B09','Theorem B固定w PDE与k+1递推恢复',I+'#fixed_endpoint_rhs; '+I+'#central_generator_coefficients',P,E,'真实24D任意阶生成函数/解析域成本未完成',derivation='yes：B1–B4，含Psi_N链式项与截断重构')
put('B10 B11','原30/31矩阵及联合逆完整恢复',I+'#original_endpoint_matrix; '+I+'#endpoint_inverse',P,E,'时变非正则图不能直接套常正则端点矩阵',verified='algebra_only：24D往返及相容矩阵通过',derivation='yes：完整变量顺序及逆矩阵')
put('B12','原32固定初端链式法则修正',I+'#fixed_endpoint_rhs',P,E,'实际时变图显式时间项待图模块验收',derivation='yes：Theorem B与原32正确块导数')
put('B13 B14','原33候选curl非零反例保留；原34增量不是生成存在证明',I+'#gradient_integrability_defect',P,E,'一般非比例控制须构造合法相容图，不修饰错误候选',derivation='yes：P=-p符号及混合偏导反例')
put('B15','完整变质量中点进入实际全线圈同场Newton',IC+'#implicit_midpoint; '+I+'#mechanical_field',IP+'; '+P,IE,'流/接触ROM闭合和长期留域常数未证明',reuse='yes：实际RodROM与完整磁能梯度复用；中点Newton新增',verified='yes_limited：12DOF全线圈三光滑分支4/8/16步，约2阶',derivation='yes：几何惯性和未知中点控制均完整')
put('B16','原36非交换左解修正，变质量采用完整非线性残差',I+'#midpoint_linear_mechanical_step; '+IC,P+'; '+IP,E+'; '+IE,'常矩阵闭式不得用于变质量或一般反馈',verified='yes_limited：常矩阵独立反例+真实24D完整残差',derivation='yes：矩阵次序、可逆假设、常/变质量责任区分')
put('B17','普通中点约2阶；反馈不保持K0的反例实测',IC,IP,IE+'; stage5/results/closed_loop/independent_checks.json','同场Ku图仍单独pending；短窗不是长期证书',verified='yes_limited：共点原K0缺陷3.9259e-4，未掩盖',derivation='yes_conditional：隐函数和局部误差证明')
put('B18','旧非可分Central4进入全线圈保守变质量分支',IC+'#step',IP,IE,'只对固定电流保守分支；一般反馈拒绝套用',reuse='yes：调用stage3继承的Central4标量生成实现，保留全混合导数',verified='yes_limited：真实24D实测阶3.996642，浮点结构缺陷另报',derivation='yes：S=hH+h³fᵀHessian(H)f/24及原函数')
put('B19','E15旧闭/恰当差别修正；中心方法单值分支给明确原函数',I+'#torus_primitive_periods; '+IC,P+'; '+IP,E+'; '+IE,'旧环面测度有效部分保留；原KAM证书不重跑或迁移',verified='partial：中心24D结构实测；环面周期为独立回归',derivation='yes：周期障碍与中心离散原函数明确')
put('B22','真实共点控制保持原K0已否定；Ku仍待同场图验收',IC+'#structure; '+CC+'#feedback_jacobian',IP+'; '+CP,'stage5/results/closed_loop/independent_checks.json; '+CE,'同一共点场Ku一般图最终结果待汇总；受限36维不得套24维证明',verified='yes_negative：原K0缺陷与完整反馈Jacobian实测',theory='conditional：Lie相容条件；不存在任意控制保原K的结论')
put('B23','同一实际闭环完整残差与有限时间误差依赖恢复',IC,IP,IE,'统一L、留域及ROM/模型/分配误差常数未认证',verified='yes_limited：步长、残差、条件数、独立参考细化',derivation='yes_conditional：e_N≤C_T(e0+h^p+Σeta)')
old('B24','新三维闭环离散KAM未证明','需选定exact-symplectic保守映射、解析域、离散小除数及twist；耗散闭环不自动满足',proof=IP,evidence='stage5/results/resonance/S5_R02_results.json')
old('B25','历史非自治分块Gauss4证据保留，本轮不新增这条方法','不把一般ODE Gauss4与时变图分块Gauss4混同',proof=IP)
put('B26','冻结反馈错误被完整链式Jacobian修正；36维受限映射独立审计',IC+'#jacobian; stage5/program/closed_loop_sampled.py',IP+'; '+CP,'stage5/results/closed_loop/independent_checks.json; stage5/results/closed_loop/sampled_jacobian.json','活动集光滑性、秩亏和电流记忆不自动满足辛/KAM',verified='yes：完整反馈方向差分2.17e-11，36×36实际映射求导',derivation='yes：物理固定输入偏导+控制复合导数')
old('B27','旧已知共轭与v10特殊回归继续作为独立基准','不能作为任意新三维一般图已完成证据',evidence='stage5/results/regression/execution.json')

# Complete complex learning: newly trained objects, not recreated old weights.
put('CK01', 'E04规范复坐标修正与实际训练正则梯度对齐',I+'#wirtinger_real_energy; '+LC,P,LE+'; '+E,'尚无统一复解析域误差',reuse='independent_correct_implementation：新训练采用D grad_x；未调用修正helper',verified='yes_limited：12DOF真几何标签与三种模型三seed',derivation='yes：sqrt2链式因子；实正则尺度另显式记录')
put('CK02','E16物理Rayleigh解码修正；新控制使用实际磁功率端口',I+'#rayleigh_force_from_momentum_gradient; '+CC,P+'; '+CP,E+'; '+CE,'ROM比例拖曳是合成载荷；未实现Morison附加质量或完整Metriplectic',verified='partial：Rayleigh独立非对角质量测试；3D磁端口已验')
put('CK03','E05能量漏项/共轭方向修正；新训练实际使用真实H梯度误差',I+'#complex_energy_rate_squared; '+LC,P,LE+'; '+E,'没有把Hdot=0当受迫开放机械能假设；完整开放系统损失仍待研究',reuse='independent_correct_implementation：真实Hamiltonian实梯度训练；非原错误复损失',verified='yes_limited：真实24D新训练，不是复域一致界')
old('CK04','旧35参数余弦/混合四次结果保留其原始低维对象','新8749机械多项式只是扩大后的有限特征基准，不替代或伪造旧35参数权重',code=LC,evidence=LE)
put('CK05','新增8749/7104/13440参数三类×3seed公平协议；函数族容量不同明列',LC,'',LE,'不同先验/容量/优化率不能称严格等容量最优对照；旧35/45原比较仍保留',reuse='yes：第二阶段ComplexResidual与MechanicalComplexResidual直接复用',verified='yes：同1024train/256validation/512test/256OOD，先冻结后标签',theory='no：实验协议不证明全域网络最优',derivation='partial：已有结构继承；新比较为实测')
old('CK06','旧严格复梯度下降结论未被Adam训练替代','需把旧定理具体假设与新复网络/Adam分开；本轮未给新收敛证明',code=LC,evidence=LE)
put('CK07','完整complex128可训练网络真实新训练并保存9权重',LC,'',LE,'不是只拟合磁势系数；完整网络高曲率与OOD失败仍需改进',reuse='yes：直接import原完整ComplexResidual及SPD复架构',verified='yes：复隐藏网络新test相对场误差0.0324–0.0370',theory='no_new_learning_theorem',derivation='partial：架构/训练完整保留，复域推广未证')
old('CK08','split-tanh实解析与独立复化边界保留','新权重没有认证复域极点距离与一致误差；不称整实H为holomorphic',code=LC,evidence=LE)
old('CK09','旧meromorphic tanh失败继续保存；新高阶AD又发现独立失败','保留旧零点jet与新mixed-AD失败，不能用小训练误差抹去导数缺陷',code=NC,evidence='stage5/results/resonance/S5_R02_forward_ad_failed_results.json')
put('CK10','训练归一化D与正则场J D grad_x统一进入loss和指标',LC+'#metrics','',LE,'经验范数不是复解析域sup界',reuse='new_corrected_training_protocol',verified='yes：全部9个新模型按正则场而非x梯度评价',theory='identity_only：链式法则成立，统计泛化界未证',derivation='yes：尺度、损失和物理秒数omega0明确')
put('CK11','保留非受限H_PP负曲率，独立有限差分确认',LC+'#hpp_legendre','',LE,'8点/分支是有限检查；真动量初始化root成功不等于正确反解或全域凸性',verified='yes_negative：complex test2/2/4点非正；多项式各4点非正',theory='no_convexity：观察反例',derivation='partial：Legendre条件与反例清楚')
put('CK12','继承SPD机械复网络并重新训练',LC,'',LE,'点态SPD不等于准确；全域下界和物理Legendre误差仍需认证',reuse='yes：原MechanicalComplexResidual实际导入',verified='yes_limited：test与OOD所查各8点全部正定',theory='conditional_pointwise：架构SPD条件沿用；无全域误差证书',derivation='yes_for_architecture：机械形式保留，非完整解析界')
put('CK13','SPD结构/准确性分离继续保留；OOD场误差约0.207–0.219',LC,'',LE,'当前SPD误差明显大于自由复网络；不能按SPD即准确宣传',reuse='yes：旧SPD完整结构进入新训练',verified='yes_negative_limit：误差和真实速度反解偏差均保存',theory='no_accuracy_certificate')
put('CK14','全部9检查点先冻结，随后生成独立test/OOD标签',LC,'',LE,'历史缺权重保持缺失；新检查点不是原权重复现',reuse='yes：复用几何标签，新增冻结协议',verified='yes：明确SHA和sample indices',theory='no_statistical_uniform_bound',derivation='not_a_proof：数据隔离协议')
old('CK15 CK16 CK17','旧有限特征Gram/状态观测/统计覆盖桥梁有效条件保留','未将旧有限字典范数证明推广到新完整网络或24D复解析域；需要新非退化/覆盖/噪声和解析常数',code=LC,evidence=LE)
old('CK18','旧完整Lie正规形证明保留；新增三维选定共振对四阶NF','本轮NF只给选定四实坐标的限制四阶项，虽计全12模态三次消去反馈，未算全24D所有四阶项或认证余项',code=NC,evidence=NE)
old('CK19 CK20 CK21','旧冻结有限幅值连续KAM/三对象身份/极薄管测度结果保留','原证书仍只覆盖其原两模态或指定学习对象；新三维没有解析域、小量与twist证书',evidence=NE)
put('CK22','E15闭原函数差不能冒称恰当辛的错误修正',I+'#torus_primitive_periods',P,E,'旧测度/闭形式有效部分保留；未重跑KAM证书',verified='no_new_3d_KAM：周期反例独立验',derivation='yes：周期障碍与作用常数参考修正')
put('CK23','非可分Central4完整混合导数在新全线圈H运行',IC,IP,IE,'只保守固定输入分支；不把学习非SPD或受限闭环直接套用',reuse='yes：旧Central4经stage3实现调用，非新低维替代',verified='yes：真实24D约四阶',derivation='yes_conditional：局部生成与exact primitive')
old('CK24','连续/离散KAM小除数责任保持分开','有exact中心分支仍须新离散步长非共振、twist和解析小量；1:1共振不能忽略',proof=IP,evidence=NE)
put('CK25','真实3D SO2与1:1共振研究推进至选定对四阶正规形',NC,'',NE,'不是不变低维子流形证明；未给约化twist、统一解析余项或KAM；mixed高阶AD失败已拒收',reuse='yes：实际12DOF几何H，完整12模态泊松括号反馈；旧低维证书不迁移',verified='yes_limited：纠正后角项系数约−0.0066025，原四阶约−434.7256',theory='finite_order_formal：有限阶浮点正规形，不是KAM证书',derivation='partial：三次消去与受限四阶计算，未全24D四阶')
old('CK26 CK27','旧64平面自由度提升与S形跟踪成果有效保留','新三维杆控制不是旧64平面模型证明的无条件推广；本轮未重跑旧全套S形结果',code=RC,evidence=RE)
old('CK28','旧四种学习前馈转移保留；新完整CHNN尚未真正施加到杆','新杆实验采用实际电流共点反馈；不能借它声称新完整学习控制转移已完成',proof=RP,code=RC,evidence=RE)
put('CK29','从单磁势系数推进到完整网络训练和真实全coil可达投影诊断',LC+'; stage5/program/coil_control.py',CP,LE+'; '+CE,'学习标签仍理想均匀偏置；全coil残差投影是诊断，尚非新网络闭环导航',verified='yes_partial：训练与真实端口诊断完成；学习控制闭环未完成',theory='no_new_control_performance_theorem')
old('CK30',NOMAN,'仍需把完整CHNN/复域误差/共振约化/连续与离散KAM/全杆学习控制连接成论文，而非仅新增实验',proof='stage5/notes/unified_model_contract.md',evidence=LE+'; '+NE)

# Original-route rows keep their exact OMML anchor and prior identities intact.
put('O001','最终三维血管目标继续保留，分清ROM分析层与全杆应用层',CC+'; '+RC,'stage5/notes/unified_model_contract.md',CE+'; '+RE,'全双向FSI、柔性壁、生理和闭合误差尚未完成',reuse='yes：原三维几何ROM与Cosserat均真实复用',verified='yes_intermediate：全coil ROM与有流/接触全杆；不是最终应用验证',theory='no_complete_pipeline_proof')
put('O002 O003','完整三维导演标架/平转惯性保留；Kirchhoff明确约束伸长剪切',CC+'; '+RC,P+'; '+RP,CE+'; '+RE,'ROM省略伸长剪切；模型间误差与适用极限待证明',reuse='yes：真实RodROM及完整SO3 Cosserat方程复用',verified='yes_limited：16/32/64段剪切伸长支路与12DOF弯扭分支',derivation='partial：E03修正和各分支职责；非从PDE全误差推导')
put('O004','Maxwell源外全线圈场与一致磁能/虚功实际闭合',CC+'#field_basis_tensor; stage5/program/rod_transfer_control.py#current_power_port',CP+'; '+RP,CE+'; stage5/results/rod_transfer/operator_tests.json','局部偶极/准静态/无铁芯假设及真实硬件标定仍需说明',reuse='yes：继承第二阶段圆线圈与磁力矩实现；新增ROM完整AD磁能',verified='yes：3D线圈独立SI闭式、虚功与梯度',derivation='yes_conditional：能量变分包含位置力与姿态力矩')
put('O005','E01量纲与供能修正可执行；全杆只继承规定流拖曳',I+'#corrected_morison_transverse; '+RC,P+'; '+RP,E+'; '+RE,'附加质量尚未进入M/求解；受限血管Morison标定与FSI未完成',reuse='partial：helper新增；全杆独立正确拖曳已继承，未调用完整Morison helper',verified='partial：3D投影恒等式测试和真实杆流力；非完整Morison闭合')
put('O006','E02实穿透/罚能/摩擦修正，并独立激活杆接触',I+'#contact_penalty; '+RC,P+'; '+RP,E+'; '+RE,'柔性壁/严格不穿透/切换良定性未完成；0.2s主例零接触不能代替压力支路',reuse='yes_independent：原杆正部穿透法则实际复用；helper独立回归',verified='yes_limited：压力支路61.6μm穿透和11.35μN法向力',derivation='yes_for_penalty：罚势与相对摩擦功率；非真实壁定理')
old('O007','微重力合成载荷保留，未冒称空间站生理标定','需要有依据的残余加速度、血流和血管边界参数',proof=RP,code=RC,evidence=RE)
put('O008','中心线式不能取代独立扭转/角动量已作反例和模型分工',I+'#darboux_perpendicular; '+RC,P+'; '+RP,E+'; '+RE,'从全Cosserat到12DOF的可控截断误差未证',reuse='yes：全杆材料标架与角平衡保留',verified='partial：独立扭转反例和全杆模拟，非PDE极限定理')
old('O009','Galerkin弱式/边界功旧推导保留；新匹配模型误差真实测量','需完整全杆→Ritz误差、边界层及开放载荷投影理论；两毫秒小差不是收敛证明',proof=RP,code='stage5/program/run_rod_transfer_matched.py',evidence='stage5/results/rod_transfer/matched/model_difference.json')
put('O010','真实M(q)与全部惯性持续进入H、f、积分和训练',CC+'#hamiltonian_tensor; '+I+'#mechanical_field; '+LC,P+'; '+CP,CE+'; '+IE+'; '+LE,'真实Morison附加质量/伸长剪切进入ROM仍待完成',reuse='yes：实际RodROM.mechanics及梯度，不冻结M',verified='yes：三维质量与磁端口、24D积分、真几何训练',derivation='yes：Legendre与几何惯性完整链')
put('O011','势能先定义后求梯度，未保留不可积的任意K(q)q积分',CC+'#hamiltonian_tensor',CP,CE,'一般指定广义力可积性仍需逐场检查',verified='yes：弹性+完整磁能统一求导与独立虚功',derivation='yes_for_defined_energy：不声称任意力都存在势')
put('O012','固定偏置H、瞬时含磁H与机械能三种功率账区分',CC+'; '+IC+'#energy_and_power; '+RC,CP+'; '+RP,'stage5/results/coil/closed_loop_summary.json; '+RE,'完整流体/壁内能尚未形成双向封闭能量账',verified='yes：实际全coil轨迹和全杆外端口功率',derivation='yes：电流显式参数功与磁外功不重复')
put('O013','正则次序z=(Q,P)、K0=-J与复尺度统一',I+'#canonical_J; '+CC,P+'; '+CP,E+'; '+CE,'正则尺度本身不认证学习复域',verified='yes_limited：24D正则尺度与场接口')
old('O014','机械耗散与Metriplectic双退化责任保持区分','当前磁共点负功率不是完整能量-熵扩展；内能/熵状态及耦合尚待接入',proof=P,code=I+'#rayleigh_force_from_momentum_gradient',evidence=E)
put('O015','原17–21归一化由E04纠正；新训练梯度使用正确正则尺度',I+'#wirtinger_real_energy; '+LC,P,E+'; '+LE,'复域H误差与正规形小量还没有连接',reuse='independent_correct：新训练链式正确，helper用于独立回归',verified='yes_limited：24D几何标签训练；不是holomorphic实H断言')
put('O016','能量损失漏项/共轭错误纠正，完整复网络新训练',I+'#complex_energy_rate_squared; '+LC,P,E+'; '+LE,'开放流体接触机械功率损失尚未进入新网络；学习闭环待做',reuse='partial：正确架构复用，错误旧损失不沿用',verified='yes_limited：9个新checkpoint及经验误差')
old('O017','CR充分性与实Hamiltonian复延拓问题不被网络实样本训练替代','必须证明共同解析复域、极点距离、实切片和一致学习误差',proof=P,code=LC,evidence=LE)
put('O018','原非保守F1候选混合偏导矛盾已修复为显式拒收测试',I+'#gradient_integrability_defect',P,E,'一般输运构造的实际高维场验收仍pending',derivation='yes：E06反例不因改写符号而抹去')
for rid,source in [('O019','B08'),('O020','B09'),('O021','B10'),('O022','B12'),('O023','B13'),('O024','B16'),('O025','B18'),('O027','B02')]:
    rows[rid]=dict(rows[source])
put('O026','原Uk通过真实12电流端口进入场/中点/采样控制',CC+'; stage5/program/coil_control.py; '+IC,CP+'; '+IP,CE+'; stage5/results/closed_loop/sampled_jacobian.json','任意相空间增量不可实现；受限残差、采样36维和Ku责任保留',reuse='yes：继承真实磁结构，新完整电流控制接口',verified='yes：真实不可达残差与受限闭环，不是任意Uk',derivation='yes_conditional：端口功率/可达与反馈链式')
old('O028','连续/离散非共振责任明确，三维共振推进到有限阶NF','全24D共振约化、twist、解析余项及KAM小量未证；不得套旧两模态证书',code=NC,evidence=NE)

# Physical route duplicates have distinct original anchors retained in column 3.
for rid,source in [('PHY01','O001'),('PHY02','O002'),('PHY03','O008'),('PHY04','O003'),('PHY05','O003'),('PHY06','O008'),('PHY07','O004'),('PHY08','O004'),('PHY09','O005'),('PHY10','O005'),('PHY11','O012'),('PHY12','O006'),('PHY13','O006'),('PHY15','O007'),('PHY16','O010'),('PHY17','CK02')]:
    rows[rid]=dict(rows[source])
old('PHY14','接触阻尼仅有限光滑，未宣称解析或全局Lipschitz','需独立接触切换良定性与阶数论证；ROM光滑中点阶不能移植',proof=RP,code=RC,evidence=RE)
put('PHY18','完整BiotSavart、AD能量梯度、解析空间梯度和SI单位互验',CC,CP,CE+'; stage5/results/coil/higher_ad_fix_validation.json','硬件/线圈电热标定与全域场证书未完成；高阶mixed AD另单独拒收/修复',reuse='yes：原线圈物理与解析梯度继承；新增可微能量接口',verified='yes：闭式轴上场/散度旋度/虚功/差分/求积',derivation='yes_for_quasistatic_dipole_model')
put('PHY19','约98.5%全场相对仿射力差保留，进一步实际闭环轨迹差',CC+'; stage5/program/run_coil_closed_loop.py',CP,CE+'; stage5/results/coil/closed_loop_summary.json','不能把全场控制对仿射控制短窗未分辨收益说成提升；空间模型差仍大',verified='yes_negative：全/仿射植物状态差3.907e-4；控制差约积分误差',theory='numerical_observation：不是任意位形误差界')
put('PHY20','共同物理q和公共Q基上20/40/80单元磁积分比较',CC+'; stage5/program/run_coil_validation.py',CP,CE,'20单元本身未认证空间收敛；全杆约束和更细误差另验',verified='yes：相邻全力差0.0058667、0.0014576',theory='finite_grid_observation')
put('PHY21','局部8场端口推进为完整12电流真实广义力接口',CC+'#current_port; stage5/program/coil_control.py',CP,CE,'12电流不等于12独立力；全域秩及受限最优性未证',verified='yes：20/40/80端口秩5/7/7，分配残差明确',derivation='yes：G=-D_Q phi^T及正交不可达分解')
put('PHY22','真实总电流连续斜坡幅值/变化率进入ROM与全杆', 'stage5/program/coil_control.py; '+RC,CP+'; '+RP,'stage5/results/coil/closed_loop_summary.json; '+RE,'不是零电流偏置启动验证；投影/斜坡不自动被动',verified='yes：±2A、20A/s及连续性实测',derivation='yes_conditional：端点凸盒与线性斜坡')
put('PHY23','管域固定采样约束与实际移动磁点检查分开',RC+'; stage5/program/coil_control.py',RP+'; '+CP,RE+'; '+CE,'连续全空间界未认证；matched局部偏置上游0.798T/m超界已保留',verified='yes_limited：主控制采样可行，matched明确超界诊断',derivation='conditional：固定采样点凸性不等于连续血管域')
put('PHY24','新共点电流反馈真正进入16/32/64三维全场轨迹',RC,RP,RE,'仅0.2s；名义前馈仍依赖局部场；未完成最终导航',reuse='yes：原全杆和全coil力求解直接复用，新增真实端口控制',verified='yes：7组、主例有流有壁、独立接触支路',theory='no_global_tracking_theorem')
old('PHY25','旧四种学习控制杆转移保留；新完整学习尚未转移','需把新独立冻结完整CHNN误差经真实端口施加到32/64段并重测',proof=RP,code=LC+'; '+RC,evidence=LE+'; '+RE)
old('PHY26','旧Womersley同流量比较保存，不在本轮重跑','新全杆仍规定脉动流；没有证明双向流固或微重力生理',proof=RP,code=RC,evidence=RE)
put('PHY27','保留非共点失败，新共点受限执行也未保证跟踪改善',RC+'; stage5/program/rod_transfer_analysis.py',RP,RE+'; stage5/results/rod_transfer/initial_allocator_failure/','新增反馈略差baseline；优化微误差导致负阶已修复但剩余低时间阶待研',verified='yes_negative：RMSE0.320032mm>0.318558mm；初次−10.72阶保留',theory='no_performance_superiority_claim')
put('PHY28','同一磁功率端口、杆时间空间细化与匹配模型差实际执行',RC+'; stage5/program/run_rod_transfer_matched.py',RP,RE+'; stage5/results/rod_transfer/matched/model_difference.json','时间阶0.469未达二阶；匹配差不单调趋零；有流/接触ROM误差未闭合',verified='yes_limited：空间观察阶1.007，开放机械功率账与2ms匹配诊断',theory='conditional_port_identity_only：有限差不构成全误差证明')
old('PHY29','最终双向FSI与柔性血管目标保持，尚未实现','需柔性壁牵引/几何/流场双向耦合、附加质量、参数标定和独立验证',proof='stage5/notes/unified_model_contract.md')
old('PHY30','完整开放杆无连续/离散KAM证书','保守分析分支须独立域/共振/非退化/映射条件；接触采样不能套保守证书',proof=IP+'; '+RP,evidence=NE)

# Corrections are fully distinguished from actual adoption of their hypotheses.
repairs={}
remaining={
 'E01':'附加质量尚未一致进入杆或ROM质量/求解器；受限血管Morison标定、非Newtonian及双向FSI未完成。当前实测只覆盖规定流拖曳。',
 'E02':'真实柔性壁/接触参数、严格不穿透、切换良定性与解析性未证明；压力支路为罚模型数值验证。',
 'E03':'完整Cosserat到Kirchhoff ROM的剪切/伸长极限与截断误差未证；匹配固定偏置诊断超梯度界不能作为受限导航。',
 'E04':'9个新完整网络已训练；缺少共同复解析域一致学习误差、极点/导数认证和KAM小量连接。旧缺失权重仍未补造。',
 'E05':'新真实Hamiltonian梯度损失已正确运行；一般开放系统的复能量/物理功率损失未接入完整网络。',
 'E06':'通用与同共点真实24D输运图的最终相容性、表示场和积分误差仍待单独验收。',
 'E07':'24D端点代数及完整局部证明已验；实际一般时变图的联合逆、横截留域及统一稳定常数仍需图结果。',
 'E08':'保守全coil Central4四阶已实测；任意阶24D生成函数递推及共同解析域/收敛半径、复杂度未完成。',
 'E09':'固定w/初端链式修正已有回归；实际一般时变图的完整显式时间项与端点应用仍待图验收。',
 'E10':'阻尼候选非梯度已被拒收；合法保守/比例分支不替代任意非比例控制的相容生成构造。',
 'E11':'真实全coil变质量完整中点约二阶已测；条件性局部唯一与有限时间界尚无全血管统一常数，受限采样/接触另属对象。',
 'E12':'规范半因子与正则结构已实际采用；闭性仍不蕴含全域非退化，真实一般图需域与条件数证据。',
 'E13':'符号及合法比例分支已验；任意共点反馈Ku的完整输运/原场误差另验，不能凭符号升级。',
 'E14':'加权体积结论只在已定义非退化局部流成立；没有欧氏体积、全域耗散结构或KAM结论。',
 'E15':'旧冻结TeX保持原样；修正周期障碍而保留有效体积结论，没有重跑旧KAM证书或新三维KAM。',
 'E16':'物理Rayleigh链式已独立验证，但真实血流/附加质量与一般学习H_PP全域反解尚未闭合；合成gammaP不能冒称该物理模型。',
}
adoptions={
 'E01':('corrected_morison_transverse数学修正；rod_transfer继承独立正确相对拖曳但未调用该helper、未添加附加质量',RC+'; '+I,RE,'partial：全杆规定流作用实测；完整Morison闭合未完成'),
 'E02':('原杆正部穿透/罚势/摩擦实际复用；helper为独立能量导数回归',RC+'; '+I,RE,'yes_limited：独立接触压力支路实测；非柔性壁定理'),
 'E03':('CoilROM复用SO3几何和独立扭转；Cosserat保留平转平衡/伸长剪切；helper核符号',CC+'; '+RC,CE+'; '+RE,'yes_limited：3D弯扭与全杆；没有ROM误差推广证明'),
 'E04':('learning_research实际采用grad_z=D grad_x独立正确实现；并非调用helper，复坐标归一化另在resonance使用',LC+'; '+NC,LE+'; '+NE,'yes_limited：真24D标签/新训练；非复域误差证书'),
 'E05':('新完整网络训练使用正确H梯度损失，未沿用原错误共轭损失；开放系统复能量损失仅helper核验',LC,LE,'partial：真3D训练已做；Hdot复能量开放损失未接入'),
 'E06':('不相容候选由共享反例拒收；实际一般输运和同共点图待最终结果','stage5/program/transport_native.py',E,'pending：一般3D相容图验收另行更新'),
 'E07':('端点兼容/横截/联合逆共享实现与24D矩阵回归；实际Moser端点图另验',I,P+'; '+E,'algebra_only：不把24D恒等式称为3D全场证明'),
 'E08':('固定w递推恢复；Central4用等价合法中心生成实现进入全coil；任意阶24D递推未完成',I+'; '+IC,IE,'yes_partial：全coil Central4四阶；完整高阶生成求解未完成'),
 'E09':('fixed_endpoint_rhs及原32块修正有独立非自治回归；真实时变图完整时间项待最终证据',I,E,'pending：时变图证据另验；不能仅凭回归升级'),
 'E10':('错误候选梯度明确拒绝；比例加权与保守中心生成合法分支实际采用',I+'; '+IC,IE,'yes_for_legal_branches：不证明一般阻尼候选可积'),
 'E11':('常矩阵左解独立反例；全coil闭环实际用完整变质量未知中点Newton和完整反馈Jacobian',I+'; '+IC,IE,'yes：真实24D完整残差约二阶，常矩阵式不偷用'),
 'E12':('K0=-J及半双重求和约定用于全coil结构诊断；共享函数回归；一般图非退化另验',I+'; '+IC,IE,'yes_for_canonical_diagnostics：非全域一般K非退化证明'),
 'E13':('负D与时间兼容符号恢复；全coil合法比例分支用e^(gamma t)K0，任意反馈Ku另验',I+'; '+IC,IE,'yes_for_proportional_branch：一般输运待最终结果'),
 'E14':('仅宣称加权结构体积；全coil比例分支测加权两形式；三自由度解析行列式测试独立',I+'; '+IC,IE+'; '+E,'partial：3D加权结构实测，欧氏体积不守恒'),
 'E15':('旧环面原TeX冻结，修正周期障碍；新Central4/中点给自己的明确exact原函数',I+'; '+IC,IE+'; '+E,'no_new_KAM：不以中心exact证明替代旧环面exact或KAM'),
 'E16':('helper实现物理Rayleigh链式；CoilROM保持完整M和真实磁功率；-gammaP明确合成阻尼并非本物理Rayleigh模型',I+'; '+CC,CE+'; '+E,'partial：质量/磁端口3D实测；物理Rayleigh完整载荷闭合未完成'),
}
for eid,(adopt,code,evidence,verified) in adoptions.items():
    repairs[eid]=dict(correction_status='implemented_and_independently_tested：数学修正已落地；采用/缺口见本行',
        adopted_by_stage5_modules=adopt+'；实际源码：'+code,
        execution_evidence=E+'; '+evidence,
        stage5_algorithm_reused=adopt,
        remaining_or_missing=remaining[eid],
        stage5_verified_on_3d=verified,
        stage5_generalization_proved='conditional_scope_only：见corrected_mathematics；没有全FSI/微重力生理/新KAM证书')

with (ROOT/'stage4/audit/full_inheritance_matrix.csv').open(encoding='utf-8-sig') as stream:
    original=list(csv.DictReader(stream))
assert set(rows)=={x['id'] for x in original}, ({x['id'] for x in original}-set(rows),set(rows)-{x['id'] for x in original})
manifest=dict(note='逐条核对实际源、证明、JSON和失败证据。通用/同共点输运图仍pending；原21列保持不变。此manifest不是全部研究完成声明。',inheritance=rows,repairs=repairs)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(path=str(OUT.relative_to(ROOT)),inheritance_rows=len(rows),repair_rows=len(repairs),transport_pending=[key for key,value in rows.items() if value['stage5_status'].startswith('pending')]),ensure_ascii=False))
