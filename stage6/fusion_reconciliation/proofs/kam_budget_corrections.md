# 双路线学习—正规形—KAM 预算：保留的证明、补接的算法及限制

本文件的原始对象是 1025 `p0350/m0194,p0351/m0195,p0491/m0229,p0505/m0240,p0508/m0242,p0560–0598,p1074–1078`。这些位置按第四阶段原生 OMML 顺序定位；原（17）的分母是根号 2、原（18）却是 2，不能把纯文本抽取中的同一个字符“2”视为同一个数学对象。本轮重新检查了对应 `m:f`、`m:rad` 与共轭节点。正确的 `1/√2` 导数、耗散功率和损失修正已在 `stage5/proofs/chnn_kam_restored.md:5–27` 和 `corrected_mathematics.md:54–108` 进入三维学习程序，本轮沿用。

融合稿对应：`english/sections/{kam,route_interfaces,supp_route_budgets}.tex`，中文同标签；旧固定原文 `stage4/audit/external_v10/sections/{theorem_bridge,integral_comsol_to_kam,unified_kam}.tex`。这些数学内容在其明确对象下有价值。下面的修复针对第五阶段缺少可执行预算接口，**没有发现需要推翻融合稿完整余项公式的反例**。

## 1. 两条路线有不同的基准、坐标图和余项

设 `h*=h0+R*`，`δR=R*−Rhat`。理想保守残差补偿实现

\[
h_c=h_0+\delta R,\qquad \widehat h=h_0+\widehat R=h_*-\delta R.
\]

即使完全学习，`h_c=h0` 而 `hhat=h*`，二者通常不同。这是融合稿 `ri:hamiltonians` 的正确结论，不能把两个成功的独立实验拼成同一个闭环定理。设分别有合法正则图

\[
h_0\circ T_A=N_A+R_A,\qquad h_*\circ T_B=N_B+R_B.
\]

代入并整理，得到

\[
h_c\circ T_A=N_A+R_A+\delta R\circ T_A,
\qquad \widehat h\circ T_B=N_B+R_B-\delta R\circ T_B.
\]

所以两套扰动预算为 `ε_A≤||R_A||+b_A`、`ε_B≤||R_B||+b_B`。只有 **两张图的像都位于同一个已声明复域 U**，才可用同一个 `||δR||_U` 同时控制 `b_A,b_B`。系数误差是图外数据，可能共用；由该误差形成的解析范数不能脱离图像条件共用。实现 `fusion_budget.dual_route_budget` 遇到未核验共域就拒绝执行，缺系数误差时返回 `None` 和明确条件状态，不把训练损失代进去。

这个代数推导不限维数；但新的三维 `h0,h*`、可达磁补偿、`T_A,T_B`、余项和扭转常数还没有全部构造。因此继承的是可适用于三维的**正确接口和部分输入**，不是已经完成两个三维 KAM 证明。完整线圈受限采样闭环有功率和非保守分量，不能仅把其能量名字代入上式。

## 2. 完整 Lie 余项以及 κ² 项

融合稿的保守点模型是 `hκ=h2+κh4+κT6`，`{h2,Wκ}=−κ(h4−Z4)` 且 `Wκ=κW1`。这里相流是所构造四次多项式 `Wκ` 的辅助流，不是未知原动力学的精确相流。

对固定 `z`，令 `F(s)=h2(Φ_W^s(z))`。链式法则给 `F'={h2,W}∘Φ_W^s`，`F''={{h2,W},W}∘Φ_W^s`。积分 Taylor 恒等式与对四次部分的一次积分给

\[
\begin{aligned}
h_\kappa\circ\Phi_W^1
={}&h_2+\kappa Z_4+\mathcal R_{6,\kappa},\\
\mathcal R_{6,\kappa}
={}&\kappa T_6\circ\Phi_W^1
+\int_0^1\{\kappa h_4,W\}\circ\Phi_W^s\,ds\\
&+\int_0^1(1-s)\{\{h_2,W\},W\}\circ\Phi_W^s\,ds.
\end{aligned}
\]

这是精确积分余项，已经包括由流的复合产生的高阶 Lie 项，并非只保留三项 Lie 多项式。两项括号系数随 κ² 缩放，故不能将 κ=1 的完整余项简单乘 κ。`test_full_remainder_has_quadratic_generator_terms` 给出直接反例。

若整个辅助流段在半径 `r_out` 的多圆盘内，则多项式系数三角不等式与 `|T6|≤s_d^6 cosh(s_d)/720` 给

