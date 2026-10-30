# 第六阶段：双路线融合稿与三维研究的实际贯通

本轮完成了逐章、逐式对照和五组可运行连接，**没有把整个1025研究标为完成**。第五阶段已正确承接 Theorem A/B、原（30）—（36）、变质量中点、非可分 Central4 和完整线圈端口；新增融合稿仍有未进入三维实现的有效内容。本轮补入非自治输运、规范/图缺陷接口、双路线学习预算、完整复网络参考跟踪及电流功率约束。三维 KAM、一般长时多图、含流接触全杆的统一学习控制仍未完成。

先读 [明确结论](final_verdict.md)、[十三节点路线](notes/route_continuity.md) 和 [修复清单](notes/corrections_and_connections.md)。没有改写最终论文。

## 来源和保存

- 源分支 `stage5/unified-3d-repairs`，本轮开始时本地和远端一致：`1c73a580441200d6594e2a2a96374edc1c0e98e6`。
- 研究分支 `stage6/fusion-reconciliation`。
- 实际 ZIP：`stage3/source_inputs/v10/v10_birkhoff_20261028_no_fonts_for_github.zip`，7,473,699 bytes，430个条目全部CRC通过。
- SHA-256：`416bdb3c8337816c9ef041bcaa5d5a4b8a8276c6d7be6172e37a0dec0dd9ec7f`。
- 原始临时解压：`/tmp/1028-stage6-fusion-q4idpcer/v10_birkhoff_20261028`。全部条目SHA见 `results/materials.json`。复算入口会重新核验并在需要时创建新的临时解压，原始清单不覆盖。
- 包内所称41MB含字体原包未取得，其SHA仅为来源声明。当前包没有补回原S1/第二阶段权重、Fourier/Arb/COMSOL原数据；科学数组只有一个两模态收敛NPZ。
- 历史1133个受版本管理文件最终逐字节核验。两个旧测试首次回写了耗时，已保存本次输出、恢复原字节并改为隔离副本重跑；详情 `results/tests/legacy_side_effects/restoration.json`。环境草稿不提交。

## 对照入口

|文件|内容与证据边界|
|---|---|
|`full_comparison.csv`|582个显示公式、命题/定理块和表格的精确源行、原label、原1025 OMML锚点、各阶段代码/证明/实验及六层继承状态；不是582个独立新定理|
|`chapter_coverage.csv`|46个中英章节文件及周边假设/证明的阅读位置；无显示公式的章节也有解释|
|`chapter_source_comparison.csv`、`results/source_diffs/`|与旧framework的逐章文本差异、SHA和标签变化|
|`results/manuscript_index.json`|原生TeX数学块；另有4464个行内数学上下文锚点，不能把索引覆盖当证明认证|
|`annotations/*.json`|逐式人工数学判断原记录；`program/reconcile_index.py`检查无缺项/重复并生成总表|
|`notes/*_reconciliation.md`、`proofs/`|一般Birkhoff、算法、KAM预算、物理及历史五项完整分析与新增推导|
|`results/`|实际执行数据、源SHA、日志、失败和参数；旧历史结果与本轮新数据明确分开|

旧A/B完整证明直接保留于 `stage5/proofs/corrected_mathematics.md`，没有用摘要替代。中央四阶完整混合导数及理想 exact-symplectic 原函数直接沿用 `stage5/proofs/integrators_full_coil.md`。新证明只补尚缺的接口。

## 已实际运行的主要结果

