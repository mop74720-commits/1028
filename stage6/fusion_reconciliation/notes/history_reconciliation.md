# 双路线融合稿的历史继承、复算与新三维连接

结论：新融合稿补全了有价值的双路线对象区分、同参考跟踪及误差预算，它没有补齐全部历史CHNN/环面/COMSOL数据。第五阶段已在真实三维几何、完整线圈、非可分积分和新训练上超出融合稿；它此前没有把完整复网络生成的参考运动与真实三维线圈闭环连起来。本轮修复了这个明确连接缺口，但未证明欠驱动长时间跟踪或新的三维KAM。

## 阅读范围与原始对象

本支线逐文读取英/中文 `supp_experiments.tex`、`extension_tracking_theory.tex`、`extension_tracking_results.tex`、`tracking_main.tex`、`conclusion.tex`、`endmatter.tex`、`references.tex`，并读取全部 `delivery_report/report.tex` 和 `ARCHIVE_PROVENANCE.txt`。76项显示公式/命题/表格的逐项位置和六层继承状态在 `annotations/history.json`；英文38项及中文对照均已覆盖。无显示公式的结论/数据声明/参考文献以本节逐章核对，不把引用存在等同于读过所引外部论文。

- `tracking_main.tex` 是**正文**方向II；`extension_tracking_theory/results.tex` 提供其完整推导与实验；不是仅把结果留在未引用附件中。两路h分别为`h_c=h0+δR`和`hhat=hstar−δR`。
- `supp_experiments.tex` 明确当前物理对象为 **平面Euler–Bernoulli两模态**、无流/接触/剪切、设计磁芯和理想局部磁端口。其32Hermite单元的64自由坐标只用于线性FE核查，不能改称64模态非线性闭环复现。
- `conclusion.tex` 对一般一形式存在与实用算法、普通中点与加权方法、原场误差和结构误差、参考KAM和耗散跟踪做了正确区分。但它的“统一磁模型”限定于该融合稿两模态对象，不能指代原1025完整血管机器人。
- `endmatter.tex` 明确原S1/S2只是原参数组历史记录，当前交付不复现所有历史成果；不能仅因有原v10链接就认为冻结权重和Fourier证书已补回。
- `references.tex` 英中条目相同，明确区分Su–Qin2003预印本、2007论文、Feng–Qin书中编号；Shang离散KAM、Pöschel连续KAM和Haro–Luque后验流对象不互换。引文检查不替代逐篇外部全文核验。
- `delivery_report/report.tex` 完整说明材料A是该次**正文与物理参数**底稿、材料B为理论扩展源；65项融合判断和298→359标签只统计A到融合稿，绝不是1025→三维研究的完成率。其第四节小域预算不覆盖控制初态，第六节承认完整CHNN、实用高维图、全阶控制和有限幅KAM仍待完成。
- 原稿定位仍使用 `stage4/audit/source_omml/original1025_indexed.json` 的原生数学索引：`m0097,m0099,m0109` 的变质量正则动力学、`m0268,m0280,m0282` 的完整CHNN、`m0470,m0481–m0487` 的离散控制、`m0478,m0492` 的离散KAM与误差联系。它们不是融合稿当前公式编号。

## ZIP新增了什么，仍缺什么

完整性核验与全部条目SHA在 `results/materials.json`。字体移除重打包保留429条加新增溯源文件，包内声明原ZIP SHA为 `f809a715ad9e6696c418166db61137cf32d6ea888b39d74d732e8f30fc8c953d`；本轮实际取得并校验的是无字体包SHA `416bdb3c8337816c9ef041bcaa5d5a4b8a8276c6d7be6172e37a0dec0dd9ec7f`。没有原41MB包，不能独立证实其每条对照；只把该源身份作为包内声明保存。

实际科学二进制资产清单见 `results/history/scientific_asset_inventory.json`：只有 **一个NPZ**，`reproduction/framework_experiments/closed_loop_convergence_traces.npz`，保存新两模态收敛轨迹。没有PT/PTH/CKPT/MAT/H5/MPH。PDF/图片、JSON指标、TeX证明的存在均不能补成缺失原数组/权重。

