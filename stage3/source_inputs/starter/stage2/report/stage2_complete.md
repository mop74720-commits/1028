---
title: 三维磁驱动血管内柔性机器人第二阶段研究报告
subtitle: 1025 原稿版本核对 v10 与一般 Birkhoff 融合及实际复算
date: 2026年10月29日
lang: zh-CN
---

# 1 本阶段结论与证据边界

本阶段保留1025所确定的最终对象：空间站微重力环境中，受真实磁场驱动、与脉动血流和血管壁相互作用的三维柔性介入机器人。研究已从原来的理论审查推进到实际运行的三维Cosserat杆、独立的三维Kirchhoff降阶模型、完整复值网络训练、物理磁端口分配，以及一般Birkhoff算法的高维验证。原v10中能够复用的计算链也已按其原始输入重跑。这些是不同证据层次，本文分别给出对象、参数和适用范围。

本报告不宣称已经完成患者特异性双向流固耦合，也不宣称新三维系统已有严格KAM存在性证书。已经找到的失败、架构限制、控制器失稳和不可实现的广义力分量，均与成功结果一起保存。计算结果的逐项数据表见后文；机器可读结果、初值、步长、模型配置、软件版本和执行日志随程序包交付。

两个研究方向保持独立。方向A研究给定闭环场的Birkhoff相容表示、生成函数、原（36）的修正、结构和收敛；方向B研究真实保守模型的学习误差、正规形、连续KAM及可实现磁跟踪。共享的是物理模型、数据和磁端口，不共享未经证明的结构结论或KAM小量预算。

## 1.1 结果的四种状态

| 状态 | 含义 | 本报告中的例子 |
|---|---|---|
| 原数据重算 | 冻结原参数与输入，实际重新执行 | 原v10积分证书、环面证书、64自由度提升、S路径、完整读出训练 |
| 新模型运行 | 本阶段新建程序生成结果 | 16／32／64段三维Cosserat杆、12自由度三维ROM、复网络、线圈分配 |
| 推导或条件结论 | 已写出推导，结论以明列假设成立 | 变质量Hamiltonian、热力学候选括号、Central4、误差分解 |
| 尚未完成 | 尚无对应计算或严格验证 | 双向FSI、测量标定、新三维连续／离散KAM证书、一般图的高维实时算法 |

“数值检查通过”不改写为“严格区间证明”；“已读实现并核对输出”不改写为“重新积分全部轨迹”。只有明确采用区间算术并核验定理所有假设的旧冻结证书，才按其限定对象报告计算机辅助证明。

## 1.2 最主要的已运行结果

| 研究对象 | 本轮结果 | 对论文的直接影响 |
|---|---|---|
| 原v10冻结保守模型 | Central4观察阶3.96—4.00；256-bit积分证书及512-bit环面证书复算通过 | 恢复旧完整链条，但证书对象和冻结权重保持原身份 |
| 新三维Cosserat杆 | 16／32／64段，93／189／381自由配置变量；含规定血流、接触与磁矩 | 已有真正空间杆计算；64段不写成64模态 |
| 32段理想场跟踪 | 无磁控制1.278 mm、静态前馈0.328 mm、加位置反馈0.154 mm RMSE | 可重复的有限时间改善；没有由此证明一般闭环稳定 |
| 12自由度前馈向64段转移 | 线性0.110877 mm、复网络0.112972 mm、解析字典0.276685 mm | 学习已进入高维杆；本任务不支持网络优于线性先验 |
| 完整线圈与连续电流 | 受约束支路0.617328 mm；检查点最大场0.479452 mT、梯度0.024396 T/m、电流2 A、a.e.速率20 A/s | 保留硬件约束代价；原点局部分配越界结果也必须报告 |
| 新完整复网络 | 冻结后的独立确认：局部正则向量场误差1.82%—1.95%，非零学习误差 | 尚非复域上界；域外有动量Hessian负曲率反例 |
| 正质量网络 | 结构上修复正定性，局部确认误差6.86%；压力域98.88%且病态 | 本轮为结构与精度冲突的失败记录，不作为更优模型 |
| 一般Birkhoff算法 | 8／16自由度各类阻尼、变质量和控制；合法图中观察二／四阶 | 不能把高阶普通ODE误差小写成保持任意给定二形式 |
| 一般输运／Moser | 图匹配缺陷约6.68×10⁻¹⁶，原向量场误差约0.1096 | 三种误差必须分开，结构精度不替代动力学一致性 |
| Metriplectic候选 | 总能量／熵扩展满足退化条件；32个真实ROM状态数值核验 | 热状态是有明确构造的后续选项，主机械实验暂不虚构热参数 |

跟踪RMSE的主窗口为t∈[0.5,2] s，包含三维尖端误差；不同磁场实现的约束不同，不能跨行直接排列为统一控制器排行榜。全程初值、离散步长、参考、采样和误差定义见各章与机器可读结果。新三维模型的成对弯曲频率存在1:1共振，新的连续／离散KAM仍为明确未完成项。

# 2 原稿版本与材料身份

## 2.1 1025 三个实际文件的逐层核对

本轮已取得并比较三个实际DOCX文件的完整字节、ZIP内正文XML、纯文本和OMML数学节点。结论是：当前可访问的（2）、（3）、（4）三个文件逐字节一致。该结论来自本轮的实际文件比较；并未根据文件名或先前报告直接认定版本相同。

| 文件后缀 | 文件字节数 | 正文段落数 | OMML数学节点数 | 完整文件SHA256前12位 |
|---|---:|---:|---:|---|
| （2） | 194893 | 1222 | 570 | 8c62b874caaa |
| （3） | 194893 | 1222 | 570 | 8c62b874caaa |
| （4） | 194893 | 1222 | 570 | 8c62b874caaa |

共同完整SHA256为 `8c62b874caaa6362b0f1c5612ddd6514aa7141454b17ef4cf5688408fe307338`。正文XML、文本和数学XML的各自完整摘要见 `notes/version_audit.json`。因此当前三份之间没有公式、章节或研究目标差异。用户尚未指定最终引用文件名，本报告称其为“1025共同文本”，不代替用户选择正式文件名；计算依据不存在分歧。如果以后提供字节不同的同名文件，应重新比较，不能沿用本次同一性结论。

## 2.2 两份第一阶段报告的主次和差异

以118页的 `1025_stage1_review.pdf` 及配套DOCX为主，56页的 `1025_第一阶段系统审查报告.docx` 为交叉核查。两份报告不是同一文件，也不具有相同覆盖深度。详细报告当时说明未收到（2）版，其谨慎限制符合当时材料；现在新增的文件哈希核对解决了这一历史缺口。

| 核对点 | 详细报告作为主依据的内容 | 交叉核查结论 |
|---|---|---|
| 三维模型 | 姿态、界面功率、流体和壁储能、移动边界及RCR端口更完整 | 较早报告的梁验证层不取代三维目标 |
| Birkhoff与原36 | 补空间闭性、时间相容性、图适配、横截条件和误差分解 | 两份的核心修正一致，不能只摘出普通中点的计算式 |
| Metriplectic | 详细报告用熵坐标S及内能U(S)；较早报告用内能坐标e和S(e) | 两者经e=U(S)变换等价，不是数学冲突；本报告给出显式转换 |
| 学习与KAM | 详细报告更细分实域误差、复域误差、范数桥梁和原定理缺口 | 不使用训练损失或轨迹图补足KAM假设 |
| 已有仿真 | 第一阶段只审查和设计 | 本阶段新运行结果另列，不追溯性改写第一阶段的完成状态 |

## 2.3 三类第二阶段材料确有内容差异

| 材料 | 已核实身份 | 使用方式 |
|---|---|---|
| 原GitHub v10 | main提交8761d70239a5；标签提交82519542dd05 | 原论文叙述、完整学习、连续KAM、磁提升和旧实验基准 |
| 一般Birkhoff ZIP | 20823字节、8项，SHA前12位c7df06ff2aaa | 一形式、相容性、Moser／坐标图与专门验证 |
| 当前整合ZIP | 无后缀当前版本2；41076313字节、433项，SHA前12位f809a715ad9e | 修正质量、原36、控制和一般Birkhoff新增复算 |
| 较早整合副本（2） | 39729610字节、263项，SHA前12位121fec60cea5 | 比较新增与保留内容；不当作当前包 |

当前包与较早包不同。核对发现：`framework_experiments` 和 `experiments` 中的Python计算代码保持一致；当前包增加七个 `general_birkhoff_experiments` 脚本等材料。当前包保存的 `material_B_original` 八个文件与单独的一般Birkhoff ZIP逐字节一致。新增加的G1、G2、G3和路线预算，不能被表述为已经完成一般高维血管导管的全部算法。

旧v10参数、当前整合平面参数与本轮三维参数分别冻结。原64自由度证书及跟踪数字只属于原平面有限元对象；新三维模型未采用这些数字作为初始证据。

# 3 1025 研究链的继承和必要修订

下表保留1025的原号；与后文原v10（1）—（19）以及整合稿现号严格区分。原稿缺号、重复号继续保留，不补造（11）、（13）、（23）、（29）的独立公式。

| 1025原位置 | 继承内容与本轮落地 | 必须修正或仍有缺口 |
|---|---|---|
| （1）—（3） | 三维平动、转动、弯曲、扭转；独立Cosserat程序和12自由度Kirchhoff ROM | 统一R、ν、κ及参考／空间坐标；不能由中心线单独恢复扭转 |
| （4） | Maxwell／偶极磁载；8维无源局部场和12线圈Biot–Savart接口 | 磁力与磁矩都从同一势或虚功导出；局部8分量不等于任意可实现输入 |
| （5）、重复（9） | 脉动流、相对速度、阻力投影及功率 | 已运行规定流场的单向载荷；附加质量和双向FSI尚未计算 |
| （6） | 间隙、法向罚能、法向耗散、摩擦及转动接触功 | 当前Hertz型指数是工程罚模型，没有伪称柔性血管的实测Hertz参数 |
| （7） | 非零残余加速度与抖动 | 合成空间站工况；尚无任务实测加速度与生理边界 |
| （8）—（12） | 弱式、能量一致离散、变质量、正则动量与功率 | 原（8）保留为小挠度验证层；不能充当一般三维推导；显式时间功与几何惯性必须补齐 |
| （14）—（16）、（26） | 可逆结构、机械耗散、外部端口和可选热力学扩展 | 对称耗散括号不等于Poisson；完整Metriplectic须另加总能量、熵和退化条件 |
| （17）—（21）、（24）—（25） | 尺度化复坐标、实能量输出、完整复网络及导数训练 | 修正1／√2系数和外力的i因子；H+iD本身不产生所需耗散方程 |
| （22）、（27）—（28） | 正规形、复域及解析性研究 | 极坐标不是已经构造的真作用角；实值H依赖ξ与共轭ξ，不要求对ξ单独全纯 |
| 星号Birkhoff式和A／B | 一形式相容构造、局部梯度图、解析递推 | 需加原书第15章Theorem4.5；一般Moser图目前有可量化表示误差 |
| （30）—（31） | 两端点到中心变量的变换 | 必须匹配目标二形式；沿用P=−p中点的符号，不能任意套在时变K上 |
| （32） | 从物理流推出生成梯度的时间方程 | 初始端点固定；修正分量互换、负号和双端点导数混用 |
| （33）—（34） | 截断梯度和生成关系 | 截断系数须真的具有对称Jacobian；带阻尼的原候选通常不满足 |
| （35） | 任意维数的隐式中点残差 | 加入−pᵀ∂M⁻¹p／2，采用真实∇V和中点时间 |
| （36） | 常矩阵的左乘线性系统，及变质量的一般隐式式 | 不是逐元素除法；有阻尼时不是通常辛映射，也不自动保持指定连续Birkhoff二形式 |
| U_k和KAM | 控制比较、磁分配、误差预算、独立连续与离散条件 | 任意有界反馈不继承辛性；新三维谱共振，不能调用旧两频率证书 |

因此保留的是1025的研究路线和待解决问题，而不是保留已被第一阶段明确否定的推导。当前整合稿的单特征学习和两模态示例可以作为局部验证；原v10完整特征、非可分Central4、高维控制和净空试验应恢复为独立基准。新的三维物理对象在后文独立实现。


# 4 原 v10 与当前整合稿逐项对照及旧基准复算

本文件是第二阶段的持续核查记录。当前已完成原 GitHub v10 主稿与补充稿的全文研究、主要计算链实现读取、S1 下载和输入身份锁定，以及下文明确列出的隔离复算。最新整合稿按其实际源码逐式对照。本轮复算是旧参数、旧冻结模型的基准核验，不是新三维血流—磁驱动—接触模型的证书。未复跑的历史结果均单独标明。

## 4.1 基准身份与可访问性

- 官方仓库：https://github.com/mop74720-commits/IJRR_CHNN_KAM_v10_20261007
- 读取日期：2026-10-29 UTC。
- 本地只读审查副本：`stage2/sources/v10_original/`；没有修改上游或推送。
- 当前 `main` / `HEAD`：`8761d70239a54985b40c0a6196f52e53d5b2e4d2`，提交时间 `2026-10-17T22:42:22-07:00`，消息 `Add verified S1 original and directory subset downloads`。
- 发布标签 `v10-20261008`：`82519542dd057e8fbd6d6879ef33217761e8cbbb`，提交时间 `2026-10-17T22:12:00-07:00`。
- 两次提交之间仅有 `README.md`、`reproducibility/ARTIFACT_INDEX.md` 和 `verification/package_s1_exports.py` 的下载/打包说明变更；论文、实验与既有计算结果未改变。
- 发布页：https://github.com/mop74720-commits/IJRR_CHNN_KAM_v10_20261007/releases/tag/v10-20261008 ，官方 API 记录发布时间 `2026-10-18T05:14:33Z`。文件名/文稿日期 2026-10-08 与 GitHub 发布时间不是同一概念。
- 普通沙箱网络请求因本地代理不可达失败；只读网络提权获准后 `git ls-remote`、克隆和官方 API 访问成功。网页浏览工具对指定 GitHub 页面返回 `DisabledError`，故这里的身份结论依据实际 Git 与官方 API 原始响应，并非搜索摘要。

官方元数据与逐文件 SHA-256 清单保存在 `stage2/sources/v10_metadata/`。当前仓库共有 182 个受版本控制文件、139101680 字节；未发现仓库 `AGENTS.md`。

## 4.2 当前可用结构

| 层次 | 路径/附件 | 已核实用途与边界 |
|---|---|---|
| 主稿 | `main.pdf`、`main.tex`、`sections/core_*.tex` | 15 页，当前引文适用性修订稿；平面、小斜率、无接触的梁，非用户最终三维模型 |
| 补充稿 | `supplement.pdf`、`supplement.tex`、其余 `sections/` | 45 页，包含学习、有限幅值 KAM、磁实现、净空、误差容限及积分推导 |
| S1 原科学记录 | Release `S1_complete_original_20261002.zip` | 808408246 字节，SHA-256 `f335542f8eec42067bda474306ebdcb23dcca0450f132fcba7723621eab34170`；内部稿件是历史 v9，原始实现、COMSOL、数据和证书供 v10 调用 |
| S2 当前交付包 | Release `S2_citation_revision_20261008.zip` | 125601776 字节，SHA-256 `e4fab4a3b0433ca978a54742a7ce94390ae1c3b03f7f5d0dd5566696e1dfc76a`；仓库已含对应主要文件 |
| S2 历史审阅包 | Release `S2_reviewer_revision_20261008.zip` | 125552504 字节，SHA-256 `5fbb87da73c68b729b5d452aea36bad57a24e25c72721da9307e1972fa9f93a4`；不得与当前稿混称 |
| 新增受迫扫描 | `reproducibility/reviewer_revision_20261008/stability_scan/` | 冻结协议、输入矩阵、扫描脚本、JSON/CSV/NPZ、完整 FE 交叉核查 |
| 新增容限实验 | `reproducibility/reviewer_revision_20261008/robustness/` | 非零启动/传感/执行误差下的 4 秒净空、物理功率和控制器 |
| 自检/修订记录 | `verification/`、`核对说明/` | 历史自检与当前修订记录；须独立核查其输入和计算，不以文件名中的 verified 代替证明 |

S1 原始目录还分别导出 COMSOL、积分证书、全 FE 辨识、理论证书和 S 路径五个子包。发布说明明确这些切片不补入跨目录依赖；本轮已获取完整 S1，以便核查真实依赖。解压于 `stage2/sources/s1_original/IJRR_CHNN_KAM_导师意见凝练稿_20261002/`，1114 个 ZIP 条目、解压总字节 909275804；校验无路径穿越、绝对路径和符号链接。最新版整合稿另在 `stage2/sources/integration_latest/v10_birkhoff_20261028/`，没有假定它与 GitHub 版本相同。

## 4.3 已读主稿的初步对象区分

1. 匹配实/复实现的学习比较使用两模态 Galerkin 合成轨迹、受控导数噪声和同一实系数函数类；其“复”实现不是额外物理状态，也不自动带来准确性优势。
2. 有限幅值 KAM 证明使用独立的两模态 COMSOL 状态积分辨识，目标函数包含完整余弦和可依赖动量的四次残差。
3. 全 FE COMSOL 的位置—速度增量辨识是另一组拟合，用于预测和 S 路径控制；其系数不可替代 KAM 证书中的系数。
4. 64 模态结论是同一平面梁的完整有限元控制提升，并非三维杆加血流接触的证书。
5. 本轮将分别追踪连续时间环面存在、数值积分结构/收敛、有限时域净空与跟踪。这些结论不会互相替代。

## 4.4 阅读覆盖和证据层次

原 GitHub 的 `main.tex`、五个 `core_*.tex`、`supplement.tex`、参考文献与补充所有分节已阅读全文；`stability_boundary.tex`、`operational_tolerances.tex` 由本任务子代理完整读取，其余由本代理直接读取。主稿 15 页、补充 45 页。原 S1 内历史稿不作为当前 v10 的替代版本；实现和数据按当前稿指向的原始路径读取。

已直接完整读取的核心实现包括：`feature_model.py`、`unified_model.py`、`beam_assembly.py`、`run_learning.py`、`run_integrator_check.py`；`arb_hamiltonian.py`、`hl_constants.py`、`verify_torus.py`、`torus_arb_refine.py`；`certify_integral_learning.py`、`validate_fitted_torus.py`、`audit_integral_chain.py`；`kam_magnetic_control.py`、`certify_kam_lift.py`、`run_s_path.py`、`run_safety_validation.py`；`run_robustness.py`、`run_causal_adaptation.py`。另由子代理完整读取 S2 稳定性扫描和误差容限的六个 Python 脚本。生成图片、打包、COMSOL Java/MATLAB 构建脚本和其余辅助脚本，不能以这份核心实现核验代称逐行独立复证；运行覆盖见第4.8节。

对最新整合稿，直接阅读英文主文的背景、力学、Birkhoff/生成格式、受控分析、KAM、双路线接口、应用和结论，以及完整读出、Central4 和映射 KAM 对应补充段；公式号由随包中文 `main.aux` / `supplement.aux` 核实。数值实验与一般 Birkhoff 全套实现另由团队对应代理负责。本文件不把旧复算冒充最新整合包的复算。

第一阶段依据以用户新增的 118 页详细报告 `stage2/notes/1025_stage1_detailed.md` 第 13–15 章为主。已再次对照其中 HNN 覆盖数/范数桥梁、Shang 原定理，以及 Feng–Qin 第 13 章的 exact symplectic、步长共振与 Cantor 频率条件；56 页报告仅作交叉参照。

## 4.5 原 v10（1）–（19）与最新整合稿逐式差异

此处“原”仅指 GitHub v10 主稿；不是 1025 手稿的公式编号。1025 原（36）、GitHub v10 原（36）以及整合稿现（36）必须分开。最新版说明也明确：1025 原（36）对应整合稿普通中点现（35），现（36）是矩阵消元，Central4 是现（42）。

分类：**M** = 数学/物理条件必须补齐；**P** = 参数或模型改变后必须重算；**O** = 展示顺序/移入补充，无须改动正确公式；**R** = 原实验或实现应恢复为独立基准，再在新模型上重建。没有任何一项要求永久把研究目标缩小为两模态。

| 原号及稳定标签 | 原式的作用 | 最新整合对应 | 核验与处置 | 受影响实验 |
|---|---|---|---|---|
| （1）`eq:core-beam-balance` | 小斜率 Euler–Bernoulli 内部方程、根部夹持、自由端剪力零、完整余弦磁矩 | 现（5）`mech:beam` +（6）`mech:endpoint-balance` | 原式对无端质量、无横向力的声明模型成立。新稿加入端质量 $m_t$、转动惯量 $J_t$ 和力 $F$，应使用新自然边界；这是 P，不能反向指称原简化模型内部矛盾。三维 Cosserat 必须另行建立，不由端部惯量补丁获得。 | 全部频率、学习数据、磁驱动和高模态响应重算 |
| （2）`eq:core-fe-energy` | $M\ddot q$ $+\alpha M\dot q$ $+Kq$ 与 $H_0$ 同一能量 | 现（7）FE +（8）能量 +（9）功率 | 原式正确。新 $M_f$ $=M_{beam}$ $+m_te_we_w^T$ $+J_te_\vartheta e_\vartheta^T$，新 $E_0$；加入 $F\dot w$ 功率。P；更一般 $M(q)$ 须保留 $p^T(\partial_qM^{-1})p/2$，是 M。 | FE、净空、输入功、全部数据 |
| （3）`eq:unified-scale` | $a_j$ $=\sqrt{E_0/(\omega_0\omega_j)}X_j$，$\pi_j$ $=\sqrt{E_0\omega_j/\omega_0}Y_j$ | 现（11）`mech:scaling` | 正则时间—能量缩放正确；一般 $n$ 模态仍成立。现稿明示有效质量 $\mathsf N^{-1}$。P，保留公式。 | SI 输出、训练域、所有幅值和场需求 |
| （4）`eq:unified-h` | $h_*$ $=\frac12\sum\nu_j(X_j^2$ $+Y_j^2)$ $+g(d^TX)$，$g$ $=1-\cos s-s^2/2$ | 现（13）标称 $h_0$；现（44）四个能量 | 减二次项避免偏置刚度重复计数。结构原样保留，$h_*$ 改称 $h_0$ 是 O；新的真实残差 $R_*$ 是新增模型，不与原物理目标混称。P。 | 学习目标、正规形、磁补偿 |
| （5）`eq:core-complex-chart` | $\zeta$ $=(X$ $+iY)/\sqrt2,$ $\chi$ $=(X-iY)/\sqrt2$ 及逆变换 | 现（15） | 相同。O；不是减少物理状态数。 | 全部实/复特征与导数比较 |
| （6）`eq:core-complex-energy` | 在独立 $\zeta,$ $\chi$ 中的完整余弦能量 | 现（16）、KAM 现 `kam:complex-energy` | 相同；真实切片 $\chi$ $=\overline\zeta$ 与复域独立变量须区分。不是 $\zeta$ 单变量全纯。O/P。 | 全解析 KAM 范数和神经架构 |
| （7）`eq:core-complex-canonical` | $\{\zeta_j,$ $\overline\zeta_k\}$ $=-i\delta_{jk}$，$\zeta'$ $=-ih_\chi$ | 现（17） | 符号与 $\sqrt2$ 因子正确。O。 | 自动微分、复网络解码 |
| （8）`eq:fragment-decoder` | $X'$ $=h_Y$，$Y'$ $=-h_X-\partial_v\mathcal D$ $+u d\cos\vartheta$ | 现（18）改为一般 $U$，现（20）实磁端口 | 更一般输入是有用扩展；原单均匀场只有一个方向。含动量残差时 $v$ $=h_Y$，不能偷换为 $\mathsf NY$ 或把 Rayleigh 力换成 $-\gamma Y$。M；35 参数模型要恢复。 | 完整 CHNN、耗散、跟踪、磁控制 |
| （9）`eq:fragment-power` | $h_\eta'$ $=-v^T\partial_v\mathcal D$ $+u\cos\vartheta\,$ $d^Tv$ | 现（19）改为 $v^TU$ | 完全一致的端口功率。新流体、接触、基座运动与参数时间变化需增加相应功项，不能只移换系数。M/P。 | 功率闭合、净空、Metriplectic/端口分支 |
| （10）`eq:core-complex-dynamics` | 复坐标非保守修正 $i[-\partial_v\mathcal D$ $+u d\cos\vartheta]/\sqrt2$ | 现（19）后的行内公式 | 公式仍保留，只失去独立编号。O，可恢复编号以便审查；$h$ $+i\mathcal D$ 仅双读出包装，不是该流的普通复 Hamiltonian。 | 学习架构和结构主张 |
| （11）`eq:core-central-map` | $x_+-x_-$ $=J\nabla S_\Delta(m)$ | 现（38） | 原样保留。原正则保守分支正确，不需要为引入 Birkhoff 而删除。 | 中点与 Central4 |
| （12）`eq:core-midpoint-expansion` | 时间中点与端点平均的区别 | 补充（S73）`ss:central-taylor` | 移到补充，O；推导的 $1/8$、$1/24$ 必须保留。 | 四阶证明 |
| （13）`eq:core-exact-displacement` | $\Delta f$ $+\Delta^3(f''[f,$ $f]-2(f')^2f)/24$ $+O(\Delta^5)$ | 补充（S74） | 原样正确，O。遗漏 $-2(f')^2f$ 会破坏四阶，不得以两模态便算为由删去混合项。 | 非可分完整 Hamiltonian 的四阶验证 |
| （14）`eq:core-generator-identity` | $J\nabla(f^Th''f)$ $=f''[f,$ $f]-2(f')^2f$ | 补充 S2.9 无编号等式 | 原样正确，O；依赖常数正则 $J$，一般变结构矩阵不能直接照搬。M 为适用域声明。 | 三维经正则约化后的高阶格式 |
| （15）`eq:core-central-generator` | $S_\Delta$ $=\Delta h$ $+\Delta^3 f^Th''f/24$ | 现（42）`struct:central4` | 已保留，O。带反馈的四阶版本必须把实际闭环 Hamiltonian 代入全部导数；后加任意控制增量不能承接此证明。M。 | 控制后的四阶与离散 KAM |
| （16）`eq:central4` | 用 $g_\Delta$ $=J\nabla S_\Delta$ 的完整隐式更新 | 现（38）+（42），补充（S76）专门固定动能势能式 | 一般式等价保留，但新专门显式式不覆盖动量四次项。需恢复一般 $g_\Delta,$ $Dg_\Delta$ 实现作为 R。 | 原 GC17 非可分训练模型、未来完整 CHNN |
| （17）`eq:core-central-newton` | Newton 矩阵 $I-\frac12Dg_\Delta$，用至四阶能量导数 | 现（36）后只明写普通中点 $I-\Delta Df/2$；Central4 在补充 S2.10 给专门导数 | 中点 Newton 不是一般 Central4 Newton。应明确恢复原式（17）及其残差定义，属 R/M；已有公式不必变。 | 高阶求解容差、Jacobian、非可分模型 |
| （18）`eq:core-step-tangent` | $(I-C)^{-1}(I$ $+C)$，$C$ $=JS''/2$ | 现（40）`struct:cayley`；现（41）新增 exact primitive | 保留正确 Cayley 证明；新增 exact symplectic 直接支撑离散 KAM。M 是区分理想隐式映射与有限容差输出，不是推翻原辛性。 | 结构误差、映射 KAM |
| （19）`eq:core-linear-phase` | $2\arctan(a/2)$ $=\nu\Delta-(\nu\Delta)^5/120$ $+O(\Delta^7)$ | 补充（S75） | 原样保留，O；线性相位检查仅是算例，不把 $H$ $=\nu I$ 称为有扭转 KAM。 | 数值阶、相位误差 |

### 4.5.1 可直接保留的中央生成推导

设 $x_0=x(t+\Delta/2)$、$m=(x_++x_-)/2$、$f=J\nabla h$。Taylor 给

$$m=x_0+\frac{\Delta^2}{8}f'f(x_0)+O(\Delta^4),\qquad x_+-x_-=\Delta f(x_0)+\frac{\Delta^3}{24}(f''[f,f]+(f')^2f)(x_0)+O(\Delta^5).$$

代入 $x_0=m-\Delta^2f'f(m)/8+O(\Delta^4)$，得到原（13）的系数 $1/24-1/8=-2/24$。再令 $A=h''$，$f'=JA$，则

