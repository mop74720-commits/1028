# E01–E16 修正、端点生成定理与原（30）—（36）的完整连接

本阶段以 `f3aa09c` 的冻结审计为起点；不修改原稿、旧论文或历史结果。本文件在实际读取 stage4 的专题审计、原生 OMML 索引及旧推导后，将修正写成可调用程序和测试。程序为 `stage5/program/corrected_identities.py`，独立测试为 `stage5/tests/test_corrected_identities.py`；实际运行状态见 `stage5/results/corrected_identities/latest.json`，每次运行另存独立目录。**测试通过表示所列恒等式、反例和有限数值基准通过，不表示完整血流接触机器人或 KAM 已证明。**

原稿 p/m 指 `stage4/audit/source_omml/original1025_indexed.json`；阅读文本第 N 行对应 pNNNN。原(30)、(31)、(32)、(33)、(34)、(35)、(36)分别位于 p0910/m0400、p0920/m0408、p0931/m0417、p0961/m0427、p0963/m0429、p0986/m0434、p1003/m0442；最后一式重复于 p1070/m0470、p1220/m0570。A 的陈述在 p0862–0879、附证在 p1179–1206；B 在 p0881–0888、附证在 p1208–1213。矩阵、分式、上下标以原 XML 为准。原编号不连续，不补造缺号。

主要有效旧推导是 `stage3/source_inputs/v10/v10_framework_20261028/english/sections/{supp_mechanics,supp_structure,controlled_analysis}.tex`、`stage3/source_inputs/birkhoff/一般Birkhoff_两个核心连接与验证.md` 和 `stage3/source_inputs/starter/stage2/report/stage2_complete.md` 第5、7、8章。这里恢复其内容并明确适用假设；输运和实际高维图算法的进一步实现见同目录 `birkhoff_transport.md`，非可分 Central4 的实际积分由阶段5对应模块负责，不能把下面符号回归当作高维实际运行。

## 1. E01–E03：力学对象、实值载荷和功率

### 1.1 Morison 的量纲修正与作用域（E01）

取单位切向量 t、横向投影 `P⊥=I−ttᵀ`，流体速度 u、杆速度 v，流体物质加速度 `a_f=∂_t u+(u·∇)u`、杆加速度 a。令 `w=P⊥(u−v)`。一个明确的移动细圆杆经验闭合是

\[
f_h=\rho_f A P_\perp a_f+
\rho_f C_A A P_\perp(a_f-a)
+\tfrac12\rho_f C_D D\,|w|w.
\tag{R1}
\]

三项均为当前长度上的 N/m；换成参考长度须乘伸长比。`C_A` 是附加质量系数，压力加速与附加质量合并后的流体加速度系数是 `C_M=1+C_A`。原 p0040 的 `r_tt−V_f` 把加速度与速度相减，不能通过重命名 C 修复；二次拖曳缺 D 也不满足这一线力单位。移项时 `−c|v−u|(v−u)=−c|v−u|v+c|v−u|u`，第二项不能漏。

拖曳的相对功率为 `f_D·(v−u)=−ρ_f C_D D |w|³/2≤0`；杆本身的 `f_D·v` 可以为正，脉动血流可以输入机械能。`corrected_morison_transverse` 分别返回压力、附加质量、拖曳和这两种功率。测试使用三维横向投影、独立的速度/加速度缩放和正杆功率例。它没有校准 Morison 对受限血管、低 Re、近壁或非 Newtonian 流体的有效性；Re、Womersley、KC、堵塞/间隙及壁运动条件仍需另验。不能把 R1 无条件叠加到已经解牵引的双向 FSI 上。

### 1.2 实穿透、罚势与摩擦（E02）

定义间隙 `g≥0` 为分离，`δ=(−g)_+`。对 k≥0、a>0，

\[
V_c=\frac{k}{a+1}\delta^{a+1},\qquad
\lambda_n=k\delta^a,\qquad F_n=-\nabla V_c=\lambda_n\nabla g.
\tag{R2}
\]

