# 实际执行、失败与保存

## 环境和命令

所有命令从仓库根运行，Python3.12.14。学习/微分/数值环境与PyElastica杆环境分离，具体版本见 `results/environment.json`。OMP/MKL/OpenBLAS/Numba均为1线程，关闭pyc写入。各实验结果包含本次命令、物理参数、初态、源SHA、容差和成本。入口在README；已有输出保护的程序必须给新run-id。

最终统一命令为：

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
 /workspace/1028-cloud/venvs/learning/bin/python stage6/fusion_reconciliation/program/run_tests.py --suite all
```

2026-10-30 07:06:05–07:07:45 UTC，12模块全部通过，旧45项＋新28项。逐命令、耗时、环境路径、源SHA、stdout/stderr在 `results/tests/20261030T070604_635392Z/` 和 `latest_all.json`。这只是所测试责任的证据，不是研究完成度。

|模块组|项数|实际状态|主要责任|
|---|---:|---|---|
|旧closed_loop/coil_interface|11|通过|真实完整线圈与完整反馈Jacobians|
|旧corrected_identities/high_derivatives|22|通过|E项修正、A/B递推、原36、规范/非交换顺序、高阶导数|
|旧learning/rod/transport_moser|12|通过|冻结S5新训练、杆端口、真实高阶输运与数值图|
|新fusion_budget|10|通过|两路线、精确机械Legendre充分域、特征主控、共振拒绝|
|新fusion_physics|5|通过|三维几何能量、固定电流功率、功率半空间及不可行例|
|新fusion_theory|4|通过|物理H规范、形式自伴算子、完整图缺陷恒等式|
|新learned_reference_tracking|4|通过|完整网络参考、变质量加速度及实际电流残差|
|新nonautonomous_transport|5|通过|f_t与b2、自治回归、真实Jacobian、相容性及局部域拒绝|

## 实验复算与数值标准

- 原G1–G3：源副本运行原 `run_all.py --timing-repetitions 3`，19.020s，56行结果通过原断言，误差新旧差≤4.96e−17。保留原真实计时，未强求不同机器毫秒数相等。
- 历史六入口：0.995/31.392/64.166/81.459/0.109/13.756秒，全部退出0；11873非运行时数值字段按 `1e−12+1e−9 max(|a|,|b|)`比较一致。这是结果比较容差，不改变原求解器2e−14残差标准。四个framework JSON及NPZ输出与原数据逐字节相同。
- 原双路线预算：直接执行原有理同调算法，12项主控/余项/扭转量以 `rtol=5e−13,atol=1e−30` 对照一致。仍是两模态小域，不是新3D证书。
- 非自治同场：原场和表示场各用两套DOP853参考 `(rtol,atol,max_step)=(2e−10,2e−12,T/4)`、`(5e−12,5e−14,T/8)`，参考细化差2.10e−17/1.29e−17。隐式容差2e−13，实际最大完整增量残差5.37e−14；没有降低标准。r2缓存空间误差与时间误差分别核验。8步普通/图法耗时23.804/39.644s，另有原生AD、双参考及域检查成本。
- 理论两分支：18.174/41.897s，使用S5缓存及首步轨迹，但重新计算规范、完整场导数、Moser与时间敏感度。不是整条旧轨迹重新积分。
- S6-T01：读取S5完整复网络，真实电流积分；参考RK4/DOP853差9.36e−12。第一次仅紧容差参考恰好走相同步序，浮点差0，明确保留；另缩小最大步长得到1.05569e−14。不能用“零差”声称精确解。
- 功率约束器：两支路×三时间细化共6次实际积分，总约50s；粗网格功账误差约5.85e−8高于设置的1e−8储备，不能以粗结果宣称能量阈值验证。最细为6.26e−11 E0。全21节点中心线和SO(3)另从保存轨迹独立重算。

## 真实失败和不可推论

|类别|具体证据|处理与结论|
|---|---|---|
|报告层程序错误|`results/theory/S6_THEORY01.log`和JSON：NumPy布尔序列化失败|修复标量转换，新编号S6_THEORY02重跑；未变容差/物理|
|报告层程序错误|`results/algorithms/time_gain_r2.json/.log`：字典重复steps参数|保留失败；新completed运行只复用指纹一致的已完成双参考/点诊断，重新积分所有网格|
|报告层程序错误|`results/algorithms/time_gain_domain.log`：NumPy布尔序列化|修复报告函数，completed重新运行五个窗口，不把程序错当动力学失稳|
|实际局部图越域|`time_gain_domain_completed.json`：τ=.5和2|辅助轨迹越声明球半径.002而拒绝；.05成功也不说明时间截断准确|
|解析充分界失败|`actual_3d_exact_learned_legendre_bounds.json`：归一化Q半径.1|保留失败，不把充分界失败当已找到负Hessian；S5实际负样本另保留|
|执行器不可达|`history/S6_T01/results.json`：秩5、请求残差.136–.147|实际施加受限电流，未注入不可达力；无无条件理想跟踪证明|
|速率约束使功率集合不可行|`physics/independent_diagnostics.json`|解析盒下界和求解器拒绝同时保存；不能假定任何时刻零输入可行|
|物理/理论前提缺失|双路线budget的uniform error null、KAM false|不填造缺失Gram/复域/真实误差/定理阈值；历史权重缺少明确列路径|

## 冻结证据保护的纠正记录

最初统一测试runner误以为旧测试只读；`test_closed_loop.py` 与 `test_rod_transfer.py` 的 `tearDownClass` 会写固定结果路径。实际差异仅两处耗时。已将本次输出和前后SHA保存于 `results/tests/legacy_side_effects/`，按本轮开始HEAD恢复原文件全部字节。随后修改的runner在独立临时树复制stage3/4/5执行，产生输出只收集到stage6，最终45旧项全部重新通过。

该问题不隐去、不篡改历史计时、不混为数值失败。最终 `results/frozen_preservation.json` 核对1133个旧版本文件保持本轮开始字节。新包解压源也经430项SHA再次确认；原历史材料和原结果不纳入本次改动。
