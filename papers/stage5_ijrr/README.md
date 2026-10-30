# Stage 3–5：IJRR 中英文论文稿

题目：**Local Birkhoff structure and full-coil control of a three-dimensional magnetic rod**
／**三维磁性杆的局部 Birkhoff 结构与全线圈控制**。

本稿将已经完成的 Stage 3–5 结果组织为论文，不新增科学模型、训练或实验。
保留原始 1025 的三维血管磁机器人目标，但不把尚未验证的应用层写成已经完成。

## 版本与范围

- 目标仓库：<https://github.com/mop74720-commits/1028>
- 实际获取的基准分支：`stage5/unified-3d-repairs`
- 固定基准 HEAD：`1c73a580441200d6594e2a2a96374edc1c0e98e6`
- 新论文分支：`manuscript/stage5-ijrr`
- 新文件全部位于 `papers/stage5_ijrr/`；原始 DOCX 和 Stage 3–5 文件不变。
- 不使用 Stage 6、后续 Bridge 专项或此前独立原稿审查的新结论。
- 基准提交新增的融合 ZIP 不作为新的科学结果来源。

原始 DOCX 路径为
`stage3/source_inputs/starter/references/推理草稿5月1025.docx`，SHA-256：
`8c62b874caaa6362b0f1c5612ddd6514aa7141454b17ef4cf5688408fe307338`。
逐式定位使用原生 OMML 及 Stage 4 的位置索引；已确认的符号、尺度、生成函数、
控制及 exact-symplectic 问题采用 Stage 5 已有修正，不重新研究这些问题。

`stage5/results/transport/inverse_verified_reference_bridge.json` 名称中的 bridge
是 **Stage 5 内部线圈参考核的舍入桥接**，不是后续 Bridge 专项研究。
所有引用源路径及哈希见 [source_manifest.csv](evidence/source_manifest.csv)。

## 成品

| 文件 | 内容 |
|---|---|
| [Stage5_IJRR_EN.pdf](Stage5_IJRR_EN.pdf) | 英文双栏正文，17 页 |
| [Stage5_IJRR_ZH.pdf](Stage5_IJRR_ZH.pdf) | 对应中文双栏正文，13 页 |
| [Stage5_IJRR_Supplement_EN.pdf](Stage5_IJRR_Supplement_EN.pdf) | 英文完整局部证明及补充证据，15 页 |
| [Stage5_IJRR_Supplement_ZH.pdf](Stage5_IJRR_Supplement_ZH.pdf) | 对应中文补充材料，13 页 |
| [english/main.tex](english/main.tex)、[chinese/main.tex](chinese/main.tex) | 主文入口 |
| [supplement/](supplement/) | 双语补充证明源码 |
| [references.bib](references.bib) | 15 条逐项来源核对的参考文献 |
| [figures/](figures/) | 六张矢量 PDF 图及 PNG 预览；两语言共用相同数据图 |
| [evidence/validation.json](evidence/validation.json) | 实际页数、PDF 哈希、双语一致性及编译检查 |

中文完整翻译正文和证明，图内英文轴标签共用以保持图数据和标记完全相同，图注已翻译。
字体嵌入 PDF；不上传完整字体。作者、单位、通讯方式、基金、利益冲突及贡献声明须由
作者补充。正文已有数据可用性、伦理范围和 AI 辅助准备披露；不伪造作者批准。

## 论文重点与证据对应

| 论文内容 | 主要冻结证据 | 成立范围 |
|---|---|---|
| 三维 SO(3) 几何、12 配置坐标、变质量 Hamiltonian | Stage 2 `learning/rod_rom.py`、Stage 5 `unified_model_contract.md`、`coil_rom.py` | 保留质量导数；ROM 为不可伸长、不可剪切 Kirchhoff；完整杆另保留伸长剪切 |
| 一形式输运、规范、误差与 Moser 图 | Stage 5 `proofs/birkhoff_transport.md`、`transport_native.py`、`transport_cache.py`、`moser_chart.py` | 局部、光滑、非退化域；实际自治分支，未知精确流不作为算法输入 |
| Theorem A/B、原（30）—（36）与 Central4 | Stage 5 `proofs/corrected_mathematics.md`、`integrators_full_coil.md`；Stage 3 `rom_integrators.py` | 端点拉回、横截性、规范和固定坐标递推；四阶仅适用自治保守分支 |
| 高阶输运、图匹配及积分误差 | `stage5/results/transport/{synthetic,full_coil}/inverse_verified.json` 等 | 独立原场/表示场参考；三阶表示误差更小不等于总误差更小 |
| 完整线圈磁能、虚功、可达性及闭环 | Stage 5 `coil_energy_ports.md`、`full_coil/` 最终暖启动修正输出 | 固定电流偏导后代入反馈；短时受限控制与光滑反馈分别判断 |
| 完整复隐藏层、SPD 与机械特征比较 | `S5_L01_results.json`、独立 `S5_L02` 诊断与冻结权重 | 训练对象为理想偏置能量；有限采样误差，不是完整线圈学习或统一解析域界 |
| 学习误差与 KAM 预算 | Stage 5 `chnn_kam_restored.md`；保留原对象的旧证明 | 有条件的 Gram/统计范数推论；没有新的三维 KAM 证书 |
| 三维共振正规形 | `S5_R01`—`S5_R04` 接受结果 | 保留全部 12 个括号通道的第一对四次限制；不是完整不变子系统 |
| 16/32/64 段空间杆转移 | Stage 5 `rod_transfer/` 最终分配修复结果 | 规定流、刚性壁、合成微重力；跟踪略差、时间观测阶约 0.469 |

