# 本次实际制作与检查记录

本记录只涉及论文整理、已有数据绘图和排版，不是新的科学复算报告。

## 版本与源文件

2026-10-30 获取并在交付前再次查询远端 `stage5/unified-3d-repairs`，均为
`1c73a580441200d6594e2a2a96374edc1c0e98e6`。
独立 worktree 和 `manuscript/stage5-ijrr` 分支只新增论文目录。
53 个实际引用源文件逐项核对哈希；原 DOCX 哈希与既有原生 OMML 索引对象一致。
不读取或引用 Stage 6 和后续 Bridge 新结果。

## 实际执行

```text
python tools/build_figures.py                  # 使用冻结输出；未运行模型或训练
bash tools/build.sh                           # 四份 PDF，XeLaTeX/BibTeX
python tools/check_manuscript.py              # 数学/数字/编号/引用/源哈希/PDF 检查
pdfinfo、pdffonts、pdftotext、pdftoppm          # 成品信息、字体、文字与逐页预览
git diff --check                              # 新增文稿格式
```

实际绘图命令使用 `/workspace/1028-cloud/venvs/learning/bin/python`，编译使用系统
TeX Live 2025。完整科学复算没有运行；引用数值保留 Stage 5 的原运行身份。

## 制作中发现并解决的问题

- 系统按字体族名选择了 Nimbus Roman 的 Type 1 粗体，第一次 PDF 输出失败，
  错误为 `Cannot proceed without the font ... NimbusRoman-Bold.t1`。
  改为明确指定已有 OpenType 文件，随后四份 PDF 均成功输出。
- 初次双栏编译的长公式溢出已通过 `aligned` 等分行修正，未删公式或假设；
  中英文修改同步。
- 中文宏包从有许可证的固定源生成；补齐 Git 源中未展开的包身份元数据，
  明确中文无斜体字体的使用方式。最终无缺字或字体替代警告。
- 主文逐页图表预览发现：学习图右栏同时有域内/域外样本；共振图右栏是外部扭转
  括号通道贡献，并非 twist 特征值。图注已按实际图修正；图中无量纲能量统一写为
  `h_PP`、`h_4`，不再与有量纲 `H` 混淆。
- 英文数字拼写与中文数字形式已统一，便于自动核对，不改变数值。
- 补充材料去除默认彩色链接边框，诊断表置于所属小节内；较长证明保留单栏以便阅读。

## 检查内容与剩余提示

已生成并目视检查四份 PDF 的逐页缩略预览，重点放大检查标题页、长公式、六张图、
学习表及参考文献页。检查了双栏边界、公式编号、图表标记、页码连续性和参考文献可读性。
图表数值、分支身份、坐标倍率和单位另由只读检查与冻结数据核对。
中英文10组正文/补充文件的显示与行内数学、标签、引用、数字以及编译后编号一致。

最终机器检查与真实页数见 `validation.json`；最终 LaTeX/BibTeX 日志保存于
`../build_logs/`。无公式溢出、缺字、未解析引用或未嵌入字体。
主文各保留一条 BibTeX `empty pages in Greydanus2019` 提示：原冻结书目没有该会议
条目的页码，采用其真实会议卷和原文 URL，不捏造页码消除提示。

Sage 官方指南与 Crossref 在线访问被会话网络策略阻断；模板与书目使用明确来源的
冻结记录。该限制不妨碍实际编译，但不能称最新投稿要求或全部文献已完成新的在线复核。
