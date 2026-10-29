# GitHub v10 原始基准读取与可复算性核查

本文件是第二阶段的持续核查记录。当前已完成原 GitHub v10 主稿与补充稿的全文研究、主要计算链实现读取、S1 下载和输入身份锁定，以及下文明确列出的隔离复算。最新整合稿按其实际源码逐式对照。本轮复算是旧参数、旧冻结模型的基准核验，不是新三维血流—磁驱动—接触模型的证书。未复跑的历史结果均单独标明。

## 1. 基准身份与可访问性

- 官方仓库：https://github.com/mop74720-commits/IJRR_CHNN_KAM_v10_20261007
- 读取日期：2026-10-29 UTC。
- 本地只读审查副本：`stage2/sources/v10_original/`；没有修改上游或推送。
- 当前 `main` / `HEAD`：`8761d70239a54985b40c0a6196f52e53d5b2e4d2`，提交时间 `2026-10-17T22:42:22-07:00`，消息 `Add verified S1 original and directory subset downloads`。
- 发布标签 `v10-20261008`：`82519542dd057e8fbd6d6879ef33217761e8cbbb`，提交时间 `2026-10-17T22:12:00-07:00`。
- 两次提交之间仅有 `README.md`、`reproducibility/ARTIFACT_INDEX.md` 和 `verification/package_s1_exports.py` 的下载/打包说明变更；论文、实验与既有计算结果未改变。
- 发布页：https://github.com/mop74720-commits/IJRR_CHNN_KAM_v10_20261007/releases/tag/v10-20261008 ，官方 API 记录发布时间 `2026-10-18T05:14:33Z`。文件名/文稿日期 2026-10-08 与 GitHub 发布时间不是同一概念。
- 普通沙箱网络请求因本地代理不可达失败；只读网络提权获准后 `git ls-remote`、克隆和官方 API 访问成功。网页浏览工具对指定 GitHub 页面返回 `DisabledError`，故这里的身份结论依据实际 Git 与官方 API 原始响应，并非搜索摘要。

官方元数据与逐文件 SHA-256 清单保存在 `stage2/sources/v10_metadata/`。当前仓库共有 182 个受版本控制文件、139101680 字节；未发现仓库 `AGENTS.md`。

## 2. 当前可用结构

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

## 3. 已读主稿的初步对象区分

1. 匹配实/复实现的学习比较使用两模态 Galerkin 合成轨迹、受控导数噪声和同一实系数函数类；其“复”实现不是额外物理状态，也不自动带来准确性优势。
2. 有限幅值 KAM 证明使用独立的两模态 COMSOL 状态积分辨识，目标函数包含完整余弦和可依赖动量的四次残差。
3. 全 FE COMSOL 的位置—速度增量辨识是另一组拟合，用于预测和 S 路径控制；其系数不可替代 KAM 证书中的系数。
4. 64 模态结论是同一平面梁的完整有限元控制提升，并非三维杆加血流接触的证书。
5. 本轮将分别追踪连续时间环面存在、数值积分结构/收敛、有限时域净空与跟踪。这些结论不会互相替代。

## 4. 阅读覆盖和证据层次

原 GitHub 的 `main.tex`、五个 `core_*.tex`、`supplement.tex`、参考文献与补充所有分节已阅读全文；`stability_boundary.tex`、`operational_tolerances.tex` 由本任务子代理完整读取，其余由本代理直接读取。主稿 15 页、补充 45 页。原 S1 内历史稿不作为当前 v10 的替代版本；实现和数据按当前稿指向的原始路径读取。

已直接完整读取的核心实现包括：`feature_model.py`、`unified_model.py`、`beam_assembly.py`、`run_learning.py`、`run_integrator_check.py`；`arb_hamiltonian.py`、`hl_constants.py`、`verify_torus.py`、`torus_arb_refine.py`；`certify_integral_learning.py`、`validate_fitted_torus.py`、`audit_integral_chain.py`；`kam_magnetic_control.py`、`certify_kam_lift.py`、`run_s_path.py`、`run_safety_validation.py`；`run_robustness.py`、`run_causal_adaptation.py`。另由子代理完整读取 S2 稳定性扫描和误差容限的六个 Python 脚本。生成图片、打包、COMSOL Java/MATLAB 构建脚本和其余辅助脚本，不能以这份核心实现核验代称逐行独立复证；运行覆盖见第 8 节。

对最新整合稿，直接阅读英文主文的背景、力学、Birkhoff/生成格式、受控分析、KAM、双路线接口、应用和结论，以及完整读出、Central4 和映射 KAM 对应补充段；公式号由随包中文 `main.aux` / `supplement.aux` 核实。数值实验与一般 Birkhoff 全套实现另由团队对应代理负责。本文件不把旧复算冒充最新整合包的复算。

第一阶段依据以用户新增的 118 页详细报告 `stage2/notes/1025_stage1_detailed.md` 第 13–15 章为主。已再次对照其中 HNN 覆盖数/范数桥梁、Shang 原定理，以及 Feng–Qin 第 13 章的 exact symplectic、步长共振与 Cantor 频率条件；56 页报告仅作交叉参照。

## 5. 原 v10（1）–（19）与最新整合稿逐式差异

此处“原”仅指 GitHub v10 主稿；不是 1025 手稿的公式编号。1025 原（36）、GitHub v10 原（36）以及整合稿现（36）必须分开。最新版说明也明确：1025 原（36）对应整合稿普通中点现（35），现（36）是矩阵消元，Central4 是现（42）。

分类：**M** = 数学/物理条件必须补齐；**P** = 参数或模型改变后必须重算；**O** = 展示顺序/移入补充，无须改动正确公式；**R** = 原实验或实现应恢复为独立基准，再在新模型上重建。没有任何一项要求永久把研究目标缩小为两模态。

