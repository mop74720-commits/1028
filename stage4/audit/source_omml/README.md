# 原始数学对象证据与定位约定

复算（从仓库根目录）：

```sh
python stage4/audit/program/extract_omml.py
python stage4/audit/program/verify_omml.py
```

`original1025` 对应根目录原稿，`stage1review` 对应轻量包中的详细第一阶段审查 DOCX。`*_document.xml` 是 ZIP 内 `word/document.xml` 的原始字节；`*_indexed.json` 保存每个 `m:oMath` 的原始 XML、结构标签、结构阅读式和父段落；`*_reading.txt` 为便于引用的逐段阅读副本。原稿 1222 段、570 个数学对象；第一阶段 2274 段、1343 个数学对象。原文件哈希、原 XML 哈希、分式/矩阵等数量与实际验证结果见 `extraction_verification.json`。

段落按正文所有 `w:p` 的文档顺序编号（从1开始，含表格中的段落），不是只计 `body` 的直接子段落。阅读副本第 N 行严格对应 `pNNNN`。数学对象编号独立于原稿不稳定的印刷公式编号；例如原(36)初次在 `original1025-p1003/m0442`，另有 `p1070/m0470` 和 `p1220/m0570`。`original1025-p0920/m0408` 才是原(31)的逆变换。

结构阅读器明确处理 OMML 分式、上下标、根号、定界符、矩阵、公式数组、积分/求和、上下极限、重音和横线。它不模拟 Word 字体和排版，也不是数学证明检查器；原始 XML 始终为最终判定依据。Word 的 `w:oMath` 空格式属性与包含公式的 `m:oMath` 命名空间不同，不能混计。两个文档其余 Word XML 部件没有额外 `m:oMath` 对象。

本轮完整顺序阅读原稿正文，包括末尾 A/B 证明；疑难矩阵、分式、脚标以原生 XML 核对。保存所有对象证明提取覆盖，不意味着原稿引用的外部专著全部定理已经在本轮独立复证。继承矩阵和专题审计分别记录证明、条件、数值、错误及待证状态。
