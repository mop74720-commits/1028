# 第三阶段 Codex 任务（轻量包版）

## 材料与边界
当前目录有 stage2/，包含第二阶段的真实三维 Cosserat 杆代码、12 自由度 Kirchhoff ROM、一般 Birkhoff 算例、少量原始 JSON 结果、论文符号/说明；references/ 有原稿、第一阶段审查 DOCX 和原始 Birkhoff ZIP。
本包是用于代码开发的小包，**未包含**原第二阶段完整 246 MiB 的所有大型轨迹/训练权重/旧 v10 历史数据；不要将缺失的数据编造为已复算。你的工作不要覆盖 stage2 已有文件。

最终目标仍为1025所写微重力环境下血管内三维磁驱动柔性机器人，包含三维杆、磁场、脉动血流、壁接触和控制。两模态仅作为历史回归基准。

## 本轮首要目标：落地真实三维 ROM 的一般 Birkhoff
1. 阅读 stage2/README.md、stage2/notes/route_a.md、stage2/program/learning/rod_rom.py、stage2/program/route_a/models.py 与 integrators.py、stage2/program/route_a/transport_moser_check.py，明确现有数学对象和数据的证据范围。
2. 在独立 stage3/ 中建立代码，从 12 变量位形的几何 ROM 取得 M(q), H(q,p), f(z,t,u), G_m(q) 及正则动量。不得漏掉位形相关质量导数项。
3. 从真实光滑 ROM 场尝试构造一形式 a、B 和 K=(Da)^T-Da，满足 Kf=∇B+∂_t a 与 K 的输运兼容性；记录场表示误差、二形式图匹配误差、收敛阶和构造成本。
4. 对同一个 ROM 比较原(36)矩阵化后的隐式中点、保守 Central4、合法图积分法与实际磁端口控制；必须分开保守、耗散、闭环输入等适用域，不把普通阻尼中点称辛方法，也不把拟合的 24 维状态增量当实际磁场。
5. 生成实际可执行测试与 JSON/CSV 结果，保存 stage3/program、stage3/tests、stage3/results、stage3/notes、stage3/README.md。
6. 完整复值 CHNN、共振正规形与KAM及真实流固耦合属于后续并行目标。不得因为尚未完成它们而虚构证书；第二阶段发现的 1:1 共振、SPD 网络域外失效以及磁控制失稳等负结果必须保留。

## 执行要求
先运行 python3 verify_starter.py 验证本轻量包全部文件与哈希，再根据 stage2/README.md 的依赖安装运行实际可运行的脚本。**不要运行 stage2/verify_delivery.py 来判定小包完整性：它要求原246 MiB大包中所有文件，精简包必然不满足该原清单。**
失败与环境缺失必须如实记录；不能声明未运行的三维仿真或新KAM证书已经完成。请开始阅读和实现，不要只生成报告。
