# 一般 Birkhoff、Theorem A/B 与原（30）—（36）独立继承审计

审计起点 HEAD：`38ee6a7fb8f279fc80be05ee2bd4956817364ffc`。本文件是研究审计及修正推导，不是完整新论文，也不是新三维 KAM 证书。原件和历史失败数据均未改写。

## 1. 阅读依据与结论

先按 DOCX 原生 OMML 检查原稿，再读取旧材料和实现。定位采用 `stage4/audit/source_omml/original1025_indexed.json` 中 `original1025-pNNNN/mNNNN`；`original1025_reading.txt` 的同号行便于阅读，原始数学 XML 是最终核对依据，不靠不稳定印刷编号。下面 `V/` 表示 `stage3/source_inputs/v10/v10_framework_20261028/`，`S2/` 表示 `stage3/source_inputs/starter/stage2/`，`C/` 表示 `stage3/source_inputs/birkhoff/`；CSV 使用完整路径。

实际读取的核心范围：原稿 p0840–p1221 的定义、A/B、两套重复推导与晚期证明；C 的全部 8 个文件（480 行理论、两个 Python 实验、两个结果 JSON、数值说明、README、环境）；V 中英文 `sections/structure.tex`、`supp_structure.tex`、`controlled_analysis.tex` 及数值 `analysis.tex`；S2 的 `notes/route_a.md`、`models.py`、`integrators.py`、`transport_moser_check.py` 和高维实验的结构诊断/矩阵消元实现；stage3 的 `birkhoff_rom.py`、`run_birkhoff.py`、`rom_integrators.py` 及相关笔记、长短窗口 JSON/NPZ 数据语义。书中定理编号沿原稿及材料的明确对应：A 对应 Chapter 15 Theorem 4.1，B 对应 Theorem 4.4，截断另涉及 Theorem 4.5；下面给独立推导，不把书中未核验假设省略。

**结论：第三阶段推进了真实三维变质量 ROM 的计算接入，但没有完整继承一般 Birkhoff 和生成函数理论的研究深度。** 它的 `theory.md:185-208` 只有 A/B 前提与误差界摘要，缺完整端点证明、固定生成坐标的递推、重构及精确辛原函数。S2/C 已有更一般的输运/Moser 与高维算例，stage3 改用特殊常对角阻尼的一阶输运。此选择在代码和笔记中明确承认限制，不能判为隐瞒；也不能因此称“任意三维血流/接触/控制的一般 Birkhoff 已完成”。旧 v10 的 Central4、非交换消元、精确辛性与含求解残差的有限时间证明有效，应整段继承并连接新 ROM。

## 2. 统一符号、变分原理和相容性

取列向量 (z=(q,p)\in\mathbb R^{2n})，(Da_{ij}=\partial_j a_i)，(J=\left(\begin{smallmatrix}0&I\\-I&0\end{smallmatrix}\right))，(K_0=-J)。一形式及二形式为

\[
\alpha_t=\sum_i a_i dz_i,\qquad
\Omega_t=d\alpha_t=\frac12\sum_{ij}K_{ij}dz_i\wedge dz_j,
\quad K=(Da)^T-Da.
\]

固定端点变分 (\mathcal A=\int(a\cdot\dot z-B)dt) 给

\[
\delta\mathcal A=\int\delta z^T
\{[(Da)^T-Da]\dot z-a_t-\nabla B\}dt,
\qquad Kf=\nabla B+a_t.
\]

因此原稿 p1113–p1115 的 (D=-\nabla B-a_t) 约定对应 (Kf+D=0)、(f=-K^{-1}D)。p1180/m0541 用 (+K^{-1}D) 错；后文 p1192–p1203 使用 (K^{-1}(\nabla B+a_t)) 的正号是对的。p1120/m0505 的 (\partial_tK_{ij}=\partial_jD_i-\partial_iD_j) 在负号 D 约定下正确，不能误判；p1138 的重复/交换指标则应重写。

若记 (b=Kf=\nabla B+a_t)，则

\[
\partial_kK_{ij}+\partial_iK_{jk}+\partial_jK_{ki}=0,
\qquad \partial_tK_{ij}=\partial_i b_j-\partial_j b_i.
\]

用 (\iota_f\Omega=-b\cdot dz) 与 Cartan 公式得

\[
\partial_t\Omega+\mathcal L_f\Omega=0,
\quad K_t+(f\cdot\nabla)K+(Df)^TK+KDf=0.
\]