在 g<0 区域由 `dδ/dg=−1` 直接得到，g>0 为零。接触法线朝增大间隙方向；若坐标约定相反，必须同步改 g，不能再随意翻转力。原 `d≤d0` 下 `(d−d0)^1.5` 非实，正确穿透是 `(d0−d)_+`。此修正保留罚能的可微结构，但 a=3/2 的接触力在开闭点不是解析函数；罚模型也不等于真实柔性壁 Hertz 参数。

令 `v_t` 是表面接触点相对壁的切向速度，包含旋转贡献。正则摩擦

\[
F_t=-\mu\lambda_n\frac{v_t}{\sqrt{|v_t|^2+\epsilon^2}},\qquad
F_t\cdot v_t=-\mu\lambda_n\frac{|v_t|^2}{\sqrt{|v_t|^2+\epsilon^2}}\le0.
\]

`contact_penalty` 和 `regularized_friction` 实现这些式子；测试独立差分罚能验证法向力，并检查相对功率。它们不证明切换解唯一性、严格不穿透、整个壁面的光滑性或全系统 KAM。

### 1.3 Darboux 符号和中心线无法恢复扭转（E03）

若约定 `t_s=u×t`、`|t|=1`，则
`t×t_s=t×(u×t)=u−(u·t)t=u_perp`。因此 `t_s×t` 是相反向量。若原文只是另命名反向副法线，这本身不错误；错误是把它再当同一 u 的横向分量。`darboux_perpendicular` 明确采用上述约定并验证单位/正交条件。

同一条直中心线 `r=(0,0,s)` 可对应 `R=I` 或 `R=Rot_z θ(s,t)`。两者 r、r_s 完全相同，而后者有 `κ_3=θ_s`、`Ω_3=θ_t`，能量含 `∫(GJ_p θ_s²+J_3 θ_t²)/2 ds`。因此中心线四阶梁式不能无条件替代三维角动量方程。完整 Cosserat 保留伸长/剪切/弯扭；12配置 DOF Kirchhoff ROM 是不可伸长、不可剪切的独立理论分支，仍保留材料标架与扭转。圆截面扭转刚度为 `GJ_p`，不能无条件写成 `EI_3`。

## 2. E04、E05、E16：复坐标、功率损失和真正物理耗散

### 2.1 统一复坐标及损失

先作明确的正则尺度化，才能把不同单位的 q 与 p 组成

\[
\xi=(q+ip)/\sqrt2,\quad
q=(\xi+\bar\xi)/\sqrt2,\quad
p=(\xi-\bar\xi)/(i\sqrt2).
\]

链式法则逐项给

\[
\partial_\xi=(\partial_q-i\partial_p)/\sqrt2,
\quad \partial_{\bar\xi}=(\partial_q+i\partial_p)/\sqrt2,
\quad \dot\xi=-iH_{\bar\xi}+iQ_{nc}/\sqrt2.
\tag{R3}
\]

由右式实虚部分别恢复 `qdot=H_p,pdot=−H_q+Qnc`。原 p0351 的 1/2 不适用于已缩放的 ξ；后文未缩放 `z=x+iy` 的 1/2 仍正确。两个错误因子有时抵消，修正必须同时进入预测器、损失和作用角式。`complex_coordinates`、`wirtinger_real_energy`、`complex_hamiltonian_rhs` 共用 R3，并在两自由度带真实动量端口的回归上逐分量核验。

对实 H、P，`Htilde=√2(H+iP)` 满足

\[
|\dot{\widetilde H}|^2=2\dot H^2+2\dot P^2.
\tag{R4}
\]

原 p0591 省去第一项需另外证明 `Hdot=0`，不适用于一般受迫耗散机械能。`complex_energy_rate_squared` 保留两项。HNN 损失必须使用与预测器一致的 `H_barξ`；不能损失用 `H_ξ`、推进用 `H_barξ`。这些修正不把一般非保守向量场变成一个实 Hamiltonian 梯度。

### 2.2 变质量与 Rayleigh 链式法则

对时间独立机械嵌入、正定 `M(q)`，

