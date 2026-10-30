# 使第一衔接成立的最少修改

不重写论文、不替换三维物理目标。原稿正确的变质量能量、Hamiltonian端口方程、功率式、复坐标辛形式及正则Birkhoff特例保留。以下修改仅对应 `CHNN → 明确的实际场 → Birkhoff`；不实施下一步生成函数。

## 1. 原12之后：固定一个物理对象与载荷拆分

**原位置**：`p0150–0171/m0097–0116`，Birkhoff回顾 `p0842/m0359`。

保留并统一为

\[
z=(Q,P)\in\mathbb R^{24},\quad
h_*(z)=\tfrac12P^T\mathsf M(Q)^{-1}P+v_{ideal}(Q),\quad
f_*=J\nabla_z h_*+(0,R_*),\quad
h_*'=h_{*,\tau}+h_{*,P}^TR_*.
\]

只把明显笔误 `Q'=h_Q`、梯度块倒序、`½pᵀMq` 改回原稿前面已经正确的式子。M(Q)每次在实际位形计算；不改变维数、材料、磁参数或消去几何惯性。原稿一般恢复力的势只在可积条件下存在，本轮直接复用已经由杆能量导出的V。

**应插入的一句话**：“本节固定已声明的保守磁偏置作为h的一部分；其余载荷作为R列出，避免同一磁作用在h与外力中重复计算；若换完整线圈磁势，模型对象和误差预算须同步改变。”

## 2. 原15—16：复数包装不替代真实耗散力

**原位置**：`p0287–0288/m0175–0176`，`p0338–0345/m0185–0192`。

保留 `z'=(J-D)∇h+F` 在其明确D、F下的含义。把 `G1=½pᵀCp ⇒R=−G1,p` 的一般断言改为已有Rayleigh关系：

\[
R=-\partial_v\mathcal D(Q,v)\big|_{v=h_P};\qquad
G(Q,P)=\mathcal D(Q,h_P),\quad
\nabla_PG=h_{PP}^T\mathcal D_v.
\]

只有h_PP可逆时才有 `R=−h_PP^{-T}∇_P G`。对机械二次动量能量退化为 `−M∇_P G`；若直接已知R，本桥不需要此反解。该修正已在S5 `corrected_mathematics.md` R6证明。

把实虚势“总能表示”改为有条件的特殊表示。正确原17约定下，若实G满足

\[
\xi'=-i\partial_{\bar\xi}(h+iG),
\quad Q'=h_P+G_Q,\quad P'=-h_Q+G_P,
\]

则对同一固定h和纯动量端口R，必须 `G_Q=0,G_P=R`。一维 `R(Q,P)=QP` 要求 `G_{PQ}=P` 又要求 `G_{QP}=0`，一般矛盾。原p0578要求Ptilde实值，故不能用任意复标量积分掩盖这个反例。

**应插入的一句话**：“本节不假定一般非保守载荷是某个实虚势的复梯度；CHNN学习实保守Hamiltonian，R独立保留。若学习R，其误差另计。”

## 3. 原17—21、24—28：一起修正坐标、导数与预测器

**原位置**：`p0350–0368/m0194–0206`，重复 `p0424/m0212,p0556/m0266,p0572/m0273`，损失 `p0591–0598`。

正则缩放以后，保持原17，统一

\[
\xi=(Q+iP)/\sqrt2,\qquad
\partial_{\bar\xi}=(\partial_Q+i\partial_P)/\sqrt2,\qquad
\xi'=-i h_{\bar\xi}+iR/\sqrt2.
\]

不保留“系数可调整”的任意性，不同时使用预测器barξ导数和损失ξ导数。原27/28的Cauchy–Riemann内容保留，仅补充它不要求实 `h(ξ,barξ)` 对ξ单独全纯。原后文未缩放 `z=x+iy` 的1/2导数保持，不机械替换。

现有冻结模型真正使用

\[
x=Dz,\quad D=\operatorname{diag}(\sqrt\nu,\sqrt\nu)/a,\ a=.08,
\quad\widehat h_\theta(z)=\tfrac12 a^2|Dz|^2+\mathcal N_\theta(Dz)\in\mathbb R,
\quad\nabla_z\widehat h=D\nabla_x\widehat h.
\]

`x`仅为训练归一化，通常不正则；若在x中写动力学，结构矩阵应为 `DJD`，不能仍用J。S5真实训练损失已经按正则梯度加权，本轮不重训。

原 `|Htilde_dot|²=2|Ptilde_dot|²` 改为 `2 Hdot²+2 Ptilde_dot²`；若采用实能量端口模型，应直接核验功率 `h'=h_P^TR+h_tau`，而非强制耗散机械能恒定。可选拟合损失使用同一 `f_theta=J∇hhat+(0,R_theta)`；本轮沿用S5冻结损失和权重，不因文稿修改训练目标。

## 4. 学习对象之后：补一段共同场和三种误差