必须另有 (\det K\ne0)。闭性保证非退化 (K^{-1}) 的 Poisson Jacobi 恒等式；闭性不保证非退化。p1125 的 (\Omega=\sum_{ij}K_{ij}dz_i\wedge dz_j=d\alpha) 漏 (1/2)，p1156 已自行算出该双重求和等于 (2d\alpha)。最小修正就是统一上面的 (1/2)。这不是新理论错误，属于原稿约定混用。

流满足 (\Phi_{t,s}^*\Omega_t=\Omega_s)，故保持的是两个时间截面的 (\Omega_t^n/n!)；p1167 不能直接解释成欧氏相空间体积守恒。耗散振子欧氏行列式为 (e^{-\gamma h})。局部存在时变二形式也不推出自治可积性或 KAM。

原稿 p0846–p0851 同时要求 (a_p=0,\partial_pa_q=1,B=H) 并把阻尼积分写入 (a_q)，一般不相容。例 (a_q=(1+\gamma t)p)、(H=(q^2+p^2)/2)、(f=(p,-q-\gamma p)) 给 (\partial_pa_q=1+\gamma t)，且表示残差为 ((\gamma t(q+\gamma p),\gamma tp))。原稿 p0842 的 \(\dot q=H_q\) 标记应为 \(H_p\)；H 的 OMML 中也有异常矩阵/缺逆，应以正确 (H=p^TM(q)^{-1}p/2+V(q)) 恢复，不能把错误字符继承为新的物理假设。

## 3. 应完整继承的一般构造：存在、可计算递推与规范

C `一般Birkhoff_两个核心连接与验证.md:39-148` 和 V `supp_structure.tex:14-34` 给出正确局部理论。若 f 足够光滑，局部流可逆，初始 \(\alpha_0\) 的外微分非退化，则

\[
\alpha_t=(\Phi_{t,s}^{-1})^*\alpha_s,
\quad a_t+Da\,f+(Df)^Ta=0,
\quad B=a^Tf
\]

表示原 f，因为 (\nabla(a^Tf)=(Da)^Tf+(Df)^Ta)，从而 (Kf=\nabla B+a_t)。闭性来自 (d^2=0)，非退化来自流拉回。使用精确流的这一式是**存在性证明**；不能把未知流当作算法输入。

可计算局部级数令 \(\tau=t-s\)、(f=\sum_{j\ge0}\tau^j f_j)、(a=\sum_{j\ge0}\tau^ja_j)，系数不是原始导数而已包含阶乘。逐幂匹配给

\[
a_{m+1}=-\frac1{m+1}\sum_{r+s=m}
\{(Da_r)f_s+(Df_s)^Ta_r\}.
\tag{T}
\]

这是由场及其导数计算有限阶系数的实际入口；自治时 (a_j=(-\mathcal L_f)^j a_0/j!)。解析性及共同域估计才可能证明无限级数收敛，有限次 AD 不能提供解析半径。对 (a^{[r]})、(B^{[r]}=(a^{[r]})^Tf)，自治残差精确为

\[
e_B=K^{[r]}f-a_t^{[r]}-\nabla B^{[r]}
=-\tau^r\mathcal L_f a_r,
\quad f_a=f-(K^{[r]})^{-1}e_B.
\]

本轮新增 `program/birkhoff_counterexamples.py` 真正计算了非可分变质量 (H=(1+q^2)p^2/2+q^2/2+q^4/4)、状态相关阻尼 (-(1/5+q^2/10)p) 的 (a_1,a_2)；符号验证残差分别为 (O(\tau),O(\tau^2))。它是复核通用递推的最小算例，**不代替三维 ROM 的高阶输运实现**。

规范变换 (a\mapsto a+\nabla\sigma, B\mapsto B-\sigma_t) 保持 K 和被表示场不变。选 \(\sigma_t=B-H\) 可令新 B=H，但不能修复 (e_B\ne0)。新增程序符号验证任意所选非平凡规范不改变残差。S2 `route_a.md:284-308` 已有完整此论证，stage3 不能把规范当成精确恢复。

## 4. Moser 图、时间图场和误差责任

给定 (\Omega_t=d\alpha_t)，设

\[
K_{\lambda,t}=K_0+\lambda(K_t-K_0),\qquad
K_{\lambda,t}v_{\lambda,t}=a_t-a_0,
\quad \frac{d\rho_{\lambda,t}}{d\lambda}=v_{\lambda,t}\circ\rho_{\lambda,t}.
\]

