# 一般 Birkhoff 路线：两个核心连接、控制与数值验证

## 本轮目标与证据范围

本笔记沿原草稿的顺序补充，不覆盖原稿：完整物理模型 → 正则有限维动力学 → Birkhoff 表示 → 相容端点变换 → 生成函数差分 → 控制 → 条件性 KAM。

这里明确区分三类内容：

1. **原稿保留的研究对象与路线**：Kirchhoff 杆、磁输入、流体和接触；Galerkin 有限维化；Theorem A/B 与旧式（36）；控制和离散 KAM。
2. **文献基础**：Feng–Qin Chapter 15 的自伴性、端点相容性与生成函数定理；Moser 的局部规范化；Shang 的精确辛近可积映射 KAM。
3. **本轮新增推导和计算**：一形式运输构造及可逐阶计算的系数；可保留 B=H 的函数调整；端点变换的直接相容恒等式；构型相关质量、非比例阻尼的非线性合成算例；v10 两模态作为单独的退化检验。

这些是既有几何方法的推导和实例化，不宣称提出了新的普适定理。理论局部成立；一般高维运输方程的低成本求解、完整导管数据、跨接触切换及严格 KAM 阈值并未在本轮全部完成。

## 1. 保留完整物理模型，但先明确数学入口

在一个可使用独立坐标的正则工作域内，设半离散系统已正确写为

$$
H(q,p)=\frac12p^TM(q)^{-1}p+V(q),\qquad M(q)=M(q)^T\succ0,
$$
$$
\dot q=H_p,\qquad \dot p=-H_q+Q_{\rm nc}(q,p,t).
$$

其中 $H_q$ 必须含 $\frac12p^T(\partial_{q_i}M^{-1})p$。把流体、非保守磁力等保留在 $Q_{\rm nc}$ 中，保守作用放入 $V$，避免重复计力。这里不要求 $M$ 恒定，不要求 $C=\gamma M$。

记 $z=(q,p)\in\mathbb R^{2n}$、$\dot z=f(z,t)$。这是把已有力学写成紧凑记号，不是删掉物理项。若原离散方程仍有约束乘子或奇异质量矩阵，需要先在正则约束流形上取独立坐标；本文不把 DAE 自动当成普通 ODE。

统一约定：

$$
J=\begin{pmatrix}0&I_n\\-I_n&0\end{pmatrix},\quad K_0=-J,
\qquad K_{ij}=\partial_iR_j-\partial_jR_i.
$$

因此 $R_0=(p,0)$ 给出 $K_0=-J$，常结构下的 $K_0\dot z=\nabla H$ 等价于 $\dot z=J\nabla H$。$M$ 为 $n\times n$，$K$ 为 $2n\times2n$，端点变换 Jacobian 为 $4n\times4n$。

## 2. 连接一：从一般 f 构造 R、K、B

### 命题 1：局部构造

假设 $f$ 足够光滑并有局部可逆相流。在初始时刻 $t_0$ 选 $R_0=(p,0)$，令列向量 $R(z,t)$ 解线性运输方程

$$
\boxed{\partial_tR+(D_zR)f+(D_zf)^TR=0,\qquad R(z,t_0)=R_0(z).}\tag{1}
$$

定义

$$
K=(D_zR)^T-D_zR,\qquad B=R^Tf.\tag{2}
$$

则在相流及这些函数有定义的局部区域，$K$ 闭合、反对称、非退化，并且

$$
\boxed{Kf=\nabla B+\partial_tR.}\tag{3}
$$

### 逐步证明

首先，

$$
\partial_iB+\partial_tR_i
= (\partial_iR_j)f^j+R_j\partial_i f^j
- f^j\partial_jR_i-R_j\partial_i f^j
=(\partial_iR_j-\partial_jR_i)f^j.
$$

所以式（3）逐分量成立。由于 $K=d(R_i dz^i)$，其反对称性与闭合性自动满足。

为检查非退化性，令 $S=D\Phi_{t,t_0}$。式（1）沿特征线变为

