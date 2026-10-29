# 真实三维 ROM 的 Birkhoff 连接与积分/控制条件

本文件对应 `program/rom_bridge.py`、`birkhoff_rom.py`、`rom_integrators.py` 的数学对象。公式是可核对的推导；是否运行、误差值与运行时以相应 `results/` 记录为准。本文件不把尚未生成的实验值写成结果。

## 1. 真实几何模型、单位和完整惯性

复用的 `RodROM(per_axis=4,elements=20)` 有两轴弯曲和一轴扭转各四个应变 Ritz 系数；SO(3) 更新、杆中心线及其位置/角速度 Jacobian 均由既有源码求得。其 12×12 质量矩阵记为 \(M_r(q_r)\)，同时包含平动与转动惯性。这里 \(q_r\) 是应变 Ritz 广义坐标，不是 12 个空间位移；位形系数按原代码约定经曲率基函数映射到 SI 几何。当前 ROM 是不可伸长/不可剪切的 Kirchhoff 分支，不能借它删除完整 Cosserat 模型的伸长、剪切、血流和接触。

原码的固定线性正则缩放是

\[
q_r=S_qQ,\quad p_r=S_pP,\quad
S_q^TS_p=(E_0/\omega_0)I,\quad \tau=\omega_0t_{\rm s}.
\]

令 \(z=(Q,P)\)、\(J=\begin{psmallmatrix}0&I\\-I&0\end{psmallmatrix}\)、\(K_0=-J\)，则

\[
\bar M(Q)=\frac{\omega_0^2}{E_0}S_q^TM_r(S_qQ)S_q,\qquad
H(Q,P;u)=\tfrac12P^T\bar M(Q)^{-1}P+\frac{V(S_qQ;u)-V_0}{E_0}.
\]

所有数值积分时间和相坐标误差均在 \((\tau,Q,P)\) 中定义；物理时间为 \(t_{\rm s}=\tau/\omega_0\)，能量为 \(E_0H+V_0\)。同一数值表必须使用同一缩放，不能把无量纲相空间范数叫作米。

记 \(v=H_P=\bar M^{-1}P\)。完整方程为

\[
Q'=v,\qquad
P'_i=\tfrac12v^T(\partial_{Q_i}\bar M)v-\partial_{Q_i}\bar V+F_i.
\]

`rom_bridge.py` 对包含 `solve(M(Q),P)` 的完整 Hamiltonian 自动微分，因此保留上述几何惯性项。\(M_0\) 仅参与固定坐标缩放，不代替每次求值的 \(M(Q)\)。`rom_integrators.py` 的 chord 矩阵仅作为非线性求解预条件器；终止条件始终检查真实非线性残差，不能把预条件矩阵当作物理模型。

## 2. 原（36）在这一模型上的合法含义

修正的通用（36）是完整隐式中点：

\[
z_+-z_-=h f\bigl((z_++z_-)/2,\tau+h/2\bigr).
\]

\(f\) 中包含上一节全部惯性项及实际输入。原稿的常矩阵消元只能在相应假设下化成

\[
E=\tfrac{h^2}{4}K_sM^{-1}+\tfrac h2CM^{-1},\quad
P_+=(I+E)^{-1}\{(I-E)P_- -hK_sQ_-+hF\}.
\]

一般矩阵不可交换；变系数仍在未知中点评价。本轮实现直接解 24 维残差。自治保守分支中该格式保持正则二形式，光滑条件下为二阶；加入一般阻尼后不应继续称它正则辛，也不自动保持任意指定的时间 Birkhoff 二形式。

## 3. 不借未知精确流的一阶输运构造

选取一个明确、可导的非比例测试载荷

\[
f=(H_P,-H_Q-\Gamma P),\quad
\Gamma=\operatorname{diag}(\gamma_i),\quad a_0=(P,0).
\]

\(\Gamma\) 是声明的无量纲常对角动量阻尼矩阵，不是已经辨识的血流/接触投影。保守 Hamiltonian 仍为真实变质量三维 ROM。令 \(T=\tfrac12P^T\bar M^{-1}P\)、\(V=H(Q,0)\)、\(F=V-T\)。对固定时间原点 \(\tau_0=0\)，一形式输运的一阶系数为

