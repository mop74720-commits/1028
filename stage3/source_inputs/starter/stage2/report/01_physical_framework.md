# 5 三维多物理场模型及其能量接口

本节给出继续写作和实现的统一数学框架。F系列是本报告的新编号，不替换1025的原号。已经运行的闭合近似与完整目标方程在实验章节逐项对应。Cosserat的几何、转动自由度和离散依据Gazzola等2018；磁性材料和远端磁段参数依据Tong等2025的对应实例，使用范围另作限定。[R1，R2]

## 5.1 参考构形与三维杆方程

用材料坐标 $s\in[0,L]$ 标记截面，中心线 $r(s,t)$，截面姿态 $R(s,t)\in\mathrm{SO}(3)$。$R$ 把体坐标映射到空间坐标；帽算子满足 $\widehat a\,b=a\times b$。定义

$$\nu=R^T r_s,\qquad \kappa=(R^TR_s)^\vee,\qquad \Omega=(R^TR_t)^\vee,\qquad v=r_t.\tag{F1}$$

因而 $r_s=R\nu$、$R_s=R\widehat\kappa$、$R_t=R\widehat\Omega$。应变相容关系由混合偏导直接给出

$$\nu_t=R^Tv_s-\Omega\times\nu,\qquad \kappa_t=\Omega_s+\kappa\times\Omega.\tag{F2}$$

每单位参考长度的质量 $\mu_r$、体坐标角惯量 $J_r$、内力 $n$ 和内矩 $m$ 给出

$$\mu_r r_{tt}=n_s+f_m+f_f+f_c+f_g,\tag{F3}$$

$$J_r\dot\Omega+\Omega\times(J_r\Omega)=R^T(m_s+r_s\times n+\ell_m+\ell_f+\ell_c).\tag{F4}$$

这里 $J_r$ 若与形变或时间有关，左侧应改为体角动量的完整物质导数，不能遗漏其变化。F3—F4采用相同参考长度测度；若水动力以当前长度定义，应乘伸长因子 $e=|r_s|$。这也解释了为什么不能把一份每单位体积的Maxwell体力直接加到每单位长度的杆方程。

本构从能量出发：

$$W=\tfrac12(\nu-\nu_0)^TC_\nu(\nu-\nu_0)+\tfrac12(\kappa-\kappa_0)^TC_\kappa(\kappa-\kappa_0),\tag{F5}$$

$$n=R\partial_\nu W,\qquad m=R\partial_\kappa W.\tag{F6}$$

圆截面可取 $C_\nu=\operatorname{diag}(k_sGA,k_sGA,EA)$，$C_\kappa=\operatorname{diag}(EI,EI,GJ_t)$，$J_t=2I$；不能一般地把扭转刚度写为 $EI_3$。Kirchhoff层施加 $\nu=e_3$，内力成为约束乘子；它保留三维弯曲和扭转。Cosserat层则允许剪切与伸长。本轮二者分别实现，没有把 $R$ 的九个矩阵元素当成九个无约束坐标。

夹持边界应规定 $r(0,t)=r_b(t)$、$R(0,t)=R_b(t)$；自由端或附加磁芯端应由边界虚功给出 $n(L)$、$m(L)$ 与端部惯性、外力、外矩的平衡。本轮数值采用固定基座和自由端，磁矩分布在远端5 mm，没有把远端段同时当成另一个重复计数的点偶极。推进／抽出和运动基座是后续独立边界任务。

## 5.2 磁载荷从同一个能量导出

在磁体周围取闭合面，空气／非磁背景下的Maxwell应力为

$$T_M=\mu_0^{-1}(BB^T-\tfrac12|B|^2I),\quad F=\int_{\partial\mathcal V}T_Mn\,dA,\quad \tau=\int_{\partial\mathcal V}(x-x_c)\times(T_Mn)\,dA.\tag{F7}$$

该公式是总力和总矩，不能无说明地换成截面线积分。若外场尺度大于磁性截面且硬磁化可视为给定，设每单位参考长度体磁矩 $\mu_b(s)$、空间磁矩 $\mu=R\mu_b$，磁势为

$$V_m=-\int_0^L\mu(s)^TB(r(s),i,t)\,ds.\tag{F8}$$

对位置和空间转角分别取虚变分，$\delta\mu=\delta\theta\times\mu$，得到

$$f_m=(\nabla B)^T\mu,\qquad \ell_m=\mu\times B.\tag{F9}$$