\[
\overline R_\kappa=
|\kappa|s_d^6\cosh(s_d)/720
+\kappa^2[\{h_4,W_1\}]_{r_{out}}
+\tfrac12\kappa^2[\{\{h_2,W_1\},W_1\}]_{r_{out}}.
\]

如果速度每分量主控界为 `m`，从 `r_in` 出发的首离开时间论证在 `r_in+m<r_out` 时保证 `0≤s≤1` 内不离开；变分方程及 Grönwall 给图和逆图 Jacobian 范数 `≤exp(ell)`。正作用域避开零，使极坐标图及局部逆图有定义。角的全局多值性不被局部 Jacobian 界消除。

本轮直接执行融合原脚本，其有理数同调恒等式检查通过。两套完整余项是 `4.689940278267777e−13`、`6.293752412502822e−13`，图域余量分别为 `0.008680451129618762`、`0.008680412929660535`。这是融合稿 **2 配置自由度**、`r_out=.03` 辅助域的结果，不是新三维结果，也不覆盖融合稿主控制初值最大分量 `.09`。超越函数数值和上述余项评价仍是普通浮点主控量，不是向外取整区间证书。

## 3. 把有限特征主控界接入真正的 24 维冻结学习对象

S5-L01 没有学习一个磁势系数；它的机械字典是 `Q³(364),Q⁴(1365),QP²(936),Q²P²(6084)`，共 8749 项，和 7104 实参数全复隐藏层、13440 参数 SPD 网络分开实验。旧 v10 的 35 维完整余弦/混合四次字典是另一个历史对象。本次不重训、不替换它们。

设冻结多项式输出为 `P(x)=s Σθ_α x^α`，`x=Dz` 是实际 12 自由度 ROM 的训练尺度，`z=(Q,P)` 是正则变量。解析延拓时 24 个 `z_j` 独立取复值。则

\[
P(Dz)=\sum_\alpha c_\alpha z^\alpha,
\qquad c_\alpha=s\theta_\alpha\prod_jD_j^{\alpha_j}.
\]

`from_checkpoint` 直接读取 S5-L01 的指数缓冲区与所有冻结系数，完整展开为 8749 个不同的 24 变量单项式。本轮与原 `MechanicalPolynomial.forward` 的独立 PyTorch 自动微分核对能量及 `∇_z=D∇_x`，没有把归一化梯度冒充正则向量场。

对 `|z_j|≤ρ_j`，逐项三角不等式给

\[
\begin{aligned}
|P|&\le\sum_\alpha|c_\alpha|\rho^\alpha=:B_0,\\
|\partial_iP|&\le\sum_\alpha|c_\alpha|\alpha_i\rho^{\alpha-e_i}=:B_i,\\
|\partial_i\partial_jP|&\le\sum_\alpha|c_\alpha|\alpha_i(\alpha_j-\delta_{ij})
 \rho^{\alpha-e_i-e_j}=:B_{ij}.
\end{aligned}
\]

不存在的导数项为零。由 Cauchy–Schwarz，冻结特征参数的误差若已独立满足 `||Δθ||₂≤b`，则

\[
\|\Delta P\|_\rho\le
b\,B_F(\rho),\quad
B_F=s\bigl(\sum_\alpha[(D\rho)^\alpha]^2\bigr)^{1/2}.
\]

这是旧 `theorem_bridge.tex:180–264`、融合 `kam:feature-bounds`/`sr:majorant` 真正进入新三维代码的部分。得到真实 `H*−Hhat` 的统一复域误差，还需要：无常数规范方向的实际设计矩阵 Gram 下界、同归一化的独立观测误差、真实 ROM 复解析域与类外余项界。S5-L01 的实域有限测试误差不提供这些输入，程序保留 `true_ROM_uniform_complex_error_bound=null`。全复隐藏层还需要逐层 tanh 极点裕量；本次多项式界不代替该网络的界。

## 4. 冻结机械多项式的精确局部 Legendre 充分域

这是本轮新增的可证明结果，限定于同一三维 ROM 上训练的冻结机械模型。其能量为

\[
\widehat h(z)=\tfrac12a^2|Dz|^2+P(Dz),\qquad a=.08.
\]

`P` 关于动量至多二次且为偶函数。以归一化动量 `x_p` 求 Hessian，`P_{x_px_p}` 只依赖 `x_q`。若 `|x_{q,j}|≤r`，设每行绝对主控和为

\[
L_i(r)=s\sum_{\alpha\text{含}P^2}\sum_j
 |\theta_\alpha|\alpha_{p_i}(\alpha_{p_j}-\delta_{ij})r^{|\alpha_q|}.
\]