这里右侧的 (a_t) 指时间 t 的一形式系数，非时间导数。由于 \(\iota_v\Omega_{\lambda,t}=-(\alpha_t-\alpha_0)\)，Cartan 公式给 (\rho_{1,t}^*\Omega_t=\Omega_0)。取 (\chi_t=\rho_{1,t}^{-1}) 得 (D\chi_t^TK_0D\chi_t=K_t)。必须检查插值非退化、辅助流留域、图与逆及导数稳定；端点非退化本身不保证整段插值非退化。

转到 (y=\chi_t(z)) 的真实场为

\[
g(y,t)=\{\partial_t\chi_t+D\chi_t f\}\circ\chi_t^{-1}(y).
\]

相容条件推出 (K_0g\cdot dy) 闭，在星形局部域可取
\(\mathcal H(y,t)=\int_0^1(K_0g)(y_*+s(y-y_*),t)\cdot(y-y_*)ds\)。这给 (g=J\nabla\mathcal H)。忽略 (\chi_t\) 时间导数会改变实际积分场。

S2 `transport_moser_check.py:21-93` 已计算一般非比例非线性场的一阶 a、辅助积分、逆、复步 Jacobian 和时间导数；8/16 DOF 的点图匹配约 (2.47\times10^{-16}/6.68\times10^{-16})，表示场差却约 .0761/.1096，且没有宣称已完成通用时间推进。其 `integrators.py:114-151` 的矩阵指数图只适用明示线性共轭；`run_extended.py:44-65` 的逆流结构属于昂贵独立诊断，不是算法免费输入。C 的已知共轭图实验同样不能自动移植真实三维杆。

## 5. Theorem A：完整端点相容与局部生成函数证明

固定端点时间 t、s，将二形式相容的局部端点变换写为
\(\alpha:(z_+,z_-)\mapsto(\widehat w,w)\)。必须要求

\[
d(\widehat w^Tdw)=\Omega_t(z_+)-\Omega_s(z_-).
\tag{A1}
\]

若两端已经各用 \(\chi_t,\chi_s\) 正则化，可用
\(\widehat w=J(y_+-y_-),w=(y_++y_-)/2\)。或者采用原稿的等价符号（下一节）。设端点 Jacobian 分块为 \(D\alpha=\left(\begin{smallmatrix}A&B\\C&D\end{smallmatrix}\right)\)，物理流或待分析映射 Jacobian 为 (M=D\Phi)。流图像上的切向量为 \((Mv,v)\)。由结构保持与 (A1)，该图像上的 \(\widehat w^Tdw\) 闭。

若 (\det(CM+D)\ne0)，w 是图像上的局部坐标；Poincaré 引理给局部单值 \(\phi\)，(\widehat w=\nabla_w\phi\)，且

\[
N=\phi_{ww}=(AM+B)(CM+D)^{-1}=N^T.
\tag{A2}
\]

反向重构用完整局部逆 \((z_+,z_-)=\alpha^{-1}(\nabla\phi,w,t,s)\)，再检查投影到 \(z_-\) 可逆。由 \((NC-A)M=B-ND\) 可在对应分块可逆时写 \(M=(A-NC)^{-1}(ND-B)\)。**不能在未检查条件时对 N 求逆。** 中心恒等映射 \(h=0\) 时 N=0，合法投影仍为 I（原稿坐标为 \(T_0\)）。p1204 要求 N 可逆的证明步骤错误。\(\phi\) 仅在加与 w 无关的时间函数意义下唯一，p1186 的无条件唯一需指定规范。

端点变换任意可逆也不够：新增反例对精确谐振子旋转取 \(\widehat w=z_+-z_-\)、w 为均值，完整变换与投影均可逆，生成候选 Jacobian 反对称缺陷 .60454，不能为梯度；改为相容的 J 差分后缺陷 (4.48\times10^{-17})。V 中英文 `structure.tex:36-67` 和 `supp_structure.tex:36-92` 已经正确修复这些点；这是必须继承的完整旧证明。

## 6. Theorem B：恢复固定 w 的 PDE、递推、截断和重构

这部分在 stage3 只有一句提醒，而原稿有详细但部分错误的展开。应恢复如下完整链条，不能把 Theorem B 简化为“用一次中点”。固定初始端点时间 s，令 \(g(w,t;s)=\nabla_w\phi\)、\(N=D_wg\)。通过 **完整端点逆** 在当前 \((g,w,t,s)\) 上计算

