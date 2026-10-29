# CHNN、正规形、连续／离散 KAM 的继承审查

结论：**有效的旧数学与第二阶段完整可训练复能量网络尚未充分进入第三阶段计算链。** 第三阶段如实保留了源码与限制，没有证据显示把单系数拟合冒称完整 CHNN；但“保存并引用”不能代替复用。旧 v10 的确定性学习误差界、完整混合四次读出、非可分 Central4、有限幅值连续环面、64 平面自由度提升和 S 路径，均应独立保留并接入最终论文。新的三维共振体系没有获得连续或离散 KAM 证书。

## 1. 本轮实际读取的对象及证据边界

原稿位置使用 `source_omml/original1025_indexed.json` 的全体 `w:p` 顺序，`p0350/m0194` 表示原段落与原生 OMML 对象。实际核对了下列数学对象的 XML 分数、共轭、上下标；六项关键原 XML 另存 `results/chnn_checks/original_formula_raw_omml.json`，并非只看纯文本。

| 层次 | 本轮读取位置 | 可以确认／不能确认 |
|---|---|---|
| 原始 1025 | `推理草稿5月1025.docx`；p0337–0367、p0424–0520、p0533–0598、p0639–0790、p1074–1078 | 原始复坐标、耗散解码、学习损失、作用角及 KAM 主线；其错误应修正而非删去该路线 |
| 固定 GitHub v10 | 本轮从 `82519542dd057e8fbd6d6879ef33217761e8cbbb` 逐文件取得 `external_v10/sections/{core_derivation,core_analysis,core_kam,complex_theorem_note,theorem_bridge,unified_kam,integral_comsol_to_kam,full_fe_kam_control,s_path,measure_proof,measure_persistence}.tex` 与 `supplement.tex` 等 | 直接审阅完整相关证明及表格；`external_v10/manifest.json` 保存 URL、大小、SHA。不是把 stage2 笔记当旧原文。旧 S1 科学代码、MAT、NPZ、Arb 候选仍缺，不宣称本轮重跑其证书 |
| 英／中文整合包 | `stage3/source_inputs/v10/v10_framework_20261028/{english,chinese}/sections/{structure,kam,supp_structure}.tex` | 两种正文与补充中的公式和限制一致；这个参数已更新的两模态稿不是原 GitHub 冻结对象，也不是新的完整三维论文 |
| 第二阶段 | `stage3/source_inputs/starter/stage2/program/learning/`；`notes/{learning_independent_review,learning_confirmation,learning_spd,v10_baseline}.md`；`report/02_learning_metriplectic.md`、`report/stage2_complete.md` | 完整融合 Markdown 报告**存在且已读取相关章节**；不能写“第二阶段完整报告缺失”。历史权重/数据/独立结果文件缺失，只有源码与报告不能独立复算数值 |
| 第三阶段 | `stage3/program/{control_learning,control_experiments,rom_bridge}.py`；`stage3/notes/{materials_and_scope,theory,control,integrators}.md` | 真实三维变质量 ROM、磁端口与保守 Central4 的新增连接；完整 CHNN/KAM 未进入新运行。没有新的完整正式三维论文，现状是代码、结果和数学笔记 |

这次审查不是旧引用文献全部定理的重新证明。已直接检查项目中实际使用的命题、证明、假设和来源版本；旧 S1 的高精度逐项算术以及所引外部 KAM 定理的全篇常数证明未在本轮重新执行。下文分别标明“推导成立”“条件性结果”“历史证据”“新运行”“未完成”。

## 2. 原稿复坐标路线：必须恢复，同时整组修正

### 2.1 原（17）／（18）的归一化不一致

原 p0350/m0194 的原生分式是

\[
\xi=(q+ip)/\sqrt2,\quad\bar\xi=(q-ip)/\sqrt2.
\]

p0357/m0200 的逆变换正确。其链式法则应为

\[
\partial_\xi=(\partial_q-i\partial_p)/\sqrt2,\qquad
\partial_{\bar\xi}=(\partial_q+i\partial_p)/\sqrt2,
\quad \{\xi_j,\bar\xi_k\}=-i\delta_{jk},\quad
\dot\xi=-iH_{\bar\xi}+if/\sqrt2.
\]