**原位置**：在原 `p0583–0598` 的网络/预测器后、`p0793` 的Birkhoff入口前插入。

定义

\[
f_*=J\nabla h_*+(0,R_*),\quad
f_\theta=J\nabla\widehat h_\theta+(0,R_\theta),\quad
\delta f=f_\theta-f_*=J\nabla(\widehat h_\theta-h_*)+(0,R_\theta-R_*).
\]

同一R为本轮明确选择，不是对所有耗散模型的默认事实。例如若使用同一个物理阻尼律 `R_*=-C h_{*,P}`、`R_theta=-C hhat_P`，函数R通常不同，差值必须保留。本轮沿用既有合成光滑状态载荷，是代码接口基准，不称生理血流，也不由正系数推断其对任意h均负功。

本轮独立冻结网络检查已有实际反例：旧测试样本180的同一R对 `H_ideal` 功率约 `−1.10205e−4`，对 `hhat` 却约 `+1.20601e−4`；见 `results/network_power_witness.json`。这不破坏Birkhoff表示，但禁止把“对真实能量耗散”直接继承为“对学习能量耗散”。

若构造 `a_theta,B_theta`、`K_theta=(Da_theta)^T-Da_theta`，定义

\[
e_B=K_\theta f_\theta-\nabla B_\theta-\partial_\tau a_\theta,
\quad e_*:=K_\theta f_*-\nabla B_\theta-\partial_\tau a_\theta
=e_B-K_\theta\delta f.
\]

这是精确代数恒等式，符号与用户提出式C一致。若K非退化，表示场
`f_B=K^{-1}(∇B+a_tau)=f_theta−K^{-1}e_B`，从而

\[
\|f_B-f_*\|\le\|\delta f\|+\|K^{-1}\|\|e_B\|.
\]

时间积分误差仍是第三项，不并入e_B或学习误差。要给统一域/有限时间界，必须另有共同留域、Lipschitz、K逆和统一误差界；采样最大值只作诊断。这些是已有一般Birkhoff残差定理的直接代入，不新增KAM模块。

## 5. 原第31—32页Birkhoff内容：保留正确退化，替换不相容候选

**原位置**：`p0797/m0347,p0804/m0349` 和 `p0846–0851/m0362–0366`。

保守分支先用原稿本来正确的精确对

\[
a_0=(P,0),\quad K_0=-J,\quad B_\theta=\widehat h_\theta,
\quad K_0J\nabla\widehat h_\theta=\nabla\widehat h_\theta.
\]

它不要求训练误差为零，不要求h_PP正定，也不要求近似图。h_PP正定另决定机械Legendre反解/解释的合法域。

删去原 `F2=0,F1,p=1,B=H` 与一般含p耗散时间积分同时成立的断言。直接继承一般材料的局部输运

\[
\partial_\tau a+Da f_\theta+(Df_\theta)^Ta=0,
\quad a(0)=a_0,\quad B=a^Tf_\theta.
\]

在光滑局部可逆流域它给闭、非退化、时间相容K；相流只用于证明，算法用已有有限Lie系数，未知精确相流不作免费输入。

若复用S5有源规范，必须把机械专用 `ell=T−V` 改为**任意实可微Hamiltonian**都成立的

\[
\ell=P^T\widehat h_{\theta,P}-\widehat h_\theta,
\quad\mathcal L_{f_\theta}a_0=d\ell+(R,0).
\]

由 `a'=a0+b`、`b1=−(R,0)`、`b_(k+1)=−L_f b_k/(k+1)`、`B'=hhat+b·f` 得同一合法有源构造。齐次首系数必须取 `a1=−L_f a0=−∇ell−(R,0)`。旧 `transport_native.py` 中 `a1=∇[2H(Q,0)−H]−(R,0)` 只对P二次机械H成立，不能无条件用于完整复网络。这是本桥必须修复的程序适用条件；旧机械实现本身无需改动。

冻结网络在旧测试样本146的实测机械简式误差约0.198086，而一般式与 `−L_f a0` 的差约 `1.2e−15`；见 `results/network_checks.json`。这说明不是为了增加一般性而任意改写旧算法，而是完整网络确实不满足该机械简式前提。

有限系数对应的截断残差、闭性、K非退化域和对学得/真实场的不同相容性分别测量，不宣称有限输运多项式精确表示原场。

## 6. 本桥向下一步只交接条件

原A/B以一个已确定的Birkhoff相流为入口。本桥应交付明确的 `(f_theta,a_theta,B_theta,K_theta)` 或明确的近似表示场f_B、共同局部域和分离误差。下一桥仍需检查端点二形式匹配、初始/演化横截、局部生成梯度、固定生成坐标的时间PDE、解析展开域以及反向重构矩阵可逆。S5已有正确局部证明可直接引用；本轮不声称数值采样已经核验这些全部前提，不自动进入原30—36。