\[
\mathcal A=\alpha_{1,t}+A_\alpha f(z_+,t),\quad
\mathcal B=\alpha_{2,t}+C_\alpha f(z_+,t).
\]

沿真实末端演化时 \(\dot{\widehat w}=\mathcal A,\dot w=\mathcal B\)，链式法则给

\[
\left.\partial_tg\right|_w
=\mathcal A-N\mathcal B
=:\Psi(g,w,D_wg,t;s).
\tag{B1}
\]

原稿 p1180 的结构正是此式，但须用正确 (f=K^{-1}(\nabla B+a_t)\)；p1040–p1057 若沿移动中点求导再称固定 w Taylor 系数，会多算项。时间图的导数保留在 \(\alpha_{j,t}\)，不能省略。

令 \(g=\sum_{j\ge0}\tau^jc_j(w;s)\)，\(\tau=t-s\)，初值 \(c_0\) 由 \(\alpha(z,z,s,s)\) 的图确定。正确递推是

\[
c_{r+1}=\frac1{r+1}[\tau^r]\,
\Psi\left(\sum_{j=0}^{r}\tau^jc_j,w,
\sum_{j=0}^{r}\tau^jD_wc_j,s+\tau;s\right).
\tag{B2}
\]

特别 \(c_1=\Psi_0\)、\(c_2=(\Psi_t+\Psi_g c_1+\Psi_N[D_wc_1])_0/2\)。等价导数形式是 \(c_{r+1}=D_t^r\Psi|_{t=s}/(r+1)!\)，其中沿系数 PDE 取导数并固定 w。原稿 p0888/m0399 写成 \(c_k\) 的下标错；晚期 p1213/m0565 已改成 \(c_{k+1}\)，应保留这个有效修订。

从解析且满足 A1 的精确局部图出发，(D_wc_j) 对称；因而每个系数在共同局部域是标量梯度。有限截断 \(g^{[r]}=\sum_{j=0}^r\tau^jc_j=\nabla\phi^{[r]}\) 仍给相容端点上的结构保持图；但必须检查隐式重构分支留在同一域，截断梯度误差与端点逆条件数才能给局部状态缺陷。解析性+隐函数条件给局部解析分支；只有有限光滑时只能谈有限 Taylor 余项，不能把形式无限级数叫作收敛级数。局部误差 (O(h^{r+1})\) 配合 (1+O(h)\) 稳定性才给通常全局 r 阶；对称性可提高阶数，不能只数非零项。

**可直接实现的正则中心专式。** 用 \(w=(y_++y_-)/2,\widehat w=J(y_+-y_-)=\nabla\phi\)，则

\[
y_+=w-\tfrac12J\nabla\phi,\quad y_-=w+\tfrac12J\nabla\phi,
\quad
\partial_t\phi(w,t;s)=-\mathcal H\left(w-\tfrac12J\nabla\phi,t\right),
\quad \phi(w,s;s)=0.
\tag{B3}
\]

这里已选择时间加常数规范。验证：对右侧求 w 梯度为 \(-(I+NJ/2)\nabla\mathcal H\)，等于 \((J-N/2)J\nabla\mathcal H\)，恰为 (B1)。因此标量递推

\[
\phi_{r+1}=-\frac1{r+1}[\tau^r]\,
\mathcal H\left(w-\tfrac12J\nabla\sum_{j=1}^{r}\tau^j\phi_j,s+\tau\right)
\tag{B4}
\]

不会丢掉梯度可积性。新增程序的 `central_generator_coefficients` 已实算非可分变质量例；自治时 \(\phi_1=-H,\phi_2=\phi_4=0,\phi_3=-f^TH''f/24\)，时变 \(H+tq^2/2\) 给 \(\phi_2=-q^2/4\)，说明不能向非自治图盲套自治奇次展开。对真实 24D ROM，B3/B4 可输入完整 AD Hamiltonian；保守分支目前只实现到 Central4，任意 \(K_u\) 的高阶图/生成 PDE 尚未完成。这是明确接入接口而非已完成推广证明。

## 7. 原（30）—（36）的逐式修正与继承

