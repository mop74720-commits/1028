# 非自治线圈反馈：一般输运系数真正进入24维ROM

证据分类：下面的有限系数恒等式为直接代数推导；程序对实际三维 Kirchhoff ROM 的指定点和短窗独立检验。未给出全域解析延拓、任意接触切换输运或新的KAM证书。原始位置为 `original1025-p0846..p0851/m0362..m0366`（不相容原构造需修正）及 `p1082..p1088/m0481..m0487`（实际控制如何进入同一隐式格式）。融合稿 `controlled_analysis.tex:5,17,36,79,92` 的物理输入、结构判据和残差递推完整继承。第五阶段 `proofs/birkhoff_transport.md:151-163` 已正确给出一般时间卷积递推，但实际程序仅运行自治场；这里补齐一个真实非自治磁端口实例。

## 1. 实际闭环及部分导数

保持第五阶段完整 Biot–Savart 能量、12个配置变量、20个几何积分单元、12个总电流及全部位形质量：

\[
H_0(Q,P)=\tfrac12P^T\bar M(Q)^{-1}P+V_e(Q)+v(Q)^Ti_0,
\quad G(Q)=-D_Qv(Q)^T.
\]

采用已知、光滑、正的时变增益

\[
\kappa(\tau)=\kappa_0[1+a\sin(\Omega\tau)],\quad |a|<1,
\quad i(\tau,z)=i_0-\kappa(\tau)G(Q)^TH_{0,P}(z),
\]

\[
f(\tau,z)=J\nabla H_0+(0,R(\tau,z)),\quad
R=-\kappa(\tau)GG^TH_{0,P}.
\tag{N1}
\]

物理 Hamiltonian 求导先固定电流，再代入反馈；求闭环状态Jacobian时才对反馈取全导。程序使用第五阶段 `feedback_field`/`feedback_jacobian`，不把任意24维增量解释为磁输入。原场每次重算完整 \(M(Q)\)；仅一形式空间系数使用缓存。高阶求导继承已验证的完整质量逆矩阵私有表达式，避免已记录的嵌套 `solve` AD错误，没有冻结质量。

采用 \(\tau=\omega_0t\)、能量尺度 \(E_0\)；\(\Omega\) 为无量纲时间角频率，其物理角频率为 \(\Omega\omega_0\)。输入是总电流A，偏置不重复计入。本实验的 \(a=0.25,\Omega=200\) 是规定控制调制，**不是生理脉动血流标定**。

由于 \(H_0\) 不显含时间，有

\[
\frac{dH_0}{d\tau}=\nabla H_0^Tf
=-\kappa(\tau)\|G^TH_{0,P}\|^2\le0.
\tag{N2}
\]

此处没有 \(\dot\kappa\) 项：所观测的是固定偏置能量 \(H_0\)，不是把 \(i(z,\tau)\) 代入后当作新的闭环Hamiltonian。物理功率乘 \(E_0\omega_0\)。正增益不保证电流/变化率/场强处处满足硬件约束；程序另报告采样值，未把限幅插入此光滑场。

## 2. 非自治有源规范与完整卷积

固定原点 \(\tau=0\)，用含阶乘的时间幂系数

\[
f=\sum_{s\ge0}\tau^sf_s,\quad R=\sum_{s\ge0}\tau^sR_s,
\quad b=\sum_{r\ge1}\tau^rb_r,\quad b_0=0.
\]