$$
\frac{dR(z(t),t)}{dt}=-(D_zf)^T R,
\qquad R(z(t),t)=S^{-T}R_0(z_0).
$$

因此

$$
K(\Phi_{t,t_0}(z_0),t)=S^{-T}K_0S^{-1}.
$$

局部相流可逆，$S$ 非奇异，故 $K$ 非退化。并有

$$
\partial_tK+(f\cdot\nabla)K+(Df)^TK+KDf=0,
$$
$$
S^TK(\Phi_{t,t_0}(z_0),t)S=K_0.
$$

这给出一般的局部 Birkhoff 表示。初始结构先固定、再由真实向量场运输；不允许计算完离散轨迹以后，为了令结构缺陷为零再任意反推一个 K。

### 2.1 不必已知精确轨迹才能逐阶计算

相流公式用于证明。实际构造可使用式（1）。在解析情形，令 $s=t-t_0$，展开

$$
f(z,t)=\sum_{b\ge0}s^bf_b(z),\quad R(z,t)=\sum_{a\ge0}s^aR_a(z).
$$

比较同次幂得到

$$
\boxed{R_{m+1}=-\frac1{m+1}\sum_{a+b=m}\big[(DR_a)f_b+(Df_b)^TR_a\big].}\tag{4}
$$

这里 $f_b$ 是通常 Taylor 系数（含对应的阶乘）。第一项是

$$
R_1=-(DR_0)f_0-(Df_0)^TR_0.
$$

对 $H=\frac12p^TM(q)^{-1}p+V(q)$，$f=(H_p,-H_q+Q_{\rm nc})$，可算得

$$
(R_1)_q=\nabla V-\frac12\big[p^T(\partial_{q_i}M^{-1})p\big]_i-Q_{\rm nc},
\qquad (R_1)_p=-M^{-1}p.
$$

这说明一般系统所需的 $R$ 通常必须允许 q、p 两组分量同时变化，不能预先始终固定 $R_p=0$、$\partial_pR_q=I$。

式（4）是明确的局部系数构造，但不代表高维计算成本很低。解析情形可在足够小的邻域内使用收敛级数；仅有限阶光滑时应采用有限阶展开及余项估计，不宣称解析级数收敛。

### 2.2 尽量保留原稿 B=H 也可以，但 R 必须同步调整

式（2）的 B 一般不等于物理能量 H。若希望保留原稿的 $B=H$ 记号，可以定义一个标量函数

$$
\sigma(z,t)=\int_{t_0}^{t}[B(z,s)-H(z,s)]\,ds,
$$
$$
\widetilde R=R+\nabla\sigma,\qquad \widetilde B=B-\partial_t\sigma=H.
$$

则

$$
d\widetilde R=dR=K,
\qquad \nabla\widetilde B+\partial_t\widetilde R
=\nabla B+\partial_tR=Kf.
$$

因此 $B=H$ 本身不是禁用的；问题是不能同时强行保留原稿那组不相容的 R 条件。这项调整不改变运动方程，也不意味着耗散系统的 H 守恒。

## 3. 连接二：构造与实际 K 相容的端点变换

### 3.1 坐标变换应满足的恒等式

在局部域内找 $u=\chi_t(z)$，使

$$
\boxed{D\chi_t(z)^TK_0D\chi_t(z)=K(z,t).}\tag{5}
$$

一种可计算的局部构造是 Moser 辅助积分。以物理时间 t 为参数，取

$$
K_{\lambda,t}=K_0+\lambda(K_t-K_0),\qquad 0\le\lambda\le1.
$$

在足够小时间和工作域内保证全部 $K_{\lambda,t}$ 非退化，解

$$
K_{\lambda,t}(z)v_{\lambda,t}(z)=R_t(z)-R_0(z),
$$
$$
\frac{da}{d\lambda}=v_{\lambda,t}(a),\qquad a(0)=z.
$$

设该辅助流的终点映射为 $\rho_t$，取 $\chi_t=\rho_t^{-1}$。由于

