# 第一个衔接：同一正则对象上的 CHNN 与 Birkhoff

本文件只补《1025》从学习能量到实际向量场再到 Birkhoff 表示所需的接口。原稿正确的 Hamiltonian 是 Birkhoff 特例的内容（p0793–0820/m0344–0357）直接保留；一般局部输运证明继承已有材料，不把 CHNN 训练成功当作该存在定理的前提。原意及逐式判定见 `original_intention.md`，最少原文改动见 `minimal_revision.md`。

证据分层：下面的恒等式有直接推导；一般局部存在结论有明确正则性/留域假设；实测参数、样本、残差及负 Hessian 证据在 `results/`。有限采样不提供未证明的统一误差界。

## 1. 共同相空间、物理模型和冻结学习目标

沿用 S5 `proofs/chnn_kam_restored.md:5–27`，物理变量满足

\[
q=S_qQ,\quad p=S_pP,\quad S_q^TS_p=(E_0/\omega_0)I,
\quad \tau=\omega_0t,\quad z=(Q,P)\in\mathbb R^{24}.
\tag{B1}
\]

物理作用量除以 \(E_0/\omega_0\) 后，一形式是 \(P^TdQ\)，
\(J=\begin{pmatrix}0&I\\-I&0\end{pmatrix}\)、\(K_0=-J\)。这里的 Q/P 是同一三维 Kirchhoff 几何 ROM 的正则坐标，不是训练输入，也不是另建平面模型。

真实参考选为冻结网络实际训练的理想轴向偏置分支：

\[
h_*(z)=H_{\rm ideal}(S_qQ,S_pP)/E_0
 =\tfrac12 P^T\mathsf M(Q)^{-1}P+v_{\rm ideal}(Q),
\quad
\mathsf M(Q)=\frac{\omega_0^2}{E_0}S_q^TM(S_qQ)S_q.
\tag{B2}
\]

能量零点按 `RodROM.hamiltonian` 中原点势 \(V_0\) 平移。变质量及其全部几何惯性保留。定义真实机械正则域
\(U_M=\{z:\mathsf M(Q)\succ0\}\)；不能未经验证把质量坐标奇异处纳入此域。对象是20几何单元、12配置自由度的现有 ROM，不冒充全空间 Cosserat 或患者真值。

S5-L01 冻结完整复隐藏网络学的是这个实能量相对于二次先验的残差：

\[
x=Dz,\quad D=\operatorname{diag}(\sqrt\nu,\sqrt\nu)/a,
\quad a=0.08,
\qquad
\widehat h_\theta(z)=\tfrac12a^2|Dz|^2+\mathcal N_\theta(Dz).
\tag{B3}
\]

这是对完整保守 Hamiltonian 的残差参数化，不是只学磁势单系数，也不是拟合任意非保守场。调用既有 `ComplexResidual` 全部复隐藏层/复读出、共轭输入、动量偶对称与三阶门控，不重新训练。输出通过实部读出，故 \(\widehat h_\theta\) 在实相空间实值。split real/imag tanh 使它是实解析函数，不是关于 \(\xi\) 单独的全纯函数；本桥的实局部存在不要求额外复域认证。

链式法则必须进入解码器：

\[
\nabla_z\widehat h_\theta=D^T\nabla_x\widehat h_\theta,
\quad z'=J D^T\nabla_x\widehat h_\theta,
\quad x'=D J D^T\nabla_x\widehat h_\theta.
\tag{B4}
\]