原 p0351/m0195、p0364/m0204 的 `m:f` 明写 **1/2**；p0545、p0548 等又使用 `−√2 i H_barξ`。这两处不能各自保留。后文 p0779–0789 使用未缩放 `z=x+iy` 时的 `1/2` 属于另一套合法约定，不应一概删改。

本轮新测试取 `H=(q²+p²)/2,q=.7,p=−.4`：正确式误差为 0；原（18）的导数与实际链式法则差 `0.1669748251`。**两个错误因子在这个线性例子相乘可抵消至 `1.24e−16`**，所以不能据此说原所有标量轨迹都错；反而说明只修正导数却保留 `√2` 会引入 `0.2361380623` 的场误差。修正必须贯穿作用角、损失及预测器。

原 p0491–0505 采用 `ξ=√I exp(iθ)`，其约定下保守 `I'=0, θ'=−H_I`；旧 v10 则采用 `Y=−√(2I)sin φ`，对应 `φ'=H_I`。角的定向可以改变符号，不能任意改变频率的 `√2` 因子。原 p0505 的标量 `ω'(I)≠0` 也不能直接充当 12 自由度的 `det D_Iω≠0`。

旧 GitHub 已正确修复这组关系：`external_v10/sections/core_derivation.tex:69–134`；整合包 `english/sections/supp_structure.tex:247–265`（中文同标签 `ss:complex-force`）。这些完整公式应作为最终稿共用约定，而非只留下“使用复坐标”。

### 2.2 耗散、虚部和损失不是普通 Hamiltonian 的等价包装

原 p0342 用 `G1=.5 pᵀCp` 推出所需阻尼，一般变质量系统不成立：若 `H=p²/(2m)` 且物理阻力 `−c H_p=−cp/m`，`−∂p(.5cp²)=−cp` 只有特殊尺度才一致；若 `C` 依赖速度，还有其偏导项。本轮最小反例 `m=2,c=.3,p=.4` 给物理力−.06、原式−.12，绝对差.06。可靠解码是先定义 `D(q,v)=.5vᵀC(q)v`，先对 `v` 求导再代入 `v=H_p`。见旧 `core_derivation.tex:104–134`；不要用虚部读出名称代替功率恒等式。

原 p0571–0578 把一般向量扰动积分为一个实标量势，需要混合偏导／实值相容条件，不能默认存在。任意学得的非保守力或磁分配残差，不自动是某个 Hamiltonian 的梯度。原 p0591/m0284 对实 `H,P` 的正确展开应为

\[
|d[\sqrt2(H+iP)]/dt|^2=2\dot H^2+2\dot P^2.
\]

原式删去第一项，需另有 `dot H=0` 假设；与前述受迫耗散功率不一致。本轮阻尼振子取 `γ=.3,p=−.4` 得 `dot H=−.048`，被遗漏项为 `0.004608`。p0593/m0286 的 HNN 损失用 `∂ξ`，p0598/m0289 预测器却用 `∂barξ`，应统一为上述正确解码；同一规范振子的真实轨迹给错误导数损失.32、正确损失0。能量／辛损失很小也不保证精确守恒、Jacobi 恒等式或辛性；应从结构参数化和实际闭环推导。

## 3. “完整 CHNN”必须区分三类已存在对象

### 3.1 固定旧 v10：完整四次函数类，固定特征的可训练读出

固定原文 `external_v10/sections/core_analysis.tex:70–140`、`supplement.tex:65–99`、`complex_theorem_note.tex:48–49` 自己明确：实验是线性最小二乘拟合读出。它不是仅学一个实磁势系数，也不是已训练深层复隐藏权重的证明。

\[
h_\eta=h_2+a\,g(d^TX)+m_4(X,Y)^TUc,
\quad g(s)=1-\cos s-s^2/2,
\quad U\in\mathbb R^{35\times34}.
\]

