'''
Author: gwyxjtu
Date: 2022-06-01 15:18:53
LastEditors: gwyxjtu 867718012@qq.com
LastEditTime: 2022-06-13 11:10:12
FilePath: /optimization/Input/generate_input_data.py
Description: 人一生会遇到约2920万人,两个人相爱的概率是0.000049,所以你不爱我,我不怪你.

Copyright (c) 2022 by gwyxjtu 867718012@qq.com, All Rights Reserved. 
'''
'''
                       .::::.
                     .::::::::.
                    :::::::::::
                 ..:::::::::::'
              '::::::::::::'
                .::::::::::
           '::::::::::::::..
                ..::::::::::::.
              ``::::::::::::::::
               ::::``:::::::::'        .:::.
              ::::'   ':::::'       .::::::::.
            .::::'      ::::     .:::::::'::::.
           .:::'       :::::  .:::::::::' ':::::.
          .::'        :::::.:::::::::'      ':::::.
         .::'         ::::::::::::::'         ``::::.
     ...:::           ::::::::::::'              ``::.
    ````':.          ':::::::::'                  ::::..
                       '.:::::'                    ':'````..
'''



import pandas as pd
import numpy as np
import pprint

dict_demo_24h = {# 未来二十四小时负荷,每天维护
    'ele_load':[30]*6+ [80, 150, 290, 250, 200, 80, 60, 150, 180, 220, 360, 480, 550, 420, 320, 280, 180, 110],
    'g_load':[50]*6 + [80, 150, 290, 250, 200, 80, 60, 150, 180, 220, 360, 480, 550, 420, 320, 280, 180, 110],
    'q_load':[0]*24,# + [80, 150, 290, 250, 200, 80, 60, 150, 180, 220, 360, 480, 550, 420, 320, 280, 180, 110],
    'solar':[0,0,0,0,0,0,0.01,0.13,0.3,0.4,0.58,0.66,0.67,0.6,0.51,0.36,0.21,0.05,0,0,0,0,0,0],
    'day':13,
}
t = 5
dict_demo_4h = {# 未来4小时负荷，每小时维护
    'ele_load':dict_demo_24h['ele_load'][t:t+4],
    'g_load':dict_demo_24h['g_load'][t:t+4],
    'q_load':dict_demo_24h['q_load'][t:t+4],
    'solar':dict_demo_24h['solar'][t:t+4],
    'time':t,
}
short_dict_now = {# 储能状态，每小时维护
    'hydrogen_bottle_max':1000,
    'hst_kg':100,
    't_ht':50,#蓄能水箱
    't_ct':10,#消防水池
    'time':t,#当前时间
    'end_slack':False,
}
tmp_24h = pd.DataFrame(dict_demo_24h)
tmp_24h.to_excel('Input/input_24h.xls')
tmp_4h = pd.DataFrame(dict_demo_4h)
tmp_4h.to_excel('Input/input_4h.xls')
tmp_now = pd.DataFrame(short_dict_now,index=[0])
tmp_now.to_excel('Input/input_now.xls')
# to list
#ans = pd.read_excel('input_day.xls')
#print(list(ans['g_load'])) 
