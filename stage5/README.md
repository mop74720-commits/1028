# 第五阶段：三维 ROM、一般 Birkhoff 与完整线圈闭环

从 `f3aa09c6449ff6d0ff732f2b19a4f65c6dcf4cda` 开始，分支为
`stage5/unified-3d-repairs`。开始时和提交前均核对远端；原始材料及
stage2/3/4 的 580 个已跟踪文件由 SHA-256 保护。新增内容全部在本目录。
本地环境配置草稿 `stage3/install.sh` 不属于交付。

目标继续是**空间站微重力条件下人体血管内的三维磁驱柔性介入机器人**。
这是实际代码、证明修正和实验交付；还不是完整正式论文，也不是整个目标已经完成。
十三章路线沿用第四阶段，不把旧两模态 KAM 证书改称三维证书。

## 先读哪些证据

| 入口 | 内容与责任 |
|---|---|
| [notes/stage5_results.md](notes/stage5_results.md) | 本轮 P0 A—D 验收边界、结果与剩余工作 |
| [notes/unified_model_contract.md](notes/unified_model_contract.md) | 同一几何/质量模型、不同物理分支、单位、输入和对照身份 |
| [repair_status.csv](repair_status.csv) | E01—E16 的错误、修正、测试、实际采用与未完责任 |
| [inheritance_update.csv](inheritance_update.csv) | 原 115 条记录及原 21 列逐值保留，新增实际继承进度和证据 |
| [notes/repair_ledger_guide.md](notes/repair_ledger_guide.md) | 六层继承状态、修复采用边界、账本重建命令与真实代码锚点 |
| [proofs/corrected_mathematics.md](proofs/corrected_mathematics.md) | 变分符号、Theorem A/B、固定生成坐标 PDE、递推及原（30）—（36） |
| [proofs/birkhoff_transport.md](proofs/birkhoff_transport.md) | 高阶一形式、规范、空间缓存误差、实际 24 维 Moser 图与有限时间误差 |
| [notes/transport_experiments.md](notes/transport_experiments.md) | 接受的高阶图结果、同一 Ku 比较、原场/表示场功率分解与失败域 |
| [proofs/coil_energy_ports.md](proofs/coil_energy_ports.md) | 完整线圈磁能、虚功、总电流、真实力端口和受限分配 |
| [proofs/integrators_full_coil.md](proofs/integrators_full_coil.md) | 同一闭环隐式更新、非可分 Central4、恰当辛原函数与收敛条件 |
| [proofs/high_derivative_ad.md](proofs/high_derivative_ad.md) | 实际发现的高阶自动微分错误、最小反例和独立替代验证 |
| [proofs/chnn_kam_restored.md](proofs/chnn_kam_restored.md) | 完整复坐标、有限特征/统计误差证明链、旧 KAM 与新共振部分结果 |
| [notes/chnn_kam_experiments.md](notes/chnn_kam_experiments.md) | 九次新训练、真实端口分配、负 Hessian、共振正规形及不变性反例 |
| [notes/rod_transfer.md](notes/rod_transfer.md) | 新控制进入有流、有壁的 16/32/64 段 Cosserat 杆，包括不利结果 |
| [results/start_provenance.json](results/start_provenance.json) | 起点 HEAD、原件哈希、三个 ZIP 的 391 个条目逐字节核对 |

原始 1025 的原生 OMML 索引位于 `stage4/audit/source_omml/`；固定旧 GitHub
v10 的正文与下载清单位于 `stage4/audit/external_v10/`。本轮按这些定位继承证明，
不只读 README。完整第二阶段融合 Markdown 报告实际存在于轻量包，不能称它缺失。
缺的是下述部分历史权重/原始证书资产。

## 当前可运行的连接

`CoilROM` 直接继承真实 12 配置自由度、20 空间几何单元的 Kirchhoff ROM。
每次求值重新计算 SO(3) 几何、完整位形质量及其导数；固定模态缩放不等于固定质量。
全线圈磁势来自实际磁化求积点和 12 个圆线圈，每圈 256 个导线积分点。
偏置只记入总电流一次。物理磁力先对固定电流求偏导，组成反馈后再对闭环场求全导。

高阶 Birkhoff 用本场及其导数计算时间系数，实际解 Moser 辅助 ODE；
原场、表示场、空间缓存、数值图和离散积分误差分别保存。
采用有源规范避免把保守 Hamiltonian 的可消除截断误差归咎于物理模型，
并独立算回齐次输运的前三阶系数关系。没有使用未知精确相流作为算法输入。