四变量全部 35 个四次方向包含混合位置—动量项；余弦尾项完整保留。已知二次先验分支有 35 个有效实参数，无先验再学 10 个二次项，共 45。复单项式及共轭确实实现同一实函数类。原 GR/GC、BR/BC 用相同数据、正则、函数类，三个种子实／复差小于参考积分分辨率，不能改写为“复表示更优”。这一基准的容量、完整方向及确定性误差证书非常有价值。

原复杂梯度下降命题 `complex_theorem_note.tex:9–47` 的实化证明成立：`G=2∂barw L`，`κ=Reρ−L|ρ|²/2>0` 给下降与梯度范数趋零；不保证全局最优、参数收敛，也不是实验的最小二乘算法。第二阶段 Adam 训练不满足这个固定梯度步公式，不能用此命题直接给其收敛保证。

整合包 `english/sections/structure.tex:165–187` 将主实验缩成一个势能系数；`supp_structure.tex:356–394` 仍保留 35 参数公式及动量项的 Legendre 接口，但明写“未在新参数重训”。这是**公式保存、主计算缩窄**。要恢复它作为独立回归，并扩展到新三维数据时重新给激励/Gram/类误差界；不要求把原两模态系数硬迁移到三维。

### 3.2 第二阶段：真正训练全部复隐藏层，但没有完成所有结构要求

`stage3/source_inputs/starter/stage2/program/learning/run_learning.py:15–43,135–169` 是实际 `complex128` 三层读出（两个宽48隐藏层），共3552复参数／7104实参数；同时输入 `ξ,barξ`，split tanh，三次门控，`P→−P` 平均；在真实 24 维 ROM 能量及导数标签上训练。`run_learning_initial.py:15–34` 是此前 meromorphic tanh 失败架构，必须保留。

这不是“只把数组转为复数”。本轮直接调用现有类，在真实 ROM 的16个新标签上运行5次 Adam更新，所有 `l1.weight,l2.weight,l2.bias,l3.weight` 实／虚部更新非零，原点残差 Hessian 与动量偶性缺陷均为0；结果见 `results/chnn_checks/checks.json`。此项只验证源码确可训练，**不等于恢复旧冻结训练或科学性能实验**。对 `run_learning.py` 与 `run_learning_trained_source.py` 的 AST 复核仅 `main` 不同，模型和训练函数相同，支持来源防护补丁没有改写旧训练定义。

实际激活 `σ(z)=tanh(Re z)+i tanh(Im z)` 不对单个 `z` 全纯。本轮在 `.2+.9i` 计算 Cauchy–Riemann 缺陷 `0.4741256`。它在实输入域实解析，能以独立 `z,w` 延拓为

\[
\sigma^{\mathbb C}(z,w)=\tanh((z+w)/2)
+i\tanh((z-w)/(2i)).
\]

因此“非单变量全纯”**不是**否定解析 KAM 的充分理由；需要整个网络在某个固定复域避开各层 tanh 极点，并界定函数／导数范数。第二阶段没有这样的域与误差证书。实输出的复延拓也必须冻结共轭系数，不能在扩展复域继续调用 `.real` 或取实际共轭运算。旧整合 `ss:conjugate-extension` 已给合法方法，应继承。

历史报告 `report/02_learning_metriplectic.md:23–68` 与 `notes/learning_confirmation.md:35–57` 保存局部确认的正则向量场误差约1.815%–1.950%，压力域约5.444%–6.167%，以及初次 tanh 域外失败、非受限 H_PP 负曲率反例。**这些本轮只可称历史结果**：必要 NPZ/PT 未在轻量包，不能把本轮5步架构测试当其复证。48特征基线与7104实参数的网络容量不同，不能据此隔离“复数表示优势”；公平对照应增加相同函数类／参数预算的实网络及多种子协议。

### 3.3 SPD 机械网络：结构真修复，精度负结果必须保留

实际 `train_spd_complex.py:30–96` 有13440实参数。其动量只二次出现，`L` 下三角且 `L_ii=exp(raw_ii)>0`，`raw(Q)=head(h(Q)−h(0))`，所以 `L(0)=I`。在规范变量中