该推导同时固定力、矩、符号及功率。磁矩随姿态旋转的贡献已经由力矩承担；求位置梯度时应固定姿态，不能重复加入姿态导数。若材料存在诱导磁化、饱和、磁滞或显著退磁场，则F8须替换为相应本构自由能，不能仅修改一个磁矩常数。

本轮局部无电流场采用

$$B(x)=b+G(x-x_0),\qquad G=G^T,\qquad \operatorname{tr}G=0,\tag{F10}$$

输入顺序为 $(B_x,B_y,B_z,G_{xx},G_{yy},G_{xy},G_{xz},G_{yz})$。无旋和无散约束留下 $3+5$ 个局部自由分量，并不提供八个任意独立的广义力。对离散坐标 $q$，写磁通特征 $\phi(q)\in\mathbb R^8$，则

$$V_m(q,u)=-\phi(q)^Tu,\qquad Q_m=G_m(q)u,\qquad G_m=(D_q\phi)^T,\quad P_m=\dot q^TG_mu.\tag{F11}$$

任何理想 $U$ 必须经过实际端口映射。最小二乘分配留下的误差 $r_u=G_m u-U$ 明确进入闭环误差预算；不足秩时不能称作精确磁实现。本轮12自由度ROM的参考分配约有18.5%的加权广义力残差，后续真实杆仿真采用受限后的实际磁输入。

进一步，线圈产生的场应由 $B(x,i)=\sum_a i_a b_a(x)$ 决定。本轮建立12个空气芯圆线圈的Biot–Savart模型，计算了 $8\times12$ 局部场—电流矩阵、限流和限电流变化率分配；尺寸和匝数均是明确工程选值。该模型证明了一个可运行的电磁输入接口，不构成实物标定。真实线圈上的电感、互感、电阻、温升及驱动电压上限仍需参数。

如需把驱动电路计入总能量，使用磁链 $\lambda_c$ 而不是把电流当独立守恒状态：

$$\lambda_c=L_ci+\Phi(q),\quad v_{\rm drive}=L_c\dot i+R_ci+(D_q\Phi)\dot q,\tag{F12}$$

$$E_c=\tfrac12(\lambda_c-\Phi)^TL_c^{-1}(\lambda_c-\Phi).$$

于是 $-\partial_q E_c$ 给出相同的磁广义力，电端口功率为 $i^T v_{\rm drive}$，电阻热为 $i^T R_c i$。这是可扩展总能量系统的接口；本轮线圈分配尚未积分F12。

## 5.3 完整血流目标与已经运行的闭合层

完整目标是在移动血管—导管流域 $\Omega_f(t)$ 上求不可压缩流动：

$$\rho_f(\partial_tu+(u-w_{\rm ALE})\cdot\nabla u)=\nabla\cdot\sigma_f+\rho_fg_{\rm eff},\qquad \nabla\cdot u=0,\tag{F13}$$

其中 $\sigma_f=-p_f I+2\eta D(u)$，或使用有来源、经过参数识别的非牛顿应力。F13中的时间导数是在ALE坐标下的导数；若在固定空间坐标下写，则对流项为 $u\cdot\nabla u$。导管和壁表面满足速度连续及牵引反作用。全耦合时杆表面牵引积分已经给出 $f_f$、$\ell_f$，不再叠加另一份Morison拖曳。

入口给定实测或文献支持的周期流量／压力波形；出口可接RCR模型，静脉／动脉的顺应性、压力和生理调节分别标定。微重力不能通过把常数 $g$ 置零同时“推导”出新的入口波形。当前没有空间站个体数据，故没有虚构心排量、血压或血管尺寸的微重力修正率。

本轮基准采用规定的曲管脉动速度剖面：

$$u_f(x,t)=U_0[1+a\sin(2\pi f_bt)]\,[1-(d(x)/R_v)^2]_+\,t_v(x).\tag{F14}$$

曲管中直接规定的F14并不是一个已求解的Navier–Stokes无散解；它是低成本单向载荷闭合。为检查瞬时抛物线近似，本轮还实际运行了相同流量下的Womersley分支。令 $\omega_b=2\pi f_b$、$\alpha=R_v\sqrt{\rho_f\omega_b/\eta}$、$\lambda^2=-i\alpha^2$，定义

$$F(r)=1-\frac{J_0(\lambda r/R_v)}{J_0(\lambda)},\qquad \overline F=1-\frac{2J_1(\lambda)}{\lambda J_0(\lambda)},\tag{F14a}$$

$$u_z(r,t)=2\overline U[1-(r/R_v)^2]+\operatorname{Re}\left[-iU_1\frac{F(r)}{\overline F}e^{i\omega_bt}\right].\tag{F14b}$$

