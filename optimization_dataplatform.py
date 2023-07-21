'''
Author: guo_MacBookPro
Date: 2022-12-13 00:05:47
LastEditors: guo_MacBookPro 867718012@qq.com
LastEditTime: 2022-12-28 19:56:33
FilePath: /optimization/data_optimize/优化控制/optimization_dataplatform.py
Description: 人一生会遇到约2920万人,两个人相爱的概率是0.000049,所以你不爱我,我不怪你.

Copyright (c) 2022 by guo_MacBookPro 867718012@qq.com, All Rights Reserved. 
'''

import json
import pprint
import pandas as pd
from cpeslog.log_code import _logging
from Model.optimization_day import OptimizationDay,to_csv


if __name__ == '__main__':
    _logging.info('start')
    try:
        with open("data_optimize/优化控制/Config/config.json", "r") as f:
            input_json = json.load(f)
    except BaseException as E:
        _logging.error('读取config失败,错误原因为{}'.format(E))
        raise Exception
    # 读取输入excel
    try:
        load_station = pd.read_excel('data_platform/predict_24h_data_energystation.xls')
        load_17 = pd.read_excel('data_platform/predict_24h_data_17.xls')
        load_18 = pd.read_excel('data_platform/predict_24h_data_18.xls')
        solar = pd.read_excel('data_platform/hour_predict_data_pv.xls')
    except BaseException as E:
        _logging.error('读取input_24h的excel失败,错误原因为{}'.format(E))
        raise Exception
    try:
        input_now = pd.read_excel('data_platform/hour_dict_data_device.xls')
    except BaseException as E:
        _logging.error('读取input_now的excel失败,错误原因为{}'.format(E))
        raise Exception
    load_json = {
        "ele_load":[load_station['energystation_p_stable_load_pre'][i]+load_17['17_p_stable_load_pre'][i]+load_18['18_p_stable_load_pre'][i] for i in range(24)],
        "g_load":[load_station['energystation_g_load_pre'][i]+load_17['17_g_load_pre'][i]+load_18['18_g_load_pre'][i] for i in range(24)],
        "q_load":[load_station['energystation_q_load_pre'][i]+load_17['17_q_load_pre'][i]+load_18['18_q_load_pre'][i] for i in range(24)],
        "solar":[solar['p_pv'][i]/1000 for i in range(24)],
        "day":10
    }


    sto_json = {
        "hydrogen_bottle_max": 480,
        "hst_kg": input_now.iloc[-1]['h_hst'],
        "t_ht": input_now.iloc[-1]['t_ht'],
        "t_ct": input_now.iloc[-1]['t_ct'],
        "time": 0,
        "end_slack":False,
    }
    sto_end_json = {
        "hydrogen_bottle_max": 480,
        "hst_kg": input_now.iloc[-1]['h_hst'],
        "t_ht": input_now.iloc[-1]['t_ht'],
        "t_ct": input_now.iloc[-1]['t_ct'],
        "time": 24,
        "end_slack":False,
    }
    sto = pd.DataFrame(sto_json,index=[0])
    sto_end = pd.DataFrame(sto_end_json, index=[24])

    sto_end = sto.copy()
    sto_end['time']=24
    sto_end.index = [24]
    # 优化主函数
    try:
        dict_control,dict_plot = OptimizationDay(parameter_json=input_json, load_json=load_json, begin_time = 0, time_scale=24, storage_begin_json=sto, storage_end_json=sto_end)
    except BaseException as E:
        _logging.error('优化主函数执行失败，错误原因为{}'.format(E))
        raise Exception
    #print(dict_control)
    #print(dict_plot)
    
    # 写入输出Excel
    try:
        # to_csv(dict_control,"dict_opt_control_24h")
        # to_csv(dict_plot,"dict_opt_plot_24h")
        pd.DataFrame(dict_control).to_excel('data_platform/dict_opt_control_24h.xls')
        pd.DataFrame(dict_plot).to_excel('data_platform/dict_opt_plot_24h.xls')
    except BaseException as E:
        _logging.error('excel输出失败,错误原因为{}'.format(E))
        raise Exception