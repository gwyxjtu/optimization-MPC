# **约束方程**
- 主要内容：罗列综合能源系统模型的所有约束方程。

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

**2. 端点状态约束**
+ [储热罐末端状态](#储热罐末端状态)
+ [储冷罐末端状态](#储冷罐末端状态)
+ [储氢罐末端状态](#储氢罐末端状态)
+ [初始储能状态](#初始储能状态)

**3. 能量平衡约束**
+ [电力供需平衡约束](#电力供需平衡约束)
+ [热供需平衡约束](#热供需平衡约束)
+ [冷供需平衡约束](#冷供需平衡约束)

**4. 其他约束**
+ [购氢约束](#购氢约束)
+ [电力传输约束](#电力传输约束)

### 1. 设备约束
#### 燃料电池

$$
p^{fc}_t=\eta_p^{fc}*h^{fc}_t,\forall t,  \\
g^{fc}_t=\theta^{ex}*\eta_g^{fc}*h^{fc}_t,\forall t, \\ p^{fc}_t \leq P^{fc} ,\forall t
$$

其中$p^{fc}_t，g^{fc}_t，h^{fc}_t$分别是燃料电池$t$时刻发电量，产热量，耗氢量,$P^{fc}$为设备某一时刻的最大发电量。

#### 电解槽

$$
h^{el}_t=\beta^{el}*p^{fc}_t,\forall t,  \\
p^{el}_t \leq P^{el} ,\forall t
$$

其中$p^{el}_t，h^{el}_t$分别是电解槽$t$时刻用电量，产氢量。

#### 储氢罐

$$
h^{sto}_{t} - h^{sto}_{t-1}=h^{el}_t+h^{pur}_t-h^{fc}_t,\forall t,  \\
$$

其中$h^{sto}_{t},h^{pur}_{t}$分别是储氢罐$t$时刻用电量，购氢量。

#### 电锅炉

$$
g^{eb}_{t}=\beta^{eb}*p^{eb}_t,\forall t,  \\
p^{eb}_t \leq P^{eb} ,\forall t
$$

其中$p^{eb}_t，g^{el}_t$分别是电锅炉$t$时刻用电量，产热量。

#### 地源热泵（未用）

$$
g^{ghp}_{t}=\beta^{ghpg}*p^{ghp,g}_{t},\forall t,  \\
q^{ghp}_{t}=\beta^{ghpq}*p^{ghp,q}_{t},\forall t,  \\
p^{ghp}_{t}=p^{ghp,g}_{t}+p^{ghp,q}_{t},\forall t,  \\
p^{ghp}_t \leq P^{ghp} ,\forall t
$$

其中$g^{ghp}_{t}，q^{ghp}_{t}，p^{ghp}_{t}$分别是地源热泵$t$时刻产热量，制冷量，用电量。$p^{ghp,g}_{t},p^{ghp,q}_{t}$分别是地源热泵用于制热和制冷的耗电量。

#### 空气源热泵（未用）

$$
g^{hp}_{t}=\beta^{hpg}*p^{hp,g}_{t},\forall t,  \\
q^{hp}_{t}=\beta^{hpq}*p^{hp,q}_{t},\forall t,  \\
p^{hp}_{t}=p^{hp,g}_{t}+p^{hp,q}_{t},\forall t,  \\
p^{hp}_t \leq P^{hp} ,\forall t
$$

其中$g^{hp}_{t}，q^{hp}_{t}，p^{hp}_{t}$分别是空气源热泵$t$时刻产热量，制冷量，用电量。$p^{hp,g}_{t},p^{hp,q}_{t}$分别是空气源热泵用于制热和制冷的耗电量。

#### 储热罐

$$
g^{ht}_t = c*m^{ht}*(t^{ht}_{t+1}-t^{ht}_{t}),\forall t,  \\
t^{ht,min}  \leq t^{ht}_t \leq t^{ht,max} ,\forall t
$$

其中$t^{ht}_t，g^{ht}_t$分别是储热罐$t$时刻水温，换热量。

#### 储冷罐

$$
q^{ht}_t = c*m^{ct}*(t^{ct}_{t+1}-t^{ct}_{t}),\forall t,  \\
t^{ct,min}  \leq t^{ct}_t \leq t^{ct,max} ,\forall t
$$

其中$t^{ct}_t，q^{ct}_t$分别是储冷罐$t$时刻水温，换热量。

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

其中，$h^{sto}_{start}$, $h^{sto}_{final}$, $sl_{hsto}$ 分别为起始状态和末端状态储氢罐储存量，以及末端松弛尺度。

#### 初始储能状态：

$$
t^{ht}_0 = t^{ht}_{start} \\
t^{ct}_0 = t^{ct}_{start} \\
h^{sto}_0 = h^{sto}_{start}
$$

其中，$t^{ht}_0$，$t^{ct}_0$，$h^{sto}_0$ 分别为储热、储冷、储氢罐的初始状态温度与储存量。

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

