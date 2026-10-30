# 融合稿的理论接入、实现补齐与独立修正

对象固定为 stage5 的 12 配置自由度、24 维正则相空间 Kirchhoff ROM。几何质量、SO(3) 材料标架、固定偏置能量和完整线圈力均由现有模型求值；这里不重建一个双模态替代品。融合稿来源为新增 ZIP 的 `english/chinese/sections/{structure,supp_general_birkhoff,supp_structure}.tex`，逐公式锚点见 `annotations/theory.json`。本文件补齐可执行连接和误差责任；不声称以下条件性局部结论给出血流、接触、FSI 或 KAM 的全域结论。

## 1. 直接继承的完整 A/B 链，不重复发明

原1025 OMML `m0377–m0391`（p0867–p0879）与末附 p1179–p1206 对应 Theorem A；`m0399`（p0888）和 `m0565`（p1213）分别是错位和已修正的 B 递推。直接检查原生 XML 的 `m:sSubSup/m:sup` 与 `m:f/m:den`：前者左侧是 `(k)`、分母 `(k+1)!`，后者左侧已经是 `(k+1)`。不能把错误归因于纯文本提取，更不能删除原稿末附已正确的推导。

融合稿 `structure.tex:66–76` 与 `supp_general_birkhoff.tex:111–151` 正确要求端点二形式匹配、横截性与局部梯度。其 Theorem B 部分引用 Feng–Qin 递推并给中点实例；stage5 已在 `proofs/corrected_mathematics.md:153–298` 更完整地给出下列论证，应原样继承：

- 固定时间端点适配 `E* d(hatw·dw)=Ω_t−Ω_s`。流图像上左式为零；若 `T=CM+D` 可逆，则 w 为局部坐标。闭一形式在星形邻域有势，`N=(AM+B)T⁻¹=Nᵀ`。不要求 N 可逆；恒等映射恰有 N=0。
- 初始投影可逆时，先反解对角端点，得到 c0。初始势为 `φ0(w)=∫₀¹ c0(w*+r(w−w*))·(w−w*)dr`，固定 `φ0(w*)=0`。任意端点变换不一定 c0=0。
- 固定 w 时间偏导必须为 `∂t g|w=(A−NC)f+α1,t−Nα2,t`，而不是沿移动 w 的全导数。所有量经联合端点逆评价。
- 对含阶乘的普通时间幂系数，`c_(r+1)=[τ^r]Ψ(Στ^j c_j,w,Στ^j Dc_j,s+τ;s)/(r+1)`；特别 c2 包括 `Ψ_N[Dc1]/2`。解析流、端点逆及横截共同复域才保证实际收敛级数。有限可微性只能支持有限 Taylor 余项。
- 对中央规范 `hatw=J(y+−y−),w=(y++y−)/2`，`φ_t=−H(w−J∇φ/2,t)`；逐幂得到实际可算的标量递推。截断保持梯度性，端点重构需单独非奇异条件；误差阶还需共同域余项和一步稳定界。

`stage5/program/corrected_identities.py:171–292` 实现端点矩阵、联合逆、径向初始势、横截、固定w右端和生成递推。`stage5/tests/test_corrected_identities.py` 已覆盖零 N、有非零初始势、时变生成函数、非可分 Central4 及错误阻尼梯度。融合稿没有推翻这些正确修正。本轮直接复用，不新增一套容易漂移的 A/B 算法。

## 2. 将融合稿的 B=H 规范真正计算到同一个三维场

取 stage5 已实现的有源规范

