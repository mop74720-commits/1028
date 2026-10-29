# 实际复算、验证覆盖与冻结证据

本审计起点为 GitHub `main` / 本地 HEAD `38ee6a7fb8f279fc80be05ee2bd4956817364ffc`。本文件区分重新执行源码、检查旧 JSON、重新生成轨迹和独立数学反例。23 项测试通过不能代替完整三维机器人的理论与实验验证。

本轮所选 9 次主运行全部退出码 0：第一次 23/23 通过，重新生成结果后的隔离运行再次 23/23 通过，两次均 0 跳过。77 项科学标量和四个 NPZ 中 92 个数组逐项比较，最大绝对差均为 0；耗时元数据允许不同。476 个 `stage3` 源目录文件的运行前后哈希相同，审计开始时全仓库 479 个 Git 跟踪文件的 SHA256 全部保持不变。确认这几项可复现，并不改变下文的短窗口、简化控制和未证明内容限制。

先对照了原稿原生 OMML：Theorem A/B 所在段、p0986/m0434 的（35）、p1003/m0442 的（36）及重复位置，再阅读旧 v10 `english/sections/structure.tex`、`controlled_analysis.tex` 中相关充分条件，随后检查第三阶段的实现与测试。段号采用 `source_omml/original1025_reading.txt` 的全体 `w:p` 文档顺序，不采用仅正文直接子节点的另一套编号。公式审查见 `birkhoff_full_audit.md`；以下数值通过不修补原定理缺失的假设。

## 环境与复算方法

实际解释器为 `/workspace/1028-cloud/venvs/learning/bin/python`：Python 3.12.14，NumPy 2.3.5，SciPy 1.17.0，PyTorch 2.5.1+cpu，Matplotlib 3.10.8，SymPy 1.13.1。禁用 `.pyc` 写入，BLAS/OpenMP/Numba 线程均固定为 1；两个实验序列最多并行执行。完整命令数组、实际工作目录、UTC 起止时间、耗时、退出码、测试数量、跳过数量、输出生成时间和 SHA256 均保存在 `results/reproduction.json`。逐命令输出保存在 `logs/reproduction/`。

实际计算副本为 `/workspace/1028-stage4-runs/reproduction-q8kwh8w7/stage3`。复制的是普通文件，包含真实 `source_inputs`，未使用会回写源目录的符号链接。生成前删除副本中的 `integrators`、`birkhoff`、`control`、`control_learning` 结果目录，防止旧成功文件冒充新运行。唯一保留的结果是旧长窗中断记录，供“不能误报成功”的回归测试读取；它在清单中显式标记为历史记录。新 JSON/CSV/NPZ 保存到 `results/reproduced/`，完整源码副本不提交 Git。

