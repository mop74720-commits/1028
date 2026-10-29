# 修复与继承账本的读取、证据和重建

`repair_status.csv` 逐项保留 E01–E16 的原始审计位置/原文，并分别列出错误分类、正确公式、修正代码、完整测试名、实际采用模块及尚缺条件。确认错误、原定理假设不足、符号约定下的条件性错误、过强表述没有混为一种错误。原稿后附本已有正确递推/因子的内容和旧补充材料正确 Rayleigh 解码也明确保留。

`inheritance_update.csv` 的前21列逐值等于第四阶段115条记录；第五阶段只追加新的六层继承状态和精确证据。这里的六层是材料存在、正文提到、推导继承、程序复用、三维验证、推广证明。新增程序或运行通过不能自动把后五层都改成 yes。旧两模态证书保持旧对象身份，完整新论文仍未形成。

完整端点定理、初始非零生成函数规范、变质量中点和原（36）左解见 `../proofs/corrected_mathematics.md`。完整CHNN/误差桥、64平面提升的有效证明以及旧KAM适用边界见 `../proofs/chnn_kam_restored.md`。实际图方法的窗口、缓存、原场误差与拒绝的AD结果见 `../proofs/birkhoff_transport.md` 及相应结果。这些证明职责没有因20项恒等式/反例测试或115条账本完成而全部闭合。

## 独立helper与实际模型采用

- Morison量纲、实接触、Darboux/独立扭转、复坐标和Rayleigh修正有可执行独立函数。实际全杆复用了自己的正确拖曳/接触/标架模块，并不是统一调用这些helper；完整附加质量和双向FSI尚未接入。
- 真实ROM继续求完整 `M(q)` 与几何惯性；原（36）的常矩阵闭式只用于独立非交换回归。实际全线圈闭环采用未知中点完整场残差和反馈Jacobian。
- 新复网络训练实际使用正确正则梯度缩放，未沿用原错误损失。但开放系统机械功率损失和真实学习闭环尚未因此完成。
- E15修正保留原辛体积用途，给出非零作用周期与移动参考原函数；没有重新认证旧冻结环面或得到新的三维KAM。

## 重建与位置核验

基础逐项决策来自 `program/build_ledger_manifest.py`，后续证据采用独立JSON更新清单。`program/update_inheritance.py` 只允许更新新增列，拒绝未知ID、缺失证据、无效代码函数锚点，并逐值断言原115×21字段未变。最后一次实际导出的完整命令、清单顺序与SHA在：

```
stage5/results/ledgers/latest_build.json
```

复算应照该文件的 `command` 顺序传入全部 `--updates`；仅执行基础清单会丢失后续已补的状态，但不会改变冻结原表。通用调用形式为：

```bash
python3 stage5/program/update_inheritance.py \
  --updates stage5/results/ledgers/stable_branch_updates.json \
  --updates stage5/results/ledgers/learning_and_proof_updates.json \
  --updates stage5/results/ledgers/transport_final_updates.json
```

输运最终清单由 `program/build_transport_ledger_update.py` 在确认主实验、独立导数、同场功率和参考桥均完成后生成；它拒绝将运行中的数据升级为完成，并保留被替换的旧清单。如果以后还有更新，须照最新build记录追加，不可把上述清单当所有未来版本的永久全集。每次重建另存带时间戳的build记录。`source_locations_latest.json` 将表内实际Python文件、函数、测试定位为行号和当时文件SHA，避免只写抽象算法名。

一次证据锚点修复把 `current_power_port` 正确定位到 `rod_transfer_control.py`，不改变数值结果。旧清单在 `stable_branch_updates_before_anchor_fix.json`，其内容由精确补丁反向重建并与此前build的SHA一致；`anchor_fix_provenance.json` 明记这一事实，不冒称是当时另存的快照。

独立数学测试历次18、19、20项日志全部保留在 `results/corrected_identities/runs/`；指针 `latest.json` 对应最近一次真正运行。统一模块测试另存 `results/tests/`，原始阶段3的23项回归从外部临时副本运行，见 `results/regression/`。数学/物理结论依据具体证明与实验，不以测试数或表格行数作为研究完成率。
