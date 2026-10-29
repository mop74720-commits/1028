# 最终报告独立内容审读：必须修正项

阅读范围：`report/00_scope_versions.md`、`01_physical_framework.md`、`02_learning_metriplectic.md`、`03_birkhoff_bridge.md`、`04_synthesis_reproduction.md`全部正文；并检查构建器如何纳入 `notes/v10_baseline.md`、`route_a.md`、`learning_confirmation.md`、`learning_spd.md`。对照已完成旧基准复算、独立学习评估、新确认集。未修改root报告，没有新增实验。另回读Feng–Qin第15章3.5、3.7、4.1、4.4、4.5，以及118页审查对Shang原文的对应条件。

## R1：L4的阻尼符号必须明确定义，避免多除一次频率

位置：`02_learning_metriplectic.md` §8.4，L4。

当前写 $(\gamma/\omega_0)P_{\rm ref}$，但此处没有定义 $\gamma$；旧v10部分通常将 $\gamma$ 用作已经无量纲化的阻尼。新程序实际是 `mass_proportional_damping_rate_s_inv / omega0 * P`。

建议直接改为

$$
U_{\rm req}=P_{\rm ref}'+(h_{\rm model})_Q+
\frac{\alpha_s}{\omega_0}P_{\rm ref},\qquad
\alpha_s=2\ \mathrm{s}^{-1}.
$$

若保留 $\gamma$，应先定义 $\gamma=\alpha_s/\omega_0$，然后只写 $+\gamma P_{\rm ref}$。root已确认采用前者。

## R2：L5应明确绑定Shang解析小扭转版本，并补齐关键假设

位置：`02_learning_metriplectic.md` §8.5，L5前后。

该不等式及 $\tau_D>n+1$ 是所选Shang/Feng–Qin小扭转定理的可用条件，不是所有离散KAM定理的统一必要条件。当前正文没有写全整数范围、角周期约定、频率域边界与实际小量阈值。建议补一段具体定理接口：

“以下采用Shang 1999 Theorem 2的解析小扭转版本，角变量周期为 $2\pi$。理想映射在固定复域内由全局周期生成扰动 $P_h$ 定义：

$$
\widehat I=I-h\partial_\theta P_h(\widehat I,\theta),\qquad
\widehat\theta=\theta+h\omega(\widehat I)+h\partial_{\widehat I}P_h.
$$

$H_0(I)$ 解析，$\omega=\nabla H_0$，并有 $0<\vartheta\le\Theta$ 的扭转导数上下界。选 $\tau_D>n+1$、$0<\gamma_D\le\min(1,r\Theta/2)$；保留频率距频率域边界至少 $2\gamma_D$，且对所有 $0\ne k\in\mathbb Z^n$ 满足L5。解析扰动还须满足

$$
\|P_h\|_{r_0,\rho_0}
\le\delta_0\gamma_D^2\vartheta^2\Theta^{-3}.
$$

$\delta_0$ 和域宽等常数需按所选定理核算；测度结论还要求频率域的type-D等几何条件。当前没有对新三维模型核验这些条件。”

依据：118页审查§14.1及§15.3中第13章的核验；Shang 1999 Theorem2；Feng–Qin第13章Theorem2.4、原(2.38)、(2.40)。无需把全部证明移入正文，但上述条件应使L5不被单独误用。root已确认补充。

## R3：L6不能将任意求解/图误差直接吸收入KAM小量

位置：同节L6。

小的Newton残差、小的二形式匹配缺陷与exact symplectic性质是不同事项。一般有限迭代输出并非exact symplectic；任意图误差也未必对应同一周期生成函数类内的扰动。经典映射KAM不能只因这些误差很小便适用。

建议将结论明确限定为理想、精确求解的解析exact-symplectic映射。只有另外证明求解实现/图误差仍可表示为同一exact-symplectic类内的周期生成扰动时，才允许把它们列入L6的 $\varepsilon_{\rm solve},\varepsilon_{\rm chart}$；否则它们只能进入A14—A15型有限时间轨迹或结构实施误差估计，不进入经典KAM小量阈值。root已确认如此收紧。

已扫描附入的 `route_a.md` 与 `v10_baseline.md`：未发现另一个把任意求解误差直接作为KAM扰动的独立主张。route_a§8.3明确要求固定/周期exact-symplectic映射；v10§9.4的 $\|G_\Delta/\Delta\|\le C_3\epsilon+C_4\Delta^p$ 是理想生成函数预算，且已区分连续旧证书与离散KAM。可在v10该处加“理想隐式映射；有限迭代误差另验”作交叉提示，但不需要改变该预算本身。

## R4：Theorem A/B接口需给出初时横截条件和生成梯度初值

位置：`03_birkhoff_bridge.md` §7.2，A4—A7。