\[
p=M(q)v,\quad H=\tfrac12p^TM^{-1}p+V(q),\quad
\dot q=v=M^{-1}p,\quad
\dot p_i=\tfrac12v^T M_{,i}v-V_{,i}+Q_i.
\tag{R5}
\]

因为 `∂_iM⁻¹=−M⁻¹M_,iM⁻¹`，R5 与 `−H_q+Q` 等价；将 `pdot=M qdd+Mdot v` 代回即得完整 Christoffel 几何惯性。`mechanical_field` 实现 R5，规定张量次序 `dM[i,j,k]=∂_(q_i)M[j,k]`。独立符号 H 梯度测试确认非零几何力，而非用另一份同样漏项的实现作“参考”。

若 Rayleigh 耗散函数为 `D(q,v)`，先对 v 求导：`Q_R=−D_v(q,v)`，再代 `v=M⁻¹p`。令 `G(q,p)=D(q,M⁻¹p)`，在固定 q 下

\[
\nabla_pG=M^{-T}D_v,\qquad Q_R=-M^T\nabla_pG.
\tag{R6}
\]

机械质量对称时为 `−M∇pG`，一般不是 `−∇pG`。`rayleigh_force_from_momentum_gradient` 实现并检查机械质量的正定性。测试对非对角质量及含四次速度项的 D 独立符号求导，覆盖速度相关系数的附加导数。对一般学得非二次动量能量，`v=H_p` 导出 `∇pG=H_ppᵀD_v`；只有 H_pp 可逆时才可用 `−H_pp^{-T}∇pG`，不能继续无条件套常质量因子。

机械功率恒等式为 `Hdot=H_t+H_pᵀQ`。机械能衰减不等于封闭总能量消失；完整 Metriplectic 另需内能/熵状态、Poisson Casimir 与能量退化。当前这些函数不伪造血流、温度或空间站生理参数。

## 3. E06、E12–E14：一形式、变分符号与输运体积

采用列向量 `z=(q,p)∈R^(2n)`、`(Da)_ij=∂_j a_i`、`J=[[0,I],[-I,0]]`、`K0=−J`。取

\[
\alpha_t=a(z,t)^Tdz,\quad
\Omega_t=d\alpha_t=\tfrac12\sum_{ij}K_{ij}dz_i\wedge dz_j,
\quad K=(Da)^T-Da.
\tag{R7}
\]

对固定两端的 `∫[a·zdot−B]dt` 变分并把 `a·δzdot` 分部积分：

\[
\delta\mathcal A=\int\delta z^T
\{[(Da)^T-Da]\dot z-a_t-\nabla B\}dt,
\quad Kf=\nabla B+a_t.
\tag{R8}
\]

故原约定 `D=−∇B−a_t` 下必须 `f=−K⁻¹D`。原 p1120 的 `Kij,t=∂jDi−∂iDj` 本身正确；p1180 的 `+K⁻¹D` 与该约定矛盾。代码分别提供两种命名清晰的求解函数及时间相容残差，不让 D 的符号隐含在接口里。

原 p1125 全指标和没有1/2，p1156 又真实推导出其等于 `2dα`。R7 的 1/2 保证 `Ω(v,w)=vᵀKw`。由 `d²=0` 得闭性，不能由此推出 `detK≠0`；全域恰当还取决于拓扑，局部星形图可用 Poincaré 引理。

令 `b=Kf`。相容式 `K_t=Dbᵀ−Db`，结合空间闭性得

\[
K_t+(f\cdot\nabla)K+(Df)^TK+KDf=0,
\quad\partial_t\Omega+\mathcal L_f\Omega=0.
\tag{R9}
\]

积分后 `Φ_(t,s)^*Ω_t=Ω_s`，进而 `Φ^*(Ω_t^n/n!)=Ω_s^n/n!`。欧氏 Jacobian 行列式不必为1；等价密度式是

\[
\det D\Phi\;\frac{\sqrt{|\det K_t(\Phi z)|}}{\sqrt{|\det K_s(z)|}}=1
\tag{R10}
\]

