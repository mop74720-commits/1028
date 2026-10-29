# 高阶自动微分失效的独立定位与安全替代

## 可执行的最小反例

本轮实际环境为 PyTorch `2.5.1+cpu`、float64、单线程。令

\[
H(q,p)=\frac{p^2}{2(1+q^2)}
=\tfrac12p^2-\tfrac12q^2p^2+O(\|(q,p)\|^6).
\]

所以原点 `H_qqpp=H_ppqq=−2`。实现为 1×1 `torch.linalg.solve` 时，`jacfwd(jacfwd(hessian(H)))` 实际给出某个排列分量 `H_ppqq=0`，而纯反向微分给出 −2。同一个数学函数用普通除法或 `torch.linalg.inv` 表达，已执行的二/三/四阶检查均与解析除法一致。`M(q)=1+q` 时三阶已经能出现错误；原杆选定子空间原点的 H3 为零并不能排除问题。

这不是完整杆的错误物理公式，也不是“所有 forward AD 均错误”的结论。实际不同嵌套有差别：以 R/F 表示按执行构建顺序的反向/前向导数，最小例子的 RRF、RRRF 与纯反向一致，而 RFR、RFFF 等路径错误。完整模式表保存在 `stage5/results/high_derivatives/minimal.json`。

上述结论仅针对已记录版本和执行路径，未断言所有未来 PyTorch 版本都有相同问题。测试把“发现已知错误并阻止静默使用”作为通过条件，不把错误张量冒称数学导数。

## 对称化不能修复错误导数

四阶方向收缩 `T[v,v,v,v]` 对张量任意指标置换不变。因此先将错误 T 全置换平均，也不会改变其错误的方向收缩。最小例中 v=(1,1) 的四次项系数由错误张量给出 −5/12，正确值 −1/2。简单地把 Hessian 或更高张量与转置平均，只能强制一个必要的对称性，不能证明它来自原函数。

本轮真实 ROM 在原点选 `(Q0,Q1,P0,P1)`，方向 `(1,0,0,−1)`：混合路径的 H4 全置换缺陷约 1738.904823，收缩/24 为 144.912160067；独立纯反向标量四阶为 434.726041642，有限半径 `.004/.002` 的偶能量四次系数为 434.725727628/434.725977001。旧坏张量和本轮新坏张量分别保存，不互相覆盖。

## 替代路径的证明责任

对每一个实际位形重新计算

\[
H_{AD}(Q,P)=\tfrac12P^T\bar M(Q)^{-1}P+H_{base}(Q,0).
\]

这里的逆是当前完整质量矩阵的逆；它没有冻结质量，也没有删掉几何惯性。数学上与原 `solve(M,P)` 相同，但数学等价本身仍不足以证明 AD 实现正确，所以本轮另比较其实际高阶方向收缩、独立纯反向和有限差分。原场参考积分继续使用原 `solve` 的低阶场实现，确保没有把一形式表示误差藏进被更换的原场。

一般 Birkhoff 系数的 `jvp/vjp` 嵌套会经过高阶导数；必须核对 b2 数值、b2 Hessian 的实际收缩以及 Db3 的方向作用，不能只检查对称性。`verify_high_derivatives.py --section transport` 在真实 24 维 ROM 上使用少量标量方向和四维输入子空间，避免建立 24⁴ 张量，并与全反向 Lie 公式交叉检查。

本次已经实际完成这些独立检查，并非待执行方案。`rom.json` 中替代实现的 H4 全指标置换缺陷为 `2.2737e−13`，同一方向的四次系数 `434.7260416422407`，纯反向为 `434.7260416422408`。`transport.json` 中两条方向的 inverse 实现 Db3 与独立纯反向值之差分别为 `7.1054e−14`、`5.6843e−14`；旧 solve 混合路径则分别错 `0.2844011`、`0.3448673`。

`verify_high_derivative_cache.py` 进一步读取本轮早期实际保存的 `prototype_r3_jac3_source_hess2_Db3.npy`，独立收缩也得到上述错误，故不能用它缓存的新图结果作通过证据。另一方面，同一旧缓存的 D²b2 在这两条方向上与独立反向相符至 `5.6e−14`。这里按具体张量判定，不把已发现的 Db3 错误扩大成“所有旧系数均错误”，也不把两条正确方向提升为整个张量的证明。结果及旧文件 SHA 位于 `legacy_cache_comparison.json`。

当前 `transport_native.py` 在这次独立验证之后只增加了独立数值力回调，以使参考场继续走原 solve 路径。`verify_high_derivative_source_bridge.py` 先核验保留源码的 SHA 与三份实际执行报告相同，再逐方法比较 AST：一形式递推、高阶 Hamiltonian、符号向量场和 Lie 导数函数均未改变；改变的是构造器和两个数值包装器。`current_source_bridge.json` 保存这一源码证据。它不能替代新的回调物理一致性检查，后者另见 `stage5/results/coil/transport_interface_check.json`。

旧 Central4 实现使用反向 `torch.autograd.grad` 的完整标量生成函数，且在新全线圈 ROM 已实际测得 3.996642 阶。没有发现本轮故障影响它；这不是仅凭方法名称作安全断言，而是其导数实现和收敛数据不同于失效路径。

## 复算与状态

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /workspace/1028-cloud/venvs/learning/bin/python stage5/program/verify_high_derivatives.py --section all
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /workspace/1028-cloud/venvs/learning/bin/python -m unittest discover -s stage5/tests -p test_high_derivatives.py -v
PYTHONDONTWRITEBYTECODE=1 /workspace/1028-cloud/venvs/learning/bin/python stage5/program/verify_high_derivative_cache.py
PYTHONDONTWRITEBYTECODE=1 python3 stage5/program/verify_high_derivative_source_bridge.py
```

每节的独立 JSON 保存实际执行状态、时间、源码 SHA、版本和异常；NPZ 保留原始张量，不对坏数据做覆盖修复。高阶正确性仍是有限选点检验，尚非整个解析域上的严格误差证明。