$$
\iota_{v_{\lambda,t}}\omega_{\lambda,t}=-(R_t-R_0)_i dz^i,
$$

有 $\frac d{d\lambda}(\rho_{\lambda,t}^*\omega_{\lambda,t})=0$，故式（5）成立。这里的辅助积分不是原动力学精确逆相流；但数值近似它时仍必须评价误差。

### 3.2 对原稿的端点均值思想作相容实现

令

$$
u_+=\chi_{t+h}(z_+),\qquad u_-=\chi_t(z_-),
$$

并定义

$$
\boxed{w=\frac{u_++u_-}{2},\qquad\widehat w=J(u_+-u_-).}\tag{6}
$$

注：上式中的 u 是坐标，不是控制输入。为避免正文与原稿端点字母冲突，可将端点坐标统一记成 $Z_\pm$。

对 $\alpha(z_+,z_-)=(\widehat w,w)$，记 $T_+=D\chi_{t+h}(z_+)$、$T_-=D\chi_t(z_-)$，则

$$
D\alpha=\begin{pmatrix}JT_+&-JT_-\\T_+/2&T_-/2\end{pmatrix}.
$$

直接块矩阵相乘给出

$$
\boxed{D\alpha^TJ_{4n}D\alpha
=\begin{pmatrix}K(z_+,t+h)&0\\0&-K(z_-,t)\end{pmatrix}.}\tag{7}
$$

这里 $J_{4n}=\begin{pmatrix}0&I_{2n}\\-I_{2n}&0\end{pmatrix}$。式（7）明确完成端点相容性，不只检查 alpha 可逆。

在 h=0、两端重合时，$C_\alpha+D_\alpha=D\chi_t$ 非奇异。有限步沿相流还需检查

$$
\det(C_\alpha D\Phi+D_\alpha)\ne0,
$$

它在足够小步长下由连续性保持。这对应原稿 Theorem A 的局部投影条件。

## 4. 生成函数与实际算法

变换后的动力学为

$$
\dot u=g(u,t)=\left[\partial_t\chi_t+D\chi_t f\right]_{z=\chi_t^{-1}(u)}.
$$

式（5）以及 K 的运输方程保证其流保持固定 $K_0$，所以在单连通局部坐标域上 $K_0g$ 为梯度，可构造 $\mathscr H$ 满足

$$
K_0g=\nabla_u\mathscr H,\qquad g=J\nabla_u\mathscr H.
$$

例如选定星形域中心 $u_c$，取

$$
\mathscr H(u,t)=\int_0^1 (u-u_c)^TK_0g(u_c+s(u-u_c),t)\,ds+c(t).
$$

采用中心生成函数 $S_h(w)=h\mathscr H(w,t+h/2)$，则

$$
u_+-u_-=hJ\nabla\mathscr H((u_++u_-)/2,t+h/2),
$$
$$
\boxed{z_+=\chi_{t+h}^{-1}\!\left(\Psi_h^{\mathscr H}(\chi_t(z_-))\right).}\tag{8}
$$

因为式（6）有 $\widehat w=J(u_+-u_-)=-\nabla S_h(w)$，对应原稿梯度形式的标量生成函数是 $\phi_h=-S_h$。此处负号来自已声明的端点 convention，不是新的动力学。

隐式函数 Jacobian $I-\frac h2D_ug$ 非奇异时，映射局部存在。变换坐标中的中点法保持 $K_0$，按链式法则立即得到

$$
\boxed{D\Psi_h^TK(z_+,t+h)D\Psi_h=K(z_-,t).}\tag{9}
$$

对足够光滑的 f、chi 及其逆，在固定时间区间内保持局部可解和一致导数界时，式（8）局部缺陷为 $O(h^3)$、全局误差为 $O(h^2)$。隐式增量方程每步残差 $\eta_h$ 的贡献为 $O(\eta_h/h)$。这些是理想图表和精确求解映射的结论。

