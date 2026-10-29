# v10 S2 新增实验：实现读取与可复算性初查

核查日期：2026-10-29。来源为只读仓库 `stage2/sources/v10_original/`，提交 `8761d70239a54985b40c0a6196f52e53d5b2e4d2`。本轮未修改上游文件，未运行大扫描、COMSOL 或未知下载脚本。下述“原结果”与“本轮复核”严格分开。

## 1. 阅读和执行覆盖

已完整阅读两目录的全部原创 Python 实现：

- `stability_scan/run_stability_scan.py`（11562 字节）；
- `stability_scan/verify_and_boundaries.py`（17289 字节）；
- `stability_scan/summarize_scan.py`（10588 字节）；
- `stability_scan/build_manifest.py`（1918 字节）；
- `robustness/run_operational_tolerances.py`（15107 字节）；
- `robustness/inputs/feature_model.py`（5500 字节，原学习实现的冻结副本）。

已完整阅读两个 README、requirements、扫描 `protocol.json` 与 `protocol_amendment.json`、输入模型说明、robustness 输入来源清单与环境记录，以及 `sections/stability_boundary.tex`、`sections/operational_tolerances.tex`。已读主要汇总 JSON：扫描 summary、Floquet、独立求解器、完整 FE Radau、启动根及其细化、最小稳态根；robustness 的解析证书、primary/refined 结果和两级差异。

本轮没有逐项人工检查 1715 行结果 JSON，也没有完整展开所有高维轨迹；对原始 NPZ 全数组做了有限数检查，重新计算 monodromy 特征值与鲁棒性轨迹统计。没有运行原始数值积分或 Arb 证书，不能把本轮写成“1715 次积分已重跑”或“严格证书已独立重算”。

独立复核产物：`stage2/runs/v10_s2/independent_archive_audit.json`。运行方式为 Python 标准库及 NumPy 的只读脚本，完整读取上述 NPZ/清单后在隔离目录写 JSON；不导入任何上游模块，内部耗时 0.367 秒。

## 2. 科学对象：这里仍是原平面梁

两项实验均使用长 0.08 m、半径 0.0006 m、32 个一致质量 Hermite 单元的平面小斜率 Euler–Bernoulli 梁，偏场 0.03 T、端部偶极矩 $2\times10^{-5}\,\mathrm{A\,m^2}$、完整正弦/余弦磁矩。原参数明确是示例参数，不是空间站、人体或临床标定数据。

扫描对象是冻结对角模态模型，阻尼率来自输入说明 $\alpha=0.5555852368222173\,\mathrm{s^{-1}}$；鲁棒性对象是冻结的精确二进制节点矩阵 $M,K$，使用 $\alpha=0.55558524\,\mathrm{s^{-1}}$，保留 $\Phi^{\mathsf T}M\Phi$ 与 $\Phi^{\mathsf T}K_b\Phi$ 的完整非对角余差。原文已经明确这两种冻结有限精度对象不被假定为精确共轭。

扫描不含血流、接触、磁梯度、学习替代或 governor；鲁棒性实验有两个理想端部功率端口与 governor，但仍无血流、接触和三维转动。因此这些数据可作为原方案基准，不能改名为新的三维血管模型结果。

## 3. 1715 次受迫响应扫描如何产生

`run_stability_scan.py` 完整实现以下协议：

| 项目 | 冻结值/实现 |
|---|---|
| 场幅值 | 1、2、4、6、10、15、20 mT，共 7 个 |
| 频率比 | 0.70–1.30 的 0.02 网格与 0.94–1.06 的 0.005 网格去重，共 49 个 |
| 独立初态 | $0$、$\pm(0.18,0.04,0,0)$，共 $7\times49\times3=1029$ 次 |
| 延拓 | 各幅值升频、降频两条分支，共 $7\times49\times2=686$ 次 |
| 时间 | 每次 128 周期弃置、64 周期记录；总 81.2783–150.9455 s |
| 积分 | 自写固定步 DOP853，使用 SciPy 的 12 阶段系数，256 步/周期；不含自适应误差控制 |
| 启动场 | $B_y=A[1-e^{-(t/0.25)^2}]\sin(r\omega_0t)$ |
| 延拓相位 | 每段都从零场相位开始、继承上一段终态；只有每条分支第一段重启 ramp |
| 空间/时间采样 | 每周期 128 个相位作 Hermite Bernstein 空间上界；末周期保存每个积分步 |