仍缺 `stage4/audit/chnn_kam_inheritance.md` §7 所列具体原始路径：

- `results/{learning,learning_stress}/{learning_data.npz,rom_matrices.npz,analytic_coefficients.npy,learning_summary.json,evaluation_summary.json,complex_seed1025.pt,complex_seed1026.pt,complex_seed1027.pt}`；
- `results/learning_spd/{local,stress}/{spd_complex_seed1025.pt,learning_summary.json}`；`results/learning_confirmation/{main,stress}/{confirmation_data.npz,dataset_manifest.json,confirmation_summary.json}`；`results/learning_confirmation/frozen/config.json` 及 `frozen/models/{main,stress}/rom_matrices.npz`；
- `results/learning/feedforward/{linear,analytic,complex,truth}.npz`；
- 原S1 `reproducibility/unified_model/learning/{run_learning.py,raw/}`、`unified_model/theory/{verify_torus.py,hl_constants.py,torus_arb_refine.py}`、`mainline_completion/integral_certificate/comsol_integral_certificate_fit.npz`、对应Fourier候选和COMSOL观测、`mainline_completion/resonance/kam_magnetic_control.py`、`mainline_completion/s_path/kam_control_audit/certify_kam_lift.py`、`mainline_completion/s_path/run_s_path.py`及依赖。

S5自身**新训练**九个PT和NPZ已在仓库；本轮实际读取一个完整复网络权重。这不冒充原S1或第二阶段冻结训练的精确复现。

## 真正应继承且已执行的历史内容

1. **Direction II 同参考反馈。** 原公式代入给稳定误差方程、卷积及域内扰动界正确。oracle只替换plant抵消项，必须保留同一学习参考。旧v10 `full_fe_kam_control.tex#eq:full-fe-hamiltonian-feedback` 已有完整梯度/Hessian加速度实现，不能忽略动量依赖项。S5保留这段证明但L02只是状态点分配，未作新完整网络跟踪。本轮 `learned_reference_tracking.py` 实际复用S5权重、`CoilROM`与`CurrentAllocator`，在同一24维plant中执行，完整推导在 `learned_reference_tracking_proof.md`。
2. **参考误差与同步误差分离。** `num:reference-split` 的恒等分解必须保留。独立重跑得到学习末同步误差约2.98e−10，但连续参考误差约2.969e−5；两者差五个量级。新S6也单独计算网络参考RK4和DOP853差、实际闭环固定电流计划细化差，未把同步误差当总误差。
3. **完整增量残差和累积预算。** 冻结求解容差2e−14，原残差注入实验实际重跑`q=1,2,3`，新增误差阶`q−1`；没有降低Newton标准。S5真实线圈中点/非可分Central4已直接导入`stage3/program/rom_integrators.py`，不能因融合稿回到标量算例而删除这些三维验证。
4. **同场加权对照。** 融合稿的两个阻尼场分别比较普通/加权中点，其加权结构缺陷机器精度和二阶准确性是两种证据。S5高阶一般输运、Moser图和真实线圈方法保留，不把旧已知共轭合成G3冒充真实高维算法。
5. **历史KAM和高维提升。** 固定旧v10 `full_fe_kam_control.tex#thm:full-fe-kam-lift` 的低两模态精确实现、正动量Hessian/凸纤维、两端口可逆、非零cosθ、高模态阻尼线性响应证明有效保留，作用对象是128相空间内二维环面，不是全128维Hamiltonian。新线圈rank5、变质量跨模态耦合和接触流体不满足原直接提升假设；新三维推广未完成。
6. **不利S路径对照必须保留。** 固定旧 `s_path.tex#tab:s-path`：CHNN实测末端反馈6.419µm，二次6.207µm，物理静态逆4.124µm，模态输出25.308µm。其S形路径由轴向基座进给+平面磁弯曲实现，无血流/壁接触；COMSOL只是保存场的机械重放，不是在线重算控制。本轮读了原正文和全部界定，但缺历史原数组，没有把这些数值冒称本轮重跑。

## 本轮实际复算及量化结果