| 原始位置 | 应继承的数学内容与必要修正 | 对应成熟旧材料/当前实现 |
|---|---|---|
| (30) p0910/m0400 | \(\widehat Q=p_+-p_-,\widehat P=q_+-q_-,Q=\bar q,P=-\bar p\)。对一般时变 K，应先用两端图，再把 p 换成提升后的 \(\Pi\)；物理端点直接均值不自动相容 | V structure:55-90；C:183-220 |
| (31) p0920/m0408 | \(q_\pm=Q\pm\widehat P/2,p_\pm=-P\pm\widehat Q/2\)。这是联合逆，不需要 \(\widehat w\) 对 w 的逆 | V supp_structure:63-78 |
| (32) p0931/m0417 | 固定负端，\(\dot w=(\dot q_+/2,-\dot p_+/2)\)、\(\dot{\widehat w}=(\dot p_+,\dot q_+)\)；固定 w 偏导为 \(\dot{\widehat w}-N\dot w\)。原式有负号/块次序错误 | 本审计 B1；S2 route_a.md:47 |
| (33) p0961/m0427 | 在合法图中取 \(\phi=-h\mathcal H(Q,-P,t_m)\)，再求梯度。原 p0957/0960 把 \(p=-P\) 代入阻尼仍写负号，p1040又用正号；即使修正号，物理阻尼候选 \((-Q+\gamma P,-P)\) 的混合偏导差 \(\gamma\ne0\)，不存在所称标量 | V structure:68-90；新增原(33)反例 |
| (34) p0963/m0429 | 端点增量等式是代数关系；只有相容图+单值生成标量才给结构结论 | V supp_structure:72-92 |
| (35) p0986/m0434 | \(\Delta q=hM(\bar q)^{-1}\bar p,\Delta p_i=h[-\frac12\bar p^T\partial_iM^{-1}\bar p-V_i+Q_i]\)，同一未知中点及完整惯性 | stage3 rom_integrators.py:62-77；theory.md:25-49 |
| (36) p1003/m0442，重复 p1070/m0470、p1220/m0570 | 仅常 M/C/K 可作下面非交换左解；变质量直接解24维残差。一般阻尼下是二阶物理中点，不自动辛或精确指数共形 | V supp_structure:94-121；stage3原场中点 |

常矩阵消元从 \(\bar q=q_-+hM^{-1}(p_++p_-)/4\) 得

\[
E=\tfrac{h^2}{4}K_sM^{-1}+\tfrac h2CM^{-1},\quad
(I+E)p_+=(I-E)p_--hK_sq_-+h(F_m+U_m),
\quad q_+=q_-+\tfrac h2M^{-1}(p_++p_-).
\]

不能写成列向量右乘标量式分母，也不能交换 \(K_sM^{-1}\) 为 \(M^{-1}K_s\)。新增非交换例完整4维解与正确消元差 (3.40\times10^{-17}\)，错误顺序差 .00123335。一般未知中点反馈仍然隐式。p1005 因“只有一项”称一阶也不对：完整时间中点二阶可直接由 Taylor 证明；错的可积性论证不能使中点阶数改变。

## 8. 加权格式、非可分 Central4 与精确辛性

对统一动量阻尼 \(f=(H_p,-H_q-\gamma(t)p)\)，取 \(a=(a(t)p,0), B=a(t)H,K=a(t)K_0\)，其中 \(a(t)=\exp\int\gamma\)。图 \(\Pi=a(t)p\) 的 \(\mathcal H=a(t)H(q,\Pi/a(t),t)\) 对变质量同样成立。常 \(\gamma\) 的完整时间中点可中心化为 \(S_{h/2}\operatorname{MP}_H S_{h/2}\)，\(S_h(q,p)=(q,e^{-\gamma h}p)\)。这正是 stage3 `weighted_midpoint:80-92`。它保持 \(D\Psi^TK_0D\Psi=e^{-\gamma h}K_0\)，而任意非比例阻尼不满足此假设。新增 \(\gamma=.7,h=.4\) 例：普通中点行列式 .7627118644，真实指数 .7557837415，加权格式匹配后一值。

对自治 \(f=J\nabla H\)，精确时间中点状态 \(z_c\) 与端点均值 m 满足