模态方程与变分方程相符：

$$
\dot X_j=\omega_jY_j,\qquad
\dot Y_j=-\omega_jX_j-\alpha Y_j+\omega_0d_j[\vartheta-\sin\vartheta+u\cos\vartheta],
\quad\vartheta=d^{\mathsf T}X,
$$

$$
D_X\dot Y=-\operatorname{diag}(\omega_j)+\omega_0(1-\cos\vartheta-u\sin\vartheta)dd^{\mathsf T}.
$$

一根切向量每周期重新归一化，后 64 周期平均得到条件有限时间指数；驱动相位固定，没有把增广时钟的零指数混入。它不是整个 Lyapunov 谱，也不独立证明渐近混沌或无混沌。

`verify_and_boundaries.py floquet` 在每个两模态末态再积分 512 步/周期的完整 $4\times4$ 基本矩阵。由于散度为 $-2\alpha$，以 $\det\mathcal M=e^{-2\alpha T}$ 核查行列式。原记录范围：谱半径 0.8038091241–0.8890547397，最大周期余差 $6.64687\times10^{-11}$，最大行列式差 $1.40443\times10^{-14}$。

**本轮独立复核**：直接对存档 monodromy 矩阵重新求特征值，1029 与 686 个对象均有限，全部重新计算谱半径小于 1；与存档谱半径最大差为 $1.33227\times10^{-15}$。这验证了存档矩阵到稳定性统计的环节，尚未重新验证矩阵是原 ODE 的精确或数值一致基本解。

原记录中的 15 个参数点分别进行了时间加密、四模态和八模态积分。不能将其描述为“所有 1715 个点均经过 64 模态 Floquet 验证”。原 README 和正文已正确区分范围。

## 4. 完整 64 模态净空边界与启动超调

`periodic_response` 对每个模态使用精确线性传递因子

$$
X_{j,k}=\frac{\omega_0\omega_jd_jf_k}{\omega_j^2-(k\Omega)^2+i\alpha k\Omega},
\qquad f=\vartheta-\sin\vartheta+u\cos\vartheta,
$$

迭代非线性固定点，并从重构状态重新计算非线性 ODE 余差。代码没有把固定点迭代收敛当作已证明的收缩映射定理，这一点正确。FFT 相位网格默认 1024；根由 Brent 法定位。

| 结果 | 入口与数据 | 原结果/边界 |
|---|---|---|
| 稳态 4 mm 曲线 | `verify_and_boundaries.py roots`；`full_FE_steady_clearance_boundary.json`、`full_FE_boundary_waveforms.npz` | 35 个频率比、31 个幅值根；另 4 点在 20 mT 内没有该分支的交点 |
| 模态/相位细化 | `roots` 同时生成 `boundary_modal_phase_refinement.json` | 5 个代表点、2/4/8/16/32/64 模态和 512/1024/2048/4096 相位 |
| 周期解独立积分 | `roots` 后半段；`full_FE_Radau_*.npz` | $r=0.8,1,1.2$，完整 64 模态一周期 Radau；原最大端部差 $1.1021\times10^{-12}$ m |
| 最小稳态幅值 | `minimum` | 约 1.915911313 mT，$r=0.999244722$；这是近一阶共振处数值极小值 |
| 零初态启动交点 | `startup`；`startup_*mode_r*.npz` | 5 个频率比，2/8 模态、0.25 s ramp、192 周期；依赖指定初态与 ramp |
| 启动抽核 | `startup` 后半段 | 3 点时间加密与完整 64 模态前 32 周期；另算稳态，但没有证明 32 周期后的连续时间尾界 |

