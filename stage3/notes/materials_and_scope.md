# 材料身份、已有基准和本轮研究边界

本记录依据当前工作树的实际文件和本次执行记录；历史笔记中的“已复算”不自动计为第三阶段的新执行。复查命令为：

```bash
python3 stage3/program/inventory.py --network
```

`--network` 仅运行只读 `git ls-remote`。不加此参数时只做本地审计，并明确将网络核验记为未执行。JSON 清单为 `stage3/results/material_inventory.json`，含逐文件 SHA-256、ZIP 条目与解压树比较、DOCX 身份、精确缺失路径，以及本次已有基准的命令、退出码和日志摘要哈希。

## 实际附件和版本

| 实际文件 | 字节数 | 文件条目 | 本次结果 |
|---|---:|---:|---|
| `codex_stage3_starter_1MB.zip` | 1,029,007 | 120 | 全部与 `stage3/source_inputs/starter/` 匹配 |
| `v10_英文中文整合源码与复算包 (1).zip` | 39,729,610 | 263 | 全部与 `stage3/source_inputs/v10/` 匹配 |
| `一般Birkhoff_推导与验证材料.zip` | 20,823 | 8 | 全部与 `stage3/source_inputs/birkhoff/` 匹配 |
| `推理草稿5月1025.docx` | 194,893 | 1,222 段、570 个 OMML 数学对象 | 与轻量包 `references/` 中副本逐字节相同 |
| `references/1025_stage1_review.docx` | 248,446 | 2,274 段、1,343 个 OMML 数学对象 | 已提取并阅读与本轮有关的第 9—12 章及原稿编号审查 |

用户称作“1025_Codex_第三阶段_轻量开工包.zip”的材料，当前实际文件名是 `codex_stage3_starter_1MB.zip`。不是再缺一个同名第四 ZIP。ZIP 共 391 个文件全部通过 CRC 读取及路径安全检查；现有解压树完整，所以没有再覆盖解压。轻量包自带 `FILE_HASHES_SHA256.json` 的 118 项全部通过。原始 ZIP 和冻结文件均未被清单程序改写。

原 DOCX 的 SHA-256 为 `8c62b874caaa6362b0f1c5612ddd6514aa7141454b17ef4cf5688408fe307338`；其 `document.xml` 哈希与历史 `version_audit.json` 中的 (2)/(3)/(4) 副本记录一致。这里仅核实当前文件和历史记录的一致性，没有声称重新取得那三个原文件。

本次实际 Git 读取返回：

- `main` / `HEAD`：`8761d70239a54985b40c0a6196f52e53d5b2e4d2`。
- `refs/tags/v10-20261008`：`82519542dd057e8fbd6d6879ef33217761e8cbbb`，即用户指定固定提交。

这核实了版本身份，**没有**重新执行原始 GitHub/S1 科学计算。当前附带的 `v10_framework_20261028` 自述是较早的三子问题整合版；历史第二阶段材料还引用 `v10_birkhoff_20261028`，该后一目录当前不存在。不能将手边 `(1)` 包改称“最新版”，也不能把其复算等同于原固定提交的全部成果重证。

## 本次已有基准执行状态

以下是本次环境准备实际运行的命令组，全部在仓库外普通副本 `/workspace/1028-cloud/runs/validation-f1j023jo/` 执行，没有覆盖 `source_inputs` 中原有数值文件。耗时只描述本机本次运行，包括部分首次 JIT 编译。

| 检查 | 状态 | 秒 | 覆盖 |
|---|---|---:|---|
| v10 `reproduction/run_all.py` | 实际执行通过 | 249.19 | FE 基准、最小控制、共享数据跟踪、5 个阻尼场景、汇总、matrix/closed/defect/weighted 四组 |
| `verify_starter.py` | 实际执行通过 | 0.05 | 118 项清单 |
| `verify_general_birkhoff.py` | 实际执行通过 | 5.58 | 已知非线性图的合成对象，非当前三维 ROM |
| `verify_v10_special_case.py` | 实际执行通过 | 2.85 | 旧显示精度两模态特例 |
| `transport_moser_check.py` | 实际执行通过 | 12.34 | 8/16 自由度合成场的一阶输运/Moser 图 |
| `validate_rod_rom.py` | 实际执行通过 | 5.30 | 12 自由度三维 ROM 的 12 个运动学/虚功样本 |
| `metriplectic_candidate.py` | 实际执行通过 | 4.97 | 32 个 ROM 状态的候选代数退化/熵检查 |
| `verify_operators.py` | 实际执行通过 | 38.76 | 三维 Cosserat 磁力、磁矩、接触和功率接口 |
| `model.py` 短时实际积分 | 实际执行通过 | 10.92 | 16 段，200 步，0.002 秒，11 帧有限状态；不代替 32/64 段长时研究 |

