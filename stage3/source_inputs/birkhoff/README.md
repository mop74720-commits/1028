# 一般 Birkhoff 路线：本轮尝试材料

本包不改动原稿。它记录两个局部数学连接和本轮独立运行的检验。

## 阅读顺序

先读 `一般Birkhoff_两个核心连接与验证.md`，再读 `本轮数值结果.md`。
两个 Python 脚本分别输出自己的 JSON，使用固定初值和步长，可独立重跑。

```bash
python verify_general_birkhoff.py
python verify_v10_special_case.py
```

## 运行环境

Python 3.13.5; NumPy 2.3.5; SciPy 1.17.0; SymPy 1.14.0。
依赖可用 `python -m pip install numpy scipy sympy` 安装。没有下载数据或调用网络的步骤。

## 文件

- `verify_general_birkhoff.py`：变质量、非比例阻尼合成对象；普通中点与结构相容图表中点；端点相容性；独立 DOP853；理想控制。
- `verification_results.json`：上述全精度结果。
- `verify_v10_special_case.py`：v10 完整余弦势在比例阻尼分支的特例检查。
- `v10_results.json`：v10 参数、参考容差细化和全部步长结果。

## 重要边界

一般理论假设半离散动力学已正确表示为局部光滑正则 ODE。完整接触/约束事件、任意一般模型的低成本结构求解和 KAM 阈值没有在本轮全部解决。

变质量算例由已知非线性正则变换构造，K 由已知线性矩阵指数公式给出。矩阵指数也用于参考解；数值一步不是精确相流，而是平方根图表中的中点法。不能据此宣称已经实现了任意 f 的普适快速求解器。

结构保持结论指理想映射；浮点实验测量的是实现精度范围内的缺陷。并未通过事后为离散轨迹重新定义 K 来制造零缺陷。

没有覆盖或修改用户的原稿、v10 或此前方案。