更高阶仍可沿原稿 Theorem B 递推构造：Feng–Qin Chapter 15 Theorem 4.5 需要解析性、端点相容性和投影条件。不要由“截断一项”无条件判定具体算法阶数；中点的二阶可独立由 Taylor 展开核实。

### 原（36）的地位

保留原（36）作为原坐标下的普通中点候选、矩阵实施对象和比较基准。一般非线性 chi 下，式（8）通常不等于在原坐标里直接取算术中点的旧（36）。这项差异必须明说。

同一个物理 f、同一组初值和步长可以比较两者；不可因连续系统有 K 表示，就宣称任意直接中点格式保持该 K。

## 5. 计算近似构造时，用残差隔离误差

设近似 $R_a,B_a$ 定义闭且非退化的 $K_a=dR_a$，令

$$
e_B=K_af-\partial_tR_a-\nabla B_a.
$$

若用它们构造算法，严格表示的向量场是

$$
f_a=K_a^{-1}(\nabla B_a+\partial_tR_a)
=f-K_a^{-1}e_B.
$$

于是，在统一工作域内，若 $\|K_a^{-1}\|\le\kappa$、$\|e_B\|\le\epsilon_B$，则

$$
\|f-f_a\|\le\kappa\epsilon_B.
$$

若 f 为 L-Lipschitz，初值相同，则在解均留在域内的固定时间区间

$$
\|z(t)-z_a(t)\|\le \kappa\epsilon_B\frac{e^{L(t-t_0)}-1}{L},
$$

L=0 时取极限 $\kappa\epsilon_B(t-t_0)$。若二阶格式每步还有长度为增量的求解/坐标实施扰动 $\eta_h$，总体可写为

$$
\max_k\|z_k-z(t_k)\|\le C_T h^2+
\kappa\epsilon_B\frac{e^{LT}-1}{L}+C_T\frac{\eta_h}{h}.
$$

固定结构误差不会通过仅减小 h 消失。若要联合二阶收敛，应相应使 $\epsilon_B=O(h^2)$、$\eta_h=O(h^3)$，并保持稳定性常数一致。若 $\chi$ 也只近似满足式（5），几何恒等式另有对应缺陷，不能宣称对原精确 K 精确保结构。

## 6. 控制：分别处理同一 K 与新的闭环 K

设实际控制通道为 $G(z,t)\in\mathbb R^{2n\times m}$、输入 $u\in\mathbb R^m$。

### 6.1 保持原 K 的充分条件

若存在标量 W 使

$$
KGu=\nabla W,
$$

则

$$
K(f+Gu)=\nabla(B+W)+\partial_tR.
$$

只需把 B 更新成 B+W，结构 K 不变，再对新生成函数一致离散。必须检查 $\nabla W\in\operatorname{Im}(KG)$；控制幅值小本身不能替代这个条件。

### 6.2 不满足条件的控制

先写真实闭环 $f_u=f+Gu$，再针对这个闭环构造 $R_u,K_u,B_u$ 和端点变换。理论保持的是 $K_u$，不一定是原来的 K。

这种普遍存在性不等于控制有效，更不能用来使任意控制自动成为“优良控制”。有效性必须相对明确目标，以同对象、同数据和同执行器限制的对照验证。

普通阻尼补偿一般改变旧 K。在本轮非比例阻尼试验中，控制后仍保留非比例阻尼，依然可针对新闭环证明保其 K_u；没有把阻尼一律消成零。

理论收敛证明针对所实际使用的闭环 f_u。64自由度对象若只有两个磁端口，$G$ 的列秩至多2，不能实现任意128维相空间校正。此限制必须保留。

## 7. 新运行的变质量、非比例阻尼算例

这是本轮专门设计的合成检验，不是用户原始实验，也不是完整导管模拟。

令

$$
Q_1=q_1+0.2q_1^3,\qquad Q_2=(1+0.15q_1)q_2,\quad D=D_qQ,\quad P=D^{-T}p.
$$

选

$$
M_0=\begin{pmatrix}1.12&0.12\\0.12&1.32\end{pmatrix},\quad
C_0=\begin{pmatrix}0.18&0.025\\0.025&0.37\end{pmatrix},\quad
K_s=\begin{pmatrix}1.05&0.05\\0.05&2.05\end{pmatrix}.
$$