\[
a'=a_0+b^{[r]},\quad B'=H+b^{[r]}\cdot f,\quad
K=(Da')^T-Da',\quad f_a=K^{-1}(\nabla B'+a'_t).
\]

这里 `b^[r]` 可以是有明确误差的空间缓存，而 `H,f` 仍为原几何 ROM。为对应融合稿 `supp_general_birkhoff.tex:41–47` 的物理 Hamiltonian 标量规范，在固定 z（不是沿未知物理轨道）令

\[
\sigma(z,t)=\int_0^t[B'(z,s)-H(z,s)]ds,
\quad a_H=a'+\nabla\sigma,\quad B_H=B'-\sigma_t=H.
\tag{G1}
\]

对本轮自治 H,f 和 `b^[r]=Σ_(k=1)^r t^k b_k(z)`，可直接算

\[
\sigma=\sum_{k=1}^r\frac{t^{k+1}}{k+1}b_k(z)\cdot f(z).
\tag{G2}
\]

这是真实可计算多项式积分，不用精确相流。`fusion_theory.PhysicalHamiltonianGauge` 直接加载 stage5 有来源指纹的高阶缓存，保留 Df、变质量项和完整线圈力。

**证明。** Hessian 对称给 `K_H=K`，时间/空间微分交换给 `∇B_H+∂t a_H=∇B'+∂t a'`，故同一个 f_a、同一个表示残差 `e_B=Kf−∇B'−a'_t` 完全不变。代码不人为对称化原始 Hessian；另用中心差分验证 σ 的时间导数和空间方向导数。

**关键限制。** 仅把 B' 标签改成 H、却不加 `∇σ`，会改变场；新增测试给出非零差。G1 也不强迫 `Hdot=0`，因为

\[
\dot H=\nabla H^Tf_a=(Kf_a-a_{H,t})^Tf_a=-a_{H,t}^Tf_a.
\]

对真实全线圈共点反馈，原场仍有 `Hdot=−κ||G_IᵀH_P||²<0`。本轮保存规范变换前后同一原场表示误差及非零负功率，防止用 B=H 把耗散场包装成自治保守系统。G2 的实现只接受本轮明确的自治分支；非自治 κ(t) 由 `nonautonomous_transport.py` 的卷积递推另做，不能静默套 G2。

## 3. 变分形式自伴性的正确、可计算含义

融合稿 `supp_general_birkhoff.tex:29–38` 所说自伴，是 Euler–Lagrange 微分算子的线性化形式自伴，不是物理 Jacobian `Df` 对称。设

\[
E_i=K_{ij}\dot z_j-b_i,\quad b=\nabla B+a_t,\qquad
\ell_E=K\frac d{dt}+C,quad
C_{ij}=\partial_jK_{ik}\dot z_k-\partial_jb_i.
\]

固定端点变分和积分分部给（K 反对称）

\[
\ell_E^*=K\frac d{dt}+\dot K+C^T,
\quad \dot K=K_t+DK[\dot z].
\]

所以形式自伴的零阶条件为

\[
C-C^T-\dot K=0.\tag{V1}
\]

空间闭性给 `∂jKik−∂iKjk=∂kKij`；时间相容 `K_t=Dbᵀ−Db` 给剩余项消失。因此 V1 在任意速度（off-shell）成立，不必代入物理解。新增独立 SymPy 反例取 `a=(exp(t)p+qp²/10,q²/5),B=(q²+p²)/2`，V1 恒等零而 Df 不对称。

在实际24D缓存上，本轮使用真实 `Df_a`，令 `Db=DK[f_a]+K Df_a`，任取独立速度检验 V1；再把同一近似K配给原 f，记录其非零缺陷。后一值反映原场的时间相容误差，不应通过对称化或改变标签抹去。

## 4. 将融合稿图误差式补成实际程序可核验的恒等式

融合稿 `supp_general_birkhoff.tex:209–215` 的图缺陷式针对精确内部辛映射、精确链式法则。该理想假设下公式正确，但实际数值 Moser、隐式求解和逆图另有缺陷。令 `T±` 是已计算端点图导数，A 是内部图映射导数，D 是独立组装的物理映射导数，定义

\[
E_\pm=T_\pm^TK_0T_\pm-K_\pm,
\quad\Delta=A^TK_0A-K_0,
\quad C=T_+D-AT_-.
\]

记 `B=AT_-`（此处只是矩阵，勿与 Birkhoff 标量混淆）。无需任意矩阵可逆即可得到

\[
\begin{aligned}
D^TK_+D-K_-={}&E_--D^TE_+D+T_-^T\Delta T_-\\
 &+B^TK_0C+C^TK_0B+C^TK_0C.
\end{aligned}\tag{D1}
\]

**证明。** 用 `K+=T+ᵀK0T+−E+` 展开，再代入 `T+D=B+C`；B 二次项等于 `T-ᵀ(K0+Δ)T-`，减 K− 后即 D1。理想 C=Δ=0 时严格恢复融合稿原式。一般数值程序不能删掉后两组项。

`chart_defect_decomposition` 实现完整 D1；独立随机矩阵测试故意保留内部和链式误差，验证只用端点缺陷确实不够。真实 ROM 测试复用 stage5 已存四步轨迹的第一步，重新求 Moser 图/逆图/二阶和时间敏感度、真实 f_a Jacobian，构造 `A=(I−hDg/2)⁻¹(I+hDg/2)` 与 `D=Dρ_+ A Dχ_-`。报告各项及等式余差。它是**新导数与缺陷计算、复用旧轨迹**，不是本轮重新积分了该完整轨迹，也不是浮点迭代程序 exact-symplectic 的证明。

## 5. 原（30）—（36）、Central4 与收敛：继续使用已正确的实现

原30/31的块矩阵和联合逆在 `corrected_mathematics.md:302–323`；原32固定初端导数在325–338；原35完整变质量中点在340–351；原36非交换左解在353–367。原OMML位置分别为 `m0400,m0408,m0417,m0427,m0429,m0434,m0442`，重复36为 `m0470,m0570`。正则/合法图端点生成关系和普通耗散中点不是同一结论。

融合稿 `struct:central4`、`ss:central-taylor`、`ss:central-correction`、`ss:primitive` 在 stage5 `proofs/integrators_full_coil.md:63–104` 完整保留：

\[
S_h=hH+\frac{h^3}{24}(J\nabla H)^TH''(J\nabla H),\quad
\Psi_h^*\lambda-\lambda=d(\bar p\cdot\delta q-S_h).
\]

H 必须是实际固定电流自治 Hamiltonian，全混合导数不能换成旧单特征磁势公式。stage5 直接调用 stage3 正确 Central4 程序，输入 full-coil H；本轮不另造替代算法。普通共点阻尼中点并不因此四阶或辛。固定时间误差界必须同时保留模型/表示误差、图误差、积分截断与每步代数残差累积 `η/h`；接触切换、限幅和记忆状态另需混合系统分析。

旧管图“闭即恰当”的问题已由 stage5 `corrected_mathematics.md:369–406` 修正为 `F*λ=(I+I0)·dθ+dS`。融合稿 `supp_structure.tex:142` 是关于原点的标准极坐标原函数，周期修正项明确，不能误判成同一个旧错误。合法中央映射的 exact primitive 也不应因旧管图措辞问题被删除。