| 原号及稳定标签 | 原式的作用 | 最新整合对应 | 核验与处置 | 受影响实验 |
|---|---|---|---|---|
| （1）`eq:core-beam-balance` | 小斜率 Euler–Bernoulli 内部方程、根部夹持、自由端剪力零、完整余弦磁矩 | 现（5）`mech:beam` +（6）`mech:endpoint-balance` | 原式对无端质量、无横向力的声明模型成立。新稿加入端质量 $m_t$、转动惯量 $J_t$ 和力 $F$，应使用新自然边界；这是 P，不能反向指称原简化模型内部矛盾。三维 Cosserat 必须另行建立，不由端部惯量补丁获得。 | 全部频率、学习数据、磁驱动和高模态响应重算 |
| （2）`eq:core-fe-energy` | $M\ddot q+\alpha M\dot q+Kq$ 与 $H_0$ 同一能量 | 现（7）FE +（8）能量 +（9）功率 | 原式正确。新 $M_f=M_{beam}+m_te_we_w^T+J_te_\vartheta e_\vartheta^T$，新 $E_0$；加入 $F\dot w$ 功率。P；更一般 $M(q)$ 须保留 $p^T(\partial_qM^{-1})p/2$，是 M。 | FE、净空、输入功、全部数据 |
| （3）`eq:unified-scale` | $a_j=\sqrt{E_0/(\omega_0\omega_j)}X_j$，$\pi_j=\sqrt{E_0\omega_j/\omega_0}Y_j$ | 现（11）`mech:scaling` | 正则时间—能量缩放正确；一般 $n$ 模态仍成立。现稿明示有效质量 $\mathsf N^{-1}$。P，保留公式。 | SI 输出、训练域、所有幅值和场需求 |
| （4）`eq:unified-h` | $h_*=\frac12\sum\nu_j(X_j^2+Y_j^2)+g(d^TX)$，$g=1-\cos s-s^2/2$ | 现（13）标称 $h_0$；现（44）四个能量 | 减二次项避免偏置刚度重复计数。结构原样保留，$h_*$ 改称 $h_0$ 是 O；新的真实残差 $R_*$ 是新增模型，不与原物理目标混称。P。 | 学习目标、正规形、磁补偿 |
| （5）`eq:core-complex-chart` | $\zeta=(X+iY)/\sqrt2,\chi=(X-iY)/\sqrt2$ 及逆变换 | 现（15） | 相同。O；不是减少物理状态数。 | 全部实/复特征与导数比较 |
| （6）`eq:core-complex-energy` | 在独立 $\zeta,\chi$ 中的完整余弦能量 | 现（16）、KAM 现 `kam:complex-energy` | 相同；真实切片 $\chi=\bar\zeta$ 与复域独立变量须区分。不是 $\zeta$ 单变量全纯。O/P。 | 全解析 KAM 范数和神经架构 |
| （7）`eq:core-complex-canonical` | $\{\zeta_j,\bar\zeta_k\}=-i\delta_{jk}$，$\zeta'=-ih_\chi$ | 现（17） | 符号与 $\sqrt2$ 因子正确。O。 | 自动微分、复网络解码 |
| （8）`eq:fragment-decoder` | $X'=h_Y$，$Y'=-h_X-\partial_v\mathcal D+u d\cos\vartheta$ | 现（18）改为一般 $U$，现（20）实磁端口 | 更一般输入是有用扩展；原单均匀场只有一个方向。含动量残差时 $v=h_Y$，不能偷换为 $\mathsf NY$ 或把 Rayleigh 力换成 $-\gamma Y$。M；35 参数模型要恢复。 | 完整 CHNN、耗散、跟踪、磁控制 |
| （9）`eq:fragment-power` | $h_\eta'=-v^T\partial_v\mathcal D+u\cos\vartheta\,d^Tv$ | 现（19）改为 $v^TU$ | 完全一致的端口功率。新流体、接触、基座运动与参数时间变化需增加相应功项，不能只移换系数。M/P。 | 功率闭合、净空、Metriplectic/端口分支 |
| （10）`eq:core-complex-dynamics` | 复坐标非保守修正 $i[-\partial_v\mathcal D+u d\cos\vartheta]/\sqrt2$ | 现（19）后的行内公式 | 公式仍保留，只失去独立编号。O，可恢复编号以便审查；$h+i\mathcal D$ 仅双读出包装，不是该流的普通复 Hamiltonian。 | 学习架构和结构主张 |
| （11）`eq:core-central-map` | $x_+-x_-=J\nabla S_\Delta(m)$ | 现（38） | 原样保留。原正则保守分支正确，不需要为引入 Birkhoff 而删除。 | 中点与 Central4 |
| （12）`eq:core-midpoint-expansion` | 时间中点与端点平均的区别 | 补充（S73）`ss:central-taylor` | 移到补充，O；推导的 $1/8$、$1/24$ 必须保留。 | 四阶证明 |
| （13）`eq:core-exact-displacement` | $\Delta f+\Delta^3(f''[f,f]-2(f')^2f)/24+O(\Delta^5)$ | 补充（S74） | 原样正确，O。遗漏 $-2(f')^2f$ 会破坏四阶，不得以两模态便算为由删去混合项。 | 非可分完整 Hamiltonian 的四阶验证 |
| （14）`eq:core-generator-identity` | $J\nabla(f^Th''f)=f''[f,f]-2(f')^2f$ | 补充 S2.9 无编号等式 | 原样正确，O；依赖常数正则 $J$，一般变结构矩阵不能直接照搬。M 为适用域声明。 | 三维经正则约化后的高阶格式 |
| （15）`eq:core-central-generator` | $S_\Delta=\Delta h+\Delta^3 f^Th''f/24$ | 现（42）`struct:central4` | 已保留，O。带反馈的四阶版本必须把实际闭环 Hamiltonian 代入全部导数；后加任意控制增量不能承接此证明。M。 | 控制后的四阶与离散 KAM |
| （16）`eq:central4` | 用 $g_\Delta=J\nabla S_\Delta$ 的完整隐式更新 | 现（38）+（42），补充（S76）专门固定动能势能式 | 一般式等价保留，但新专门显式式不覆盖动量四次项。需恢复一般 $g_\Delta,Dg_\Delta$ 实现作为 R。 | 原 GC17 非可分训练模型、未来完整 CHNN |
| （17）`eq:core-central-newton` | Newton 矩阵 $I-\frac12Dg_\Delta$，用至四阶能量导数 | 现（36）后只明写普通中点 $I-\Delta Df/2$；Central4 在补充 S2.10 给专门导数 | 中点 Newton 不是一般 Central4 Newton。应明确恢复原式（17）及其残差定义，属 R/M；已有公式不必变。 | 高阶求解容差、Jacobian、非可分模型 |
| （18）`eq:core-step-tangent` | $(I-C)^{-1}(I+C)$，$C=JS''/2$ | 现（40）`struct:cayley`；现（41）新增 exact primitive | 保留正确 Cayley 证明；新增 exact symplectic 直接支撑离散 KAM。M 是区分理想隐式映射与有限容差输出，不是推翻原辛性。 | 结构误差、映射 KAM |
| （19）`eq:core-linear-phase` | $2\arctan(a/2)=\nu\Delta-(\nu\Delta)^5/120+O(\Delta^7)$ | 补充（S75） | 原样保留，O；线性相位检查仅是算例，不把 $H=\nu I$ 称为有扭转 KAM。 | 数值阶、相位误差 |

### 5.1 可直接保留的中央生成推导

设 $x_0=x(t+\Delta/2)$、$m=(x_++x_-)/2$、$f=J\nabla h$。Taylor 给

$$m=x_0+\frac{\Delta^2}{8}f'f(x_0)+O(\Delta^4),\qquad x_+-x_-=\Delta f(x_0)+\frac{\Delta^3}{24}(f''[f,f]+(f')^2f)(x_0)+O(\Delta^5).$$

