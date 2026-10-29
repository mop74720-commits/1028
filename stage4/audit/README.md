# 1025 全路线继承与数学审计

审计起点：`38ee6a7fb8f279fc80be05ee2bd4956817364ffc`。先读 [最终结论](final_verdict.md)，逐项证据见 [继承矩阵](full_inheritance_matrix.csv)。本目录包含原生公式索引、修正推导、可执行反例和新复算数据；不是完整新论文或新三维 KAM 证书。

十项交付为：`1025_master_route.md`、`full_inheritance_matrix.csv`、`missing_or_weakened_results.md`、`birkhoff_full_audit.md`、`chnn_kam_inheritance.md`、`physical_and_control_audit.md`、`proof_errors_and_corrections.md`、`reproduction_and_tests.md`、`proposed_complete_manuscript_structure.md`、`final_verdict.md`。

矩阵包含115条记录。六个继承字段分别回答文件存在、最新文字提及、完整推导继承、算法实际复用、新三维验证、数学推广证明；取值保留限定语，不转换成总分或“正确率”。原稿重复编号以原生段落/数学对象ID定位。专题分片及生成脚本保留在 `matrix_parts/` 和 `program/`。

从仓库根目录运行，使用已有学习环境；不同机器将路径替换为具有记录版本依赖的解释器。环境安装草稿不属于交付。

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
research_python=/workspace/1028-cloud/venvs/learning/bin/python
python3 stage4/audit/program/extract_omml.py
python3 stage4/audit/program/verify_omml.py
"$research_python" stage4/audit/program/birkhoff_counterexamples.py --with-rom
"$research_python" stage4/audit/program/chnn_audit_checks.py
"$research_python" stage4/audit/program/physical_audit_checks.py
python3 stage4/audit/program/reproduce_audit.py
"$research_python" stage4/audit/program/compare_reruns.py
python3 stage4/audit/program/assemble_audit.py
```

这些命令会更新本审计目录的新结果；复现运行器把会写文件的第三阶段测试/实验放进仓库外副本，保留冻结源码与数据。机器依赖路径和完整命令见 `reproduction_and_tests.md`，第二阶段线圈算子另见物理审计的实跑日志。原长窗口中断文件明确为历史复制，没有本轮重跑标记。

`results/start_provenance.json` 保存起点479个跟踪文件哈希；`results/frozen_preservation.json` 保存复现后的比较。`source_omml/` 保留原DOCX XML及逐公式对象，`external_v10/manifest.json` 记录固定提交下载的原文路径和哈希。缺失大型S1、训练权重与确认集的具体路径见CHNN审计和 `stage3/results/material_inventory.json`，历史结果不会因缺数据而删除，也不会冒充本轮验证。