\[
a_1=-Da_0 f-(Df)^Ta_0=\nabla F+(\Gamma P,0),\qquad a_a=a_0+\tau a_1.
\]

关键恒等式使用 \(P\cdot H_P=2T\)，不要求 \(M\) 常数。空间外微分消去精确梯度 \(\nabla F\)，故

\[
K_a=(Da_a)^T-Da_a=
\begin{pmatrix}0&-W(\tau)\\W(\tau)&0\end{pmatrix},\quad W=I+\tau\Gamma.
\]

因此此特定族的闭性是精确的：\(K_a\) 没有空间依赖。非退化需每个 \(1+\tau\gamma_i\ne0\)；程序选取正分支。这里闭性和采样条件数都不能推广成任意非线性流体阻力的结论。

定义 \(B_a=a_a^Tf\)。输运截断的原场表示残差为

\[
e_B=K_af-\partial_\tau a_a-\nabla B_a
=-\tau\{Da_1f+(Df)^Ta_1\}.
\]

通常 \(e_B=O(\tau)\)，并不为零。由构造精确表示的场是

\[
f_a=K_a^{-1}(\nabla B_a+\partial_\tau a_a)
=f-K_a^{-1}e_B,
\qquad \|f_a-f\|\le\|K_a^{-1}\|\,\|e_B\|.
\]

这是核心误差分离：可以准确保持 \(K_a\)，同时错误地逼近原来的 \(f\)。固定一阶截断和固定终时下，令时间步长趋于零也不会自动消除 \(f_a-f\)。不能每步重置 \(a_0\) 而仍声称保持同一全局 \(K\)；当前构造使用同一固定时间原点。

### 可计算的图和规范变换

无需物理精确流即可计算

\[
\chi_\tau(Q,P)=(Q,W(\tau)P),\qquad
D\chi_\tau^TK_0D\chi_\tau=K_a.
\]

这是真实 ROM 上由特殊阻尼族导出的显式图，不是拟合得到的已知线性共轭，也不使用未知真流。它的便宜计算依赖 \(\Gamma\) 常对角和一阶输运，并未解决任意状态相关阻力的通用图构造。

为避免把精确梯度写进一形式，可作 \(\sigma=-\tau F\) 的规范变换：

\[
a'_a=a_a+\nabla\sigma=(WP,0),\qquad
B'_a=B_a-\partial_\tau\sigma=B_a+F
=H+2\tau(V_Q+\Gamma P)^TH_P.
\]

\(K_a\) 和表示残差不变。程序 `gauge_hamiltonian` 正是这个 \(B'_a\)，并保留其中全部变质量导数。于是

\[
Q'_a=W^{-1}B'_{a,P},\qquad
P'_a=-W^{-1}(B'_{a,Q}+\Gamma P).
\]