|工作|结果|证据|
|---|---|---|
|旧45项测试＋新28项测试|隔离复测全部通过，12模块；不表示全研究完成|`results/tests/latest_all.json`|
|融合G1/G2/G3|56个方法/网格通过；端点误差与原数据最大差4.96e−17|`results/algorithms/fusion_original/`|
|原历史六入口与双路线正规形预算|六入口通过、11873数值字段一致；12项预算量一致|`results/history/fusion_original_reproduction/`、`results/budgets/`|
|非自治完整线圈高阶输运|正确r2表示误差呈二阶；遗漏显式时间力项则一阶；同场中点/图法约二阶|`results/algorithms/time_gain_r2_completed.*`|
|规范和图误差|B=H前后场保持，但原场误差非零；完整图缺陷分解余差6.66e−16|`results/theory/S6_THEORY02/`|
|三维冻结机械学习模型|8749项×3种子实际解析预算；小域Legendre精确有理下界约0.242–0.250|`results/budgets/actual_3d_*`|
|完整复网络参考＋真实线圈跟踪|变质量加速度恒等式4.48e−14；端口秩5，分配残差0.136–0.147保留|`results/history/S6_T01/`|
|三维能量几何界＋电流功率约束|6条实际全线圈轨迹；最细能量功账残差6.26e−11 E0|`results/physics/`|

完整域失败、报告层Python错误、较大域充分界失败、不可达/电流速率冲突均保留；详见 `notes/reproduction_and_failures.md`。不同实验的分支、初态和控制不同，不能将其成功拼为一个全闭环定理。

## 复算

本机学习环境：Python3.12.14、NumPy2.3.5、SciPy1.17.0、Torch2.5.1+cpu、SymPy1.13.1、Matplotlib3.10.8。旧杆测试另用 PyElastica1.0.0、Numba0.62.1；与学习环境分离。无需本轮新训练，读取已有S5新实验权重。数值运行采用单线程，常规实计算float64、复网络complex128；指定代数预算另用精确有理数或高精度。具体容差在每个结果JSON和测试代码中。

在提交后的新工作树复算，可保持本次交付结果原样。部分结果生成器有固定输出路径，因此完整重算应使用独立工作树：

```bash
REPRO_DIR="$(mktemp -d /tmp/1028-s6-recheck.XXXXXX)"
git worktree add --detach "$REPRO_DIR" HEAD
cd "$REPRO_DIR"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
S6_PY=/workspace/1028-cloud/venvs/learning/bin/python
S6_ROD_PY=/workspace/1028-cloud/venvs/rod/bin/python

"$S6_PY" stage6/fusion_reconciliation/program/materials.py --extract-only
"$S6_PY" stage6/fusion_reconciliation/program/run_tests.py --suite all --learning-python "$S6_PY" --rod-python "$S6_ROD_PY"
"$S6_PY" stage6/fusion_reconciliation/program/reconcile_index.py
"$S6_PY" stage6/fusion_reconciliation/program/run_fusion_algorithms.py --run-id fusion_recheck
"$S6_PY" stage6/fusion_reconciliation/program/history_reproduction.py --python "$S6_PY" --run-id history_recheck
"$S6_PY" stage6/fusion_reconciliation/program/fusion_budget_run.py
"$S6_PY" stage6/fusion_reconciliation/program/run_fusion_theory.py --run-id S6_THEORY_recheck
"$S6_PY" stage6/fusion_reconciliation/program/run_nonautonomous_experiment.py --run-id time_gain_recheck
"$S6_PY" stage6/fusion_reconciliation/program/run_nonautonomous_domain.py --run-id domain_recheck
"$S6_PY" stage6/fusion_reconciliation/program/run_learned_reference_tracking.py --run-id S6_T01_recheck
"$S6_PY" stage6/fusion_reconciliation/program/verify_tracking_refinement.py --run-id S6_T01_recheck
"$S6_PY" stage6/fusion_reconciliation/program/run_fusion_physics.py
"$S6_PY" stage6/fusion_reconciliation/program/verify_fusion_physics_results.py
"$S6_PY" stage6/fusion_reconciliation/program/materials.py --verify-frozen
```

换机器时将两个解释器路径改为相应环境；依赖版本见 `results/environment.json`。单独新测试可运行 `run_tests.py --suite current`。完整非自治原生AD/双参考最耗时，本次为分钟量级；成本记录包含失败与恢复，不能只引用热缓存步进速度。

原始结果的配套后处理 `verify_tracking_refinement.py` 默认针对 `S6_T01`，复算时使用上述相同的新 `--run-id`；它不是新训练入口。无字体包的中文TeX仍引用移除字体，本轮读取原生TeX及已有PDF，没有声称重新编译论文。