对近恒等、保定向的局部流成立。比例阻尼 n 自由度有 `detDΦ=e^(−nγh)`、`K_t=e^(γh)K_s`，恰好相消。`transported_volume_ratio` 及三自由度解析矩阵流回归检验此区别。矩阵指数只用于已知线性测试，不是实际三维图算法的免费精确流。

原候选一形式的根本问题是混合偏导：若 `∂p a_q=1`，则 `∂t∂p a_q=0`；若又要求 `∂t a_q=γp`，则 `∂p∂t a_q=γ`，γ≠0 时矛盾。改写 `a_q=(1+γt)p` 虽给某个函数，却不再满足原来的固定正则结构要求。正确修复是构造相容 a、K、B，随后测量原场表示残差；高阶输运/规范/数值 Moser 的实现和域限制另见本阶段输运证明。规范不能消除本来非零的表示误差。

## 4. E07：Theorem A 的完整局部命题与证明

固定端点时间 s、t，设 Ω_s、Ω_t 为闭、非退化二形式，Φ 为局部微分同胚并满足 `Φ*Ω_t=Ω_s`。设联合端点变换

\[
\mathcal E:(z_+,z_-)\longmapsto(\widehat w,w)
\]

在考虑邻域可逆，且满足**端点适配**

\[
\mathcal E^*d(\widehat w^Tdw)=\Omega_t(z_+)-\Omega_s(z_-).
\tag{A1}
\]

式中时间固定；时间变换的显式导数在下一节处理。记 `d=2n`、`D E=[[A,B],[C,D]]`（各块 d×d）、`M=DΦ`。对图嵌入 `ι:z_-↦(Φ(z_-),z_-)`，由 A1 得

\[
d\,\iota^*\mathcal E^*(\widehat w^Tdw)
=\Phi^*\Omega_t-\Omega_s=0.
\]

若横截矩阵 `T=CM+D` 非奇异，隐函数定理保证 w 是流图像的局部坐标。取足够小的单连通（例如星形）w 域，则闭一形式 `widehat w(w)^Tdw` 有局部势 φ：

\[
\widehat w=g(w)=\nabla_w\phi,
\qquad N=D_wg=(AM+B)(CM+D)^{-1}=N^T.
\tag{A2}
\]

推导 N 时对两端点图分别微分：`dwidehatw=(AM+B)dz_-`、`dw=(CM+D)dz_-`，因此**右乘** T⁻¹，矩阵不可交换。φ只在加一个与 w 无关的时间函数意义下唯一；要唯一值须指定例如 `φ(w*,t,s)=0` 的规范，不得宣称天然唯一。

反过来，从局部标量 φ 出发，用完整联合逆 `E⁻¹(∇φ,w)` 得 `z_+(w),z_-(w)`。必须另有 `D_w z_-` 非奇异，才定义 `z_+=Ψ(z_-)`。拉回 `d(∇φ·dw)=0`，A1 给 `Ψ*Ω_t=Ω_s`，完成反向结构命题。局部定义域、端点留域和分支选择是命题的一部分。

若相应块可逆，可由 `N(CM+D)=AM+B` 写

\[
(A-NC)M=ND-B,\qquad
M=(A-NC)^{-1}(ND-B).
\tag{A3}
\]

等价地用完整联合逆的导数 `D E⁻¹ [N;I]`，再对负端点投影求逆。**从不需要 N 本身可逆。** 正则中心图在恒等映射处 N=0，横截矩阵仍可逆。`endpoint_gradient_jacobian`、`reconstruct_flow_jacobian` 分别实现 A2/A3，并让奇异线性系统显式报错，而非用伪逆冒充合法局部反解。

只有联合变换和投影可逆仍不够。谐振子真辛旋转取 `widehatw=z_+−z_-`、`w=(z_++z_-)/2`，则 A2 的 N 一般反对称而非对称；欠缺的是 A1。测试明确重现此反例。`endpoint_compatibility_defect` 实际检查