代入 $x_0=m-\Delta^2f'f(m)/8+O(\Delta^4)$，得到原（13）的系数 $1/24-1/8=-2/24$。再令 $A=h''$，$f'=JA$，则

$$\nabla(f^TAf)=h^{(3)}[f,f]+2(f')^TAf=h^{(3)}[f,f]-2AJA f.$$

左乘 $J$ 即原（14），因此原（15）–（18）都可用于一般平滑的正则、自治 Hamiltonian，而非仅二模态梁。四阶有限时收敛还要工作域内足够高阶导数、局部分支唯一、全局误差稳定性；若每步增量残差为 $\eta_\Delta$，总误差具有 $C_T(\Delta^4+\eta_\Delta/\Delta)$ 的形式。对真实耗散/一般 Birkhoff，则应先用相容坐标或专用几何积分，不把该正则公式原封不动用于任意 $J(x,t)$。

## 6. 原“完整 CHNN”究竟实现了什么

### 6.1 实际计算图、特征数和求解器

原 `feature_model.py` 枚举四个实坐标的全部二次（10 个）和四次（35 个）单项式。复实现确实形成 $z_1,z_2,\bar z_1,\bar z_2$，取共轭成对单项式的实部/虚部，并用复指数计算磁项；并非简单把实数组改名。但隐层特征和其线性变换 `TRANSFORM` 是固定的。已知二次能量分支的实际函数类为

$$h_\eta=h_2+a\,g(d^TX)+m_4(X,Y)^TU_Fc,\quad c\in\mathbb R^{34},\quad U_F\in\mathbb R^{35\times34},$$

其中 $v_4$ 是 $-(d^TX)^4/24$ 的实系数向量，$U_F$ 张成 $v_4^\perp$，训练特征为 $F=(g/\|v_4\|_2,U_F^Tm_4)$。因此参数是 $\eta=(a\|v_4\|_2,c)\in\mathbb R^{35}$。无先验分支再学习一般二次项，45 个有效实参数。实/复分支使用同一实函数类和同一实参数正则，不存在预设的复网络容量优势。

`run_learning.py` 的 `fit_labels` 把梯度特征叠成矩阵，用 `np.linalg.lstsq` 解带 $10^{-14}$ 二次正则的增广最小二乘。它没有 Torch，没有可训练复隐层，没有反向传播训练整个深网。补充稿讨论的共享复隐层和双读出，以及复梯度下降命题，是可扩展理论，不是这些数值实验的真实训练过程。原文自身在 `complex_theorem_note.tex` 最后也明确：实验读出由线性最小二乘拟合。

这并不意味着“没有学习”：35/45 个读出系数确实由数据估计，且含全部混合和动量四次方向。正确称呼是**具有固定解析特征的复 Hamiltonian 读出辨识**。新加入可训练复网络应作为新增模型，与该解析特征基准用相同数据划分、参数/计算预算和物理指标比较；不能回写为原 v10 已经训练过深层 CHNN。

### 6.2 动量项与耗散/物理实现

若 $h_\eta$ 含 $X,Y$ 混合项，物理速度是 $v=h_{\eta,Y}$，Rayleigh 模型

$$\mathcal D_\gamma(v)=\frac\gamma2v^T\mathsf N^{-1}v$$

产生 $-\gamma\mathsf N^{-1}h_{\eta,Y}$，一般不等于 $-\gamma Y$。原训练先冻结保守读出，再以非负一元最小二乘估计 $\gamma$。最新整合单势能分支满足 $h_Y=\mathsf NY$，所以线性动量阻尼和联合线性辨识成立；将其 36 列设计推广到完整动量读出时，若保留速度型 Rayleigh，阻尼与能量系数产生乘积，联合问题一般不再线性。最新补充 S2.15 已正确提醒这一点。

对于一般已学保守参考，必须在 $h_{YY}$ 可逆的域内解

$$h_Y(X,\widetilde Y)=\frac{\dot a}{\omega_0S},\qquad \ddot a^{ref}=D_s\omega_0^2(h_{YX}h_Y-h_{YY}h_X).$$

这就是原 64 模态环面提升实际使用的 Legendre 反解和完整 Hessian。单势能残差补偿 $U=\widehat\gamma Y+\nabla\widehat R(X)$ 不能直接承担这项任务。

### 6.3 三份冻结学习对象必须分开

| 对象 | 数据与拟合 | 实际用途/结果边界 |
|---|---|---|
| Python GC17/43/91，GR/BR/BC 对照 | 每种子 12 条 4 s 两模态轨迹、129 时点；状态无噪声，导数均匀噪声 $\pm10^{-6}$；8 条独立 16 s 测试。另有 $10^{-8},10^{-9}$ 噪声拟合 | 实/复及先验配对比较、200 s 续算、GC17 Central4。目标恰好在特征类内；不能代表实体精度。 |
| 全 FE COMSOL q/v 积分拟合 | 4 条训练+2 条测试；每 0.004 s 采样、9 点 Newton–Cotes、500 个 0.032 s 窗口；35 参数，$a=1.0223248822$ | 文件 `learning/raw/comsol_identification_refined/qv_integral_fit.npz`，SHA `e3be5105300d01ffb9250ea9901c54b501f1c91be22dde1fac8e294225862bb7`；S 路径与预测，另有其自身后验环面。较小预测误差可能吸收求解器色散；不能以求解器容差充当严格观察缺陷。 |
| 两模态 COMSOL 短轨迹积分拟合 | 64 条短轨迹、每条 17 状态；端点匹配的八次精确二进有理曲线；有单独验证的积分缺陷、Gram、能量解析误差 | `mainline_completion/integral_certificate/comsol_integral_certificate_fit.npz`，SHA `a9bc1c23a811d1200b42ea4ff065e1d455e49d3dc33177e2e5d653dd581a8b85`；主误差→KAM、主约 1.9 mm 环面、主 64 模态提升。是本轮复算证书对象。 |

旧四种匹配模型的实/复结果在已分辨精度内相同，不能写成复表示普遍更优。原 S 路径的静态逆前馈还比完整 CHNN 跟踪误差更小，因此也不能用该算例证明 CHNN 优越性。

## 7. 原后半段与最新整合稿的具体恢复/修正表

最新版改变了物理参数：$E:5\to2.1$ MPa、$\rho:1100\to1028\ \mathrm{kg/m^3}$、$\mu:2.0\times10^{-5}\to1.77184214\times10^{-5}\ \mathrm{A\,m^2}$，加入磁芯质量与惯量；$\omega_0:11.41728728\to7.84000916$ rad/s，$d:(0.22567077,0.32179881)\to(0.30722439,0.45042632)$，$E_0:6.0\times10^{-7}\to5.31552642\times10^{-7}$ J。新材料来源和端部惯量是独立建模选择；**参数更换本身足以要求重新训练和重新认证，但不能证明旧数学/实验应被删除**。

| 主题 | 原 v10 实际内容 | 最新整合实际状态 | 必须修正/仅顺序与恢复建议 | 需要重建的实验 |
|---|---|---|---|---|
| 完整 CHNN | 35/45 系数、混合/动量项、实/复及先验 2×2 对照、三种子 | 主计算只有 $\beta_*=0.2$ 的单磁势特征+标量阻尼；35 参数仅补充（S86）–（S88） | 缩窄不是数学必要。恢复原固定特征基准；新增真正可训练复网络应明确新贡献。 | 新域激励、训练/验证、Gram、导数误差、损耗与复杂度 |
| 非可分 Central4 | GC17 完整余弦+全部动量四次项，四阶/辛缺陷/独立差分 Jacobian | 一般公式保留，新数值主要标称固定动能势能 | 顺序调整可接受，不能用可分专门导数替代完整实现。 | 新完整读出的四阶导数、牛顿分支和残差 |
| 非零损失→解析误差 | 三类数据清楚分开；主证书有独立物理轨迹缺陷与 Gram 下界 | 公式同类，单特征无噪声真值诊断；独立观察缺陷与 KAM 阈值未认证 | 学习界应保留确定性路线，不能调用有问题的 HNN Theorem 8/11 补缺。 | 实/复复域范数、缺陷/类误差、采样和观察器 |
| 四阶正规形与扭转 | 旧 $A_{jj}=-d_j^4/8,A_{ij}=-d_i^2d_j^2/4$，完整余弦+Lie 余项 | 新扭转重新计算；双路线 $\kappa=1,1.2$ 分别预算 | 正确新增：区分 $h_c$ 与 $\widehat h$，余项含 $\kappa^2$ 不能只线性缩放。维数可推广，不能宣称任意3D已近可积。 | 新频率小除数、完整正规形、域包含与误差预算 |
| 有限幅值环面 | 7 个旧冻结 Hamiltonian 的后验计算；主短轨迹拟合约 1.898 mm | 明确声明未完成新参数认证 | 旧证据应恢复为独立基准，不搬用频率/Fourier 系数/阈值。新参数需要新候选和域。 | Fourier 候选、解析尾项、扭转、全部定理常数 |
| 局部正测度与宽域诊断 | 另有 $w=10^{-220}$ 管状域严格比例，以及 1024/1024 有限时分类 | 没有恢复这些数值；只保留条件性 KAM | 不能把 99.6404% 置信下限当 KAM 体积；管厚远小于可分辨嵌入误差。旧管坐标 exact 修辞需改，见第9节。 | 新域 measure、独立分类与积分细化；不是优先替代真实机器人指标 |
| 64 模态磁实现 | 两实磁端口精确实现已学低模态加速度；62 个高模态稳定响应图，严格全相位包络；12 s 动力学和 COMSOL在线反馈细化 | 保留条件性提升定理，但 $4/8/64$ 闭环全列计划 | 理论保留且应恢复旧验证。低二维环面不是128维 Hamiltonian正测度结论；不代表两个端口能任意驱动64模式。 | 新端口矩阵、完整角度、Legendre域、高模态强迫/启动、执行器分配 |
| 全杆净空 | 连续能量不等式+实际磁功 governor；全64自由度数值、主动限功、零阻尼、COMSOL闭环 | 理论扩到 $(F,B_y)$ 两端口；新控制未启用，初始能量12.6567 nJ高于9.5187 nJ cap | 功率/残差能量条件必须补齐。初始能量超cap时不能援引该安全不变集；不应删除 governor 数值验证。 | 新安全初态、物理全输入功、流体/壁/基座能量、限幅和测量误差 |
| S形跟踪 | 64自由度、全FE训练权重、实际尖端反馈、单横向场、独立轴向基座馈入；16s场回放COMSOL | 新稿 Route B 为已学保守参考的两模态跟踪；未恢复原S任务 | 两种任务不同。S形端点轨迹不是S形静态杆形；不是插入长度改变，更不是血管中真实推进。恢复任务须新增血流/接触/馈入功。 | 固定控制器4/8/64/3D、相同输入约束与对照、全杆接触 |
| 未建模物理/状态噪声 | 64自由度产数、4模态辨识；未知E/磁矩、静流二次拖曳、梯度保守势、噪声、独立COMSOL | 主单系数实验没有恢复 | 有价值的过渡验证，应保留与新3D升级；静止流体拖曳不是脉动血流。 | 新血流、观测噪声/系统激励、参数可辨识与截断残差 |
| 因果慢变适应 | 29s完整FE轨迹，过去4s窗口估计，六次未来1s预测；常数和仿射趋势 | 未恢复 | 是预测实验而非一般在线学习/闭环证明；参数变时功率必须含 $\partial_tH$，不能承接自治 KAM。 | 新高维适应与冻结验证、耗散结构和功率 |
| S2受迫稳定边界 | 1715个两模态启动/延续记录，30个4/8模态精查，有限全FE检查 | 新稿一般格式/控制对照不同 | 没发现混沌不能称全局不存在混沌或KAM破裂阈值。可保留旧协议，不把扫描结果移植。 | 新频段、强迫/阻尼/接触、变分方程与步长细化 |
| S2误差容限 | 4s非零启动、测量/执行误差的净空实验，使用物理功率误差预算 | 新稿只给条件/计划 | 与精确环面证明分离；governor长期激活会明显改变请求轨迹。 | 新不确定性预算与执行器/传感校准 |

## 8. 本轮实际复算、冻结对象与计算环境

### 8.1 隔离环境

`stage2/venvs/v10_baseline/bin/python` 使用 NumPy 1.26.4、SciPy 1.13.1、Numba 0.60.0、Matplotlib 3.9.2、threadpoolctl 3.6.0、python-flint 0.9.0、SymPy 1.13.3。旧 S1 核心不需 Torch。未修改全局 Python 或原始源码；只复制已审查脚本及所需冻结输入到 `stage2/runs/v10_s1/reproducibility/`，逐项源/副本 SHA 记在 `input_copy_manifest.json`。未加载原包 `vendor` 的平台二进制；使用 Linux python-flint 正式包。

所有复算设 `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMBA_NUM_THREADS=1`；Numba/Matplotlib 缓存位于隔离运行目录。没有执行未知下载脚本，没有重新训练或改变候选环面。

### 8.2 已完成复算

| 复算 | 实际入口/参数 | 本轮结果 | 时间与边界 |
|---|---|---|---|
| GC17 完整 Hamiltonian 中点/Central4 | 隔离 `unified_model/integrator/run_integrator_check.py`；原初态 $(0.1,0.06,0,0.02)$，$\tau=10$，$\Delta=0.08,0.04,0.02,0.01$ | 六项检查通过；Central4末端误差依次 $1.8345544\times10^{-3},1.1783725\times10^{-4},7.4149058\times10^{-6},4.6421587\times10^{-7}$；阶 $3.96056,3.99022,3.99756$ | 2.21158 s；旧 Python GC17，不能称主COMSOL积分拟合或新基准 |
| 主 COMSOL积分学习证书 | 隔离 `certify_integral_learning.py --data ../comsol/comsol_two_mode_observations.mat`；未用 `--refit`；256-bit Arb | 非零MSE约 $3.6030685\times10^{-23}$；Gram最小特征值下界 $2.9302565\times10^{-7}$；系数误差 $2.3804786\times10^{-8}$；twist误差 $1.0376266\times10^{-7}$；$r=0.3$ 解析能量误差 $1.3309393\times10^{-9}$；全部检查通过 | 0.67132 s；权重 SHA `a9bc...b85`；数据 SHA `cd4bbb57d5549e69fc37bf90586e882818a24cda642ce74e17f0ba58210e517a` |
| 同一主拟合的有限幅值环面 | 隔离 `validate_fitted_torus.py verify`；512-bit Arb；256×256残差格、128×128扭转格；冻结 Fourier 候选 | 全检查通过；$\|E\|_\rho<2.7309550\times10^{-77}$；扭转平均逆范数 $<80525.201$；Haro–Luque小量 $<0.031724$；嵌入修正 $<2.089396\times10^{-41}$ | 25.51325 s；候选压缩 SHA `83e6e4cf57fac5e5735f32b8c33db2a1ec2e384958a5aa137ada6f567a81d3d9`；只证明旧冻结两模态保守 Hamiltonian |
| S2档案独立重算 | 子代理从原 NPZ/JSON重算谱半径和功率/形状指标，核对58个扫描文件及5个容限输入SHA | 1715个存储单周期矩阵的谱半径与原记录差 $\le1.33227\times10^{-15}$，全部 $<1$；容限的能量、空间极值、限功激活率与细化一致 | 0.367 s；是原输出独立审计，不是重积分1715个ODE |

命令、返回码、耗时、标准输出和错误输出分别记录在 `stage2/runs/v10_s1/{integrator_run,integral_run,torus_run}.json` 及同名前缀日志。S2独立审计为 `stage2/runs/v10_s2/independent_archive_audit.json`，实现阅读与边界报告为 `stage2/notes/v10_s2_repro.md`。

### 8.3 尚未重新执行的历史项目

本轮没有重新执行 COMSOL原生求解、旧Python训练参考轨迹的重新产数、200 s长续算、七个不同Hamiltonian的全部环面、1024条717.5s分类轨迹、1715个受迫ODE扫描。S路径全部原控制组，以及35/45特征三种子重训和16 s留出预测，已于追加复算执行，见下文。其余源码/原输出可用不等于本轮已复跑。COMSOL专有运行时还需单独检查；本轮没有假定其可用。

### 8.4 追加复算：冻结64自由度提升、S路径与净空边界

**64自由度仍指平面梁的有限元自由度。** 本轮追加执行 `stage2/runs/v10_s1/recheck_frozen_lift.py`，调用未经修改的原 `certify_kam_lift.py`，使用本轮重新通过的主 COMSOL 积分拟合环面证书。原脚本会重新求解特征值问题；为让证书对象确实是原冻结模态模型，wrapper 只把 `MagneticBeam` 构造返回值替换为原存档的精确数组，未改变提升方程、界估计或输入限制。八项模态数组逐项、逐位相同，见 `frozen_modal_identity.json`；原 NPZ 的 SHA-256 为 `c0477f4400e514ff122e7a50475a6dbba9c5bf7751870bd8e593c32e1380520b`。NPZ 容器重新打包后的文件哈希可不同，故不能仅比较压缩容器哈希判断数值身份。

单线程运行 1.03387 s，全部原检查通过：Legendre Hessian 下界大于 $0.999999998366247$；全杆图像位移界约 $1.922696$ mm，含启动瞬态界约 $1.970263$ mm；所需横向磁场界约 $0.921665$ mT，梯度界约 $0.025726$ T/m。该结论是旧冻结平面模态方程的低维环面加稳定受迫高模态图像，不是新三维有限元或真实血管动力学的环面证书，也不是128维相空间内正体积的环面族。命令/耗时/检查见 `frozen_lift_run.json`、`frozen_lift_stdout.log` 与 `frozen_comsol7_rechecked.json`。

**S路径全部五组已实际重积分。** 原 `run_s_path.py --case all` 不修改源代码，使用原全 FE COMSOL 位置—速度拟合，而非主短轨迹 KAM 拟合。总耗时 12.63690 s；原定2–14 s弯曲行程区间的误差均由本轮原始状态重新统计：

| 控制组 | 横向尖端轨迹 RMS 误差 | 相对于原档案的最大尖端位置差 |
|---|---:|---:|
| 完整 CHNN 读出与物理反馈 | $6.418803$ μm | $1.48584\times10^{-11}$ m |
| 二次 Hamiltonian | $6.207384$ μm | $1.48791\times10^{-11}$ m |
| 静态前馈 | $4.124012$ μm | $6.79924\times10^{-12}$ m |
| 模态反馈 | $25.308195$ μm | $1.62414\times10^{-11}$ m |
| CHNN 更紧积分容差 | $6.418803$ μm | $1.48584\times10^{-11}$ m |

静态前馈在这组既定工况下误差最小，二次 Hamiltonian 也略优于 CHNN。因此该旧实验不支持“学习控制在S路径上普遍优于解析/静态对照”。可以据此设计新3D工况的非线性、扰动与外推检验，不能删除不利对照。五组 governor 均未触发，故不能把这组跟踪结果当作主动限功工作时的跟踪性能。CHNN组全杆最大横向位置约 $1.488917$ mm、场峰值约 $12.917656$ mT、数值功率平衡残差约 $2.434\times10^{-18}$ J。数据和独立统计为 `s_path_run.json`、`s_path_independent_comparison.json` 及隔离输出 NPZ；COMSOL 场回放没有重新执行。

**净空重积分仅完成五个普通算例。** 原 `run_safety_validation.py` 的前五个算例完成：6 mT渐入、3 mT非零初值、0.15/6/10 mT正弦，最大全杆横向位置依次为 $0.924046$、$2.062224$、$0.077306$、$3.090305$、$5.144776$ mm。原设净空为4 mm，因此无 governor 的10 mT算例确实越界；这不是安全成功案例。新旧尖端轨迹差最大约 $1.449\times10^{-10}$ m。运行随后进入非光滑主动限功工况，原紧容差档案已显示该工况需720万次右端调用、约537 s；本轮为避免扩成长期重积分，主动中断该阶段，返回码130，未将主动限功积分标为通过，见 `safety_run.json`。

对原三条主动限功轨迹另从128维状态、冻结模态图和实际磁场独立重算能量与功率。存档能量重构差小于 $6.7\times10^{-24}$ J；样本点上 $P-5(E_{\rm cap}-W)$ 的正残差不超过 $1.9\times10^{-21}$ W。普通、零拖曳及紧容差轨迹的最大位移分别约 $3.143623$、$3.558526$、$3.143623$ mm，均低于解析能量界对应的 $3.898718$ mm；能量上限为 $22.663646$ nJ。普通/紧容差轨迹限功激活样本比例 $55.3723\%$。这是对已有输出的独立样本审计，不是新重积分，更不是由有限采样新建连续时间区间证书。零拖曳样本有约 $6.73\times10^{-18}$ J 的数值能量观察器差，应作为有限精度残差记载。详情在 `safety_independent_comparison.json`。

### 8.5 追加复算：35/45完整特征的三种子重训与2×2对照

在独立目录 `stage2/runs/v10_training/` 已实际调用原 `run_learning.py` 的 `fit_labels`、`simulate_learned`、`physical_metrics`，三者源代码均未修改。种子17、43、91各做无先验/有先验与实/复交叉，共12次完整线性读出重训；随后每组运行原8条16 s保守留出轨迹，共96次新的轨迹积分。总墙钟时间65.51540 s，脚本内部时间63.88169 s，12次最小二乘本身共0.83528 s；均为单线程。未重做原合成参考轨迹产数、耗散头辨识和200 s续算。

为消除重新对角化及不同QR/SVD基选择造成的对象改变，wrapper 从原 `model_matrices.npz` 与 `feature_basis.npz` 装载原模态图、物理尺度、完整余弦归一化及四次补空间。训练数据是原Python两模态模型每种子12条4 s轨迹，每条129状态；状态无噪声，导数标签加分量有界 $10^{-6}$ 噪声。逐个核对三种子的存储标签恰好等于 clean field 加原 unit noise 乘 $10^{-6}$。测试为原8条16 s参考，每条1601状态。没有把该数据称为COMSOL观测，也没有将此读出回归称为隐藏层端到端训练。

| 对照 | 实参数个数 | 尖端 RMS 三种子均值±样本标准差 | 留出场相对 $L^2$ 误差均值 |
|---|---:|---:|---:|
| BR：无线性先验、实表示 | 45 | $22.81494\pm7.51056$ nm | $1.722553\times10^{-7}$ |
| BC：无线性先验、复表示 | 45 | $22.81494\pm7.51056$ nm | $1.722553\times10^{-7}$ |
| GR：固定线性先验、实表示 | 35 | $11.99845\pm7.08620$ nm | $1.585065\times10^{-7}$ |
| GC：固定线性先验、复表示 | 35 | $11.99845\pm7.08620$ nm | $1.585065\times10^{-7}$ |

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

## 9. 数学核验结论与不可转移事项

### 9.1 连续KAM实际证明对象

原主证书将导出二进浮点系数解释为精确二进有理数，保守能量含完整余弦和所有导出四次项；不是仅检验四次截断。Haro–Luque 2019 Theorem 3.1 在 $n=d=2$、canonical Case III（Remark 3.2–3.3）上使用，需复域内解析全局场与导数上界、复条带参数化、$DK$满秩/Gram逆界、平均扭转逆界、全整数Diophantine频率，以及带显式常数的残差小量。代码补了插值与别名尾项；没有把离散网格残差当解析范数。

原用频率比是具有有界连分数系数（最大23）的二次无理数，因此从 $|q\zeta-p|\ge1/(25|q|)$ 得周期一角变量下 $|k\cdot\varpi|\ge(9/1750)|k|_1^{-1}$，再以较弱指数 $\tau=3$ 进入定理。原证明给出的全整数条件比有限扫描有实质区别。

本轮已从作者一手页面取得并核查 Haro–Luque arXiv:1711.05515v1：PDF pp.14–18的范数、H1–H5与Theorem3.1、p26 Remark4.7、pp56–59 Appendix B Tables1–3。还核对期刊接收稿对应定理；未宣称本轮重新独立复证全59页每个估计。书目：Àlex Haro, Alejandro Luque, *A-posteriori KAM theory with optimal estimates for partially integrable systems*, JDE 266(2–3) (2019), 1605–1674, DOI 10.1016/j.jde.2018.08.003。官方作者机构条目：https://diposit.ub.edu/items/7e54e405-d0b4-4e75-b0ed-86c8ae618e11 。本地来源及 SHA 在 `stage2/sources/primary_kam/sources.json`。

两个容易漏的常数细节已独立确认：（i）源文 $D(X_h^T)$ 是对行向量映射求导，范数是所有 Jacobian 元绝对值的总和；不是 $(DX_h)^T$ 的列和。原代码取32符合其保守上界。（ii）Table1 的 $C_{sym}$ 行存在符号打印不一致；原代码按 p26 Remark4.7 的块式用 $\max(1,\sigma_B^2)C_{\Omega_L}=192$，不是较小的 $C_{\widetilde\Omega_L}$ 值。不能因机械照表而把阈值改宽。

### 9.2 正测度、可分辨厚度和“exact symplectic”用词

Bounemoura 2016 *Non-degenerate Liouville tori are KAM stable*, Adv. Math.292,42–51, DOI10.1016/j.aim.2016.01.012，作者稿 arXiv:1412.0509 Theorem6（PDF p7）要求既有非共振环面、非奇异平均二次扭转和Gevery/解析正则性，以及其小邻域条件。其解析情形支撑原已认证环面附近的正测度族；它不证明某个任意工作域里99%以上轨迹都在KAM环面。

原另给 $w=10^{-220}$ 的明确定义管状域、严格比例 $>96.69383\%$。这是在精确环面周围的极薄作用管，嵌入已知误差上界约 $10^{-41}$ 远大于该厚度，无法据已计算候选给一个实验初态判定管内归属。原文也承认这一点。1024/1024及Clopper–Pearson区间 $[0.996404,1]$ 只针对预先定义的有限时分类器。

**需改正的确切措辞：**`measure_proof.tex` 的管状坐标段称 $\Psi$ 为“exact symplectic chart”，但只证明

$$\Psi^*\lambda-I\cdot dt=j(t)\cdot DF(t)\,dt$$

为闭形式；对正作用环面，右边通常有非零闭环积分。因此该推导证明的是 symplectic，并不证明相对于这两个原始一形式的 exact symplectic。取圆环面 $j=I_0\ne0,F=t$ 即可见其周期为 $2\pi I_{0,j}$。修正为“symplectic chart”，或明确在参考原始一形式加入作用偏移。Liouville体积转移只需辛性，故这个措辞错误本身不推翻其测度转移步骤。最新整合中央数值映射的 exact primitive 则有独立推导，不受此处影响。

### 9.3 统计HNN论文不能补上未核验条件

按118页报告第13章，Chen–Matsubara–Yaguchi 2022 的 Theorem8类覆盖界和 $C^0$ 小度直接进入强KAM范数存在实质问题。原v10主线采用确定性有限特征/Gram/缺陷路线，可避开该缺口。保留广义统计讨论时，仍须：有效的参数类复杂度界、独立采样/相关轨迹的适当理论、全域密度或覆盖、$p>2n$、域上的Poincaré条件，以及高阶或固定复域误差。

不能由“复CHNN通用逼近”“小训练损失”“实域 $C^0$ 小”“轨迹看起来准周期”中的任何一项独立推出KAM。对可训练复神经网，尤其应重新界定激活复域（如tanh极点）和训练后导数/复域范数，而非沿用有限多项式特征的系数证书。

### 9.4 连续证书不能替代离散KAM

原冻结证书是连续保守流。新整合对离散KAM增加 exact symplectic、解析隐式分支、正规形共轭后的全局周期生成函数、映射小除数

$$|e^{i\Delta k\cdot\omega}-1|\ge\Delta\gamma_D|k|^{-\tau_D},$$

以及规范化生成扰动 $\|G_\Delta/\Delta\|\le C_3\epsilon+C_4\Delta^p$，这与118页报告第14、15章核验一致。必须核实所用Shang定理的域、扭转上下界、$\tau_D>n+1$与小量；固定步长下的连续Diophantine并不排除 $2\pi$ 步长共振。旧512-bit连续证书不证明原Central4的某一离散环面。

比例耗散的时间变二形式保持也不等于自治 exact symplectic 返回映射。通用光滑ODE可局部Birkhoff化是一种表示定理，不是消除生理耗散/摩擦或证明近可积性的机制。真实血流、接触切换及非周期任务反馈必须按其实际动力学另论。

## 10. 原结果到入口、输入与模型身份的实施地图

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

## 11. 新3D理论ROM的1:1共振：本轮新增对象的明确边界

以下是 root 本轮建立的新计算结果，不是原 v10 证书的延用。已读取 `stage2/program/learning/rod_rom.py` 的模型接口及 `stage2/results/learning/rom_metadata.json`。新模型是不可伸长、不可剪切的三维 Kirchhoff 应变 Ritz：两弯曲方向与扭转各4个 Legendre 系数，共12个配置自由度、24维相空间，20个空间求积单元；质量矩阵依赖配置并包含旋转惯量。其材料、远端磁体与场接口与新高保真模型共享。该模型仍需估计剪切/伸长忽略、空间截断及血流/壁接触闭合误差。

本轮元数据给出 $E_0=3.62\times10^{-7}$ J、$\omega_0=4.4576294085$ rad/s。四组弯曲频率为

$$
(4.4576294,4.4576294),\quad
(27.6941957,27.6941957),\quad
(79.7832866,79.7832866),\quad
(356.9402367,356.9402367)\ {\rm rad/s}.
$$

另四个频率约为 $370.4309161,1118.6110907,1984.6316311,3899.8926691$ rad/s。重复弯曲频率与圆截面、各向同性、直杆轴向偏场的旋转对称性一致；不能用舍入误差人为拆开它们，再宣称验证了非共振条件。以第一对为例，整数向量 $k=(1,-1,0,\ldots,0)$ 满足 $k\cdot\omega=0$，故该线性频率向量不满足任何正 $\gamma$ 的全整数 Diophantine 不等式。

对复规范变量，齐次正规形方程作用在单项式上的除数为 $i(\alpha-\beta)\cdot\omega$。若四阶项中相应共振单项式非零，就不能使用原两模态非共振公式将其除去；应采用

$$
H_4=Z_4+\{H_2,W_4\},\qquad
Z_4=\Pi_{\ker\operatorname{ad}_{H_2}}H_4,
$$

只对非零除数求解 $W_4$，并保留共振项。这里的 $Z_4$ 一般不再只是全部独立作用量的二次函数，因而旧 $2\times2$ twist 行列式和原有限幅值环面的数值常数都不能移植。可研究保留轴向旋转对称性的共振正规形、动量映射及约化后的非退化条件；也可引入有物理来源的截面/刚度各向异性、磁化方向或偏场/平衡形状，再重新验证频率、扭转和小除数。应明确具体破对称机制及其参数，不能仅为套用定理而修改频率。

线性1:1共振不等于证明所有有限振幅KAM环面不存在。非线性频率、对称性约化后的系统和具体候选环面仍可能满足其他KAM定理；它意味着当前标准非共振椭圆平衡点论证尚不成立。对新可训练复神经网与固定解析残差特征的比较，也须分别建立训练后结构/复域界；原S1的确定性35/45特征证书不能用网络名称来转移。