固定电流保守、比例阻尼、光滑共点电流、受限采样控制是**不同分支**。
只有适用分支调用自治 Central4 或精确比例阻尼图。普通中点在未知中点内求真实反馈。
受限采样器包含先前电流，是 36 维含记忆更新，不能叫作正则 24 维辛映射。

学习与共振实验目前使用原理想均匀偏置 Hamiltonian；全线圈闭环使用新的磁能。
两者共享几何、质量与缩放，不共享磁势或平衡频谱。
`CoilROM.metadata()` 中继承的 `omega_rad_s/nu/repeated_frequency_pairs` 是原分支的
缩放/频谱资料，**不是全线圈 Hamiltonian 的新平衡频谱或 KAM 证书**。

## 环境与快速验证

实际两个环境均为 Python 3.12.14。学习/数学环境使用 Torch 2.5.1+cpu、
NumPy 2.3.5、SciPy 1.17.0、SymPy 1.13.1、Matplotlib 3.10.8；
完整杆环境使用 PyElastica 1.0.0、Numba 0.62.1、llvmlite 0.45.1。
精确依赖清单见 [results/environment.json](results/environment.json)。
新机器需要安装这些依赖；两个解释器路径可由 runner 参数替换。

在仓库根目录执行：

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export NUMBA_CACHE_DIR=/tmp/1028-stage5-rod-numba
learning_python=/workspace/1028-cloud/venvs/learning/bin/python
rod_python=/workspace/1028-cloud/venvs/rod/bin/python
python3 stage5/program/run_new_tests.py --learning-python "$learning_python" --rod-python "$rod_python"
python3 stage5/program/run_regression.py
python3 stage5/program/provenance.py --verify
python3 stage5/program/validate_delivery.py
```

新测试按模块隔离进程；完整杆测试自动使用杆环境。运行命令、退出码、时间、源码 SHA
及日志存入 `results/tests/<UTC>/`。旧 23 项测试在仓库外临时副本执行，避免旧测试的
写入行为改动冻结证据；其中 18 项是直接测试，5 项是已保存结果验收，不能称重做旧实验。
`validate_delivery.py` 只检查打包、115 行、16 ID、JSON、语法及原件哈希，不代表研究完成度。

### 分模块重算

下列耗时取决于硬件。完整高阶输运约需数十分钟，不能将小矩阵单步耗时当整个算法成本。
每个结果记录其实际源码版本。为了保留本次冻结运行，**完整重算建议在提交后的独立副本执行**：

```bash
git worktree add --detach /tmp/1028-stage5-reproduce HEAD
cd /tmp/1028-stage5-reproduce
```

数学反例、实际质量/线圈、同场闭环：

```bash
"$learning_python" stage5/program/run_corrected_identities.py
"$learning_python" stage5/program/verify_high_derivatives.py --section all
"$learning_python" stage5/program/run_transport_backend_validation.py --model synthetic --run-id independent_rerun
"$learning_python" stage5/program/run_transport_backend_validation.py --model fullcoil --run-id independent_rerun
"$learning_python" stage5/program/run_coil_validation.py --output stage5/results/coil/independent_rerun
"$learning_python" stage5/program/run_coil_closed_loop.py --output stage5/results/coil/independent_rerun
"$learning_python" stage5/program/coil_transport_check.py
"$learning_python" stage5/program/run_closed_loop.py
"$learning_python" stage5/program/run_closed_loop_summary.py
"$learning_python" stage5/program/run_closed_loop_sampled.py --output stage5/results/closed_loop/sampled_independent_rerun --initial-reference stage5/results/closed_loop/sampled_jacobians.npz
"$learning_python" stage5/program/compare_sampled_versions.py --new-output stage5/results/closed_loop/sampled_independent_rerun
"$learning_python" stage5/program/run_transport_experiments.py --model synthetic --maximum-order 3 --quadratic-through 2 --run-id independent_rerun
"$learning_python" stage5/program/run_transport_experiments.py --model fullcoil_collocated --maximum-order 2 --quadratic-through 1 --run-id independent_rerun
"$learning_python" stage5/program/run_transport_domains.py --run-id independent_rerun --output-id independent_rerun
"$learning_python" stage5/program/run_transport_postprocess.py --run-id independent_rerun
```

`run_closed_loop.py` 先提供同一共点场的两档参考。输运 runner 用新 run-id，已有同名结果会
拒绝覆盖；缓存包含源码/模型/初值指纹。不要复用旧未验证 AD 缓存。
新旧线圈核引起的偏置拟合舍入差另以当前场重新积分量化，见
`results/transport/inverse_verified_reference_bridge.json`：参考轨迹差约 `5.77e−19`，
没有把共享数学定义冒称数值输入逐位相同。
高阶场私有表达改用当前完整 `inv(M(Q))`，原场参考继续走原 `solve` 实现；
两种表达已和独立纯反向高阶方向导数核对。这是实现修复，不是改变物理质量。

新完整复值网络/解析特征/SPD 比较及三维共振部分结果：

```bash
"$learning_python" stage5/program/run_learning_research.py --evaluate-only
"$learning_python" stage5/program/learning_postprocess.py
"$learning_python" stage5/program/learning_coil_reachability.py
"$learning_python" stage5/program/resonance_research.py
"$learning_python" stage5/program/resonance_normalform_pair.py
"$learning_python" stage5/program/resonance_reduce_pair.py
"$learning_python" stage5/program/resonance_verify_partial_scope.py
```

S5-L01 是本轮新训练，包含数据、九份新权重、训练曲线、验证冻结时刻、独立测试/OOD和
Hessian/Legendre 反解检查。`--evaluate-only` 使用保存的新权重。重新训练只在上述独立副本中，
先执行 `mv stage5/results/learning stage5/results/learning_delivered` 保留已交付的整套结果，
再执行 `"$learning_python" stage5/program/run_learning_research.py --steps 1200`。
这会重新生成本轮 S5-L01 实验，不是恢复缺失的历史权重；已有协议时程序会拒绝重训。
算法预算、参数数和函数类差异已声明，不以训练步数相同推断函数类完全公平。

完整空间杆：

```bash
"$rod_python" stage5/program/run_rod_transfer.py --duration .2
"$learning_python" stage5/program/run_rod_transfer_matched.py rom --duration .002
"$rod_python" stage5/program/run_rod_transfer_matched.py rod
"$rod_python" stage5/program/rod_transfer_analysis.py
```

0.2s 主算例保留规定血流、刚性曲管、接触摩擦和合成微重力；独立 2ms 匹配诊断才关闭
双方环境载荷。后者固定偏置在上游节点超梯度限制，明确不是约束合格的控制轨迹。

## 失败与历史成果的身份

- `results/transport/legacy_status.json`、旧 run 和 `legacy_ad_source/` 保留高阶 AD 错误、
  全线圈失败及源码重建校验。重建源码与原记录 SHA 逐字节一致，但明确不是当时同步快照。
- `results/resonance/S5_R02_forward_ad_failed_*` 保留被拒绝的四阶张量/NF；新纯反向结果另存。
- `results/learning/S5_L02_pre_warmfix_*` 保留 72 次分配中的 23 次旧初值失败；新分配未放宽约束。
- `results/rod_transfer/initial_allocator_failure/` 保留分配器回退造成的反常细化结果；
  修复后时间观察阶仍只有约 0.47，控制 RMSE 略差于原基准。
- 复网络负动量 Hessian、SPD 条件数/模型误差及域外失败保持原数值；不以测试通过抹去失败。
- 旧 v10 的非可分 Central4 代码被实际复用；两模态正规形、学习误差、有限幅值环面、
  64 平面自由度和 S 路径证明/实验保留原对象。没有重跑缺资产的旧 S1 证书。

明确缺失的历史路径以 `stage3/source_inputs/starter/stage2/` 为根：
`results/{learning,learning_stress}/complex_seed1025.pt`（及 1026/1027）、
`learning_data.npz/rom_matrices.npz`，`results/learning_spd/{local,stress}/spd_complex_seed1025.pt`，
`results/learning_confirmation/.../frozen/`，以及
`results/learning/feedforward/{linear,analytic,complex,truth}.npz`。
旧 S1 Fourier/Arb/COMSOL 资产等精确列表见第四阶段
`audit/chnn_kam_inheritance.md` 第 7 节。新 S5 权重不代替这些历史文件。

双向 FSI、柔性血管壁、真实生理/微重力标定、有流有接触 ROM 闭合、长期受限控制、
学习补偿进入实际闭环、完整三维共振正规形与新的连续/离散 KAM 证书仍有独立研究责任。
本轮任何小残差、能量下降或局部图精度均不能替代这些证明。