\[
(D\mathcal E)^T J_d(D\mathcal E)
-\operatorname{diag}(K_t,-K_s),\quad
J_d=\begin{pmatrix}0&I_d\\-I_d&0\end{pmatrix}.
\]

这一步与投影条件数、场误差是三个独立检查。24维端点回归验证矩阵恒等式，不声称为任意血流接触场构造了全域 E。

### 4.1 初始生成函数、规范与演化中横截条件

在 t=s 时将对角嵌入 `z↦(z,z)` 代入 E。若初始投影
`w_0(z)=E_2(z,z,s,s)` 的导数 `C_0+D_0` 可逆，先反解 z=z(w)，再令
`c_0(w;s)=E_1(z(w),z(w),s,s)`。A1 在对角上的拉回为零，故
`Dc_0` 对称。在星形邻域以 w* 为中心，可实际选取

\[
\phi_0(w;s)=\int_0^1 c_0(w_*+r(w-w_*);s)^T(w-w_*)\,dr.
\tag{A4}
\]

对任意方向 v 对积分求导，并用 `Dc_0=Dc_0^T`，被积式为
`d[r c_0(w_*+r(w-w_*))^T v]/dr`，所以 `D\phi_0[v]=c_0(w)^Tv`，
且 `\phi_0(w_*;s)=0`。原正则中心端点变换在对角上给 c0=0，故这个规范下
φ0=0；一般端点变换不能未经计算就把初始生成梯度设零。

`radial_generator_potential` 用 Gauss–Legendre 求积实现 A4，并明确要求调用者先
验证闭性和星形域；对非闭向量场作路径积分本身并不能恢复生成函数。独立回归采用
`E_1=J(z_+−z_-)+∇ψ(w)`、`E_2=w`，其中
`ψ(w)=w_1³/3+w_2²/2+w_1w_2`。精确梯度规范保持 A1，却有非零 c0；程序同时
核验端点拉回、初始 Jacobian 和积分结果 `φ0=ψ(w)−ψ(w*)`，避免只检验 c0=0 的
特殊中心情形。

初始横截只保证存在一个小时间邻域。若 T(t,w) 连续，初始点最小奇异值为
σ>0，且在所用闭邻域满足 `||T(t,w)-T(s,w_*)||_2<σ`，则 Weyl 不等式给
`σ_min(T)>0`。反向端点投影也须有同类界。局部延拓只能持续到端点离开共同域、
联合端点逆失效或横截矩阵奇异之前。当前程序报告采样奇异值与条件数，未认证上述
整个闭邻域的统一界，不能据此宣称任意窗口的全局生成函数。

## 5. E08–E09：Theorem B 的固定生成坐标 PDE 与递推

固定初始时间 s。沿真实末端演化，初端 `z_-` 不动，故

\[
\dot{\widehat w}=A_\alpha f(z_+,t)+\alpha_{1,t},\qquad
\dot w=C_\alpha f(z_+,t)+\alpha_{2,t}.
\]

另一方面 `widehatw=g(w,t;s)`，链式法则是 `dotwidehatw=N dotw+∂_t g|_w`，从而

\[
\left.\partial_tg\right|_w
=(A_\alpha-NC_\alpha)f(z_+,t)
+\alpha_{1,t}-N\alpha_{2,t}
=:\Psi(g,w,D_wg,t;s).
\tag{B1}
\]

这里 `z_+` 以及 A、C、显式时间导数，都通过**联合端点逆** `E⁻¹(g,w,t,s)` 评价；若先使用时间图 χ_t，则其时间项不能删除。不能把沿移动 w 的物理轨道导数误叫固定 w 的 Taylor 系数。`fixed_endpoint_rhs` 实现 B1，测试用独立可解非自治振子对固定 w 差分核验，不调用未知三维精确流。

假设 f、两端结构及 E 在共同局部复邻域解析，联合逆、两端投影在该邻域非奇异。解析流与解析隐函数定理给实际局部 g 的解析性。令 τ=t−s、`g=Στ^k c_k(w;s)`，c0 来自 `E(z,z,s,s)`。逐幂比较 B1 得

