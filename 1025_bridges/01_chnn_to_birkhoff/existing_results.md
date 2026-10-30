# 已有成果：本桥直接继承、最小修正和未完成项

本轮基线为 `stage6/fusion-reconciliation` 的实际提交 `2b774acf2a76aefbe732c649a1f02d0fafea3b79`。只写本目录；原1025、旧v10、stage4/5/6保持冻结。状态词分别指“可以直接继承”“需要修正其跨对象使用”“尚未实现/未认证”，不以文件存在当作本轮再验证。

## 逐项可复用位置

|已有位置|已核对的具体内容|本轮判定及使用方式|
|---|---|---|
|`stage4/audit/1025_master_route.md`，原生索引p0150–0171、p0338–0370、p0529–0600、p0793–0851|原始物理→正则动力学与学习/一般表示的分支，原12与复数解码及混合偏导问题|可以直接继承定位；重新回查DOCX原生OMML，不能用第四阶段摘要替代原稿|
|`stage4/audit/proof_errors_and_corrections.md` E04/E05/E06/E12/E13/E16|复归一化、损失功率、错误一形式、二形式系数/符号、Rayleigh动量解码|已确认修正直接继承；本轮只复核影响第一个接口的部分|
|`stage5/proofs/corrected_mathematics.md:54–108` R3–R6|1/√2 Wirtinger、实际功率损失、完整变质量几何力、Rayleigh先对速度求导|可以直接继承；原稿不一致不能通过重新记号隐去|
|同文件`:110–151` R7–R10|K=(Da)ᵀ−Da、完整变分符号、闭性/非退化分离、时间相容、混合偏导反例|可以直接继承；对已声明f构造，CHNN不是存在定理前置条件|
|同文件`:153–298`|原A/B的端点匹配、横截性、局部生成/固定坐标递推|已正确证明，直接保留；本轮仅列下一步输入条件，不再开发|
|`stage5/proofs/chnn_kam_restored.md:5–27`|物理缩放、x=Dz与正则梯度、实能量/复隐藏层、实际耗散和功率|可以直接继承，作为本轮对象定义和尺度检查|
|同文件`:29–53`|完整复网络三阶门控/动量偶性，SPD与机械字典的不同性质，负Hpp和反解限制|可以直接继承；正机械字典证据不能转给完整复网络|
|同文件`:55–112`及旧固定 `stage4/audit/external_v10/sections/theorem_bridge.tex:180–264`|有限特征Gram误差桥和另外的条件统计强范数链|条件证明可直接继承；不是本冻结完整网络已有统一实/复域误差，原35项常数不得移植|
|旧固定 `stage4/audit/external_v10/sections/core_analysis.tex:70–140`|35特征的实能量读出、正则场误差等于梯度误差、动量相关项和观察尾差|可以直接继承误差逻辑；本轮不用旧两模态参数/证书替代三维对象|
|旧整合 `stage3/source_inputs/v10/v10_framework_20261028/english/sections/mechanics.tex:260–314`，标签`mech:complex-chart,wirtinger,decoder,power`|实能量及独立耗散读出；复解析延拓与H+iD不同；速度微分顺序|可以直接继承正确解码；本轮不学习新的耗散分支|
|同包 `structure.tex:165–221`，`struct:objects,plant`|名义、真实、学得、补偿后四种Hamiltonian不混同；该包最小主实验只学势残差|正确对象区分可继承；单势系数不是原完整CHNN的一般限制|
|同包 `supp_structure.tex:1–22`，`ss:birkhoff-compatibility`|一般场局部逆流输运的存在证明|可以直接继承；未知精确流不得作为算法输入|
|`stage3/source_inputs/birkhoff/一般Birkhoff_两个核心连接与验证.md:16–148`，式(1)–(4)|独立正则入口、局部一形式输运/高阶系数、规范保留B=H|可以直接继承完整局部证明；本轮不重复开发Moser/生成法|
|同材料`:269–303`|eB、实际表示场f_a=f−K⁻¹eB及条件有限时间误差|可以直接继承；本轮增加学得场—真实场这一独立误差项，符号逐项核验|
|`stage5/program/learning_models.py:14–49`；第二阶段 `run_learning.py:19–47`|三种模型工厂；完整ComplexResidual的全复参数、实读出、共轭、split tanh、P偶性|直接导入既有网络，不重新训练、不造旧权重|
|`stage5/results/learning/S5_L01_protocol.json`；`S5_L01_complex_hidden_seed51001.pt`|12DOF/20单元/H_ideal；a=.08，D，训练损失及冻结参数|直接加载并核对身份；测试/OOD和已有负结果不删除|
|`stage5/proofs/birkhoff_transport.md:5–61`，式(1)–(3)|齐次输运、机械有源规范、原生截断、保守精确分支|证明机制可直接继承；ℓ=T−V须改为一般ℓ=P·h_P−h后用于完整网络|
|同文件`:63–102`；`stage5/program/transport_cache.py:13–130`|一形式空间缓存、原场不缓存、eB及表示场Jacobian|直接复用算法；需用学得f重新形成相应系数，旧真实场b2缓存不能重贴标签|
|`stage5/program/transport_native.py:36–56,80–83`|高阶H的机械重建与a1二次动量shortcut|对原物理ROM正确；跨入非二次完整网络需要最小adapter：直接Hhat、一般a1=-L_f a0|
|同文件`:58–72,85–111`|现有光滑R和Lie导数/有源系数递推|可以直接继承；“正系数”不是全域非正功率证明，参见S5输运证明:149|
|`stage6/fusion_reconciliation/notes/kam_reconciliation.md`及`proofs/kam_budget_corrections.md`|理想/全线圈/学得对象分开；新机械模型正定小域不消除旧负样本|直接继承边界；本轮不扩展KAM或预算工作|
|`stage6/fusion_reconciliation/proofs/nonautonomous_transport.md:31–90` N3–N7|ℓ=P·H_P−H、有源卷积和eB=-S；空间/时间/场误差分离|正确一般恒等式可以直接继承；本轮只用已有自治光滑R，不新增时间调制|
|`stage6/fusion_reconciliation/notes/learned_reference_tracking_proof.md:51–69`；`program/learned_reference_tracking.py:25–60`|真实加载完整复网络、x=Dz正则解码；明确H_ideal目标与H_coil plant不同|直接复用网络解码逻辑；其完整线圈跟踪不是网络已学准线圈的证明，本轮不新做控制|