本例D实对角，Dᵀ=D；D一般不是辛矩阵，故不能用 \(x'=J\nabla_xh\) 代替B4。该修正已在S5训练损失和S6参考解码中落实，本轮验证而非重写。

本轮第一组为保守场R=0；第二组复用 S5 `NativeTransport.force_tensor` 的既有状态相关光滑测试载荷，所有参数不变：

\[
R_j(z)=-d_j[1+0.15\tanh(Q_j/0.02)]
 [P_j+0.1P_j^3/0.002^2]-0.04c_j(c^TP),
\tag{B5}
\]

其中 \(d_j\) 为原代码0.1到0.3的12点等分，\(c\) 为原余弦向量的单位化。它是已声明的合成光滑非保守载荷，不是血流、接触或标定的物理Rayleigh耗散；正系数本身不保证任意非可分能量的功率非正（S5输运证明:149）。本轮独立重算已有test180，真实理想能量功率为−1.10205e−4，网络能量功率为+1.20601e−4，见 `results/network_power_witness.json`；此反例保留同一个R，未为获得耗散结果更换载荷。

据此实际要比较的是

\[
f_*=J\nabla h_*+(0,R),\qquad
f_\theta=J\nabla\widehat h_\theta+(0,R),
\quad \delta f=f_\theta-f_*.
\tag{B6}
\]

“同R”是同一个定义于z的函数。如果使用同一物理Rayleigh函数 \(\mathcal D(Q,v)\)，却分别代入 \(v_*=h_{*,P}\)、\(v_\theta=\widehat h_{\theta,P}\)，一般产生不同的 \(R_*\)、\(R_\theta\)。此时必须写

\[
\delta f=J\nabla(\widehat h_\theta-h_*)+(0,\delta R),
\qquad \delta R=R_\theta-R_*.
\tag{B7}
\]

例如同一 \(C(Q)\) 的线性速度阻尼给 \(\delta R=-C(Q)\partial_P(\widehat h_\theta-h_*)\)。不能把这个误差隐藏在“相同耗散模型”的文字中。本轮B5直接共享R，故B6在所选实验中真实成立。

## 2. 复导数、功率与 Legendre 的三个不同责任

用真正正则变量定义 \(\xi=(Q+iP)/\sqrt2\)，则

\[
\partial_{\bar\xi}=(\partial_Q+i\partial_P)/\sqrt2,
\qquad \xi'=-i\widehat h_{\theta,\bar\xi}+iR/\sqrt2.
\tag{B8}
\]

实虚部分别恢复B6；原(17)与(18)的根号2/2不一致必须成组改正。复权重不改变实输出/实相空间这一约定。对任意所选实能量h，

\[
\frac{dh}{d\tau}=h_\tau+h_P^TR
\tag{B9}
\]

来自 \(\nabla h^TJ\nabla h=0\)。这是真正应由能量损失与解码器共同满足的式子；有R时不得强制机械能恒定。Birkhoff规范变换不会改变B9。这里的R若不是物理耗散，B9仍成立而符号未必非正。

\(\widehat h_{PP}\succ0\) 是机械解释与可逆速度—动量关系的责任，**不是**下面相空间 Birkhoff 的必要条件。若在一点 \(\det\widehat h_{PP}\ne0\)，逆函数定理给该点附近局部Legendre反解；若要正质量和给定域唯一反解，需要正定性、适当动量纤维及统一域条件。负Hessian样本否定全训练盒正定宣称，但不否定 \(J\nabla\widehat h\) 是合法Hamiltonian场。

三阶门控和二次先验给 \(\widehat h_{PP}(0)=\operatorname{diag}\nu\succ0\)，所以由连续性存在某个正定邻域。未给有向舍入或统一导数界时，不能把数个正定样本扩大成已认证的整个盒。S6对**机械多项式**的有理正定域也不能赋予本轮的完整复隐藏网络。现有负结果必须保留。

## 3. 保守分支直接使用精确正则表示

若R=0，任一 \(C^2\) 实Hamiltonianh都有

\[
a_0=(P,0),\quad K_0=(Da_0)^T-Da_0=-J,
\quad B=h,\qquad K_0J\nabla h=\nabla h.
\tag{B10}
\]

因此令h为 \(h_*\) 或 \(\widehat h_\theta\) 都是精确Birkhoff表示。K0闭、全相空间非退化、条件数1；Hamiltonian Hessian对称给
\((Df)^TK_0+K_0Df=0\)。B10对学得场的表示误差为零，与学习准确率、动量Hessian正定性及网络宽度无关。参考h*限于其正则域；网络实能量的该代数表示对所有有限实输入成立，解的存在时间仍另受常微分方程条件约束。

不能用低阶齐次输运截断取代B10，然后把人为引入的表示残差说成物理建模或学习不可避免的误差。

## 4. 光滑非保守场的一般局部表示及最小实现适配

在开域U内，假设所选 \(f_\theta\) 足够光滑并存在留在U内的局部可逆流 \(\Phi^\theta_{\tau,0}\)。已有一般Birkhoff材料的构造为

\[
\partial_\tau a_\theta+(Da_\theta)f_\theta
 +(Df_\theta)^Ta_\theta=0,\quad a_\theta(0)=a_0,
\quad B_\theta=a_\theta^Tf_\theta.
\tag{B11}
\]

利用 \(\nabla(a^Tf)=(Da)^Tf+(Df)^Ta\)，逐项得到
\(K_\theta f_\theta=\nabla B_\theta+\partial_\tau a_\theta\)。闭性来自 \(d^2(a^Tdz)=0\)。令 \(S=D\Phi^\theta_{\tau,0}\)，则

\[
K_\theta(\Phi^\theta z,\tau)=S^{-T}K_0S^{-1},
\quad K_{\theta,\tau}+DK_\theta[f_\theta]
 +(Df_\theta)^TK_\theta+K_\theta Df_\theta=0.
\tag{B12}
\]

因此非退化性保留于流可逆的局部区域。这里相流用于已有存在证明，不是新程序的免费输入。没有“先学准才能存在a”的假设；对f*也可独立作同样构造。

已有S5算法采用方便保守回归的有源规范。对**一般**实h，而不只动量二次机械h，令

\[
\ell=P^Th_P-h,\qquad \mathcal L_fa_0=\nabla\ell+(R,0).
\tag{B13}
\]

证明：\(Da_0f=(-h_Q+R,0)\)，而 \((Df)^Ta_0=(D h_P)^TP\)；两项和正是B13。故

\[
a'=a_0+b,\quad b_\tau+\mathcal L_fb=-(R,0),\quad b(0)=0,
\qquad B'=h+b^Tf
\tag{B14}
\]

给 \(a'_\tau+\mathcal L_fa'=\nabla\ell\)，以及所需Birkhoff恒等式。它是有源规范，不能称a'本身满足齐次B11。局部标量 \(\sigma_\tau+f\cdot\nabla\sigma=\ell\) 把 \(a=a'-\nabla\sigma\)、\(B=B'+\sigma_\tau\) 变回B11；程序不需要未知精确σ。

本轮复用既有自治递推（时间幂系数已含阶乘）：

\[
b_1=-(R,0),\quad b_{k+1}=-\mathcal L_f b_k/(k+1).
\tag{B15}
\]

需要的最小代码修正并非新算法，而是避免把机械专用恒等式用到任意完整网络：

\[
a_1=-\mathcal L_fa_0=\nabla(h-P^Th_P)-(R,0).
\tag{B16}
\]

S5 `NativeTransport.a1` 的 \(\nabla[2h(Q,0)-h]-(R,0)\) 已明确限定 \(h=T+V\)、T对P二次，在原物理ROM上正确；一般网络不受此限制，所以该shortcut不可直接套用。同理 `high_order_hamiltonian` 用 \(\tfrac12P^TM^{-1}P+h(Q,0)\) 重建能量只是机械分支代数等价，学得能量必须直接调用冻结网络。共享R可以共享b1，b2及更高项依赖各自f，不能把真实ROM缓存当作学得场缓存。本轮 `program/bridge_interface.py` 的 `LearnedIdealBase` 和 `GeneralHamiltonianTransport` 直接复用旧网络解码/递推，只适配上述对象限制。

实际运行还暴露PyTorch2.5.1默认批量 `jacrev/vmap` 对复共轭张量的 `aten::_neg_view` 不支持。保留失败后，最小后端适配使用 `jacrev(chunk_size=1)` 逐行反向求导；没有改网络、数学递推或物理模型。新的采样器仍构造既有 `OneFormCache`，这是程序后端修复，与B16的数学条件修正分开记录。

独立最小反例：\(h=(Q^2+P^2)/2+\epsilon P^4\)、R=0。B16给 \(a_1=(Q,-P-12\epsilon P^3)\)，机械shortcut给 \((Q,-P-4\epsilon P^3)\)，差为 \((0,8\epsilon P^3)\)。但保守B10仍精确。该反例定位的是接口假设，不是宣称S5机械算法原先错误。

## 5. 有限时间/空间近似及三个分离误差

对实际计算的 \(\widetilde b\)（可为既有时间截断和空间缓存），定义

\[
\widetilde a=a_0+\widetilde b,\quad
\widetilde B=\widehat h_\theta+\widetilde b^Tf_\theta,
\quad \widetilde K=K_0+(D\widetilde b)^T-D\widetilde b.
\tag{B17}
\]

**A 学习场误差**：B6的 \(\delta f\)。共享R时，由J正交性，
\(\|\delta f\|_2=\|\nabla(\widehat h_\theta-h_*)\|_2\)。不同载荷时使用B7。

**B 对学得场的表示误差**：

\[
e_B=\widetilde Kf_\theta-\nabla\widetilde B-\widetilde a_\tau
=-[\widetilde b_\tau+D\widetilde b f_\theta
 +(Df_\theta)^T\widetilde b+(R,0)].
\tag{B18}
\]

若是原生r阶自治时间系数而无空间近似，则 \(e_B=-\tau^r\mathcal L_{f_\theta}b_r\)。空间缓存有额外残差，需另测，不能仅根据r自动声明大小。

**C 同一构造用于真实场的残差**：仅作加减同一项即得

\[
\boxed{\widetilde Kf_* -\nabla\widetilde B-\widetilde a_\tau
=e_B+\widetilde K(f_*-f_\theta)=e_B-\widetilde K\delta f.}
\tag{B19}
\]

用户给出的加号形式正确；若采用 \(\delta f=f_\theta-f_*\)，右侧必须是减 \(K\delta f\)。此等式对任意有限近似a/B成立，不依赖学习误差很小。

在 \(\widetilde K\) 非退化处，所算a/B真正表示的场为

\[
g_\theta=\widetilde K^{-1}(\nabla\widetilde B+\widetilde a_\tau)
=f_\theta-\widetilde K^{-1}e_B,
\quad g_\theta-f_* =\delta f-\widetilde K^{-1}e_B.
\tag{B20}
\]

因此在共同留域且 \(\|K\|\le\kappa_+\)、\(\|K^{-1}\|\le\kappa_-\)、
\(\|e_B\|\le\epsilon_B\)、\(\|\nabla\delta h\|\le\epsilon_H\)、\(\|\delta R\|\le\epsilon_R\) 的**统一**条件下，

\[
\|e_*\|\le\epsilon_B+\kappa_+(\epsilon_H+\epsilon_R),
\quad\|g_\theta-f_*\|\le\epsilon_H+\epsilon_R+\kappa_-\epsilon_B.
\tag{B21}
\]

若真实场L-Lipschitz，同初值解均留域，则已有Grönwall论证给
\(\|z_g(\tau)-z_*(\tau)\|\le(\epsilon_H+\epsilon_R+\kappa_-\epsilon_B)(e^{L\tau}-1)/L\)，L=0取连续极限。若另实际离散积分，离散误差须另加，不能混进 \(\epsilon_H\) 或 \(\epsilon_B\)。本轮有限样本只验证点态等式及实测数值，没有认证此统一常数。

\(\widetilde K\) 的空间闭性由外微分直接成立；其精确相容场是gθ。原fθ的时间相容缺陷是
\(C_\theta=K_\tau+DK[f_\theta]+(Df_\theta)^TK+KDf_\theta\)，它一般非零；由B18可得 \(C_\theta=De_B-(De_B)^T\)。所以小点态eB也不自动给小导数相容缺陷，二者应独立记录。

本轮缓存中心直接取旧S5合成分支 `inverse_verified` 的中心，使用原参数球半径ρ=.002、时间窗口0≤τ≤.0005；r2按旧方式对b1保留空间二次项、b2保留线性项。场仍在每个状态调用完整网络或完整真实ROM，不作场Taylor替代。本轮缓存的可检查局部定义域沿用S5球界：对 \(z\in B_\rho(z_c)\)，若
\(\delta_K=\|K(z_c,\tau)-K_0\|_2+\rho(\sum_j\|\partial_jK\|_2^2)^{1/2}<1\)，
则仿射K缓存及全部插值矩阵非退化，\(\sigma_{\min}K\ge1-\delta_K\)。这是指定多项式的充分条件；浮点评价不是区间数值认证，也不是实际完整一形式全域界。具体ρ/τ由本轮结果声明，不另造更方便物理参数。

## 6. 到完整线圈分支需要额外说明，不能偷换训练目标

若仍使用同一冻结网络而把真实参考改成 \(h_{\rm coil}(z,i_b)\)，则

\[
\widehat h_\theta-h_{\rm coil}
=(\widehat h_\theta-h_{\rm ideal})+(h_{\rm ideal}-h_{\rm coil}).
\tag{B22}
\]

后一项是磁物理模型差，必须单独求值/估计；不是网络对其训练目标的误差。本轮不新训网络或设计线圈。固定偏置/增量电流、能量零点、正则尺度必须一致；真实输入仍通过 \(G_{\rm coil}(Q)(i-i_b)\) 进入动量方程。求磁力时先固定电流偏导，再代反馈，反馈Jacobian另取全导。若转换还改变R或其速度解码，另加B7的δR。S6完整网络参考跟踪已明确这一区别，可直接继承，但它不是网络已学准完整线圈动力学的证据。

## 7. 本衔接结束处需要交给下一步的条件

本轮合法输出是明确标识的h、f、a、B、K、域与B18–B21误差接口。CHNN准确性与Birkhoff存在性并行：前者控制真实—学得场差，后者要求同一明确场的正则性及相容形式。

进入原Theorem A/B之前仍需确认：选择的是精确fθ还是有限构造真正表示的gθ；同一闭非退化K及两端点时间；局部流和所用图逆留域；端点二形式拉回匹配及投影横截性。若用Theorem B解析展开，还须同一对象的解析性、固定生成坐标求导、展开/截断余项与重构可逆域。正Hpp只在另作机械Legendre转换时需要，不能替代这些条件。这里只列交接条件，不计算第二个衔接点的生成函数、原30—36或KAM。

## 8. 本轮实际桥接证据及其边界

`results/B01_run03/report.json` 与配套NPZ使用上述同一冻结网络、真实H_ideal、相同R、旧初态、ρ=.002及T=.0005。没有重训、改参数或推进下一桥。下表为旧缓存中心在τ=.0005的无量纲正则数值；不是统一域上界。

|独立量|r1一形式|r2一形式|
|---|---:|---:|
|学习场误差\(\|f_\theta-f_*\|\)|1.11412694e−3|1.11412694e−3|
|对学得场的表示残差\(\|e_B\|\)|3.62225319e−5|6.45216832e−6|
|同一对a/B对真实场残差\(\|e_*\|\)|1.11052614e−3|1.11157076e−3|
|B19符号恒等式余差|2.30e−17|1.93e−17|
|真正表示场与学得场之差\(\|g_\theta-f_\theta\|\)|3.62173473e−5|6.45122944e−6|
|对学得fθ的时间相容缺陷|3.24803e−3|3.48417e−4|
|对真正表示场gθ的时间相容缺陷（最大分量）|2.73e−15|2.74e−15|

两阶闭性最大分量均0，K条件数约1.00009。以已有浮点球界评价r2在所声明球内的充分最小奇异值下界为0.9997744503。另对**保存的缓存点多项式本身**作精确有理检查：把保存的二进制系数视作精确有理数，令其雅可比/二阶系数为J_k、H_k，在 \(|z-z_c|_\infty\le r=1/500\)、\(0\le\tau\le T=1/2000\) 上逐项取

\[
A_{ij}=\sum_{k=1}^{2}T^k\left[|(J_k)_{ji}-(J_k)_{ij}|
 +r\sum_l|(H_k)_{jil}-(H_k)_{ijl}|\right].
\]

绝对值三角不等式给 \(|(K-K_0)_{ij}|\le A_{ij}\)；令δ为A的最大行和/列和的较大者，则
\(\|K-K_0\|_2\le\sqrt{\|K-K_0\|_1\|K-K_0\|_\infty}\le\delta\)。精确Fraction加乘求得
\(\delta=113825318032753881167091/590295810358705651712000000<1\)，因此这整个盒/时间窗内
\(\sigma_{\min}K\ge1-\delta\approx0.9998071724\)。盒包含前述欧氏球。这是明确的缓存结构非退化域，不是网络学习误差或真实原生输运的统一域证书，也未包围浮点执行全部舍入。缓存原始Hessian舍入级不对称已按旧S5方法检查后平均，并保留raw证据；如此系数才与所定义缓存多项式导数一致。

物理质量在中心正定，并与原点质量相差0.0245608（结果记录的矩阵范数）；没有用常质量替换。共享R下旧b1与新b1差为0，而物理场旧b2与网络b2相差1.03644e−4，证明直接搬用旧二阶缓存会改变本桥对象。

保守B10在中心和旧物理端点的直接表示残差均0；另复用已有比例阻尼 \(R=-.2P\) 的精确对 \(a=e^{.2\tau}a_0,B=e^{.2\tau}\widehat h\)，残差≤1.67e−17。这些精确基准避免将不必要的一形式截断误差归因于物理或学习。

原生时间系数在两个固定点的r1/r2残差细化分别为一阶/二阶。这里是B18所定义时间展开余项，不是新积分器阶数。离开中心，缓存与原生r2残差另有非零差，旧物理端点τ=.0005为5.62e−9；未隐藏空间缓存误差。

三种场各自用DOP853双容差短积分，参考细化差分别≤1.05e−17、2.91e−18、2.66e−18。最大轨迹差分别为学得—真实5.76978e−7、表示—学得1.05578e−9、表示—真实5.76395e−7。后者略小只反映误差向量相消，不说明Birkhoff构造改善学习。最大缓存中心距离1.21918e−4，小于声明半径；这是本轨迹留域证据，不能推出所有同域初态都留域。没有把数值参考细化差称为严格误差包围。

独立网络检查还保留原test146的负 \(\widehat h_{PP}\) 特征值约−.0692894、test180的相反功率符号，以及机械a1 shortcut对完整网络的非零误差。这些反例意味着：本桥的相空间对象和误差恒等式已实际接通，但整个训练域的正机械解释、统一真实场精度及共同耗散性仍未成立。
