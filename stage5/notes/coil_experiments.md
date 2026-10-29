# 全线圈接口与实际受限闭环：执行记录

所有新增文件位于stage5；旧v10、stage2、stage3及stage4证据未改动。核心模块 `program/coil_rom.py` 直接继承实际12自由度三维几何ROM，默认20空间单元、每圆线圈256求积点。圆线圈物理、场导数与第二阶段一致；这里新增可高阶自动微分的全磁能与全电流端口，不再把原点8场参数当完整空间线圈力。

## 1. 可复算命令与接口

仓库根目录执行：

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
/workspace/1028-cloud/venvs/learning/bin/python stage5/tests/test_coil_interface.py
/workspace/1028-cloud/venvs/learning/bin/python stage5/program/run_coil_validation.py
/workspace/1028-cloud/venvs/learning/bin/python stage5/program/run_coil_closed_loop.py
```

可导入 `CoilROM`，保持 `z=(Q,P), τ=ω₀t`。主要接口：

- `hamiltonian_tensor(z,currents,model='full')` 与 NumPy标量版 `hamiltonian`。
- `field_tensor/field(z,currents,gamma=0,model='full')`：物理偏导保持电流固定。
- `jacobian`：固定输入场Jacobian。
- `current_port_tensor/current_port(Q)`：12×12真实电流广义力映射。
- `collocated_current_tensor`、`feedback_field_tensor`、`feedback_jacobian`：完整状态反馈导数。
- `physical_samples(Q,i)`：实际磁积分点的全场、全梯度和到精确圆导线距离。
- `model='affine'`：相同电流、相同原点场/梯度的局部展开，只作为公平近似对照。

`coil_control.CurrentAllocator.allocate_force` 在真实广义力空间分配；`allocate` 是共点电流请求的投影，两者明确区分。`bias_currents` 是已建立的总偏置电流，最大1.5124804024A；本轮没有伪称验证零电流启动的斜率过程。

## 2. 独立接口验证：实际执行通过

`results/coil/interface_tests.log`：5项测试通过，覆盖能量/端口/偏置一次性计账、Maxwell与解析梯度、反馈偏导和完整链式求导、连续电流约束、不可达力残差。没有降低旧容差。

`results/coil/validation.json`、`validation_arrays.npz`、`validation.log`：实际运行约19.82秒，保存环境、源码SHA和各项容差。

| 检查 | 实测 |
|---|---:|
| 独立几何虚功与AD磁力差 | 5.78e−16 |
| 12方向磁能中心差分误差，步长2e−6/1e−6 | 2.94e−10 / 7.30e−10 |
| 绝对SI轴上圆环场闭式误差 | 3.01e−16 |
| Maxwell散度/旋度缺陷 | 9.00e−18 / 1.23e−17 T/m |
| 128/256/512线圈积分的力变化 | ≤5.70e−16 |
| 正确反馈Jacobian方向差分误差 | 2.39e−9 |
| 错误计算 `J∇H(z,i(z))` 的场误差 | 5.4730 |
| 忽略 `Di/Dz` 的Jacobian谱范数差 | 12.5649 |

同一物理Ritz系数q、统一投回20单元Q基的空间检查：

| 空间单元/磁点 | 全场相对仿射力差 | 真实12电流端口秩（相对阈值1e−8） |
|---|---:|---:|
| 20 / 1 | 0.985236 | 5 |
| 40 / 2 | 0.985979 | 7 |
| 80 / 4 | 0.986183 | 7 |

全力20→40差0.00586672，40→80差0.00145763。这是公共位形/公共坐标的空间诊断，没有把20单元说成已空间收敛；真实12电流全空间场比原8参数仿射接口有不同秩，但仍秩亏。

独立的真实广义力目标 `d=.2P`，在相同Q、i_previous=i_bias、物理Δt=0.1ms下：

| 目标放大 | 正交不可达残差 | 受限后力残差 | 最大连续斜率 |
|---|---:|---:|---:|
| 1 | 2.65530e−4 | 4.01583e−4 | 20 A/s |
| 10 | 2.65530e−3 | 5.00641e−3 | 20 A/s |
| 100 | 2.65530e−2 | 7.30564e−2 | 20 A/s |

残差包括真实执行器不可达性和约束，而不是把任意相空间增量解释成磁输入。

## 3. 真正重新积分的闭环，非轨迹重放

`results/coil/closed_loop_trajectories.npz` 保存每个实际状态与总电流；每支对应 `*_details.json` 包含控制分配、逐RK阶段真实B/G/功率/导线距离及能量节点。汇总为 `closed_loop_summary.json/.csv`，日志 `closed_loop_run.log`。

共同条件：同一材料/质量函数、初态 `initial_state(.01)`、预通电偏置、γ=.2、共点增益κ=.1542504562、电流±2A、斜率20A/s、场5mT、梯度.03T/m。时间 `τ∈[0,.004]`，即0.89733794ms，8次控制更新；每区间分别1/2个RK4子步，得到8/16步两网格。每个RK阶段用**该轨迹实际位形及实际电流**重新计算全线圈力。

前三支比较同一反馈结构的全场/仿射差；第四支是同真实全场上的受限力补偿政策，目标 `.2P`。控制器各自闭合到其真实状态，不共享或重放另一轨迹。

| 植物/控制 | 16步耗时/s | 8→16最大状态差 | 总能量—功率残差 | 最大电流/A | 最大连续斜率A/s |
|---|---:|---:|---:|---:|---:|
| full / full共点 | 20.75 | 7.22063e−8 | −6.24566e−11 | 1.51251 | 13.1466 |
| affine / affine共点 | 20.46 | 7.22054e−8 | −6.24653e−11 | 1.51270 | 13.2372 |
| full / affine共点 | 20.94 | 7.22063e−8 | −6.24561e−11 | 1.51251 | 13.2372 |
| full / 受限广义力阻尼补偿 | 22.61 | 7.22068e−8 | −6.24576e−11 | 1.53043 | 20.0000 |

机械能账的残差同样约−6.25e−11；总H的输入功是 `φᵀdi/dτ`，机械H的磁功是 `vᵀG i`，没有把两种能量/外功混用。8步功率残差约−1.97e−9；只有两层网格，不据此报告严格实际收敛阶。积分器阶数研究由统一闭环模块另行执行。

16步下，`full/full` 与 `affine/affine` 最大状态差 **3.90705e−4**，显著大于本轮粗细差，表明实际力模型改变了轨迹。`full/full` 与 `full/affine` 仅 **7.17555e−8**，与当前积分误差同量级，不能声称本窗口已分辨出全场控制设计的精度收益。这个负面/分辨率结果保留，不因新的控制程序而宣布控制必然更优。

实际RK阶段磁点场最大不超过0.501325mT，梯度不超过0.00431404T/m，检查点无超限；距精确圆导线最小约76.60mm。电流的连续幅值/斜率界可由线性斜坡证明，场/梯度只在已检查的实际磁点和时刻有数值证据。未声称整杆或整个血管工作域、连续空间与所有中间时刻均通过认证。

受限补偿支路确实激活20A/s限制，最大力分配残差约4.01416e−4，不能实现全部阻尼抵消。其总能量变化约0.0123主要包含电流变化引起的磁势参数功，不应误当机械能激增；机械能变化约2.90e−7，两种功率账均已保存。

## 4. 与原研究路线的连接及限制

这轮把第三阶段“全线圈能量点审计”的缺口推进到可高阶AD的真实磁场模型与实际闭环；保留其揭示的大仿射力误差。接口供原（36）/中点/Central4/合法阻尼图及完整CHNN误差的实际可达性研究共用。实际场 Jacobian 包括完整反馈导数；受限采样闭环的36维含电流记忆映射另审，不将其叫作自治24维保辛更新。

证明 `proofs/coil_energy_ports.md` 明确固定电流与反馈、无约束耗散律与受限延迟律的区别。光滑共点反馈的负功率证明不自动适用于受限采样器，也不构成KAM。空间误差、长时间跟踪、全域线圈界、真实硬件校准、血流/接触投影、双向FSI和柔性壁仍分别待完成。最终目标继续是空间站血管内三维柔性磁机器人。

## 5. 高阶AD与分配器修复：源版本和真实重跑边界

首次8个闭环及 `validation.json` 使用 `coil_rom.py` SHA `53004846…` 与 `coil_control.py` SHA `9df4995b…`，结果保持不动。后续 Birkhoff 全系数高阶自动微分暴露 PyTorch 2.5.1 的 `vector_norm` 混合AD内部错误。离导线域内将同一距离范数改为 `sqrt(sum(distance*distance))`，得到当前coil源 SHA `48eda69a…`，不改变物理方程。原字节保存在 `results/coil/source_before_higher_ad_fix.py`。

实际执行 `run_coil_higher_ad_fix.py`，报告 `higher_ad_fix_validation.json/.log`：旧/新固定场差8.64e−16，固定Jacobian差7.23e−15，共点反馈场差8.60e−16、反馈Jacobian差1.16e−14；完整反馈Jacobian的高阶方向导数与两步长有限差分相对差4.33e−9/1.06e−8。该方向收缩的旧范数也能运行；不伪称每个旧mixed调用都会失败。Birkhoff全张量失败及后续修复保留在其独立记录。这一检查验证的是所列三阶/反馈方向导数，**不是完整四阶Hamiltonian张量的正确性证书**；继承杆中更高阶 `solve` 的混合AD异常另由 Birkhoff/学习任务处理，不能对原始高阶张量先对称化再宣布通过。

完整CHNN学习误差可达性调用又暴露分配初值缺陷：72个不同目标中23次失败，大伪逆请求最高约326A，旧力分配器先做一个无必要的巨大电流距离投影来取初值。失败及旧源码保留；当前 `allocate_force` 先独立检验 previous 在决策位形上可行，则直接以它启动**同一个**归一化广义力目标。成功标志、容差、场/梯度/电流约束均不放宽。旧源码与旧runner快照保存为 `source_before_force_warm_fix_*.py`；新分配器SHA `1b01c4fc…`，每次结果增加 `seed_policy`。

在新目录真实重跑，避免覆盖首次证据：

```bash
/workspace/1028-cloud/venvs/learning/bin/python stage5/program/run_coil_validation.py \
  --output stage5/results/coil/force_warm_fix
