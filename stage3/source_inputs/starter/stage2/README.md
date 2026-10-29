# 1025 / v10 第二阶段可复算研究包

本包对应《1025_v10_第二阶段融合研究报告》。完整研究对象仍为三维血管内磁驱动柔性机器人。本轮实际实现三维 Cosserat 杆、独立 12 自由度 Kirchhoff 分析模型、脉动规定血流、接触摩擦、受限磁端口、完整复网络与一般 Birkhoff 数值验证。双向流固耦合、柔性血管壁、实物标定和新三维 KAM 证书尚未完成。

## 目录与证据

所有命令从**含有 `stage2/` 的解压根目录**运行。

| 位置 | 内容 |
|---|---|
| `stage2/program/rod3d/` | 三维杆、算子、稳定与失败控制、完整 Biot–Savart、工作域受限分配、连续电流斜坡、Womersley 分支 |
| `stage2/program/learning/` | 变质量三维 ROM、完整复网络、解析基线、独立确认、正质量网络、磁前馈 |
| `stage2/program/route_a/` | 8／16 自由度变质量、中点、中央生成函数、一般输运／Moser 与原包复算 |
| `stage2/program/coil_field.py` | 12 个圆线圈的几何、局部场矩阵和电流分配 |
| `stage2/program/metriplectic_candidate.py` | 扩展内能状态、退化条件及熵产生检查 |
| `stage2/results/` | 本轮真实输出，含数据、训练权重、完整轨迹、失败记录、图和运行日志 |
| `stage2/notes/` | 版本与 ZIP 摘要、分方向详细记录、学习独立审计 |
| `stage2/evidence_v10/` | 原 v10 重算输出与日志；不重新分发上游仓库或原 S1 数据包 |
| `stage2/paper/` | 共享公式、符号、文献、主张清单和中英文可扩写框架源码 |
| `stage2/report/` | 报告源、组装程序和版式核查记录；PDF/DOCX 另附 |
| `stage2/delivery_manifest.json` | 逐文件字节数与 SHA256；用于检查交付完整性 |

报告章序：2—3 为版本／1025继承，4 为原 v10（1）—（19）及后半段，5 为三维方程，6 为实际物理计算，7 为方向 A，8 为方向 B，9 为 Metriplectic，10—11 为后续任务与文献。每项数值均应随其模型范围引用。

## 软件环境

实际计算采用 Python 3.12。旧 v10／方向 A 与新学习／三维杆采用独立环境，避免不兼容的 NumPy、Numba 和 Arb 依赖。原输出的 `environment.json`、运行 JSON 和训练摘要保留实际版本及代码哈希。下载的 wheel、虚拟环境和编译缓存没有打包。

```bash
python3.12 -m venv stage2/env_route_a
stage2/env_route_a/bin/python -m pip install -r stage2/requirements_route_a.txt
python3.12 -m venv stage2/env_learning
stage2/env_learning/bin/python -m pip install -r stage2/requirements_learning.txt
stage2/env_learning/bin/python -m pip install torch==2.5.1+cpu --index-url https://download.pytorch.org/whl/cpu
python3.12 -m venv stage2/env_rod
stage2/env_rod/bin/python -m pip install -r stage2/program/rod3d/requirements.txt
```