它对应平均速度 $\overline U+U_1\sin(\omega_b t)$，实际取 $\overline U=0.02\,\mathrm{m/s}$、$U_1=0.009\,\mathrm{m/s}$；$\alpha$ 约4.533。$J_0$、$J_1$ 是第一类Bessel函数。直刚管解满足无滑移和给定谐波通量，其4097点径向表的最大通量积分误差约 $5.13\times10^{-14}\,\mathrm{m^3/s}$，独立有限差分的直管动量方程相对残差约 $3.28\times10^{-7}$。将它沿弯管切向映射仍是局部单向近似；未计算二次流或双向FSI。[R9]

两种流场共用相对速度 $w=u_f-v$、$P_\parallel=tt^T$、$P_\perp=I-tt^T$，每单位当前长度阻力为

$$f_d=c_\perp P_\perp w+c_\parallel P_\parallel w+\rho_fC_Da\,|P_\perp w|P_\perp w.\tag{F15}$$

第三项等于 $\tfrac12\rho_f C_D(2a)|w_\perp|w_\perp$，投影宽度 $2a$ 没有遗漏。细长体线性阻力系数采用 $c_\perp=4\pi\eta/[\log(2L/a)+1/2]$、$c_\parallel=2\pi\eta/[\log(2L/a)-1/2]$。狭窄血管中的壁面放大、水动力屏蔽、有限 $\mathrm{Re}$ 修正仍需另校准，不能宣称细长体无限流体公式在贴壁时自动精确。

移动体Morison惯性项若启用，应分开压力梯度与附加质量，例如 $\rho_f A a_f+m_a(a_f-r_{tt})$，其中 $a_f=\partial_tu_f+(u_f\cdot\nabla)u_f$。它会同时改变惯性、几何项和流体功率，不能只给质量矩阵加常数而遗漏相关项。本轮明确关闭附加质量；不存在用速度减加速度的量纲错误。转动黏性采用轴向自旋阻力 $-4\pi\eta a^2(\omega\cdot t)t$，并记录其功率。

F15对相对运动耗散：$w^Tf_d\ge0$；对机器人机械能，$f_d^Tv$ 可正可负。规定流动是能源端口，血流可以推动导管。将全部血流简单记为 $-C\dot q$ 并据此宣称机械能单调下降，既不符合F15，也不符合本轮程序。

## 5.4 壁面接触与摩擦

设法向间隙 $g=R_v-a-d$，穿透量 $\delta=[-g]_+$，$n$ 指向管壁。理想接触可写 $g\ge0$、$\lambda_n\ge0$、$g\lambda_n=0$ 及切向摩擦锥。实际运行采用连续罚能与耗散：

$$V_c=\int\frac{k_c}{r+1}\delta^{r+1}\,ds,\quad f_{c,e}=-k_c\delta^r n,\quad r=3/2,\tag{F16}$$

$$f_{c,d}=-c_n[ v_{\rm rel}\cdot n ]_+n-\mu_f\lambda_n\tanh(|v_\tau|/v_\epsilon)\,\frac{v_\tau}{|v_\tau|}.\tag{F17}$$

最后一项在零速取零；接触耗散只在 $\delta>0$ 的激活接触上施加。程序取每单位长度的阻尼系数及法向合力密度为

$$c_n=2\zeta\sqrt{\mu_r r k_c\delta^{r-1}},\qquad \lambda_n=k_c\delta^r+c_n[v_{\rm rel}\cdot n]_+.\tag{F17a}$$

它随 $\delta$ 趋零而消失。接触点速度包含 $v_c+\omega\times(a n)$ 减壁速度；对应接触矩为 $(a n)\times f_\tau$。忽略这一转动速度会使摩擦功率与转动方程不闭合。F16的 $k_c$ 按每单位长度定义，单位 $\mathrm{N}/\mathrm{m}^{5/2}$；两点Gauss积分后才是节点力。本轮的 $k_c$ 和 $\mu_f$ 属于工程罚模型参数，不宣称由弹性半空间的Hertz接触几何推得。

固定壁时，$f_{c,d}$ 及接触矩对总接触点运动的功率非正。若壁移动，壁端口须计入总功率。弹性力 $\delta_+^{3/2}$ 跨接触开闭仅 $C^1$；实际 $c_n$ 正比 $\delta_+^{1/4}$，其系数跨开闭也不满足通常的局部Lipschitz条件。因此完整接触场既不能直接放进解析KAM定理，也不能无条件沿用光滑向量场的全局阶数或Gronwall收敛证明。采用光滑近似须给出逼近误差、导数界和复域，不能仅用“正则化”替代证明。

