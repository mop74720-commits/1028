# 第三阶段：真实三维 ROM、局部 Birkhoff 与磁控制

最终对象仍为空间站微重力条件下人体血管内的三维磁驱动柔性机器人。本目录实际连接原来的 **12 配置自由度、24 维相空间、20 单元几何求积** Kirchhoff ROM；没有把质量矩阵冻结，也没有用旧两模态梁替代它。

新增程序在 `program/`，数学测试在 `tests/`，实际输出在 `results/`，推导与限制在 `notes/`。`source_inputs/` 是已核对的原材料，不在其中运行会写结果的实验。原始 DOCX、三个 ZIP 和旧冻结结果保持不变。

## 环境与复算

本次计算使用 Python 3.12.14、CPU PyTorch 2.5.1、NumPy 2.3.5、SciPy 1.17.0。旧方向 A 单独使用 NumPy 1.26.4。当前云机器的研究解释器为 `/workspace/1028-cloud/venvs/learning/bin/python`；在其他机器上，可从仓库根目录按原始依赖清单建立仓库外虚拟环境：

```bash
research_env="${TMPDIR:-/tmp}/1028-research"
python3.12 -m venv "$research_env"
research_python="$research_env/bin/python"
"$research_python" -m pip install -r stage3/source_inputs/starter/stage2/requirements_learning.txt
"$research_python" -m pip install 'torch==2.5.1+cpu' --index-url https://download.pytorch.org/whl/cpu
```

复用当前云机器时，直接设置 `research_python=/workspace/1028-cloud/venvs/learning/bin/python`。随后从仓库根目录运行：

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export MPLBACKEND=Agg

python3 stage3/program/inventory.py
"$research_python" stage3/program/run_integrators.py
"$research_python" stage3/program/run_birkhoff.py --duration .0005
"$research_python" stage3/program/diagnose_birkhoff_window.py
"$research_python" stage3/program/control_experiments.py
"$research_python" stage3/program/control_coil_force.py
"$research_python" stage3/program/control_quadrature.py
"$research_python" stage3/program/control_learning.py
"$research_python" -m unittest discover -s stage3/tests -v
"$research_python" stage3/program/plot_integrators.py
"$research_python" stage3/program/plot_birkhoff.py
"$research_python" stage3/program/package_manifest.py
```

`inventory.py --network` 还核对上游 Git 标签。程序从文件位置定位原始 ROM；云环境配置草稿与安装脚本不属于本次 GitHub 交付。

上述实验会更新本目录中的相应新结果；要保留一次运行，请先另存该结果目录。旧基准复跑器保留在 `/workspace/1028-cloud/validate.py`：它自动建立仓库外副本，再运行所有会写输出的旧程序。已有 9 项基准的退出状态和日志已复制到 `results/baseline/`。

## 主要入口与证据

| 入口 | 实际内容与证据 |
|---|---|
| `rom_bridge.py` | 复用原始 SO(3) 几何，计算完整变质量 Hamiltonian、场、Jacobian、磁接口；`results/rom_bridge.json` |
| `birkhoff_rom.py`、`run_birkhoff.py` | 固定展开原点的一阶输运一形式，显式局部图、原场表示误差、近似场积分；`results/birkhoff/` |
| `rom_integrators.py`、`run_integrators.py` | 修正原（36）全残差中点、合法比例阻尼加权中点、非可分 Central4；`results/integrators/` |
| `control_experiments.py` | 真实磁接口上的补偿、势整形、共点阻尼、限幅；`results/control/` |
| `control_coil_force.py` | 完整 Biot–Savart 磁能独立差分及线圈/仿射模型差异；没有冒称完成线圈闭环轨迹 |
| `control_learning.py` | 新执行的单解析特征、无噪声残差拟合及真实磁补偿；`results/control_learning/`；不是完整 CHNN 重训 |
| `inventory.py` | ZIP、DOCX、源码、缺失文件和已执行基准清单；`results/material_inventory.json` |

## 实验口径

所有新动力学使用同一实际 ROM 和初态规则，采用无量纲时间 `tau=omega0*t`，能量 `H/E0`；实际缩放和 SI 值记录在 JSON。积分器/磁控制主窗口 `tau=.004` 约为 **0.897 ms**，只是高频全模态短时验证，不是血管导航任务时长。保守、比例阻尼、非比例阻尼与不同闭环分别指定其真实参考场，不能跨分支混报误差。

一般 Birkhoff 研究首先尝试同一 `.004` 窗口。其一阶表示在高频模态上离开有效局部近似尺度，表示场参考计算在 246 秒后主动中止；记录、未完成项与日志均保留。完成态局部实验使用 `.0005`，其内部所有方法使用相同初态、终时和网格，并分别比较原场参考与实际表示场参考。**不能将这个局部结果写成长窗口 Birkhoff 成功**。`window_diagnostic.json` 的瞬时特征值也不能单独证明非自治轨迹失稳。

二形式匹配、原场表示误差、求解器残差、积分误差分别报告。结构诊断是首步理想隐式切线抽样；浮点结果不是全域严格证书。参考解只用于评估，不作为推进器的免费输入。

## 已知范围与缺失数据

此分析 ROM 是不可伸长、不可剪切的三维 Kirchhoff 几何层。原始 Cosserat 程序仍保留剪切、伸长、规定脉动血流、刚性管腔接触和摩擦；本次新控制尚未在 32/64 段模型上完成长时闭环验证。ROM 的测试阻尼 `Gamma P` 是明确指定的光滑载荷，不冒称完整血流/接触降阶闭合。

轻量包包含 37 个 Python 文件，但不含冻结的 `.pt/.pth/.npy/.npz` 学习数据/权重。具体缺失路径见 `material_inventory.json`；例如 `stage2/results/learning/learning_data.npz`、`complex_seed1025.pt`、`analytic_coefficients.npy`、`learning_summary.json` 及冻结确认集。完整 CHNN、公平重训、Legendre/正质量全域保证、三维共振正规形和新连续/离散 KAM 证书未在本轮完成。旧 v10 的对应历史成果保留其原始对象和证据身份。

主推导见 `notes/theory.md`；局部接入与失败分析见 `notes/birkhoff_experiments.md`；材料和原审查对应见 `notes/materials_and_scope.md`；积分器结果见 `notes/integrators.md`；磁控制与线圈反例见 `notes/control.md`。完整双向 FSI、柔性血管壁、真实微重力生理标定和有限幅值三维 KAM 均仍属后续工作。
