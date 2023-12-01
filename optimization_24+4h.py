'''
Author: gwyxjtu
Date: 2023-11-28 13:40:00
LastEditors: wjxjtu 2309914740@qq.com
LastEditTime: 2023-11-29 16:00:00
FilePath: /optimization/optimization_24+4h.py
Description: 人一生会遇到约2920万人,两个人相爱的概率是0.000049,所以你不爱我,我不怪你.

Copyright (c) 2022 by gwyxjtu 867718012@qq.com, All Rights Reserved.
'''
'''
                       _oo0oo_
                      o8888888o
                      88" . "88
                      (| -_- |)
                      0\  =  /0
                    ___/`---'\___
                  .' \\|     |// '.
                 / \\|||  :  |||// \
                / _||||| -:- |||||- \
               |   | \\\  - /// |   |
               | \_|  ''\---/''  |_/ |
               \  .-\__  '-'  ___/-. /
             ___'. .'  /--.--\  `. .'___
          ."" '<  `.___\_<|>_/___.' >' "".
         | | :  `- \`.;`\ _ /`;.`/ - ` : | |
         \  \ `_.   \_ __\ /__ _/   .-` /  /
     =====`-.____`.___ \_____/___.-`___.-'=====
                       `=---='


     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

           佛祖保佑     永不宕机     永无BUG
'''


import json
import pprint
import pandas as pd
from cpeslog.log_code import _logging
from Model.optimization_day import OptimizationDay, to_csv

if __name__ == '__main__':
    _logging.info('start')
    # 读取设备参数
    try:
        with open("Config/config.json", "rb") as f:
            input_json = json.load(f)
    except BaseException as E:
        _logging.error('读取config失败,错误原因为{}'.format(E))
        raise Exception
    # 读取初始时刻状态
    try:
        sto_0h = pd.read_excel('Input/input_now.xls')
    except BaseException as E:
        _logging.error('读取input_now的excel失败,错误原因为{}'.format(E))
        raise Exception
    # 读取输入实时负荷数据(应为4h的短期预测数据，此处以24h的日前预测数据代替)
    try:
        load = pd.read_excel('Input/input_24h.xls')
    except BaseException as E:
        _logging.error('读取input_24h的excel失败,错误原因为{}'.format(E))
        raise Exception
    # 读取日前设备决策结果
    try:
        day_ahead_plan = pd.read_excel('Output/dict_opt_plot_24h.xls')
    except BaseException as E:
        _logging.error('读取dict_plot_24h的excel失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化决策序列
    opex_without_opt = {}
    p_fc = {}
    p_hp = {}
    p_eb = {}
    p_el = {}
    h_hst = {}
    t_ht = {}
    t_ct = {}
    h_tube = {}
    # 考虑20h的MPC控制
    period = 20

    for i in range(period):
        if i == 0:
            sto = sto_0h.copy()
        else:
            # sto['hst_kg'] = dict_combine_plot['h_hst'][i-1]
            # sto['t_ht'] = dict_combine_plot['t_ht'][i-1]
            # sto['t_ct'] = dict_combine_plot['t_ct'][i-1]
            # sto['time'] = i
            # sto['hydrogen_bottle_max'] = dict_combine_plot['h_tube'][i-1]
            # sto.index = [0]

            # 以上一时刻MPC first hour控制结果作为此时初始状态
            sto['hst_kg'] = h_hst[i - 1]
            sto['t_ht'] = t_ht[i - 1]
            sto['t_ct'] = t_ct[i - 1]
            sto['time'] = i
            sto['hydrogen_bottle_max'] = h_tube[i-1]
            sto.index = [0]

        # 读取输入中的储氢罐、热水罐温度
        sto_4 = day_ahead_plan.loc[i + 3, ['h_hst', 't_ht', 't_ct']].to_frame().T
        sto_4 = sto_4.rename(columns={'h_hst': 'hst_kg'})
        # 确定终止时刻设备容量(此处不考虑购氢与末端松弛)
        sto_4['hydrogen_bottle_max'] = 1000
        sto_4['time'] = i+4
        sto_4['end_slack'] = False
        sto_4.index = [4]
        # print(sto)
        # print(sto_4)

        load_4h = load[i:i+4]

        try:
            dict_control, dict_plot = OptimizationDay(parameter_json=input_json, load_json=load_4h,
                                                      begin_time=0, time_scale=4,
                                                      storage_begin_json=sto, storage_end_json=sto_4)
        except BaseException as E:
            _logging.error('优化住函数执行失败，错误原因为{}'.format(E))
            raise Exception

        # dict_plot = pd.DataFrame(dict_plot)
        # if i == 0:
        #     dict_combine_plot = dict_plot.loc[0].to_frame().T
        # else:
        #     dict_combine_plot.loc[i] = dict_plot.loc[0]
        #     dict_combine_plot['hour'][i] = i+1

        # 取MPC控制结果的first hour
        opex_without_opt[i] = dict_plot['opex_without_opt'][0]
        p_fc[i] = dict_plot['p_fc'][0]
        p_hp[i] = dict_plot['p_hp'][0]
        p_eb[i] = dict_plot['p_eb'][0]
        p_el[i] = dict_plot['p_el'][0]
        h_hst[i] = dict_plot['h_hst'][0]
        t_ht[i] = dict_plot['t_ht'][0]
        t_ct[i] = dict_plot['t_ct'][0]
        h_tube[i] = dict_plot['h_tube'][0]
    
    dict_combine_plot = {
        'hour': [i + 1 for i in range(period)],
        # operational day cost
        'opex_without_opt': [opex_without_opt[i] for i in range(period)],  # 未经优化的运行成本
    
        # ele
        'p_fc': [p_fc[i] for i in range(period)],  # 燃料电池
    
        'p_hp': [p_hp[i] for i in range(period)],  # 热泵
        'p_eb': [p_eb[i] for i in range(period)],  # 电锅炉
        'p_el': [p_el[i] for i in range(period)],
        # hydrogen
        'h_hst': [h_hst[i] for i in range(period)],
        # thermal
        't_ht': [t_ht[i] for i in range(period)],
        't_ct': [t_ct[i] for i in range(period)],
        'h_tube': [h_tube[i] for i in range(period)],
    }
    # 写入输出到excel
    try:
        # dict_combine_plot.to_excel('Output/dict_plot_24+4h3.xlsx',index=False)
        to_csv(dict_combine_plot, "dict_plot_24+4h")
    except BaseException as E:
        _logging.error('excel输出失败,错误原因为{}'.format(E))
        raise Exception