本轮用于计时的主要运行把 BLAS 和 OpenMP 固定为单线程。下列设置只影响当前终端：

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMBA_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
```

耗时依赖硬件、首次编译、准备成本及负载；不能把热启动时间与另一个方法的全部准备时间直接比较。各 JSON 区分冷／热成本。不同 BLAS 后端可能改变浮点末位，冻结证书／确认集的严格输入断言若失败，应核对环境与输入身份，不应关闭检查并沿用旧证书名称。

## 先复核已交付结果

先运行清单校验，而不是训练覆盖原结果：

```bash
python3 stage2/verify_delivery.py
stage2/env_learning/bin/python stage2/program/learning/validate_rod_rom.py
stage2/env_rod/bin/python stage2/program/rod3d/verify_operators.py
stage2/env_learning/bin/python stage2/program/metriplectic_candidate.py
```

`verify_delivery.py`只读交付文件。后续实验入口会写入其结果目录，建议在独立解压副本中复算；本次冻结输出可由原压缩包恢复。新的运行耗时、绝对路径和时间戳本来就会变化，不能要求它们逐字节相同。

## 方向 A：原36、变质量和一般图

```bash
stage2/env_route_a/bin/python stage2/program/route_a/run_extended.py
stage2/env_route_a/bin/python stage2/program/route_a/transport_moser_check.py
stage2/env_route_a/bin/python stage2/program/route_a/build_summary.py
stage2/env_route_a/bin/python stage2/program/route_a/plot_results.py
```

新算例的具体初态、时间范围、非比例阻尼、两个磁势端口与误差范数在 `notes/route_a.md` 和代码中。已知点变换产生的变质量试验不是任意真实杆 Birkhoff 图的证明。`transport_moser_check.py`刻意分别测量图匹配、原场表示误差和准备成本；机器精度结构缺陷并不意味着动力学准确。

若重跑用户原 ZIP，先验证原始压缩包，再提取到代码所需的目录：

```bash
python3 stage2/prepare_inputs.py --birkhoff '/实际路径/一般Birkhoff_推导与验证材料.zip' --latest '/实际路径/v10_英文中文整合源码与复算包.zip'
stage2/env_route_a/bin/python stage2/program/route_a/replay_supplied.py
```

`--older`为较早后缀（2）整合包的可选核对入口。准备程序验证整包与每个条目的 SHA256，拒绝路径穿越、软链接或覆盖不匹配的已有源目录。当前整合版本与旧副本不同；哈希不匹配时应先做新版本核查。

## 三维 Cosserat 杆及磁、流、接触

```bash
stage2/env_rod/bin/python stage2/program/rod3d/run_study.py --resume
stage2/env_rod/bin/python stage2/program/rod3d/failure_study.py
stage2/env_rod/bin/python stage2/program/rod3d/run_wall_sensitivity.py
stage2/env_rod/bin/python stage2/program/rod3d/run_learning_comparison.py --resume
stage2/env_rod/bin/python stage2/program/rod3d/run_womersley.py
stage2/env_rod/bin/python stage2/program/rod3d/run_biot_savart.py
stage2/env_rod/bin/python stage2/program/rod3d/run_biot_savart_constrained.py
stage2/env_rod/bin/python stage2/program/rod3d/run_biot_savart_ramped.py
stage2/env_rod/bin/python stage2/program/rod3d/analyze.py
```

`--resume`只接受满足相应身份检查的已有算例；在交付副本上使用它主要用于核对／补齐，不会强行重新积分所有已完成项。要实际重算某项，使用另一份解压副本并把目标结果目录移走，或以 `model.py --name 新名字 ...` 指定独立输出。单例64段入口和完整参数含义见 `program/rod3d/README.md`。

16／32／64**空间段**对应93／189／381个自由配置变量，不能写成64个模态。常用终时2 s、步长10／5／2.5 µs。位置反馈采用 `config_position_feedback.json`；`config.json`保留初次非共点速度反馈失败配置。不能用失败配置冒充已接受的主表。

“coil_allocated”局部仿射场、完整 Biot–Savart 场、采样管域约束场是三个独立模型。前两个包含实际场／梯度越界的反例。ZOH电流只满足相邻样本差商限制，连续分段线性分支才满足几乎处处的连续电流速率限制。387点场约束不是连续空间的严格上界。Womersley 分支保持同一平均流量；沿弯管映射仍不是双向FSI。

## 方向 B：完整复网络和独立确认

实际修正网络每种子训练6001次更新（`--steps 6000`含索引0）。在新的输出目录生成一组重算结果：

```bash
stage2/env_learning/bin/python stage2/program/learning/run_learning.py --output stage2/results/recomputed_learning --amplitude .08 --steps 6000 --seeds 1025 1026 1027
stage2/env_learning/bin/python stage2/program/learning/run_learning.py --output stage2/results/recomputed_stress --amplitude .35 --steps 6000 --seeds 1025 1026 1027
stage2/env_learning/bin/python stage2/program/learning/evaluate_models.py --folders stage2/results/recomputed_learning stage2/results/recomputed_stress
```

正式交付目录 `learning`、`learning_stress`、`learning_initial_meromorphic`保存原训练数据、日志、系数和每个检查点。`run_learning_trained_source.py`是训练时的精确源码快照；当前 `run_learning.py`只在入口增加数据复用身份检查，科学模型／训练函数没有改变。`--reuse-data`验证域、数据SHA和正则图，避免复用另一幅值的标签。

```bash
stage2/env_learning/bin/python stage2/program/learning/run_confirmation.py
stage2/env_learning/bin/python stage2/program/learning/train_spd_complex.py --data-dir stage2/results/learning --output stage2/results/recomputed_spd_local --steps 6000 --seed 1025
stage2/env_learning/bin/python stage2/program/learning/train_spd_complex.py --data-dir stage2/results/learning_stress --output stage2/results/recomputed_spd_stress --steps 6000 --seed 1025
stage2/env_learning/bin/python stage2/program/learning/evaluate_spd_confirmation.py
```

独立确认入口使用 `learning_confirmation/frozen/`中的冻结模型和协议，不会把另一次重训自动冒充该确认实验。正质量确认入口评估已交付冻结的 `learning_spd/{local,stress}`；新重训目录应另行冻结并明确登记后评估，不能覆盖原确认集协议。

正质量网络通过 (C=LL^T) 修复动量 Hessian 正定性，但本轮大幅域拟合失败且条件数严重恶化。它不是比无约束网络更精确的结果。无约束网络的域外负曲率反例也保留。所有标签来自三维ROM，无实测学习数据，无新系统的KAM误差证书。

```bash
stage2/env_learning/bin/python stage2/program/learning/make_feedforward.py
stage2/env_learning/bin/python stage2/program/plot_learning.py
```

前馈入口按验证集选择既有检查点，输出4种模型的同一磁场接口。`run_learning_comparison.py`已将它们真正施加到32／64段杆，包含血流和接触；结果不支持该慢小幅任务中神经模型优于线性先验。

## 原 v10 的独立复算

原仓库：<https://github.com/mop74720-commits/IJRR_CHNN_KAM_v10_20261007>。本轮main提交为 `8761d70239a54985b40c0a6196f52e53d5b2e4d2`，标签提交 `82519542dd057e8fbd6d6879ef33217761e8cbbb`。主文和补充材料采用原正式 S1 发布包，其完整 SHA256、入口、参数、文件对应和命令见 `notes/v10_baseline.md` 及 `evidence_v10/`日志。

本包不重复分发原 Git 仓库或909 MB的解压S1。需从原库获取同一提交和S1后，将运行JSON中的源根替换为本地对应目录；不要替换科学输入。原积分与环面证书使用冻结权重及256／512-bit Arb。原证书只针对原冻结保守模型。新三维参数、非零学习误差、接触和受限磁输入不在该证书范围内。

旧12次实／复读出重训、96条验证轨迹、Central4误差、64平面自由度提升、S形跟踪已实际重算。S2的1715个矩阵是独立特征值复核，不是1715次重新积分；净空治理器的长积分中止记录保留。没有完成原COMSOL原生重算、全部长扫参和全部高幅值环面复证。

## 写作、报告和可证结论

`paper/`共享公式而分开A／B主张；编译说明由该目录README给出。报告使用可编辑Word公式。报告正文组装需 Python-docx、Pandoc、中文字体；PDF预览还需LibreOffice。若只复算科学结果，不需要文档工具链。

允许直接引用的结论必须带上对象和证据，例如“16自由度合成变质量系统上观察四阶”“32／64段规定血流模型上的有限时间跟踪”“旧冻结保守Hamiltonian的区间证书”。轨迹、FFT、抽样正定性、低结构缺陷、低能量残差均不自动升级为一般收敛、稳定、无穿透、临床安全或KAM存在性结论。
