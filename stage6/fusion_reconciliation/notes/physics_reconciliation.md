# 融合稿物理路线、真实电流控制及本轮修复

已完整读取中英文 `background.tex`、`mechanics.tex`、`application.tex`、`supp_mechanics.tex`，与第四阶段原始 OMML 位置、旧 framework 同名章节、第五阶段实际源代码和结果对照。逐公式/定理/表共有92项双语对照、184条精确位置记录，位于 `annotations/physics.json`；双语数学规范化与人工阅读结果在 `results/physics/bilingual_comparison.json`。这表示审阅覆盖，不是184个新证明。全文中的 `\input{tracking_main}` 由跟踪任务另查，不能用本四章读取代替其证明。

## 已经真正贯通的有效成果

1. 原1025 `p0115–p0171` 的 FEM/Galerkin—变质量—Hamiltonian 路线，经融合稿 `mech:general-lagrange/general-hamiltonian`、`sm:configuration-derivatives/galerkin-metric/christoffel`，已经进入真实 `RodROM.mechanics` 和第五阶段 `CoilROM.hamiltonian_tensor`。完整平动/转动几何及弯曲、扭转仍在；没有把非线性质量替换为原点常数。完整 Cosserat 剪切/伸长属于另一个杆层，不能把12自由度 Kirchhoff 的约束说成完整杆自由度。
2. 原1025 `p0202–p0225` 的磁能、力与力矩，以及融合稿 `sm:distributed-magnetism`，已经通过完整圆线圈磁势和固定电流偏导进入12自由度 ROM。`stage5/results/coil/validation.json` 及独立虚功测试支持该连接。原仿射端口约98.5%的力差仍保留；局部 Maxwell 矩阵代数不等于有限线圈可实现性。
3. 融合稿严格区分实际端口、总力矩和主动力矩的要求已进入第五阶段真实12电流端口、秩亏残差、限流及连续电流斜坡。原两输入 `A_mag^{-1}` 不可移植为12维任意控制。默认20单元只有一个磁积分点，数值电流端口秩5；40/80单元公共物理位形下是7，尚无全域满秩结论。
4. 正则尺度、复坐标 `1/sqrt(2)`、Rayleigh 速度偏导及磁/机械能的分账都有正确实现或修正证明。完整复网络成果仍需学习任务自己的证据；融合稿本身的可运行学习只是明确声明的单磁势特征，并未声称替代完整复隐藏层网络。
5. 第五阶段把同单位的共点电流反馈真正带到16/32/64段 Cosserat：规定脉动流、刚性曲管、摩擦/接触和合成微重力仍在。有流曲管0.2s下新反馈略差于名义基准，时间观察阶约0.469，空间约1.007；这些负结果没有被融合稿恢复覆盖。它们不是保守辛/KAM实验。

## 融合稿仍未充分进入第五阶段的内容

- **完整能量净空和功率约束器**：第五阶段有端口功率预算，没有旧 `app:work-governor` 的实际约束器，也没有三维几何界。本轮已补代码、证明、独立测试和完整线圈短窗积分，详见下一节。
- **已学习二模态控制器向高模态推广的三类缺陷**：`e_mag-e_R+e_port` 的完整代数应保留。融合稿 `app:validation-stages` 自己把新4/8/64受迫模态比较标为计划；旧固定v10另有64维成果，不能据此把这份新融合稿的计划表改成完成。第五阶段 ROM—杆比较尚未给出这些缺陷的统一误差界。
- **更强的精确有限元提升**：`app:conditional-lift` 要求已存在低维解析环面、目标动量Hessian正定且纤维凸、精确已知阻尼、可行完整反馈和整个响应域。该有限平面定理正确且必须保留，但真实3D全线圈秩亏、复杂反馈、共振与未观测高模态不满足自动迁移条件。
- **采样功率包络和误差储备**：`sm:power-envelope/additive-power/robust-governor/discrete-work` 给出条件性实施论证；当前没有全时间区间、传感延迟、线圈误差和血流功的校准包络。不得用本轮 RK 采样代替它们。
- **最终物理责任**：附加质量、双向FSI、柔性血管壁、微重力真实生理标定、完整学习控制到全杆的定量误差仍缺失。融合稿明确采用80mm平面梁、无流无接触；它只能恢复旧理论基准，不能成为缩减原1025三维血管目标的理由。