精确文件、JSON 字段、公式位置和源 SHA 分别记录在：

- [theory_claims.csv](evidence/theory_claims.csv)：数学假设及证明源；
- [physics_claims.csv](evidence/physics_claims.csv)：物理参数、力、约束和杆结果；
- [numerical_claims.csv](evidence/numerical_claims.csv)：表示、图、积分、参考与成本；
- [learning_claims.csv](evidence/learning_claims.csv)：网络、反解、分配与共振；
- [figure_sources.csv](evidence/figure_sources.csv)、[plotted_data.json](evidence/plotted_data.json)：62 个绘图序列。

论文保留的重要负结果包括：约 98.6% 仿射力偏差、端口秩亏、光滑共点反馈不保留原正则二形式、
采样电流记忆使完整更新为 36 维、复网络非正动量 Hessian、早期高阶 AD 错误、初次分配失败、
全杆跟踪略差和低时间细化阶。错误 AD 输出不参与接受结果的统计。

## 编译与核验

推荐环境：TeX Live 2025、XeLaTeX、BibTeX、Poppler (`pdfinfo`, `pdffonts`, `pdftotext`)；
字体 Nimbus Roman、Nimbus Sans、DejaVu Sans Mono、Noto Serif/Sans CJK SC。
例如常见 Debian 安装包包括 `texlive-xetex`、`texlive-latex-extra`、`fonts-urw-base35`、
`fonts-noto-cjk`、`poppler-utils`。中文宏包已随附，见 [template/README.md](template/README.md)。

从仓库根目录执行：

```bash
bash papers/stage5_ijrr/tools/build.sh
python papers/stage5_ijrr/tools/check_manuscript.py
```

构建脚本对每份文档执行 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX，保存最终日志。
不会调用任何机器人、学习或控制实验程序。检查程序核对：

1. 中英文各节与补充材料的显示公式、行内数学、标签、引用及数值 token；
2. 53 个引用源文件的 SHA-256 与允许阶段；
3. 重复/缺失交叉引用、公式溢出、缺字、PDF 页数及字体嵌入；
4. 基准提交以外是否改动已有研究文件。

重画图表只读已有输出，需要 Python、NumPy、Matplotlib：

```bash
python papers/stage5_ijrr/tools/build_figures.py
bash papers/stage5_ijrr/tools/build.sh
python papers/stage5_ijrr/tools/check_manuscript.py
```

本次绘图实际使用 Python 3.12.14、NumPy 2.3.5、Matplotlib 3.10.8。
上述重画不是科学实验复算。科学复算入口及依赖仍见冻结的 `stage3/README.md` 和
`stage5/README.md`；本次不声称重新执行它们。

## 排版及文献核验边界

使用 SAGE 原版权 `sagej.cls` v1.20 和 `sageh.bst`，采用 A4 双栏与作者年份引用；类与样式未改。
模板副本的固定 GitHub 来源、SHA 和中文包来源见 [provenance.json](evidence/provenance.json)。

本次网络策略以 CONNECT 403 阻止访问 IJRR 官方投稿网页和 Crossref。
因此文献已逐项与可取得的冻结书目、原出版社/机构核验记录核对，但**不声称全部进行了新的在线核验**。
15 条文献的核对层级见 [reference_verification.csv](evidence/reference_verification.csv)。
没有增补猜测 DOI。Greydanus 等（2019）的冻结书目没有页码，保留其会议、卷与原文 URL；
BibTeX 因此有一条 `empty pages` 提示，未捏造页码消除该提示。正文无未解析引用。
实际投稿前仍需核对期刊最新要求以及作者资料和声明。

## 明确尚未完成的证明与验证

- 受限采样控制、学习补偿、局部 Birkhoff 图和有流有壁空间杆的单一组合闭环验证；
- 全工作域的图非退化/逆界、长期图延拓和向外舍入误差证书；
- 当前网络的统一解析域学习误差、全域 Legendre 条件及真实学习闭环；
- 新三维系统的完整共振正规形、解析余项和小除数预算、连续/离散 KAM 证书；
- 受载血管环境下 ROM 到完整杆的统一误差界；
- 双向 FSI、柔性管壁、真实线圈硬件与微重力生理标定。

这些内容在正文讨论和补充材料中保留为未完成责任，不以历史两模态证书或独立算例代替。
