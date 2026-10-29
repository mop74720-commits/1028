# 冻结模型后的独立确认评估与数据复用防护

## 1. 冻结顺序与范围

2026-10-29，本轮在保持现有修正版网络、训练参数及checkpoint不变的前提下，增加了独立确认集。新增入口是 `stage2/program/learning/run_confirmation.py`，源文件本身、训练时源码快照、ROM源码、共享配置、全部6份复网络checkpoint、两组48特征系数、各自模态矩阵和旧摘要，均先复制并计算SHA。

`stage2/results/learning_confirmation/freeze_manifest.json` 在 **02:34:00.845711 UTC** 写入，早于任何新确认数据生成；其SHA-256为：

`b8587d4e2b28d0c28fa8096dfd80c2de302100e2deb6f4c74df7906b27b64c03`

随后使用唯一新采样种子 **20261030**，按 main/test → main/OOD → stress/test → stress/OOD 的固定顺序生成数据。幅值0.08和0.35各有2048个域内样本、1024个扩大域样本；输入分别均匀分布于24维 $[-1,1]^{24}$ 与 $[-1.5,1.5]^{24}$。标签来自相同的12自由度变质量Kirchhoff ROM。没有重训、调架构、改超参数或按确认误差选择checkpoint；三种子1025、1026、1027全部评估。

每组与旧train/validation/test/OOD的精确行交集均为0，新test与新OOD也无重复。旧结果文件没有覆盖，`evaluation_status.json` 明确将它们保留为开发期探索性评估。

## 2. 数据与运行身份

| 项目 | 文件与身份 |
|---|---|
| 主确认数据 | `results/learning_confirmation/main/confirmation_data.npz`；SHA `6c8bceb1a6a67a59b4c9b72eddf6b455512f21897014b119d462659a32980602` |
| stress确认数据 | `results/learning_confirmation/stress/confirmation_data.npz`；SHA `e80ec3917f0f6345338f1d7d6eb1655606dde4ebc187c84c0bad8bb26cce19c4` |
| 主结果 | `results/learning_confirmation/main/confirmation_summary.json` |
| stress结果 | `results/learning_confirmation/stress/confirmation_summary.json` |
| 冻结权重及来源 | `results/learning_confirmation/frozen/`，逐文件身份在 `freeze_manifest.json` |
| 环境与命令 | `results/learning_confirmation/run_record.json` |
| 完成记录 | `results/learning_confirmation/completion.json`；单线程总耗时约22.04 s |

NPZ键为 `test_x`、`test_h_res`、`test_g_res`、`test_q_raw`、`test_tip_m`，以及相同含义的 `ood_*`。这里 `g_res` 是输入 $x$ 上的无量纲梯度；转回正则变量必须乘 $D=\operatorname{diag}(\sqrt\nu,\sqrt\nu)/a$。

后续SPD等模型家族可以使用这一确认集，但必须在打开标签/结果之前另行冻结其全部模型和训练选择，再作一次评估；不能据此继续调参或选择模型。当前确认清单仅包含本轮冻结的原修正版复网络及48特征、二次基线。

## 3. 新确认集结果

### 3.1 梯度和正则向量场

复网络三种子的最小—最大值如下：

| 幅值与域 | 归一化 $x$ 梯度相对误差 | 正则 $z$ 向量场相对误差 | 原始Ritz广义速度相对误差 |
|---|---:|---:|---:|
| 0.08，域内2048点 | 1.628–1.706% | 1.815–1.950% | 1.841–2.018% |
| 0.08，OOD1024点 | 6.357–6.895% | 4.506–4.720% | 4.560–4.726% |
| 0.35，域内2048点 | 1.852–1.891% | 5.444–6.167% | 5.987–7.883% |
| 0.35，OOD1024点 | 6.752–6.993% | 9.176–10.081% | 10.870–14.223% |

两固定基线的正则向量场相对误差为：主域内二次模型62.537%、48特征62.304%，主OOD分别77.700%、77.137%；stress域内分别97.154%、93.598%，stress OOD分别98.948%、94.624%。这确认该具体小特征库在全相空间域中的表达不足；48与7104实参数、不同损失和不同函数类的比较仍不支持单独的“复数表示优势”。

### 3.2 能量误差

物理能量RMSE已经乘以 $E_0=3.62\times10^{-7}$ J：

| 幅值与域 | 二次基线 | 48特征 | 复网络三种子范围 |
|---|---:|---:|---:|
| 0.08，域内 | $3.8866\times10^{-9}$ J | $2.9714\times10^{-9}$ J | $(6.5142\text{–}6.7407)\times10^{-11}$ J |
| 0.08，OOD | $1.8551\times10^{-8}$ J | $1.3994\times10^{-8}$ J | $(7.8897\text{–}8.7908)\times10^{-10}$ J |
| 0.35，域内 | $1.2853\times10^{-6}$ J | $9.2184\times10^{-7}$ J | $(1.6449\text{–}1.7912)\times10^{-8}$ J |
| 0.35，OOD | $5.8033\times10^{-6}$ J | $4.0711\times10^{-6}$ J | $(2.2829\text{–}2.3821)\times10^{-7}$ J |

这些是冻结模型面对新独立合成样本的经验误差，不是高阶或复域误差界，也不是连续体、实验机器人或闭环精度结论。

### 3.3 12点动量Hessian检查

每个新域用预先固定种子20261031选12点，各模型共享相同索引。主域内三种子的最小特征值约0.5833、0.5641、0.6056；所抽样本全部为正，不能据此认证全域正定。

主OOD的最小特征值约−0.6255、−3.1213、−2.3663，非正数为4/12、1/12、1/12。stress域内最小约−10.6695、−13.7534、−44.8897，非正数为10/12、8/12、9/12；stress OOD三个seed均12/12出现负方向，最小约−234.14、−295.77、−466.83。新独立数据再次支持原审查的限制：一般Hamiltonian残差拟合没有保持正质量结构。负方向也按独立能量二阶差分复核，细节在结果JSON中。

## 4. `--reuse-data` 防护补丁

先保存了未经修改的训练时源码快照：

- `program/learning/run_learning_trained_source.py`
- SHA `8b5c0eb4f8a0c8b7b4b9db2b2330f49809bca10d3d8aeafef1e3b0e9dcfbd6a2`

随后只修改当前 `run_learning.py` 的主入口数据读取防护与相关输出时序：要求既有数据、`learning_summary.json` 和 `rom_matrices.npz` 存在；验证幅值、数据SHA、相空间维数及 $M_0,K_0,S_q,S_p$ 与当前模型逐值相同；不一致立即明确拒绝。原来在读取前覆盖矩阵的写入被移到校验成功以后，以避免损坏旧身份记录。

补丁后源码SHA为 `868de74c224e46082555b5a6553ea70f52a0ee17ec23ed4631fc932e10aecdae`。AST检查证明全部非main函数与类完全相同，包含网络、特征、标签、损失、优化和评分；没有重新训练或覆盖现有结果。记录为 `notes/learning_reuse_guard_patch.json`。

另在复制的隔离输入上检验六种情况：正常身份通过读取后、在训练前主动停止；幅值错误、数据SHA错误、矩阵错误、相空间维数错误、缺失摘要全部明确拒绝，并确认拒绝时已有复制证据文件不变。结果在 `runs/learning_reuse_guard/results.json`。这是I/O身份防护补丁，不是对旧训练算法的数值修订；旧冻结研究使用训练时快照解释其结果。