原坐标下的机械模型为

$$
M(q)=D^TM_0D,\quad C(q)=D^TC_0D,\quad V(q)=\tfrac12Q(q)^TK_sQ(q).
$$

因此 M、C 都随构型改变，且 C 不等于任何标量乘 M；H_q 的几何惯性项完整保留。它通过已知非线性正则图 $\xi(z)=(Q,P)$ 转成 $y'=Ay$，用于建立可靠参考，不作为一般问题已全部求解的证据。

### 7.1 如何构造非精确的数值一步

先以已知线性结构式

$$
K_y(t)=e^{-A^Tt}K_0e^{-At}
$$

定义模型的固定结构（不是根据数值轨迹反推）。在测试区间取实主平方根

$$
T(t)=\big(K_0^{-1}K_y(t)\big)^{1/2}.
$$

因为 $K_0^{-1}K_y$ 是相对 $K_0$ 自伴的，主平方根在当前连续分支上也相对自伴，有 $T^TK_0T=K_y$。导数由 Sylvester 方程

$$
T\dot T+\dot T T=K_0^{-1}\dot K_y
$$

求得。取 $\chi_t=T(t)\xi$。变换后线性场

$$
L(t)=\dot T T^{-1}+TAT^{-1}
$$

满足 $L^TK_0+K_0L=0$。

数值映射为

$$
y_+=T(t+h)^{-1}
\left(I-\tfrac h2L(t+h/2)\right)^{-1}
\left(I+\tfrac h2L(t+h/2)\right)T(t)y_-.
$$

再用 $\xi^{-1}$ 返回 z。这不是直接用 $e^{Ah}$ 更新状态，误差非零并表现为二阶。它利用了本算例可显式计算的 K；并不意味着一般模型的 K 已有同样便宜的算法。

初值 $z_0=(0.25,-0.18,0.03,0.04)$，终止时间2。误差为终点欧氏范数；结构缺陷为每步矩阵谱2范数的最大值。精确线性共轭参考与独立原坐标 DOP853 在终点相差约 $9.53\times10^{-15}$。

详细数值见同包 verification_results.json。

### 7.2 控制试验

设目标仍有非比例阻尼

$$
C_d=\begin{pmatrix}.09&.009\\.009&.14\end{pmatrix},\quad
K_p=\operatorname{diag}(.05,.10),
$$

目标刚度为 $K_s+K_p$。使用理想广义控制

$$
u_q=D^T\big[(C_0-C_d)M_0^{-1}P-K_pQ\big].
$$

代回后，系统恰对应这个指定目标，仍含阻尼。分别为无控制和受控方程构造各自 K。共同步长0.025、时间2、初值相同，参考始终是受控目标的精确轨迹。

这是理想全驱动合成试验；没有加入学习、噪声、饱和或磁执行器。它验证的是“控制不必完全消除阻尼，也能对实际闭环建立并验证相应 Birkhoff 保结构格式”。

## 8. v10 作为验证实例，而非一般理论的假设

采用 v10 展示精度参数

$$
\mathsf N=\operatorname{diag}(1,6.152117504),\quad
d=(0.225670773,0.321798806)^T,
$$
$$
\gamma=0.55558524/11.417287283,
$$

与完整余弦势 $V_0=\frac12X^T\mathsf NX+g(d^TX)$。它在已知二次动能、比例阻尼分支中具有显式结构 $K(t)=e^{\gamma t}K_0$，可取图 $(X,e^{\gamma t}Y)$。一般公式于是退化为既有加权中点式。

本轮新跑初值 $(.18,.16,.03,-.02)$、无量纲终止时间5、步长 .04,.02,.01,.005。结果见 v10_results.json。这里只是检验一般公式在简单特例上是否退化正确，不重做原学习试验，也不认证 v10 的 KAM 数值结论。

## 9. KAM 与非光滑区域的边界