\[
m=z_c+\tfrac{h^2}{8}f'f(z_c)+O(h^4),\quad
z_+-z_-=hf(m)+\tfrac{h^3}{24}\{f''[f,f]-2(f')^2f\}(m)+O(h^5).
\]

微分 \(Q=f^TH''f\) 给 \(J\nabla Q=f''[f,f]-2(f')^2f\)。所以

\[
S_h=hH+\tfrac{h^3}{24}f^TH''f,\qquad z_+-z_-=J\nabla S_h(m)
\]

有局部五阶缺陷。正号是前向生成修正；普通中点的后向修正 Hamiltonian 首项为负号，两者不矛盾。V `supp_structure:147-211` 的完整证明/磁势导数应保留。stage3 `central_scalar:15-27` 对真实非可分 H 作 AD，保留混合导数；预条件器仅加速求解，没有冻结实际动力学。新增谐振子末档阶：中点1.99990、正确Central4 3.99990、负号错误版1.99986。

若 \(C=JS_h''/2\)、\(I-C\) 可逆，理想一步导数 \(D\Psi=(I-C)^{-1}(I+C)\) 保 K0。**用于离散 KAM 还必须保留更强的原函数证明**：\(\delta q=S_p,\delta p=-S_q\) 给

\[
p_+dq_+-p_-dq_-=\bar p\,d\delta q+\delta p\,d\bar q
=d[\bar p^T\delta q-S_h(m)].
\tag{E}
\]

只要 S 和隐式分支单值，此为 exact-symplectic。作用角环域上 \(p\,dq=I\,d\theta-d(I\sin\theta\cos\theta)\)，正规形变换若由单值 Hamiltonian 生成，精确性可传递，才能形成周期混合生成函数。V `supp_structure:123-145` 已证明，stage3 只写“精确辛”而没有这一论证。反例 \((\theta,I)\mapsto(\theta,I+c)\) 保二形式，却有周期积分 \(2\pi c\ne0\)，不能有单值周期原函数。有限容差输出不是自动精确辛；当前程序记录首步**理想隐式切线**，不是有限迭代程序的精确导数。

## 9. 三维一阶图的真实推进和限制：独立核对长短窗口

stage3 `birkhoff_rom.py:23-91` 使用实际 RodROM 的完整 H；\(a_1=d(V-T)+(\Gamma P,0)\) 的恒等式利用动能对动量二次，允许 \(M(Q)\)。\(K_a=\left(\begin{smallmatrix}0&-W\\W&0\end{smallmatrix}\right),W=I+t\Gamma\)，\(\chi_t=(Q,WP)\) 精确匹配这个近似形式。规范 \(\sigma=-t(V-T)\) 给

\[
a'_a=(WP,0),\quad B'_a=H+2t(V_Q+\Gamma P)^TH_P.
\]

代码中的场和时间图项与此式一致。它准确表示的是 \(f_a\)，不准确表示原 f；并非实现错误导致全部偏差。

读取历史 `stage3/results/birkhoff/results_T0.0005.json`，并运行新增 `program/check_frozen_birkhoff_results.py` 从 NPZ 数组独立重算6组轨迹指标和双参考间隔（与JSON差均为0，`results/birkhoff_frozen_npz_check.json`；这是存档指标复核，不冒称新积分）：固定 T=.0005、相同步长与初态，细网格原场中点误差 (2.2451\times10^{-9}\)，图中点对 \(f_a\) 误差 (9.9849\times10^{-9}\)，对 f 误差 (2.18576\times10^{-5}\)；两个连续参考差 (2.18600\times10^{-5}\)。图的首步结构缺陷 (4.44\times10^{-16}\) 不消除这项场误差。原场功率残差图法约 (3.2523\times10^{-6}\)，普通中点 (4.1838\times10^{-15}\)。两方法分别逼近不同的场，不能以原场中点不保近似 \(K_a\) 作为它逼近真实动力学更差的证据。参考细化差约 (10^{-17}\) 是本次短区间浮点诊断，非严格参考包络。

`results_T0.004.json` 明确为 `interrupted_due_to_diagnosed_transport_truncation_failure`、rows为空；不能称该窗口图积分已通过。`window_diagnostic.json` 固定初始状态的瞬时谱在 t=.001/.004 有最大实部1255.44/6052.88，这是近似图场的局部诊断，不是原物理系统的失稳证明。当前实际做完的图时间窗短于其他积分/控制试验8倍，因此四法统一长窗比较尚未完成。

**本轮新增原生24D反证/归因**：直接调用冻结 `LocalBirkhoffROM(rates=zeros(12))`，原场已经是已知保守 Hamiltonian。初态为 `ROMBridge.initial_state(amplitude=.01)`（完整24维数组保存于新JSON），在固定该状态处、无量纲时间 t=.0005 测量 `||f_a(t,z0)-f(z0)||_2`，这是点态欧氏范数而非轨迹误差；此时 K=K0、图匹配0、原场输运相容缺陷 (1.36\times10^{-13}\)、条件数1；但所选一形式截断仍给场误差 .08920957，几乎等于原非比例阻尼实验 .08920657。可见主要局限来自截断后的 \(a,B\) 配对，即使 K 的输运正确也可能发生；这不是一般 Birkhoff 理论失效，也不是由血流或12维本身造成。在独立保守谐振子 H=ν(q²+p²)/2 上同一截断给 B′=H+2tν²qp，其瞬时Hamiltonian矩阵满足 λ²=4t²ν⁴−ν²，超过 t=1/(2ν) 后即出现实特征值，尽管真实保守振子始终椭圆。这一解析反例解释截断的局限，仍不是非自治轨迹增长定理。最小算法选择应对已知保守分支直接使用 \(a_0=(P,0),B=H\)，对统一阻尼用精确指数结构；对一般载荷才需控制高阶输运误差。此诊断已运行，结果在本审计 JSON，未改旧实验或伪称已实现通用替代器。

## 10. 控制、局部可解、有限时收敛和 KAM：分开证明

对真实闭环 \(f_u=f+g\)，\(g=(0,G_m(q)u)\) 必须来自磁端口。保持同一 \(\Omega\) 的条件为 \(\mathcal L_g\Omega=0\)；局部单连通域等价于 \(Kg=\nabla W\)，对应 \(B_u=B+W\)。全域还需零周期/精确性条件。若不成立，需对**实际分配后**闭环重新构造 \(a_u,K_u,B_u\)，不由小输入或下降能量推出保结构。势能整形满足梯度且力可达才成立；动量阻尼/饱和/分配残差一般不保原 K。旧 C:305-331 已完整区分，V `controlled_analysis.tex:4-60` 也已把反馈放到同一未知中点并给精确辛原函数。第三阶段实际磁端口是重要推进，但还未计算一般闭环 Ku 或其图。

若 \(\|Df\|\le L\)、共同凸局部域映回自身且 \(hL/2<1\)，中点局部唯一。仅某采样处 Newton 最小奇异值>0，不能推出全域唯一。对同一实际闭环、状态增量残差 \(\|r_k\|\le\eta_k\)，完整不等式为

\[
(1-hL/2)e_{k+1}\le(1+hL/2)e_k+Ch^3+\eta_k,
\quad
e_N\le q_h^Ne_0+\frac1{1-hL/2}\sum_{j<N}q_h^{N-1-j}(Ch^3+\eta_j),
\quad q_h=\frac{1+hL/2}{1-hL/2}.
\]

固定 T 得 \(C_T(e_0+h^2+\eta_h/h)\)；Central4 有足够高阶导数/稳定性才把 h² 换成 h⁴。当前无穷范数残差到24维欧氏范数需最多 \(\sqrt{24}\) 因子，不能混单位。额外场差满足共同域界 \(\|f_a-f\|\le\kappa\epsilon_B\) 时再加 \(\kappa\epsilon_B(e^{LT}-1)/L\)，图实施每步状态误差也按累积处理。上述完整证明 V `controlled_analysis:65-128`、`supp_structure:213-244` 已有，stage3摘要不是新证明；样本测量没有给出这些统一常数。

数值图若 \(D\widetilde\chi_t^TK_0D\widetilde\chi_t=K_t+E_t\)，内部理想映射保K0，外部结构缺陷是 \(E_- -D\widetilde\Psi^TE_+D\widetilde\Psi\)，再加内部误差；它与轨迹误差预算不同。

保守 exact-symplectic 固定/周期映射进入离散 KAM 还需：共同复解析域、留域/逆图界、可积/正规形骨架、twist下界、全整数且含步长的 \(|e^{ihk\cdot\omega}-1|\) 非共振、小量阈值。V `supp_structure:396-445` 已给条件路径与 \(G_h/h\) 预算，不能压成“辛+高阶所以KAM”。时变一阶图序列、残余阻尼、非光滑接触不自动满足该定理。旧两模态有限证书不推广到新三维1:1共振；本审计没有新证书。

## 11. 已运行修正测试与证据

实际命令（仓库根目录）：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /workspace/1028-cloud/venvs/learning/bin/python stage4/audit/program/birkhoff_counterexamples.py --with-rom > stage4/audit/logs/birkhoff_counterexamples.log 2>&1
```

运行退出码0，10组断言通过；实际耗时见JSON（约12秒）。环境、版本、源SHA256、每项容差和原始数值见 `results/birkhoff_counterexamples.json`。所谓“通过”是确认具体反例和修正关系，不是原稿错误公式通过。一般代数相等用精确 SymPy；浮点矩阵阈值 (2\times10^{-14}\)，原生ROM相容阈值 (2\times10^{-10}\) 且实测 (1.36\times10^{-13}\)。本程序没有修改冻结输入，也没有降低旧测试标准。另执行 `/workspace/1028-cloud/venvs/learning/bin/python stage4/audit/program/check_frozen_birkhoff_results.py > stage4/audit/logs/birkhoff_frozen_npz_check.log 2>&1`，退出码0，以1e-16为核对阈值重算全部6组存档指标（实测差0）。stage3整套测试与主要实验独立复跑由同目录 `reproduction_and_tests.md` 统一记录。

## 12. 需要恢复/新增的明确顺序

1. 恢复原稿路线中一般一形式变分→相容/输运→Moser→A端点→B固定w递推→重构→（36）/高阶→实际控制→收敛→条件KAM的完整证明链；本审计第2–10节提供可核对的修正版，不把一阶图算例当整条理论。
2. 原样保留 V 的非交换矩阵证明、非可分Central4及精确辛原函数、学习/控制误差分裂、离散KAM条件；继承 C 的一般输运/Gauge/Moser和 S2 的高维成本/失败证据。区分已证明条件定理与未核验三维前提。
3. 三维保守/统一阻尼分支采用已知精确结构。一般三维血流/接触投影及实际磁反馈进入同一 f、Df 后，先控制输运残差和所表示场差，再构图；高阶/分片重启必须传递 a/K 或证明过渡相容，不能每步任意重置K0。
4. 将 B4 及一般 B2 接到可导24D图Hamiltonian，给共同域截断/图逆/隐式Jacobian成本和误差包络；目前只有保守Central4真的在该ROM实施，通用高阶Birkhoff尚未完成。
5. 之后做统一时间窗四法同对象比较及实际闭环Ku；最后才对独立保守三维分支研究共振正规形、连续/离散KAM。整体机器人目标仍须回到Cosserat、流体、接触、真实磁场，不以这些局部光滑数学检验替代。

## 13. 不能因三维新模块而丢弃的旧算法与负结果

C 的 `verification_results.json`、`本轮数值结果.md` 保存了已知点变换共轭的2配置DOF实验。无控制、h=.025时原场中点/图中点终点误差分别为5.257716e-5/5.121475e-5；受控时为6.606436e-5/6.625670e-5，**图法后一值略大**，结构缺陷虽约3e-15也不保证更准确。理想全驱动控制RMS从.03581297降到3.397717e-5，是同初态同目标的合成广义力结果，没有学习或真实磁端口。C `v10_results.json` 的旧显示精度参数又是独立两模态加权回归，不能与较新v10参数混用。这些均是存档证据，本轮实际重跑状态另见复现总表。

S2 `notes/route_a.md:168-258` 和 `program/route_a/integrators.py:40-101,103-202` 中至少有三项未充分用于stage3：

- **非自治图上的两阶段Gauss4**：对明示分块质量/势能、不同阻尼块互不耦合的分块加权系统，阶段时间正确求值，四阶且保持所给时变K；16DOF h=.025,T=2时历史误差1.072807e-9、阶3.999773、缺陷1.333032e-15。它是已有的合法非自治高阶基准，不能把stage3自治Central4当作唯一可用高阶工具；但未经证明的真实ROM块分离不允许直接套它。
- **一般跨块场的Gauss4与阻尼分裂对照**：16DOF同网格历史Gauss4误差1.795071e-9、阶3.999714，采样输运K缺陷7.449379e-11。这里Gauss4只是一般ODE四阶；小结构缺陷不等于精确保持K。S2已用独立昂贵逆流变分作诊断，并只取三个步骤。应作为一般载荷算法比较和成本对照保留。
- **冻结反馈电流的真实失败/降阶**：每步固定输入子问题虽辛，真实闭环导数还有 `partial_i Phi * D_z i`（源码integrators.py:180-188附近）；S2已显式加入并用实际有限差分检查。16DOF进一步细化到h=.00078125才显现约1.062247阶；主四档似二阶不说明实际连续反馈达到二阶。`extended_run.log` 早期渐近门槛失败被保留，细化后解释为前渐近混合。stage3的真实线圈/受限控制应继承这一采样、链式导数和失败保全教训。

S2线性已知图的161次expm、161次sqrtm、80次Sylvester准备也必须计入成本（`route_a.md:230-236`），不能仅报缓存推进。上述结果的共同价值是适用条件和失败解释；它们没有完成血流/接触的一般三维Birkhoff，但也不是可以被一个新的低阶短窗算例替代的无用历史。
