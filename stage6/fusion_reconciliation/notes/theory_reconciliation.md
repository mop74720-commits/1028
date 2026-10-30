# Birkhoff、Theorem A/B、原（30）—（36）与 Central4 的融合继承结果

结论：补入融合稿后，不应把第五阶段退回“一阶局部图”。stage5 已在真实 24D ROM 上实施高阶有源一形式、实际 Moser 辅助流、完整线圈同场反馈以及非可分 Central4，且已恢复完整 A/B 证明；融合稿补充了更清晰的双路线接口、一般规范和完整误差责任，但并非每项在第五阶段都已经计算落地。本专题补齐物理 H 规范、变分算子形式自伴性和完整图缺陷分解的真实三维验证，保留明确非零的原场误差。本轮并行完成的非自治完整线圈 κ(t) 二阶一形式桥接见 `proofs/nonautonomous_transport.md` 和 `results/algorithms/time_gain_r2_completed.json`；它推进的是一形式时间递推，不等于已经完成任意高阶生成函数定理的全部数值实例。原始三维血管机器人目标没有被这些光滑 ROM 检验替代。

## 实际阅读与定位

完整阅读新增 ZIP 中英文及中文的 `sections/structure.tex`、`sections/supp_general_birkhoff.tex`、`sections/supp_structure.tex`（中文结构章比英文多1空行，不能机械用英文行号当中文锚点）。对照原1025 `stage4/audit/source_omml/original1025_indexed.json` 的原生 OMML、`original1025_document.xml`、p0840–p1221 数学段落，尤其 m0399 与 m0565 的实际上下标/分式，m0400/m0408 的联合矩阵以及 m0417 的负号/分块。没有根据 README 反推原稿。

旧材料直接对照 `stage3/source_inputs/v10/v10_framework_20261028/english/sections/{structure,supp_structure}.tex`、`stage3/source_inputs/birkhoff/一般Birkhoff_两个核心连接与验证.md` 与 stage5 证明及程序。`supp_structure.tex` 与旧版 diff 表明：除插入一般 Birkhoff 补充、局部构造表述和新余项预算的交叉引用外，大部分旧有效公式原样存在。原样存在不是三维重证，因此逐式表另外区分实际三维实现和推广条件。

精确的190个中英显示公式/命题记录见 `annotations/theory.json`，使用总索引的源文件、行号、label、ID，不自行制造原编号。本文是对照与新代码解释，不是完整新论文。概率误差、完整 KAM 预算和旧实验的全部对象另见本轮历史路线专题，不能把本小节当它们的替代。

## 哪些已经实际贯通

| 原始路线节点 | 融合稿定位 | 第五阶段已继承的实现/证明 | 本轮判断 |
|---|---|---|---|
| 变分符号、二形式与输运 | struct:birkhoff/transport，ss:general-K-transport | `stage5/proofs/corrected_mathematics.md:110`；`program/transport_native.py:77`；`transport_cache.py:83` | 正确符号和同场残差已经进入真实ROM；原 m0541 的负D符号错未再传播 |
| 高阶一般一形式 | ss:general-R-recurrence | `transport_native.py:95`；`results/transport/{synthetic,fullcoil_collocated}/inverse_verified.json` | 自治合成r3/完整线圈r2已经计算；空间缓存单列误差。不是任意流血接触全域表示 |
| Moser/逆图/时间项 | ss:general-moser、chart-Hamiltonian | `program/moser_chart.py:22,39,91,95`；`proofs/birkhoff_transport.md:104` | 真实24D辅助流和时间敏感度已实现；不使用未知物理逆流作算法 |
| Theorem A | struct:endpoint-proposition、ss:general-endpoint-compatibility | `corrected_mathematics.md:153–235`；`corrected_identities.py:171–244` | 证明比原稿补足匹配/横截/初值/规范；新全载荷全域假设仍未验证 |
| Theorem B | supp_general_birkhoff:149 附近 | `corrected_mathematics.md:237–298`；`corrected_identities.py:265` | 第五阶段固定w PDE和递推比融合稿引用更完整，不是遗漏；一般24D非自治高阶生成式尚未全算 |
| 原（30）—（36） | struct:endpoint-variables、mechanical-midpoint、matrix-elimination | `corrected_mathematics.md:300–367`；stage3真实中点由stage5复用 | 正确联合逆、变质量几何力、非交换左解已继承；耗散中点不是自动保原K |
| Central4与exact primitive | struct:central4、ss:primitive | `proofs/integrators_full_coil.md:63–104`；stage5复用`stage3/program/rom_integrators.py` | 已接固定全线圈H，保留全混合导数；自治结论不赋予任意反馈 |
| 实际控制U | ss:general-control | `coil_energy_ports.md:37–89`；`coil_rom.py`及完整线圈闭环结果 | 真实电流场可达性与残差已进入；理想任意广义力补偿不可直接移植 |

