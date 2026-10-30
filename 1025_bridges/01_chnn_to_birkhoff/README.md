# 1025桥接01：CHNN → 同一动力学对象 → Birkhoff

基于远端 `stage6/fusion-reconciliation` 的实际HEAD `2b774acf2a76aefbe732c649a1f02d0fafea3b79`，独立分支 `bridges/01-chnn-to-birkhoff`。所有新代码、推导和结果只写本目录；1351个既有版本文件逐字节保持。环境草稿不提交。

本轮不训练网络、不改模型参数、不设计线圈、不做KAM/FSI，也不自动进入下一桥。最小实现直接复用S5/S6网络、真实12自由度ROM、既有光滑载荷、Lie递推和缓存，只修复一般学习Hamiltonian不能使用机械二次捷径的问题，并加入独立误差分解。

阅读顺序：

1. [原稿本意及逐式分类](original_intention.md)：原12、15–28及Birkhoff入口的OMML位置。
2. [已有成果](existing_results.md)：可以直接继承、跨对象需修正、未认证。
3. [必要数学连接](mathematical_bridge.md)：共同对象、精确保守表示、局部一般表示及三个误差。
4. [最小修订](minimal_revision.md)：原文应改的公式与最少解释。
5. [八个问题的验收结论](final_verdict.md)：明确成立域、实际结果与剩余条件。

## 主要实证

- 原有seed51001完整复网络，目标是 `H_ideal` 的保守残差。512个test和256个OOD点重算，场误差与S5一致。
- 保守Birkhoff对学得场精确；已有一般光滑载荷下，新适配器实际生成r1/r2一形式、闭二形式、表示场和相容性诊断。
- `B01_run03` 是最终报告：原场/学得场/表示场分别积分、双容差及最大步长核验，明确分开学习误差和表示误差。
- 负Hpp、共享R对学得能量正功、旧机械a1捷径错误、复AD后端失败均保存。
- 最终11项新增＋10项继承回归通过。没有通过调低容差或改变物理对象消除负结果。

## 复算入口

本机使用 Python3.12.14，NumPy2.3.5、SciPy1.17.0、Torch2.5.1+cpu，实计算float64、复网络complex128。精确缓存非退化界单独使用标准库Fraction；它只对应保存的点多项式，不是全网络误差证明。执行后仍核对冻结文件SHA。

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
BRIDGE_PY=/workspace/1028-cloud/venvs/learning/bin/python
"$BRIDGE_PY" 1025_bridges/01_chnn_to_birkhoff/program/verify.py
"$BRIDGE_PY" 1025_bridges/01_chnn_to_birkhoff/program/check_frozen_network.py --run-id network_recheck
"$BRIDGE_PY" 1025_bridges/01_chnn_to_birkhoff/program/run_bridge.py --run-id B01_recheck
```

从仓库根执行。换机器时更改解释器路径；不需要缺失的原S1权重，读取仓库已有S5新训练权重。已存在的实验编号会拒绝覆盖；再次执行时换新编号。网络检验本次约2.3秒，主桥接约29秒；机器不同耗时不同。容差、初值、源哈希及每个场的成本保存在JSON。

`verify.py` 只运行新桥接测试及两个已确认无结果回写的旧测试模块；不调用会回写历史目录的旧总入口。独立原生OMML核对的节点/XML和复现说明在 `results/original_omml.json`。

## 结果身份与失败保留

|路径|身份|
|---|---|
|`results/provenance.json`|实际起始HEAD、分支、全部1351个冻结文件SHA|
|`results/network_checks.json/.npz`、`network_power_witness.json`|未重训的独立冻结网络检验；Hpp、梯度、功率与负样本|
|`results/network_checks_failure01.*`、`network_interface_tests_failure01.log`|PyTorch复共轭默认vmap不支持的真实失败；后改逐行反向求导|
|`results/B01_run01/`|数值成功，但元数据继承了S5机械重建和S6线圈plant标签，不用其标签解释本轮对象|
|`results/B01_run02/`|元数据已修正；缓存Hessian仍保留舍入级反对称，最终版进一步恢复旧采样器的检查后对称化|
|`results/B01_run03/`|最终代码完整重跑；保存raw Hessian及其反对称量，严格对称缓存、真实全部轨迹与残差|
|`results/latest_verification.json`|最终测试、环境、命令、源SHA、冻结保护及日志|
|`results/execution_notes.json`|运行修订原因；区分程序限制、元数据问题和数学负结果|

没有覆盖上述早期运行。对称化只处理已经核验的约1e−15级反对称舍入，原始张量仍在NPZ中；没有掩盖高阶导数错误。一般Birkhoff实现的时间截断残差非零，其实际表示场与学习场仍不同。这里不存在一份已完成的最终论文。