## 5.5 微重力与生理边界

若在空间站随动参考系中描述，$g_{\rm eff}$ 包括重力与平台平移之差，以及科里奥利、离心、欧拉项；压力梯度造成的浮力不能重复加进两次。完整FSI由流体压力自然承担；当前规定流场层使用 $(\rho_r-\rho_f)A g_{\rm eff}$ 作为一次性的浸没有效重力。残余加速度和抖动的本轮数值是合成参数，不是空间站测量数据。

生理适配至少包括入口脉动、出口阻抗和顺应性、血管几何／壁本构、血液黏度或流变模型、体位与循环状态。它们属于边界和材料参数，不是把杆的重力项删去即可得到。当前固定血管壁、固定基座和无插入只是本轮可复算层的假设，后续三维目标继续包含这些物理扩展。

## 5.6 弱式与可验证的降阶

对F3—F4分别用平移虚位移 $\delta r$ 和体虚转角 $\eta$，内力虚功可写

$$\delta\nu=R^T\delta r_s-\eta\times\nu,\quad \delta\kappa=\eta_s+\kappa\times\eta,\tag{F18}$$

$$\delta\int W\,ds=\int(\partial_\nu W)^T\delta\nu+(\partial_\kappa W)^T\delta\kappa\,ds.$$

分部积分产生自然边界 $n\cdot\delta r+m\cdot\delta\theta$，给出与端部载荷一致的离散方程。降阶从构形嵌入 $r=r(q,s)$、$R=R(q,s)$ 出发，分别定义平移Jacobian $A_r=\partial_q r$、体角速度Jacobian $A_\Omega$，即 $r_t=A_r\dot q$、$\Omega=A_\Omega\dot q$。动能立即给出

$$M(q)=\int[\mu_rA_r^TA_r+A_\Omega^TJ_rA_\Omega]ds+M_{\rm tip}(q),\quad T=\tfrac12\dot q^TM(q)\dot q.\tag{F19}$$

这里 $J_r$ 仍表示F4中的截面角惯量，不与两个几何Jacobian混用。Euler–Lagrange方程为

$$M\ddot q+c_{\rm geo}(q,\dot q)+\nabla V=Q_{\rm nc},\quad (c_{\rm geo})_i=\sum_{jk}\tfrac12(\partial_jM_{ik}+\partial_kM_{ij}-\partial_iM_{jk})\dot q_j\dot q_k.\tag{F20}$$

令 $p=M\dot q$，不可遗漏的Hamiltonian和动量方程为

$$H=\tfrac12p^TM^{-1}p+V,\quad \dot q=H_p,\quad \dot p_i=-\tfrac12p^T(\partial_iM^{-1})p-\partial_iV+Q_{{\rm nc},i}.\tag{F21}$$

等价地，质量项为 $+\tfrac12\dot q^T(\partial_iM)\dot q$。这不是可忽略的高阶修饰，而是变质量能量守恒所需的项。移动基座嵌入还会产生 $T=\tfrac12\dot q^TM(q,t)\dot q+a(q,t)^T\dot q+c(q,t)$，因此 $p=M\dot q+a$、$H=\tfrac12(p-a)^TM^{-1}(p-a)+V-c$，显式时间功也须保留。

本轮12自由度模型在两个弯曲轴和一个扭转轴分别使用四个Legendre曲率系数，以 $\mathrm{SO}(3)$ 指数更新姿态，以几何Jacobian装配 $M(q)$，20／40／80空间积分进行独立对照。它是可验证的Kirchhoff分析层，不能当作已经收敛的完整Cosserat真值。有限差分中心速度和体角速度独立重算动能，与装配质量给出的结果相符至约 $4.8\times10^{-10}$ 相对误差；磁势的虚功检查也通过。完整杆与ROM采用相同材料、远端磁段和磁输入顺序，随后进行跨模型控制验证。

## 5.7 总功率作为共同验收量

机械能取平动动能、转动动能、杆应变能与罚接触势；磁载作为输入功计入，则

$$\dot E_{\rm mech}=P_m+P_f+P_{c,d}+P_g+P_b-P_{\rm structural\ loss}.\tag{F22}$$

若把 $V_m$ 也计入能量，则相应把机械磁功改写为外场显式变化功，不能两边重复计数。完整流固耦合时，把流体动能、壁能、出口电路式储能和必要的热能加入，界面牵引功成对抵消，只剩外部边界功和不可逆耗散。这个能量闭合是学习、降阶、数值离散和控制比较的共同核查量。