## 本轮实际补齐的三项

程序为 `program/fusion_theory.py`，复算 `program/run_fusion_theory.py --run-id 新编号`；数学推导见 `proofs/theory_corrections.md`。

1. **B=H 规范适配器。** 对同一既有有源对 `(a0+b,H+b·f)`，固定空间点积分 `σ=∫b·f dt`，同时改 a 为 a+∇σ。不重训、不重建原力学，不把近似误差重新命名为精确表示。保持原场误差可见。
2. **形式自伴算子检验。** 独立符号例和真实24D场验证 Euler–Lagrange 线性化 `K d/dt+C`，而非要求 Df 对称。用同一个截断K配原场的非零缺陷，明确展示“可变分表示场”和“原物理场”之间差别。
3. **完整图缺陷分解。** 在融合稿的理想端点项之外显式加入内部辛缺陷和逆图/链式缺陷；先独立随机矩阵测试，再在同一24D旧轨迹第一步重算实际Moser导数。分解恒等式成立不等于原场轨迹精确。

## 实际执行结果

`results/theory/unit_tests.log`：4项独立测试通过，0.940s。测试中的2DOF例仅是符号/程序回归，不承担机器人证据。`results/theory/S6_THEORY02/results.json`：两种真实24D分支全部声明检查通过。该运行复用第五阶段指纹匹配的缓存和第一步轨迹，**重新计算规范、原场和表示场导数、Moser图/逆图及二阶时间敏感度**；未宣称重新训练或重新积分整条轨迹。

| 量（无量纲正则坐标） | 合成状态相关载荷 r3 | 完整线圈共点控制 r2 |
|---|---:|---:|
| 固定检查时间τ | 0.00025 | 0.00025 |
| B=H前后方程右端差 | 4.25e−17 | 1.96e−17 |
| 新规范与旧表示场之差 | 9.67e−17 | 1.04e−16 |
| 原场表示残差 | 1.656e−7 | 1.630e−6 |
| 不改a而直接令B=H造成的场差 | 1.427e−5 | 1.071e−4 |
| 原场H功率 | −1.6740e−5 | −6.7007e−5 |
| 表示场形式自伴缺陷 | 1.364e−13 | 5.061e−14 |
| 同K配原场的形式自伴缺陷 | 4.359e−6 | 1.818e−3 |
| 真实物理Df的反对称范数 | 1749.769 | 1749.769 |
| 实际首步二形式缺陷 | 8.882e−16 | 8.882e−16 |
| 完整缺陷分解等式余差 | 6.662e−16 | 6.662e−16 |
| 计算耗时 | 18.174s | 41.897s |

完整K、导数、规范量、输入状态、图矩阵、容差、源码SHA及缓存SHA保存在JSON。以上绝对范数遵循已有正则尺度，不能直接读成米、牛顿或生理阈值。

首次 `S6_THEORY01` 在数值检查后向控制台输出 NumPy bool 时发生 JSON 序列化错误；失败JSON及完整日志保留。修复仅为使用与结果文件一致的 NumPy标量转换；未改数学、容差或缓存。S6_THEORY02使用新编号，未覆盖失败证据。

## 尚未贯通及不能倒退的边界

- **不能从已有Moser恢复全域精确流。** 目前一般图仍受缓存空间半径、固定展开窗口、辅助流留域和成本限制；闭性、图匹配到舍入精度并未消除非零原场表示误差。
- **Theorem B并非已经全维实现完毕。** 完整局部证明和标量符号递推已恢复；实际24D保守分支Central4已实现。一般时间依赖图Hamiltonian更高阶生成函数、统一复域和截断常数仍未全做。
- **CHNN与KAM不能用“同一个章节”贯通。** 三维完整复隐藏层和SPD实验存在且负结果保留；融合稿新两模态单系数实验仍是有限基准。三维8749参数机械字典、网络误差不自动继承旧35方向Gram界。全12维共振正规形、余项、twist、小除数与定理阈值仍未闭合。
- **两种H不能混证。** 第五阶段共振研究是理想均匀轴向偏置H_ideal，全线圈控制是H_coil。原1:1对称性不可不检验地赋予一般空间线圈。旧二维连续/离散证书和64平面提升保持独立历史对象。
- **物理终点保持完整。** ROM不可伸长/不可剪切的Kirchhoff职责不等于Cosserat全模型；带规定血流、刚性壁的全杆只是一层中间计算。柔性壁、双向FSI和真实微重力生理标定不能从一般Birkhoff变分形式推得。

因此新增融合稿的有效理论大部分已由stage5的完整证明和程序真正承接；本轮补齐上述三项实际接口和误差检验。任意血流/接触闭环的一般全域图、完整非自治高阶生成法、新三维KAM证书与最终人体环境验证仍未完成，不能用190行对照或测试数量替代它们。
