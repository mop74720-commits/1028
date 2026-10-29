# 高阶一形式、规范选择、数值 Moser 与真实三维动力学

本节连接第四阶段审计的完整一般 Birkhoff 理论与第五阶段程序，不重写原稿 A/B 或原（30）—（36）。其完整修正版本见 `stage5/proofs/corrected_mathematics.md` 的 Theorem A/B、固定生成坐标递推及（30）—（36）部分，并对照 `stage4/audit/birkhoff_full_audit.md`。这里的有限时间阶数、局部图、磁控制实现、连续/离散 KAM 是不同证明责任。所有主场求值保留继承 RodROM 的完整20几何单元 SO(3)、12配置自由度、24维相空间、位形相关质量和全部几何惯性；没有以常质量代替原场。

## 1. 符号和两个不同截断

约定 \(Da_{ij}=\partial_j a_i\)、\(J=(0,I;-I,0)\)、\(K_0=-J\)、\(\alpha_0=p\cdot dq\)。原机械场为

\[
f=(H_p,-H_q+R),\qquad H=T(q,p)+V(q),\quad T=\tfrac12p^TM(q)^{-1}p.
\]

R 是明确给出的真实广义力接口。本轮既有合成光滑非比例/状态相关载荷，也有全 Biot–Savart 磁能及共点电流反馈的实际 ROM 闭环；两者在数据中分开，不把前者称为已校准血流或摩擦。

齐次一形式输运是

\[
\partial_t a+\mathcal L_f a=0,\qquad
\mathcal L_f a=(Da)f+(Df)^Ta,\quad B=a^Tf,
\quad K=(Da)^T-Da.
\]

固定时间原点0的自治系数满足 \(a_{j+1}=-\mathcal L_fa_j/(j+1)\)。`transport_native.py` 仍实现这条递推并保存第一轮真实导数成本；它保留第四阶段对纯Hamiltonian梯度导致低阶截断失真的反例。高阶有限输运不是未知精确流输入；它只用局部场及导数。

但可以先选择适当规范再截断。令 \(\ell=T-V=p^TH_p-H\)。直接用动能对p二次齐次性有

\[
\mathcal L_f a_0=d\ell+R\cdot dq.
\]