当前A4的二形式适配、A5的对称性、A6的固定初始端点推导、A7的幂系数系数都正确；“不要求N可逆”和标量势的规范自由度也已正确修复原书/原稿问题。

缺少的是把Theorem4.1和4.5真正变为可执行局部初值构造的两个条件。建议在A5后补：

$$
\det\big(C_\alpha(z,z,t_0,t_0)+D_\alpha(z,z,t_0,t_0)\big)\ne0,
$$

并以

$$
w_0=\alpha_2(z,z,t_0,t_0),\qquad
f_0(w_0)=\alpha_1(z,z,t_0,t_0)
$$

作为A7的初始梯度。一般图不能任意设 $f_0=0$；否则即使递推保持“梯度”，也不一定从恒等流出发。

由Theorem3.7回到端点时，还需截断图的逆横截性，例如用 $D\alpha^{-1}$ 的对应块写 $\det(C^\alpha N_m+D^\alpha)\ne0$；它在正确初值、解析性和足够小步长下由连续性保证。这样才能严谨调用Theorem4.5给局部 $m$ 阶保K格式，而非只检查精确相流上的 $\det(C_\alpha M+D_\alpha)$。

依据：原书第15章Theorem4.1原(4.1)，印刷625—626；Theorem4.4原(4.10)，印刷628；Theorem4.5及其对Theorem3.7的调用，印刷629。这里没有发现A7的阶乘错误：$[h^j]/(j+1)$与原书总导数除以 $(j+1)!$ 一致。

## R5：F17应明确接触激活与实际法向阻尼系数

位置：`01_physical_framework.md` §5.4，F16—F17。

建议把间隙直接定义为 $g=R_v-a-d$、$\delta=[-g]_+$。当前“$g=-\delta$，接触外另定义”虽表达了意图，但不如一个全域有符号间隙清楚。

更实质的是F17未显式限定接触活动域，容易被读成分离时仍有法向阻尼。实际程序仅在 $\delta>0$ 时计算接触力，且每单位参考长度采用

$$
c_n(\delta)=2\zeta\sqrt{\rho A\,r k_c\delta^{r-1}},\qquad
\lambda_n=k_c\delta^r+c_n(\delta)[v_{\rm rel}\cdot n]_+.
$$

应写“F16—F17仅在 $\delta>0$ 生效，$\delta=0$ 时接触耗散和摩擦置零”，或明确采用上述随 $\delta$ 消失的 $c_n$ 及总法向力 $\lambda_n$。这样文本与 `rod3d/model.py` 的接触门控、摩擦锥和功率相符。

若谈开闭正则性，弹性力 $\delta_+^{3/2}$ 为C¹的结论正确，但不能据此称整个接触场C¹：实际阻尼系数在该指数下含 $\delta_+^{1/4}$。正文目前没有宣称整个接触场C¹，保留这一限制即可，不需要扩大实验。

## 已通过的内容与覆盖结论

1. 原v10后半段对照已齐全纳入第4章：固定35/45特征真实算法、三份不同冻结拟合、完整非可分Central4、连续有限幅值环面、超薄管测度/有限分类区分、平面64自由度磁提升、Legendre条件、全杆净空、S形跟踪、未知物理/状态噪声、因果适应、S2稳定边界与误差容限。没有将原64平面结果写成三维，也保留静态前馈优于旧CHNN的对照。
2. 旧证书本轮只重验一个冻结主模型，未移植为新参数、新3D或离散KAM证书；COMSOL、200 s续算、大扫描及主动限功未完成重积分均有边界说明。数值未见影响结论的误抄。
3. 新学习测试/确认集的坐标范数、三种子、Hessian反例与不同容量限制，与独立JSON一致。旧探索结果和新冻结确认结果分列，没有互相替代。
4. 正质量结构的精确代数结论与实际拟合失败、病态条件数区分正确；它没有消除原三维1:1共振。对实际前馈仅使用已知M(q)和学习H_Q的范围也一致。
5. Metriplectic M1—M5的因式分解、退化条件、熵/内能坐标转换均正确；没有把外部血流功率全部转成内部耗散，也没有把奇维退化Poisson矩阵强行反演成Birkhoff结构。

除R1—R5及root已确认的相关补充外，未发现需要改变总体研究结论的事项。待最终版生成后可进入逐页视觉QA。

## 主报告落实记录

上述R1—R5已在最终组装前落实：L4明确物理耗散率α_s；L5、L5a、L5b列出所选定理的映射、全整数条件与实际阈值形式；L6限定理想exact-symplectic类；A5—A7补初值及截断图逆横截性；F16—F17统一间隙、接触门控、随穿透消失的阻尼及其非Lipschitz开闭限制。正文没有为新三维模型填入未经计算的δ₀或KAM证书。
