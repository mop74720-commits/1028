# 7 Birkhoff 生成函数 控制与收敛的统一推导

## 7.1 相容一形式与局部构造

在一个光滑的偶维机械相空间局部坐标域内，先确定实际向量场 $\dot z=f(z,t)$，包括真实质量导数、阻尼和所选择的控制。取一形式 $\theta=R_i(z,t)\,dz_i-B(z,t)\,dt$，定义

$$\mathcal K_{ij}=\partial_iR_j-\partial_jR_i,\qquad \mathcal K f=\nabla B+R_t.\tag{A1}$$

这里 $R$ 是Pfaff一形式系数，不是三维姿态矩阵，后文用上下文区分。除 $K$ 反对称和 $\det K\ne0$ 外，还要求空间闭性及时间相容性：

$$d_z\Omega_t=0,\qquad \partial_t\mathcal K+(f\cdot\nabla)\mathcal K+(Df)^T\mathcal K+\mathcal K Df=0,\tag{A2}$$

其中 $\Omega_t=\tfrac12K_{ij}\,dz_i\wedge dz_j$。A2等价于沿同一真实流保持 $D\Phi^TK(\Phi,t)D\Phi=K(z,t_0)$。它不等于保持固定欧氏体积，也不等于机械能守恒。

一般B材料提供的可用局部构造是解一形式输运方程

$$R_t+(DR)f+(Df)^TR=0,\qquad B=R^Tf.\tag{A3}$$

因为 $\nabla B=(DR)^Tf+(Df)^TR$，代入即得A1。若初始 $dR_0$ 非退化，真实局部微分同胚的拉回保留非退化性。这个存在性说明有价值，但计算A3仍需输运方程或等价的流与变分计算；不能视为免费获得结构矩阵。

规范变换 $\widetilde R=R+\nabla\sigma$、$\widetilde B=B-\sigma_t$ 不改变A1。令 $\sigma_t=B-H$ 可令 $\widetilde B=H$，但没有减少构造 $R$ 和 $K$ 的难度，也不能消去近似输运的原场表示误差。后文实际Moser算例正好量化了这一点。

## 7.2 Theorem A 和 B 的可用衔接

按照Feng–Qin第15章Theorem3.5、4.1、4.4和4.5，生成坐标 $\alpha:(\widehat z,z)\mapsto(\widehat w,w)$ 必须满足端点二形式适配，而非仅为可逆变换。写 $D\alpha$ 的四个块为 $A_\alpha$、$B_\alpha$、$C_\alpha$、$D_\alpha$，有

$$D\alpha^T\mathbb J D\alpha=\operatorname{diag}(\mathcal K(\widehat z,t),-\mathcal K(z,t_0)).\tag{A4}$$

若真实相流 $M=D_z\Phi$ 满足 $\det(C_\alpha M+D_\alpha)\ne0$，则生成图的Jacobian为

$$N=(A_\alpha M+B_\alpha)(C_\alpha M+D_\alpha)^{-1}=N^T.\tag{A5}$$

局部存在 $\widehat w=\nabla_w\phi$；标量 $\phi$ 只确定到与 $w$ 无关的函数，须另给规范。初时 $M(t_0)=I$，所以初始横截条件为 $\det(C_\alpha+D_\alpha)\ne0$，初始生成梯度由对角端点图确定：$f_0(w)=\alpha_1(z,z,t_0,t_0)$，其中 $w=\alpha_2(z,z,t_0,t_0)$。一般图上 $f_0$ 不必为零，不能默认沿用某个中央图的初值。无需 $N$ 本身可逆，原稿把 $N(t_0)=0$ 与 $N$ 可逆并用的问题由此消除。固定初始端点，令 $X=f$，则

$$\partial_t\nabla_w\phi=(A_\alpha-NC_\alpha)X+\partial_t\alpha_1-N\partial_t\alpha_2.\tag{A6}$$

解析时可按幂系数递推生成梯度 $f_j$：

$$f_{j+1}=\frac1{j+1}[h^j]\,\mathcal A\left(\sum_{r=0}^jh^rf_r,w,\sum_{r=0}^jh^rD_wf_r,t_0+h,t_0\right).\tag{A7}$$