`learning_rom` 与 `metriplectic` 脚本主要输出数值诊断，不能把退出码单独解释为全域定理。本次前者运动学能量相对误差最大 `4.8012e-10`、磁虚功相对误差最大 `7.9747e-8`；后者能量退化相对误差最大 `6.3608e-17`，最小熵产生 `0.0382983`。这些均是有限样本浮点核验。当前九项无执行失败或缺少依赖；其他未运行项目另列如下。

## 轻量包实际缺少什么

压缩包内有 37 个 Python 源文件，但 **没有任何 `.pt`、`.pth`、`.npy` 或 `.npz`**。已有小型 JSON/CSV 只保存摘要。原训练权重、冻结确认集、大型轨迹不能从摘要中恢复。`material_inventory.json` 列出 37 个精确要求路径，均按当前文件存在性检查；主要组为：

1. 在 `stage3/source_inputs/starter/stage2/results/learning/` 及 `learning_stress/` 下缺少 `learning_data.npz`、`analytic_coefficients.npy`、`rom_matrices.npz`、`learning_summary.json`、`evaluation_summary.json`、`complex_seed1025.pt`、`complex_seed1026.pt`、`complex_seed1027.pt`。因此原冻结模型评估、原学习数据复用以及原确认协议复跑记为**缺少数据**。可另建新目录重新生成/训练，但不得把新训练称为原冻结权重的复证。
2. `results/learning_spd/{local,stress}/spd_complex_seed1025.pt` 及各自 `learning_summary.json` 不存在。`evaluate_spd_confirmation.py` 还需要 `results/learning_confirmation/{main,stress}/confirmation_data.npz`、`dataset_manifest.json`、`confirmation_summary.json`，以及 `frozen/config.json` 和 `frozen/models/{main,stress}/rom_matrices.npz`。原正质量确认检查记为**缺少数据**。
3. `results/learning/feedforward/{linear,analytic,complex,truth}.npz` 不存在。现有 `rod3d/run_learning_comparison.py` 直接读取这些文件；原四种控制器的 32/64 段冻结前馈对比记为**缺少数据**。
4. `stage2/verify_delivery.py` 不在轻量包中，完整归档清单验证记为**缺少源码**；轻量包应使用根目录 `verify_starter.py`。`stage2/notes/1025_stage1_detailed.md` 也不存在，但本次已实际读取独立提供的第一阶段审查 DOCX。
5. `stage2/sources/s1_original/IJRR_CHNN_KAM_导师意见凝练稿_20261002/` 和 `stage2/sources/integration_latest/v10_birkhoff_20261028/` 不存在。原 S1 的 COMSOL、冻结区间 KAM、64 平面自由度控制和 S 路径的重新执行记为**缺少数据/未执行**；保留历史出处，不删除其原成果。历史笔记给出的完整 S1 下载大小为 808,408,246 字节，并非本轻量包的一部分。

上述缺失不妨碍从真实 `rod_rom.py` 新建本轮 Birkhoff、积分器与磁控制实验。完整新训练、原 KAM 重证、32/64 段长时新控制验证和文稿排版未被这九项基准覆盖。

## 原稿与第一阶段审查中直接影响本轮代码的结论

原 DOCX 全文和第一阶段审查的文本提取分别在 `original_1025_text.txt`、`stage1_review_text.txt`。提取包括 OMML 文字 token，但不保留完整分式、上下标和矩阵排版；数学判断以原 XML、明确推导和实际源码互相核对。未宣称本次又阅读了历史审查提到的全部 898 页文献。

