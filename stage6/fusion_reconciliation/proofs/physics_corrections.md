# 从融合稿能量净空到真实三维线圈端口

状态：下述几何界和功率恒等式是给定假设下的完整推导；实际 ROM 检验、受限电流及积分结果另存 `results/physics/`。有限采样不升级为血管安全或 KAM 证书。融合稿原公式本身在其声明的平面、固定偏置模型上成立；修复的是迁移时缺失的假设和第五阶段尚未实现的连接，而非改写历史原文。

## 1. 历史结果及不可直接迁移的两处

融合稿英文 `application.tex:240–285` 的 `app:clamped-identity`、`app:energy-bound`、`app:work-observer`、`app:work-governor`，以及 `supp_mechanics.tex:655–817` 的完整证明、初始化、误差包络和采样条件均需继承。原结论是固支 Euler–Bernoulli 梁

\[
\|w\|_\infty^2\le {2L^3\over3EI}E_{\rm bend}\le {2L^3\over3EI}H_0,
\quad H_0=T+E_{\rm bend}+E_0(1-\cos\theta)\ge E_{\rm bend}.
\]

它不是只对静态端载荷成立；Cauchy–Schwarz 等号由曲率正比于 \(L-s\) 实现。历史补偿算例初始能量为 12.6567 nJ，高于其 9.5187 nJ 上限，融合稿已明确没有用该算例验证此约束器。第五阶段已有完整线圈功率账，但没有实现这一功率约束器或三维净空界。

不能直接把旧 \(H_0\) 换成完整线圈 \(H\)：
\[
H=T+V_{\rm el}+V_{\rm coil},\qquad
V_{\rm coil}=-\sum_e\mu_e\cdot B(r_e,i)
\]
的磁势可以为负。本次实际三维共同初态和第五阶段偏置电流下，\(H/E_0=-1.00156326624\)，而 \((T+V_{\rm el})/E_0=0.000313158789143>0\)。直接声称 \(H\ge V_{\rm el}\) 是反例已证的错误迁移。任意平移一个常数也不能自动提供整个变化电流、位形域上的有效下界。本轮选择非负机械能并把全部磁功列为端口。

第二处是把平面曲率能界用于可剪切、可伸长杆。直杆可取 \(D=I\)、\(\Gamma=e_3+\varepsilon e_1\)，于是 \(\kappa=0\) 但末端偏移为 \(L|\varepsilon|\)。忽略剪切能的曲率净空界因此不成立。本次独立测试保留该反例。

## 2. 三维 Cosserat 的充分几何界

设参考为直杆，\(r(0)=0,D(0)=I\)，\(D\in SO(3)\)，
\(r_s=D\Gamma,D_s=D\widehat\kappa\)。无初始应变，且弹性能满足
\[
E_{\rm el}\ge\frac12\int_0^L
  [b|\kappa|^2+s_*|\Gamma-e_3|^2]ds,
\qquad b>0,\ s_*>0.
\]
这里 \(b\) 的单位为 N m²，\(s_*\) 的单位为 N。它们分别是弯扭刚度和剪切伸长刚度的统一下界；不同模量和各向异性允许用更精细权范数改善常数，但本式无需假设小转角。

令 \(d_3=De_3\)，则
\(d_{3,s}=D(\kappa\times e_3)\)，故
\(|d_3(s)-e_3|\le\int_0^s|\kappa_\perp(u)|du\)。于是
\[
\begin{aligned}
|r(s)-se_3|
&\le\int_0^s|\Gamma(u)-e_3|du+
          \int_0^s(s-u)|\kappa_\perp(u)|du\\
&\le\left({s\over s_*}+{s^3\over3b}\right)^{1/2}
 \left[\int_0^s s_*|\Gamma-e_3|^2+b|\kappa_\perp|^2du\right]^{1/2}.
\end{aligned}
\]
第二步是直和空间中一次带权 Cauchy–Schwarz，并未把两项各自的最大能量重复分配。因此
\[
\boxed{\sup_{s\in[0,L]}|r(s)-se_3|^2
 \le2\left({L\over s_*}+{L^3\over3b}\right)E_{\rm el}.}
\]
Kirchhoff 的不可剪切不可伸长分支令 \(\Gamma=e_3\)，删去 \(L/s_*\)。本轮代码使用实际 `RodROM.bending` 的最小特征值，保留扭转、两方向弯曲与所有几何运动学。

该界控制相对直参考线的整个中心线距离。若直通道与参考线同轴且可用中心线净空已扣除杆半径，才可导出该通道的充分净空；弯曲血管、运动壁、非直自然形、变化根部姿态必须另建相应几何估计。当前证明不含这些情形。

### 实际 20 单元几何 ROM 的离散版本