\[
h_\theta=\tfrac12a^2 x_P^TL(x_Q)L(x_Q)^Tx_P
+\tfrac12a^2|x_Q|^2+V_{res}(x_Q),\qquad
(h_\theta)_{PP}=D_\nu LL^TD_\nu,\quad D_\nu=\operatorname{diag}\sqrt\nu.
\]

任意有限实输入、有限实输出的精确算术下，`vᵀH_PP v=|LᵀDνv|²>0`；因此固定 `Q` 的动量—速度映射是线性双射，Legendre 反解合法。它没有证明全域统一最小特征值、物理质量误差或浮点良态性。本轮对新初始化的同类 H_PP 解析／自动微分相对误差 `1.63e−16`，最小特征值 `.9839905`，条件数 `886.895`；自回代误差 `5.83e−18` 仅检验同一学得矩阵的求解。

历史 `notes/learning_spd.md:174–210,225–255` 则显示压力域 test/OOD 质量 Hessian 相对误差320%/372%，条件数约 `4.61e10/1.13e12`；新确认正则场误差约98.88%（主域约6.86%）。这些是**正确结构与不佳近似并存**的负结果。不能抹去它们，也不能把“SPD”单独写成“学习物理质量正确”。由于旧权重缺，本轮没有重新宣称验证其具体数值。

### 3.4 正则归一化不能与训练缩放混同

实际 `rod_rom.py:55–66,113–145` 保留 `M(q)`，`S_q^TS_p=(E0/ω0)I` 配合时间能量缩放给规范 Hamilton 方程。训练 `x=Dz`，`D=diag(√ν,√ν)/a` 是另一组非辛缩放：

\[
\nabla_zh=D\nabla_xh,\qquad x'=DJD\nabla_xh.
\]

`evaluate_models.py:29–48` 已正确转换。只引用 `run_learning.scores` 的 `gradient_relative_l2` 会丢失它是 `x` 梯度这一事实。本轮实际 `||DJD−J||=226107.9022`；把 `x` 直接当正则变量会显著改变动力学，不是记号差异。最终论文应完整保留第二阶段已经做好的修正。

## 4. 学习误差进入 KAM：旧有效证明有两条，不能丢失

### 4.1 确定性有限特征／积分缺陷路线

旧 `theorem_bridge.tex:180–264`、`core_kam.tex:22–68`、`integral_comsol_to_kam.tex:14–128` 的核心证明可直接核验：在同一归一化的观测范数下，`e=y−Dη*`，`G=DᵀD/Nobs ≽ λI`，故

\[
\|\hat\eta-\eta_*\|_2\le (r+\epsilon)/\sqrt\lambda,
\quad
\|\hat h-h_*\|_{\mathcal U}\le B_F(\mathcal U)(r+\epsilon)/\sqrt\lambda
+\|R_{out}\|_{\mathcal U}+\delta_{export}.
\]

证明是最小奇异值、三角不等式和 Cauchy–Schwarz；不要求独立采样或最小二乘最优。需要额外独立控制观测／物理缺陷与模型类误差；不能由拟合残差自己推出它们。积分识别的曲线端点匹配、求积误差、导出系数舍入和真实误差预算必须全部保留。整合稿 `kam.tex:6–37`、`supp_structure.tex:322–354` 对这条证明有良好继承，但当前主计算只有单系数无噪声诊断。

这条方法能接三维：先选明确有限特征或经验证的网络近似基，再对**真实变质量模型及磁端口**建立观测矩阵和类误差；不能保持旧35维矩阵／旧数值下界。原机械变量质量也意味着学习动量项改变 `H_P`，物理速度阻尼应使用 `−γN⁻¹H_P`，而非不加判断继续 `−γP`；整合 `supp_structure.tex:385–394` 已说明这一点。

### 4.2 统计强范数路线

旧 `external_v10/sections/theorem_bridge.tex:18–178` 给出详细的参数覆盖＋Hoeffding＋Poincaré＋Gagliardo–Nirenberg证明，明确 iid、密度下界、参数范围、全域梯度/参数 Lipschitz、高阶统一 Sobolev界、规范固定，得到 `C^ell` 误差，再分别应用有限可微 KAM。这个**条件性命题和证明链可保留**，不能因尚无3D数值常数就说命题错误。

