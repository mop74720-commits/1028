# 排版依赖的来源与许可证

`sagej.cls` 和 `sageh.bst` 来自 SAGE 模板的公开分发副本：

- 仓库：<https://github.com/rstudio/rticles>
- 固定提交：`accdfa39225570a8ad9b786fbb3077060d1e12a5`
- 路径：`inst/rmarkdown/templates/sage/skeleton/`
- 类版本：`2017/01/17 v1.20`，SAGE 版权及 Rules of Use 保留在文件头。
- **类文件及参考文献样式逐字节保留，未修改。**

本文使用 `Afour,sageh,times`，A4 双栏、Harvard 作者年份引用。文档自己的
`preamble.tex` 删除了未投稿稿件不应具有的示例 DOI、卷期及转载元数据；
这不是修改 `sagej.cls`。作者与资助信息保留占位。

本次访问 <https://journals.sagepub.com/author-instructions/ijr> 被会话网络策略
以 CONNECT 403 阻断。因此采用可核实来源的 SAGE 模板，但**不声称已在线确认
2026-10-30 最新 IJRR 全部投稿细则**。实际投稿前应由作者核对最新指南。

中文依赖来自 <https://github.com/CTeX-org/ctex-kit>，标签 `ctex-v2.5.10`、
提交 `13a22565bdd14d750b604c2f1ed0fa1938cb6cd4`（2022-07-14）。
`chinese/` 包含 docstrip 生成的 xeCJK 3.9.0、ctexhook 2.5.10 及配置，
源文件和提取依赖压缩在 `ctex-source-2.5.10.tar.gz`。LPPL 1.3c 版权声明保留。
Git 源码中未展开的 `$Id$` 按上述标签文件名、版本和提交日期展开，避免空包名；
功能实现未改。无需管理员权限或环境配置草稿。

字体使用系统 Nimbus Roman / Nimbus Sans、DejaVu Sans Mono 和 Noto CJK。
PDF 嵌入使用的字体子集；不将完整字体文件上传仓库。
