# **结合文献与pandapipes的热网模型**
- 主要内容：整理调研文献与pandapipes中的热网数学模型。
- 进一步优化：  
（1）压力损失方程、热力损失方程线性化；  
（2）管道传输延时的考虑（热惯性）。
- 参考文献：  
[1]W. Gu, L. Shuai, J. Wang, et al., Modeling of the heating network for multi-district integrated energy system and its operation optimization, Zhongguo Dianji Gongcheng Xuebao/Proc. Chinese Soc. Electr. Eng. 3737 (55) (2017) 160991, https://doi.org/10.13334/j.0258-8013.pcsee.  
[2]Gu W, Wu C, Wang J, et al. Optimal operation for integrated energy system considering thermal inertia of district heating network and buildings. Appl Energy2017;199:234–46.

## **0. 目录**

**1. 节点**
+ [流量平衡](#流量平衡)
+ [节点热能平衡](#节点热能平衡)
+ [节点压力平衡](#节点压力平衡)

**2. 压力**
+ [压力损失方程](#压力损失方程)
+ [管道阻力系数](#管道阻力系数)

**3. 热功率**
+ [热功率与流量温度关系](#热功率与流量温度关系)
+ [热损方程](#热损方程)

**4. 边界约束**
+ [温度约束](#温度约束)
+ [流速约束](#流速约束)
+ [压力约束](#压力约束)

### 1. 节点
#### 流量平衡
$$
\sum _ {k\in {S_ i^e}}{q_ {k,t}}=\sum _ {k\in {S_ i^s}}{q_ {k,t}},i\in S_ n,\forall t
$$

其中$S_ i^e$,$S_ i^s$分别为与$i$节点相连，流入、流出$i$节点的管道集合，$q_ {k,t}$为$t$时刻$k$序号对应流量，$S_ n$为所有节点的集合。

#### 节点热能平衡：

假设对于同一节点流出的热媒温度相同，则：

$$
T_ {k,t}^{in}=T_ {i,t}^{in},\forall k\in S_ i^s
$$

$$
\sum _ {k\in {S_ i^e}}{q_ {k,t}T_ {k,t}^{out}}=\sum _ {k\in {S_ i^s}}{q_ {k,t}T_ {k,t}^{in}},i\in S_ n,\forall t
$$

其中$T_ {k,t}^{out}$为$t$时刻$k$管道的出口温度，$T_ {k,t}^{in}$为$t$时刻$k$管道的进口温度，$T_ {i,t}^{in}$为与节点$i$相连管道的进口温度。

#### 节点压力平衡
考虑理想条件，即流入流出节点的热媒压力平衡，对于$i$节点：

$$
p_ {k1,t}^{out}=p_ {k2,t}^{in}=p_ {i,t},\forall k1\in S_ i^e,k2\in S_ i^s
$$

其中，$p_ {k,t}^{in},p_ {k,t}^{out}$分别为$t$时刻$k$管道流入、流出节点处压力，$p_ {i,t}$为$i$节点$t$时刻热媒压力。

### 2. 压力
#### 压力损失方程

$$
\triangle p_ {k,t}=p_ {k,t}^{in}-p_ {k,t}^{out}=\rho g(h_ {k}^{in}-h_ {k}^{out})-\frac {\rho \lambda l_ {k}{{v^2_ {k,t}}}}{2d}-\zeta \frac {\rho v^2_ {k,t}}{2},k\in S_ p
$$

其中，$\triangle p_ {k,t}$为$t$时刻管段$k$的压力损失，$p_ {k,t}^{in},p_ {k,t}^{out}$为管道$k$进口、出口热媒压力，$\rho ,g,d,l$分别为热媒密度、重力常数、管道直径、管道长度，$h_ {k}^{in},h_ {k}^{out}$分别为$k$管道进口、出口节点高度，$\lambda ,\zeta $分别为管道沿程阻力系数、局部阻力系数，$v_ {k,t}$为$t$时刻管道$k$的平均流速。$S_ p$为所有管道的集合。

#### 管道阻力系数
关于管道沿程阻力系数$\lambda $，Nikuradse阻力系数公式如下：

$$
\lambda =\frac {64}{Re}+\frac {1}{(-2log(\frac {k}{3.71d}))^2}
$$

其中，$k$为管道粗糙度。$Re$为流体雷诺数，其与流体密度、流速、管道直径、动力粘性系数有关：

$$
Re=\frac {\rho{v}{d}}{\eta }
$$

### 3. 热功率
#### 热功率与流量温度关系

$$
Q_ {k,t}^{in}=C_ q q_ {k,t}T_ {k,t}^{in},k\in S_ p \\
Q_ {k,t}^{out}=C_ q q_ {k,t}T_ {k,t}^{out},k\in S_ p
$$

其中，$Q_ {k,t}^{in},Q_ {k,t}^{out}$分别为管道$k$的进口、出口热功率，$C_ q$为热量比例系数且$C_ q=c\rho $，$c,\rho $分别为热媒比热容和密度。

#### 热损方程
热损方程考虑由于管道介质与周围温度之间的温差而造成的热损失，同时假设系统外界环境温度与管道导热系数为常量：

$$
Q^{loss}_ {k,t}=\int _ 0^{l_ k}\alpha \pi d(T(x)-T_ {ext})dx=Q_ {k,t}^{in}-Q_ {k,t}^{out},k\in S_ p
$$

其中，$Q^{loss}_ {k,t}$为$t$时刻$k$管道热损，$\alpha ,l,d$分别为导热系数、管道长度、管道直径，$T_ {ext}$为管道外温度。
求解可得：

$$
T_ {k,t}^{out}=T_ {k,t}^{in}e^{-\frac {\alpha \pi d}{C_ q{q_ {k,t}}}l_ k}+(1-e^{-\frac {\alpha \pi d}{C_ q{q_ {k,t}}}l_ k})T_ {ext},k\in S_ p
$$

### 4. 边界约束
#### 温度约束

$$
T_ {k}^{min} \le T_ {k,t}^{in} \le T_ {k}^{max},k\in S_ i^s,\forall i\in S_ n \\
T_ {k}^{min} \le T_ {k,t}^{out} \le T_ {k}^{max},k\in S_ i^e,\forall i\in S_ n
$$

其中，$T_ {k}^{min},T_ {k,t}^{in}$分别为$k$管道温度的最小与最大值。

#### 流速约束

$$
v_ {k}^{min}\le v_ {k,t}\le v_ {k}^{max},k\in S_ p
$$

其中，$v_ {k}^{min},v_ {k}^{max}$分别为$k$管道的最小、最大流速。

#### 压力约束

$$
p_ {k}^{min}\le p_ {k,t}^{in},p_ {l,t}^{out}\le p_ {k}^{max},k\in S_ p
$$

其中，$p_ {k}^{min},p_ {k}^{max}$分别为$k$管道的最小、最大压力。