对称矩阵的 Gershgorin/行范数估计给
`a²I+P_xpxp ≽ δ(r)I`，其中 `δ(r)=min_i[a²−L_i(r)]`。
从 `H_PP=D_p(a²I+P_xpxp)D_p` 得，当 `δ>0`，

\[
\widehat h_{PP}\succeq\delta(r)\min_iD_{p,i}^2 I>0.
\]

所有 checkpoint 浮点权重、输出尺度和 `float(a**2)` 被视为该冻结点多项式的精确二进制有理系数；`r=1/20` 用精确分数。`exact_normalized_momentum_bound` 用 `Fraction` 进行每个绝对值、乘法和求和，JSON 保存完整有理分数。因此这个**代数点模型**的正定判据不依赖浮点评价余量。它不包围物理参数误差，也不保证浮点执行的所有舍入误差。

三种子在 `|D_q Q|≤1/20` 的下界约为 `0.2500000261,0.2478039198,0.2417770408`。由于该模型对 P 二次，给定此域中的任意 Q，`P→∂_P hhat` 是对所有实 P 的可逆线性映射；不是整个相空间的非线性全局坐标图证明。在 `r=1/10` 同一充分判据失败。失败意味着主控界不能认证该较大域，**不是**已经找到负 Hessian；阶段二/五的真实负样本另行保留。

普通浮点的复杂域能量/导数主控与此精确有理 Legendre 检查分别保存，不能把后者准确性外推到真实 ROM、全复网络或 KAM。

## 5. 三维同调方程的共振门槛不能跳过

在合法复正则变量 `ζ=(Q+iP)/√2,χ=(Q−iP)/√2` 下，独立复化有

\[
\{h_2,\zeta^\alpha\chi^\beta\}
=i\nu\cdot(\alpha-\beta)\zeta^\alpha\chi^\beta.
\]

旧双模态四阶无非动作共振，故角平均可作为完整四阶核。实际三维 ROM 的四对 1:1 共振使这个步骤不成立。本轮直接重新调用实际 `RodROM.nu`，枚举全部 17550 个四阶单项式，阈值 `1e−10` 下有 206 个核项，其中 78 个动作项、128 个非动作项。`homological_compatibility` 对旧 action-only 模板返回拒绝。

阶段五已有的正确进展保留：三阶消元后应是 `Π_res(H4+{H3,W3}/2)`；第一对限制中括号仍需保留全部 12 通道。其候选 `A N²+B L²`、外子空间不变性反例和高阶 AD 失败来源，见 `stage5/proofs/chnn_kam_restored.md:110–158`、`stage5/results/resonance/S5_R02_*`、`S5_R04_partial_scope.json`。不能用旧余弦两模态余项替代该系统的 12 维共振余项。

## 6. 连续与离散 KAM 的未完成责任

有限特征 Gram 定理与旧统计强范数定理是两个不同条件链；后者需要 iid、密度、统一高阶正则性和参数类界，连续轨迹不会自动满足。旧冻结有限幅值环面、64 平面自由度提升和 S 路径不利对照仍按原 Hamiltonian/原权重保存；不能在新参数点或新维数上继承数值常数。

连续 KAM 需要新保守解析对象、可积/共振约化基准、完整 twist 逆与域、全整数连续小除数和足够小的扰动。离散 KAM 另外需要同一 **理想 exact-symplectic 自治映射**、合法周期生成函数与图域，以及

\[
|e^{i\Delta k\cdot\omega}-1|\ge\Delta\gamma_D|k|^{-\tau_D},\qquad
\|G_\Delta/\Delta\|\le C_3\epsilon+C_4\Delta^p.
\]

取单频 `ω=2,Δ=π`，连续除数非零而离散除数为零，是可执行最小反例。三维共振、实际磁端口不可达残差、阻尼/血流/接触、非自治图序列、浮点 Newton 残差均不能通过这两个公式自动获得证书。融合 `kam:map-theorem` 明写条件性，缺定理阈值、`C3,C4` 与独立观测误差；本轮保留而不改写为已完成。

参考文献定位已对照融合 `references.tex`：Chen–Matsubara–Yaguchi 2022 DOI `10.1609/aaai.v36i6.20582`；Shang 1999 DOI `10.1007/s002110050460` Theorem 2/Remark 2/§4；Pöschel arXiv `0908.2234v1`；Haro–Luque arXiv `1711.05515v1` Theorem 3.1。这里检查了项目引用的假设与使用方式，没有声称重新证明外部论文全篇常数，也没有新增三维 KAM 证书。