必须保持每个 $f_j$ 是梯度。截断后用Theorem4.5将 $\alpha_1=\sum_jh^jf_j(\alpha_2)$ 还原到端点变量，还须验证截断图的逆横截性。若 $D(\alpha^{-1})$ 的下排块为 $C^\alpha$、$D^\alpha$，$N_m$ 为截断梯度的Jacobian，则要求 $\det(C^\alpha N_m+D^\alpha)\ne0$；正确初值及解析性下可在足够小步长局部由连续性保证。仅在精确相流上检查A5的分母可逆，并未自动核验这一步。原稿的A／B不独立给出磁输入可实现性、非光滑接触上的解析性或KAM结论。一般变质量三维ROM已有Hamiltonian接口，但本轮尚未把A3—A7的完整一般推进算法接到该ROM；实际实现及误差检查见本章后半部分。

## 7.3 原36的矩阵推导和一般变质量形式

由F21，对 $z=(q,p)$ 直接写真实中点残差：

$$q_+-q=hM(\overline q,\overline t)^{-1}\overline p,\tag{A8}$$

$$p_{+,i}-p_i=h[-\tfrac12\overline p^T(\partial_iM^{-1})\overline p-\partial_iV+Q_{{\rm nc},i}]_{(\overline q,\overline p,\overline t)}.\tag{A9}$$

所有中点和未知量必须同时求解。对常 $M$、$K_s$、$C$，令 $Q_{\mathrm{nc}}=F-CM^{-1}p$，$V=q^TK_sq/2$。将 $q_+=q+(h/2)M^{-1}(p_++p)$ 代入动量中点，令

$$E_h=\tfrac{h^2}{4}K_sM^{-1}+\tfrac h2CM^{-1},$$

得到正确的原（36）推广：

$$p_+=(I+E_h)^{-1}[(I-E_h)p-hK_sq+hF_{1/2}],\quad q_+=q+\tfrac h2M^{-1}(p_++p).\tag{A10}$$

逆矩阵从左乘，$K_sM^{-1}$ 和 $CM^{-1}$ 不可任意交换；只有单自由度才是一个标量分式。实际可解对称或一般线性系统，而不显式构造逆：

$$[M+\tfrac h2C+\tfrac{h^2}{4}K_s]\overline v=p-\tfrac h2K_sq+\tfrac h2F_{1/2},\quad q_+=q+h\overline v,\quad p_+=2M\overline v-p.\tag{A11}$$

变质量／非线性情况下A10中的系数仍依赖未知中点，不能把它称作显式算法。应直接实现A8—A9的残差和Newton Jacobian，加入正确的磁反馈链式导数。

A8—A9是二阶数值方法；在无非保守力或力可吸收为势的正则分支，理想隐式映射保辛。阻尼振子即给反例：对于 $\dot z=Az$、$\operatorname{tr}A=-\gamma$，中点映射 $D\Psi=(I-hA/2)^{-1}(I+hA/2)$ 的行列式通常不等于1，也不精确等于 $\exp(-\gamma h)$。因而它既非通常辛映射，也不自动保持所选连续指数加权二形式。

## 7.4 高阶中央生成函数及非可分实现

对自治正则保守场 $f=J\nabla H$，精确流的端点差用端点平均 $m$ 表示为

$$z_+-z_-=hf(m)+\tfrac{h^3}{24}[D^2f[f,f]-2(Df)^2f](m)+O(h^5).\tag{A12}$$

恒等式 $J\nabla(f^TH''f)=D^2f[f,f]-2(Df)^2f$ 给出

$$S_h=hH+\tfrac{h^3}{24}f^TH''f,\qquad z_+-z_-=J\nabla S_h(m).\tag{A13}$$

这正是应恢复的原v10一般非可分Central4。Newton矩阵为 $I-\tfrac12JS_h''$，不是普通中点的 $I-hDf/2$。即使学习能量含全部混合动量项，A13仍成立，但需要相应三、四阶导数与解析分支；仅保留某个可分势能的专门导数实现不够。

令 $C_h=\tfrac12JS_h''$，隐式切线为 $(I-C_h)^{-1}(I+C_h)$，Hessian对称给出辛性；相应原始一形式差为全微分才能进一步用于exact symplectic映射的KAM。有限Newton容差的输出必须额外报告实施误差，不把该代数证明直接赋给一个未收敛迭代。

