# 16自由度共同步长 h=0.025，T=2 的实测汇总

一般跨块组的 K 缺陷是三个步骤样本最大值，其余为全步最大值；成本为三次中位数，冷启动含图构造。

| 模型 | 方法 | 全网格最大误差 | 观测阶 | K 缺陷 | 冷启动秒 | 构造秒 | 缓存推进秒 |
|---|---|---:|---:|---:|---:|---:|---:|
| block_weighted | ordinary_midpoint_eq36 | 7.667935e-05 | 1.999350 | 2.075617e-06 | 0.053811 | 0.000004 | 0.052488 |
| block_weighted | weighted_chart_midpoint | 6.711364e-05 | 1.999162 | 1.555208e-15 | 0.034565 | 0.000022 | 0.035299 |
| block_weighted | weighted_chart_gauss4 | 1.072807e-09 | 3.999773 | 1.333032e-15 | 0.075112 | 0.000003 | 0.072830 |
| block_weighted | frozen_current_weighted | 6.730852e-05 | 1.995906 | 8.138298e-06 | 0.028131 | 0.000024 | 0.029065 |
| conservative | ordinary_midpoint_eq36 | 8.287256e-05 | 1.999201 | 8.884502e-16 | 0.050959 | 0.000003 | 0.051413 |
| conservative | canonical_chart_midpoint | 8.275566e-05 | 1.999202 | 1.110229e-15 | 0.030888 | 0.000003 | 0.031122 |
| conservative | canonical_chart_central4 | 7.704358e-09 | 3.999387 | 1.110242e-15 | 0.059507 | 0.000003 | 0.073063 |
| generic_nonproportional | ordinary_midpoint_eq36 | 9.879047e-05 | 1.999324 | 2.829159e-06 | 0.050609 | 0.000004 | 0.051860 |
| generic_nonproportional | canonical_chart_midpoint | 9.882546e-05 | 1.999325 | 2.816666e-06 | 0.032932 | 0.000003 | 0.034001 |
| generic_nonproportional | damping_split_midpoint | 9.018572e-05 | 1.999102 | 2.986422e-07 | 0.043176 | 0.000245 | 0.035269 |
| generic_nonproportional | gauss4_chart | 1.795071e-09 | 3.999714 | 7.449379e-11 | 0.087070 | 0.000003 | 0.082451 |
| linear_known_chart | ordinary_midpoint_eq36 | 7.726417e-05 | 1.999309 | 1.305367e-06 | 0.059515 | 0.000004 | 0.075332 |
| linear_known_chart | matrix_chart_midpoint | 7.169256e-05 | 1.999231 | 2.132607e-14 | 0.167058 | 0.156844 | 0.010120 |