但沿轨迹的相邻状态并不自动 iid；第二阶段标签虽为独立抽样，尚未为新神经网给 `M_s,Q,L_g,m0`、动作角图及 KAM阈值。Adam 训练误差也不验证这些条件。此路线的完整推导在第三阶段 `notes/theory.md:214` 被压成一句“有限训练误差不是高阶统一范数”，限制正确，数学内容却未实际继承进新研究链。

本轮可执行反例：`P(z)=∏_{xj∈{−1,−.5,0,.5,1}}(z−xj)^2` 在全部训练点的值与一阶导数均为0，但 `|P(i)|=6.25`。任乘常数可使复域范数任意大。它否定无附加条件的“有限样本误差→复域误差”，不否定上述附充分假设的旧命题。

## 5. 连续 KAM、离散 KAM、旧高维提升分别属于什么对象

### 5.1 旧连续结果不只是相图：必须保存完整证明责任

固定 `unified_kam.tex:23–62` 的全n余弦角平均给

\[
A=(\operatorname{diag}(d_j^4)-2vv^T)/8,\quad v_j=d_j^2,
\quad\det A=(1-2n)8^{-n}\prod d_j^4.
\]

在所声明余弦平面模型中此代数推导成立；非奇异不要求正定。`unified_kam.tex:143–177` 还需要四次非共振、真实 Lie图、包含变换项的解析余项，不能只保留余弦 Taylor尾项；`supp_structure.tex:267–320` 已正确补充有三次项时 `Z4=<H4+.5{H3,W3}>`。新三维变质量能量通常需重新计算三／四次项，不是将上述 `d` 换成12个数。

固定 `core_kam.tex:136–182` 与 `unified_kam.tex:179–464` 明确冻结系数、二次无理频率及全整数 Diophantine界、Fourier候选、复条带、插值／别名尾项、Gram／扭转逆、Haro–Luque常数与小量条件。原短轨迹 COMSOL 主拟合的历史证书：复条带缺陷 `<2.731e−77`、修正 `<2.0894e−41`、tip witness `>1.8977904 mm`。这是旧精确导出 **2 DOF保守 Hamiltonian** 的有条件计算证明链，不是“只看能量稳定”。本轮读了证明，但缺旧候选和Arb计算依赖，未重新认证这些数值；其有效历史地位不因缺包而被删除。

三份冻结对象不得互换：Python三种子GC读出、全FE COMSOL积分拟合（`a≈1.0223248822`，用于S路径）、64条短轨迹COMSOL拟合（`a≈.9999996888`，主误差→KAM证书）。精确路径见 `matrix_parts/chnn.csv` 及原 `ARTIFACT_INDEX.md`。数据来源不同，性能数值与证书不能跨用。

`unified_kam.tex:501–604` 保留精确环面附近的辛管、平均扭转与正规形证明，`measure_proof.tex:16–113,140–420` 另给极薄 `w=10^-220` 管上的96.69383%下界。原文已承认嵌入可定位误差约10^-41不足以判实验初态是否落入该管。宽域1024/1024仅为有限时分类器，不能当严格KAM体积。

**确认修正：**`measure_proof.tex:153–162` 称 Ψ“exact symplectic”，却只证明 `Ψ*λ−I·dt=j(t)DF(t)dt` 闭。取半径.1圆环面，周期积分 `.0314159265≠0`，故相对所声明 primitives 并非恰当形式。应改“symplectic”或加入参考作用偏移。体积转移只需辛性，故这处措辞错误不推翻其测度转移。第二阶段完整报告:344–354已经指出；第三阶段应继承这个修正。

### 5.2 旧连续证书没有自动认证 Central4 的离散环面

原非可分 Central4 推导在 `core_derivation.tex:138–207`：

\[
S_h=hH+\frac{h^3}{24}(J\nabla H)^TH''(J\nabla H),
\quad z_+−z_-=J\nabla S_h((z_++z_-)/2).
\]