1. 原稿(35)/(36)保留了变质量二次惯性项的意图；实际应直接解完整中点残差：`q+−q=h M(q_mid)^{-1}p_mid`，`p+−p=h[−∂qH+Q_nc]`。其中 `−∂qH` 包含 `−1/2 pᵀ(∂qM^{-1})p`，不得冻结成 `M0` 后仍称原系统。
2. 常矩阵(36)的消元包含 `Ks M^{-1}`、`C M^{-1}`，不允许交换次序或把矩阵当标量分式。变系数下，所有系数仍依赖未知中点，隐式性不能被符号消元藏掉。完整中点在光滑分支为二阶，原稿的“一阶精度”不是本轮预设答案。
3. 对 `K=(Da)ᵀ−Da`，必须检查空间闭性、非退化以及时间输运。Theorem A 还需端点坐标变换的二形式拉回匹配和横截投影可逆；不是“任意可逆坐标变换”。生成梯度的 Jacobian 本身不要求可逆。Theorem B 的解析递推和梯度截断前提不能由一个小结构残差代替。
4. 合法比例阻尼特例 `p'=−H_q−γp` 可取 `K(t)=exp(γt)K0`、`Π=exp(γt)p`。变质量时依旧能用此规范变换，但变换后 Hamiltonian 仍包含完整 `M(q)^{-1}` 及其 q 导数。一般非比例阻尼、接触、磁分配反馈不自动满足此特例。
5. 自治正则分支 Central4 的标量为 `S_h=hH+h³ fᵀH''f/24`，正号；增量为 `J∇S_h`。它适用于非可分的完整 Hamiltonian，不能只保留常质量振子公式。它与普通中点后向修正 Hamiltonian 的负号回答不同问题。
6. 磁力必须对固定输入求偏导：若 `V_m=−uᵀΦ(q)`，则 `Q_m=(DΦ)ᵀu`。把反馈 `u=κ(q,p)` 先代入势能再求总导数，会额外产生 `Dκ` 项，通常不是真实磁力。闭环切线也必须包含反馈导数，不能拿固定电流子映射的辛性冒充闭环辛性。
7. 当控制增加场 `g` 后，原 K 继续适用至少需相应 Lie 输运条件（固定结构下 `DgᵀK+KDg+g·∇K=0`）。不可达控制残差、饱和及采样保持应纳入真实闭环；否则须重新构造 `K_u`，或只声明耗散/端口结构。
8. 局部更新唯一性和有限时误差仍需共同光滑域、稳定的隐式分支和逆 Jacobian 界。二阶误差含 `O(h²+η_h/h)`；Central4 相应为 `O(h⁴+η_h/h)`。小残差和样本条件数只是诊断，不是已建立这些域上界。
9. 相图、FFT、能量下降、二形式小缺陷都不是 KAM 证书。圆截面三维杆的 1:1 弯曲共振使旧两模态非共振条件不能移植。连续/离散 KAM 应分别给解析域、正规形、非退化、小量和非共振条件；接触摩擦闭环另有正则性问题。

## 三维目标与当前计算层

最终对象仍是空间站微重力环境下人体血管内的三维磁驱动柔性介入机器人。实际 `RodROM` 是每个弯曲轴和扭转轴各四个应变 Ritz 系数，共 12 配置自由度、24 维相空间、20 个积分单元的三维 Kirchhoff 几何 ROM。它保留 SO(3) 姿态、位形相关平动/转动质量和磁偶极接口；采用不可伸长、不可剪切约束，当前 Hamiltonian 没有把规定血流/接触力完整投影进去。因此本轮先连接此真实 ROM 只是可执行中间层，不能当完整血管机器人已验证。

现有 `rod3d/model.py` 则是三维 Cosserat 动力学，含弯曲、扭转、伸长、剪切，调用实际 PyElastica，带规定脉动血流、刚性管腔惩罚接触/正则摩擦和声明的残余微重力项。`config_position_feedback.json` 明示该流场不是 Navier–Stokes 求解，`added_mass_implemented=false`；管壁固定。其磁接口使用八维源外对称无迹仿射场，另有实际线圈/Biot–Savart程序和采样工作域约束。双向 FSI、柔性血管壁、实际传感/线圈标定和微重力生理标定仍未完成。

方向 B 的复网络源码、非可分 Central4、历史学习/KAM/控制材料均保留。当前 `ComplexResidual` 确实使用 complex128 可训练层和实/虚分裂 tanh；源码存在不等于历史权重存在，更不等于本轮重训或新三维 KAM 已完成。