复算命令（在仓库根目录执行）：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 stage4/audit/program/reproduce_audit.py
PYTHONDONTWRITEBYTECODE=1 /workspace/1028-cloud/venvs/learning/bin/python stage4/audit/program/compare_reruns.py
```

脚本使用上述已记录的虚拟环境；在其他机器上须将脚本顶部 `PYTHON` 和 `SCRATCH_BASE` 改为实际解释器与临时目录。无需重写冻结的第三阶段数据或降低容差。脚本最终检查源目录哈希，比较脚本进一步检查审计开始时全部 Git 跟踪文件。

## 23 项测试到底覆盖什么

| 文件 | 数量 | 实际检查 | 限制 |
|---|---:|---|---|
| `stage3/tests/test_rom_bridge.py` | 6 | 真实几何质量与 Hamiltonian、方向导数、场 Jacobian、非零几何惯性、磁虚功、可微接口 | 点态一致性，非所有位形上的全域误差界 |
| `stage3/tests/test_birkhoff.py` | 4 | 一阶输运系数、直接势函数/规范恒等式、图场和原场误差区分、非退化域拒绝 | 特殊常对角阻尼图与局部截断，不覆盖任意血流接触 |
| `stage3/tests/test_integrators.py` | 5 | 非可分二次 Hamiltonian 的矩阵指数独立基准、真实 ROM Central4 梯度/理想切映射、中点及加权格式 | 理想隐式切映射的结构检查不是有限精度程序 Jacobian 的全域证明 |
| `stage3/tests/test_control.py` | 3 | 共点反馈功率、真实 Gm 接口、Maxwell/场约束、不可达残差 | 小范围局部端口，不代表完整线圈沿杆的场一致性 |
| `stage3/tests/test_numerical_outputs.py` | 3 | 读取已存 JSON，检查短窗阶数与误差分离、旧长窗中断状态、模型和初值相同 | 测试自身不重新积分；其中一项只确认失败记录没有被改成成功 |
| `stage3/tests/test_control_results.py` | 2 | 读取已存学习/线圈结果及源 SHA，检查留出集、约束与虚功 | 不训练完整 CHNN；通过不能证明学习误差在复解析域内有界 |

合计 18 项直接数学/接口测试、5 项结果文件验收。第一次 23 项通过时，后 5 项仍主要读取已交付证据。随后重新生成上述结果，再在隔离副本运行同样 23 项，才构成“新计算 + 验收”的证据；旧长窗状态测试仍明确依赖历史失败文件。

采样范围也必须区分：质量变化约 13.74% 的检查使用 `initial_state(.08)`；积分器与控制轨迹使用幅值 `.01`。Birkhoff 恒等式测试使用另一个幅值 `.025` 和时间 `.003` 的点；成功的图积分只覆盖无量纲 `T=.0005`。不能把这些点态检查拼接成“13.74% 变质量下已完成长时间图积分”的结论。

## 实际生成的实验与容差

每项命令均以前述学习环境解释器运行，相对路径以运行副本根目录为工作目录。机器可读的最终状态、精确耗时和失败原因以 `results/reproduction.json` 为准。

实际耗时：首次 23 项 51.829 s；完整积分器 216.250 s；短窗 Birkhoff 382.269 s；窗口诊断 19.575 s；控制 225.070 s；线圈力 13.743 s；求积 11.927 s；标量学习 49.701 s；新结果上的 23 项 56.597 s。比较程序退出码 0，另存 `results/comparison_run.json` 及对应日志。

| 命令参数 | 范围 | 判据/容差 | 实际证据 |
|---|---|---|---|
| `-m unittest discover -s stage3/tests -v` | 交付数据上的 23 项 | 各冻结测试原阈值；不修改 | `logs/reproduction/original_23_tests.log` |
| `stage3/program/run_integrators.py` | 保守中点、Central4；阻尼中点、合法加权中点，各三级网格 | 隐式增量残差无穷范数 `2e-13`；参考解见下 | `results/reproduced/integrators/` |
| `stage3/program/run_birkhoff.py --duration .0005` | 原场中点与局部图中点，各三级网格 | 同一 `2e-13`；原场与表示场分别建立参考 | `results/reproduced/birkhoff/results_T0.0005.json` |
| `stage3/program/diagnose_birkhoff_window.py` | 多个时间/状态处的截断场病态诊断 | 直接 Jacobian、谱、奇异值计算 | `results/reproduced/birkhoff/window_diagnostic.json` |
| `stage3/program/control_experiments.py` | 六类闭环/控制方向、磁端口投影与约束 | RK4，8/16 步细化；不是隐式求解残差 | `results/reproduced/control/control_results.json` |
| `stage3/program/control_coil_force.py` | 完整线圈力与仿射 Gm 对照 | 保留原虚功、求导、约束阈值 | `results/reproduced/control/full_coil_force_audit.json` |
| `stage3/program/control_quadrature.py` | 磁端口求积/数值秩 | 原阈值及 SVD 结果 | `results/reproduced/control/port_quadrature_rank.json` |
| `stage3/program/control_learning.py` | 解析磁势系数辨识与磁端口补偿 | 固定训练/留出集，各 8 个 24 维状态 | `results/reproduced/control_learning/` |
| `-m unittest discover -s stage3/tests -v` | 新生成结果上的 23 项 | 原阈值不变；保留旧长窗失败状态检查 | `logs/reproduction/fresh_23_tests.log` |

积分器的 DOP853 参考设置依次为 `(rtol,atol,max_step)=(2e-11,2e-13,T/4)`、`(5e-13,5e-15,T/8)`；Birkhoff 参考依次为 `(2e-10,2e-12,T/8)`、`(5e-12,5e-14,T/16)`。报告逐项保存参考细化差。参考解采用相同 ROM 右端项，属于独立时间离散，不是完全独立的物理建模实现。非可分二次 Hamiltonian 的矩阵指数基准才提供了独立解析时间解。

积分器与控制窗口 `T=.004` 约为 `0.897 ms`；Birkhoff 成功窗口 `T=.0005` 约为 `0.112 ms`。所有状态误差均在程序给定的无量纲正则坐标上计算，不能直接解释为末端毫米误差。结构缺陷主要检查首步理想隐式切映射，不代表整条有限精度轨迹上每步的最大缺陷。

## 实际结果应如何解释

已完成重跑的最细网格数值如下。二形式列是首步理想切映射的谱范数缺陷；阻尼行使用适用的共形目标。

| 分支/方法 | 最大状态误差 | 实际阶数 | 二形式缺陷 | 最大增量求解残差 |
|---|---:|---:|---:|---:|
| 保守中点，h=.00025 | 1.142950083e-6 | 1.975366 | 5.5511e-16 | 1.3485e-18 |
| 保守 Central4，h=.00025 | 4.786112137e-9 | 3.969394 | 4.6082e-16 | 2.0405e-18 |
| 阻尼普通中点，h=.00025 | 1.142568103e-6 | 1.975372 | 5.9089e-7 | 2.4263e-18 |
| 阻尼加权中点，h=.00025 | 1.142480008e-6 | 1.975357 | 6.7269e-16 | 2.3484e-18 |
| 局部图中点，h=.00003125，对表示场 | 9.984918016e-9 | 1.999702 | 4.4417e-16 | 1.5970e-16 |
| 同一局部图轨迹，对原场 | 2.185759971e-5 | 不随步长呈二阶消失 | 同上一行 | 同上一行 |

积分器参考细化差约 `1.1734e-12`。最细图方法的最大求解矩阵条件数 `1.023438`，首步最小奇异值 `0.999714`；这些是此次有限点集上的数值证据。保守中点、Central4、阻尼普通中点和加权中点的最大中点功率残差分别约为 `1.0433e-12`、`1.9812e-15`、`1.0671e-12`、`1.4085e-10`；局部图相对原动力学的功率残差约 `3.2523e-6`。功率残差包含功率积分的中点求积误差，不是精确离散能量恒等式。

保守中点和 Central4 的实际阶数分别接近 2 和 4；阻尼加权格式在其合法常阻尼分支上满足相应共形二形式关系。这些结果继承了有效算法并接入真实位形相关质量矩阵。它们没有证明一般非比例反馈、接触和规定血流下仍保持同一形式。

局部 Birkhoff 图中点趋向它实际积分的表示场，二阶误差能降至约 `1e-8`，但相对原场仍约 `2.19e-5`。结构匹配接近机器精度与原场拟合误差大约三个数量级的差距可同时存在。步长趋零不能消除固定一阶输运截断的模型误差。细化图积分器而不改进一形式输运不会自动补齐一般 Birkhoff 研究路线。

重新运行线圈力程序保留了接近 1 的完整场/仿射广义力相对差异；没有把负结果删掉或放宽阈值。此处是相同源码的可重复性核验；独立单位、磁能、求积与场空间变化核查见 `physical_and_control_audit.md` 及 `results/physical_independent.json`。

学习程序拟合一个已知解析磁势形状的实数系数，不能替代旧 v10 或第二阶段的完整可训练复值网络。其留出集误差很小，说明该可辨识标量问题被正确复算，不说明三维完整 CHNN 已完成。完整网络的继承与缺失权重核对见 `chnn_kam_inheritance.md`。

科学数值逐项差异保存在 `results/rerun_comparison.json`：比较 12 个积分器/网格结果、6 个 Birkhoff 结果、磁力差异与学习指标，合计 77 个标量；四个 NPZ 内全部 92 个同名数组的形状和有限性检查通过。这两组的最大绝对差均为 0。运行耗时、路径和日志字节不作为科学等值目标。同机可重现不等同于跨平台精确相等或全域正确。

## 保留的失败与未执行内容

`results/reproduced/birkhoff/results_T0.004.json` 是原有长窗失败记录的原样复制：状态为 `interrupted_due_to_diagnosed_transport_truncation_failure`，行结果为空，仅完成原场的两组参考。旧 JSON 记录约 246 秒后人工中断；旧日志末尾为 `KeyboardInterrupt`，`stage3/notes/birkhoff_experiments.md:23` 报告退出码 130，后者不是本轮重新测得的退出码。本轮没有再次昂贵地运行整个长窗。重新运行了局部窗口病态诊断，但某时刻 Jacobian 的正实部特征值只能提示局部刚性/放大风险，不能单独证明时变系统的全窗增长率。

本文件列出的复算没有执行：缺少冻结权重/大型轨迹的完整 CHNN 训练复核、旧区间 KAM 证书全部生成过程、32/64 段三维杆上新闭环的长时间转移实验、完整双向 FSI、柔性血管壁或真实微重力生理标定。旧文件存在、历史结果保存和本轮实际运行是不同状态。其他审计程序的独立运行见对应专题文档，不能并入这 23 项的通过数量。

## 测试副作用与修复记录

发现冻结测试本身具有写出副作用：`stage3/tests/test_rom_bridge.py:98` 的 `tearDownClass` 重写 `results/rom_bridge.json`；`test_birkhoff.py:108` 重写 `birkhoff_identity_checks.json`。初次在原仓库运行测试后，前者计时字段发生变化；后者内容字节相同但仍发生写入。审计立即从运行前普通副本恢复原字节，并与 Git HEAD 校验一致，没有将新计时冒充冻结结果。具体前后 SHA256 在 `results/test_side_effect_restore.json`。

这是实际执行时暴露的复现性缺陷，不能把第一次运行描述为完全只读。新 `program/reproduce_audit.py` 已修正为连首次验收也使用独立的交付数据副本；本轮日志保留首次真实工作目录，不追改历史。最后一轮 23 项在计算副本中执行，新的诊断 JSON 单独保存至审计结果。`results/frozen_preservation.json` 检查全部起始 Git 跟踪文件，`results/stage3_source_hashes.json` 保存源目录哈希。`stage3/install.sh` 是起始未跟踪的环境草稿，不提交。

运行耗时处于共享机器且有两个实验序列并行，适合记录复算成本，不适合直接据此发布算法速度排名。最终新结果、日志及原始失败记录均保留；没有更改物理目标、降低原求解标准或改写旧成功/失败数据来满足测试。
