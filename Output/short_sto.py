'''
Author: guo_win 867718012@qq.com
Date: 2023-10-15 15:20:20
LastEditors: guo_MateBookPro 867718012@qq.com
LastEditTime: 2024-01-11 16:59:26
FilePath: /Code_scichina/data_result/script/short_sto.py
Description: 人一生会遇到约2920万人,两个人相爱的概率是0.000049,所以你不爱我,我不怪你.
Copyright (c) 2023 by ${git_name} email: ${git_email}, All Rights Reserved.
'''
from matplotlib.pyplot import summer
import pandas as pd

xls = pd.read_excel('mat/res_2023-10-15 21-36-41_PV.xls')
# print(xls)
day = [31,28,31,30,31,30,31,31,30,31,30,31]
month = [sum(day[:i]) for i in range(13)]
spring_date = (month[3]+16)*24
summer_date = (month[6]+16)*24
autumn_date = (month[9]+16)*24
winter_date = 15*24

print(spring_date,summer_date,autumn_date,winter_date)
# 短期储能绘图，电能和冷热水箱，三个季节
spring_m = xls['m'][spring_date+1:spring_date+25].reset_index(drop=True)
spring_g = xls['g'][spring_date+1:spring_date+25].reset_index(drop=True)
spring_q = xls['q'][spring_date+1:spring_date+25].reset_index(drop=True)

summer_m = xls['m'][summer_date+1:summer_date+25].reset_index(drop=True)
summer_g = xls['g'][summer_date+1:summer_date+25].reset_index(drop=True)
summer_q = xls['q'][summer_date+1:summer_date+25].reset_index(drop=True)

autumn_m = xls['m'][autumn_date+1:autumn_date+25].reset_index(drop=True)
autumn_g = xls['g'][autumn_date+1:autumn_date+25].reset_index(drop=True)
autumn_q = xls['q'][autumn_date+1:autumn_date+25].reset_index(drop=True)

winter_m = xls['m'][winter_date+1:winter_date+25].reset_index(drop=True)
winter_g = xls['g'][winter_date+1:winter_date+25].reset_index(drop=True)
winter_q = xls['q'][winter_date+1:winter_date+25].reset_index(drop=True)

short_sto = pd.DataFrame({'spring_b':spring_m,'spring_g':spring_g,'spring_q':spring_q,
                            'summer_b':summer_m,'summer_g':summer_g,'summer_q':summer_q,
                            'autumn_b':autumn_m,'autumn_g':autumn_g,'autumn_q':autumn_q,
                            'winter_b':winter_m,'winter_g':winter_g,'winter_q':winter_q})
short_sto.to_csv('data_result/short_sto.csv')