在 \(y=(Q,\Pi)=\chi_\tau(z)\) 中，Hamiltonian 为
\(\mathcal H_a(y,\tau)=B'_a(Q,W^{-1}\Pi,\tau)\)，有
\(Q'=W^{-1}B'_{a,P},\ \Pi'=-B'_{a,Q}\)。在这个时间依赖正则图中用合法辛方法，才得到对近似场 \(f_a\) 的结构保持推进。图场必须包含 \(\partial_\tau\chi\)；遗漏它会改变目标场。

原场输运相容性应独立测量
\(\partial_\tau K_a+(Df)^TK_a+K_aDf+f\cdot\nabla K_a\)。这里最后项为零，前面各项一般留下 \(O(\tau)\) 的缺陷；该缺陷不能因图匹配精确而忽略。

## 4. 两个精确适用分支

**统一动量阻尼。** 若实际选定场为 \(P'=-H_Q-\gamma P\)，则
\(K(\tau)=e^{\gamma\tau}K_0\)、\(\Pi=e^{\gamma\tau}P\) 给出精确时间 Birkhoff 结构。对完整 \(M(Q)\)，规范 Hamiltonian 为

\[
\mathcal H_c(Q,\Pi,\tau)=e^{\gamma\tau}H(Q,e^{-\gamma\tau}\Pi).
\]

以时间中点为中心变换，正则中点等价于
\(S_{h/2}\circ\operatorname{MP}_H\circ S_{h/2}\)，其中
\(S_{h/2}(Q,P)=(Q,e^{-\gamma h/2}P)\)。该二阶加权方法的理想切线满足
\(D\Phi^TK_0D\Phi=e^{-\gamma h}K_0\)。这仍保留 \(H_Q\) 中动能几何导数。它不能用于宣称一般血流、接触或非比例反馈具有同一个指数结构。

**自治保守 Central4。** 对 \(f=J\nabla H\)，定义

\[
S_h=hH+\tfrac{h^3}{24}f^TH''f,\qquad
z_+-z_-=J\nabla S_h((z_++z_-)/2).
\]

恒等式
\(J\nabla(f^TH''f)=D^2f[f,f]-2(Df)^2f\)
给四阶中心增量。`central_scalar` 对非可分真实 \(H\) 自动微分，不丢掉动量和位形的混合导数。正号对应前向中心生成修正；不是普通中点后向误差 Hamiltonian 的负号。代码禁止在该自治保守公式上附加 \(\gamma\ne0\) 而继续称 Central4。

理论上的理想隐式切线为
\(D\Phi=(I-C)^{-1}(I+C)\)，\(C=\tfrac12J S_h''\)。它保持 \(K_0\)。有限容差 chord 迭代的实际程序导数不与此自动相同；结果中必须分别注明理想切线和非线性残差。

## 5. 真磁接口与控制后的结构

输入 \(u\) 为轴向偏置场之上的 SI 增量，顺序是
\((B_x,B_y,B_z,G_{xx},G_{yy},G_{xy},G_{xz},G_{yz})\)。对称无迹 \(G\) 满足局部源外 Maxwell 条件。设固定输入的磁能增量为 \(-\Phi(q_r)^Tu\)，则

\[
Q_{m,r}(q_r,u)=(D_{q_r}\Phi)^Tu,\qquad
G_m(Q)=E_0^{-1}S_q^T(D_{q_r}\Phi)^T,\quad P'_m=G_m(Q)u.
\]

`ROMBridge.magnetic_map` 返回后一个 12×8 矩阵。因此其秩至多为 8，在对称形态还可能降低；一般 12 维残差不可能任意补偿。线圈映射 \(u=A i\) 还会进一步限制可达性，并需处理电流、速率、场和梯度边界。

磁力是对固定输入的偏导。若 \(u=\kappa(z)\)，真实闭环是 \(G_m(Q)\kappa(z)\)，不是先把 \(\kappa\) 代入磁势再对总函数求导；后一操作会多出 \(D\kappa\) 项。对求解器切线则相反：必须包括真实反馈链式导数。所谓“冻结输入子步辛”不能代表反馈闭环辛。

设原二形式为闭的 \(\Omega_\tau\)，原场 \(f\) 已满足 \(\partial_\tau\Omega+\mathcal L_f\Omega=0\)。加入真实控制场 \(g\) 后，继续保持原结构的条件是

\[
\mathcal L_g\Omega=d(\iota_g\Omega)=0.
\]

在局部单连通域，这等价于收缩一形式为精确形式（符号取决于 \(K\) 约定）；可写为 \(K g=\nabla W\)。矩阵条件是
\((Dg)^TK+KDg+g\cdot\nabla K=0\)。对于固定正则 \(K_0\)、纯动量力 \(g=(0,Q_c(Q))\)，要求 \(D_QQ_c\) 对称。若力依赖动量，一般不满足该条件。

- 固定磁输入产生真实磁势，保守分支有明确 Hamiltonian。
- 精确可达的势能整形可保原正则形式；分配残差不为零时必须按实际力重新判断。
- 阻尼补偿若受限后不能完全实现，不会变成精确保守系统。
- 共点阻尼反馈可证明 \(v^TQ_c\le0\) 的功率性质，但这不是辛性。
- 学习残差必须经过实际 \(G_m\) 分配，不能直接作为相空间跳变；需要区分学习误差和不可达误差。

一般情形应重新构造闭环 \(K_u\)，或诚实采用耗散/端口结论。功率为
\(dH/d\tau=H_P^TQ_c+\partial_\tau H\)，再加入声明的阻力功项；SI 功率为 \(E_0\omega_0\) 倍此无量纲功率。非二次 \(H\) 的能量差减中点功率积分会包含求积误差，不是自动精确平衡。

## 6. Theorem A/B、局部解与有限时间误差

一般 Birkhoff 生成定理需先有足够光滑的闭、非退化二形式和动力学相容性；端点变换 \(\alpha\) 需满足两个端点二形式与标准形式的拉回匹配。还需横截投影 \(C_\alpha D\Phi+D_\alpha\) 可逆，才能用局部隐函数表示生成梯度；不能要求初始为零的生成梯度 Jacobian 本身可逆。标量生成函数有加时间函数的规范自由度。Theorem B 的解析幂级数递推还要求解析性和正确固定生成坐标求导；截断项必须保持梯度性质。上述前提未经验证时，不能仅凭低数值结构误差援引定理。

对中点，若共同轨道邻域内 \(\|Df\|\le L\) 且 \(hL/2<1\)，可由压缩映射得到局部唯一更新。更一般可用 \(I-hDf/2\) 可逆的隐函数条件，但单点最小奇异值不等于已证明全域唯一性。图方法还需图及逆图有统一导数界、辅助形式不退化、迭代轨迹不离开该域。

在这些共同域/稳定性条件下，若时间方法阶数为 \(p\)、每步状态残差不超过 \(\eta_h\)、表示误差有统一界 \(\epsilon_f\)，则

\[
\max_{kh\le T}\|z_k-z(kh)\|
\le C_T\left(\|e_0\|+h^p+\frac{\eta_h}{h}\right)
+\epsilon_f\frac{e^{LT}-1}{L}.
\]

对 Birkhoff 近似可取 \(\epsilon_f\le\kappa\epsilon_B\)，其中需有域上界 \(\|K_a^{-1}\|\le\kappa\)、\(\|e_B\|\le\epsilon_B\)。若另有每步图实施状态误差 \(\eta_\chi\)，同样累计为 \(O(\eta_\chi/h)\)；图条件数控制其放大。样本范数不能被直接冒充这些统一常数。保持二阶需有关每步误差至少 \(O(h^3)\)，四阶需 \(O(h^5)\)；固定模型截断误差形成独立误差项。

若数值图满足 \(D\widetilde\chi_t^TK_0D\widetilde\chi_t=K_t+E_t\)，内部理想映射保 \(K_0\)，则其外部图误差的结构缺陷为

\[
D\widetilde\Psi^TK_+D\widetilde\Psi-K_-
=E_- -D\widetilde\Psi^TE_+D\widetilde\Psi,
\]

再叠加内部求解和切线估计误差。这个结构预算与上面的原动力学误差预算是不同命题。

## 7. KAM 和后续物理验证仍缺的条件

本轮没有新三维连续或离散 KAM 证书。圆截面/轴向偏置的实际 ROM 有成对弯曲频率，旧非共振两模态证书不可直接使用；需研究三维共振正规形、适当对称性约化及扭转/非退化条件。

连续 KAM 还需要指定实解析 Hamiltonian 的复延拓域、近可积或正规形分解、解析范数、小量和全整数非共振条件。完整复值 CHNN 的有限训练误差不是这些高阶统一范数界。动量 Hessian 的样本正定也不等于全域 Legendre 可逆。

离散 KAM 还需适用的固定或周期 exact-symplectic 映射、相应解析域、非退化和步长相关离散非共振条件。时间变化的局部 Birkhoff 图序列、耗散分配闭环和跨接触/摩擦事件没有因此自动满足所选定理。相图、FFT、低残差、能量下降只能作为不同层次诊断。

后续需把选定实际磁控制律施加到 32/64 段 Cosserat，量化末端三维误差、血流、接触力/穿透、磁限制、功率和时间/空间细化。现有规定脉动流和刚性管腔只是已经实施的中间层；双向 FSI、柔性壁、实际微重力生理输入、完整 CHNN 公平训练与新 KAM 条件均另列未完成，不能由当前局部 ROM 桥接代替。