$$\nabla(f^TAf)=h^{(3)}[f,f]+2(f')^TAf=h^{(3)}[f,f]-2AJA f.$$

左乘 $J$ 即原（14），因此原（15）–（18）都可用于一般平滑的正则、自治 Hamiltonian，而非仅二模态梁。四阶有限时收敛还要工作域内足够高阶导数、局部分支唯一、全局误差稳定性；若每步增量残差为 $\eta_\Delta$，总误差具有 $C_T(\Delta^4+\eta_\Delta/\Delta)$ 的形式。对真实耗散/一般 Birkhoff，则应先用相容坐标或专用几何积分，不把该正则公式原封不动用于任意 $J(x,t)$。

## 4.6 原“完整 CHNN”究竟实现了什么

### 4.6.1 实际计算图、特征数和求解器

原 `feature_model.py` 枚举四个实坐标的全部二次（10 个）和四次（35 个）单项式。复实现确实形成 $z_1,z_2,\overline z_1,\overline z_2$，取共轭成对单项式的实部/虚部，并用复指数计算磁项；并非简单把实数组改名。但隐层特征和其线性变换 `TRANSFORM` 是固定的。已知二次能量分支的实际函数类为

$$h_\eta=h_2+a\,g(d^TX)+m_4(X,Y)^TU_Fc,\quad c\in\mathbb R^{34},\quad U_F\in\mathbb R^{35\times34},$$

其中 $v_4$ 是 $-(d^TX)^4/24$ 的实系数向量，$U_F$ 张成 $v_4^\perp$，训练特征为 $F=(g/\|v_4\|_2,U_F^Tm_4)$。因此参数是 $\eta=(a\|v_4\|_2,c)\in\mathbb R^{35}$。无先验分支再学习一般二次项，45 个有效实参数。实/复分支使用同一实函数类和同一实参数正则，不存在预设的复网络容量优势。

`run_learning.py` 的 `fit_labels` 把梯度特征叠成矩阵，用 `np.linalg.lstsq` 解带 $10^{-14}$ 二次正则的增广最小二乘。它没有 Torch，没有可训练复隐层，没有反向传播训练整个深网。补充稿讨论的共享复隐层和双读出，以及复梯度下降命题，是可扩展理论，不是这些数值实验的真实训练过程。原文自身在 `complex_theorem_note.tex` 最后也明确：实验读出由线性最小二乘拟合。

这并不意味着“没有学习”：35/45 个读出系数确实由数据估计，且含全部混合和动量四次方向。正确称呼是**具有固定解析特征的复 Hamiltonian 读出辨识**。新加入可训练复网络应作为新增模型，与该解析特征基准用相同数据划分、参数/计算预算和物理指标比较；不能回写为原 v10 已经训练过深层 CHNN。

### 4.6.2 动量项与耗散/物理实现

若 $h_\eta$ 含 $X,Y$ 混合项，物理速度是 $v=h_{\eta,Y}$，Rayleigh 模型

$$\mathcal D_\gamma(v)=\frac\gamma2v^T\mathsf N^{-1}v$$

产生 $-\gamma\mathsf N^{-1}h_{\eta,Y}$，一般不等于 $-\gamma Y$。原训练先冻结保守读出，再以非负一元最小二乘估计 $\gamma$。最新整合单势能分支满足 $h_Y=\mathsf NY$，所以线性动量阻尼和联合线性辨识成立；将其 36 列设计推广到完整动量读出时，若保留速度型 Rayleigh，阻尼与能量系数产生乘积，联合问题一般不再线性。最新补充 S2.15 已正确提醒这一点。

对于一般已学保守参考，必须在 $h_{YY}$ 可逆的域内解

$$h_Y(X,\widetilde Y)=\frac{\dot a}{\omega_0S},\qquad \ddot a^{ref}=D_s\omega_0^2(h_{YX}h_Y-h_{YY}h_X).$$

这就是原 64 模态环面提升实际使用的 Legendre 反解和完整 Hessian。单势能残差补偿 $U=\widehat\gamma Y+\nabla\widehat R(X)$ 不能直接承担这项任务。

### 4.6.3 三份冻结学习对象必须分开

| 对象 | 数据与拟合 | 实际用途/结果边界 |
|---|---|---|
| Python GC17/43/91，GR/BR/BC 对照 | 每种子 12 条 4 s 两模态轨迹、129 时点；状态无噪声，导数均匀噪声 $\pm10^{-6}$；8 条独立 16 s 测试。另有 $10^{-8},$ $10^{-9}$ 噪声拟合 | 实/复及先验配对比较、200 s 续算、GC17 Central4。目标恰好在特征类内；不能代表实体精度。 |
| 全 FE COMSOL q/v 积分拟合 | 4 条训练+2 条测试；每 0.004 s 采样、9 点 Newton–Cotes、500 个 0.032 s 窗口；35 参数，$a$ $=1.0223248822$ | 文件 `learning/raw/comsol_identification_refined/qv_integral_fit.npz`，SHA `e3be5105300d01ffb9250ea9901c54b501f1c91be22dde1fac8e294225862bb7`；S 路径与预测，另有其自身后验环面。较小预测误差可能吸收求解器色散；不能以求解器容差充当严格观察缺陷。 |
| 两模态 COMSOL 短轨迹积分拟合 | 64 条短轨迹、每条 17 状态；端点匹配的八次精确二进有理曲线；有单独验证的积分缺陷、Gram、能量解析误差 | `mainline_completion/integral_certificate/comsol_integral_certificate_fit.npz`，SHA `a9bc1c23a811d1200b42ea4ff065e1d455e49d3dc33177e2e5d653dd581a8b85`；主误差→KAM、主约 1.9 mm 环面、主 64 模态提升。是本轮复算证书对象。 |

旧四种匹配模型的实/复结果在已分辨精度内相同，不能写成复表示普遍更优。原 S 路径的静态逆前馈还比完整 CHNN 跟踪误差更小，因此也不能用该算例证明 CHNN 优越性。

## 4.7 原后半段与最新整合稿的具体恢复/修正表

最新版改变了物理参数：$E:5\to2.1$ MPa、$\rho:1100\to1028\ \mathrm{kg/m^3}$、$\mu:2.0\times10^{-5}\to1.77184214\times10^{-5}\ \mathrm{A\,m^2}$，加入磁芯质量与惯量；$\omega_0:11.41728728\to7.84000916$ rad/s，$d:(0.22567077,0.32179881)\to(0.30722439,0.45042632)$，$E_0:6.0\times10^{-7}\to5.31552642\times10^{-7}$ J。新材料来源和端部惯量是独立建模选择；**参数更换本身足以要求重新训练和重新认证，但不能证明旧数学/实验应被删除**。

| 主题 | 原 v10 实际内容 | 最新整合实际状态 | 必须修正/仅顺序与恢复建议 | 需要重建的实验 |
|---|---|---|---|---|
| 完整 CHNN | 35/45 系数、混合/动量项、实/复及先验 2×2 对照、三种子 | 主计算只有 $\beta_*$ $=0.2$ 的单磁势特征+标量阻尼；35 参数仅补充（S86）–（S88） | 缩窄不是数学必要。恢复原固定特征基准；新增真正可训练复网络应明确新贡献。 | 新域激励、训练/验证、Gram、导数误差、损耗与复杂度 |
| 非可分 Central4 | GC17 完整余弦+全部动量四次项，四阶/辛缺陷/独立差分 Jacobian | 一般公式保留，新数值主要标称固定动能势能 | 顺序调整可接受，不能用可分专门导数替代完整实现。 | 新完整读出的四阶导数、牛顿分支和残差 |
| 非零损失→解析误差 | 三类数据清楚分开；主证书有独立物理轨迹缺陷与 Gram 下界 | 公式同类，单特征无噪声真值诊断；独立观察缺陷与 KAM 阈值未认证 | 学习界应保留确定性路线，不能调用有问题的 HNN Theorem 8/11 补缺。 | 实/复复域范数、缺陷/类误差、采样和观察器 |
| 四阶正规形与扭转 | 旧 $A_{jj}$ $=-d_j^4/8,$ $A_{ij}$ $=-d_i^2d_j^2/4$，完整余弦+Lie 余项 | 新扭转重新计算；双路线 $\kappa$ $=1,$ $1.2$ 分别预算 | 正确新增：区分 $h_c$ 与 $\widehat h$，余项含 $\kappa^2$ 不能只线性缩放。维数可推广，不能宣称任意3D已近可积。 | 新频率小除数、完整正规形、域包含与误差预算 |
| 有限幅值环面 | 7 个旧冻结 Hamiltonian 的后验计算；主短轨迹拟合约 1.898 mm | 明确声明未完成新参数认证 | 旧证据应恢复为独立基准，不搬用频率/Fourier 系数/阈值。新参数需要新候选和域。 | Fourier 候选、解析尾项、扭转、全部定理常数 |
| 局部正测度与宽域诊断 | 另有 $w$ $=10^{-220}$ 管状域严格比例，以及 1024/1024 有限时分类 | 没有恢复这些数值；只保留条件性 KAM | 不能把 99.6404% 置信下限当 KAM 体积；管厚远小于可分辨嵌入误差。旧管坐标 exact 修辞需改，见第4.9节。 | 新域 measure、独立分类与积分细化；不是优先替代真实机器人指标 |
| 64 模态磁实现 | 两实磁端口精确实现已学低模态加速度；62 个高模态稳定响应图，严格全相位包络；12 s 动力学和 COMSOL在线反馈细化 | 保留条件性提升定理，但 $4/8/64$ 闭环全列计划 | 理论保留且应恢复旧验证。低二维环面不是128维 Hamiltonian正测度结论；不代表两个端口能任意驱动64模式。 | 新端口矩阵、完整角度、Legendre域、高模态强迫/启动、执行器分配 |
| 全杆净空 | 连续能量不等式+实际磁功 governor；全64自由度数值、主动限功、零阻尼、COMSOL闭环 | 理论扩到 $(F,$ $B_y)$ 两端口；新控制未启用，初始能量12.6567 nJ高于9.5187 nJ cap | 功率/残差能量条件必须补齐。初始能量超cap时不能援引该安全不变集；不应删除 governor 数值验证。 | 新安全初态、物理全输入功、流体/壁/基座能量、限幅和测量误差 |
| S形跟踪 | 64自由度、全FE训练权重、实际尖端反馈、单横向场、独立轴向基座馈入；16s场回放COMSOL | 新稿 Route B 为已学保守参考的两模态跟踪；未恢复原S任务 | 两种任务不同。S形端点轨迹不是S形静态杆形；不是插入长度改变，更不是血管中真实推进。恢复任务须新增血流/接触/馈入功。 | 固定控制器4/8/64/3D、相同输入约束与对照、全杆接触 |
| 未建模物理/状态噪声 | 64自由度产数、4模态辨识；未知E/磁矩、静流二次拖曳、梯度保守势、噪声、独立COMSOL | 主单系数实验没有恢复 | 有价值的过渡验证，应保留与新3D升级；静止流体拖曳不是脉动血流。 | 新血流、观测噪声/系统激励、参数可辨识与截断残差 |
| 因果慢变适应 | 29s完整FE轨迹，过去4s窗口估计，六次未来1s预测；常数和仿射趋势 | 未恢复 | 是预测实验而非一般在线学习/闭环证明；参数变时功率必须含 $\partial_tH$，不能承接自治 KAM。 | 新高维适应与冻结验证、耗散结构和功率 |
| S2受迫稳定边界 | 1715个两模态启动/延续记录，30个4/8模态精查，有限全FE检查 | 新稿一般格式/控制对照不同 | 没发现混沌不能称全局不存在混沌或KAM破裂阈值。可保留旧协议，不把扫描结果移植。 | 新频段、强迫/阻尼/接触、变分方程与步长细化 |
| S2误差容限 | 4s非零启动、测量/执行误差的净空实验，使用物理功率误差预算 | 新稿只给条件/计划 | 与精确环面证明分离；governor长期激活会明显改变请求轨迹。 | 新不确定性预算与执行器/传感校准 |

## 4.8 本轮实际复算、冻结对象与计算环境

### 4.8.1 隔离环境

`stage2/venvs/v10_baseline/bin/python` 使用 NumPy 1.26.4、SciPy 1.13.1、Numba 0.60.0、Matplotlib 3.9.2、threadpoolctl 3.6.0、python-flint 0.9.0、SymPy 1.13.3。旧 S1 核心不需 Torch。未修改全局 Python 或原始源码；只复制已审查脚本及所需冻结输入到 `stage2/runs/v10_s1/reproducibility/`，逐项源/副本 SHA 记在 `input_copy_manifest.json`。未加载原包 `vendor` 的平台二进制；使用 Linux python-flint 正式包。

所有复算设 `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMBA_NUM_THREADS=1`；Numba/Matplotlib 缓存位于隔离运行目录。没有执行未知下载脚本，证书复算没有重新训练或改变候选环面；独立的读出重训另列。

### 4.8.2 已完成复算

| 复算 | 实际入口/参数 | 本轮结果 | 时间与边界 |
|---|---|---|---|
| GC17 完整 Hamiltonian 中点/Central4 | 隔离 `unified_model/integrator/run_integrator_check.py`；原初态 $(0.1,$ $0.06,$ $0,$ $0.02)$，$\tau$ $=10$，$\Delta$ $=0.08,$ $0.04,$ $0.02,$ $0.01$ | 六项检查通过；Central4末端误差依次 $1.8345544$ $\times10^{-3},$ $1.1783725$ $\times10^{-4},$ $7.4149058$ $\times10^{-6},$ $4.6421587$ $\times10^{-7}$；阶 $3.96056,$ $3.99022,$ $3.99756$ | 2.21158 s；旧 Python GC17，不能称主COMSOL积分拟合或新基准 |
| 主 COMSOL积分学习证书 | 隔离 `certify_integral_learning.py --data ../comsol/comsol_two_mode_observations.mat`；未用 `--refit`；256-bit Arb | 非零MSE约 $3.6030685$ $\times10^{-23}$；Gram最小特征值下界 $2.9302565$ $\times10^{-7}$；系数误差 $2.3804786$ $\times10^{-8}$；twist误差 $1.0376266$ $\times10^{-7}$；$r$ $=0.3$ 解析能量误差 $1.3309393$ $\times10^{-9}$；全部检查通过 | 0.67132 s；权重 SHA `a9bc...b85`；数据 SHA `cd4bbb57d5549e69fc37bf90586e882818a24cda642ce74e17f0ba58210e517a` |
| 同一主拟合的有限幅值环面 | 隔离 `validate_fitted_torus.py verify`；512-bit Arb；256×256残差格、128×128扭转格；冻结 Fourier 候选 | 全检查通过；$\|E\|_\rho<2.7309550$ $\times10^{-77}$；扭转平均逆范数 $<80525.201$；Haro–Luque小量 $<0.031724$；嵌入修正 $<2.089396$ $\times10^{-41}$ | 25.51325 s；候选压缩 SHA `83e6e4cf57fac5e5735f32b8c33db2a1ec2e384958a5aa137ada6f567a81d3d9`；只证明旧冻结两模态保守 Hamiltonian |
| S2档案独立重算 | 子代理从原 NPZ/JSON重算谱半径和功率/形状指标，核对58个扫描文件及5个容限输入SHA | 1715个存储单周期矩阵的谱半径与原记录差 $\le1.33227$ $\times10^{-15}$，全部 $<1$；容限的能量、空间极值、限功激活率与细化一致 | 0.367 s；是原输出独立审计，不是重积分1715个ODE |

命令、返回码、耗时、标准输出和错误输出分别记录在 `stage2/runs/v10_s1/{integrator_run,integral_run,torus_run}.json` 及同名前缀日志。S2独立审计为 `stage2/runs/v10_s2/independent_archive_audit.json`，实现阅读与边界报告为 `stage2/notes/v10_s2_repro.md`。

### 4.8.3 尚未重新执行的历史项目

本轮没有重新执行 COMSOL原生求解、旧Python训练参考轨迹的重新产数、200 s长续算、七个不同Hamiltonian的全部环面、1024条717.5s分类轨迹、1715个受迫ODE扫描。S路径全部原控制组，以及35/45特征三种子重训和16 s留出预测，已于追加复算执行，见下文。其余源码/原输出可用不等于本轮已复跑。COMSOL专有运行时还需单独检查；本轮没有假定其可用。

### 4.8.4 追加复算：冻结64自由度提升、S路径与净空边界

**64自由度仍指平面梁的有限元自由度。** 本轮追加执行 `stage2/runs/v10_s1/recheck_frozen_lift.py`，调用未经修改的原 `certify_kam_lift.py`，使用本轮重新通过的主 COMSOL 积分拟合环面证书。原脚本会重新求解特征值问题；为让证书对象确实是原冻结模态模型，wrapper 只把 `MagneticBeam` 构造返回值替换为原存档的精确数组，未改变提升方程、界估计或输入限制。八项模态数组逐项、逐位相同，见 `frozen_modal_identity.json`；原 NPZ 的 SHA-256 为 `c0477f4400e514ff122e7a50475a6dbba9c5bf7751870bd8e593c32e1380520b`。NPZ 容器重新打包后的文件哈希可不同，故不能仅比较压缩容器哈希判断数值身份。

单线程运行 1.03387 s，全部原检查通过：Legendre Hessian 下界大于 $0.999999998366247$；全杆图像位移界约 $1.922696$ mm，含启动瞬态界约 $1.970263$ mm；所需横向磁场界约 $0.921665$ mT，梯度界约 $0.025726$ T/m。该结论是旧冻结平面模态方程的低维环面加稳定受迫高模态图像，不是新三维有限元或真实血管动力学的环面证书，也不是128维相空间内正体积的环面族。命令/耗时/检查见 `frozen_lift_run.json`、`frozen_lift_stdout.log` 与 `frozen_comsol7_rechecked.json`。

**S路径全部五组已实际重积分。** 原 `run_s_path.py --case all` 不修改源代码，使用原全 FE COMSOL 位置—速度拟合，而非主短轨迹 KAM 拟合。总耗时 12.63690 s；原定2–14 s弯曲行程区间的误差均由本轮原始状态重新统计：

| 控制组 | 横向尖端轨迹 RMS 误差 | 相对于原档案的最大尖端位置差 |
|---|---:|---:|
| 完整 CHNN 读出与物理反馈 | $6.418803$ μm | $1.48584$ $\times10^{-11}$ m |
| 二次 Hamiltonian | $6.207384$ μm | $1.48791$ $\times10^{-11}$ m |
| 静态前馈 | $4.124012$ μm | $6.79924$ $\times10^{-12}$ m |
| 模态反馈 | $25.308195$ μm | $1.62414$ $\times10^{-11}$ m |
| CHNN 更紧积分容差 | $6.418803$ μm | $1.48584$ $\times10^{-11}$ m |

静态前馈在这组既定工况下误差最小，二次 Hamiltonian 也略优于 CHNN。因此该旧实验不支持“学习控制在S路径上普遍优于解析/静态对照”。可以据此设计新3D工况的非线性、扰动与外推检验，不能删除不利对照。五组 governor 均未触发，故不能把这组跟踪结果当作主动限功工作时的跟踪性能。CHNN组全杆最大横向位置约 $1.488917$ mm、场峰值约 $12.917656$ mT、数值功率平衡残差约 $2.434\times10^{-18}$ J。数据和独立统计为 `s_path_run.json`、`s_path_independent_comparison.json` 及隔离输出 NPZ；COMSOL 场回放没有重新执行。

**净空重积分仅完成五个普通算例。** 原 `run_safety_validation.py` 的前五个算例完成：6 mT渐入、3 mT非零初值、0.15/6/10 mT正弦，最大全杆横向位置依次为 $0.924046$、$2.062224$、$0.077306$、$3.090305$、$5.144776$ mm。原设净空为4 mm，因此无 governor 的10 mT算例确实越界；这不是安全成功案例。新旧尖端轨迹差最大约 $1.449\times10^{-10}$ m。运行随后进入非光滑主动限功工况，原紧容差档案已显示该工况需720万次右端调用、约537 s；本轮为避免扩成长期重积分，主动中断该阶段，返回码130，未将主动限功积分标为通过，见 `safety_run.json`。

对原三条主动限功轨迹另从128维状态、冻结模态图和实际磁场独立重算能量与功率。存档能量重构差小于 $6.7\times10^{-24}$ J；样本点上 $P-5(E_{\mathrm{cap}}-W)$ 的正残差不超过 $1.9\times10^{-21}$ W。普通、零拖曳及紧容差轨迹的最大位移分别约 $3.143623$、$3.558526$、$3.143623$ mm，均低于解析能量界对应的 $3.898718$ mm；能量上限为 $22.663646$ nJ。普通/紧容差轨迹限功激活样本比例 $55.3723\%$。这是对已有输出的独立样本审计，不是新重积分，更不是由有限采样新建连续时间区间证书。零拖曳样本有约 $6.73\times10^{-18}$ J 的数值能量观察器差，应作为有限精度残差记载。详情在 `safety_independent_comparison.json`。

### 4.8.5 追加复算：35/45完整特征的三种子重训与2×2对照

在独立目录 `stage2/runs/v10_training/` 已实际调用原 `run_learning.py` 的 `fit_labels`、`simulate_learned`、`physical_metrics`，三者源代码均未修改。种子17、43、91各做无先验/有先验与实/复交叉，共12次完整线性读出重训；随后每组运行原8条16 s保守留出轨迹，共96次新的轨迹积分。总墙钟时间65.51540 s，脚本内部时间63.88169 s，12次最小二乘本身共0.83528 s；均为单线程。未重做原合成参考轨迹产数、耗散头辨识和200 s续算。

为消除重新对角化及不同QR/SVD基选择造成的对象改变，wrapper 从原 `model_matrices.npz` 与 `feature_basis.npz` 装载原模态图、物理尺度、完整余弦归一化及四次补空间。训练数据是原Python两模态模型每种子12条4 s轨迹，每条129状态；状态无噪声，导数标签加分量有界 $10^{-6}$ 噪声。逐个核对三种子的存储标签恰好等于 clean field 加原 unit noise 乘 $10^{-6}$。测试为原8条16 s参考，每条1601状态。没有把该数据称为COMSOL观测，也没有将此读出回归称为隐藏层端到端训练。

| 对照 | 实参数个数 | 尖端 RMS 三种子均值±样本标准差 | 留出场相对 $L^2$ 误差均值 |
|---|---:|---:|---:|
| BR：无线性先验、实表示 | 45 | $22.81494\pm7.51056$ nm | $1.722553$ $\times10^{-7}$ |
| BC：无线性先验、复表示 | 45 | $22.81494\pm7.51056$ nm | $1.722553$ $\times10^{-7}$ |
| GR：固定线性先验、实表示 | 35 | $11.99845\pm7.08620$ nm | $1.585065$ $\times10^{-7}$ |
| GC：固定线性先验、复表示 | 35 | $11.99845\pm7.08620$ nm | $1.585065$ $\times10^{-7}$ |

新旧拟合的多项式系数最大差 $1.469\times10^{-13}$、余弦系数最大差 $7.962\times10^{-12}$，全部预测状态最大差 $7.251\times10^{-13}$。结果支持对原实现的复算一致性；匹配函数类、映射正则化及采样下，实/复结果数值相同，不支持“仅换复表示就提高精度”。固定线性先验在本设置下改善均值，但仍需新物理、新噪声与域外任务检验。这里的纳米级数值误差来自目标在所选解析特征类内、低标签噪声及一致模型；不表示真实机器人具有纳米级测量或控制精度。

六个关键输入 SHA-256 如下，完整十文件源/副本清单在 `input_manifest.json`：

| 输入 | SHA-256 |
|---|---|
| `model_matrices.npz` | `ae1b221b5f67ff455c478c17552bc26ce4d8c155169b9e2682f53b992cca4288` |
| `feature_basis.npz` | `493ee9ff5a3cf75dbe26d2112d4d6ab0770212df0720eab7d2e9c39aa10d18aa` |
| `conservative_test.npz` | `2d95bf58e7135060fa6d34f4c413d15a5f07908b966771de24e886e417713eaf` |
| `train_conservative_17.npz` | `8a6a36ea63816b405c86d0da33dc5a5a9d6cea9be2c9540d3e4d2f337b17a922` |
| `train_conservative_43.npz` | `ea9bbe575a40a0c0225e8914093e35a1e68ab6ee73f3c99e27c64c1a84776d1f` |
| `train_conservative_91.npz` | `7417d4eefa396dda0f5bb2e4c2c470134cc30ea212e7725cbcfc073ab4e40287` |

独立执行入口是 `stage2/runs/v10_training/refit_training.py`，调用 `stage2/venvs/v10_baseline/bin/python`；命令和环境见 `training_run.json`，所有指标及逐种子记录在 `training_results.json`，12份新系数与96条预测在 `refits/`。这些重训输出没有覆盖任何旧冻结环面或积分证书输入。

## 4.9 数学核验结论与不可转移事项

### 4.9.1 连续KAM实际证明对象

原主证书将导出二进浮点系数解释为精确二进有理数，保守能量含完整余弦和所有导出四次项；不是仅检验四次截断。Haro–Luque 2019 Theorem 3.1 在 $n=d=2$、canonical Case III（Remark 3.2–3.3）上使用，需复域内解析全局场与导数上界、复条带参数化、$DK$满秩/Gram逆界、平均扭转逆界、全整数Diophantine频率，以及带显式常数的残差小量。代码补了插值与别名尾项；没有把离散网格残差当解析范数。

原用频率比是具有有界连分数系数（最大23）的二次无理数，因此从 $|q\zeta-p|\ge1/(25|q|)$ 得周期一角变量下 $|k\cdot\varpi|\ge(9/1750)|k|_1^{-1}$，再以较弱指数 $\tau=3$ 进入定理。原证明给出的全整数条件比有限扫描有实质区别。

本轮已从作者一手页面取得并核查 Haro–Luque arXiv:1711.05515v1：PDF pp.14–18的范数、H1–H5与Theorem3.1、p26 Remark4.7、pp56–59 Appendix B Tables1–3。还核对期刊接收稿对应定理；未宣称本轮重新独立复证全59页每个估计。书目：Àlex Haro, Alejandro Luque, *A-posteriori KAM theory with optimal estimates for partially integrable systems*, JDE 266(2–3) (2019), 1605–1674, DOI 10.1016/j.jde.2018.08.003。官方作者机构条目：https://diposit.ub.edu/items/7e54e405-d0b4-4e75-b0ed-86c8ae618e11 。本地来源及 SHA 在 `stage2/sources/primary_kam/sources.json`。

两个容易漏的常数细节已独立确认：（i）源文 $D(X_h^T)$ 是对行向量映射求导，范数是所有 Jacobian 元绝对值的总和；不是 $(DX_h)^T$ 的列和。原代码取32符合其保守上界。（ii）Table1 的 $C_{sym}$ 行存在符号打印不一致；原代码按 p26 Remark4.7 的块式用 $\max(1,\sigma_B^2)C_{\Omega_L}=192$，不是较小的 $C_{\widetilde\Omega_L}$ 值。不能因机械照表而把阈值改宽。

### 4.9.2 正测度、可分辨厚度和“exact symplectic”用词

Bounemoura 2016 *Non-degenerate Liouville tori are KAM stable*, Adv. Math.292,42–51, DOI10.1016/j.aim.2016.01.012，作者稿 arXiv:1412.0509 Theorem6（PDF p7）要求既有非共振环面、非奇异平均二次扭转和Gevery/解析正则性，以及其小邻域条件。其解析情形支撑原已认证环面附近的正测度族；它不证明某个任意工作域里99%以上轨迹都在KAM环面。

原另给 $w=10^{-220}$ 的明确定义管状域、严格比例 $>96.69383\%$。这是在精确环面周围的极薄作用管，嵌入已知误差上界约 $10^{-41}$ 远大于该厚度，无法据已计算候选给一个实验初态判定管内归属。原文也承认这一点。1024/1024及Clopper–Pearson区间 $[0.996404,1]$ 只针对预先定义的有限时分类器。

**需改正的确切措辞：**`measure_proof.tex` 的管状坐标段称 $\Psi$ 为“exact symplectic chart”，但只证明

$$\Psi^*\lambda-I\cdot dt=j(t)\cdot DF(t)\,dt$$

为闭形式；对正作用环面，右边通常有非零闭环积分。因此该推导证明的是 symplectic，并不证明相对于这两个原始一形式的 exact symplectic。取圆环面 $j=I_0\ne0,F=t$ 即可见其周期为 $2\pi I_{0,j}$。修正为“symplectic chart”，或明确在参考原始一形式加入作用偏移。Liouville体积转移只需辛性，故这个措辞错误本身不推翻其测度转移步骤。最新整合中央数值映射的 exact primitive 则有独立推导，不受此处影响。

### 4.9.3 统计HNN论文不能补上未核验条件

按118页报告第13章，Chen–Matsubara–Yaguchi 2022 的 Theorem8类覆盖界和 $C^0$ 小度直接进入强KAM范数存在实质问题。原v10主线采用确定性有限特征/Gram/缺陷路线，可避开该缺口。保留广义统计讨论时，仍须：有效的参数类复杂度界、独立采样/相关轨迹的适当理论、全域密度或覆盖、$p>2n$、域上的Poincaré条件，以及高阶或固定复域误差。

不能由“复CHNN通用逼近”“小训练损失”“实域 $C^0$ 小”“轨迹看起来准周期”中的任何一项独立推出KAM。对可训练复神经网，尤其应重新界定激活复域（如tanh极点）和训练后导数/复域范数，而非沿用有限多项式特征的系数证书。

### 4.9.4 连续证书不能替代离散KAM

原冻结证书是连续保守流。新整合对离散KAM增加 exact symplectic、解析隐式分支、正规形共轭后的全局周期生成函数、映射小除数

$$|e^{i\Delta k\cdot\omega}-1|\ge\Delta\gamma_D|k|^{-\tau_D},$$

以及规范化生成扰动 $\|G_\Delta/\Delta\|\le C_3\epsilon+C_4\Delta^p$，这与118页报告第14、15章核验一致。必须核实所用Shang定理的域、扭转上下界、$\tau_D>n+1$与小量；固定步长下的连续Diophantine并不排除 $2\pi$ 步长共振。旧512-bit连续证书不证明原Central4的某一离散环面。

比例耗散的时间变二形式保持也不等于自治 exact symplectic 返回映射。通用光滑ODE可局部Birkhoff化是一种表示定理，不是消除生理耗散/摩擦或证明近可积性的机制。真实血流、接触切换及非周期任务反馈必须按其实际动力学另论。

## 4.10 原结果到入口、输入与模型身份的实施地图

以下路径均相对原 S1 `reproducibility/`，S2两行除外。入口已定位；“历史”不表示本轮复跑。

| 原结果 | 主要脚本入口 | 冻结输入/依赖 | 当前核验层次 |
|---|---|---|---|
| 35/45参数实/复与先验比较 | `unified_model/learning/run_learning.py` | `feature_model.py`,`unified_model.py`,`beam_assembly.py`、种子17/43/91 | 原函数12次重训及96条16 s预测本轮完成；未重做参考数据产数与200 s续算 |
| 导数噪声损失/Gram证书 | `unified_model/learning/certify_learning_noise.py` | `raw/fit_*`、训练状态/标签、矩阵 | 历史；主积分证书另已复算 |
| COMSOL位置速度积分拟合 | `unified_model/learning/check_comsol_integral_data.py`、`run_comsol_identification.py` | refined四训练两测试MAT | 数据链和论文方法已读；历史 |
| 全FE拟合耗散读出 | `unified_model/learning/fit_qv_model_dissipation.py` | frozen qv fit+Python阻尼数据 | 身份区分；历史 |
| 原完整非可分Central4 | `unified_model/integrator/run_integrator_check.py` | `raw/fit_17_GC.npz` | 本轮实际复算通过 |
| 主短轨迹积分证书 | `mainline_completion/integral_certificate/certify_integral_learning.py` | `comsol_two_mode_observations.mat`、冻结fit和精确曲线 | 本轮实际复算通过 |
| 有限幅值环面 | `unified_model/theory/torus_candidate.py`→`torus_arb_refine.py`→`verify_torus.py`；主拟合wrapper `validate_fitted_torus.py` | 各自Hamiltonian和Fourier候选，`hl_constants.py` | 本轮主冻结模型verify通过；未重建候选或复跑另外6个 |
| 64模态理想磁提升/启动界 | `mainline_completion/s_path/kam_control_audit/certify_kam_lift.py` | 主fit、候选、certificate、冻结modal_model | 实现全文读，原冻结模态全部数组一致的本轮证书通过 |
| 64模态低流实现 | `mainline_completion/resonance/kam_magnetic_control.py` | 指定fit/certificate/geometry；默认是全FE拟合第6模型，主结果须通过参数选择第7模型 | 实现全文读；不能误跑默认后称复现主证书 |
| COMSOL在线KAM反馈 | `mainline_completion/resonance/prepare_comsol_kam_control.py`,`compare_comsol_kam_control.py` | 原生模型、反馈采样步细化 | 原结果与协议；未运行COMSOL |
| 全杆能量governor | `unified_model/safety/run_safety_validation.py` |64模态物理能量、实际磁矩功率 | 五普通算例本轮重积分；三主动限功存档独立审计，主动限功未完成重积分 |
| S形端点任务 | `mainline_completion/s_path/run_s_path.py --case all` | 全FE qv冻结fit与`qv_dissipation_fit.npz`、实际tip反馈 | 核心实现全文读；本轮全部五组复算通过；COMSOL回放未重跑 |
| 新物理/噪声与因果适应 | `mainline_completion/robustness/run_robustness.py`,`run_causal_adaptation.py` |64自由度产数、4模态预测、5/14读出 | 论文和两核心实现全文读；历史 |
| 超薄管严格测度 | `mainline_completion/measure_completion/analytic/certify_ck_torus_tube.py`、`verify_tube_geometry.py` | 精确中心环面与几何界 | 证明全段已读；历史，非工作域可分辨率 |
| 有限时宽域分类 | `mainline_completion/measure_completion/numerical/setup_protocol.py`,`run_ensemble.py`,`analyse_ensemble.py` |1024独立初态、冻结分类器、8192维数时间、步长1/64 | 论文协议全读；未重跑大扫描 |
| S2受迫扫描 | `v10_original/reproducibility/reviewer_revision_20261008/stability_scan/` |冻结protocol+rawNPZ | 六核心脚本团队全读，原输出独立审计 |
| S2容限实验 | `v10_original/reproducibility/reviewer_revision_20261008/robustness/` |非零启动/实际功误差界+rawNPZ | 同上 |

恢复路径应同时保留三层：旧冻结基准便于检测算法退化；新的理论ROM用于结构/KAM问题；三维Cosserat—血流—壁接触高保真模型承担最终物理目标。旧基准的“复算通过”只提供回归锚点，不能成为把最终模型永久降为两模态的理由。

## 4.11 新3D理论ROM的1:1共振：本轮新增对象的明确边界

以下是 root 本轮建立的新计算结果，不是原 v10 证书的延用。已读取 `stage2/program/learning/rod_rom.py` 的模型接口及 `stage2/results/learning/rom_metadata.json`。新模型是不可伸长、不可剪切的三维 Kirchhoff 应变 Ritz：两弯曲方向与扭转各4个 Legendre 系数，共12个配置自由度、24维相空间，20个空间求积单元；质量矩阵依赖配置并包含旋转惯量。其材料、远端磁体与场接口与新高保真模型共享。该模型仍需估计剪切/伸长忽略、空间截断及血流/壁接触闭合误差。

本轮元数据给出 $E_0=3.62\times10^{-7}$ J、$\omega_0=4.4576294085$ rad/s。四组弯曲频率为

$$\begin{matrix}(4.4576294,4.4576294),\ (27.6941957,27.6941957),\\(79.7832866,79.7832866),\ (356.9402367,356.9402367)\ \mathrm{rad/s}.\end{matrix}$$

另四个频率约为 $370.4309161,1118.6110907,1984.6316311,3899.8926691$ rad/s。重复弯曲频率与圆截面、各向同性、直杆轴向偏场的旋转对称性一致；不能用舍入误差人为拆开它们，再宣称验证了非共振条件。以第一对为例，整数向量 $k=(1,-1,0,\ldots,0)$ 满足 $k\cdot\omega=0$，故该线性频率向量不满足任何正 $\gamma$ 的全整数 Diophantine 不等式。

对复规范变量，齐次正规形方程作用在单项式上的除数为 $i(\alpha-\beta)\cdot\omega$。若四阶项中相应共振单项式非零，就不能使用原两模态非共振公式将其除去；应采用

$$
H_4=Z_4+\{H_2,W_4\},\qquad
Z_4=\Pi_{\ker\operatorname{ad}_{H_2}}H_4,
$$

只对非零除数求解 $W_4$，并保留共振项。这里的 $Z_4$ 一般不再只是全部独立作用量的二次函数，因而旧 $2\times2$ twist 行列式和原有限幅值环面的数值常数都不能移植。可研究保留轴向旋转对称性的共振正规形、动量映射及约化后的非退化条件；也可引入有物理来源的截面/刚度各向异性、磁化方向或偏场/平衡形状，再重新验证频率、扭转和小除数。应明确具体破对称机制及其参数，不能仅为套用定理而修改频率。

线性1:1共振不等于证明所有有限振幅KAM环面不存在。非线性频率、对称性约化后的系统和具体候选环面仍可能满足其他KAM定理；它意味着当前标准非共振椭圆平衡点论证尚不成立。对新可训练复神经网与固定解析残差特征的比较，也须分别建立训练后结构/复域界；原S1的确定性35/45特征证书不能用网络名称来转移。

# 5 三维多物理场模型及其能量接口

本节给出继续写作和实现的统一数学框架。F系列是本报告的新编号，不替换1025的原号。已经运行的闭合近似与完整目标方程在实验章节逐项对应。Cosserat的几何、转动自由度和离散依据Gazzola等2018；磁性材料和远端磁段参数依据Tong等2025的对应实例，使用范围另作限定。[R1，R2]

## 5.1 参考构形与三维杆方程

用材料坐标 $s\in[0,L]$ 标记截面，中心线 $r(s,t)$，截面姿态 $R(s,t)\in\mathrm{SO}(3)$。$R$ 把体坐标映射到空间坐标；帽算子满足 $\widehat a\,b=a\times b$。定义

$$\nu=R^T r_s,\qquad \kappa=(R^TR_s)^\vee,\qquad \Omega=(R^TR_t)^\vee,\qquad v=r_t.\qquad\text{(F1)}$$

因而 $r_s=R\nu$、$R_s=R\widehat\kappa$、$R_t=R\widehat\Omega$。应变相容关系由混合偏导直接给出

$$\nu_t=R^Tv_s-\Omega\times\nu,\qquad \kappa_t=\Omega_s+\kappa\times\Omega.\qquad\text{(F2)}$$

每单位参考长度的质量 $\mu_r$、体坐标角惯量 $J_r$、内力 $n$ 和内矩 $m$ 给出

$$\mu_r r_{tt}=n_s+f_m+f_f+f_c+f_g,\qquad\text{(F3)}$$

$$J_r\dot\Omega+\Omega\times(J_r\Omega)=R^T(m_s+r_s\times n+\ell_m+\ell_f+\ell_c).\qquad\text{(F4)}$$

这里 $J_r$ 若与形变或时间有关，左侧应改为体角动量的完整物质导数，不能遗漏其变化。F3—F4采用相同参考长度测度；若水动力以当前长度定义，应乘伸长因子 $e=|r_s|$。这也解释了为什么不能把一份每单位体积的Maxwell体力直接加到每单位长度的杆方程。

本构从能量出发：

$$W=\tfrac12(\nu-\nu_0)^TC_\nu(\nu-\nu_0)+\tfrac12(\kappa-\kappa_0)^TC_\kappa(\kappa-\kappa_0),\qquad\text{(F5)}$$

$$n=R\partial_\nu W,\qquad m=R\partial_\kappa W.\qquad\text{(F6)}$$

圆截面可取 $C_\nu=\operatorname{diag}(k_sGA,k_sGA,EA)$，$C_\kappa=\operatorname{diag}(EI,EI,GJ_t)$，$J_t=2I$；不能一般地把扭转刚度写为 $EI_3$。Kirchhoff层施加 $\nu=e_3$，内力成为约束乘子；它保留三维弯曲和扭转。Cosserat层则允许剪切与伸长。本轮二者分别实现，没有把 $R$ 的九个矩阵元素当成九个无约束坐标。

夹持边界应规定 $r(0,t)=r_b(t)$、$R(0,t)=R_b(t)$；自由端或附加磁芯端应由边界虚功给出 $n(L)$、$m(L)$ 与端部惯性、外力、外矩的平衡。本轮数值采用固定基座和自由端，磁矩分布在远端5 mm，没有把远端段同时当成另一个重复计数的点偶极。推进／抽出和运动基座是后续独立边界任务。

## 5.2 磁载荷从同一个能量导出

在磁体周围取闭合面，空气／非磁背景下的Maxwell应力为

$$T_M=\mu_0^{-1}(BB^T-\tfrac12|B|^2I),\quad F=\int_{\partial\mathcal V}T_Mn\,dA,\quad \tau=\int_{\partial\mathcal V}(x-x_c)\times(T_Mn)\,dA.\qquad\text{(F7)}$$

该公式是总力和总矩，不能无说明地换成截面线积分。若外场尺度大于磁性截面且硬磁化可视为给定，设每单位参考长度体磁矩 $\mu_b(s)$、空间磁矩 $\mu=R\mu_b$，磁势为

$$V_m=-\int_0^L\mu(s)^TB(r(s),i,t)\,ds.\qquad\text{(F8)}$$

对位置和空间转角分别取虚变分，$\delta\mu=\delta\theta\times\mu$，得到

$$f_m=(\nabla B)^T\mu,\qquad \ell_m=\mu\times B.\qquad\text{(F9)}$$

该推导同时固定力、矩、符号及功率。磁矩随姿态旋转的贡献已经由力矩承担；求位置梯度时应固定姿态，不能重复加入姿态导数。若材料存在诱导磁化、饱和、磁滞或显著退磁场，则F8须替换为相应本构自由能，不能仅修改一个磁矩常数。

本轮局部无电流场采用

$$B(x)=b+G(x-x_0),\qquad G=G^T,\qquad \operatorname{tr}G=0,\qquad\text{(F10)}$$

输入顺序为 $(B_x,B_y,B_z,G_{xx},G_{yy},G_{xy},G_{xz},G_{yz})$。无旋和无散约束留下 $3+5$ 个局部自由分量，并不提供八个任意独立的广义力。对离散坐标 $q$，写磁通特征 $\phi(q)\in\mathbb R^8$，则

$$V_m(q,u)=-\phi(q)^Tu,\qquad Q_m=G_m(q)u,\qquad G_m=(D_q\phi)^T,\quad P_m=\dot q^TG_mu.\qquad\text{(F11)}$$

任何理想 $U$ 必须经过实际端口映射。最小二乘分配留下的误差 $r_u=G_m u-U$ 明确进入闭环误差预算；不足秩时不能称作精确磁实现。本轮12自由度ROM的参考分配约有18.5%的加权广义力残差，后续真实杆仿真采用受限后的实际磁输入。

进一步，线圈产生的场应由 $B(x,i)=\sum_a i_a b_a(x)$ 决定。本轮建立12个空气芯圆线圈的Biot–Savart模型，计算了 $8\times12$ 局部场—电流矩阵、限流和限电流变化率分配；尺寸和匝数均是明确工程选值。该模型证明了一个可运行的电磁输入接口，不构成实物标定。真实线圈上的电感、互感、电阻、温升及驱动电压上限仍需参数。

如需把驱动电路计入总能量，使用磁链 $\lambda_c$ 而不是把电流当独立守恒状态：

$$\lambda_c=L_ci+\Phi(q),\quad v_{\mathrm{drive}}=L_c\dot i+R_ci+(D_q\Phi)\dot q,\qquad\text{(F12)}$$

$$E_c=\tfrac12(\lambda_c-\Phi)^TL_c^{-1}(\lambda_c-\Phi).$$

于是 $-\partial_q E_c$ 给出相同的磁广义力，电端口功率为 $i^T v_{\mathrm{drive}}$，电阻热为 $i^T R_c i$。这是可扩展总能量系统的接口；本轮线圈分配尚未积分F12。

## 5.3 完整血流目标与已经运行的闭合层

完整目标是在移动血管—导管流域 $\Omega_f(t)$ 上求不可压缩流动：

$$\rho_f(\partial_tu+(u-w_{\mathrm{ALE}})\cdot\nabla u)=\nabla\cdot\sigma_f+\rho_fg_{\mathrm{eff}},\qquad \nabla\cdot u=0,\qquad\text{(F13)}$$

其中 $\sigma_f=-p_f I+2\eta D(u)$，或使用有来源、经过参数识别的非牛顿应力。F13中的时间导数是在ALE坐标下的导数；若在固定空间坐标下写，则对流项为 $u\cdot\nabla u$。导管和壁表面满足速度连续及牵引反作用。全耦合时杆表面牵引积分已经给出 $f_f$、$\ell_f$，不再叠加另一份Morison拖曳。

入口给定实测或文献支持的周期流量／压力波形；出口可接RCR模型，静脉／动脉的顺应性、压力和生理调节分别标定。微重力不能通过把常数 $g$ 置零同时“推导”出新的入口波形。当前没有空间站个体数据，故没有虚构心排量、血压或血管尺寸的微重力修正率。

本轮基准采用规定的曲管脉动速度剖面：

$$u_f(x,t)=U_0[1+a\sin(2\pi f_bt)]\,[1-(d(x)/R_v)^2]_+\,t_v(x).\qquad\text{(F14)}$$

曲管中直接规定的F14并不是一个已求解的Navier–Stokes无散解；它是低成本单向载荷闭合。为检查瞬时抛物线近似，本轮还实际运行了相同流量下的Womersley分支。令 $\omega_b=2\pi f_b$、$\alpha=R_v\sqrt{\rho_f\omega_b/\eta}$、$\lambda^2=-i\alpha^2$，定义

$$F(r)=1-\frac{J_0(\lambda r/R_v)}{J_0(\lambda)},\qquad \overline F=1-\frac{2J_1(\lambda)}{\lambda J_0(\lambda)},\qquad\text{(F14a)}$$

$$u_z(r,t)=2\overline U[1-(r/R_v)^2]+\operatorname{Re}\left[-iU_1\frac{F(r)}{\overline F}e^{i\omega_bt}\right].\qquad\text{(F14b)}$$

它对应平均速度 $\overline U+U_1\sin(\omega_b t)$，实际取 $\overline U=0.02\,\mathrm{m/s}$、$U_1=0.009\,\mathrm{m/s}$；$\alpha$ 约4.533。$J_0$、$J_1$ 是第一类Bessel函数。直刚管解满足无滑移和给定谐波通量，其4097点径向表的最大通量积分误差约 $5.13\times10^{-14}\,\mathrm{m^3/s}$，独立有限差分的直管动量方程相对残差约 $3.28\times10^{-7}$。将它沿弯管切向映射仍是局部单向近似；未计算二次流或双向FSI。[R9]

两种流场共用相对速度 $w=u_f-v$、$P_\parallel=tt^T$、$P_\perp=I-tt^T$，每单位当前长度阻力为

$$f_d=c_\perp P_\perp w+c_\parallel P_\parallel w+\rho_fC_Da\,|P_\perp w|P_\perp w.\qquad\text{(F15)}$$

第三项等于 $\tfrac12\rho_f C_D(2a)|w_\perp|w_\perp$，投影宽度 $2a$ 没有遗漏。细长体线性阻力系数采用 $c_\perp=4\pi\eta/[\log(2L/a)+1/2]$、$c_\parallel=2\pi\eta/[\log(2L/a)-1/2]$。狭窄血管中的壁面放大、水动力屏蔽、有限 $\mathrm{Re}$ 修正仍需另校准，不能宣称细长体无限流体公式在贴壁时自动精确。

移动体Morison惯性项若启用，应分开压力梯度与附加质量，例如 $\rho_f A a_f+m_a(a_f-r_{tt})$，其中 $a_f=\partial_tu_f+(u_f\cdot\nabla)u_f$。它会同时改变惯性、几何项和流体功率，不能只给质量矩阵加常数而遗漏相关项。本轮明确关闭附加质量；不存在用速度减加速度的量纲错误。转动黏性采用轴向自旋阻力 $-4\pi\eta a^2(\omega\cdot t)t$，并记录其功率。

F15对相对运动耗散：$w^Tf_d\ge0$；对机器人机械能，$f_d^Tv$ 可正可负。规定流动是能源端口，血流可以推动导管。将全部血流简单记为 $-C\dot q$ 并据此宣称机械能单调下降，既不符合F15，也不符合本轮程序。

## 5.4 壁面接触与摩擦

设法向间隙 $g=R_v-a-d$，穿透量 $\delta=[-g]_+$，$n$ 指向管壁。理想接触可写 $g\ge0$、$\lambda_n\ge0$、$g\lambda_n=0$ 及切向摩擦锥。实际运行采用连续罚能与耗散：

$$V_c=\int\frac{k_c}{r+1}\delta^{r+1}\,ds,\quad f_{c,e}=-k_c\delta^r n,\quad r=3/2,\qquad\text{(F16)}$$

$$f_{c,d}=-c_n[ v_{\mathrm{rel}}\cdot n ]_+n-\mu_f\lambda_n\tanh(|v_\tau|/v_\epsilon)\,\frac{v_\tau}{|v_\tau|}.\qquad\text{(F17)}$$

最后一项在零速取零；接触耗散只在 $\delta>0$ 的激活接触上施加。程序取每单位长度的阻尼系数及法向合力密度为

$$c_n=2\zeta\sqrt{\mu_r r k_c\delta^{r-1}},\qquad \lambda_n=k_c\delta^r+c_n[v_{\mathrm{rel}}\cdot n]_+.\qquad\text{(F17a)}$$

它随 $\delta$ 趋零而消失。接触点速度包含 $v_c+\omega\times(a n)$ 减壁速度；对应接触矩为 $(a n)\times f_\tau$。忽略这一转动速度会使摩擦功率与转动方程不闭合。F16的 $k_c$ 按每单位长度定义，单位 $\mathrm{N}/\mathrm{m}^{5/2}$；两点Gauss积分后才是节点力。本轮的 $k_c$ 和 $\mu_f$ 属于工程罚模型参数，不宣称由弹性半空间的Hertz接触几何推得。

固定壁时，$f_{c,d}$ 及接触矩对总接触点运动的功率非正。若壁移动，壁端口须计入总功率。弹性力 $\delta_+^{3/2}$ 跨接触开闭仅 $C^1$；实际 $c_n$ 正比 $\delta_+^{1/4}$，其系数跨开闭也不满足通常的局部Lipschitz条件。因此完整接触场既不能直接放进解析KAM定理，也不能无条件沿用光滑向量场的全局阶数或Gronwall收敛证明。采用光滑近似须给出逼近误差、导数界和复域，不能仅用“正则化”替代证明。

## 5.5 微重力与生理边界

若在空间站随动参考系中描述，$g_{\mathrm{eff}}$ 包括重力与平台平移之差，以及科里奥利、离心、欧拉项；压力梯度造成的浮力不能重复加进两次。完整FSI由流体压力自然承担；当前规定流场层使用 $(\rho_r-\rho_f)A g_{\mathrm{eff}}$ 作为一次性的浸没有效重力。残余加速度和抖动的本轮数值是合成参数，不是空间站测量数据。

生理适配至少包括入口脉动、出口阻抗和顺应性、血管几何／壁本构、血液黏度或流变模型、体位与循环状态。它们属于边界和材料参数，不是把杆的重力项删去即可得到。当前固定血管壁、固定基座和无插入只是本轮可复算层的假设，后续三维目标继续包含这些物理扩展。

## 5.6 弱式与可验证的降阶

对F3—F4分别用平移虚位移 $\delta r$ 和体虚转角 $\eta$，内力虚功可写

$$\delta\nu=R^T\delta r_s-\eta\times\nu,\quad \delta\kappa=\eta_s+\kappa\times\eta,\qquad\text{(F18)}$$

$$\delta\int W\,ds=\int(\partial_\nu W)^T\delta\nu+(\partial_\kappa W)^T\delta\kappa\,ds.$$

分部积分产生自然边界 $n\cdot\delta r+m\cdot\delta\theta$，给出与端部载荷一致的离散方程。降阶从构形嵌入 $r=r(q,s)$、$R=R(q,s)$ 出发，分别定义平移Jacobian $A_r=\partial_q r$、体角速度Jacobian $A_\Omega$，即 $r_t=A_r\dot q$、$\Omega=A_\Omega\dot q$。动能立即给出

$$M(q)=\int[\mu_rA_r^TA_r+A_\Omega^TJ_rA_\Omega]ds+M_{\mathrm{tip}}(q),\quad T=\tfrac12\dot q^TM(q)\dot q.\qquad\text{(F19)}$$

这里 $J_r$ 仍表示F4中的截面角惯量，不与两个几何Jacobian混用。Euler–Lagrange方程为

$$M\ddot q+c_{\mathrm{geo}}(q,\dot q)+\nabla V=Q_{\mathrm{nc}},\quad (c_{\mathrm{geo}})_i=\sum_{jk}\tfrac12(\partial_jM_{ik}+\partial_kM_{ij}-\partial_iM_{jk})\dot q_j\dot q_k.\qquad\text{(F20)}$$

令 $p=M\dot q$，不可遗漏的Hamiltonian和动量方程为

$$H=\tfrac12p^TM^{-1}p+V,\quad \dot q=H_p,\quad \dot p_i=-\tfrac12p^T(\partial_iM^{-1})p-\partial_iV+Q_{{\mathrm{nc}},i}.\qquad\text{(F21)}$$

等价地，质量项为 $+\tfrac12\dot q^T(\partial_iM)\dot q$。这不是可忽略的高阶修饰，而是变质量能量守恒所需的项。移动基座嵌入还会产生 $T=\tfrac12\dot q^TM(q,t)\dot q+a(q,t)^T\dot q+c(q,t)$，因此 $p=M\dot q+a$、$H=\tfrac12(p-a)^TM^{-1}(p-a)+V-c$，显式时间功也须保留。

本轮12自由度模型在两个弯曲轴和一个扭转轴分别使用四个Legendre曲率系数，以 $\mathrm{SO}(3)$ 指数更新姿态，以几何Jacobian装配 $M(q)$，20／40／80空间积分进行独立对照。它是可验证的Kirchhoff分析层，不能当作已经收敛的完整Cosserat真值。有限差分中心速度和体角速度独立重算动能，与装配质量给出的结果相符至约 $4.8\times10^{-10}$ 相对误差；磁势的虚功检查也通过。完整杆与ROM采用相同材料、远端磁段和磁输入顺序，随后进行跨模型控制验证。

## 5.7 总功率作为共同验收量

机械能取平动动能、转动动能、杆应变能与罚接触势；磁载作为输入功计入，则

$$\dot E_{\mathrm{mech}}=P_m+P_f+P_{c,d}+P_g+P_b-P_{\mathrm{structural\ loss}}.\qquad\text{(F22)}$$

若把 $V_m$ 也计入能量，则相应把机械磁功改写为外场显式变化功，不能两边重复计数。完整流固耦合时，把流体动能、壁能、出口电路式储能和必要的热能加入，界面牵引功成对抵消，只剩外部边界功和不可逆耗散。这个能量闭合是学习、降阶、数值离散和控制比较的共同核查量。


# 6 三维杆 血流 接触与磁驱动的实际计算

## 6.1 本轮真正实现了什么

实现对象是空间中心线、完整材料姿态、平动及转动惯性均保留的三维 Cosserat 杆。16、32、64 段分别具有 93、189、381 个受约束后的位形自由度；相空间维数再加相应速度。不是两模态梁，也没有把第二弯曲方向或扭转删除。

方程和姿态更新支持有限转动，但当前通过验证的主跟踪幅值较小，不能据此声称大挠度、多圈扭转或大范围插入已全面验证。不可行目标压力试验也不能替代这些独立验证。

基准层包括规定的脉动参考流、相对速度阻力、三维弯曲刚性管腔、罚函数接触、接触阻尼和摩擦、残余加速度及抖动。主程序使用官方 PyElastica 1.0.0 的空间离散与 PositionVerlet 步进。新增的磁、流、接触和控制算子在 `stage2/program/rod3d/model.py` 中可独立审查。

**这里的“高维杆”不等于已经完成高保真双向 FSI。** 未求解 Navier–Stokes 压力与速度场，未求解可变形血管壁，未加入附加质量、壁面润滑、插入/ALE、自接触或实测空间站加速度。当前固定基部和固定杆长是计算基准的边界选择；下一层可以替换边界和流/壁求解器，完整三维目标没有被简化模型取代。

独立的 12 自由度三维 Kirchhoff 应变 Ritz 模型由主任务实现，用作训练与控制设计。它的四类磁前馈实际传入本三维杆，不能把它自身的训练或拟合误差当成本杆的跟踪结果。

## 6.2 参数来源：重新核读原文，而非搬用旧 v10

本轮重新获取并阅读 Tong 等的正式发表 PDF，视觉核对第 10 页 §5.1 和第 11 页的实验/数值上下文。原文：Dezhong Tong, Zhuonan Hao, Jiyu Li, Boxi Sun, Mingchao Liu, Liu Wang, Weicheng Huang, “Real-time simulation enabled navigation control of magnetic soft continuum robots in confined lumens”, *Journal of the Mechanics and Physics of Solids* 203 (2025), 106198, DOI 10.1016/j.jmps.2025.106198。原文链接：<https://eprints.ncl.ac.uk/file_store/production/306197/7CAB59D2-D36A-4A12-8648-428A2D798BBC.pdf>。所读 PDF SHA256：`41c2420bccc7e27e12050605a5d4bd5a56174af456e415ea91e5662c11a9f6f5`。

| 数量 | 本轮取值 | 证据类别与范围 |
|---|---:|---|
| 长度 $L$ | $0.100\,$ $\mathrm m$ | Tong 第 10 页 §5.1 报告 |
| 半径 $r_0$ | $0.0006\,$ $\mathrm m$ | 同上 |
| 弹性模量 $E$ | $3\,$ $\mathrm{MPa}$ | 原文报告磁性复合材料测量值 |
| 剪切模量 $G$ | $1\,$ $\mathrm{MPa}$ | 同上；把该 $E,$ $G$ 赋予全长均匀杆是本轮显式工程假设 |
| 末端磁段 $L_m$ | $0.005\,$ $\mathrm m$ | 原文报告 |
| 轴向线磁矩密度 $\mathfrak m_0$ | $0.1448\,$ $\mathrm{A\,m}$ | 原文报告；不能误读成总体磁偶极矩 |
| 总磁偶极矩 | $\mathfrak m_0L_m$ $=7.24$ $\times10^{-4}\,$ $\mathrm{A\,m^2}$ | 由以上报告量推导 |
| 杆密度 $\rho_s$ | $1800\,$ $\mathrm{kg/m^3}$ | 工程值；另算 $1200,$ $2400$ 敏感性，原文未提供可直接沿用的实测值 |
| 质量比例耗散率 $\gamma$ | $2\,$ $\mathrm{s^{-1}}$ | 工程值；另算 $1,$ $4$ 敏感性 |
| 流体密度 $\rho_f$ | $1060\,$ $\mathrm{kg/m^3}$ | 文献常用模型值，本轮工程采用 |
| 定常黏度 $\eta$ | $0.0035\,$ $\mathrm{Pa\,s}$ | 文献高剪切黏度尺度，本轮采取常黏度近似 |
| 脉动流基准尺度 $U_0$ | $0.04\,$ $\mathrm{m/s}$ | 工程给定；实际中心线峰值为 $0.04(1$ $+0.45)$ $=0.058\,$ $\mathrm{m/s}$ |
| 管腔半径 $R_v$ | $3\,$ $\mathrm{mm}$ | 合成几何 |
| 接触系数 $k_H$ | $2000\,$ $\mathrm{N/m^{5/2}}$ | 每参考弧长罚系数，非由血管材料计算出的 Hertz 常数；另算 $2$ $\times10^4,$ $2$ $\times10^5$ |
| 摩擦系数、速度正则化 | $0.15$、$10^{-4}\,$ $\mathrm{m/s}$ | 工程取值，未以导管—血管实验校准 |
| 残余加速度 | $(8,$ $-5,$ $2)$ $\times10^{-5}\,$ $\mathrm{m/s^2}$ 加合成抖动 | 非空间站测量记录 |

流体模型值的一级来源是 Lunnoo 与 Puangmali, *Nanoscale Research Letters* 10 (2015), 426，DOI 10.1186/s11671-015-1127-5，Methods 的式(14)附近及式(16)：<https://link.springer.com/article/10.1186/s11671-015-1127-5>。该文实际使用广义幂律黏度，$0.0035$ 是高剪切尺度；因此不能拿这篇文献为本轮整套常黏度杆阻力闭合“背书”。这里只核验两个物性尺度及其语境。

Tong 文中的约 $4\,\mathrm T$ 是制造时磁化脉冲，**不是本轮施加的控制磁场**。原文约 $10\,\mathrm{ms}$ 的时间步属于其拟静态/插入算法；本轮显式动力学采用微秒步长并另做收敛检查，不直接沿用该时间步。

本轮没有用户实测材料、血流或空间站记录。参数类别在完整 `config.json` 中保留，原始配置不被调参后的配置覆盖。

## 6.3 离散几何、磁能与真实磁输入

中心线初态沿 $+z$，$\boldsymbol r(0)=(0,0,0)$，$\boldsymbol r(L)=(0,0,0.1)$。材料姿态用 $D_e\in SO(3)$ 表示，约定它把空间向量变为材料坐标。因而

$$
\boldsymbol\mu_e=D_e^T\boldsymbol\mu_e^b,
\qquad \boldsymbol\tau_e^b=D_e\boldsymbol\tau_e,
\qquad
(\boldsymbol\tau_e^b)^T\boldsymbol\omega_e^b
=\boldsymbol\tau_e^T\boldsymbol\omega_e.
$$

PyElastica 的截面转动惯性、剪切和弯扭矩阵从其官方构造器生成。所用版本剪切校正系数为 $27/28$，不是自行把所有剪切刚度设为 $GA$。杆的参考截面积、截面二次矩分别为 $A_0=\pi r_0^2$、$I=\pi r_0^4/4$，$J_p=2I$。

对每个元素 $[s_e,s_{e+1}]$ 与末端磁段 $[L-L_m,L]$ 求**精确交叠长度** $\ell_{m,e}$，设置

$$
\boldsymbol\mu_e^b=\mathfrak m_0\ell_{m,e}\boldsymbol e_3,
\quad
\alpha_e=\frac{(\max(s_e,L-L_m)+\min(s_{e+1},L))/2-s_e}{s_{e+1}-s_e}
$$

（无交叠元素磁矩为零）。磁载荷位置为 $\boldsymbol x_{m,e}=(1-\alpha_e)\boldsymbol r_e+\alpha_e\boldsymbol r_{e+1}$。这样 16/32/64 段总磁矩均为 $7.24\times10^{-4}\,\mathrm{A\,m^2}$；不会因磁段不足一整段而随网格人为改变执行器能力。

输入为

$$
u=(B_x,B_y,B_z,G_{xx},G_{yy},G_{xy},G_{xz},G_{yz}),\qquad
\boldsymbol B(\boldsymbol x)=\boldsymbol B_0+\mathsf G(\boldsymbol x-\boldsymbol x_0),
$$

$$
\mathsf G=
\begin{pmatrix}
G_{xx}&G_{xy}&G_{xz}\\
G_{xy}&G_{yy}&G_{yz}\\
G_{xz}&G_{yz}&-G_{xx}-G_{yy}
\end{pmatrix},\qquad \boldsymbol x_0=(0,0,0.1).
$$

因此仿射场严格满足 $\nabla\cdot\boldsymbol B=0$ 与无源区 $\nabla\times\boldsymbol B=0$。$B$ 的单位是 T，$\mathsf G$ 的单位是 T/m；它不是磁场强度 $H$。这八个输入作用于同一空间场，不能替换成每个杆模态可独立施加的广义力。

由

$$
V_m=-\sum_e\boldsymbol\mu_e^T\boldsymbol B(\boldsymbol x_{m,e})
$$

求变分得到

$$
\boldsymbol F_e=\mathsf G^T\boldsymbol\mu_e,
\qquad \boldsymbol\tau_e=\boldsymbol\mu_e\times\boldsymbol B(\boldsymbol x_{m,e}).
$$

按 $(1-\alpha_e),\alpha_e$ 分配节点力，并把力矩转换到材料坐标。磁势被单独记录；本轮机械能 $H_{\mathrm{mech}}$ 只包含动能、弹性能和接触势，磁输入只在外功中计账，避免重复计入。

请求信号经过 $\|\mathsf G\|_F\le0.03\,\mathrm{T/m}$ 和充分条件 $\|\boldsymbol B_0\|+0.12\|\mathsf G\|_F\le0.005\,\mathrm T$ 限制。该条件约束指定球域内的**仿射场**。对于完整线圈场，实际 $B$ 与实际梯度另行计算和报告，不把仿射充分条件当成完整非均匀场的全域定理。

## 6.4 血流、接触、摩擦与微重力的确切闭合

三维管腔中心线为

$$
\boldsymbol c(z)=\left(0.0009\sin\frac{2\pi z}{L},\;0.0006\sin\frac{\pi z}{L},\;z\right).
$$

牛顿迭代求最近点，得到距离 $d$、外法向 $\boldsymbol n$ 与中心线切向 $\boldsymbol t_f$。这里不是把三维点直接投到一条平面曲线上。规定流为

$$
\boldsymbol u_f(\boldsymbol x,t)=
U_0[1+0.45\sin(2\pi\times1.2t)]
\max\left(0,1-\frac{d^2}{R_v^2}\right)\boldsymbol t_f.
$$

以杆当前切向分解 $\boldsymbol w=\boldsymbol u_f-\boldsymbol v$，使用

$$
\boldsymbol f_f=c_\perp\boldsymbol w_\perp+c_\parallel\boldsymbol w_\parallel
+\rho_f C_Dr\,|\boldsymbol w_\perp|\boldsymbol w_\perp,
\quad
c_\perp=\frac{4\pi\eta}{\log(2L/r)+1/2},
\quad c_\parallel=\frac{2\pi\eta}{\log(2L/r)-1/2}.
$$

以上是每**当前长度**的力，乘当前元素长度后组装。轴向自旋阻力矩为 $-4\pi\eta r^2\ell(\boldsymbol\omega\cdot\boldsymbol t)\boldsymbol t$。未加入环境流体涡量、非局部水动力、流体附加质量和 Morison 惯性项，不能把此模型称为完整 Morison/FSI。

相对速度耗散 $\boldsymbol f_f\cdot\boldsymbol w\ge0$，但对杆的功率满足

$$
\boldsymbol f_f\cdot\boldsymbol v=
\boldsymbol f_f\cdot\boldsymbol u_f-\boldsymbol f_f\cdot\boldsymbol w,
$$

所以脉动血流可以给杆供能。程序同时保存实际流体功率和非负相对耗散；不把流体项一律当成负耗散。以所选 $R_v,\rho_f,\eta,1.2\,\mathrm{Hz}$ 计算的 Womersley 数约为 $4.53$，因此这一无相位滞后的抛物线参考流不是该参数下严格的 Womersley 解，更不是弯管 Navier–Stokes 解。

每元素取两点 Gauss 接触求积。固定接触包络半径 $r_0$，穿透量 $\delta=[d-(R_v-r_0)]_+$，每参考长度接触势与弹力为

$$
\Psi_c=\frac{k_H}{5/2}\delta^{5/2},\qquad
\boldsymbol f_{c,\mathrm{el}}=-k_H\delta^{3/2}\boldsymbol n.
$$

使用参考长度权重，保证保存的接触势与所组装弹力的变分一致。该 $3/2$ 指数在这里是工程罚律，不代表已经证明细杆—薄血管壁满足球面 Hertz 接触的适用条件。

接触点速度包括表面力臂 $r_0\boldsymbol n$ 的转动速度。令参考线质量 $\mu_\ell=\rho_s A_0$、接触指数 $p_c=3/2$。代码实际采用的每参考长度阻尼系数及法向合力密度是

$$
c_n(\delta)=2\zeta\sqrt{\mu_\ell p_c k_H\delta^{p_c-1}},\qquad
\lambda_n=k_H\delta^{p_c}+c_n(\delta)[v_n]_+\quad(\delta>0),
$$

未激活时 $\lambda_n=0$，单个求积点的法向力为 $F_n=w_g\lambda_n$。由于 $p_c=3/2$，$c_n\propto\delta^{1/4}$，完整接触场在开闭点一般不具局部 Lipschitz 正则性；即便弹性力是 $C^1$，也不能把光滑场的 Gronwall 或积分阶数证明直接用于这一完整接触模型。该点不影响程序中已验证的点态非负法向力与耗散功率符号，却使良定性及收敛证明需要另外处理。法向只在向壁运动时耗散；求积点切向力采用

$$
\boldsymbol F_t=-\mu F_n\tanh(|\boldsymbol v_t|/v_\epsilon)
\frac{\boldsymbol v_t}{|\boldsymbol v_t|},
$$

并组装表面力臂对应的摩擦矩。于是 $|\boldsymbol F_t|\le\mu F_n$、摩擦功率非正；法向耗散也非正。仅弹性函数 $[\delta]_+^{3/2}$ 跨开闭点为 $C^1$、不为 $C^2$；完整接触场还有上述更低正则性的阻尼以及 $[v_n]_+$，不能把含接触支路直接送入解析 KAM 定理。

残余重力采用 $(\rho_s-\rho_f)A_0\boldsymbol g(t)$ 的浮力近似，只计一次。当前阻力闭合没有另外求解流体压力，因此没有把同一静水压力重复加入。$\boldsymbol g(t)$ 为合成残余矢量和两频率抖动，不能替代真实轨道/舱体/人体坐标系中的加速度记录。代码的 `flow.enabled` 同时表示“启用浸没流体环境”，并非仅开关流速或拖曳：设为 `false` 时不计流体力，也不减去流体密度。若要模拟静止血液中的杆，应保持该开关 `true`、把参考流速尺度设为零，这样浮力和相对运动阻力仍然存在。纯扭转保守诊断同时关闭流体环境和残余重力，不把它解释为静止血液实验。

### 6.4.1 相同流量下的局部 Womersley 改进

另外实际运行了一条同参数的 Womersley 流型敏感性支路。对刚性直圆管、充分发展且轴对称的 Newtonian 流，轴向速度满足

$$
\rho_f\partial_t u=G_p(t)+\eta\frac1r\partial_r(r\partial_r u),
\qquad \partial_r u(0,t)=0,\quad u(R_v,t)=0.
$$

取复谐波时间约定 $e^{i\omega t}$、$\alpha=R_v\sqrt{\rho_f\omega/\eta}$、$\lambda^2=-i\alpha^2$，设

$$
F(r)=1-\frac{J_0(\lambda r/R_v)}{J_0(\lambda)},\qquad
\overline F=\frac{2}{R_v^2}\int_0^{R_v}rF(r)\,dr
=1-\frac{2J_1(\lambda)}{\lambda J_0(\lambda)}.
$$

归一化因子由 Bessel 积分恒等式得到，故平均谐波速度指定为 $\widehat{\overline u}=-i\,0.009\,\mathrm{m/s}$ 时，解为

$$
u(r,t)=0.04\left(1-\frac{r^2}{R_v^2}\right)
+\operatorname{Re}\left[-i\,0.009\frac{F(r)}{\overline F}e^{i\omega t}\right],
\quad Q(t)=\pi R_v^2[0.02+0.009\sin(\omega t)].
$$

把谐波解代入动量方程，压力梯度幅值满足 $\widehat G_p=i\rho_f\omega\widehat{\overline u}/\overline F$；这也提供了独立方程残差检验。截面流量与原瞬时抛物线严格相同，但径向谐波幅值和相位不同。径向表在进入杆动力学之前已验证无滑移、通量及独立有限差分动量残差。采用同一相对阻力算子，只替换参考速度；沿弯管切向的映射仍是局部近似，没有因此求解流体压力对杆的完整作用、附加质量或双向 FSI。

原始理论书目已核对：J. R. Womersley, “Method for the calculation of velocity, rate of flow and viscous drag in arteries when the pressure gradient is known”, *The Journal of Physiology* 127(3) (1955), 553–563，DOI 10.1113/jphysiol.1955.sp005276：<https://physoc.onlinelibrary.wiley.com/doi/10.1113/jphysiol.1955.sp005276>。以上固定流量归一化与本轮查表/残差检验是此处明确给出的推导和实际计算，不声称原文验证了本轮弯管机器人。

## 6.5 控制、失败与修正选择

解析静态前馈只用作控制基准。令 $a=L-L_m$，小挠度悬臂的分布磁偶矩、梯度力顺应度为

$$
C_B=\frac{\mathfrak m_0}{EI}
\left[\frac{Ls^2}{2}-\frac{s^3}{6}\right]_{a}^{L},\qquad
C_G=\frac{\mathfrak m_0}{EI}
\left[\frac{Ls^3}{6}-\frac{s^4}{24}\right]_{a}^{L}.
$$

这分别来自截面点偶矩的尖端影响核 $s(2L-s)/(2EI)$ 和点力影响核 $s^2(3L-s)/(6EI)$，积分区间均为真实末端磁段。选均匀场份额 $\alpha=0.8$，对目标横向位移 $d_x,d_y$ 取 $B_x=\alpha d_x/C_B$、$G_{xz}=(1-\alpha)d_x/C_G$，另一个方向同理，叠加 $B_z=0.5\,\mathrm{mT}$。这是设计前馈所用的线性近似；被控制的动力学始终是完整三维杆。

初始控制采用 $d=e_{\mathrm{ref}}+1.5e+0.35\dot e$。这个“尖端平动速度→分布磁矩/梯度”的反馈不是共点功率反馈，也没有被动性保证。长时间实际计算出现高模态增长，相关失败轨迹被保留。10/5 微秒步长分别约在 $0.603/1.252\,\mathrm s$ 崩溃。2.5 微秒虽跑完 $2\,\mathrm s$，但剪切/伸长达到 $0.224$、限幅比例约 $80.5\%$、机械能—外功归一残差约 $0.965$，仍不合格。首次出现 $0.1\%$ 应变的时刻约为 $0.229,0.243,0.251\,\mathrm s$，显示早期增长并非仅由某一个粗步长产生；这不是连续 PDE 有限时爆破的证明。

随后只在独立 `config_position_feedback.json` 把速度反馈增益设为零，保留同一物理参数、目标和位置增益，完成全部主比较及收敛算例。实测可用只指本轮给定 $2\,\mathrm s$ 窗口内的有限、可收敛轨迹，**不是全局闭环稳定性定理**。未来若采用负功率反馈，应从真实磁端口 $y=A(q)^Tv$ 出发设计 $u_{\mathrm{fb}}=-K y$，并考虑刚性、限幅和采样分配；不能把非共点尖端速度直接称为该被动端口输出。

四类 12 自由度 ROM 前馈是 linear、analytic residual、trainable complex、exact ROM。文件已经包含轴向偏置，插值后加同一个 $K_p=1.5,K_d=0$ 位置反馈，再施加同样磁场约束。没有重新训练来迎合三维杆测试结果，也没有用磁场端口给每个模态独立施力。exact ROM 只意味着低维参考模型自身的精确函数，不是完整杆的真值。

## 6.6 线圈实现与必须保留的不利结果

12 个无铁芯圆线圈采用固定工程几何、Biot–Savart 场、每线圈 $2\,\mathrm A$ 与相邻采样 $20\,\mathrm{A/s}$ 差商限制；并非已制造、热设计完成或实测标定的装置。每 $2\,\mathrm{ms}$ 做一次受限电流分配，起始电流为零，第一步也受采样变化率限制。初始支路在采样间零阶保持，只有样本差商满足限制；最终支路改用连续分段线性电流，才得到几乎处处的连续时间速率界。

先运行的仿射线圈分支在真实磁段质心处与完整 Biot–Savart 场比较：场强相对 $L^2$ 误差约 $1.30\%$，但梯度力误差约 $105.2\%$，力差峰值约 $1.31\,\mu\mathrm N$；磁矩误差约 $4.65\%$。力的分母很小且梯度比场值对高阶空间变化更敏感，**小场误差绝不推出小力误差**。该结果不能删除，也不能用在原点映射秩为 8 来掩盖。

因此另实现 `run_biot_savart.py`：在每个实际时间步、实际杆位置与材料姿态上，对磁段质心计算完整圆线圈求积场及其解析空间导数。设源元 $d\boldsymbol\ell$、$\boldsymbol d=\boldsymbol x-\boldsymbol x'$，则

$$
\boldsymbol B=\frac{\mu_0NI}{4\pi}\oint
\frac{d\boldsymbol\ell\times\boldsymbol d}{|\boldsymbol d|^3},\qquad
\partial_j\boldsymbol B=
\frac{\mu_0NI}{4\pi}\oint
\left(\frac{d\boldsymbol\ell\times\boldsymbol e_j}{|\boldsymbol d|^3}
-\frac{3(d\boldsymbol\ell\times\boldsymbol d)d_j}{|\boldsymbol d|^5}\right).
$$

该闭环支路使用相同电流分配和控制律，改变的是动力学中的实际磁力/矩评估。圆线圈以 256 个中点源元求积；杆元素上的磁段仍采用对应交叠区间质心，这是明确的空间离散误差来源。完整场可有高阶空间项；名义输入的八个分量只描述原点的场及梯度，不能代表全部空间场。

## 6.7 数值验证的证据等级

首先独立核验算子，而不是只检查最终轨迹“看起来合理”。磁势方向导数与组装磁力相对误差约 $1.68\times10^{-8}$，转动方向导数与磁矩误差约 $1.63\times10^{-9}$，接触势与弹力误差约 $5.75\times10^{-11}$。材料/空间力矩功率恒等式误差为舍入范围；随机接触速度下耗散功率为负，Coulomb 超界仅约 $10^{-20}\,\mathrm N$ 的浮点余量。16/32/64 段总磁矩相同，截面转动惯性矩阵正定、条件数为 2。

PyElastica 构造器因采用绝对阈值，对 SI 制下约 $10^{-13}\,\mathrm{kg\,m^2}$ 的截面转动惯性打印“小于容差”提示。本轮检查了矩阵正定与条件数；未为消除提示擅自改大半径、密度或惯性。

每一步保存并累积功率端口，检验

$$
H_{\mathrm{mech}}(T)-H_{\mathrm{mech}}(0)
\simeq W_m+W_f+W_{c,\mathrm{diss}}+W_g+W_{\mathrm{struct}}.
$$

接触弹力功已与接触势配对，不重复放入右端。使用实际力评估时刻的载荷与 kick 前后速度平均求功；输出整个能量—外功残差，不只报告能量“保持良好”。完整开放系统不应该严格守恒机械能。

空间收敛：在相同 $5\,\mu\mathrm s$ 步长比较 16、32、64 段；时间收敛：固定 32 段比较 $10,5,2.5\,\mu\mathrm s$。杆中心线插值到共同参考弧长网格，在完全相同输出时刻比较，另外比较材料姿态的 $SO(3)$ 测地距离。相邻差估计阶数 $p=\log_2(e_h/e_{h/2})$ 只是该算例的实测证据。

接触压力算例采用不可行目标 $(20,10)\,\mathrm{mm}$，专门触发场限幅和接触；其巨大跟踪误差不能与可行目标主算例混为算法性能。基础软罚系数的 $0.525\,\mathrm{mm}$ 穿透说明罚参数不可忽视；另做罚刚度敏感性并与空间收敛分开。接触曲线的峰值是两点求积处的峰值；不宣称已建立整条连续杆的严格不穿透界。

保守纯扭转算例去掉流、壁、重力、结构耗散及磁输入，初态沿杆给定 $0.03(s/L)^2$ 弧度材料扭转，保留完整转动惯性。它单独检查姿态与无外载能量误差随步长缩小的行为。它不能为有血流、摩擦、反馈、限幅或零阶保持的系统证明辛性或 KAM。

## 6.8 软件来源与复算文件

官方离散依据：Gazzola, Dudte, McCormick, Mahadevan, *Royal Society Open Science* 5 (2018), 171628，DOI 10.1098/rsos.171628，尤其 §3.3；原文作者组 PDF：<https://www.cosseratrods.org/publications/pubs/2018_RSOS.pdf>。该节明确说明一般外载情形未必为 Hamilton 系统，伸长几何重标度与经典 Hamilton Cosserat 的关系还需相应条件；本轮不把“PositionVerlet”名称当作完整开放系统结构保持的证明。

官方源码：<https://github.com/GazzolaLab/PyElastica>；版本文档：<https://docs.cosseratrods.org/en/v1.0.0/api/rods.html>。在执行前已阅读所用 rod factory、内部力/矩、能量、PositionVerlet、外力和边界条件实现。下载的 PyElastica 1.0.0 wheel SHA256 为 `ae2277d77ae9f20473c3beb1cbaa883869b826597a074da0b62a4e5fce7cc9f8`，与 PyPI 元数据一致。

每个成功算例保存 `trajectory.npz`、`diagnostics.csv`、`parameters.json`、`summary.json` 和 `environment.json`。后者记录实际依赖版本与运行时实现哈希，外部学习前馈也记录哈希。失败试验保存 `failure.json` 和有限时段原始轨迹。完整复算命令见 `stage2/program/rod3d/README.md`。最终综合数值在同目录 `analysis.json`、`comparison.csv` 和静态可编辑 SVG/PNG 图中给出；以下结果表由这些原始结果重新生成。

<!-- COMPUTED_RESULTS_BEGIN -->

## 6.9 已完成的实际计算结果

以下均由保存的原始轨迹计算；主跟踪窗口为 $t\in[0.5,2]\,\mathrm s$，目标是同一三维尖端位置，误差包含轴向几何缩短。不同分支的工程限制与模型层级不得混在一起解释。

| 分支 | 段数 | 步长/μs | 尖端RMSE/mm | 能量—外功归一残差 | 耗时/s |
|---|---:|---:|---:|---:|---:|
| 无磁控制 | 32 | 10 | 1.278463 | 1.050e-05 | 33.80 |
| 静态顺应度前馈 | 32 | 10 | 0.327783 | 2.579e-06 | 33.82 |
| 前馈＋位置反馈 | 32 | 10 | 0.153806 | 2.878e-06 | 37.10 |
| 前馈＋位置反馈 | 64 | 5 | 0.155474 | 2.858e-06 | 111.62 |
| 同流量局部Womersley | 32 | 10 | 0.153218 | 3.025e-06 | 48.75 |
| 仿射线圈模型 | 32 | 10 | 0.160319 | 2.389e-06 | 35.62 |
| 完整线圈场，原点分配 | 32 | 10 | 0.737609 | 2.198e-06 | 64.13 |
| 完整线圈场，原点分配 | 64 | 5 | 0.742583 | 2.103e-06 | 187.61 |
| 完整场，管状域采样约束，ZOH | 32 | 10 | 0.617319 | 3.287e-06 | 65.35 |
| 完整场，采样约束，连续电流斜坡 | 32 | 10 | 0.617328 | 3.152e-06 | 68.66 |

完整线圈原点分配在数值上有小能量—外功残差，但违反工程场界并表现出显著控制模型失配；因此不能把该列当作已满足场约束的实现。最终受约束连续斜坡支路通过所检查的约束，但跟踪精度仍低于理想场。该性能差距是本轮发现，不删去。

### 6.9.1 学习前馈向真实三维杆的转移

| 前馈模型 | 32段RMSE/mm | 64段RMSE/mm | 64段最大接触穿透/μm |
|---|---:|---:|---:|
| 线性ROM | 0.111325 | 0.110877 | 0.000 |
| 解析残差字典 | 0.267221 | 0.276685 | 34.566 |
| 可训练复网络 | 0.113801 | 0.112972 | 0.000 |
| 精确低维ROM函数 | 0.111325 | 0.110877 | 0.000 |

复网络优于这次解析残差字典，但没有优于线性ROM或精确低维函数。不能据此宣布“神经网络必然提升控制”。线性与精确低维结果接近，说明此小变形目标下非线性修正并未成为决定性收益。所有四类前馈均受到同一物理场输入和同一位置反馈约束；这里只验证理想场下的跨模型转移，没有把这些结果冒充实际线圈实现的误差。

### 6.9.2 网格、步长与保守扭转

| 细化对象 | 相邻差1 | 相邻差2 | 观察阶 |
|---|---:|---:|---:|
| 平滑工况16→32→64段 | 14.195520 μm | 6.907143 μm | 1.03927 |
| 32段10→5→2.5μs | 1.464503 nm | 0.731988 nm | 1.00052 |
| 接触工况16→32→64段 | 39.808217 μm | 25.563117 μm | 0.63900 |

相邻差为中心线在时间及参考弧长上的RMS差，并非与精确PDE解的误差。完整开放工况实际显示约一阶时间收敛，不能套用无耗散Verlet的二阶标签。空间误差明显大于所测时间误差。能量—外功归一残差在10/5/2.5μs之间约保持 $2.88\times10^{-6}$；它小但没有继续随步长收缩，不能据此声称精确能量守恒。

| 纯扭转步长/μs | 保存时刻最大相对能量缺陷 | 保存时刻最大SO(3)正交缺陷 |
|---|---:|---:|
| 10 | 9.755345e-05 | 2.983e-13 |
| 5 | 2.516442e-05 | 5.712e-13 |
| 2.5 | 6.333167e-06 | 1.589e-12 |

纯扭转能量缺陷的相邻观察阶为 1.9548、1.9904。这是受限保守诊断，不能扩展为整个流—接触—反馈系统的辛性或KAM证明。扭转/多频激励日志中的通用tip_error列不作为跟踪性能指标。

### 6.9.3 接触与罚刚度敏感性

| 工况 | 段数 | 罚系数 | 最大求积点穿透/μm | 最大总法向力/μN |
|---|---:|---:|---:|---:|
| 不可行目标压力测试 | 16 | 2000 | 423.665 | 55.146 |
| 不可行目标压力测试 | 32 | 2000 | 525.282 | 54.093 |
| 不可行目标压力测试 | 64 | 2000 | 571.100 | 53.850 |
| 不可行目标压力测试 | 64 | 20000 | 213.155 | 75.355 |
| 不可行目标压力测试 | 64 | 200000 | 75.949 | 104.732 |

64段基础接触算例中，保存时刻接触耗散功率最大值为 0.000e+00 W，Coulomb上界数值超量最大为 2.118e-22 N；流体机械功率范围为 [-3.291e-07,6.605e-10] W。接触耗散与流体供能已被区分。提高罚刚度减小穿透，但未建立严格硬不穿透条件。

### 6.9.4 工程密度/耗散率敏感性

| 密度/(kg/m³) | 耗散率/s⁻¹ | 32段RMSE/mm |
|---:|---:|---:|
| 1200 | 2 | 0.128752 |
| 1800 | 2 | 0.153806 |
| 2400 | 2 | 0.191221 |
| 1800 | 1 | 0.149645 |
| 1800 | 4 | 0.176388 |

这些差异量化了缺少实测密度/耗散数据的影响，不把工程取值升级为实测材料参数。

### 6.9.5 完整线圈约束的最终可核查结果

最终连续电流支路的每线圈幅值最大 2 A，几乎处处的电流斜率最大 20 A/s，电流连接点不连续缺陷为 0.000e+00 A。999 次受约束分配全部收敛，无可行电流回退；归一化采样约束数值超量最大 7.559e-11。

在 1000 个控制检查时刻，实际杆节点场峰值 0.479452 mT、梯度范数峰值 0.02439634 T/m；分别低于5 mT、0.03 T/m。实际节点距精确圆导线最小 8.87754 mm。387个工作域采样点距导线最小5.87 mm；整个指定管状域到导线的保守几何距离下界4.49 mm。该几何界保证所定义管状域不包含线圈导线，但不把离散场幅值检查升级为连续空间全域场界。

ZOH支路只有相邻样本电流差商的20 A/s约束；其电流跳变不能具有有限连续时间导数。最终斜坡支路用连续分段线性电流替代ZOH，因而真正满足几乎处处的速率界。由于磁场和梯度关于电流线性、范数约束集合凸，两个可行电流端点间的整条线段在每一个固定空间采样点仍可行。这是对执行器采样场约束的明确推导，不是对机械积分器辛性的声明。

### 6.9.6 相同流量的Womersley改进

Womersley数为 4.53336537。4097点径向查表的壁面速度为零，截面流量积分最大绝对误差为 5.125e-14 m³/s；复形状插值最大相对误差 1.061e-07，独立径向有限差分代入直管谐波动量方程的相对残差 3.277e-07。中心振荡相对平均流量相位为 -0.304630 rad。

保持完全相同的流量波形和机械/控制参数后，中心线时空RMS变化为 2.774620 μm，尖端时间RMS位置变化为 4.943996 μm。该算例跟踪RMSE变化小，并不证明瞬时抛物线在其他频率、管径或目标下均充分准确。映射到弯管切向仍是局部近似，流体压力、附加质量和双向FSI仍未由此补齐。

### 6.9.7 计算环境与耗时解释

硬件报告为 AMD EPYC 9V74 80-Core Processor，x86_64；Python及依赖精确版本见每案environment.json。主套件、学习转移与Womersley按导入顺序在NumPy前设置OMP_NUM_THREADS=1，终局复查NumPy/SciPy OpenBLAS均为1线程。原始完整Biot–Savart脚本在设置OMP前导入NumPy，历史每次线程池大小未逐案记录，不能事后编造；相同导入顺序的终局复查为9/1线程，仅作环境诊断。最终受约束ZOH及连续斜坡显式固定两套BLAS均为1线程。

表内耗时包含当次初始化、必要JIT与并行任务竞争，不是受控硬件性能排行榜。首次受约束计算观察到17个进程线程，耗时130.749 s；随后固定BLAS单线程复算耗时65.351 s，跟踪结果在舍入范围一致。首次完整结果作为执行记录保留，未作为额外独立科学样本计数。完整说明见runtime_context.json。

本轮形成的是可复算的分层研究平台和多项明确的正、负结果。完整双向FSI、插入边界、患者/空间站数据校准、真实线圈硬件带宽热设计，以及带控制非光滑全系统的稳定性、结构保持与KAM定理仍需分别完成，不能由当前数值结果代替证明。

<!-- COMPUTED_RESULTS_END -->

## 6.10 计算结果图

![图6-1 曲管内三维中心线的时间截面。各轴采用不同显示比例；该主跟踪例为小幅运动。](/workspace/scratch/990e101b41bd/stage2/results/rod3d/figures/geometry_3d.png){width=6.2in}

![图6-2 同一12自由度前馈接口施加到32与64段杆。线性与精确低维ROM曲线接近，复网络在本例未优于它们。](/workspace/scratch/990e101b41bd/stage2/results/rod3d/figures/learned_feedforward_transfer.png){width=6.85in}

![图6-3 从局部场分配到完整线圈及采样管域约束。原点分配违反实际梯度界；连续电流分支保留了可行性与性能代价。](/workspace/scratch/990e101b41bd/stage2/results/rod3d/figures/full_coil_constraints.png){width=6.85in}

![图6-4 空间与时间细化。纵轴为相邻网格差，完整开放系统实测约一阶时间收敛。](/workspace/scratch/990e101b41bd/stage2/results/rod3d/figures/refinement.png){width=6.85in}



# 7 Birkhoff 生成函数 控制与收敛的统一推导

## 7.1 相容一形式与局部构造

在一个光滑的偶维机械相空间局部坐标域内，先确定实际向量场 $\dot z=f(z,t)$，包括真实质量导数、阻尼和所选择的控制。取一形式 $\theta=R_i(z,t)\,dz_i-B(z,t)\,dt$，定义

$$\mathcal K_{ij}=\partial_iR_j-\partial_jR_i,\qquad \mathcal K f=\nabla B+R_t.\qquad\text{(A1)}$$

这里 $R$ 是Pfaff一形式系数，不是三维姿态矩阵，后文用上下文区分。除 $K$ 反对称和 $\det K\ne0$ 外，还要求空间闭性及时间相容性：

$$d_z\Omega_t=0,\qquad \partial_t\mathcal K+(f\cdot\nabla)\mathcal K+(Df)^T\mathcal K+\mathcal K Df=0,\qquad\text{(A2)}$$

其中 $\Omega_t=\tfrac12K_{ij}\,dz_i\wedge dz_j$。A2等价于沿同一真实流保持 $D\Phi^TK(\Phi,t)D\Phi=K(z,t_0)$。它不等于保持固定欧氏体积，也不等于机械能守恒。

一般B材料提供的可用局部构造是解一形式输运方程

$$R_t+(DR)f+(Df)^TR=0,\qquad B=R^Tf.\qquad\text{(A3)}$$

因为 $\nabla B=(DR)^Tf+(Df)^TR$，代入即得A1。若初始 $dR_0$ 非退化，真实局部微分同胚的拉回保留非退化性。这个存在性说明有价值，但计算A3仍需输运方程或等价的流与变分计算；不能视为免费获得结构矩阵。

规范变换 $\widetilde R=R+\nabla\sigma$、$\widetilde B=B-\sigma_t$ 不改变A1。令 $\sigma_t=B-H$ 可令 $\widetilde B=H$，但没有减少构造 $R$ 和 $K$ 的难度，也不能消去近似输运的原场表示误差。后文实际Moser算例正好量化了这一点。

## 7.2 Theorem A 和 B 的可用衔接

按照Feng–Qin第15章Theorem3.5、4.1、4.4和4.5，生成坐标 $\alpha:(\widehat z,z)\mapsto(\widehat w,w)$ 必须满足端点二形式适配，而非仅为可逆变换。写 $D\alpha$ 的四个块为 $A_\alpha$、$B_\alpha$、$C_\alpha$、$D_\alpha$，有

$$D\alpha^T\mathbb J D\alpha=\operatorname{diag}(\mathcal K(\widehat z,t),-\mathcal K(z,t_0)).\qquad\text{(A4)}$$

若真实相流 $M=D_z\Phi$ 满足 $\det(C_\alpha M+D_\alpha)\ne0$，则生成图的Jacobian为

$$N=(A_\alpha M+B_\alpha)(C_\alpha M+D_\alpha)^{-1}=N^T.\qquad\text{(A5)}$$

局部存在 $\widehat w=\nabla_w\phi$；标量 $\phi$ 只确定到与 $w$ 无关的函数，须另给规范。初时 $M(t_0)=I$，所以初始横截条件为 $\det(C_\alpha+D_\alpha)\ne0$，初始生成梯度由对角端点图确定：$f_0(w)=\alpha_1(z,z,t_0,t_0)$，其中 $w=\alpha_2(z,z,t_0,t_0)$。一般图上 $f_0$ 不必为零，不能默认沿用某个中央图的初值。无需 $N$ 本身可逆，原稿把 $N(t_0)=0$ 与 $N$ 可逆并用的问题由此消除。固定初始端点，令 $X=f$，则

$$\partial_t\nabla_w\phi=(A_\alpha-NC_\alpha)X+\partial_t\alpha_1-N\partial_t\alpha_2.\qquad\text{(A6)}$$

解析时可按幂系数递推生成梯度 $f_j$：

$$f_{j+1}=\frac1{j+1}[h^j]\,\mathcal A\left(\sum_{r=0}^jh^rf_r,w,\sum_{r=0}^jh^rD_wf_r,t_0+h,t_0\right).\qquad\text{(A7)}$$

必须保持每个 $f_j$ 是梯度。截断后用Theorem4.5将 $\alpha_1=\sum_jh^jf_j(\alpha_2)$ 还原到端点变量，还须验证截断图的逆横截性。若 $D(\alpha^{-1})$ 的下排块为 $C^\alpha$、$D^\alpha$，$N_m$ 为截断梯度的Jacobian，则要求 $\det(C^\alpha N_m+D^\alpha)\ne0$；正确初值及解析性下可在足够小步长局部由连续性保证。仅在精确相流上检查A5的分母可逆，并未自动核验这一步。原稿的A／B不独立给出磁输入可实现性、非光滑接触上的解析性或KAM结论。一般变质量三维ROM已有Hamiltonian接口，但本轮尚未把A3—A7的完整一般推进算法接到该ROM；实际实现及误差检查见本章后半部分。

## 7.3 原36的矩阵推导和一般变质量形式

由F21，对 $z=(q,p)$ 直接写真实中点残差：

$$q_+-q=hM(\overline q,\overline t)^{-1}\overline p,\qquad\text{(A8)}$$

$$p_{+,i}-p_i=h[-\tfrac12\overline p^T(\partial_iM^{-1})\overline p-\partial_iV+Q_{{\mathrm{nc}},i}]_{(\overline q,\overline p,\overline t)}.\qquad\text{(A9)}$$

所有中点和未知量必须同时求解。对常 $M$、$K_s$、$C$，令 $Q_{\mathrm{nc}}=F-CM^{-1}p$，$V=q^TK_sq/2$。将 $q_+=q+(h/2)M^{-1}(p_++p)$ 代入动量中点，令

$$E_h=\tfrac{h^2}{4}K_sM^{-1}+\tfrac h2CM^{-1},$$

得到正确的原（36）推广：

$$p_+=(I+E_h)^{-1}[(I-E_h)p-hK_sq+hF_{1/2}],\quad q_+=q+\tfrac h2M^{-1}(p_++p).\qquad\text{(A10)}$$

逆矩阵从左乘，$K_sM^{-1}$ 和 $CM^{-1}$ 不可任意交换；只有单自由度才是一个标量分式。实际可解对称或一般线性系统，而不显式构造逆：

$$[M+\tfrac h2C+\tfrac{h^2}{4}K_s]\overline v=p-\tfrac h2K_sq+\tfrac h2F_{1/2},\quad q_+=q+h\overline v,\quad p_+=2M\overline v-p.\qquad\text{(A11)}$$

变质量／非线性情况下A10中的系数仍依赖未知中点，不能把它称作显式算法。应直接实现A8—A9的残差和Newton Jacobian，加入正确的磁反馈链式导数。

A8—A9是二阶数值方法；在无非保守力或力可吸收为势的正则分支，理想隐式映射保辛。阻尼振子即给反例：对于 $\dot z=Az$、$\operatorname{tr}A=-\gamma$，中点映射 $D\Psi=(I-hA/2)^{-1}(I+hA/2)$ 的行列式通常不等于1，也不精确等于 $\exp(-\gamma h)$。因而它既非通常辛映射，也不自动保持所选连续指数加权二形式。

## 7.4 高阶中央生成函数及非可分实现

对自治正则保守场 $f=J\nabla H$，精确流的端点差用端点平均 $m$ 表示为

$$z_+-z_-=hf(m)+\tfrac{h^3}{24}[D^2f[f,f]-2(Df)^2f](m)+O(h^5).\qquad\text{(A12)}$$

恒等式 $J\nabla(f^TH''f)=D^2f[f,f]-2(Df)^2f$ 给出

$$S_h=hH+\tfrac{h^3}{24}f^TH''f,\qquad z_+-z_-=J\nabla S_h(m).\qquad\text{(A13)}$$

这正是应恢复的原v10一般非可分Central4。Newton矩阵为 $I-\tfrac12JS_h''$，不是普通中点的 $I-hDf/2$。即使学习能量含全部混合动量项，A13仍成立，但需要相应三、四阶导数与解析分支；仅保留某个可分势能的专门导数实现不够。

令 $C_h=\tfrac12JS_h''$，隐式切线为 $(I-C_h)^{-1}(I+C_h)$，Hessian对称给出辛性；相应原始一形式差为全微分才能进一步用于exact symplectic映射的KAM。有限Newton容差的输出必须额外报告实施误差，不把该代数证明直接赋给一个未收敛迭代。

对于非自治合法规范图，应把图时间导数计入场，使用时变中点或合法Gauss阶段；不能把A13的自治式不加处理地代入任意阻尼、饱和、血流或接触场。

## 7.5 $U_k$ 的选择及物理实现判据

若 $U$ 表示动量方程的力，离散增量具有 $hU$ 的尺度；若 $U_k$ 被定义为状态增量，应明确它已包含步长。任意大小有界的附加增量没有保结构定理。

| 控制方案 | 可说明的目标 | 结构与磁实现限制 |
|---|---|---|
| 无控制 | 真实耗散和血流基准 | 不人为删除已有外部功率 |
| 精确阻尼补偿 | 补偿已知 $Cv$ | 是主动能量注入；其余流体／接触不补偿时不恢复保守系统 |
| 学习补偿 | 用学习误差模型修正力 | 残余误差须计入；含动量残差时速度是 $H_p$，不能偷换成固定 $M^{-1}p$ |
| 理想全驱动力 | 分离算法／模型误差 | 是理论上界对照；不等于磁硬件能够施加同一 $U$ |
| 一致势形控制 | 通过闭环磁势保留Hamiltonian分支 | 例如 $i_a$ $=i_{0a}-k_a(\phi_a-\phi_{\mathrm{ref},a})$，闭环势为 $-i_0\cdot\phi$ 加上 $\tfrac12\sum_a k_a(\phi_a-\phi_{\mathrm{ref},a})^2$ |
| 共点端口阻尼 | $y$ $=G_m^T\dot q$，$u$ $=-K_y y$，控制功率 $-y^TK_y y\le0$ | 给出被动耗散而非通常辛性；饱和和偏置须重新核查 |
| 轨迹前馈与反馈 | 实际跟踪、抗流与接触 | 非共点速度反馈可激发高频模态；本轮已经出现不合格长轨迹 |
| 采样保持与受限线圈 | 体现带宽、电流及场约束 | 闭环导数含输入对状态的导数；固定输入子步辛性不等于闭环辛性 |

在已知 $K$ 下，新增 $g=G_u u$ 仍保持同一 $K$ 的局部充分条件为 $Kg=\nabla W$，即所对应一形式恰当；任意反馈通常不满足。若重新构造闭环 $K_u$，则必须报告保持的是新 $K_u$，不能仍用无控制结构作结论。实磁力由固定电流磁势对 $q$ 的偏导得到；将反馈 $i(q)$ 直接代回原磁势再对全部 $q$ 求导会多出非物理项，除非重新构造上述一致闭环势。

## 7.6 三类误差分别证明

普通中点的状态增量残差 $r_k$ 满足离散稳定估计

$$ (1-hL/2)e_{k+1}\le(1+hL/2)e_k+Ch^3+\|r_k\|.\qquad\text{(A14)}$$

在共同紧域、稳定隐式分支和 $hL/2<1$ 条件下，得到固定 $T$ 的 $C_T(h^2+\eta_h/h)$。四阶合法格式把局部 $h^3$ 换成 $h^5$，才得到 $C_T(h^4+\eta_h/h)$。本轮残差注入和高维网格细化均实际检查了这类趋势。接触开闭、饱和、采样和非光滑事件可改变阶数，不能自动沿用光滑证明。

近似一形式若有 $e_B=K_af-\partial_tR_a-\nabla B_a$，则 $f_a-f=-K_a^{-1}e_B$，加入表示误差后

$$\|z_h-z\|\le C_T(h^p+\eta_h/h)+\kappa\varepsilon_B(e^{LT}-1)/L,\quad \|K_a^{-1}\|\le\kappa.\qquad\text{(A15)}$$

图匹配误差是另一个量。若 $D\widetilde\chi^TK_0D\widetilde\chi=K+E$，内部映射保 $K_0$，则外部结构缺陷为 $E_--D\widetilde\Psi^TE_+D\widetilde\Psi$，加上内部求解误差。A15里的表示残差与这里的图匹配残差不能相互替代。本轮16自由度Moser试验给出了结构缺陷约 $6.68\times10^{-16}$ 而原场误差约0.1096的实测例子。

进一步连接机器人时，还要加入ROM截断、学习、流体闭合、实际磁场、观测及采样误差，并使所有范数、时间区间和状态域一致。本轮尚未把这些有限试验误差提升为整个三维血管模型的统一误差界。下面保留全部可复现计算及其条件。


## 7.7 一般 Birkhoff 高维算法复算与误差审计

### 7.7.0 结论和本次边界

**本轮已经完成源码审阅、两包继承关系核验、四支现有实验入口复跑、8/16 自由度八组新计算，以及一般输运截断与数值 Moser 图的实际构造检查。没有把这些数学试验称作三维血管机器人验证，也没有把尚未实现的一般高维图推进器写成已完成。**

最重要的新结论是：**Birkhoff 表示误差与二形式结构误差必须分别验收。**在本轮 16 自由度一般跨块阻尼、非线性磁势试验中，一阶输运截断所构造的 Moser 图满足二形式匹配到 $6.68\times10^{-16}$，但对原场的表示残差仍为 $0.111422$，相应向量场误差为 $0.109619$。它精确对应的是近似场 $f_a$，不能因此称原场 $f$ 已准确求解。第7.7.7节给出推导、代码和实测值。

原（36）修正后的普通隐式中点在本轮全部光滑算例表现为二阶；自治、保守、正则分支的三阶中心生成项给四阶辛格式；时变图上采用合法的两阶段 Gauss 方法也可以在其额外条件下得到四阶，但这不等于把自治 Central4 公式直接套在一般耗散场上。高维一般非比例阻尼算例中，普通中点、阻尼分裂及一般 ODE Gauss 方法均不被声称精确保持指定的输运二形式。

主审查依据是 `stage2/notes/1025_stage1_detailed.md` 第 9–12 章和第 15 章的生成函数、Runge–Kutta、后向误差及变分离散核验；56 页版的 `analysis/report_birkhoff_control.md` 只作交叉核对。共同原稿内容已由根代理对 (2)/(3)/(4) 文件进行逐字节及 OMML 核对，本记录使用共同内容，**不替用户选择最终引用文件名**。

根代理另行完成的 12 自由度三维 Kirchhoff 应变 Ritz 学习 ROM、以及三维 Cosserat/血流/接触计算属于真实建模推进。本文件中的一般 Birkhoff 图尚未与该 12 自由度 ROM 接通；两者的结果必须分列。这项缺口不允许用本文件的已知点变换模型替代。

### 7.7.1 实际检查了哪些材料，融合改变了什么

#### 7.7.1.1 阅读与代码覆盖

本次完整检查了独立 B 包 480 行一般推导、217 行 `verify_general_birkhoff.py`、60 行 `verify_v10_special_case.py` 及说明和结果文件。对最新版完整阅读了 `general_birkhoff_experiments` 的 7 个 Python 文件：四个动力学/驱动核心共 679 行，三个结果生成和翻译核验脚本共 262 行；并完整检查 `framework_common.py` 与 `framework_experiments/run_all.py` 共 472 行。理论交叉核对覆盖 `structure.tex` 的几何、端点、矩阵和高阶部分、`controlled_analysis.tex` 全文及 `supp_general_birkhoff.tex` 全文。其余目录通过哈希/调用关系检查时，不把“目录或哈希检查”写成逐行阅读。

| 材料 | 字节级/调用级核验 | 数学和计算定位 |
|---|---|---|
| 独立 `birkhoff_supplied`，8 文件 | 与最新版 `provenance/material_B_original` 的 8 文件全部字节相同 | 原样保存的理论及两类合成验证，不是完整导管求解器 |
| 旧 `integration_older_copy2/v10_framework_20261028` | `framework_experiments` 的 5 个 Python 与最新版相同；`experiments` 的 6 个 Python 亦相同 | 旧的矩阵、中点、Central4、学习/控制等实现被继承 |
| 最新 `integration_latest/v10_birkhoff_20261028` | `general_birkhoff_experiments` 7 个 Python 为新增 | 新增 G1/G2 磁两模态方法对照、G3 已知线性共轭试验；未把一般输运 PDE 变成完整导管的通用数值解法 |

详细哈希和继承表见 `stage2/results/route_a/replay_and_inheritance_audit.json`。所有上游文件在复跑前后哈希相同；源文件只读，实际执行独立副本中的脚本。

#### 7.7.1.2 “已用于磁导管”必须分级表述

| 内容 | 原包实际使用情况 | 本轮继承方式 |
|---|---|---|
| 普通中点、比例阻尼加权中点 | 已用于有物理参数基准的两模态磁梁/导管模型 | 保留其模型、参数和维数限定，不说是三维血流接触模型 |
| 自治 Central4 | 用于同一磁势的保守目标分支；未用于一般含残余阻尼闭环 | 复跑并扩展到 8/16 自由度的自治正则试验 |
| 一般一形式输运、规范调整、Moser 图存在性 | 原 B 包和融合稿给出推导 | 推导可继承；本轮新增有限阶系数和 Moser 辅助积分的实际计算，但仍非完整通用推进器 |
| 原包的非比例阻尼“图表法” | 两自由度、已知非线性点变换共轭于常系数线性 $y'$ $=Ay$ | 原样复跑；扩展到 8/16 自由度，显式记录 `expm/sqrtm/Sylvester` 成本 |
| 原包的 G3 控制改善 | 理想、无约束、两维全驱动广义力 | 仅承认同一目标轨道上的合成控制结果，不能解释成磁硬件性能 |
| 任意高维 $R,$ $\mathcal K,$ $\chi$ 的低成本计算 | 未完成 | 本轮没有把理论普遍存在性冒充低成本算法 |
| 完整 CHNN、三维杆、流体、真实接触中的一般 Birkhoff 结构 | 原上述验证脚本未实现 | 与根代理的三维 ROM/学习结果分列，不能相互借证 |

### 7.7.2 原稿与详细审查报告的逐项修订/继承表

| 原稿位置 | 118 页报告应继承的判断 | B 包/最新版的修复 | 本轮核验与仍需限制 |
|---|---|---|---|
| 原（30）端点变换 | 代数有效；一般时变二形式还需拉回匹配 | 先变到 $Z$ $=\chi_t(z)$，再采用原稿中心/差分约定 | 保留原号和符号；新增高维实际图检查。任意可逆端点变换仍不够 |
| 原（31）逆变换 | 必须贯穿 $P$ $=-\overline p$；不可混用带帽量 | 联合端点逆、投影条件及 Newton 矩阵分别说明 | 不能把梯度 Jacobian $N$ 当成所需可逆矩阵；初始 $N$ $=0$ 不构成矛盾 |
| 原（32）时间导数 | 初始端固定；区分全导数与固定生成坐标的偏导数 | 一般图场包含 $\partial_t\chi_t$ $+D\chi_t f$ | 已知矩阵图保留 $\dot T T^{-1}$；忽略该项会是不同动力学 |
| 原（33）一阶梯度 | 有阻尼时原候选向量的混合偏导通常不对称；`o(2)` 无定义 | 在合法正则图中先定义标量 $-h\mathcal H$，再求梯度 | 不以“一个生成项”机械判一阶；完整时间中点法实际为二阶 |
| 原（34）增量关系 | 增量定义不能反向证明向量可积成标量 | 相容端点变换与单值标量一起使用 | 本轮普通中点是比较方法；除满足条件的分支外不赋予生成函数结论 |
| 原（35）变质量中点 | 保留每个 $\partial_{q_i}M^{-1}$ 和同一中点评价 | 原包一般机械方程保留几何惯性 | 本轮 8/16 自由度全惯性表达用独立复步梯度、Jacobian 及共轭恒等式核验，误差约 $10^{-15}$ |
| 原（36）消元 | 左乘矩阵解，顺序为 $CM^{-1},$ $K_sM^{-1}$，一般不能交换 | 矩阵版本与完整中点残差分列 | 扩展到 8/16 自由度非对易矩阵，两个一步矩阵一致到浮点精度；它们是同一方法，不是两种精度算法 |
| Theorem A | 闭、非退化二形式；端点拉回匹配；横截投影；局部域 | 一般图构造给完整匹配式；不用 $N^{-1}$ | 理论可继承；计算的近似图需另报告匹配缺陷，未知精确图不能当零成本输入 |
| Theorem B 和截断定理 | 系数下标/阶乘、固定 $w$ 的依赖须正确；还需要 Chapter 15 Theorem 4.5 | 明确解析、横截与梯度系数条件 | 仅有限阶光滑可作有限截断估计；不把形式无限级数称为收敛。普通中点二阶另证 |
| 原（36）之后高阶展开 | 自治中心生成函数的偶数幂为零；三次项产生四阶 | 正确 Central4 显式导数已编程 | 复跑旧两模态和新 8/16 自由度；时变/非保守分支不得照搬自治式 |
| $U_k$ 直接状态增量 | 小、有界、光滑均不能代替结构条件，增量需有步长尺度 | 磁广义力放在同一隐式闭环方程 | 新增两磁势端口的一致闭环与冻结电流对照；后者必须包含反馈链式导数 |
| 控制后保持原 $\mathcal K$ | 需 $\mathcal KGu$ $=\nabla W$；一般反馈可能改变结构 | 同结构条件与重建闭环 $\mathcal K_u$ 分开 | G3 原样复跑确实只保持新结构；新非比例阻尼试验没有冒认旧结构自动保持 |
| 固定时间收敛 | 同一实际闭环、稳定隐式分支、轨道留域，误差含 $\eta_h/h$ | 原包完整中点残差与误差分裂已正确 | 二阶需状态增量误差 $O(h^3)$，四阶需 $O(h^5)$；Gauss 阶段残差与最终状态残差分别标注 |
| KAM | 保结构、有限时间收敛、机械能、环面存在互不替代 | 原包保持条件性保守 KAM 分支 | 本轮不产生新的 KAM 证书；非比例耗散例、时变图序列、接触切换均不能由此直接调用 Shang |

#### 7.7.2.1 对第 11、15 章四阶公式的实质核对

令 $f=J\nabla H$，$m=(z_++z_-)/2$。精确流关于时间中点展开并消去该时间中点后有

$$z_+-z_-=hf(m)+\frac{h^3}{24}\left(D^2f(m)[f,f]-2Df(m)^2f(m)\right)+O(h^5).$$

微分恒等式

$$J\nabla\left(f^T H''f\right)=D^2f[f,f]-2Df^2f$$

给出正确的正号中心标量

$$S_h=hH+\frac{h^3}{24}f^TH''f,\qquad z_+-z_-=J\nabla S_h(m).$$

这对应原稿约定下 $\phi_h(Q,P)=-S_h(Q,-P)$。它是**用于消除中点截断误差的预修正**；普通中点的后向误差 Hamiltonian 首项却是

$$\widetilde H_h=H-\frac{h^2}{24}f^TH''f+O(h^4).$$

两者符号相反，所回答的问题不同。118 页报告第 11 章、15.1 的生成函数段及 15.2 的后向误差段是相容的。原书第 14 章把作用量量纲的 $\psi_h\sim-hH$ 直接塞进 $p\dot q-\psi_h$ 的做法仍不可继承；需要 $-\psi_h/h$，时间变分还要保留 $h\partial_hK_h$，不能借此声称任意两步变步长格式都具有四阶/精确物理能量。

本轮 Central4 的潜能包含完整余弦、四次项及非线性磁势反馈的全部导数。对于 $H=P^TM_0^{-1}P/2+V(Q)$，记 $v=M_0^{-1}P$、$g=\nabla V$、$A=V''$，实际使用的三次增量是

$$\frac{h^3}{24}\begin{pmatrix}2M_0^{-1}Av\\-V^{(3)}[v,v]-2AM_0^{-1}g\end{pmatrix}.$$

它的 Jacobian 又包含 $V^{(4)}$，在新程序中显式实现并用复步导数独立检查。没有仅把线性振子系数套到非线性磁势上。

### 7.7.3 原样复跑：对象、输入、时间和误差定义

#### 7.7.3.1 复跑规格

| 入口/组 | 初态与维数 | 时间、步长 | 比较对象、参考与输出 |
|---|---|---|---|
| B `verify_general_birkhoff.py` | $z_0$ $=(0.25,$ $-0.18,$ $0.03,$ $0.04)$；2 构型、4 相变量 | $T$ $=2$；$h$ $=0.2,$ $0.1,$ $0.05,$ $0.025$ | 无控制与受控各自真实场；普通中点 vs 指定矩阵图中点。已知共轭指数参考，原坐标 DOP853 复核 |
| B `verify_v10_special_case.py` | $(0.18,$ $0.16,$ $0.03,$ $-0.02)$；2/4 | $T$ $=5$；$h$ $=0.04,$ $0.02,$ $0.01,$ $0.005$ | **旧显示精度** $N$ $=\mathrm{diag}(1,$ $6.152117504)$、$d$ $=(0.225670773,$ $0.321798806)$、$\gamma$ $=\frac{0.55558524}{11.417287283}$；两个 DOP853 容差参考 |
| framework `matrix` | $n$ $=1$: $(.1,$ $0)$；$n$ $=2$: $(.1,$ $.06,$ $0,$ $.02)$；$n$ $=4$: $(.1,$ $.06,$ $.04,$ $.025,$ $0,$ $.02,$ $-.01,$ $.005)$ | $T$ $=4$；$h$ $=.08,$ $.04,$ $.02,$ $.01$ | 非对易常矩阵，$\gamma$ $=.2$；指数真流，原（36）矩阵一致性、二阶/四阶和结构；额外非比例 $C$ 仅做消元代数检查 |
| framework `closed` | $(.09,$ $.08,$ $.015,$ $-.01)$；2/4 | $T$ $=20$；$h$ $=.04,$ $.02,$ $.01,$ $.005,$ $.0025$ | 固定制造的识别误差 $\delta\beta$ $=.02,$ $\delta\gamma$ $=.01$，实际闭环与名义目标分开；保守 Central4 只用前四档 |
| framework `defect` | $(.1,$ $.02)$；1/2 | $T$ $=4$；$h$ $=.08,$ $.04,$ $.02,$ $.01$ | 人为增量残差 $r_k$ $=.01h^q(1,$ $0)$，$q$ $=1,$ $2,$ $3$；验证 $\eta/h$ 累积，不冒称 Newton 的实际误差 |
| framework `weighted` | $(.09,$ $.08,$ $.015,$ $-.01)$；2/4 | $T$ $=4$；$h$ $=.04,$ $.02,$ $.01,$ $.005$ | 植物场 $(\kappa,$ $\gamma)$ $=(1.2,$ $.05)$ 和固定误差场 $(1.02,$ $.01)$；普通/加权中点 |
| 新版 G1 | 同上；2/4 | $T$ $=4$；同上四档 | 新基准完整余弦势，普通、直接加权、独立规范图中点三者；已知系数是方法诊断输入 |
| 新版 G2 | 同上；2/4 | 同 G1 | 保守 $h_0$，前三法重合，再比较 Central4 |
| 新版 G3 | 同 B 一般例；2/4 | 同 B 一般例 | 同已知共轭、无控制/理想全驱动两组；补完整轨迹、旧/新结构、有限差分切线和冷/热成本 |

最新版磁参数为 $N=\mathrm{diag}(1,6.045857300068718)$、$d=(0.30722439332376256,0.4504263248454578)$、$\omega_0=7.840009161840092\,\mathrm{rad/s}$。其声明的比例阻尼系数不是测量值。不能把旧 B 特例的显示精度参数与这个新基准混算。全部更长参数、矩阵、单位和来源哈希保存在原副本 JSON，本轮没有改写。

误差分别保存终点欧氏范数、全网格最大欧氏范数和 RMS；观测阶按每一类误差单独计算。新脚本的结构指标是谱 2 范数 $\|D\Psi^T\mathcal K_+D\Psi-\mathcal K_-\|_2$，其切线为理想隐式映射在求解点的解析切线，另有实际复合程序的有限差分验证。有限容差 Newton 程序本身没有被称为精确辛映射。参考容差细化只是浮点检查，不是区间包络。

#### 7.7.3.2 复跑结果和复现程度

四个实际入口均成功，墙钟时间依次为 B 一般例 **2.193 秒**、B 特例 **1.018 秒**、framework 全四组 **11.568 秒**、最新版 G1/G2/G3 **16.877 秒**。这些入口耗时包含参考和诊断，不能与下面只计方法推进的冷启动时间混用。

共逐项比较 **9513 个非计时数值条目**。最大绝对差异是一个误差已约 $3.35\times10^{-11}$ 的单自由度 Central4 算例的观测阶相差 $1.98\times10^{-5}$，两者均约四阶；不是轨道误差相差 $1.98\times10^{-5}$。其余组的最大差异约 $10^{-10}$ 或更小，许多只是微小量的观测阶或有限差分差值。完整路径和值保存在审计 JSON。

| 最新版实际复跑，最细公共网格 | 方法 | 最大网格误差 | 观测阶 | 指定 $\mathcal K$ 缺陷 | 方法冷启动秒 |
|---|---|---:|---:|---:|---:|
| G1 植物场，$h$ $=.005$ | 普通中点 | $1.345330$ $\times10^{-4}$ | 1.999452 | $6.972315$ $\times10^{-8}$ | .052924 |
| 同一场 | 直接加权中点 | $1.344909$ $\times10^{-4}$ | 1.999400 | $8.882034$ $\times10^{-16}$ | .064628 |
| 同一场 | 独立规范图中点 | $1.344909$ $\times10^{-4}$ | 1.999400 | $6.712299$ $\times10^{-16}$ | .057459 |
| G2 保守 $h_0$，$h$ $=.005$ | 普通中点 | $1.484494$ $\times10^{-4}$ | 1.999404 | $3.330671$ $\times10^{-16}$ | .058686 |
| 同一场 | Central4 | $1.356384$ $\times10^{-8}$ | 3.999503 | $4.444337$ $\times10^{-16}$ | .129590 |
| G3 无控制，$h$ $=.025$ | 普通中点 | $5.257716$ $\times10^{-5}$ | 1.999533 | $2.917312$ $\times10^{-6}$ | .013635 |
| 同一场 | 矩阵图中点 | $5.121475$ $\times10^{-5}$ | 1.999329 | $3.858774$ $\times10^{-15}$ | .032513 |
| G3 受控，$h$ $=.025$ | 普通中点 | $6.606436$ $\times10^{-5}$ | 1.999357 | $8.382003$ $\times10^{-7}$ | .013600 |
| 同一场 | 矩阵图中点 | $6.625670$ $\times10^{-5}$ | 1.999278 | $3.152390$ $\times10^{-15}$ | .029863 |

G3 受控图保持新 $\mathcal K_u$，并不保持无控制结构；两者在指定 $t=1,z_0$ 处的谱范数差为 $0.212111$。相对同一受控目标的 RMS 从无控制 $0.0358130$ 到理想控制 $3.39772\times10^{-5}$，输入是无约束全驱动广义力，峰值范数 $0.0607119$；这些数值没有磁硬件性能含义。受控 G3 中图法的轨道误差甚至略大于普通中点，亦说明结构保持不保证每个网格误差更小。

### 7.7.4 新 8/16 自由度模型：确切定义与限制

#### 7.7.4.1 共同变质量机械结构

取 $n=8,16$，相空间维数为 $2n=16,32$。在全部新推进试验中

$$Q_i=q_i+a q_i^3+bq_{i-1}^2,\quad a=.15,\quad b=.07,$$

第一个分量不含前驱项。令 $D=D_qQ$、$P=D^{-T}p$，则 $\xi(q,p)=(Q,P)$ 是已声明的正则点提升。模型为

$$M(q)=D^TM_0D,\quad C(q)=D^TC_0D,\quad H(q,p)=\tfrac12P^TM_0^{-1}P+V(Q(q)).$$

该质量随构型变化且一般含非对角项。它由已知常质量度量拉回，所以**不是任意质量度量 $M(q)$ 的通解**；真实三维杆的质量不能未经检查就假定有这种平直化点变换。这里的“一般跨块”指阻尼及势耦合超出可分块加权条件，不意味着所有三维杆质量均已覆盖。

记 $W$ 的第 $i$ 列为 $6aq_i e_i+2be_{i+1}$（最后一列无第二项），$c=W^TP$、$u=M_0^{-1}P$、$v=D^{-1}u$。程序实际实现

$$\dot q=v,\qquad \dot p=D^T[-\nabla_QV-C_0u]+c\odot v.$$

后项正是完整几何惯性，绝非删掉的质量导数。由 $p=D^TP$ 直接微分得

$$\dot p=D^T\dot P+\dot D^TP,\qquad (\dot D^TP)_i=c_iv_i.$$

另一方面 $-\partial_{q_i}(P^TM_0^{-1}P/2)=P^T(\partial_{q_i}D)v=c_iv_i$，故与 Hamilton 方程完全一致。程序同时核查了这两种表达、物理场解析 Jacobian 的复步导数以及 $D\xi^TJD\xi=J$。

#### 7.7.4.2 两个非线性磁势端口和闭环势

取

$$\Phi_a(Q)=\cos(d_a^TQ+\theta_a),\quad V_{\mathrm{mag}}(Q,i)=-\sum_{a=1}^2i_a\Phi_a(Q).$$

固定电流的真实广义力是 $G(Q)i$，其中 $G=[\nabla\Phi_1,\nabla\Phi_2]$。选择可积反馈

$$i_a(Q)=i_{0a}-k_a[\Phi_a(Q)-\Phi_{{\mathrm{ref}},a}],$$

则

$$G(Q)i(Q)=-\nabla_QV_c(Q),\quad V_c=-\sum_a i_{0a}\Phi_a+\frac12\sum_a k_a(\Phi_a-\Phi_{{\mathrm{ref}},a})^2.$$

这是实际对固定输入磁势偏导得到的力与闭环势一致的特殊构造，不是把电流代回原磁势后错误地对全部函数求导。物理坐标输入矩阵为 $G_q=D^TG$，秩至多 2；8/16 模态广义力不能任意指定。程序逐点核对上述梯度恒等式，并记录两输入矩阵的奇异值和电流峰值。

固定参数为 $i_0=(.18,.14)$、$k=(.12,.09)$、$\theta=(.35,-.45)$、$\Phi_{\mathrm{ref}}=(.8,.85)$；另有 $V_0=Q^TK_sQ/2+.16\sum_iQ_i^4/4$。所有数值是无量纲、声明的数学测试值，未由三维杆姿态和真实线圈场标定。它们只是结构正确的磁势端口模型；真正接口须用三维杆的 $\Phi_a(q)=\int\mu_\ell\cdot b_a(r)\,ds$ 替换，再核秩、限幅和磁场约束。

#### 7.7.4.3 四组新算例

| 标识 | 质量、阻尼与势 | 已知结构与合法方法 | 未声称的内容 |
|---|---|---|---|
| `conservative` | 上述变质量，$C_0$ $=0$；完整非线性 $V_0$ $+V_c$ | 物理中点、正则点图中点、点图 Central4 均保标准二形式；前两者二阶、后者四阶 | 不是耗散血流模型，不能把此分支替代最终对象 |
| `block_weighted` | $M_0,$ $K_s,$ $V$ 分成两个组，组内可耦合；$C_0$ $=M_0\Gamma$，$\Gamma$ $=\mathrm{diag}(.08I,$ $.21I)$ | 非比例阻尼仍有可计算的分块指数图；加权中点二阶，时变规范图 Gauss4 四阶 | 一旦质量/磁势跨不同阻尼率的块耦合，该结构一般失效 |
| `generic_nonproportional` | 在分块基准中加入跨块 $C_0$、$K_s$ 的秩一耦合，两个磁势端口横跨全部模态 | 普通物理中点、正则点变换后的普通 ODE 中点、阻尼 Strang 分裂为二阶；一般 ODE Gauss4 为四阶 | 这些方法不被声明精确保持输运 $\mathcal K$；Gauss 的保辛结论不能套在非 Hamilton 场上 |
| `linear_known_chart` | 全非比例、非对易常 $M_0,$ $C_0,$ $K_s$，经非线性点提升形成变质量；关闭四次与磁势项 | 既有 B 包矩阵指数/主平方根/Sylvester 图扩维；图中点二阶且保指定 $\mathcal K$ | 已知线性共轭是测试输入，其结构构造利用精确矩阵指数，不是一般未知场的廉价算法 |

$M_0$ 基准对角元为 $1+.045i$，$K_s$ 为 $1+.11i$，两组内分别加 $.07\mathbf1\mathbf1^T/(n/2)$、$.09\mathbf1\mathbf1^T/(n/2)$。跨块及线性组的全部附加矩阵见每组 JSON `parameters`；源码给确定性构造，不依赖随机拟合。

所有组初态统一为

$$q_{i,0}=.12\cos(.7i),\qquad p_{i,0}=.04\sin(.9i+.1),\quad i=0,\ldots,n-1,$$

终时 $T=2$，主步长 $h=.2,.1,.05,.025$。磁反馈冻结组额外细化，见第7.7.6节。DOP853 在**原变质量坐标**中用两套容差独立参考：$(\mathrm{rtol},\mathrm{atol},h_{\max})=(10^{-11},10^{-13},.05)$ 与 $(2\times10^{-13},2\times10^{-15},.025)$。线性共轭组另由指数真流核对。新矩阵/磁势/几何推导没有替换这些参考。

### 7.7.5 新计算的结构、精度与成本

#### 7.7.5.1 分块加权结构为什么合法，跨块时为什么不能推广

在 `block_weighted` 的 $y=(Q,P)$ 坐标中，$M_0$ 与 $\Gamma$ 可交换，且每个势项只依赖一个等阻尼率块。令 $E(t)=e^{\Gamma t}$，则

$$\Pi=E(t)P,\qquad \mathcal K_y(t)=\begin{pmatrix}0&-E(t)\\E(t)&0\end{pmatrix}.$$

逐块定义

$$\mathcal H_c(Q,\Pi,t)=\sum_g\left[\tfrac12e^{-\gamma_gt}\Pi_g^TM_g^{-1}\Pi_g+e^{\gamma_gt}V_g(Q_g)\right].$$

其规范中点变回后等于 $S_{h/2}\circ\mathrm{MP}_H\circ S_{h/2}$，其中 $S_{h/2}(Q,P)=(Q,e^{-\Gamma h/2}P)$。最后经 $\xi^{-1}$ 返回物理变质量坐标，保持

$$\mathcal K_z(z,t)=D\xi(z)^T\mathcal K_y(t)D\xi(z).$$

新四阶对照是在同一明确的**非自治** $\mathcal H_c$ 上，用两阶段 Gauss 系数 $b_1=b_2=1/2$、$a_{11}=a_{22}=1/4$、$a_{12}=1/4-\sqrt3/6$、$a_{21}=1/4+\sqrt3/6$。阶段时间为 $t+c_ih$；满足 $b_ia_{ij}+b_ja_{ji}=b_ib_j$，所以固定时间片的规范映射保辛，回拉后保上述时变二形式，并在光滑稳定分支上四阶。这里没有声称已实现一般 Theorem B 的任意高阶系数递推。

代码中该分块指数特例可以每步移去绝对时间指数，依靠的是指数群性和不同阻尼块之间的可分性；不能把这种便宜实现推广成“一般图每步把初始二形式重置为 $-J$ 仍保持同一全局结构”。

若势横跨不同 $\gamma_g$ 块，$E\nabla V$ 的 Jacobian 一般不对称；若 $M_0$ 与 $\Gamma$ 不交换，动能也不满足此分块梯度构造。`generic_nonproportional` 故意破坏这些条件。该组的分裂法只利用可计算的动量衰减 $P\mapsto\exp(-hC_0M_0^{-1}/2)P$ 和保守子步，不能因此称为保持连续 Birkhoff 二形式。

#### 7.7.5.2 16 自由度主网格结果

以下全部取 $h=.025,T=2$。误差为物理相坐标的全网格最大欧氏误差。前三类已知结构及线性共轭类的 $\mathcal K$ 缺陷检查每个步骤；一般跨块类只检查起步、中间和末步的三个样本，表中加星号明确标注，不能称为全网格上界。

| 模型 | 方法 | 最大轨道误差 | 观测阶 | $\mathcal K$ 缺陷 | 冷启动秒 |
|---|---|---:|---:|---:|---:|
| 保守变质量 | 物理中点/原（36） | $8.287256$ $\times10^{-5}$ | 1.999201 | $8.884502$ $\times10^{-16}$ | .050959 |
| 同一场 | 正则点图中点 | $8.275566$ $\times10^{-5}$ | 1.999202 | $1.110229$ $\times10^{-15}$ | .030888 |
| 同一场 | 点图 Central4 | $7.704358$ $\times10^{-9}$ | 3.999387 | $1.110242$ $\times10^{-15}$ | .059507 |
| 分块非比例阻尼 | 物理中点/原（36） | $7.667935$ $\times10^{-5}$ | 1.999350 | $2.075617$ $\times10^{-6}$ | .053811 |
| 同一场 | 合法加权图中点 | $6.711364$ $\times10^{-5}$ | 1.999162 | $1.555208$ $\times10^{-15}$ | .034565 |
| 同一场 | 时变图 Gauss4 | $1.072807$ $\times10^{-9}$ | 3.999773 | $1.333032$ $\times10^{-15}$ | .075112 |
| 一般跨块阻尼/势 | 物理中点/原（36） | $9.879047$ $\times10^{-5}$ | 1.999324 | $2.829159$ $\times10^{-6}$* | .050609 |
| 同一场 | 点坐标 ODE 中点 | $9.882546$ $\times10^{-5}$ | 1.999325 | $2.816666$ $\times10^{-6}$* | .032932 |
| 同一场 | 阻尼分裂+中点 | $9.018572$ $\times10^{-5}$ | 1.999102 | $2.986422$ $\times10^{-7}$* | .043176 |
| 同一场 | 一般 ODE Gauss4 | $1.795071$ $\times10^{-9}$ | 3.999714 | $7.449379$ $\times10^{-11}$* | .087070 |
| 已知线性共轭 | 物理中点/原（36） | $7.726417$ $\times10^{-5}$ | 1.999309 | $1.305367$ $\times10^{-6}$ | .059515 |
| 同一场 | 矩阵图中点 | $7.169256$ $\times10^{-5}$ | 1.999231 | $2.132607$ $\times10^{-14}$ | .167058 |

一般跨块组的诊断 $\mathcal K(z,t)$ 在离散前已定义为真实连续场对初始 $-J$ 的逆流拉回。本轮用独立 DOP853 联合积分逆流及变分方程近似它，**不从离散轨迹反推二形式，不把该真流信息用于任何状态推进**。这项昂贵诊断的参考细化差在代表点为 $1.15\times10^{-15}$；它仍不是全域严格误差包络。一般 ODE Gauss4 的结构缺陷随精度提高而小，不等于精确结构保持。

8 自由度全部对应组也完成，原始 111 个方法—网格记录见 `extended_metrics.csv` 和八份 `extended_*dof.json`。所有初值、矩阵、输入、Newton 迭代数、最小奇异值、结构指标、残差坐标、参考和计时重复均随 JSON 保存。共同最细主网格轨迹在八份 NPZ 中；冻结反馈的额外网格误差在 JSON/CSV 中，不能把公共 NPZ 误称为额外最细网格轨迹。

#### 7.7.5.3 成本不能只报缓存后的推进

每个方法/网格做一次未计时库预热，然后三次测量，报告中位数。冷启动包含所有该方法必需的格点图、矩阵指数、平方根和线性求解准备；缓存推进单独列出。独立参考、理想切线和结构诊断对全部方法一致排除。代码设单 BLAS 线程。计时只是本实现、本机器的墙钟数据，不是跨机器复杂度定理。

16 自由度已知线性共轭例在 $h=.025,T=2$ 时共 80 步，矩阵图需要 **161 次 `expm`、161 次主平方根、80 次 Sylvester 求解**。其冷启动 $.167058$ 秒中，准备为 $.156844$ 秒，缓存推进约 $.010120$ 秒；普通物理中点冷启动 $.059515$ 秒。因此不能只拿图法 $.010120$ 秒与中点比较，然后说一般图法更快。更不能忽略这一例已知 $A$，本来就可以直接计算指数真流；它的价值是验证相容图和结构恒等式。

全部八组最终新计算入口用时 **49.813 秒**，另一般输运/Moser 检查 **6.981 秒**。这些总入口时间包含诊断与参考，和上表方法成本属于不同统计口径。

### 7.7.6 反馈电流采样保持：实际失败、细化和正确解释

本轮比较两种实现：一致计算闭环势 $V_c$ 的梯度，并在中点/相应 Gauss 阶段评价；或在每一步先取 $i_k=i(q_k)$，随后把该电流冻结到整步。后者每个**固定电流**子问题可以使用辛格式，但整个闭环导数还包含

$$D_z\Phi_h(z,i(z))=\partial_z\Phi_h+\partial_i\Phi_h\,D_zi.$$

程序对冻结组的切线显式加入这一项，并以实际复合程序的中心有限差分检查；没有用固定电流的条件切线冒充闭环切线。

| 16 自由度冻结电流，$T$ $=2$ | 最大轨道误差 | 本次减半观测阶 |
|---:|---:|---:|
| $h$ $=.05$ | $2.684713$ $\times10^{-4}$ | 1.995929 |
| $.025$ | $6.730852$ $\times10^{-5}$ | 1.995906 |
| $.0125$ | $1.698748$ $\times10^{-5}$ | 1.986317 |
| $.00625$ | $4.404603$ $\times10^{-6}$ | 1.947388 |
| $.003125$ | $1.247743$ $\times10^{-6}$ | 1.819692 |
| $.0015625$ | $4.481069$ $\times10^{-7}$ | 1.477406 |
| $.00078125$ | $2.145919$ $\times10^{-7}$ | 1.062247 |

在主网格 $.025$，冻结电流组相对所声明连续闭环二形式的缺陷为 $8.138298\times10^{-6}$；一致闭环加权中点只有 $1.555208\times10^{-15}$。对 8 自由度，细到 $.00625$ 已观察到 .982619 阶。

最初新批在 8 自由度冻结电流的四个主网格上得到最后 1.315518 阶，触发了预设的一阶渐近核验门槛。这是**前渐近误差混合**，不是 Newton 不收敛。保留 `extended_run.log` 的失败记录，随后仅为此实际不确定性补充网格，16 自由度进一步显示“前四档似二阶”的风险。未改初态、未调控制增益来制造期望阶数，也未删掉不利数据。最终 `extended_run_final.log` 和清单记录全部通过。

该比较的参考是同一光滑连续闭环，因此零阶保持误差一般降为一阶；若研究对象改成真正的离散采样系统，应重新指定该系统的参考与收敛定义，不能把此结果称为采样系统本身的求解失败。这里不设实际线圈带宽/饱和，没有因此得到工程控制认证。

### 7.7.7 一般输运与数值 Moser 的实做：结构残差小不代表原场准确

#### 7.7.7.1 完全不借真流的有限阶构造

对本轮一般跨块非比例阻尼、非线性磁势场 $f(z)$，取

$$R_0=(p,0),\quad R_1=-(DR_0)f-(Df)^TR_0.$$

本轮实际用解析场和 Jacobian 算出 $R_1$，再以复步核对其导数，构造

$$R_a(z,t)=R_0(z)+tR_1(z),\quad B_a=R_a^Tf,\quad K_a=K_0+tK_1,$$

$$K_1=dR_1=-(Df)^TK_0-K_0Df.$$

这是从固定原点 $t_0=0$ 截到一阶的输运构造。没有使用物理精确流、没有使用离散映射来选 $K_a$。

给定 $t$，对辅助参数 $\lambda\in[0,1]$ 解

$$[K_0+\lambda tK_1(z)]v_{\lambda,t}(z)=tR_1(z),\quad\frac{d\rho_{\lambda,t}}{d\lambda}=v_{\lambda,t}\circ\rho_{\lambda,t},\quad\chi_t=\rho_{1,t}^{-1}.$$

当插值二形式非退化且辅助轨迹留在域内，Cartan 公式给 $D\chi_t^TK_0D\chi_t=K_a$。本轮在每个检查点真实积分了此辅助 ODE及其逆；另用 $2n$ 个复步方向求图 Jacobian、一个时间复步求 $\partial_t\chi_t$，并做容差细化和逆复合检查。非退化性在所经过的辅助点上检查，**未把采样最小奇异值写成整个域的严格下界**。

#### 7.7.7.2 表示误差的明确推导

令 $DR$ 的行指标为一形式分量，故 $K=(DR)^T-DR$。有

$$\nabla B_a=(DR_a)^Tf+(Df)^TR_a.$$

于是

$$\begin{matrix}
e_B=K_af-\partial_tR_a-\nabla B_a\\
=-\bigl[(DR_a)f+R_1+(Df)^TR_a\bigr]\\
=-t\bigl[(DR_1)f+(Df)^TR_1\bigr].
\end{matrix}$$

所以它一般只有 $O(t)$，不是零。近似结构真实表示的场是

$$f_a=K_a^{-1}(\nabla B_a+\partial_tR_a)=f-K_a^{-1}e_B,$$

从而

$$\|f_a-f\|\le\|K_a^{-1}\|\,\|e_B\|.$$

**Moser 图的匹配等式是对 $K_a$ 成立；若用它构造保结构算法，所对应的是 $f_a$。**即使时间步长趋于零，固定 $R_a$ 的表示误差也不会随之消失。这正是 118 页审查与新整合稿所要求的误差分离，现在已经实际测量。

规范调整也不能消去这一误差：令 $\partial_t\sigma=B_a-H$、$\widetilde R_a=R_a+\nabla\sigma$、$\widetilde B_a=H$，则 $K_a$ 与 $\nabla B_a+\partial_tR_a$ 都不变，故 $e_B$ 原样保留。允许写 $B=H$ 与准确表示原场是不同条件。

#### 7.7.7.3 实测值

以下固定 $z=z_0$、$t=.1$，不是全轨迹误差或全域上界。

| 项目 | 8 自由度 | 16 自由度 |
|---|---:|---:|
| $\|e_B\|_2$ | .0774246391 | .1114222310 |
| $\|f_a-f\|_2$ | .0761358990 | .1096190274 |
| $\|K_a^{-1}\|_2\|e_B\|_2$ | .0768102110 | .1105383613 |
| 图二形式匹配谱范数 | $2.473826$ $\times10^{-16}$ | $6.680373$ $\times10^{-16}$ |
| 辅助图逆复合误差 | $9.842550$ $\times10^{-17}$ | $1.115799$ $\times10^{-16}$ |
| 图积分容差细化差 | $6.270252$ $\times10^{-17}$ | $1.045632$ $\times10^{-16}$ |
| 单点图、导数及复核耗时 | .526271 秒 | 1.302746 秒 |

在 $t=.2,.1,.05,.025$，表示残差随 $t$ 减半严格约减半；图匹配缺陷一直在舍入量级。8/16 自由度的 $K_1$ 闭性最大分量残差分别约 $2.87\times10^{-17}$、$4.30\times10^{-17}$。这些是浮点微分/积分核验，不是区间证书。

单次辅助图积分用了 74 次场/导数计算。16 自由度的 Jacobian 另需 32 次方向积分，时间敏感度另一次；逐点成本还含逆图和容差复核，不含已经预计算的 $R_1,DR_1$ 的公共一次性成本。全脚本 6.981 秒包含这些预计算。**没有在此基础上继续声称已完成一般 $f$ 的低成本、高阶 Birkhoff 时间推进。**下一步需要更高输运截断或可控近似、统一域误差、图与逆的稳定条件，以及把它们真正纳入每步求解成本。

### 7.7.8 收敛与结构可以证明到什么程度

#### 7.7.8.1 普通中点及真实闭环

对同一光滑场，完整增量残差 $r_k$ 满足

$$\left(1-\frac{hL}{2}\right)e_{k+1}\le\left(1+\frac{hL}{2}\right)e_k+Ch^3+\|r_k\|.$$

轨道/隐式分支留在共同域，且 $hL/2$ 被一个小于 1 的常数控制时，固定 $T$ 给

$$\max_{kh\le T}e_k\le C_T(e_0+h^2+\eta_h/h).$$

四阶 Central4 或合法 Gauss4 需要相应五阶局部余项、阶段稳定性和高阶导数界，才有 $C_T(e_0+h^4+\eta_h/h)$ 形式。Gauss 的代码报告的是两阶段增量残差；要进入最终状态误差界需经阶段逆 Jacobian 和输出导数转换，不能直接与物理坐标中点的数值残差相比。新 JSON 已分别命名残差坐标及未知量维数。

Newton 满足指定小残差、观测到二/四阶和样本最小奇异值为正，都没有替代上述统一域假设。所有本轮试验光滑，没有接触开启、库仑粘滑、饱和、约束奇异或事件降秩；这些情况需另行理论和实验。

#### 7.7.8.2 近似结构和近似图

若在共同域已有统一 $\|K_a^{-1}\|\le\kappa$、$\|e_B\|\le\epsilon_B$，则相同初值下

$$\|z(t)-z_a(t)\|\le\kappa\epsilon_B\frac{e^{Lt}-1}{L}.$$

若图方法为二阶且有统一稳定性，总误差可写为

$$\max_k\|z_k-z(t_k)\|\le C_T(h^2+\eta_h/h)+\kappa\epsilon_B\frac{e^{LT}-1}{L}.$$

保持联合二阶需让结构表示误差至少随 $h^2$ 缩小，状态每步实施误差随 $h^3$ 缩小，并控制图的逆和导数。四阶须相应提高条件，不能仅把时间积分器换成四阶。

若近似图满足

$$D\widetilde\chi_t^TK_0D\widetilde\chi_t=K_t+E_t,$$

而内部理想映射保 $K_0$，则外部图的结构缺陷为

$$D\widetilde\Psi^TK_+D\widetilde\Psi-K_-=E_--D\widetilde\Psi^TE_+D\widetilde\Psi,$$

还要叠加内部求解与切线计算误差。这与上一条动力学误差界是两件不同的事；第7.7.7节就是实际证据。

#### 7.7.8.3 KAM 的本轮结论

本轮不把耗散/时变图的局部存在性、机器精度的二形式缺陷、Gauss4 的四阶、低维磁场解码或一次长轨迹图形当作 KAM 认证。经典离散 KAM 仍需对选定固定/周期精确辛映射建立解析域、可积或正规形骨架、非退化、全整数与步长非共振，以及定量小度。三维模型的适用域和控制目标先由真实动力学/约束决定，不为套定理而永久消去血流与接触。

### 7.7.9 失败、未覆盖处和下一步接口

1. 原样四入口没有复跑失败；保留了源码、参数和参考的版本区别。
2. 新批最初对冻结控制的渐近阶门槛失败，已保留日志并用额外细网格澄清；没有换初态或调参数掩盖。
3. 一阶输运的原场表示误差明显不小。它不是程序故障，而是理论截断的实际限制；本轮不把该图当作原场的完成态求解器。
4. 所有新高维时间推进模型都声明了已知点提升；它不能覆盖任意三维杆的质量几何。
5. `generic_nonproportional` 的精确输运结构只作有限样本诊断，其计算用了独立逆流变分积分，绝非低成本已知输入。
6. 本轮两磁势端口没有真实线圈标定、硬件电流/梯度/发热约束，也没有在 8/16 维上宣称任意模态力可实现。
7. 新 12 自由度三维 Kirchhoff ROM 尚未接上一般 Birkhoff 图。所需接口为可导的 $H(q,p,t)$、完整非保守场及 Jacobian、磁端口 $\Phi_a/G_a$、有效光滑域、初始状态和量纲；然后先做 $e_B$ 与图匹配的独立验收，再做完整推进/控制比较。
   若采用局部输运展开并重启，须传递上一时片的一形式/二形式，或证明重启之间的相容转换；不能每步都任意重置 $R_0=(p,0)$ 而宣称保持原来的全局 $K(z,t)$。
8. 没有跨接触/摩擦事件、高维热变量退化结构、全域误差包络、长期稳定性或 KAM 新证明。不能用本轮可复现的数学算例替代这些目标。

### 7.7.10 复现入口与交付文件

核心脚本均在 `stage2/program/route_a/`，独立结果均在 `stage2/results/route_a/`。建议顺序为：

```bash
stage2/venvs/v10_baseline/bin/python stage2/program/route_a/replay_supplied.py
stage2/venvs/v10_baseline/bin/python stage2/program/route_a/run_extended.py
stage2/venvs/v10_baseline/bin/python stage2/program/route_a/transport_moser_check.py
python stage2/program/route_a/build_summary.py
python stage2/program/route_a/plot_results.py
```

动力学运行环境为 Python 3.12.14、NumPy 1.26.4、SciPy 1.13.1；原样 B 脚本另使用 SymPy 1.13.3。画图程序只读已完成 JSON，不再执行动力学。计算和图均未覆盖上游材料。

重要结果入口：

- `supplied_replay_manifest.json`、`replay_*.log`：原样入口、耗时、源文件保全。
- `replay_and_inheritance_audit.json`：9513 个数值条目的对比和版本继承。
- `original36_linear_identity.json`：8/16 维非对易矩阵消元，以及单自由度阻尼面积反例。
- 八份 `extended_*dof.json`、八份同名 NPZ、`extended_metrics.csv`：完整新实验。
- `extended_run_final.log`、`extended_run_manifest_all.json`：成功批次及所用动力学代码哈希；早期失败日志保留。
- `transport_moser_results.json`、`transport_moser.log`：实际一般场系数与辅助图、表示误差和成本。
- `route_a_16dof_convergence.png/.pdf`、`route_a_moser_error_separation.png/.pdf`：科学绘图，数据来自上述 JSON，均已检查图像布局。

主要数学来源仍是所给原稿、118 页详细审查、Feng–Qin 第 5/7/15 章，以及 B 包的明示推导；本文件没有把未读取的新论文、未知临床参数或未运行的机器人结果写成证据。

![图7-1 16自由度合成变质量模型中的实测误差与收敛阶。各方法适用的二形式和阻尼条件见本节正文。](/workspace/scratch/990e101b41bd/stage2/results/route_a/route_a_16dof_convergence.png){width=6.85in}

![图7-2 一般近似输运与Moser图中的两种误差。图匹配达到机器精度，并不意味着近似一形式准确表示原向量场。](/workspace/scratch/990e101b41bd/stage2/results/route_a/route_a_moser_error_separation.png){width=6.85in}

# 8 新三维模型的学习路线与独立 KAM 边界

## 8.1 从三维构形到正则学习坐标

本轮新建12配置自由度、24相空间维数的Kirchhoff应变Ritz族，四个基函数分别描述两个弯曲方向和扭转。它与完整Cosserat程序共享长度、半径、材料、远端磁化段和8分量磁接口。它没有删去一个弯曲方向或扭转，也没有将整根杆固定为两个动力学模态。

由几何嵌入独立装配 $M(q)$，在直杆轴向偏场平衡点计算 $M_0$、$K_0$ 并解 $K_0\phi_j=\omega_j^2M_0\phi_j$、$\Phi^TM_0\Phi=I$。以 $E_0=\mu_{\mathrm{total}}B_0$、$\omega_0=\min_j\omega_j$ 定义

$$S_q=\Phi\operatorname{diag}\sqrt{\frac{E_0}{\omega_0\omega_j}},\qquad S_p=M_0\Phi\operatorname{diag}\sqrt{\frac{E_0\omega_j}{\omega_0}},\qquad\text{(L1)}$$

$$q=S_qQ,\quad p=S_pP,\quad \tau=\omega_0t,\quad S_q^TS_p=(E_0/\omega_0)I.\qquad\text{(L2)}$$

因此这是一组带共同作用量尺度的正则变量，缩放后的Hamilton方程为 $Q'=\partial_Ph$、$P'=-\partial_Qh$。定义 $\nu_j=\omega_j/\omega_0$，则 $h_2=\tfrac12\sum_j\nu_j(Q_j^2+P_j^2)$。实际非线性能量使用完整 $M(q)^{-1}$、三维姿态和磁势，没有将动能固定为 $h_2$。

本轮 $E_0=3.62\times10^{-7}\,\mathrm{J}$，$\omega_0$ 约 $4.45763\,\mathrm{rad/s}$。空间积分20格的最低频率为4.45763、4.45763、27.69420、27.69420、79.78329、$79.78329\,\mathrm{rad/s}$；后续仍含高阶弯曲与扭转，总共12个频率。规范缩放残差约 $5.55\times10^{-21}$，原点线性Hamiltonian Hessian相对残差约 $2.27\times10^{-15}$。空间积分从20增加到40，与80格相比的质量矩阵相对差从约1.105%降到0.222%；这不是12基函数截断误差的上界。

## 8.2 完整可训练复网络和简化残差对照

网络输入先作独立统计归一化 $x=Dz$，其中 $z=(Q,P)$、$D_j=\sqrt{\nu_j}/a$。这个 $x$ 不是新的正则坐标。复输入 $\xi=(x_Q+ix_P)/\sqrt2$，显式同时输入 $\xi$ 与共轭 $\overline\xi$；网络最终输出实数能量，再在 $z$ 坐标中使用Hamilton方程。

对照设置如下。全部标签来自同一个12自由度三维ROM在完整相空间的独立随机点，不来自患者、传感器或完整Cosserat杆真值。相同训练4096、验证512、测试1024、域外512个样本；主域 $\lvert x_j\rvert\le1$，域外扩大到1.5。随机种子和数据SHA随包保存。

| 模型 | 实际可训练内容 | 物理／函数类限制 |
|---|---|---|
| 线性先验 $h_2$ | 无训练参数 | 不包含变质量耦合和非线性势 |
| 简化解析残差 | 48个实系数，最小二乘拟合 $q^3$、$q^4$、$q^2p^2$ 及相邻 $q^2q^2$ 特征 | 非完整四阶函数类；大量跨模态项缺失 |
| 初次完整复网络 | 两个48宽复隐藏层，7202个实参数 | 采用holomorphic $\tanh(z)$，只消能量常数，无固定线性化；实际失败对照保留 |
| 修正完整复网络 | 两个48宽复隐藏层，7104个实参数；全部复权重训练 | split tanh、三次门控、动量偶对称、实能量；仍不保证机械动能凸性 |
| 机械结构复网络 | 独立追加，具体结果见其记录 | $C(Q)$ $=L(Q)L(Q)^T$ 确保动量Hessian正定，保持全部12自由度 |

修正网络的激活是 $\sigma(w)=\tanh(\operatorname{Re}w)+i\tanh(\operatorname{Im}w)$。它是 $(w,\overline w)$ 的实解析函数；没有声称它对 $w$ 单独全纯。令 $A$ 是零偏置复线性层，另一个复网络产生 $c(x)$，读出 $\operatorname{Re}\sum_j a_j(x)^3c_j(x)$，再取 $P$ 和 $-P$ 的平均。三次门控使残差在原点的0、1、2阶jet精确为零，因此不会移动已知平衡或线性谱；动量偶对称匹配固定磁场下该机械模型的 $p$ 偶性。

损失为归一化能量梯度匹配加0.15倍能量匹配；训练索引0—6000，共6001次Adam更新，批量256。按验证集每200个索引选择检查点，未按测试误差或高维杆跟踪结果选择。每种子约52—55秒，CPU单线程。$\mathrm{amp}=0.08$ 为主域，另以 $\mathrm{amp}=0.35$ 作较大幅压力测试。

主域的归一化输入梯度相对 $L^2$ 误差：线性先验78.94%，48特征解析残差71.21%，修正复网络三个种子分别约1.683%、1.604%、1.653%。转换回真正正则向量场 $J\nabla_z h$，独立复核结果约1.75%—1.91%。这些误差都只是测试分布下的均方指标，不是解析域上界。不同模型参数量不同，因此本实验支持“该可训练函数类能拟合所给变质量数据”，不支持“复数表示本身优于实数网络”。原v10匹配函数类的实／复训练结果实际上相同。

## 8.3 必须保留的失败和适用域

初次复tanh网络在主训练应力域内能降低误差，但域外产生导数尖峰，三个种子的归一化梯度相对误差约4.0—12.1倍，并产生非零平衡梯度。它的检查点、数据、日志和原始实现保存为 `learning_initial_meromorphic`，未被成功结果覆盖。split tanh和门控的修改针对这两个实际失败，不是为隐藏失败换一组数据。

修正网络依然有机械结构问题。独立检查12个测试点和12个域外点的 $H_{PP}$：$\mathrm{amp}=0.08$ 的测试样本均正，域外分别有2、2、3个负最小特征值；$\mathrm{amp}=0.35$ 压力域的测试样本已有9、10、10个非正定反例。因而不能仅写“正定性未认证”：在这些采样域内，正动量Hessian的全域断言已经被反例否定。有限测试点全正也不是全域保证。

当前磁前馈没有反解学习模型的 $H_P$，也没有将其非正定 $H_{PP}$ 解释成物理负质量。它使用已知几何 $M(q)$ 构造参考动量，只用学习 $H_Q$ 作广义力补偿。这是一项明确受限、实际运行的控制比较。追加的Cholesky型复网络则直接修复机械能类：

$$h_\theta=\tfrac12a^2x_P^TC_\theta(x_Q)x_P+\tfrac12a^2|x_Q|^2+V_{\theta,\mathrm{res}}(x_Q),\quad C_\theta=L_\theta L_\theta^T,\qquad\text{(L3)}$$

$L$ 为下三角且对角为指数，故在有限输出处 $C_\theta$ 严格正定。质量读出减去原点读出并固定对角使 $C_\theta(0)=I$；势残差的三次门控保留已知线性化。该架构限制的是机械Hamiltonian类，不是空间维数，也不把任意非可分Hamiltonian全部等同于机械杆。其实际拟合代价及误差见独立追加实验，不能预先宣称精度一定更高。

## 8.4 从学得梯度到实际磁输入

参考轨迹与Cosserat程序采用相同的0.3秒三次启动和两个横向周期目标；用全部弯曲基函数求满足尖端横向位置的最小线性能量构形，再作几何校正。参考扭转为零，杆的三维扭转自由度仍然参与动力学。已知 $M(q)$ 给出 $p_{\mathrm{ref}}=M\dot q_{\mathrm{ref}}$，离散求其时间导数。各模型产生

$$U_{\mathrm{req}}=P_{\mathrm{ref}}'+(h_{\mathrm{model}})_Q(Q_{\mathrm{ref}},P_{\mathrm{ref}})+(\alpha_s/\omega_0)P_{\mathrm{ref}}.\qquad\text{(L4)}$$

这里 $\alpha_s=2\,\mathrm{s}^{-1}$ 是本轮机械质量比例损耗的物理时间系数，故无量纲时间 $\tau$ 下应除以 $\omega_0$ 一次。它不与原v10中已经无量纲化的阻尼 $\gamma$ 混用。

分配使用全部12条方程和相同端口矩阵，权重 $1/\sqrt\nu$，磁输入二次正则 $1\times10^{-5}$，保持训练时的 $B_z=0.5\,\mathrm{mT}$；随后施加场幅值和梯度约束。最高归一化参考坐标1.093，略超训练盒，明确标为轻微外推。真实ROM、线性先验、解析残差、复网络四种前馈都通过同一接口，加相同位置反馈，实际进入32／64段完整杆。

这一比较的误差包含学习、ROM截断、未在前馈中补偿的血流／接触、磁分配、采样和时间离散。它不是纯学习误差实验。真实ROM前馈仍有约18.5%加权力残差，因为磁输入无法精确实现所指定的任意12维力；把理想 $U$ 直接注入全部坐标会得到另一项实验，不能代替真实磁驱动结果。

分配残差也必须使用共同真值比较。四种输入对各自所请求力的相对残差约为18.5283%、31.1104%、18.6869%、18.5284%；以同一真实ROM所需力为分母及目标，依次变成18.5284%、56.0190%、18.5109%、18.5284%。解析残差的31.1%不能被解释为相对真实所需力的误差。该缓慢小幅参考上，线性先验所需力与真实ROM的相对差仅0.000638%，复网络约1.195%，解析残差约74.03%；因此该跟踪任务并不提供神经网络优于线性先验的证据。32／64段杆的实际跟踪结果与这一限制相符。

## 8.5 新三维 KAM 必须经过的数学步骤

圆截面各向同性与轴向偏场产生四组1:1弯曲频率。以最前一对为例，$k=(1,-1,0,\ldots,0)$ 满足 $k\cdot\omega=0$。故原v10依靠非零低阶同调除数消去全部非共振项的算法不能直接使用；用舍入误差把相同频率拆开不具有物理或数学依据。

可行的下一步有两类，均需新的计算。保持轴向对称时，构造共振正规形、保留共振项并视条件作动量约化，研究非退化约化分支的环面。采用真实各向异性截面、磁化分布或偏场方向时，先根据实验确定破对称模型，再重算平衡、频谱、正规形、扭转和余项。两者都没有在本轮被替换成旧两频率证书。

连续KAM的候选对象必须是明确的保守Hamiltonian或适用定理覆盖的受迫／耗散结构。需要固定复解析域、有效的Cauchy导数界、频率全整数非共振条件、扭转下界、正规形及学习误差的同域范数。本轮随机测试误差和轨迹FFT不给这些界。原v10的512-bit证书重跑通过，证明对象仍是其旧冻结两模态保守能量，未证明新三维系统。[R3]

若选择Shang解析小扭转映射版本，离散KAM还需要目标映射的exact symplectic性质、统一解析隐式分支、周期生成扰动、指定频率域及其边界裕度、相应扭转非退化条件，并须对全部整数向量排除步长共振：

$$|e^{ihk\cdot\omega}-1|\ge h\gamma_D|k|^{-\tau_D},\quad k\in\mathbb Z^n,\quad k\ne0,\quad \tau_D>n+1.\qquad\text{(L5)}$$

更具体地，Shang 1999 Theorem 2的所选解析版本采用 $2\pi$ 周期角和全局周期生成扰动 $P_h$：

$$\widehat I=I-h\partial_\theta P_h(\widehat I,\theta),\qquad\widehat\theta=\theta+h\omega(\widehat I)+h\partial_{\widehat I}P_h.\qquad\text{(L5a)}$$

要求 $H_0(I)$ 在指定复域解析，$\omega=\nabla H_0$，频率导数满足 $\vartheta\lvert dI\rvert\le\lvert d\omega\rvert\le\Theta\lvert dI\rvert$ 且 $0<\vartheta\le\Theta$；$0<\gamma_D\le\min(1,r\Theta/2)$，保留频率距频率域边界至少 $2\gamma_D$。小量须满足

$$\|P_h\|_{r_0,\rho_0}\le\delta_0\gamma_D^2\vartheta^2\Theta^{-3}.\qquad\text{(L5b)}$$

$\delta_0$ 依赖所选定理的维数、指数、解析域和带宽，不是本轮已经得到的机器人阈值。测度结论还要求频率域的type-D等几何条件。上述条件来自已核读原文及Feng–Qin第13章Theorem2.4、原（2.38）、（2.40）；本轮没有为新三维系统完成这些数值常数。[R5，R6]

连续Diophantine条件不自动推出固定 $h$ 上的L5；$\tau_D$ 的不等式这里按所选定理版本列出，不宣称它是所有映射KAM定理的最优必要条件。若已经合法构造正规形及解析生成图，并限定对象为理想的exact-symplectic隐式映射，方向A的规范化生成扰动预算才可示意写为

$$\varepsilon_A\le\varepsilon_{\mathrm{model}}+\varepsilon_{\mathrm{learn}}+\varepsilon_{\mathrm{control}}+C h^p.\qquad\text{(L6)}$$

各项须对应同一解析exact-symplectic类内的生成扰动，采用同域同范数并连同定理常数计算，不能直接把若干测试RMSE相加代替。一般阻尼、饱和反馈和接触也不能仅作为一个小数 $\varepsilon_{\mathrm{control}}$ 放入该定理。求解器容差和近似图通常造成非辛缺陷；只有另证其所定义映射仍属于上述解析exact-symplectic类，才能再以 $\varepsilon_{\mathrm{solve}}$、$\varepsilon_{\mathrm{chart}}$ 形式计入生成扰动，否则只进入数值轨迹／结构误差报告，不给出该实际有限精度映射的KAM结论。方向B的连续保守模型预算不应混入数值积分项 $h^p$；实现跟踪时的受迫耗散误差另行估计，不能据跟踪成功反推KAM存在。



## 8.6 冻结模型后的新样本确认

### 8.6.1 冻结顺序与范围

2026-10-29，本轮在保持现有修正版网络、训练参数及checkpoint不变的前提下，增加了独立确认集。新增入口是 `stage2/program/learning/run_confirmation.py`，源文件本身、训练时源码快照、ROM源码、共享配置、全部6份复网络checkpoint、两组48特征系数、各自模态矩阵和旧摘要，均先复制并计算SHA。

`stage2/results/learning_confirmation/freeze_manifest.json` 在 **02:34:00.845711 UTC** 写入，早于任何新确认数据生成；其SHA-256为：

`b8587d4e2b28d0c28fa8096dfd80c2de302100e2deb6f4c74df7906b27b64c03`

随后使用唯一新采样种子 **20261030**，按 main/test → main/OOD → stress/test → stress/OOD 的固定顺序生成数据。幅值0.08和0.35各有2048个域内样本、1024个扩大域样本；输入分别均匀分布于24维 $[-1,1]^{24}$ 与 $[-1.5,1.5]^{24}$。标签来自相同的12自由度变质量Kirchhoff ROM。没有重训、调架构、改超参数或按确认误差选择checkpoint；三种子1025、1026、1027全部评估。

每组与旧train/validation/test/OOD的精确行交集均为0，新test与新OOD也无重复。旧结果文件没有覆盖，`evaluation_status.json` 明确将它们保留为开发期探索性评估。

### 8.6.2 数据与运行身份

| 项目 | 文件与身份 |
|---|---|
| 主确认数据 | `results/learning_confirmation/main/confirmation_data.npz`；SHA `6c8bceb1a6a67a59b4c9b72eddf6b455512f21897014b119d462659a32980602` |
| stress确认数据 | `results/learning_confirmation/stress/confirmation_data.npz`；SHA `e80ec3917f0f6345338f1d7d6eb1655606dde4ebc187c84c0bad8bb26cce19c4` |
| 主结果 | `results/learning_confirmation/main/confirmation_summary.json` |
| stress结果 | `results/learning_confirmation/stress/confirmation_summary.json` |
| 冻结权重及来源 | `results/learning_confirmation/frozen/`，逐文件身份在 `freeze_manifest.json` |
| 环境与命令 | `results/learning_confirmation/run_record.json` |
| 完成记录 | `results/learning_confirmation/completion.json`；单线程总耗时约22.04 s |

NPZ键为 `test_x`、`test_h_res`、`test_g_res`、`test_q_raw`、`test_tip_m`，以及相同含义的 `ood_*`。这里 `g_res` 是输入 $x$ 上的无量纲梯度；转回正则变量必须乘 $D=\operatorname{diag}(\sqrt\nu,\sqrt\nu)/a$。

后续SPD等模型家族可以使用这一确认集，但必须在打开标签/结果之前另行冻结其全部模型和训练选择，再作一次评估；不能据此继续调参或选择模型。当前确认清单仅包含本轮冻结的原修正版复网络及48特征、二次基线。

### 8.6.3 新确认集结果

#### 8.6.3.1 梯度和正则向量场

复网络三种子的最小—最大值如下：

| 幅值与域 | 归一化 $x$ 梯度相对误差 | 正则 $z$ 向量场相对误差 | 原始Ritz广义速度相对误差 |
|---|---:|---:|---:|
| 0.08，域内2048点 | 1.628–1.706% | 1.815–1.950% | 1.841–2.018% |
| 0.08，OOD1024点 | 6.357–6.895% | 4.506–4.720% | 4.560–4.726% |
| 0.35，域内2048点 | 1.852–1.891% | 5.444–6.167% | 5.987–7.883% |
| 0.35，OOD1024点 | 6.752–6.993% | 9.176–10.081% | 10.870–14.223% |

两固定基线的正则向量场相对误差为：主域内二次模型62.537%、48特征62.304%，主OOD分别77.700%、77.137%；stress域内分别97.154%、93.598%，stress OOD分别98.948%、94.624%。这确认该具体小特征库在全相空间域中的表达不足；48与7104实参数、不同损失和不同函数类的比较仍不支持单独的“复数表示优势”。

#### 8.6.3.2 能量误差

物理能量RMSE已经乘以 $E_0=3.62\times10^{-7}$ J：

| 幅值与域 | 二次基线 | 48特征 | 复网络三种子范围 |
|---|---:|---:|---:|
| 0.08，域内 | $3.8866$ $\times10^{-9}$ J | $2.9714$ $\times10^{-9}$ J | $(6.5142\text{–}6.7407)$ $\times10^{-11}$ J |
| 0.08，OOD | $1.8551$ $\times10^{-8}$ J | $1.3994$ $\times10^{-8}$ J | $(7.8897\text{–}8.7908)$ $\times10^{-10}$ J |
| 0.35，域内 | $1.2853$ $\times10^{-6}$ J | $9.2184$ $\times10^{-7}$ J | $(1.6449\text{–}1.7912)$ $\times10^{-8}$ J |
| 0.35，OOD | $5.8033$ $\times10^{-6}$ J | $4.0711$ $\times10^{-6}$ J | $(2.2829\text{–}2.3821)$ $\times10^{-7}$ J |

这些是冻结模型面对新独立合成样本的经验误差，不是高阶或复域误差界，也不是连续体、实验机器人或闭环精度结论。

#### 8.6.3.3 12点动量Hessian检查

每个新域用预先固定种子20261031选12点，各模型共享相同索引。主域内三种子的最小特征值约0.5833、0.5641、0.6056；所抽样本全部为正，不能据此认证全域正定。

主OOD的最小特征值约−0.6255、−3.1213、−2.3663，非正数为4/12、1/12、1/12。stress域内最小约−10.6695、−13.7534、−44.8897，非正数为10/12、8/12、9/12；stress OOD三个seed均12/12出现负方向，最小约−234.14、−295.77、−466.83。新独立数据再次支持原审查的限制：一般Hamiltonian残差拟合没有保持正质量结构。负方向也按独立能量二阶差分复核，细节在结果JSON中。

### 8.6.4 `--reuse-data` 防护补丁

先保存了未经修改的训练时源码快照：

- `program/learning/run_learning_trained_source.py`
- SHA `8b5c0eb4f8a0c8b7b4b9db2b2330f49809bca10d3d8aeafef1e3b0e9dcfbd6a2`

随后只修改当前 `run_learning.py` 的主入口数据读取防护与相关输出时序：要求既有数据、`learning_summary.json` 和 `rom_matrices.npz` 存在；验证幅值、数据SHA、相空间维数及 $M_0,K_0,S_q,S_p$ 与当前模型逐值相同；不一致立即明确拒绝。原来在读取前覆盖矩阵的写入被移到校验成功以后，以避免损坏旧身份记录。

补丁后源码SHA为 `868de74c224e46082555b5a6553ea70f52a0ee17ec23ed4631fc932e10aecdae`。AST检查证明全部非main函数与类完全相同，包含网络、特征、标签、损失、优化和评分；没有重新训练或覆盖现有结果。记录为 `notes/learning_reuse_guard_patch.json`。

另在复制的隔离输入上检验六种情况：正常身份通过读取后、在训练前主动停止；幅值错误、数据SHA错误、矩阵错误、相空间维数错误、缺失摘要全部明确拒绝，并确认拒绝时已有复制证据文件不变。结果在 `runs/learning_reuse_guard/results.json`。这是I/O身份防护补丁，不是对旧训练算法的数值修订；旧冻结研究使用训练时快照解释其结果。

## 8.7 机械正质量复网络的实际结果

本文件记录因已观察到的动量 Hessian 失正定而进行的一项结构修正。它与方向 A 的一般 Birkhoff / Moser 复算分开；不将下面的 12 位形自由度 Kirchhoff 学习模型冒称为已连接一般 Birkhoff 图的完整血流—接触 Cosserat 模型。

### 8.7.1 问题依据与此次实际完成的目标

原有完整复值网络允许任意偶动量非线性，虽保证实值 Hamiltonian、动量偶性以及原点 0/1/2 阶 jet，却没有约束 $H_{PP}$。在已有同一模型、同一种子 1025 的冻结检查点上：主域幅值参数 $a=0.08$ 的 12 个 OOD 抽样有 2 个 $H_{PP}$ 非正，最小特征值约 $-2.66015$；压力域 $a=0.35$ 的测试/ OOD 抽样分别有 9/12、11/12 非正，最小值约 $-10.7654$、$-534.390$。原评估还以能量方向二阶差分核验了负曲率，并非只看自动微分单个输出。这是此次修正的实际问题依据。[输入证据：`stage2/results/learning/evaluation_summary.json` 与 `stage2/results/learning_stress/evaluation_summary.json`。]

因此本次采用与原机械标签一致的动量二次结构，要求质量逆矩阵处处正定，并实际重新训练，而不是将旧网络的负特征值裁剪后声称旧模型已有机械 Legendre 反解。原模型、原始失败实验以及此次第一次审计中止记录均保留。

### 8.7.2 模型结构与可直接证明的性质

#### 8.7.2.1 坐标、尺度与完整相空间

保留同一 $n=12$ 个位形坐标及其 12 个正则动量。令

$$
z=(Q,P),\qquad D_\nu=\operatorname{diag}(\sqrt{\nu_1},\ldots,\sqrt{\nu_n}),\qquad
x_Q=D_\nu Q/a,\quad x_P=D_\nu P/a.
$$

已知线性 Hamiltonian 是

$$
H_0(z)=\frac12\sum_i\nu_i(Q_i^2+P_i^2)
=\frac{a^2}{2}(\lVert x_Q\rVert^2+\lVert x_P\rVert^2).
$$

$x$ 是用于平衡能量的归一化坐标，并非正则坐标；其 Poisson 矩阵为 $D J D$，其中 $D=\operatorname{diag}(D_\nu,D_\nu)/a$。本次训练仍沿用原标签的 $\nabla_x H$，评估另行换算

$$
\nabla_z H=D\nabla_x H,\qquad z'=J\nabla_z H.
$$

这避免把输入归一化梯度误差等同于正则 Hamiltonian 向量场误差。幅值 $a=0.08$ 或 $0.35$ 是能量坐标盒的尺度，不是米、弧度或尖端位移幅值。

#### 8.7.2.2 共享的可训练复值位形主干

全部隐藏层和两类读出均为可训练复权重。采用宽度 48，位形输入复化为 $\operatorname{complex}(x_Q,0)$，令

$$
A=W_1\operatorname{complex}(x_Q,0),\qquad
F=\sigma\left(W_2\sigma(A)+b_2\right),
$$

$$
\sigma(u+iv)=\tanh(u)+i\tanh(v).
$$

这里是实输入上的实解析复值网络，不是将复平面上的有极点 $\tanh(z)$ 当作无条件稳定的激活，也不声称整个网络关于独立复坐标全纯。第一层没有偏置，所以 $A(0)=0$。

质量读出具有 $n(n+1)/2=78$ 个复系数通道：

$$
r(x_Q)=\Re\left[W_M(F(x_Q)-F(0))\right].
$$

按下三角位置排列它们，定义

$$
L_{ij}=\begin{cases}
r_{ij},&i>j,\\
\exp(r_{ii}),&i=j,\\
0,&i<j,
\end{cases}
\qquad C_\theta=L_\theta L_\theta^T.
$$

实现中的 $F(0)$ 分支参与自动微分；没有将它缓存为与更新权重无关的常量。因而所有参数更新后都有 $r(0)=0$、$L(0)=I$、$C(0)=I$。

势能残差采用三次零偏置门控：

$$
V_{\theta,\mathrm{res}}(x_Q)
=s_H\Re\left[W_V\big(A(x_Q)^{\odot3}\odot F(x_Q)\big)\right].
$$

最终总 Hamiltonian 明确为

$$
\boxed{
H_\theta(z)=\frac{a^2}{2}x_P^TC_\theta(x_Q)x_P
+\frac{a^2}{2}\lVert x_Q\rVert^2
+V_{\theta,\mathrm{res}}(x_Q).
}
$$

代码 `energy(x)` 返回该总能量；`forward(x)` 返回 $H_\theta-H_0$，与原残差标签和评估函数兼容。计算动能时采用 $\lVert L^Tx_P\rVert^2$，没有把 $LL^T$ 的顺序误换为 $L^TL$。

#### 8.7.2.3 正定性、Legendre 反解与 jet 的推导

由 $x_P=D_\nu P/a$，固定 $Q$ 后有

$$
\nabla_P H_\theta=A_\theta(Q)P,\qquad
H_{\theta,PP}=A_\theta(Q)=D_\nu L_\theta L_\theta^TD_\nu.
$$

每个 $\nu_i>0$，每个有限实数输入及有限权重下 $L_{ii}=\exp(r_{ii})>0$，所以 $L$ 可逆。对任意非零 $v$，

$$
v^TH_{\theta,PP}v=\lVert L_\theta^TD_\nu v\rVert^2>0.
$$

这给出结构上的严格正定性。对每一个固定 $Q$，动量到正则速度的映射全局线性可逆：

$$
P=A_\theta(Q)^{-1}\dot Q,\qquad
\mathcal L_\theta(Q,\dot Q)=\frac12\dot Q^TA_\theta(Q)^{-1}\dot Q-V_\theta(Q).
$$

这里 $\dot Q$ 是无量纲时间下的正则位形速度；不能直接解释为尖端速度。该结论不要求有限样本特征值全部为正才能成立；样本用于核对实现与浮点条件数。指数参数化仍可能在极端浮点输入发生上溢、下溢或病态，解析正定性不提供自动的实际数值条件数界。

其次，$C(x_Q)-I=O(\lVert x_Q\rVert)$，故

$$
\frac{a^2}{2}x_P^T(C-I)x_P=O(\lVert x_Q\rVert\lVert x_P\rVert^2).
$$

门控势残差是 $O(\lVert x_Q\rVert^3)$。联合原点附近 $H_\theta-H_0$ 的最低总阶至少三阶，故残差能量、梯度和 Hessian 在原点均为零。无需在训练中软惩罚其 0/1/2 阶 jet。动量只以二次型出现，所以 $H(Q,P)=H(Q,-P)$、$\partial_P^3H=0$，而 $H_{PP}$ 与 $P$ 无关。

#### 8.7.2.4 结构先验的范围

这是完整 12 位形自由度、24 相空间维度模型中的机械结构先验，不是降低状态维数。原标签的确来自 $\frac12P^TM(Q)^{-1}P+V(Q)$，所以二次动量约束有物理依据。一般偶动量 Hamiltonian 允许 $P^4$ 等项，此处没有保留这种自由度；因此不能把此次结果称为一般任意动量依赖的 HNN。

实参数数目为 13,440（6,720 个复参数）：第一层 576、第二层权重 2,304 及偏置 48、质量读出 3,744、势读出 48 个复参数。原非受限网络为 7,104 个实参数；这不是等容量对比，也不是实网络与复网络的表示优势试验。这里比较的是对原实际机械可逆性失败的修正及其精度、成本代价。

### 8.7.3 数据、训练与审计约定

两个域均直接读取原有 NPZ 标签，没有重新采样训练集或修改标签。每域 train 4,096、validation 512、test 1,024、OOD 512。数据种子为 20261029；主域和压力域的归一化样本行相同，物理幅值及标签不同。训练、验证与测试满足 $x_j\in[-1,1]$，OOD 为 $[-1.5,1.5]$。相同行交集和数据 SHA 单独核验。

标签来自同一 12 自由度三维不可伸长、不可剪切 Kirchhoff 应变 Ritz 模型：两个弯曲轴及扭转各四个 Legendre 应变系数；20 段几何积分；SO(3) 姿态更新；含平动与转动惯性的位形相关质量；偏置磁场下的弹性与磁势。它不是全 Cosserat 血流—接触高保真标签，也不是实验测量。物理能量尺度 $E_0=3.62\times10^{-7}\,\mathrm J$，时间尺度 $\omega_0=4.4576294085\,\mathrm{s}^{-1}$。[来源：`rod_rom.py`、`learning/rom_metadata.json`。]

两域各一次预设 seed 1025、宽度 48、Adam 学习率 0.003、batch 256、梯度范数裁剪 10、步数标签 6,000。严格沿用原脚本的 `range(steps+1)` 约定，实际是 6,001 次更新。损失为

$$
\mathcal J=\operatorname{mean}\left\lVert
\frac{\nabla_x(H_\theta-H_0)-g_{\mathrm{res}}}{s_g}\right\rVert_{\mathrm{component}}^{2}
+0.15\operatorname{mean}\left(
\frac{H_\theta-H_0-h_{\mathrm{res}}}{s_H}\right)^2,
$$

其中 $s_H$ 为训练能量残差标准差，$s_g$ 为训练残差梯度的逐分量 RMS。每 200 步按 validation 的残差梯度相对 $L^2$ 误差选模；未使用 test 或 OOD 选检查点。全复参数的实部、虚部更新范数分别保存，用于核验隐藏层实际参与训练而非固定复特征回归。

本次是在已经检查旧 test/OOD 负曲率后设计的结构修正，因此原 test/OOD 复用比较属于探索性结果；原划分行无重复也不能消除这种架构选择上的自适应性。新独立确认集若另行生成，只做冻结模型评估，不能再用于改架构或选训练步数。

源脚本为 `stage2/program/learning/train_spd_complex.py`。只输出新的 `stage2/results/learning_spd/`，不覆盖原学习网络、失败模型和数据。

#### 8.7.3.1 第一次运行的审计中止必须保留

第一次主域训练实际完成了 6,001 次更新及预测，最终验证残差梯度相对误差为 0.0881432403，训练约 50.29 秒。但末尾来源哈希检查发现另一项并行工作修改了 `run_learning.py`，于是按预设审计守则中止，没有生成正式汇总。该次日志、检查点和预测保存在 `learning_spd/local_hashaudit_interrupted/`。

已查明变更是为旧 `--reuse-data` 增加幅值、SHA 和模态矩阵身份检查，并调整 `main` 的读写时序；旧标签、网络、训练和预测函数未改。仍将原日志保留，并在冻结来源后同种子、同架构、同超参数重新完整运行；没有将第一次不完整运行静默覆盖或把重跑包装成额外超参数搜索。正式运行会逐个核对输入文件前后哈希，并保存完整训练历史、最佳验证步、预测、Hessian 样本与复参数更新。

实际 AST 比较已保存至 `upstream_guard_change_audit.json`：所有共同定义中只有 `main` 不同，`ComplexResidual`、`labels`、`network_prediction`、`scores`、`train_one` 等定义相同。`modal_identity_audit.json` 另行逐项核对本次实际构造的 $M_0,K_0,S_Q,S_P,\nu,\omega$ 与原两个数据域的存储矩阵，全部逐元素相等；配置 SHA 为 `500006a75ab5f3ba951c2f7912e6e27dc97418faf1b0a9149258318ca6b81c5b`。两次正式运行的上游源码、数据和评估文件前后 SHA 全部一致。

### 8.7.4 实际训练结果与成本

#### 8.7.4.1 两个预设训练运行

| 域 | 幅值参数 | 最佳验证步标签 | 最佳验证残差梯度相对误差 | 第 6,000 步验证误差 | 正式训练耗时（含验证） | 含初始化与评估总耗时 |
|---|---:|---:|---:|---:|---:|---:|
| 主域 | 0.08 | 6,000 | 0.0881432 | 0.0881432 | 92.10 s | 95.48 s |
| 压力域 | 0.35 | 2,000 | 0.552936 | 0.581583 | 45.52 s | 47.20 s |

两域都按计划完成 6,001 次更新。压力域采用 validation 所选第 2,000 步，并非挑选测试表现较好的后期检查点。未继续调参、换训练数据、增加种子或调整步数以隐藏其失败。训练缩放量分别为主域 $s_H=0.00899810$、$s_g=0.00651396$，压力域 $s_H=2.78164395$、$s_g=2.10666889$。

这是 CPU 单线程运行：Torch 2.5.1，`OMP_NUM_THREADS=1`、`OPENBLAS_NUM_THREADS=1`，Torch 线程数为 1。正式主域运行期间存在并行任务负载；第一次相同验证轨迹用时 50.29 s，正式重跑用时 92.10 s。原非受限网络主域、压力域训练记录为 55.05 s、51.49 s。这些是实际墙钟记录，不是控制 CPU 竞争、预热和多次重复后的性能基准，不能据此宣称该结构更快或更慢。

全部可训练层的实部、虚部更新范数均非零，包括两个复隐藏层、质量读出和势读出。主域第一次与正式重跑的验证误差逐点一致。

#### 8.7.4.2 原探索性 test/OOD 比较

下表均为同 seed 1025；梯度项是对真实总梯度的全样本相对 $L^2$ 误差，不是逐点误差上界；能量列为无量纲残差能量 RMSE。参考总能量中的相同 $H_0$ 抵消，因此能量误差亦为总能量差。

| 域 / 集合 | 网络 | $\nabla_x H$ 相对误差 | $\nabla_z H$ / 正则向量场相对误差 | 能量 RMSE |
|---|---|---:|---:|---:|
| 主域 test | 原非受限 | 1.6830% | 1.9066% | $1.82761$ $\times10^{-4}$ |
| 主域 test | 本次 SPD | 6.8990% | 6.8925% | $6.51672$ $\times10^{-4}$ |
| 主域 OOD | 原非受限 | 7.3546% | 4.9047% | $2.92285$ $\times10^{-3}$ |
| 主域 OOD | 本次 SPD | 15.7656% | 12.5111% | $5.52089$ $\times10^{-3}$ |
| 压力域 test | 原非受限 | 1.7535% | 5.9443% | $4.50397$ $\times10^{-2}$ |
| 压力域 test | 本次 SPD | 55.4690% | 97.0362% | 1.35461 |
| 压力域 OOD | 原非受限 | 7.7862% | 10.2903% | 0.947471 |
| 压力域 OOD | 本次 SPD | 63.9457% | 113.3749% | 9.93365 |

主域 SPD 的 Ritz 位形速度相对误差为 test 8.3041%、OOD 13.2886%；压力域为 104.5806%、116.3619%。这些仍是 12 个 Ritz 曲率系数的速度，不是血管内尖端位置或跟踪误差。

此次结果不支持“加上 SPD 先验便提高精度”。主域以明显的拟合代价换得了正确机械结构；压力域甚至没有获得可用的动力学近似。在当前单种子、固定预算和超参数下可以这样报告，不能推演成所有 SPD 参数化必然难以拟合的普遍命题。

#### 8.7.4.3 同一有限样本的质量 Hessian 与数值反解

每域分别使用原独立审查确定的 12 个 test 和 12 个 OOD 索引；具体索引、每点特征值和误差均在各域 `learning_summary.json`。下表 $A=H_{PP}$，Frobenius 误差将该组全部矩阵合并计算。

| 域 / 集合 | 本次 $\min\lambda(A_\theta)$ | 原机械标签对应 $\min\lambda(A_*)$ | 本次最大条件数 | $\frac{\lVert A_\theta-A_*\rVert_F}{\lVert A_*\rVert_F}$ |
|---|---:|---:|---:|---:|
| 主域 test | 0.916001 | 0.968972 | $1.014$ $\times10^3$ | 6.1352% |
| 主域 OOD | 0.439566 | 0.922258 | $2.297$ $\times10^3$ | 13.4148% |
| 压力域 test | $7.56054$ $\times10^{-8}$ | 0.620996 | $4.614$ $\times10^{10}$ | 320.3440% |
| 压力域 OOD | $2.62776$ $\times10^{-9}$ | 0.385909 | $1.133$ $\times10^{12}$ | 371.8084% |

这些数值全部有限，非正样本计数均为 0。解析矩阵 $D_\nu LL^TD_\nu$ 与总能量自动微分 Hessian 的最大相对差不超过 $7.33\times10^{-16}$。改变同一 $Q$ 下的动量后 Hessian 变化为 0。原点残差能量、梯度、Hessian 及 $L(0)-I$ 范数均为 0；64 个样本的动量偶性差为 0。

但必须区分以下三个层面。

1. **解析结构**：对每个固定有限 $Q$，矩阵严格正定，Legendre 映射在动量变量上可逆。这由构造证明。
2. **浮点数值可逆性**：并没有获得在整个工作域有效的最小特征值常数或条件数界。压力域出现约 $10^{12}$ 的抽样条件数，已构成“仅凭 SPD 就可安全数值反解”的实际反例。
3. **物理近似准确性**：即使线性方程能解，所求的仍可能是错误的近似质量。压力域相对 Hessian 误差超过 300%，不能用于可靠的物理速度—动量转换。

已用 $v=A_\theta P$ 后解 $A_\theta\widetilde P=v$ 做自洽性检查；主域 test/OOD 的最大 $\lVert\widetilde P-P\rVert$ 为 $3.18\times10^{-16}$、$8.14\times10^{-16}$，压力域为 $3.55\times10^{-9}$、$5.79\times10^{-7}$。这只是在学得矩阵下自回代的误差，不是用真实物理速度反求真实动量的误差，不能拿来掩盖上表中的质量表示误差。

原机械标签在相同压力域样本的最小特征值约 0.62/0.39，远高于学得的近零值；这里的病态并非由这些被检查的真实质量样本本身要求。未进一步确定优化困难的唯一原因，也未借此开展额外参数搜索。

### 8.7.5 冻结权重后的新确认集

独立任务以新种子 20261030 生成每域 2,048 个 test、1,024 个 OOD 样本。两个 SPD 模型先完成预定训练、按旧 validation 选模并记录 SHA，再由 `evaluate_spd_confirmation.py` 写入本次自己的冻结清单、复制检查点，然后才打开新确认标签。本次没有用新集训练、选架构、调超参数或选择训练步数。新确认集在 SPD 冻结前已由另一项任务生成，这一时间关系也明确写入清单；没有声称所有确认数据都在 SPD 冻结之后才生成。

新样本与原 train/validation/test/OOD 的逐行精确交集全部为 0；对应模态矩阵与本次模型全部逐元素相同；确认数据与独立生成清单的 SHA 一致。两权重 SHA 在确认前后不变：

- 主域：`c35f6ba663de0577dc96c0e06066dd6af6794d8c12a1075442678bc783f75afd`。
- 压力域：`116a9879da594b9c3118c6595ef462612c6257e59781289f7b89304a9dd98a17`。

#### 8.7.5.1 新确认集上的同种子比较

| 域 / 集合 | 网络 | $\nabla_x H$ 相对误差 | $\nabla_z H$ / 正则向量场相对误差 | 无量纲能量 RMSE |
|---|---|---:|---:|---:|
| 主域 test | 原非受限 | 1.7032% | 1.9501% | $1.80042$ $\times10^{-4}$ |
| 主域 test | 本次 SPD | 7.1098% | 6.8558% | $6.62023$ $\times10^{-4}$ |
| 主域 OOD | 原非受限 | 6.6797% | 4.6933% | $2.38173$ $\times10^{-3}$ |
| 主域 OOD | 本次 SPD | 15.4082% | 13.6084% | $5.18895$ $\times10^{-3}$ |
| 压力域 test | 原非受限 | 1.8632% | 6.0427% | $4.75669$ $\times10^{-2}$ |
| 压力域 test | 本次 SPD | 58.8819% | 98.8827% | 1.66619 |
| 压力域 OOD | 原非受限 | 6.7518% | 9.4627% | 0.630627 |
| 压力域 OOD | 本次 SPD | 63.5162% | 119.7516% | 7.97035 |

SPD 的物理能量 RMSE 依次为主域 test $2.39652\times10^{-10}\,\mathrm J$、OOD $1.87840\times10^{-9}\,\mathrm J$，压力域 test $6.03159\times10^{-7}\,\mathrm J$、OOD $2.88527\times10^{-6}\,\mathrm J$。这些只是模型能量误差，不是安全指标。

作为数量级参照，同一新确认集的正则梯度相对误差如下。线性基线没有可训练参数；解析残差具有 48 个固定特征的线性拟合系数；原非受限网络 7,104 实参数；本次 SPD 网络 13,440 实参数，各容量与训练形式不同。

| 域 / 集合 | 已知线性 $H_0$ | 48 特征解析残差 | 原非受限复NN | 本次 SPD 复NN |
|---|---:|---:|---:|---:|
| 主域 test | 62.5373% | 62.3044% | 1.9501% | 6.8558% |
| 主域 OOD | 77.7005% | 77.1368% | 4.6933% | 13.6084% |
| 压力域 test | 97.1541% | 93.5977% | 6.0427% | 98.8827% |
| 压力域 OOD | 98.9481% | 94.6239% | 9.4627% | 119.7516% |

压力域 SPD 的归一化 $\nabla_x$ 指标虽优于线性基线，其正则 $\nabla_z$ 指标反而更差，说明只报归一化指标会掩盖高频坐标的动力学误差。新确认集没有推翻原探索集发现的不利结果。确认评估共约 0.64 s，没有重新计算有限 Hessian 抽样来代替已有结构证明；其任务是检验冻结网络的表示误差。

这仍是同一 12 自由度 ROM 的新合成状态确认，不是新物理实验、不同杆参数、全 Cosserat 轨迹或临床条件确认；只有一个预设初始化种子，不据此宣称初始化稳健性。

### 8.7.6 对主线研究能继承什么，不能继承什么

可以继承的是一个实际可训练、可复现的完整复隐藏层机械 Hamiltonian 参数化；它没有降维，并对动量偶性、二次性、原点 jet 及逐点正定性给出了精确结构证明。它同时提供了重要反例：结构成立与函数逼近准确、数值条件良好是独立问题，类似方向 A 中“图的结构缺陷很小但所表示的向量场仍不准确”的区分。

当前不能将压力域 SPD 检查点用作可靠的质量替代或 Legendre 反解，也不能用其逐点正定性给出 KAM 的统一误差预算。主域同样没有全域误差、全域条件数、复邻域解析范数或非退化性认证。原 ROM 的成对弯曲共振也未因此消失。可训练结构本身不能填平 Birkhoff 坐标构造、血流/接触闭合和离散结构证明的缺口。

对于已有前馈对照，项目目前使用已知几何质量 $M$ 进行相关机械计算，学习网络只参与所声明的有限 $H_Q$ 补偿对照。此次发现不能被表述为那组实验已经使用了错误的神经质量，也不能反过来借该对照声称神经质量已有验证。

若后续继续研究，可另设预注册试验，考虑以已知几何质量或其逆作为基线、直接约束质量残差的尺度/条件数、分开监督质量与势能、或将正则向量场误差纳入验证指标。这里没有实施这些新方案，不能把它们写成已取得的改善。当前按预定方案停止，保留单种子压力域失败及所有原始文件。

### 8.7.7 可重现文件与命令

核心程序：

- `stage2/program/learning/train_spd_complex.py`：架构、训练、同数据指标、原点 jet、动量 Hessian 与自洽 Legendre 回代核验。
- `stage2/program/learning/evaluate_spd_confirmation.py`：先冻结两检查点，再进行新确认集评估；无优化器。

正式结果：

- `stage2/results/learning_spd/local/`、`stress/`：`learning_summary.json`、`run_inputs.json`、`training_seed1025.json`、检查点、test/OOD 预测及 `run.log`。
- `stage2/results/learning_spd/confirmation/`：冻结清单、冻结检查点副本、主域/压力域汇总、预测及完成记录；根目录另有 `confirmation_run.log`。
- `stage2/results/learning_spd/local_hashaudit_interrupted/`：首次主域运行的审计中止证据。
- `stage2/results/learning_spd/upstream_guard_change_audit.json`、`modal_identity_audit.json`：并行变更范围及模态坐标一致性核验。

从工作区根目录运行以下命令。默认脚本拒绝覆盖已经写完的正式汇总；复现实验应使用新的输出子目录。确认评估同样拒绝覆盖已有冻结记录。

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 stage2/envs/learning/bin/python \
  stage2/program/learning/train_spd_complex.py \
  --data-dir stage2/results/learning \
  --output stage2/results/learning_spd/reproduction_local --steps 6000

OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 stage2/envs/learning/bin/python \
  stage2/program/learning/train_spd_complex.py \
  --data-dir stage2/results/learning_stress \
  --output stage2/results/learning_spd/reproduction_stress --steps 6000

# 对已正式训练并冻结身份的 local/stress 检查点仅做确认评估：
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 stage2/envs/learning/bin/python \
  stage2/program/learning/evaluate_spd_confirmation.py \
  --output stage2/results/learning_spd/confirmation_reproduction
```

上述最后一条默认评估本次正式 `local`/`stress` 检查点。若要评估重新训练的模型，应将两运行分别置于另一共同根目录的 `local`/`stress`，并显式传入该目录的 `--spd-root`；不应把 `--output` 路径误当作模型输入路径。



![图8-1 冻结模型在新独立数据上的正则向量场误差。复网络显示三个种子的范围；正质量网络仅一个种子。容量不同，不据此推断复数表示优越。](/workspace/scratch/990e101b41bd/stage2/results/figures/learning_confirmation.png){width=6.85in}

# 9 Metriplectic 的具体候选及本阶段取舍

1025引入对称耗散括号的动机成立：机械耗散应与可逆几何分开，并希望用总能量和熵统一描述不可逆过程。需要修正的是把机械能衰减公式直接称为完整Metriplectic，以及把任意耗散隐藏到复能量虚部或正则Birkhoff一形式中。当前机械研究可用Rayleigh耗散与外部功率端口闭合；是否增加热状态取决于是否研究温升、热软化、磁损耗和热损伤，不能由数学形式的便利决定。[R4]

## 9.1 以内部能量为坐标的候选

在实际 $N$ 自由度机械系统上增加一个内部能量 $e$，令 $x=(q,p,e)$、$E=H(q,p)+e$、$S=S(e)$、$T=1/S'(e)>0$，$v=H_p$，$C=C^T\succeq0$。取扩展Poisson矩阵

$$\mathcal J=\begin{pmatrix}0&I&0\\-I&0&0\\0&0&0\end{pmatrix},\qquad\text{(M1)}$$

以及对称算子

$$\mathcal M=T\begin{pmatrix}0&0&0\\0&C&-Cv\\0&-v^TC&v^TCv\end{pmatrix}.\qquad\text{(M2)}$$

对任意协向量 $(\alpha,\beta,\eta)$，

$$ (\alpha,\beta,\eta)^T\mathcal M(\alpha,\beta,\eta)=T(\beta-\eta v)^TC(\beta-\eta v)\ge0.\qquad\text{(M3)}$$

直接相乘给出完整退化条件

$$\mathcal J\nabla S=0,\qquad\mathcal M\nabla E=0.\qquad\text{(M4)}$$

于是 $\dot x=\mathcal J\nabla E+\mathcal M\nabla S$ 产生 $\dot q=H_p$、$\dot p=-H_q-Cv$、$\dot e=v^TCv$，故 $\dot E=0$、$\dot S=v^TCv/T\ge0$。机械能减少而总能量不变，丢失的机械能流入内部能量；这正是原稿缺失的热力学状态。

若机械 $H$ 显式依赖时间、存在磁驱动、流体或移动壁，则仍有外部功率。M4只负责内部不可逆交换，不会消除外部能源。若热流、散热或磁滞需要纳入，必须另建相应能量交换与熵产生项及参数，不可用一个任意标量熵函数充当全部热物理。

## 9.2 与详细报告熵坐标形式的等价

令 $e=U(S)$、$U'(S)=T$。由坐标变换 $\mathcal M_S=D\chi\mathcal M_e D\chi^T$、$\partial S/\partial e=1/T$ 可得

$$\mathcal M_S=\begin{pmatrix}0&0&0\\0&TC&-Cv\\0&-v^TC&v^TCv/T\end{pmatrix},\quad E=H+U(S).\qquad\text{(M5)}$$

这就是详细118页报告的形式。较早56页报告的内能形式M2与它完全相容。两者的状态坐标不同，不能仅比较矩阵中的 $T$ 因子就判为矛盾。

本轮在实际12自由度ROM的32个状态上进行了无量纲候选核验：取 $e>0$、$S=\log e$、$T=e$，采用明确的非比例正定 $C$。$\mathcal M\nabla E$ 的最大归一化残差约 $6.36\times10^{-17}$，$\mathcal J\nabla S$ 为零，总能量变化率最大绝对值约 $4.44\times10^{-16}$；熵变化率与 $v^TCv/T$ 相符。数值特征值的 $-1.57\times10^{-16}$ 级相对值属于半正定矩阵的浮点舍入；正半定结论由M3的精确因式分解给出，不由抽样本身证明。该核验没有热容或温度实测数据，不是温升模拟。

## 9.3 为什么暂不把热状态加入主机器人仿真

当前目标首先是轨迹、磁约束、接触力和机械功率；已运行模型没有温度依赖材料或磁滞热源。机械Rayleigh损耗和端口能量足以定义这些已运行试验。加入一个没有热容、导热、血流换热和边界温度依据的 $S$ 状态，不会提高机械结果的可信度。因此本轮保留M1—M5作为已推导、已作代数数值核验的候选，但不宣称实际完成热—流—固—磁耦合。

固定壁的平滑摩擦可用非线性正半定阻力表示，但规定流速 $u_f$ 下的流体阻力依赖 $v-u_f$，不能直接把其机械功率全部转成 $v^TCv$ 热量。完整热力学需要把流体或运动介质的功率端口计入，或显式增加流体动量与内部能量。电阻热与线圈电源亦相同。

Birkhoff研究非退化闭二形式及其跨时刻保持；Metriplectic研究退化Poisson结构、对称耗散及总能量／熵。扩展状态 $(q,p,S)$ 为奇维，M1的Poisson矩阵本来不可逆，不能直接取逆当作全状态正则Birkhoff矩阵。在相应辛叶上研究可逆子系统、或对特定机械闭环构造时变Birkhoff表示，是另外的论证。


# 10 统一写作框架与下一阶段的具体工作

## 10.1 三层模型保留不同职责

| 层次 | 统一对象 | 本轮完成 | 仍需补齐 |
|---|---|---|---|
| 完整研究目标 | 三维Cosserat杆、磁场／电路、脉动血流、柔性血管壁、接触摩擦、微重力生理边界 | 给出方程、虚功、能量和端口框架；完整空间杆和多载荷已有独立程序 | 双向FSI、壁动力学、插入及生理／硬件标定 |
| 高维可运行验证 | 16／32／64段三维杆，SO(3)姿态、伸长剪切、弯曲扭转，规定血流和刚性管腔接触 | 网格与步长细化、失败记录、控制／接触／输入／鲁棒性比较、完整线圈载荷 | 更复杂血管几何及初始构形、事件求解、连续净空与力上界 |
| 理论与学习ROM | 从三维构形嵌入产生的12自由度Kirchhoff模型，M(q)与磁端口可微 | 三维几何和质量独立检查，完整复网络／解析残差、磁前馈到32／64段 | 从完整杆数据做辨识与ROM误差界；一般Birkhoff图；新连续／离散KAM证书 |

两模态旧模型继续承担旧结论回归和低维公式验证，不能成为最终研究对象。8／16自由度数学试验补强Birkhoff算法，但其已知点变换质量也不等同于任意真实杆的质量几何。三个层次的参数、训练权重、误差和证明分别冻结。

## 10.2 论文中可写与不可写的结论

| 主题 | 本轮证据允许的表述 | 需要避免的越界表述 |
|---|---|---|
| 原稿同一性 | 当前（2）（3）（4）实际文件逐字节一致 | 所有历史或未来同名版本都一样 |
| 1025继承 | 三维、多物理、复学习、Birkhoff、控制和条件KAM均保留并推进 | 原稿全部推导已经成立 |
| 原v10证书 | 原冻结两模态保守Hamiltonian的学习和环面证书重新执行通过 | 新材料／三维／血流接触系统已获得同一KAM证明 |
| 高维机器人 | 已运行16／32／64段三维杆及ROM控制转移 | 原64平面模态结果本来就是三维杆 |
| CHNN | 可训练复隐藏层已实际训练；新确认集与结构反例均给出 | 复表示普遍优于实表示，或小测试误差保证正质量与KAM |
| 结构保持 | 指明二形式、向量场、时间图及隐式分支后验证 | 小结构缺陷代表原动力学准确；任意反馈仍保原结构 |
| 磁实现 | 实际电流、完整场／梯度及约束分配已计算 | 任意高维U都能由磁场实现；原点8维输入限制自动约束全域 |
| 接触 | 给定罚律下的有限轨迹、接触力和罚参数敏感性 | 用有穿透的罚模型证明连续杆绝不穿壁 |
| 收敛 | 给出实际观测阶及相应光滑条件 | 仅因积分器名称而声称所有开放系统二阶或辛 |
| Metriplectic | 总能量—熵候选满足退化，并作独立代数数值核验 | 已测出机器人温升；它与Birkhoff是同一结构 |

## 10.3 英中稿共用的符号和章节

为继续撰写英文、中文论文，建议将原v10成熟的学习、正规形、环面及控制叙述保留为独立路线，在共同模型之后并列展开。原稿编号留在本报告对照表；论文新编号应在两种语言中由同一公式源生成，避免手动搬号。

| 统一符号 | 中文含义 | 英文表述 |
|---|---|---|
| $r$，$R$ | 中心线，材料到空间的姿态 | centerline and material-to-spatial orientation |
| $\nu$，$\kappa$，$\Omega$ | 伸长剪切，曲率扭率，体角速度 | shear-extension strain, curvature-twist strain, body angular velocity |
| $q$，$p$，$H$ | 降阶位形，正则动量，实机械Hamiltonian | reduced configuration, canonical momentum, real mechanical Hamiltonian |
| $Q$，$P$，$h$ | 规范尺度化相变量和能量 | canonically scaled state and Hamiltonian |
| $x$ $=Dz$ | 仅用于统计训练的归一化输入 | statistical input normalization, not a canonical chart |
| $\xi$及$\overline\xi$ | 复输入及其共轭 | complex and conjugate-complex inputs |
| $\phi(q)$，$G_m$ | 磁通／势特征，磁广义力端口 | magnetic potential features and generalized-force port |
| $a_i\,$ $dz_i-B_B\,$ $dt$ | Pfaff一形式 | Pfaffian one-form |
| $K$，$\chi_t$ | 非退化闭二形式矩阵及适配图 | nondegenerate closed two-form and compatible chart |
| $S_h$ | 中央生成函数 | central generating function |
| $E$，$S$，$\mathcal M$ | 总能量，熵，对称耗散算子 | total energy, entropy, symmetric dissipative operator |
| $\varepsilon_B$ | 原场的Birkhoff表示误差 | Birkhoff representation error |
| $\varepsilon_{\mathrm{chart}}$ | 图匹配与数值实现误差 | chart compatibility and implementation error |

引文或归档代码中的R若指Pfaff系数，正式统一稿应改用a；磁场B与Birkhoff标量B_B也分开。姿态与几何约束、机械状态与神经网络输入尺度都不能用同一个符号暗中替换。

适宜的共同章节顺序是：三维模型与能量；磁硬件端口与可实现域；空间离散和ROM；完整复学习及误差；方向A的相容构造、原36、控制和离散收敛；方向B的保守正规形、连续KAM及磁跟踪；多层数值实验；来源与限制。正文保留关键推导，全部旧基准和新算例协议放补充材料。随包的英中LaTeX框架只组织这些已明确的数学对象和待证条件，不将缺失结论补写为已证明定理。

## 10.4 按依赖关系继续推进

下一步先解决已经被实际计算暴露的缺口。第一，磁场近似必须在实际工作域和实际梯度上验收，并把可实现域加入控制器；需要真实线圈几何、匝数、电感／互感、电阻、电源、标定场图和热约束。第二，接触罚参数和血流闭合必须与实验或更高保真模型交叉验证；需要血管壁厚、本构、导管—壁摩擦、流量／压力波形及材料耗散识别。第三，完整杆的状态／力数据进入12自由度或更高ROM的学习，而非长期只用ROM自生成标签；需要观测映射、激励可辨识性及截断误差估计。

方向A在已有12自由度真实三维M(q)上实现高阶一形式输运和数值图，首先验收e_B与图匹配两个独立残差，再加入每步成本、域内非退化与重启相容性。不能把每步任意重置R₀=(p,0)描述为保持一个统一全局结构，也不能把独立逆流得到的结构诊断当作廉价在线算法。

方向B先冻结具有物理可逆Legendre映射的能量类，独立计算三维1:1共振正规形或有来源的破对称谱，再选择具体连续KAM定理、候选环面、复域、扭转和全部常数。可运行的学习／磁跟踪已提供工具，但尚未提供新KAM存在性。完整接触轨迹与KAM分析应在适用的无接触光滑邻域或经过明确证明的其他理论中建立联系，不能将接触删去后声称整个任务已经证明。

微重力的生理适配需要真实任务或经验证的循环模型输入。新增残余g信号不足以代替流量、压力、顺应性和血管几何的变化。若热损耗成为研究对象，再用已经验证的退化结构扩展状态，同时补热容量、导热、血流换热、磁滞与线圈热参数。

## 10.5 复现入口与数据组织

程序包保留 `stage2/program`、`stage2/results`、`stage2/notes` 的相对结构，从解压根目录运行。新代码与已执行数据一起交付，原仓库和上传ZIP的身份通过摘要及入口清单指向，避免混成一个无法区分来源的代码树。具体软件环境分开，不将旧v10的NumPy／Arb依赖强行与新PyElastica和Torch混装。

| 任务 | 入口 | 主要结果与复现要求 |
|---|---|---|
| 新方向A | program/route_a/run_extended.py | 8／16自由度、111条方法—网格记录、初态和每步残差 |
| 一般输运／Moser | program/route_a/transport_moser_check.py | 表示误差、图匹配、辅助流和成本 |
| 原包对照 | program/route_a/replay_supplied.py | 需按README放置已上传的B与整合ZIP；哈希不符应停止 |
| 三维杆 | program/rod3d/run_study.py | 各算例配置、NPZ状态、CSV功率、summary与环境哈希 |
| 完整线圈载荷 | program/rod3d/run_biot_savart.py | 直接在实际杆上使用完整Biot–Savart场及空间导数 |
| 12自由度学习 | program/learning/run_learning.py | 训练、验证、测试、域外、检查点；数据复用身份防护 |
| 新确认集 | program/learning/run_confirmation.py | 冻结权重后新seed，与开发数据零重复 |
| 正质量复网络 | program/learning/train_spd_complex.py | 结构正定性、非零学习误差及额外训练成本 |
| 磁前馈 | program/learning/make_feedforward.py | 四种模型同目标、同约束，实际分配残差 |
| 独立算子核验 | learning/validate_rod_rom.py及rod3d/verify_operators.py | 质量动能、磁虚功、接触势和摩擦功 |
| Metriplectic候选 | program/metriplectic_candidate.py | 32个真实ROM状态上的退化和熵产生代数检查 |
| 旧v10 | notes/v10_baseline.md中的冻结入口和日志 | 需原S1／仓库；本轮结果不替代COMSOL原生重算 |

每个仿真保存初态、参数、求解器、步长、终时、空间网格、误差定义、输入限制、耗时和代码摘要；失败与不合格算例也保留。较大NPZ包含真实数值状态，不是从图片反推的数据。统计和图由JSON／CSV重新生成，不人工填入“合理”的数值。

# 11 文献继承核验与待补资料

第一阶段已逐篇处理的六份PDF继续作为理论基线，本轮未宣称重新独立证明其全部898页。本轮针对v10新增的Haro–Luque、Bounemoura、三维杆实现和磁性材料来源读取对应原始材料，并把适用对象与本项目的新对象区分。以下列出继续写作时应使用的书目信息及证据责任。

| 文献 | 本阶段实际用途与限制 |
|---|---|
| Moser 1962，上传18页俄译，Matematika 6(5):51—68 | 继承原定理及版本说明；二维扭转环域结果不直接适用任意高维耗散杆 |
| Pöschel 2001，A lecture on the classical KAM theorem，PSPM69:707—732，DOI 10.1090/pspum/069/1858551 | 保留参数版KAM条件与讲义勘误；2009为arXiv归档年，不是正式刊年 |
| Kuksin 1993，Nearly Integrable Infinite-Dimensional Hamiltonian Systems，LNM1556，DOI 10.1007/BFb0092243 | PDE极限的候选工具，谱／正则化条件尚未对三维多物理杆建立；原稿1998应纠正 |
| Chen、Matsubara、Yaguchi 2022，AAAI36(6):6322—6332，DOI 10.1609/aaai.v36i6.20582 | 保留学习到KAM的问题意识；详细报告指出的覆盖界和范数桥梁缺口不能被小损失替代 |
| Shang 1999，KAM theorem of symplectic algorithms for Hamiltonian systems，Numer. Math.83:477—496 | DOI 10.1007/s002110050460；上传首页旧DOI另存；解析辛映射、扭转、Cantor频率及步长条件仍必需 |
| Feng、Qin 2010，Symplectic Geometric Algorithms for Hamiltonian Systems | DOI 10.1007/978-3-642-01777-3；第15章3.5、4.1、4.4、4.5支撑生成图路线，书中符号／系数问题按详细报告修正 |
| Haro、Luque 2019 | 原v10冻结证书实际调用的后验定理；本轮核对原始假设、常数表、代码并重跑，不移植为新模型证书 |
| Bounemoura 2016 | 已认证非退化Liouville环面邻域的KAM稳定性；不证明任意工作域的数值分类比例 |
| Gazzola等2018及PyElastica官方实现 | 三维杆的几何、材料姿态、外力接口；开放系统及伸长重标度下不可只凭Verlet名称断言辛性 |
| Tong等2025 | 长度、半径、材料模量、远端磁段和线磁矩密度的来源；不提供本轮密度、耗散、血流或空间站数据 |
| Coquinot、Morrison 2020 | 总能量、熵、对称括号与退化的理论依据；原对象为扩展磁流体，不是本机器人模型的直接证明 |
| Womersley 1955 | 脉动直圆管解析闭合及相位滞后的依据；向弯管局部映射仍非完整FSI |

待补的文献／数据不是一份笼统“以后再找”的清单，而与具体结论相连。若要引用Shang 2000的独立终刊定理或Su–Qin／Su–Sun–Qin–Scherer的最终版本，应补齐相应原始PDF并逐条核对，不能仅凭B包或专著二手转述。若要把当前工程Hertz型罚律称为真实壁接触，则需导管—薄壁接触的材料、几何及实验来源。若要补完整Morison惯性、近壁润滑或非牛顿FSI，则需相应系数与适用Re／Wo域，并避免与牵引积分重复计力。任何新三维KAM声明还需要一个选定定理的完整定量核验档案，尚无可用参数可以由旧证书代填。

## 11.1 本报告直接引用的主要原始来源

[R1] M. Gazzola, L. H. Dudte, A. G. McCormick, L. Mahadevan. Forward and inverse problems in the mechanics of soft filaments. Royal Society Open Science 5 (2018), 171628. DOI: 10.1098/rsos.171628. 作者组全文：https://www.cosseratrods.org/publications/pubs/2018_RSOS.pdf 。

[R2] D. Tong, Z. Hao, J. Li, B. Sun, M. Liu, L. Wang, W. Huang. Real-time simulation enabled navigation control of magnetic soft continuum robots in confined lumens. Journal of the Mechanics and Physics of Solids 203 (2025), 106198. DOI: 10.1016/j.jmps.2025.106198. 机构存档：https://eprints.ncl.ac.uk/306197 。

[R3] À. Haro, A. Luque. A-posteriori KAM theory with optimal estimates for partially integrable systems. Journal of Differential Equations 266(2—3) (2019), 1605—1674. DOI: 10.1016/j.jde.2018.08.003. 作者预印本：https://arxiv.org/abs/1711.05515 。

[R4] B. Coquinot, P. J. Morrison. A general metriplectic framework with application to dissipative extended magnetohydrodynamics. Journal of Plasma Physics 86 (2020), 835860302. DOI: 10.1017/S0022377820000392. 作者全文：https://web2.ph.utexas.edu/~morrison/20_morrison_BC.pdf 。

[R5] K. Feng, M. Qin. Symplectic Geometric Algorithms for Hamiltonian Systems. Springer, 2010. DOI: 10.1007/978-3-642-01777-3. 本报告沿用已上传全文与第一阶段校勘。

[R6] Z. Shang. KAM theorem of symplectic algorithms for Hamiltonian systems. Numerische Mathematik 83 (1999), 477—496. DOI: 10.1007/s002110050460.

[R7] A. Bounemoura. Non-degenerate Liouville tori are KAM stable. Advances in Mathematics 292 (2016), 42—51. DOI: 10.1016/j.aim.2016.01.012. 作者预印本：https://arxiv.org/abs/1412.0509 。

[R8] T. Lunnoo, T. Puangmali. Capture efficiency of biocompatible magnetic nanoparticles in arterial flow: a computer simulation for magnetic drug targeting. Nanoscale Research Letters 10 (2015), 426. DOI: 10.1186/s11671-015-1127-5. 只用于核对所述流体物性尺度及其语境。

[R9] J. R. Womersley. Method for the calculation of velocity, rate of flow and viscous drag in arteries when the pressure gradient is known. The Journal of Physiology 127(3) (1955), 553—563. DOI: 10.1113/jphysiol.1955.sp005276.

[R10] 用户提供的1025三个DOCX、118页和56页审查、一般Birkhoff ZIP及当前／较早整合ZIP；GitHub仓库 https://github.com/mop74720-commits/IJRR_CHNN_KAM_v10_20261007 。本轮读取的精确提交、原始文件摘要及冻结科学输入见版本清单和各复算日志。