原稳态 4 mm 幅值在 $r=0.8,0.9,1,1.1,1.2$ 依次约为 13.6362、7.5005、1.91685、8.7909、18.5936 mT；八模态启动交点约为 8.6513、5.1882、1.91689、5.7662、10.4455 mT。$r=0.8$ 的 8.6513 mT 请求，完整 FE 稳态约 2.5411 mm，启动却达 4.00197 mm。代码没有添加碰壁力，4 mm 仅为穿越诊断阈值。

**限制**：Bernstein 行给定时刻的全空间上界；只抽取有限相位仍不是连续时间严格上界。原文已注明这一点。负条件指数、Floquet 模小于 1、所有采样分支一致均只能支持所列数值局部稳定/吸引性证据，不能推出连续参数域无混沌、全局唯一吸引子或保守 KAM 环面破裂阈值。0.1 rad 也只是报告筛选条件，不能作为已标定的小斜率有效性阈值。

## 5. 非零初始化/传感/执行误差的 4 秒净空证明

原证明与实现的主要链条一致。对于冻结节点模型，

$$
E=\tfrac12v^{\mathsf T}Mv+\tfrac12q^{\mathsf T}Kq+E_0(1-\cos\vartheta),
\quad\dot E=-\alpha v^{\mathsf T}Mv+Fv_w+\mu B\cos\vartheta\,v_\vartheta.
$$

设 $C_w=\max_r b_rK^{-1}b_r^{\mathsf T}$，则 $\sup_s|w|\le\sqrt{2C_wE}$。$K_b=K+E_0e_\vartheta e_\vartheta^{\mathsf T}$ 的二次能量 $Q$ 控制初始化：$Q(e)\le5$ pJ 推出

$$
E(0)\le\overline E_0=(\sqrt{Q(q_{\rm ref},v_{\rm ref})}+\sqrt{5\mathrm{pJ}})^2.
$$

这是一整个全状态能量椭球，不能把端部位移、角度、速度的各个投影上界独立拼成误差盒。参考是导出的有限 Fourier 点及节点状态，原文没有假定它属于精确环面。

传感误差给出 $|a_i-\widehat a_i|\le\Delta_i$；相对执行误差 $|g_i|\le\eta_i$ 则由

$$
P^+(u)=\sum_i\{\widehat a_i u_i+[\Delta_i+\eta_i(|\widehat a_i|+\Delta_i)]|u_i|\}
$$

覆盖非加性功率。独立加性误差与阻尼完成平方，得到

$$
r^{\mathsf T}v-\alpha v^{\mathsf T}Mv\le\frac{r^{\mathsf T}M^{-1}r}{4\alpha}
\le p_e=\frac{(\epsilon_F\sqrt{m_F}+\mu\epsilon_B\sqrt{m_\vartheta})^2}{4\alpha}.
$$

令 $R_T=Tp_e$、$C=E_{\max}-R_T$，$\dot W=P^+(u)$ 并按正齐次径向因子缩放请求，使 $\dot W\le\kappa(C-W)$，便有

$$
E(t)\le W(t)+tp_e\le E_{\max}<\frac{c^2}{2C_w},\qquad 0\le t\le T.
$$

这里实际持续施加的控制受 governor 改写，所以证明的是有限时净空，不是含噪环面保持。若加性误差持续非零，不能把 $T=4$ s 的储备外推为无限时保证。原定理对采样时延、slew 的讨论也是条件公式，并未数值标定硬件延迟。

`certify()` 用 256-bit Arb 对精确导出矩阵作正 LDL 枢轴检查、逆矩阵柔度、Hermite 精确系数和初始化上界。原证书给出：$C_w<335.338810137$，$E_c>23.85646921$ nJ，$\overline E_0<22.11866366$ nJ，$R_T<0.09677917$ nJ，$E_{\max}=22.66$ nJ，净空位移界小于 3.898405 mm。证书是冻结数学矩阵的证书，未包含材料、外力模型或真实血管的误差。

## 6. 鲁棒数值实现及本轮复核