上表中的路径均相对仓库根。原稿段落p/数学m使用第四阶段DOCX顺序锚点，不假造稳定页码或缺失公式号；本轮原生节点证据另保存。

## 尚未由已有结果解决的最小接口

1. **同一完整网络与同一非保守场的Birkhoff实际接线。** 之前完整网络训练/参考与高阶输运各自存在；不能仅将物理ROM的a/B缓存称作学得场的表示。本轮只增加明确Hhat适配和误差记录。
2. **机械shortcut的适用对象。** 完整网络有高于二次的P项，动量偶性不等于二次性。禁止用原物理质量重建Hhat或以 `2H(Q,0)-H` 代一般 `H-P·H_P`。保守分支直接a0/K0/Hhat，无需截断。
3. **三个误差的连接。** 明确记录δf、eB以及 `e*=eB−Kδf`；实际表示场与真实场的差为 `δf−K⁻¹eB`。已有输运的近零闭性/图匹配不能补上δf。
4. **机械可逆域与相空间表示域分开。** 完整网络实值且光滑足够给局部Hamiltonian/Birkhoff；Hpp负值阻止全域正质量解释。原点门控只提供局部正定存在，不提供既定盒的统一常数。

上述接口已在本轮 `program/bridge_interface.py`、`program/run_bridge.py` 与 `results/B01_run03/report.json` 实际连接，未重写旧网络/递推/缓存算法。程序同时完成了针对PyTorch2.5.1复共轭张量默认vmap限制的逐行反向AD适配；这是运行后确认的后端问题，失败记录保留，不能当作数学存在性失败。独立网络负结果见 `results/network_checks.json`、`network_power_witness.json`；完整误差分解和明确成立域见 `mathematical_bridge.md` B17–B21及实测表。

## 本轮不会重新完成或擅自扩展的事项

旧KAM、完整Theorem A/B推导、原30–36积分算法、线圈设计、全杆流接触及网络训练全部保持已有身份。本桥只列它们可能需要的接口条件。没有认证完整复网络统一复域误差、实际血流/接触中的一般图、所有状态的Legendre正定性或原始生理目标。已有具体失败不得用本轮短窗/小域成功覆盖。