## 新实现与实际结果

新增 `program/fusion_physics.py` 直接复用第五阶段 `CoilROM`、`CurrentAllocator` 和连续斜坡，只增加三维充分几何界及真实电流功率半空间。`proofs/physics_corrections.md` 给出从原平面界到三维SO(3)、可伸长/剪切分支及实际离散中点几何的完整推导。

确认并防止两项不合法迁移：有符号完整线圈 H 不大于弹性能的假设；仅用弯曲能约束可剪切杆偏移。实际反例、真实能量/端口恒等式、几何界、解析半空间投影以及电流速率导致不可行的反例均通过独立测试，`tests.log` 为5项通过。

新实验由真实完整线圈力推进，不是重放仿射轨迹。统一20空间单元、24维状态、256点线圈求积、同一初态、零电流启动、四次控制更新；\(\tau\in[0,0.004]\)，实际0.89733794ms，\(\gamma=0.02\)，电流±2A、20A/s、决策磁点5mT及0.03T/m。两条支路是同一电流请求的普通受限分配与新增功率受限分配，分别使用每控制间隔1/2/4个RK4子步。全部6次实际运行成功，完整初值、参数、场/功/约束与求解残差在 `experiment.json`、`trajectory_summary.csv`、`trajectories.npz`，耗时合计约50秒。

| 最细积分的末值/最大值 | 普通分配 | 功率约束分配 |
|---|---:|---:|
| 末机械能/E0 | 3.15186531349e-4 | 3.13116644409e-4 |
| 末实际功账/E0 | 3.15192836267e-4 | 3.13122849076e-4 |
| 能量减功加耗散残差/E0 | −6.26259e-11 | −6.26215e-11 |
| 电流幅值/A | 0.0179468 | 0.0134630 |
| 连续斜率/A每秒 | 20 | 20 |
| 末磁点场/T | 2.82045e-5 | 1.87596e-5 |
| 末磁点梯度/T每米 | 5.05967e-4 | 1.82917e-4 |
| 1→2子步末状态差 | 1.14815e-6 | 1.14812e-6 |
| 2→4子步末状态差 | 7.22315e-8 | 7.22293e-8 |

粗网格能量账误差约5.85e-8，明显大于本次设置的1e-8能量余量；不能靠粗网格宣称能量上限验证。最细网格数值误差下降，但仍是有限时间数值结果。功率约束支路的决策约束实际激活，电流变化率真实激活。它减少了本短窗的磁输入功；这不是普遍跟踪优越性或长时安全结论。

独立读取保存轨迹后重新生成全21节点三维中心线，见 `centerlines.npz` 和 `independent_diagnostics.json`：普通/功率约束支路的最大直参考偏移分别为0.245160/0.245114mm，平方偏移除以证明中的弹能界最大约0.1993；SO(3)正交性缺陷不超过1.44e-15。`power_governor.svg` 直接绘制实际机械能变化和全中心线偏移。速率冲突反例还给出整个速率盒上功率的解析下界，严格大于允许的零功率，不只是优化器失败消息。

最重要的限制：**该实现约束决策状态功率，不是已认证的整区间功率包络**。电流在区间内连续斜坡，状态/磁点移动。虽然实际积分工作账保留了这些变化，它不能证明未采样时刻的安全。有限斜率还可能使零电流不在可行集，本测试中的失败被明确拒绝。未知流体功、接触与壁功未加入本光滑 ROM 实验。本轮不以“有一个governor程序”宣布血管净空问题完成。

## 复算

从仓库根目录执行，不在冻结源中运行写文件的入口：

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
/workspace/1028-cloud/venvs/learning/bin/python -m unittest discover -s stage6/fusion_reconciliation/tests -p test_fusion_physics.py -v
/workspace/1028-cloud/venvs/learning/bin/python stage6/fusion_reconciliation/program/run_fusion_physics.py
/workspace/1028-cloud/venvs/learning/bin/python stage6/fusion_reconciliation/program/verify_fusion_physics_results.py
python stage6/fusion_reconciliation/program/index_physics_reconciliation.py
```

历史证据仅作为历史证据保留：本轮没有重新跑完整Cosserat轨迹或新造旧权重，也没有更改第五阶段数据。其程序及既有结果均按实际身份引用。
