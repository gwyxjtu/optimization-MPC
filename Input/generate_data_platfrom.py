'''
Author: guo_MacBookPro
Date: 2022-12-03 20:54:40
LastEditors: guo_MacBookPro 867718012@qq.com
LastEditTime: 2022-12-03 21:41:26
FilePath: /optimization/Input/generate_data_platfrom.py
Description: 人一生会遇到约2920万人,两个人相爱的概率是0.000049,所以你不爱我,我不怪你.

Copyright (c) 2022 by guo_MacBookPro 867718012@qq.com, All Rights Reserved. 
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
import datetime



hour_dict_data = {
'date_time':[datetime.datetime.now() + datetime.timedelta(hours=i) for i in range(24)],
# 各个区域的冷热电负荷
'F2_p_total_load':[0 for _ in range(24)],
'F2_p_stable_load':[0 for _ in range(24)],
'F2_q_load':[0 for _ in range(24)],
'F2_g_load':[0 for _ in range(24)],
'F1_p_total_load':[0 for _ in range(24)],
'F1_p_stable_load':[0 for _ in range(24)],
'F1_q_load':[0 for _ in range(24)],
'F1_g_load':[0 for _ in range(24)],
'B1_p_total_load':[0 for _ in range(24)],
'B1_p_stable_load':[0 for _ in range(24)],
'B1_q_load':[0 for _ in range(24)],
'B1_g_load':[0 for _ in range(24)],
'17_p_total_load':[0 for _ in range(24)],
'17_p_stable_load':[0 for _ in range(24)],
'17_q_load':[0 for _ in range(24)],
'17_g_load':[0 for _ in range(24)],
'18_p_total_load':[0 for _ in range(24)],
'18_p_stable_load':[0 for _ in range(24)],
'18_q_load':[0 for _ in range(24)],
'18_g_load':[0 for _ in range(24)],

# 电相关
'p_sold':[0 for _ in range(24)],
'p_pur':[0 for _ in range(24)],
'p_pv':[0 for _ in range(24)],
'p_fc':[0 for _ in range(24)],
'p_hp':[0 for _ in range(24)],
'p_eb':[0 for _ in range(24)],
'p_pump':[0 for _ in range(24)],
'p_el':[0 for _ in range(24)],
'p_stable_load':[0 for _ in range(24)],
'p_total_load':[0 for _ in range(24)],

# 氢相关
'h_hst':[0 for _ in range(24)],
'h_el':[0 for _ in range(24)],
'h_pur':[0 for _ in range(24)],
'h_fc':[0 for _ in range(24)],

# 热相关
't_ht':[0 for _ in range(24)],
'water_load':[0 for _ in range(24)],
'g_load':[0 for _ in range(24)],
'g_hp':[0 for _ in range(24)],
'g_eb':[0 for _ in range(24)],
'g_fc':[0 for _ in range(24)],
'g_ht':[0 for _ in range(24)],

# 冷相关
't_ct':[0 for _ in range(24)],
'q_ct':[0 for _ in range(24)],
'q_hp':[0 for _ in range(24)],
'q_load':[0 for _ in range(24)],
}

day_dict_data = {
'date_time':[datetime.datetime.now() + datetime.timedelta(days=i) for i in range(30)],

'F2_p_total_load':[0 for _ in range(30)],
'F2_p_stable_load':[0 for _ in range(30)],
'F2_q_load':[0 for _ in range(30)],
'F2_g_load':[0 for _ in range(30)],
'F1_p_total_load':[0 for _ in range(30)],
'F1_p_stable_load':[0 for _ in range(30)],
'F1_q_load':[0 for _ in range(30)],
'F1_g_load':[0 for _ in range(30)],
'B1_p_total_load':[0 for _ in range(30)],
'B1_p_stable_load':[0 for _ in range(30)],
'B1_q_load':[0 for _ in range(30)],
'B1_g_load':[0 for _ in range(30)],
'17_p_total_load':[0 for _ in range(30)],
'17_p_stable_load':[0 for _ in range(30)],
'17_q_load':[0 for _ in range(30)],
'17_g_load':[0 for _ in range(30)],
'18_p_total_load':[0 for _ in range(30)],
'18_p_stable_load':[0 for _ in range(30)],
'18_q_load':[0 for _ in range(30)],
'18_g_load':[0 for _ in range(30)],


# 电相关
'p_sold':[0 for _ in range(30)],
'p_pur':[0 for _ in range(30)],
'p_pv':[0 for _ in range(30)],
'p_fc':[0 for _ in range(30)],
'p_hp':[0 for _ in range(30)],
'p_eb':[0 for _ in range(30)],
'p_pump':[0 for _ in range(30)],
'p_el':[0 for _ in range(30)],
'p_stable_load':[0 for _ in range(30)],
'p_total_load':[0 for _ in range(30)],

# 氢相关
'h_hst':[0 for _ in range(30)],
'h_el':[0 for _ in range(30)],
'h_pur':[0 for _ in range(30)],
'h_fc':[0 for _ in range(30)],

# 热相关
't_ht':[0 for _ in range(30)],
'water_load':[0 for _ in range(30)],
'g_load':[0 for _ in range(30)],
'g_hp':[0 for _ in range(30)],
'g_eb':[0 for _ in range(30)],
'g_fc':[0 for _ in range(30)],
'g_ht':[0 for _ in range(30)],

# 冷相关
't_ct':[0 for _ in range(30)],
'q_ct':[0 for _ in range(30)],
'q_hp':[0 for _ in range(30)],
'q_load':[0 for _ in range(30)],
}


month_dict_data = {
'date_time':[i+1 for i in range(12)],

'F2_p_total_load':[0 for _ in range(12)],
'F2_p_stable_load':[0 for _ in range(12)],
'F2_q_load':[0 for _ in range(12)],
'F2_g_load':[0 for _ in range(12)],
'F1_p_total_load':[0 for _ in range(12)],
'F1_p_stable_load':[0 for _ in range(12)],
'F1_q_load':[0 for _ in range(12)],
'F1_g_load':[0 for _ in range(12)],
'B1_p_total_load':[0 for _ in range(12)],
'B1_p_stable_load':[0 for _ in range(12)],
'B1_q_load':[0 for _ in range(12)],
'B1_g_load':[0 for _ in range(12)],
'17_p_total_load':[0 for _ in range(12)],
'17_p_stable_load':[0 for _ in range(12)],
'17_q_load':[0 for _ in range(12)],
'17_g_load':[0 for _ in range(12)],
'18_p_total_load':[0 for _ in range(12)],
'18_p_stable_load':[0 for _ in range(12)],
'18_q_load':[0 for _ in range(12)],
'18_g_load':[0 for _ in range(12)],


# 电相关
'p_sold':[0 for _ in range(12)],
'p_pur':[0 for _ in range(12)],
'p_pv':[0 for _ in range(12)],
'p_fc':[0 for _ in range(12)],
'p_hp':[0 for _ in range(12)],
'p_eb':[0 for _ in range(12)],
'p_pump':[0 for _ in range(12)],
'p_el':[0 for _ in range(12)],
'p_stable_load':[0 for _ in range(12)],
'p_total_load':[0 for _ in range(12)],

# 氢相关
'h_hst':[0 for _ in range(12)],
'h_el':[0 for _ in range(12)],
'h_pur':[0 for _ in range(12)],
'h_fc':[0 for _ in range(12)],

# 热相关
't_ht':[0 for _ in range(12)],
'water_load':[0 for _ in range(12)],
'g_load':[0 for _ in range(12)],
'g_hp':[0 for _ in range(12)],
'g_eb':[0 for _ in range(12)],
'g_fc':[0 for _ in range(12)],
'g_ht':[0 for _ in range(12)],

# 冷相关
't_ct':[0 for _ in range(12)],
'q_ct':[0 for _ in range(12)],
'q_hp':[0 for _ in range(12)],
'q_load':[0 for _ in range(12)],
}



tmp_24h = pd.DataFrame(hour_dict_data)
tmp_24h.to_excel('Input/hour_dict_data.xls')
tmp_4h = pd.DataFrame(day_dict_data)
tmp_4h.to_excel('Input/day_dict_data.xls')
tmp_now = pd.DataFrame(month_dict_data)
tmp_now.to_excel('Input/month_dict_data.xls')
# to list
#ans = pd.read_excel('input_day.xls')
#print(list(ans['g_load'])) 