定义有源一形式 \(a'=a_0+b\)，取

\[
b_0=0,\quad b_1=-(R,0),\qquad
b_{j+1}=-\frac1{j+1}\mathcal L_f b_j.
\tag{1}
\]

则无限形式对应 \(\partial_ta'+\mathcal L_fa'=d\ell\)，不是齐次输运。选择

\[
B'=a'^Tf-\ell=H+b^Tf
\tag{2}
\]

得到所需 Birkhoff 表示。对 r 阶时间截断 \(b^{[r]}=\sum_{j=1}^rt^jb_j\)，

\[
e_B=K^{[r]}f-a_t'^{[r]}-\nabla B'^{[r]}
=-t^r\mathcal L_f b_r,
\quad f_a=f-(K^{[r]})^{-1}e_B.
\tag{3}
\]

这给固定状态、固定原点的表示残差阶r。它不是离散时间积分器的全局r阶声明；积分误差需另测。若R=0，则所有b_j=0，a'=a0、B'=H精确，避免旧一阶齐次截断即使无阻尼仍破坏原场的问题。若R=-γp且γ为常数，另有精确指数结构a=e^{γt}a0、B=e^{γt}H；本有源截断不声称等于这一精确规范，合法加权基准单独实现。

## 2. 与原齐次输运的规范关系及有限截断末项

解局部标量方程 \(\sigma_t+f\cdot\nabla\sigma=\ell\)、\(\sigma(0)=0\)。由于外微分与Lie导数交换，\(a=a'-d\sigma\) 满足齐次输运，且B=B'+σ_t=a^Tf。这是规范等价的条件推导；未知标量PDE精确解未被当作算法输入。

可逐阶算 \(\sigma_1=\ell,\ \sigma_{j+1}=-(f\cdot\nabla\sigma_j)/(j+1)\)。逐系数有 \(a_j=b_j-d\sigma_j\)。**截断与规范变换一般不交换**：只取σ到r阶，并把原齐次a截到r阶、B取a·f，变回有源形式时，B与式(2)还差末阶 \(t^r f\cdot\nabla\sigma_r\)。本方法是对等价有源方程重新截断，不是假称对旧有限阶结果作规范就消除其原场误差。若要以有限σ把本对(a',B')变回齐次表示到同阶，需要保留σ的下一阶和由此产生的一形式高阶项。测试独立核对前三个系数关系。

## 3. 原场不变，仅缓存一形式的空间Taylor系数

直接在每个 Moser 辅助场求值中重新计算高阶原生AD会很昂贵。程序采用明确的第二层近似：在初态z0处以原场AD求得b_j及其空间导数，缓存

\[
\widetilde b_j(z)=b_j(z_0)+Db_j(z_0)\delta z
+\tfrac12D^2b_j(z_0)[\delta z,\delta z],
\quad\delta z=z-z_0.
\]

数据逐阶记录是否保留二次项；未算的二次项不冒称已算。主合成分支b1/b2二次、b3线性；完整线圈分支b1二次、b2线性。所有实际场和参考仍使用完整 \(f_{\rm full}\)、\(Df_{\rm full}\)、\(H_{\rm full}\)，不是空间Taylor场，更没有冻结M(q)。所用定义是

\[
\widetilde a=a_0+\widetilde b,\quad
\widetilde B=H_{\rm full}+\widetilde b^Tf_{\rm full},\quad
\widetilde K=K_0+(D\widetilde b)^T-D\widetilde b.
\]

在缓存中心，因为b_j与Db_j均原生精确取值，各阶时间截断表示残差等于原生时间jet的残差。离开中心后，空间缓存产生独立误差；程序在实际偏离方向重新用原生AD计算b_j、Db_j，报告系数差、导数差、\(e_B\)差和两个表示场的差，而非只给缓存自洽残差。

实际表示残差可不经过高阶AD重复计算而直接写成

\[
\widetilde e_B=-\left(\widetilde b_t+D\widetilde b f_{
\rm full}+Df_{\rm full}^T\widetilde b+(R,0)\right),\quad
\widetilde f_a=f_{\rm full}-\widetilde K^{-1}\widetilde e_B.
\tag{4}
\]

此式准确对应定义的(\(\widetilde a,\widetilde B\))，也说明 `field_approximated=False` 仅表示**没有对原场求值器作Taylor近似**，不表示推进的 \(\widetilde f_a\) 等于原f。闭性来自外微分，是代数性质；时变相容性针对 \(\widetilde f_a\)，对原f应独立测 \(K_t+DK[f]+Df^TK+KDf\)。

实际切线采用

\[
D\widetilde f_a=\widetilde K^{-1}
\left(\nabla^2\widetilde B+D\widetilde b_t-
[\partial_{z_j}\widetilde K\,\widetilde f_a]_j\right).
\]

H及f中的全部原模型导数进入 \(\nabla^2\widetilde B\)；缓存不是把切线中反馈链式项冻结。

## 4. 真正数值求解的24维Moser辅助流

在固定物理时间t，取

\[
K_{\lambda,t}=K_0+\lambda(\widetilde K_t-K_0),\quad
v_{\lambda,t}=K_{\lambda,t}^{-1}\widetilde b_t^{\rm value},
\quad \partial_\lambda\rho_{\lambda,t}=v_{\lambda,t}\circ\rho_{\lambda,t}.
\]

上标value强调右侧为一形式差的当前值 \(\widetilde b(z,t)\)，不是时间导数。用DOP853实际积分λ∈[0,1]；逆图χ通过同一辅助场从λ=1反向积分至0。由于 \(\iota_v\Omega_\lambda=-\widetilde b\cdot dz\)，精确辅助流满足ρ*Ω_t=Ω0，χ*Ω0=Ω_t。数值积分的图匹配、逆复合、容差/λ步长细化差均独立记录，未把数值图称为精确图。

程序同时积分 \(R=D_y\rho\)、\(w=\rho_t\)：

\[
R'=D_zvR,\quad w'=D_zv\,w+v_t,
\quad R(0)=I,w(0)=0.
\]

因此转换场是

\[
g(y,t)=R^{-1}\{\widetilde f_a(\rho(y,t),t)-w\}.
\tag{5}
\]

这实际包含χ_t，不能只算Dχf。进一步积分二阶状态敏感度S=D²ρ和W=D_yρ_t：

\[
S'=DvS+D^2v[R,R],\qquad
W'=DvW+D^2v[R,w]+Dv_tR.
\]

于是 \(Dg=R^{-1}(D\widetilde f_a R-W-S[\cdot,g])\)，实现中逐索引收缩，并用独立有限差分测试。它用于首步隐式切线和二形式缺陷，避免用“冻结图/冻结反馈”的条件切线。

非退化性检查包括全部实际求解器λ采样点、均匀17点及缓存多项式整个球域的解析充分界：若\(\delta_K\)界定球内 \(\|K-K_0\|_2\) 且δK<1，则所有λ∈[0,1]的最小奇异值至少1−δK。多项式K为仿射空间函数，其界可由中心值和DK直接算；\(\|b\|/(1-\delta_K)\)给辅助速度界。初点距球心加此速度界小于半径时，用首次离域反证保证精确辅助轨迹留域。这是**给定浮点系数多项式的解析充分条件**；当前数值上界未作有向舍入区间认证，不能升级成完整物理域的严格数值证书。

## 5. 积分、分离误差与控制适用条件

数值方法在同一时间中点解完整g的隐式中点，残差无穷范数2e−13；弦矩阵仅预条件器，最终接受以实际g残差为准。理想图/精确求解下中点在图中辛，回拉保缓存K。实际有限辅助/隐式误差和图导数误差另报。

每个阶r的同一初态/区间/网格分别比较：原f独立DOP853参考；缓存表示场 \(\widetilde f_a\) 的两档DOP853参考；真正Moser图中点。曲线细化所得二阶是对 \(\widetilde f_a\) 的积分阶；相对原f可能出现表示误差平台。报告原生时间jet差、额外空间缓存差、Moser匹配与实施误差、时间积分差、求解残差、CPU成本，不把任意一项替代另一项。

在共同光滑域、K逆/图逆有界、稳定隐式分支下，时间截断与缓存的统一原场差 \(\epsilon_f\) 给有限时 \(\epsilon_f(e^{LT}-1)/L\)；二阶中点给 \(C_T(h^2+\eta_h/h)\)，辅助图每步状态误差也需累计。当前点态样本并未认证全部统一常数，故不声称全域误差定理已数值核实。

合成载荷的正对角“动量阻尼系数”**不保证机械功率非正**：\(-p^TM^{-1}D(q)p\)在两个SPD矩阵不交换时不能由系数正性直接定号。它只是明确的平滑测试载荷。完整线圈共点反馈 \(R=-\kappa G_I G_I^T H_p\) 则严格满足 \(H_p^TR=-\kappa\|G_I^TH_p\|^2\le0\)，前提是实际同一输入未被限幅等操作改变。无论功率负否，耗散闭环不能自动保原K0；本构造给该实际闭环的近似Ku。时间序列图与有限时间收敛仍未满足三维连续/离散KAM的解析域、共振处理和小量等条件。

## 6. 时间依赖一般递推的范围与本轮实施边界

若在同一时间原点采用含阶乘的幂系数
\(f(z,t)=\sum_{s\ge0}t^sf_s(z)\)、\(a(z,t)=\sum_{r\ge0}t^ra_r(z)\)，把系数逐幂相等给出

\[
a_{m+1}=-\frac1{m+1}\sum_{r+s=m}
\{Da_r f_s+(Df_s)^Ta_r\}.
\]

这里外部脉动输入、非自治反馈的显式时间导数必须进入 \(f_s\)，不能把它们埋进一个自治 \(f_0\) 后套用单项递推。本轮程序真正运行的是两个**自治光滑分支**：非比例状态相关合成载荷及完整线圈共点状态反馈。因此 `NativeTransport` 的单项递推准确针对这些分支，而没有宣称完成任意脉动血流或接触切换的一般输运。光滑性、系数收敛半径、空间导数统一界均是无限解析展开的额外假设；有限多项式及其残差可直接求值，并不依赖证明整个级数收敛。

本轮在固定时间原点和固定空间球中计算，没有每一步重置一形式，也没有把彼此不同的局部结构拼成一个全局结构。覆盖更长实际轨迹需要明确的重叠图、过渡映射与二形式一致性；这仍未实现。

## 7. 高阶AD错误的修复不是对物理质量矩阵的近似

独立最小反例与实际ROM检查发现，当前 PyTorch 2.5.1 中某些**嵌套前向/反向组合通过 `torch.linalg.solve`** 的高阶导数给错值。不能由一二阶结果正确或局部张量某两轴对称推断四阶结果正确。原始失败与当时得到的数值结果保留，不能作为最终高阶结论。

新高阶求导私有表达式使用

\[
H_{\rm AD}(Q,P)=\tfrac12P^T[M_{\rm full}(Q)]^{-1}P+H_{\rm original}(Q,0).
\]

它每次在实际Q计算完整几何质量，故代数上与原机械 Hamiltonian 相同；原物理场及参考解仍使用原 `solve` 路径。此替换本身不是证明AD正确，因而另以纯反向方向导数和有限差分检验。`results/high_derivatives/transport.json` 中，两方向的三阶输运系数Jacobian旧实现与独立反向计算相差0.2844和0.3449，而新实现差为 \(7.11\times10^{-14}\)、\(5.68\times10^{-14}\)。`backend_validation_synthetic_inverse.json` 还真正算出齐次 \(a_1,a_2,a_3\) 并与 \(b_j-d\sigma_j\) 比较，三阶误差 \(4.44\times10^{-12}\) 对应系数范数约36788。完整线圈分支亦检查三、四阶方向导数。它们是指定点和方向的独立数值检验，不是所有状态所有阶数的AD正确性证明。

新run的源代码在运行开始即按字节保存，空间缓存以模型、初态、增益、阶数和源代码哈希共同指纹标识。旧缓存不用于新run；原错误版本结果不覆盖。新缓存的Hessian先保留原始张量并检查反对称部分，再对舍入级反对称做平均；**不以强制对称掩盖错误导数**。

## 8. 原场参考的数值版本边界

实际连接的完整线圈源为 `stage5/program/coil_rom.py`。旧中点实验的冻结核为 `stage5/results/closed_loop/source_used/coil_rom.py`。范数表达式修复虽保持数学磁场不变，舍入及偏置重拟合使新旧电流存在最大6.56142e−14 A差；不可把“相同数学控制定义”写成逐位相同数值输入。`stage5/program/run_transport_reference_bridge.py` 已独立以当前原场重新积分同一个严格参考，65点轨迹差最大5.76978e−19；源哈希、偏置、场值和对当前参考重新评估的六个误差在 `stage5/results/transport/inverse_verified_reference_bridge.json`。原共享参考及原实验数据不覆盖。

可计算构造对应 `stage5/program/transport_native.py`、`stage5/program/transport_cache.py`、`stage5/program/moser_chart.py`；主实验为 `stage5/program/run_transport_experiments.py`。24维图时间导数和Jacobian独立差分为 `stage5/program/run_transport_tangent_checks.py`；精确分支/域失败为 `stage5/program/run_transport_domains.py`；同原场、同Ku、功率与误差分解为 `stage5/program/run_transport_postprocess.py`。这些程序的数值检查分别支持上文特定实施环节，不能以一个输出文件代替全部定理假设。