/workspace/1028-cloud/venvs/learning/bin/python stage5/program/run_coil_closed_loop.py \
  --force-only --output stage5/results/coil/force_warm_fix
/workspace/1028-cloud/venvs/learning/bin/python stage5/program/run_coil_higher_ad_fix.py
```

`force_warm_fix/` 含新的JSON/CSV/NPZ与日志；力补偿8/16步实际闭环重新执行。与首次成功补偿轨迹的状态最大差1.17e−12、电流最大分量差6.51e−10A（记录于 `version_comparison.json`）。因此未改写原科学结果，也未把算法修复仅称为浮点等价；该初值策略对失败目标的改进由学习分支的新run_id另行检验。最新 `interface_tests_after_higher_ad_fix.log` 的**6项**测试实际通过，包含新增mixed高阶方向差分。原5项通过日志也保留。

学习分支的72个新误差目标已实际重新分配，`results/learning/S5_L02_coil_reachability.json` 记录72成功、0失败、17.42秒，旧23失败完整保存于 `S5_L02_pre_warmfix_*`。最大约束超量9.4e−13，电流2A与梯度.03T/m约束实际激活。但真实端口秩仍为5，完整复网络聚合场误差只从2.112降至2.041；配置速度误差不能靠磁动量输入抵消，不可达动量分量也仍存在。修复的是分配初始化，不是消除了学习误差或证明了闭环性能。
