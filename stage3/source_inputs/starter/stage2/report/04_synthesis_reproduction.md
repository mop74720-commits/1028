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
| $x=Dz$ | 仅用于统计训练的归一化输入 | statistical input normalization, not a canonical chart |
| $\xi$及$\overline\xi$ | 复输入及其共轭 | complex and conjugate-complex inputs |
| $\phi(q)$，$G_m$ | 磁通／势特征，磁广义力端口 | magnetic potential features and generalized-force port |
| $a_i\,dz_i-B_B\,dt$ | Pfaff一形式 | Pfaffian one-form |
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