继承的 `RodROM.mechanics` 采用单元常体曲率和精确旋转（小角处为高精度级数）以及中点中心线增量 \(\Delta sD_{j+1/2}e_3\)。在精确旋转下，由上面的切向量变化界，对第 \(k\) 个节点，
\[
|r_k-k\Delta s e_3|
\le\Delta s^2\sum_{j=0}^{k-1}(k-j-\tfrac12)|\kappa_{\perp,j}|.
\]
带权平方和为
\[
\Delta s^3\sum_{j=0}^{k-1}(k-j-\tfrac12)^2
 ={(k\Delta s)^3\over3}-{k\Delta s^3\over12}
 \le{L^3\over3}.
\]
与 \(E_{\rm el}\ge\frac b2\sum_j\Delta s|\kappa_j|^2\) 配合，连续公式的常数对该离散嵌入仍成立。节点间线性插值时距离范数由端点上界控制。这里没有将中点求积误差假定为零。浮点 SO(3) 误差和四组随机真实三维应变场的界均由独立测试检查；不能据四点测试宣称任意幅值浮点实现严格守界。

## 3. 完整线圈、变质量的机械功率端口

原代码保持 \(z=(Q,P),\tau=\omega_0t\)，\(q=S_qQ\)，
\(\overline M=(\omega_0^2/E_0)S_q^TM(q)S_q\)。定义
\[
E_m=\tfrac12P^T\overline M(Q)^{-1}P+V_{\rm el}(Q)/E_0,
\quad \phi_j(Q)=V_{\rm coil}(Q,e_j)/E_0,
\quad G=-D_Q\phi^T.
\]
对固定电流求物理偏导，真实场为
\[
Q'=v=(E_m)_P,\qquad P'=-(E_m)_Q+G(Q)i-\gamma P.
\]
因此所有变质量惯性项相消于同一能量链，给出
\[
E_m'=y^Ti-\gamma v^TP,\qquad y=G^Tv,
\quad v^TP=P^T\overline M^{-1}P\ge0.
\]
这是第五阶段已经正确的磁能/虚功证明的复用，不另造磁力近似。实际 W 单位功率为 \(E_0\omega_0y^Ti\)。不得把能量 \(H=E_m+\phi^Ti\) 的参数功 \(\phi^Ti'\) 和机械磁功 \(y^Ti\) 重复计入一张账。

`power_port` 复用原完整 `mass` 与 `current_port`；独立测试比较自动微分的 \(\nabla E_m\cdot f\) 与上述端口恒等式，容差 \(2\times10^{-13}\)。新动力学每个积分阶段都直接调用完整 `CoilROM.field`，没有重放仿射轨迹、冻结质量或把任意12维力当作执行输入。

## 4. 恢复功率约束器并保留其证明责任

在连续时间、精确状态以及非空闭凸实际电流集 \(\mathcal I(Q)\) 上，可取
\[
i_* =\arg\min_{i\in\mathcal I(Q)}\tfrac12(i-i_{\rm req})^TR(i-i_{\rm req}),
\quad y^Ti\le\kappa(E_{\max}-W),\quad W'=y^Ti,
\quad W(0)\ge E_m(0),\ W(0)<E_{\max}.
\]
其中 \(R\succ0\)；所有电流单位相同，本实现用 \(R=I\)。若 \(0\in\mathcal I(Q)\)，则功率半空间与集合相交，强凸性给出唯一极小点。比较原理给出
\(E_m\le W<E_{\max}\) 及
\(E_{\max}-W\ge(E_{\max}-W_0)e^{-\kappa\tau}\)。结合第2节得到连续理想实现的直参考几何界。

实际加入 \(|i-i_{\rm prev}|\le S\Delta t\) 后，零可能不可行；本轮用真实 ROM 端口构造正功率的前一电流和极短变化时间，优化被明确拒绝。这是新增测试验证的反例，不采用“失败则输出零”破坏电流斜率条件。严格凸性不消除不可行性；SLSQP 数值成功亦不是区间严格优化证书。

本次新 `PowerCurrentAllocator` 在继承的 ±2 A、20 A/s、决策磁点 5 mT、0.03 T/m 约束上加入真实电流功率半空间。功率约束归一化只改善优化条件数，未放宽物理标准。实际执行端点之间的连续电流斜坡，保持幅值和几乎处处斜率界。但状态和 \(y\) 在斜坡中变化，故决策时刻约束**不是**整个区间的功率界。继承融合稿 `sm:discrete-work` 必须给出覆盖整个保持区间、传感延迟和几何不确定性的 \(P_k^+\) 才能完成采样净空证明。

本轮的 RK 阶段功率和实际积分账是数值观察，不冒充 \(P_k^+\)。可剪切全杆、移动流体、接触与壁功、未建模学习残差还需额外能量项或经过验证的外功上界。真实电流可达性、空间约束、功率约束、结构相容和 KAM 仍是不同责任。限制器改变请求动力学，即便观察到能量下降，也不证明保存原 Birkhoff 二形式或目标环面。