对于非自治合法规范图，应把图时间导数计入场，使用时变中点或合法Gauss阶段；不能把A13的自治式不加处理地代入任意阻尼、饱和、血流或接触场。

## 7.5 $U_k$ 的选择及物理实现判据

若 $U$ 表示动量方程的力，离散增量具有 $hU$ 的尺度；若 $U_k$ 被定义为状态增量，应明确它已包含步长。任意大小有界的附加增量没有保结构定理。

| 控制方案 | 可说明的目标 | 结构与磁实现限制 |
|---|---|---|
| 无控制 | 真实耗散和血流基准 | 不人为删除已有外部功率 |
| 精确阻尼补偿 | 补偿已知 $Cv$ | 是主动能量注入；其余流体／接触不补偿时不恢复保守系统 |
| 学习补偿 | 用学习误差模型修正力 | 残余误差须计入；含动量残差时速度是 $H_p$，不能偷换成固定 $M^{-1}p$ |
| 理想全驱动力 | 分离算法／模型误差 | 是理论上界对照；不等于磁硬件能够施加同一 $U$ |
| 一致势形控制 | 通过闭环磁势保留Hamiltonian分支 | 例如 $i_a=i_{0a}-k_a(\phi_a-\phi_{\mathrm{ref},a})$，闭环势为 $-i_0\cdot\phi$ 加上 $\tfrac12\sum_a k_a(\phi_a-\phi_{\mathrm{ref},a})^2$ |
| 共点端口阻尼 | $y=G_m^T\dot q$，$u=-K_y y$，控制功率 $-y^TK_y y\le0$ | 给出被动耗散而非通常辛性；饱和和偏置须重新核查 |
| 轨迹前馈与反馈 | 实际跟踪、抗流与接触 | 非共点速度反馈可激发高频模态；本轮已经出现不合格长轨迹 |
| 采样保持与受限线圈 | 体现带宽、电流及场约束 | 闭环导数含输入对状态的导数；固定输入子步辛性不等于闭环辛性 |

在已知 $K$ 下，新增 $g=G_u u$ 仍保持同一 $K$ 的局部充分条件为 $Kg=\nabla W$，即所对应一形式恰当；任意反馈通常不满足。若重新构造闭环 $K_u$，则必须报告保持的是新 $K_u$，不能仍用无控制结构作结论。实磁力由固定电流磁势对 $q$ 的偏导得到；将反馈 $i(q)$ 直接代回原磁势再对全部 $q$ 求导会多出非物理项，除非重新构造上述一致闭环势。

## 7.6 三类误差分别证明

普通中点的状态增量残差 $r_k$ 满足离散稳定估计

$$ (1-hL/2)e_{k+1}\le(1+hL/2)e_k+Ch^3+\|r_k\|.\tag{A14}$$

在共同紧域、稳定隐式分支和 $hL/2<1$ 条件下，得到固定 $T$ 的 $C_T(h^2+\eta_h/h)$。四阶合法格式把局部 $h^3$ 换成 $h^5$，才得到 $C_T(h^4+\eta_h/h)$。本轮残差注入和高维网格细化均实际检查了这类趋势。接触开闭、饱和、采样和非光滑事件可改变阶数，不能自动沿用光滑证明。

近似一形式若有 $e_B=K_af-\partial_tR_a-\nabla B_a$，则 $f_a-f=-K_a^{-1}e_B$，加入表示误差后

$$\|z_h-z\|\le C_T(h^p+\eta_h/h)+\kappa\varepsilon_B(e^{LT}-1)/L,\quad \|K_a^{-1}\|\le\kappa.\tag{A15}$$

图匹配误差是另一个量。若 $D\widetilde\chi^TK_0D\widetilde\chi=K+E$，内部映射保 $K_0$，则外部结构缺陷为 $E_--D\widetilde\Psi^TE_+D\widetilde\Psi$，加上内部求解误差。A15里的表示残差与这里的图匹配残差不能相互替代。本轮16自由度Moser试验给出了结构缺陷约 $6.68\times10^{-16}$ 而原场误差约0.1096的实测例子。

进一步连接机器人时，还要加入ROM截断、学习、流体闭合、实际磁场、观测及采样误差，并使所有范数、时间区间和状态域一致。本轮尚未把这些有限试验误差提升为整个三维血管模型的统一误差界。下面保留全部可复现计算及其条件。