\[
c_{r+1}=\frac1{r+1}[\tau^r]\Psi\!\left(
\sum_{j=0}^{r}\tau^jc_j,w,
\sum_{j=0}^{r}\tau^jD_wc_j,s+\tau;s\right).
\tag{B2}
\]

特别 `c1=Ψ0`、`c2=(Ψ_t+Ψ_g c1+Ψ_N[D_wc1])0/2`；最后项是对矩阵 N 的 Fréchet 导数作用，不能省略。等价 `c_(r+1)=D_t^r Ψ|_s/(r+1)!` 中的 D_t 也必须沿该固定 w 的 PDE 作全链式求导。原 p0888 下标 k 错位，而 p1213/m0565 已正确写 k+1；应恢复其正确末附推导，不删去整个定理。

由 A2 的 N 对称与解析展开唯一性，逐系数 `D_wc_j` 对称。因此每一系数是局部标量梯度；在共同星形域选择规范可写 `c_j=∇φ_j`。有限截断 `g^[r]=∇Σ_(j=0)^r τ^jφ_j` 仍为精确梯度，经 A1 和反向横截条件重构，得到保持指定两端二形式的局部图。

精度责任另行成立：若截断梯度误差在共同域为 `O(h^(r+1))`，联合逆和负端点重构有统一稳定常数，则局部状态缺陷也是该阶；加一步稳定因子 `1+O(h)` 才得固定时间全局 r 阶。对称结构可使偶次项消失、提高阶数，不能只数保留了几个项。只有有限光滑时可证明有限 Taylor 余项，不能宣称形式无限级数收敛。当前有限数值测试没有认证实际 ROM 的统一解析域和所有常数。

### 5.1 可计算的标量中心递推，不把精确流作为输入

在正则坐标 y 选 `w=(y_++y_-)/2`、`widehatw=J(y_+−y_-)=∇φ`，联合逆为

\[
y_+=w-\tfrac12J\nabla\phi,\quad
y_-=w+\tfrac12J\nabla\phi.
\]

此时 A=J、C=I/2。代 B1 并取梯度，得到规范化 Hamilton–Jacobi 方程

\[
\partial_t\phi(w,t;s)=-\mathcal H\left(w-\tfrac12J\nabla\phi,t\right),
\quad\phi(w,s;s)=0.
\tag{B3}
\]

验证右侧梯度为 `−(I+NJ/2)∇H=(J−N/2)J∇H`，恰与 B1 一致。故标量递推

\[
\phi_{r+1}=-\frac1{r+1}[\tau^r]\,
\mathcal H\left(w-\tfrac12J\nabla\sum_{j=1}^{r}\tau^j\phi_j,s+\tau\right)
\tag{B4}
\]

仅依赖所给 H 及其导数，不需调用未知流。`central_generator_coefficients` 逐项实际计算 B4；测试非可分变质量例 `H=(1+q²)p²/2+q²/2+q⁴/4` 得 `φ1=−H,φ2=φ4=0,φ3=−fᵀH″f/24`。非自治 `H+tq²/2` 给 `φ2=−q²/4`，说明不能把自治奇次结构直接搬到一般时间图。此符号基准并未证明高维符号运算成本可控；实际高维方法应利用 AD/方向导数并记录成本。

## 6. 原（30）—（36）完整变量、矩阵和适用条件

### 6.1 原（30）、（31）的联合矩阵

令物理或已正则化端点顺序为 `Z=(q_+,p_+,q_-,p_-)`。原变量

\[
\widehat Q=p_+-p_-,\quad\widehat P=q_+-q_-,
\quad Q=(q_++q_-)/2,\quad P=-(p_++p_-)/2
\]

由下面 4n×4n 矩阵给出：

\[
L=\begin{pmatrix}
0&I&0&-I\\I&0&-I&0\\I/2&0&I/2&0\\0&-I/2&0&-I/2
\end{pmatrix},\qquad
L^{-1}=\begin{pmatrix}
0&I/2&I&0\\I/2&0&0&-I\\0&-I/2&I&0\\-I/2&0&0&-I
\end{pmatrix}.
\tag{C30-31}
\]

