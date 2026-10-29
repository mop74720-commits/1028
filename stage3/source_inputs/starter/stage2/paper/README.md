# 中英文统一论文框架源码

这是用于继续写作的骨架，不是将最终目标改写为简化模型的完成论文。完整三维 Cosserat／磁场与电路／血流／血管壁／接触摩擦／微重力目标、12 自由度 Kirchhoff 分析学习层和 64 段空间杆验证层分别保留。方向 A 与方向 B 的证据责任并列，不能相互借用。

## 文件结构

- `framework_en.tex`、`framework_zh.tex`：两个编译入口；配套 PDF 为英文 10 页、中文 9 页。
- `body_en.tex`、`body_zh.tex`：可继续扩写的语言正文。
- `shared_symbols.tex`：统一符号；用 `\Rot` 表示姿态，`\Pfaff` 表示 Pfaff 系数，避免原稿的 R 重名。
- `shared_notation.tex`：同源中英符号表。
- `shared_formulas.tex`：33 个共享显示公式，包含物理、Birkhoff、原（36）矩阵修正、控制、误差、学习与 Metriplectic。两语言调用同一组宏，公式标签一致。
- `preamble.tex`：统一版式、字体、交叉引用。
- `claims.tsv`：24 项主张，逐项给路线、状态、假设、证据路径和未完成／不允许外推的内容。TSV 可用文本编辑器或表格工具读取。
- `references.bib`、`reference_verification.tsv`：9 条具有已核验 DOI 的书目；核验页面、日期和用途限制逐条保存。
- `provenance.json`：依据报告和详细记录的 SHA。它冻结本框架所用来源，不表示所有上游报告此后永远不修改。
- `fonts/`：上传材料中已有的 Noto Sans CJK SC 字体及其 OFL 许可，用于可移植中文编译。
- `build.sh`：XeLaTeX → BibTeX → XeLaTeX → XeLaTeX。中间日志在 `build/`。
- `qa.json`：编译、共享公式及逐页视觉核验记录。

## 编译

从任意目录运行：

```bash
bash /absolute/path/to/stage2/paper/build.sh
```

脚本会切换到自己的目录；也可进入本目录后执行 `bash build.sh`。需要 XeLaTeX、BibTeX 和常见 TeX Live 包：`fontspec`、`amsmath`、`amssymb`、`mathtools`、`bm`、`booktabs`、`tabularx`、`array`、`longtable`、`enumitem`、`natbib`、`xcolor`、`hyperref`、`xurl`、`titlesec`。英文用 Latin Modern，中文用随包字体。当前实现不依赖未安装的 `ctex` 或 `xeCJK`，中文换行由 XeTeX 的 `zh` locale 处理。

PDF 视觉核验另需 Poppler 的 `pdftoppm`／`pdfinfo`。本次环境已具备上述依赖；没有通过安装或修改全局字体配置来掩盖缺字。

```bash
pdftoppm -r 130 -png framework_en.pdf render/en
pdftoppm -r 130 -png framework_zh.pdf render/zh
```

## 继续撰写时的规则

1. 在 `shared_formulas.tex` 修改数学内容，两语言只调用宏；不要复制显示公式再独立手改。
2. 新增公式保留稳定 `\label` 和框架标签；原稿的原（30）至原（36）是来源编号，不能被新标签悄悄覆盖。
3. 每个新结论先更新 `claims.tsv`：它属于推导、条件性定理、有限观察还是待证？假设、证据文件和实际对象分别是什么？
4. 原 Theorem A/B 的初始横截、初始生成梯度、演化横截、端点还原分支都已分别写出，不能再以“可逆变换”一句取代。
5. 离散 KAM 只对所选理想解析 exact-symplectic 映射讨论；任意非辛求解／图误差不能直接计入生成扰动预算。若提出新实现，先证明该实现仍在适用映射类内。
6. 保留学习与结构的失败证据。SPD 压力域近似误差和约 `1e12` 条件数均写入框架；逐点正定不是可靠反解或 KAM 常数的认证。
7. 各语种并非逐字镜像，但其对象、条件、公式及结论状态一致。扩写后重新编译两份、检查日志并逐页查看 PDF。

## 本次完成的范围

本目录没有执行新动力学、训练或控制实验。有限数值数据来自第二阶段已经冻结的结果；完整输入、初始化、求解器、误差定义和失败记录仍以对应详细记录为准。论文骨架没有把 8／16 自由度已知点变换例称为真实杆，也没有把旧两模态 KAM 证书转移给新 12 自由度或完整血流接触系统。