完整混合高阶导数不可删。它可在同一3D规范保守 ROM 上直接复用，第三阶段这项有真实推进；但“正确阶数／辛性”与“KAM假设闭合”是两个任务。整合 `kam.tex:113–184`、`supp_structure.tex:396–445` 给出更完整的**条件性**离散路线：exact-symplectic隐式分支、解析域与逆图、混合周期生成函数、`||G_h/h||≤C3ε+C4h^p`、扭转上下界、频率边界和

\[
|e^{ihk\cdot\omega}−1|\ge h\gamma_D|k|^{-\tau_D}.
\]

其文本明确没有认证新两模态参数的数值阈值，不能说它已经给出新3D离散证书。时间变 Birkhoff 图之间的二形式匹配也不是所选自治exact-symplectic映射定理。

本轮反例取连续频率 `(1,√2)`、`k=(1000,0)`、`h=2π/1000`，连续分母1000，离散分母仅浮点 `2.45e−16`（数学上0）。令k增大可任意减小h，故“小步长”本身不替代离散非共振。非辛求解残差、饱和切换、摩擦不能无条件塞入解析 Hamiltonian小扰动预算。

### 5.3 64平面自由度与 S路径：应继承算法和不利对照，不扩大对象

旧 `full_fe_kam_control.tex:23–128` 的低模态 Legendre反解、两端口反馈和高模态受迫稳定线性响应图证明在其假设下成立。`H_YY≻0`、凸动量纤维保证局部逆／单射；实际场梯度对称无迹，需真实独立场和梯度权限。62高模态的阻尼传递分母不消失，给不变二维环面提升和高模态收敛。它**不证明全128维闭环 Hamiltonian，也不给128维正体积环面族**。表中的1.970263mm包络及场限属于旧冻结平面模态对象。

旧 `s_path.tex:1–67,70–146` 的S形是轴向基座供给＋单横向磁场的端点历程，固定材料长度、没有轴向血流／导管接触；不是三维曲血管插入。CHNN tip反馈6.419µm，二次模型6.207µm，已知物理静态逆4.124µm，模态输出反馈25.308µm；静态逆在该慢任务更好，实际governor未激活。这些匹配负对照是成果的一部分，必须进入最终稿。当前缺原S1输入，本轮不称重新积分完成。

### 5.4 新三维 1:1 共振是实质数学分叉

本轮直接重建 `RodROM` 得前八个频率（rad/s）为 `(4.4576294085,4.4576294085,27.6941957200,27.6941957200,79.7832865951,79.7832865951,356.9402366588,356.9402366588)`，另有四个动力学频率。`k=e_i−e_j` 在每对线性弯曲频率给零分母。旧非共振椭圆正规形的假设失败。

这不证明所有有限幅值环面不存在；需要保留共振项、轴对称约化的动量映射/约化空间、三次项和变质量耦合，再为具体约化域或候选环面检验相应KAM定理。随意删除一个弯曲方向、把频率扰动至不共振或回到两模态梁，都不能称完成原三维目标。

## 6. 第三阶段新增单系数控制究竟证明了什么

`stage3/program/control_learning.py:17–80` 构造 `δh=β[h(z,u*)−h(z,0)]`，β=.2，8训练+8留出，拟合一个实系数，再施加 `u_c=−βhat u*`。残差刻意在磁端口像内；近机器精度系数及抵消，是实际几何磁势和端口代数一致性证据。比较目标用相同RK4步长，近零差不是对连续真实流的零误差。

它不检验未知质量、完整复隐藏层、动量Hessian、非可达残差、噪声、线圈实现或新KAM。源码和 `stage3/notes/control.md:69–71` 已明确这些限制，审计不能伪造相反指控。缺口在于：第二阶段已有完整学习和SPD结构，第三阶段还没有将这些分支接入当前一般Birkhoff／实际闭环场，也没有完整证明链接的文稿。

## 7. 确切缺失输入与本轮可复算记录

以下路径均应在 `stage3/source_inputs/starter/stage2/` 下；当前不存在：