因此 `q±=Q±hatP/2,p±=−P±hatQ/2`，没有任何 `N⁻¹`。直接矩阵乘法给 `LᵀJ_(2n)L=diag(K0,−K0)`，所以对固定正则端点满足 A1。对一般时变 Birkhoff 系统，须先分别使用两个合法 χ_t、χ_s，提升后的动量 Π 才可代入同一中心关系；物理 p 直接平均不自动匹配任意 K。代码中 L 与联合逆对24维相端点执行了回归。

### 6.2 原（32）的固定初端导数与（33）、（34）的梯度责任

负端固定时，

\[
\dot{\widehat w}=\binom{\dot p_+}{\dot q_+},\qquad
\dot w=\tfrac12\binom{\dot q_+}{-\dot p_+},\qquad
\partial_tg|_w=\dot{\widehat w}-N\dot w.
\tag{C32}
\]

原 p0931 交换分量并漏负号，不是另一种合法记号。对正则保守场，`c1=(-H_q,H_p)|_(q=Q,p=-P)=∇_w[-H(Q,-P)]`。一阶中心标量 `φ=−hH(Q,−P,t_mid)` 重构完整时间中点；这是合法的（33）—（34）分支。

若原物理阻尼 `pdot=−q−γp`，在 P=−p 下候选为 `(-Q+γP,-P)`，其 Jacobian 的(1,2)为γ、(2,1)为0。即使修正阻尼符号，它仍不是梯度。必须先改变相容二形式/合法图，而不能给向量命名“生成梯度”就认为存在标量。`gradient_integrability_defect` 的 E10 测试重现这个不可积性。

### 6.3 原（35）的变质量完整式

令 `qbar=(q_++q_-)/2,pbar=(p_++p_-)/2,tbar=(t+s)/2`，

\[
q_+-q_-=hM(\bar q)^{-1}\bar p,
\quad p_{+,i}-p_{-,i}=h\left[-\tfrac12\bar p^T(\partial_iM^{-1})(\bar q)\bar p
-V_{,i}(\bar q)+Q_i(\bar q,\bar p,\bar t)\right].
\tag{C35}
\]

质量、势、真实血流/接触/控制及非自治时间必须一致评价。变质量时这是完整隐式系统，不是把 M 在初态冻结后作显式消元。固定求解预条件矩阵不等于冻结物理 M；停止判据必须检查 C35 的真实残差。光滑保守分支为二阶正则辛中点；一般阻尼中点仍二阶，但通常不保固定 K0 或某个预先指定的时间 K。

### 6.4 原（36）的非交换左解

仅在常 M、常恢复矩阵 K_s、常阻尼 C，且给定中点外力 F 的线性分支，C35 给

\[
\bar q=q_-+\tfrac h4M^{-1}(p_++p_-),\qquad
E=\tfrac{h^2}4K_sM^{-1}+\tfrac h2CM^{-1},
\]
\[
(I+E)p_+=(I-E)p_--hK_sq_-+hF,
\qquad q_+=q_-+\tfrac h2M^{-1}(p_++p_-).
\tag{C36}
\]

推导直接将第一式代入动量式，将所有 p_+ 项左移；无需 M、K_s、C 可交换。需 `I+E` 非奇异；小 h 时由连续性局部成立，任意大 h 不自动保证。程序用左线性求解，绝不写列向量右乘“分式”或逐元素除法。独立基准直接解完整一阶矩阵中点，验证与 C36 相同，并保留错误 `M⁻¹K_s` 次序的非零反例。若 F 是未知中点反馈，C36 仍隐式，不能假装已经给出显式一步。

## 7. E15：辛与恰当辛、以及不同证明责任

闭一形式不必恰当。环域上的 `β=ΣI0_j dθ_j` 满足 dβ=0，但基本周期为 `∮β=2πI0_j`。若有非零 I0，它不是单值函数的微分。旧 v10 `stage4/audit/external_v10/sections/measure_proof.tex:153` 的管图只证明这种差一形式闭，故应称辛图；若移动参考原函数为 `(I+I0)·dθ`，需明确说明这一改变。测度变换仅用辛体积，不能因该措辞错误把有效体积论证一并删除。

