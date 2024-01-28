# **模型约束方程**
- 主要内容：建立各设备简化后的数学模型，形成设备约束。整理能源系统模型的约束条件。

## **0. 约束方程目录**

**1. 设备约束**
+ [燃料电池](#燃料电池)
+ [电解槽](#电解槽)
+ [储氢罐](#储氢罐)
+ [电锅炉](#电锅炉)
+ [地源热泵](#地源热泵)
+ [空气源热泵](#空气源热泵)
+ [储热罐](#储热罐)
+ [储冷罐](#储冷罐)
+ [光伏](#光伏)

**2. 末端状态约束**
+ [储热罐末端状态](#储热罐末端状态)
+ [储冷罐末端状态](#储冷罐末端状态)
+ [储氢罐末端状态](#储氢罐末端状态)

**3. 能量平衡约束**
+ [电力供需平衡约束](#电力供需平衡约束)
+ [热供需平衡约束](#热供需平衡约束)
+ [冷供需平衡约束](#冷供需平衡约束)

**4. 其他约束**
+ [购氢约束](#购氢约束)
+ [电力传输约束](#电力传输约束)

### 1. 设备约束
#### 燃料电池
在氢氧环境下，燃料电池可同时提供电力与热力需求，本模型下燃料电池运行约束包括产电、产热以及边界约束：

$$
p^{fc}_t=\eta_p^{fc}*h^{fc}_t,\forall t  \\
g^{fc}_t=\theta^{fc}*\eta_g^{fc}*h^{fc}_t, \forall t \\ 0 \le p^{fc}_t \le P^{fc} ,\forall t
$$

其中$p^{fc}_t，g^{fc}_t，h^{fc}_t$分别是燃料电池$t$时刻发电量、产热量、耗氢量，$\eta_p^{fc}$为燃料电池产电效率系数，$\eta_g^{fc}$为燃料电池产热效率系数，$\theta^{fc}$为热回收系数,$P^{fc}$为设备任一时刻的最大发电量。

#### 电解槽
电解槽产生的氢气可以描述为：

$$
h^{el}_t=\beta^{el}*p^{el}_t,\forall t  \\
0\le p^{el}_t \le P^{el} ,\forall t
$$

其中$p^{el}_t，h^{el}_t$分别是电解槽$t$时刻用电量，产氢量，$\beta^{el}$为电解槽产氢效率系数。

#### 储氢罐
相邻两时刻的储氢罐储氢量之差与用氢产氢应保持平衡关系。同时，储氢罐的储氢量应维持在最小最大储氢量之间；储氢罐的充放也应满足充放限制：

$$
h^{sto}_{t} - h^{sto}_{t-1}=h^{el}_t+h^{pur}_t-h^{fc}_t,\forall t  \\
h^{sto}_{min}\le h^{sto}_{t}\le h^{sto}_{max},\forall t \\
-H^{trans}_{max}\le h^{sto}_{t} - h^{sto}_{t-1}\le H^{trans}_{max}
$$

其中$h^{sto}_{t},h^{pur}_{t}$分别是储氢罐$t$时刻用电量，购氢量。$h^{sto}_{min},h^{sto}_{max}$分别为最小最大储氢量。$H^{trans}_{max}$为最大充放氢限制。

#### 电锅炉
为了满足部分的热量需求，电锅炉可以通过用电来产生热量。EB产生的热功率与最大热功率限制可用下述等式来描述：

$$
g^{eb}_{t}=\beta^{eb}*p^{eb}_t,\forall t,  \\
0\le p^{eb}_t \le P^{eb} ,\forall t
$$

其中$p^{eb}_t，g^{el}_t$分别是电锅炉$t$时刻用电量、产热量，$\beta^{eb}$为电锅炉效率系数。

#### 地源热泵

$$
g^{ghp}_{t}=\beta^{ghpg}*p^{ghp,g}_{t},\forall t,  \\
q^{ghp}_{t}=\beta^{ghpq}*p^{ghp,q}_{t},\forall t,  \\
p^{ghp}_{t}=p^{ghp,g}_{t}+p^{ghp,q}_{t},\forall t,  \\
p^{ghp}_t \leq P^{ghp} ,\forall t
$$

其中$g^{ghp}_{t}，q^{ghp}_{t}，p^{ghp}_{t}$分别是地源热泵$t$时刻产热量，制冷量，用电量。$p^{ghp,g}_{t},p^{ghp,q}_{t}$分别是地源热泵用于制热和制冷的耗电量。

#### 空气源热泵
热泵是一种将低品位热能转化为高品位热能的装置。能源转换效率高，功耗低，具有冬热、夏冷双重功能。从能量的角度来看，热泵的输出模型如下：

$$
g_t^{hp}=p_t^{hp}*COP_{hp\_g}*T_{hp},\forall t \\
q_t^{hp}=p_t^{hp}*COP_{hp\_q}*(1-T_{hp}),\forall t \\
0 \le p^{hp}_t \le P^{hp} ,\forall t
$$

其中$g^{hp}_{t}，q^{hp}_{t}，p^{hp}_{t}$分别是空气源热泵$t$时刻产热量，制冷量，用电量。$COP_{hp\_g},COP_{hp\_q}$分别是空气源热泵制热和制冷的能效系数，$T_{hp}$为热泵运行状态，$P^{hp}$为热泵最大运行功率。

#### 储热罐
储热罐的运行约束包括换热量温度转换关系、储热量限制、以及换热量限制：

$$
g^{ht}_t = c*m^{ht}*(t^{ht}_{t+1}-t^{ht}_{t}),\forall t  \\
t^{ht,min}  \leq t^{ht}_t \leq t^{ht,max} ,\forall t  \\
-G_{max}^{ht}\le g^{ht}_t\le G_{max}^{ht}
$$

其中$t^{ht}_t，g^{ht}_t$分别是储热罐$t$时刻水温，换热量。$t^{ht,min},t^{ht,max}$分别为储热罐的最小最大水温。$G_{max}^{ht}$为最大换热量。

#### 储冷罐
与储热罐类似，运行约束如下：

$$
q^{ct}_t = c*m^{ct}*(t^{ct}_{t+1}-t^{ct}_{t}),\forall t  \\
t^{ct,min}  \leq t^{ct}_t \leq t^{ct,max} ,\forall t  \\
-Q_{max}^{ct}\le q^{ct}_t\le Q_{max}^{ct}
$$

其中$t^{ct}_t，q^{ct}_t$分别是储冷罐$t$时刻水温，换冷量。$t^{ct,min},t^{ct,max}$分别为储冷罐的最小最大水温。$Q_{max}^{ht}$为最大换冷量。

#### 光伏

$$
p^{pv}_{t} = P^{pv}*p^{pv,fo}_{t},\forall t,  \\
$$

其中$p^{pv}_t，p^{pv,fo}_t$分别是光伏$t$时刻光伏发电量和单位光伏发电预测量，$P^{pv}$为光伏总量。

#### 太阳能集热器（未用）

$$
g^{sc}_{t}=G^{sc}*g^{sc,fo}_t,\forall t,
$$

其中$g^{sc}_t，g^{sc,fo}_t$分别是集热器$t$时刻实际产热量和单位预测产热量。

#### 冷水机组（未用）

$$
q^{ec}_{t}=\beta^{e}*p^{ec}_t,\forall t,  \\
p^{ec}_t \leq P^{ec} ,\forall t
$$

其中$p^{ec}_t，q^{ec}_t$分别是冷水机组$t$时刻用电量，制冷量。

#### 地热井（未用）
$$
\sum g^{ghp}_{t} = \sum (p^{ghp}_{t} + p^{ghp,q}_{t}+p^{gr}_{t}),
$$
其中$p^{gr}_{t}$是$t$时段向地热井的灌热量。

#### 相变储热箱（未用）

$$
g^{xb}_{t} = s^{xb}_{t+1}-s^{xb}_{t},\forall t,  \\
g^{xb}_t  \leq G^{xb}  ,\forall t,\\
s^{xb}_t \leq S^{xb},\forall t
$$

其中$g^{xb}_t，s^{xb}_t$分别是相变储热$t$时刻换热量和储热量。

#### 风电（未用）

$$
p^{wd}_{t} = P^{wd}*p^{wd,fo}_{t},\forall t,  \\
$$

其中$p^{wd}_t，p^{wd,fo}_t$分别是风电$t$时刻风电发电量和单位风电发电预测量。

#### 电化学储能（未用）

$$
p^{bs}_{t} = s^{bs}_{t+1}-s^{bs}_{t},\forall t,  \\
p^{bs}_t  \leq P^{bs}  ,\forall t,\\
s^{bs}_t \leq S^{bs},\forall t
$$

其中$p^{bs}_t，s^{bs}_t$分别是蓄电池$t$时刻供电\用电量和储电量。

### 2. 末端状态约束
#### 储热罐末端状态：

$$
t^{ht}_{start} * (1-sl_{ht}) \le t^{ht}_{final} \le t^{ht}_{start} * (1+sl_{ht})
$$

其中，$t^{ht}_{start}$, $t^{ht}_{final}$, $sl_{ht}$ 分别为起始状态和末端状态储热罐温度，以及末端松弛尺度。

#### 储冷罐末端状态：

$$
t^{ct}_{start} * (1-sl_{ct}) \le t^{ct}_{final} \le t^{ct}_{start} * (1+sl_{ct})
$$

其中，$t^{ct}_{start}$, $t^{ct}_{final}$, $sl_{ct}$ 分别为起始状态和末端状态储冷罐温度，以及末端松弛尺度。

#### 储氢罐末端状态：

$$
h^{sto}_{start} * (1-sl_{hsto}) \le h^{sto}_{final} \le h^{sto}_{start} * (1+sl_{hsto})
$$

其中，$h^{sto}_{start}$, $h^{sto}_{final}$, $sl_{hsto}$ 分别为起始状态和末端状态储氢罐温度，以及末端松弛尺度。

### 3. 能量平衡约束
#### 电力供需平衡约束：

$$
p^{fc}_t + p^{pur}_t + p^{pv}_t = p^{el}_t + p^{eb}_t + p^{hp}_t + p^{load}_t,\forall t
$$

其中，$p^{load}_t$ 为 $t$ 时刻负载端用电需求。

#### 热供需平衡约束：

$$
g^{ht}_t + g^{load}_t = g^{fc}_t + g^{hp}_t + g^{eb}_t,\forall t
$$

其中，$g^{load}_t$ 为 $t$ 时刻负载端热需求。

#### 冷供需平衡约束：

$$
q^{ct}_t + q^{hp}_t = q^{load}_t,\forall t
$$

其中，$q^{load}_t$ 为 $t$ 时刻负载端冷需求。

### 4. 其他约束
#### 购氢约束：
当 ${hydrogen\_max\_final} - {hydrogen\_max\_start} \ge 0$ 时：

$$
\sum\limits_{t=t_{s}^{st}}\limits^{T_s} h^{pur}_t  \leq hydrogen\_max\_final - hydrogen\_max\_start
$$

否则：

$$
\sum\limits_{t=t_{s}^{st}}\limits^{T_s} h^{pur}_t  = 0
$$

其中，${hydrogen\_max\_final}$,${hydrogen\_max\_start}$ 分别为末端状态和起始状态的氢气瓶容量,$t_{s}^{st}$, $T_s$ 分别为起始时刻和滚动周期。

#### 电力传输约束（可能）：

$$
0 \le p^{pur}_t \le f_l ,\forall t
$$

其中，$f_l$ 为电网运输线路限制。