`run_operational_tolerances.py --stage {certificate,primary,refined,compare,all}` 仅依赖本目录 `inputs/`。请求器调用完整学习梯度和 Hessian，并通过最多 8 次 Newton 迭代反解速度到动量；安全过滤本身不要求请求器完美。节点物理模型在完整模态基中计算，保留变换后质量与刚度，不把对角化浮点余差直接删除。

传感、相对执行和加性端口误差均为不同频率的确定性正弦，幅值与声明包络一致。它们不是随机噪声统计模型。给定扰动初态的实际全状态误差用 Arb 重新计算；随后用 Radau 积分 4 秒，2001 个共同输出时刻。

原 primary 相对误差 $2\times10^{-8}$，分量绝对误差为位置 $2\times10^{-13}$、速度 $2\times10^{-11}$、归一化能量 $2\times10^{-13}$；refined 全部缩小 10 倍，`max_step=.008`。原两次运行耗时 49.59/152.15 秒，不能作为当前机器预计耗时保证。

本轮直接从保存轨迹重新计算并与 JSON 一致：

| 量 | 本轮从存档数组重算 |
|---|---:|
| refined 最大物理能量 | $2.1744897926469604\times10^{-8}$ J |
| refined 保存时刻全中心线 Bernstein 上界 | $0.0019441442280068192$ m |
| governor 激活比例 | $0.9780109945027486$ |
| refined 最大功率账本余差 | $2.480243958190763\times10^{-16}$ J |
| primary/refined 最大端部差 | $9.695051731263907\times10^{-9}$ m |
| 最大能量差 | $3.1595801409201517\times10^{-15}$ J |
| 最大功观察器差 | $1.1644306120029247\times10^{-15}$ J |

97.8% 激活比例和最小请求比例约 $4.25\times10^{-5}$ 意味着请求大幅被过滤，不能把该轨迹当作精确 KAM 实现结果。原文对此已有明确说明。

## 7. 可复算性、哈希和尚待执行事项

本轮对扫描 `manifest.json` 的全部 58 个文件重新核对字节数和 SHA-256，无不一致。robustness 五个输入文件逐项匹配 `inputs/manifest.json`；输入来源不依赖历史 E 盘路径。主目录只把旧路径留在 provenance 元数据中，未参与运行。

当前运行环境：Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8、threadpoolctl 3.6.0、PyMuPDF 1.26.6；**缺少 Numba 和 python-flint**。因此当前不能直接运行原入口。原 requirements 锁定 NumPy 1.26.4、SciPy 1.13.1、Numba 0.60.0、python-flint 0.9.0；后续应使用隔离环境安装匹配依赖，不能在现有 NumPy 2.3.5 环境直接补入旧 Numba 并声称原环境重现。本轮未安装或修改包。

后续最有价值的低成本入口是：

1. 在隔离副本运行 `python verify_and_boundaries.py checks --threads 1`，复算解析 Jacobian 与独立 DOP853 检查。
2. 运行 `python run_operational_tolerances.py --stage certificate`，实际复算 Arb 正定性、柔度、储备与初态证书。
3. 用同一隔离副本运行 `--stage compare` 仅重建存档差异；这仍不重跑轨迹。
4. 如需原轨迹重现，再运行 primary/refined。大网格、完整启动扫描和根曲线需单独安排，限制为一个 Numba/BLAS 线程。

原入口都写入自身目录，故必须先复制到运行目录。`run_stability_scan.py` 默认线程数 12，README 示例 14–16；不能不带 `--threads 1` 在当前审查中照抄。`robustness` 内部设置 threadpoolctl 为 1，但 Numba 缓存也在自身目录，因此亦须隔离副本。

截至本轮，未发现这六个已读 Python 文件与相应两节数学模型之间足以直接推翻所述限定结论的明确代数错误。仍待检验的关键部分是：实际重积分的环境稳定性、完整 Arb 重算、以及新的三维血流/接触模型所需的外力功率、输入可达性和非光滑切换扩展。本轮核查没有完成这些后续证明。