`torus_primitive_periods` 和独立圆环参数积分验证非零周期；未覆写旧冻结 TeX。相比之下，中心离散映射若有单值 S、隐式分支，`δq=S_p,δp=−S_q` 给

\[
p_+dq_+-p_-dq_-
=\bar p\,d\delta q+\delta p\,d\bar q
=d(\bar p^T\delta q-S).
\tag{R11}
\]

这是另一个独立的恰当辛证明，不受旧管图措辞牵连；在非单连通角域仍需单值/周期原函数及共轭的适当条件。有限求解容差会引入结构误差，不能把理想隐式映射的 R11 直接当实际浮点程序恒等式。

旧管图还有一个可以保留而不误称原图恰当辛的精确修正版。设管域是
`T^n×U`，其中 U 为可缩的小作用域，F 为辛管图，`λ=p·dq`、`λ0=I·dθ`。
则 `β=F*λ−λ0` 闭。以 n 个基本角循环定义
`I0_j=(2π)^(-1)∮_(γ_j)β`；闭性保证在同一同调类上积分不依赖所取作用值。
`β−ΣI0_j dθ_j` 的全部基本周期为零，沿路径积分因此与路径无关，给出单值 S，
于是

\[
F^*\lambda=(I+I_0)^T d\theta+dS.
\tag{R12}
\]

这是明确给出作用常数和参考原函数后的恰当关系；并不是对原 `I·dθ` 原函数
直接宣称 I0=0。若新作用变量 J=I+I0，需同时平移定义域和 Hamiltonian，
不能只在证明中删除常数。辛体积由 `dλ` 决定，故旧管测度推导不受此常数影响。

此外，管图自身不恰当辛不必否定一个被共轭后的离散映射。若原映射 Ψ 满足
`Ψ*λ−λ=dA`，且 `G=F^(-1)ΨF` 在管域同伦于恒等，则
`G*λ0−λ0=d(A∘F)+β−G*β`。G 对第一上同调作用为恒等，故后两项之差闭且
周期为零，从而也恰当。此结论需要所有复合映射留在该管域以及同伦条件；当前
未用它重新认证任何历史冻结环面或三维 KAM。

局部可解性、有限时间收敛、控制可达性与 KAM 各有独立责任。中点的压缩条件 `hL/2<1` 还需域映回自身；仅一次 Newton 条件数好不构成统一唯一性。控制改变实际场后要检验 `L_gΩ=0` 或构造新的 K_u；共点负功率不等于辛性。连续或离散 KAM 还需真实保守/解析域、正规形、非退化、全整数小除数及小量界。新三维1:1共振未因上述16项修正消失，完整血管机器人也未因代数测试通过而完成。

## 8. 已执行、修复边界和复算

```sh
PYTHONDONTWRITEBYTECODE=1 /workspace/1028-cloud/venvs/learning/bin/python stage5/program/run_corrected_identities.py
```

实际输出按运行生成，`latest.json` 指向最新一次，`runs/` 保留各次日志、命令、版本、容差来源、耗时、源码前后哈希和逐测试状态。首轮18项通过：E01–E16各一项，另加24维端点联合逆及非零几何惯性独立验证。后续发现小SI量级质量矩阵不能使用固定绝对对称阈值，已将 `_spd` 改为相对尺度的对称检验并拒绝非有限值；新增独立反例后，`20261029T152011_509777Z` 实际19项通过。初始非零生成函数的非线性端点规范测试加入后，`20261029T174049_252985Z` 实际20项通过；全部早期日志仍保留。测试适用范围在程序文档、证明和账本均单列。若后续真实三维场/控制模块采用这些修正，其源码/新结果将另记到 `repair_status.csv` 和 `inheritance_update.csv`；不依据“导出115行”或“16项测试成功”批量宣布全部研究缺口已闭合。