记 \(a_0=(P,0)\)、\(\ell=P^TH_{0,P}-H_0\)。直接微分 \(a_0\) 得
\(\mathcal L_fa_0=d\ell+(R,0)\)，对每个时间均成立。令 \(a'=a_0+b\) 满足

\[
\partial_\tau b+\mathcal L_{f(\tau)}b=-(R(\tau),0),
\quad B'=H_0+b^Tf(\tau).
\tag{N3}
\]

则 \(\partial_\tau a'+\mathcal L_f a'=d\ell\)。利用
\(\nabla(a'^Tf)=(Da')^Tf+(Df)^Ta'\)，有

\[
[(Da')^T-Da']f=\nabla B'+\partial_\tau a'.
\]

因此这是齐次输运的有源规范，不冒称 \(a'\) 本身满足齐次方程。局部标量 \(\sigma_\tau+f\cdot\nabla\sigma=\ell\) 给 \(a=a'-d\sigma\)、\(B=B'+\sigma_\tau=a^Tf\) 的齐次规范；未知 \(\sigma\) 精确解没有输入任何算法。截断规范边界沿用第五阶段证明。

比较式(N3)的 \(\tau^m\) 系数，得到

\[
b_{m+1}=-\frac1{m+1}\left[(R_m,0)+
\sum_{r=1}^{m}\{Db_r f_{m-r}+(Df_{m-r})^Tb_r\}\right].
\tag{N4}
\]

这里 \(R_m\) **不可遗漏**。代码实现这一卷积，而非仅将自治公式的 \(f_0\) 换一个时间标签。尤其

\[
b_1=-(R_0,0),\qquad
b_2=-\tfrac12[(R_1,0)+\mathcal L_{f_0}b_1].
\tag{N5}
\]

本例 \(R_1=a\Omega R_0\)，因此已验证自治缓存可精确转接为

\[
b_1^{\rm new}=b_1^{\rm old},\qquad
b_2^{\rm new}=b_2^{\rm old}+\tfrac{a\Omega}{2}b_1^{\rm old}.
\tag{N6}
\]

新程序逐字节验证旧缓存关联的线圈源、增益、初值，并重新AD求原生 \(b_1,b_2,Db_1,Db_2\) 作独立检查。旧缓存保留的空间次数为[2,1]，所以(N6)只用于b2值和Jacobian；没有把未求出的b2二阶空间项称为已有。源缓存和旧结果不写入。

若错误地继续使用自治b2，则有 \(2b_2+\mathcal L_{f_0}b_1=0\)，但真实(N3)的首阶残差仍是 \(\tau(R_1,0)\)。除非 \(R_1=0\)，原场表示误差只有一阶。这是确定的遗漏反例，并非新物理模型自身的困难。

## 3. 截断、闭性和实际表示场

对任意有限多项式缓存 \(\widetilde b\)，定义

\[
K=K_0+(D\widetilde b)^T-D\widetilde b,\quad
B=H_0+\widetilde b^Tf(\tau),\quad
S=\widetilde b_\tau+D\widetilde b f+(Df)^T\widetilde b+(R,0).
\]

直接代数给 \(e_B=Kf-\nabla B-a_\tau=-S\)。在K非退化处，真正与此对 \((a,B)\) 相容的场是

\[
f_a=f+K^{-1}S.\tag{N7}
\]

空间闭性 \(dK=0\) 来自外微分；精确代数下 \(K_\tau+DK[f_a]+Df_a^TK+KDf_a=0\)。这**不意味着**原f的输运相容性残差为零。代码分别记录eB、\(f_a-f\)、原f的二形式输运缺陷、空间缓存引入的额外误差、K条件数和闭性。

原生时间r阶系数满足(N4)时，固定z处 \(S=O(\tau^r)\)。要升级为统一域估计，还需导数/余项界和K逆界；有限采样不能证明这些常数。浮点缓存闭性也不能替代原场准确度。

## 4. Moser和同场隐式更新：复用已有算法

直接复用第五阶段 `MoserChart` 的辅助流、逆图、时间及一二阶状态敏感度，不复写旧算法。以 \(\rho_\tau^*K_\tau=K_0\)、\(\chi_\tau=\rho_\tau^{-1}\) 的约定，图场

\[
g(\tau,y)=(D\rho_\tau)^{-1}[f_a(\tau,\rho_\tau(y))-\partial_\tau\rho_\tau(y)].
\]

对g在同一未知中点和时间中点解完整隐式残差；控制的 \(\kappa(\tau_m)\)、实际反馈导数、图时间导数都进入。旧例程中时间零的Df仅作为弦迭代预条件器；验收残差和切线使用真实时变g，故并未冻结实际物理场。

作为公平比较，普通中点同样解 \(z_+-z_-=h f(\tau_m,(z_++z_-)/2)\)，反馈实际求在未知中点。两者共有初值、时间窗和原f参考；图方法另有独立fa参考，以分离积分误差和表示模型差。只对fa的二阶收敛不等于对原f无误差。测量数值辅助图误差不宣称浮点程序exact symplectic；恰当辛原函数和条件性收敛继承融合稿与第五阶段，不用残差接近零代替证明。

本轮只有固定原点、固定球和短时间窗，未逐步重置一形式。一般长轨迹所需的相邻图过渡、饱和活动集、真实血流/接触/柔性壁和高维杆转移仍待完成。耗散非自治闭环不符合已选自治保守KAM定理。