- `results/{learning,learning_stress}/{learning_data.npz,rom_matrices.npz,analytic_coefficients.npy,learning_summary.json,evaluation_summary.json,complex_seed1025.pt,complex_seed1026.pt,complex_seed1027.pt}`。
- `results/learning_spd/{local,stress}/{spd_complex_seed1025.pt,learning_summary.json}`；`results/learning_confirmation/{main,stress}/{confirmation_data.npz,dataset_manifest.json,confirmation_summary.json}`；`results/learning_confirmation/frozen/config.json` 及 `frozen/models/{main,stress}/rom_matrices.npz`。
- `results/learning/feedforward/{linear,analytic,complex,truth}.npz`：因此旧新网络32/64段杆前馈对照仍不能从轻量包原样复算。
- 旧S1的 `reproducibility/unified_model/learning/{run_learning.py,raw/}`、`unified_model/theory/{verify_torus.py,hl_constants.py,torus_arb_refine.py}`、`mainline_completion/integral_certificate/comsol_integral_certificate_fit.npz`、该证书冻结Fourier候选与COMSOL观测，以及 `mainline_completion/resonance/kam_magnetic_control.py`、`mainline_completion/s_path/kam_control_audit/certify_kam_lift.py`、`mainline_completion/s_path/run_s_path.py` 实验依赖。`feature_model.py` 也是原学习依赖，其精确子目录需取得S1原树核定。当前可直接读固定旧稿，**不可声称本轮逐行审查或运行这些未提供的S1程序**。旧论文与stage2报告提供入口，非替代数据。

本轮新增检查命令：

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /workspace/1028-cloud/venvs/learning/bin/python stage4/audit/program/chnn_audit_checks.py
```

实际退出码0，最终脚本内耗时2.199s。环境Python/NumPy/SciPy/SymPy/Torch、源文件前后SHA、容差、原始新样本和所有结果分别在 `results/chnn_checks_run.log`、`results/chnn_checks/checks.json`、`fresh_architecture_samples.npz`。未改源权重／冻结数据，未降低旧标准。本轮只新增身份、公式、反例和架构核验；历史性能与高精度证书缺数据，未重训或重证。

## 8. 恢复进完整论文的优先顺序

1. **P0：统一规范坐标／复导数／物理功率。** 将本节2的修正及旧功率解码置于3D变质量Hamiltonian之后；学习、控制、生成函数使用同一个实际场。保留原稿耗散/磁力问题而非靠“复能量”省去。
2. **P1：恢复完整学习两条证据链。** 旧35/45解析特征做独立冻结回归；第二阶段7104实参数能量网与13440实参数SPD网做新3D训练分支，恢复失败、确认集、正则误差和质量条件数。相同数据和预算下增加实网络对照；新标签及权重另存，不覆盖历史。
3. **P1：从学得模型到磁控制必须经过物理动量与可达性。** 对混合动量网络先确定Legendre可逆域，使用正确物理Rayleigh力；把要求力投影误差、线圈约束与原模型误差分开。一般Birkhoff对实际闭环重建，不用旧理想 Hamiltonian代替含残差闭环。
4. **P1：恢复完整学习范数与正规形证明。** 原确定性Gram/观测缺陷界、统计强范数命题、Cauchy域缩减、三次修正、生成函数及离散扰动除以h的规范化，均作为正式证明章节或详细补充；不能压缩为“误差小所以KAM”。
5. **P2：新三维共振理论另建。** 明确对称性约化／共振正规形目标、解析域、扭转与小量，之后才选连续或离散定理。旧有限幅值证明保留为已完成的独立回归，不回写成3D证书。
6. **P2：新控制进入32/64段Cosserat及血管任务。** 继承旧真实磁端口、Legendre提升、能量/净空/工作界及S路径不利对照的方法，重新做三维血流接触、时间空间细化和控制转移误差。保留最终微重力血管机器人目标，不把旧无轴向载荷平面任务作为终点。

因此，CHNN/KAM方面的最终判断是：**路线保存但应用不充分；旧多项有效推导保留在旧稿和stage2报告，第三阶段尚未整链继承；部分原公式及旧exact措辞确需修正；条件性旧定理不等于新模型完成；完整新论文必须显式恢复这些数学链及证据层级。**