局部时变 Birkhoff 表示存在，不推出不变环面存在。把任意系统用逆相流化为零向量场，也不能凭此宣布原坐标中的长期 KAM 稳定性。

Shang 的结论应作用于可明确验证的解析精确辛映射，以及它的非退化可积/近可积基准、全整数非共振和小扰动条件。控制后可能满足，也可能不满足。非自治坐标变换后得到的任意时间依赖辛更新序列，不自动成为该定理的固定近可积映射。

物理模型的流体与接触项不删掉，但平滑域、接触切换和冲击应分开。Hertz 启动或速度绝对值可能降低光滑阶数；不允许为应用解析定理悄悄正则化后声称仍是完全相同模型。对于实际跳跃/事件线性化 S，应另查 $S^TK^+S=K^-$；若 S 降秩，非退化两形式的精确保结构不可能由这个事件映射保持。

本轮的非比例阻尼合成测试本身没有非平凡保守 KAM 声明。v10 的 KAM 分支仍需单独满足相关条件；无论结构误差多小，数值结果不替代定理阈值。

## 10. 放回原稿的最小改动位置

- 原（12）后、具体 F_i/B 选择处：插入式（1）—（4）的局部构造和逐项代回。
- Theorem A 前、原（30）附近：插入式（5）—（7）的端点相容性；保留 Theorem A/B 顺序。
- 原（36）附近：保留原坐标中点作为候选和对照，列出式（8）的相容实现，不称两者一般等价。
- 原 U_k 位置：明确同 K 兼容控制和重新构造闭环 K 两种结论，以及输入秩限制。
- 原 KAM 位置：保留条件性分支，不把局部表示的普遍性当作 KAM 普遍性。
- v10 前文作为模型例子/验证节，可供详细演示；一般推导仍对完整半离散 f 展开。

## 参考依据

[S1] 用户原始《推理草稿5月1025(2)》：一般力学、Birkhoff、Theorem A/B、原（30）—（36）的研究顺序。

[S2] Feng, K.; Qin, M. (2010), *Symplectic Geometric Algorithms for Hamiltonian Systems*, Chapter 15, §§15.2–15.4, Theorems 2.2, 3.5, 4.1, 4.4, 4.5。用户附件。

[S3] Su, H.; Qin, M., *Symplectic Schemes for Birkhoffian system*, arXiv:math-ph/0301001。预印本与书的定理编号不同，引用时不要混用。
https://arxiv.org/abs/math-ph/0301001

[S4] Guo, Y.-X.; Liu, C.; Liu, S.-X. (2010), *Generalized Birkhoffian realization of nonholonomic systems*, Communications in Mathematics 18, 21–35。提供局部解析普遍性背景；不能从其标题直接推出任意非光滑全局结论。
https://dml.cz/handle/10338.dmlcz/141670

[S5] Cannas da Silva, A., *Symplectic Geometry*, §§1.4–1.5，Moser 局部规范化。
https://arxiv.org/abs/math/0505366

[S6] Kong, X.-L.; Wu, H.-B.; Mei, F.-X. (2016), *Birkhoffian symplectic algorithms derived from Hamiltonian symplectic algorithms*, Chin. Phys. B 25, 010203，DOI:10.1088/1674-1056/25/1/010203。

[S7] Shang, Z.-J. (1999), *KAM theorem of symplectic algorithms for Hamiltonian systems*, Numerische Mathematik 83, 477–496, Theorems 1–2 and §4。用户附件。

[S8] 用户 v10 主文 main.pdf，式（1）—（19）：本轮特例的模型和展示精度参数来源。

## 未完成与不可夸大的部分

一般局部推导成立不等于已经为原完整 Kirchhoff—流体—接触模型计算出便宜的 R、K、chi。当前实际运行的是已知结构的变质量非比例阻尼合成模型和 v10 两模态特例。新算法相对普通中点的优点在本轮是保持指定结构，不是已证明更低轨迹误差、更快速度或更好控制鲁棒性。源文件、原稿和此前 PDF 均未改动。