运行在独立复制 `/tmp/1028-stage6-history-124hcf02/reproduction`，冻结解压源的前后SHA全部相同。入口`program/history_reproduction.py`支持新run-id；fresh checkout通过`materials.resolve_source()`重新核验提取。六条实际命令、退出码和成本在`results/history/fusion_original_reproduction/execution.json`：

|入口|状态|实际秒数|证据|
|---|---|---:|---|
|verify_baseline.py|通过|0.995|baseline_reverification.json，1880数值叶项FE核验|
|experiments/minimal_control_loop.py|通过|31.392|minimal_control_results.json|
|experiments/route_b_shared_data.py|通过|64.166|route_b_shared_results.json|
|experiments/damping_sensitivity.py|通过|81.459|damping_sensitivity_results.json|
|experiments/summarize_results.py|通过|0.109|control_audit_summary.json|
|framework_experiments/run_all.py|通过|13.756|四个framework JSON和NPZ|

framework输出与随包输出逐字节相同；它们确经日志记录重算，收集说明在`framework_output_collection.json`。11873个非运行时数值字段与包内结果在`1e−12+1e−9×max(|a|,|b|)`比较容差内一致，`supplied_vs_rerun_numeric.json`保存字段数量/差异。此比较容差未改变求解器容差，也不等于严格区间证书。

关键字段：

- `minimal_control_results.json#oracle_midpoint_convergence[-1]`：T20、h=.005、最大误差7.4224462458e−4，阶1.99933069896，理想辛切映射缺陷3.33e−16。
- `route_b_shared_results.json#tracking.groups.learned_tracking`：后半窗独立参考RMS2.26767e−5，同步RMS8.55100e−7；`numerical_checks.reference_midpoint_error_ratio_on_halving_step=3.99998370190`；同参考oracle/Cayley差1.003989e−15。
- `closed_loop_convergence_results.json#conservative_nonlinear_central4.rows[-1]`：T20、h=.005、误差6.7819304969e−8、阶3.99950317646。不能与G2 T4的1.356e−8混用时间窗口。
- `nonlinear_weighted_results.json#cases[0].methods`：h=.04，普通指数加权缺陷2.87627e−5，对应合法加权缺陷3.37711e−16；末次阶均约1.9994。
- 各阻尼扫描均重新识别参数，不能说同一冻结控制器对未知阻尼变化均鲁棒。

本轮新S6-T01的四项独立测试通过，记录`S6_T01_tests.log`。真实线圈短窗全部约束检查通过而分配误差明显非零；精确数值/原轨迹/物理单位见 `S6_T01/results.json,trajectories.npz`。额外固定计划小最大步长细化差1.05569e−14；这是浮点数值核验，不是全窗严格包围。

## 尚未贯通及不能恢复成“已完成”的内容

- 融合稿本身用两个标量势/阻尼拟合代替了原完整CHNN比较；第五阶段已另做完整复隐藏层/SPD/机械字典新训练，且保留负Hessian、病态和失败。本轮新增参考生成闭环连接，仍缺完整模型误差控制与公平同预算实网络比较。
- 融合稿辅助小复域正规形预算没有覆盖控制初态，更没有给三维共振体系的两个合法复域、twist逆、全整数小除数和阈值。原两模态证书继续作为历史有效成果，不能移植。
- 新S6实际force request采用已知完整plant，网络只生成参考；不能称为“完整CHNN已补偿完整线圈物理误差”。欠驱动/速率约束残差阻止无条件误差收敛结论。
- S5的16/32/64段全杆有流/接触/微重力中间层已实际推进，主控制新共点项略差、时间细化阶不足、ROM/杆差异不消失等负结果保留。S6新学习参考尚未转入该全杆。
- 双向FSI、柔性血管壁、生理数据与真实微重力标定均未由本融合稿补齐。最终目标必须继续以原1025约束完整路线，不能退回平面梁。

一个轻微文档不一致：`supp_experiments.tex`称外层先“rebuilds/重建”FE，实际`reproduction/run_all.py`调用`verify_baseline.py`在复制目录重算并比较冻结基准；冻结基准本身未覆盖。新复算wrapper明确采用核验语义，无须改历史TeX。
