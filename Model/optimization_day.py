'''
Author: gwyxjtu
Date: 2022-05-31 21:46:00
LastEditors: yxs 572412425@qq.com
LastEditTime: 2023-12-16 22:44:02
FilePath: \设备能效计算\mx\optimization-MPC\Model\optimization_day.py
Description: 人一生会遇到约2920万人,两个人相爱的概率是0.000049,所以你不爱我,我不怪你.

Copyright (c) 2022 by gwyxjtu 867718012@qq.com, All Rights Reserved. 
'''
#!/usr/bin/env python3.7

import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import numpy as np
from pandas import period_range
import xlwt
import random

from cpeslog.log_code import _logging


import scipy.sparse as ss

BASIC = 0
SUPER_BASIC = -3
CBASIC = 0

def extract_basis(model) -> ss.csr_matrix:
    """Extract the basis matrix in sparse representation."""
    #  model.optimize()

    # Mapping constraint names to indices
    constr_names_to_indices = {
        c.ConstrName: i for i, c in enumerate(model.getConstrs())
    }
    m = model.NumConstrs
    col_index = 0
    # Initialize the lists to store the row and column indices of non-zero 
    # elements in the basis matrix
    row_indices, col_indices, values= [], [], []
    for v in model.getVars():
       col = model.getCol(v)
       
       # Find basic variables
       if v.VBasis == BASIC:
           for j in range(col.size()):
               coeff, name = col.getCoeff(j), col.getConstr(j).ConstrName
               row_index = constr_names_to_indices[name]
               row_indices.append(row_index)
               col_indices.append(col_index)
               values.append(coeff)
           col_index +=1

       elif v.VBasis == SUPER_BASIC:
           raise ValueError(f"Variable {v.varName} is superbasic!")
        
    # Find constraints with slack variable in the basis
    for c in model.getConstrs():
        name = c.ConstrName
        row_index = constr_names_to_indices[name]
        
        if c.CBasis == CBASIC:
            row_indices.append(row_index)
            col_indices.append(col_index)
            values.append(1)
            col_index +=1

    return ss.csr_matrix((values, (row_indices, col_indices)), shape=(m, m))




def crf(year):
    i = 0.08
    crf=((1+i)**year)*i/((1+i)**year-1);
    return crf

def to_csv(res,filename):
    """生成excel输出文件

    Args:
        res (_type_): 结果json，可以包括list和具体值
        filename (_type_): 文件名，不用加后缀
    """
    items = list(res.keys())
    wb = xlwt.Workbook()
    total = wb.add_sheet('test')
    for i in range(len(items)):
        total.write(0,i,items[i])
        if type(res[items[i]]) == list:
            sum = 0
            #print(items[i])
            for j in range(len(res[items[i]])):
                total.write(j+1,i,float((res[items[i]])[j]))
        else:
            #print(items[i])
            total.write(1,i,float(res[items[i]]))
    wb.save("Output/"+filename+".xls")

def OptimizationDay(parameter_json,load_json,begin_time,time_scale,storage_begin_json,storage_end_json,model_type,z_file):
    """计算优化问题，时间尺度不定，输入包括末时刻储能。

    Args:
        parameter_json (_type_): 输入config文件中读取的参数
        load_json (_type_): 预测的负荷向量
        time_scale (_type_): 计算的小时
        storage_begin_json (_type_): 初始端储能状态
        storage_end_json (_type_): 末端储能状态
    """
    # 一些常熟参数
    modelType={
        'MIP':'MIP',
        'LP':'LP',
    }
    c = 4200/3.6/1000 #kwh/(吨*℃)
    period = time_scale

    # 初始化设备效率参数
    try:
        k_fc_p = parameter_json['device']['fc']['k_fc_p']*parameter_json['device']['fc']['theta_ex']
        k_fc_g = parameter_json['device']['fc']['k_fc_g']*parameter_json['device']['fc']['theta_ex']

        # k_fc_p_200 = 33/(parameter_json['device']['fc']['power_200']['g_p_ratio']+1)*parameter_json['device']['fc']['power_200']['theta_ex']
        # g_p_ratio_200=parameter_json['device']['fc']['power_200']['g_p_ratio']
        # k_fc_p_400 = 33/(parameter_json['device']['fc']['power_400']['g_p_ratio']+1)*parameter_json['device']['fc']['power_400']['theta_ex']
        # g_p_ratio_400=parameter_json['device']['fc']['power_400']['g_p_ratio']
        # k_fc_p_600 = 33/(parameter_json['device']['fc']['power_600']['g_p_ratio']+1)*parameter_json['device']['fc']['power_600']['theta_ex']
        # g_p_ratio_600=parameter_json['device']['fc']['power_600']['g_p_ratio']

        k_b=parameter_json['device']['battery']['k_b']

        max_count_day=parameter_json['device']['ghp']['max_count_day']
        # k_el = parameter_json['device']['el']['beta_el']
        k_eb = parameter_json['device']['eb']['k_eb']
        # k_pv = parameter_json['device']['pv']['beta_pv']
        # k_hp_q = parameter_json['device']['hp']['beta_hpq']
        # k_hp_g = parameter_json['device']['hp']['beta_hpg']
        # k_pump = parameter_json['device']['pump']['beta_p']

        ht_loss = parameter_json['device']['ht']['miu_loss']
        # ct_loss = parameter_json['device']['ct']['miu_loss']
        de_loss = parameter_json['device']['de']['miu_loss']
    except BaseException as E:
        _logging.error('读取config.json中设备效率参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化容量参数
    try:
        m_ht = parameter_json['device']['ht']['water_max']
        # m_ct = parameter_json['device']['ct']['water_max']
        m_de = parameter_json['device']['de']['water_max']
        m_gtw=parameter_json['device']['gtw']['water_max']
        # k_gtw_fluid=877/898*m_gtw/400-0.0297
        k_gtw_fluid=0.12
        p_fc_max = parameter_json['device']['fc']['power_max']
        # p_el_max = parameter_json['device']['el']['power_max']
        p_eb_max = parameter_json['device']['eb']['power_max']
        # a_pv = parameter_json['device']['pv']['area_max']
        # hst_max = parameter_json['device']['hst']['sto_max']
        p_hp_max = parameter_json['device']['ghp']['power_max']
    except BaseException as E:
        _logging.error('读取config.json中设备容量参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化边界上下限参数
    try:
        t_ht_max = parameter_json['device']['ht']['t_max']
        t_ht_min = parameter_json['device']['ht']['t_min']
        # t_ct_max = parameter_json['device']['ct']['t_max']
        # t_ct_min = parameter_json['device']['ct']['t_min']
        t_de_max = parameter_json['device']['de']['t_max']
        t_de_min = parameter_json['device']['de']['t_min']
        t_gtw_in_min=parameter_json['device']['gtw']['t_in_min']
        c_b_max=parameter_json['device']['battery']['capacity_max']
        # t_ht_wetbulb = parameter_json['device']['ht']['t_wetbulb']
        # t_ct_wetbulb = parameter_json['device']['ct']['t_wetbulb']
        # slack_ht = parameter_json['device']['ht']['end_slack']
        # slack_ct = parameter_json['device']['ct']['end_slack']
        # slack_hsto = parameter_json['device']['hst']['end_slack']
        tem_diff=parameter_json['device']['de']['temperature_difference']#读取供回水温度差
    except BaseException as E:
        _logging.error('读取config.json中边界上下限参数失败,错误原因为{}'.format(E))
        raise Exception
    # 初始化价格
    try:
        lambda_ele_in = parameter_json['price']['ele_TOU_price']
        lambda_ele_in=(lambda_ele_in*(int(period/24)))[begin_time:period]
        # lambda_ele_out = parameter_json['price']['power_sale']
        hydrogen_price = parameter_json['price']['hydrogen_price']
        # p_demand_price=parameter_json['price']['demand_electricity_price']
    except BaseException as E:
        _logging.error('读取config.json中价格参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化负荷
    try:
        p_load = list(load_json['ele_load'])[begin_time:period]
        g_load = list(load_json['g_load'])[begin_time:period]
        # q_load = list(load_json['q_load'])
        pv_generation = list(load_json['pv_generation'])[begin_time:period]
        t_tem = list(load_json['ambient_temperature'])[begin_time:period] #读环境温度
        g_func= list(load_json['g函数值'])
    except BaseException as E:
        _logging.error('读取负荷文件中电冷热光参数失败,错误原因为{}'.format(E))
        raise Exception
    # 初始化储能
    # t_ht_start=17

    try:
        # hydrogen_bottle_max_start = storage_begin_json['hydrogen_bottle_max'][begin_time]  #气瓶
        # hst_kg_start = storage_begin_json['hst_kg'][begin_time]  # 缓冲罐剩余氢气
        t_ht_start = storage_begin_json['t_ht'][begin_time]  # 热水罐
        # t_ct_start = storage_begin_json['t_ct'][begin_time]  # 冷水罐
        t_de_start = storage_begin_json['t_de'][begin_time]  # 末端
        soc_b_start= storage_begin_json['soc_b'][begin_time]
        ghp_has_open=storage_begin_json['ghp_has_open'][begin_time]
        t_gtw_g=storage_begin_json['t_gtw_g'][begin_time]
        # hydrogen_bottle_max_final = storage_end_json['hydrogen_bottle_max'][begin_time+time_scale] #气瓶
        # hst_kg_final = storage_end_json['hst_kg'][begin_time+time_scale]  # 缓冲罐剩余氢气
        t_ht_final = storage_end_json['t_ht'][period]  # 热水罐
        # t_ct_final = storage_end_json['t_ct'][begin_time+time_scale]  # 冷水罐
    except BaseException as E:
        _logging.error('读取储能容量初始值和最终值失败,错误原因为{}'.format(E))
        raise Exception

    # 通过gurobi建立模型
    try:
        m = gp.Model("bilinear")
    except BaseException as E:
        _logging.error('gurobi创建优化模型失败{}'.format(E))
        raise Exception
    
    # 添加变量
    if model_type==modelType['MIP']:
        # z_a=[m.addVar(vtype=GRB.BINARY,name=f"z_a{t}")for t in range(begin_time,period)]#工况a,水箱供给末端
        # z_b=[m.addVar(vtype=GRB.BINARY,name=f"z_b{t}")for t in range(begin_time,period)]#工况b,锅炉给水箱蓄
        # z_c=[m.addVar(vtype=GRB.BINARY,name=f"z_c{t}")for t in range(begin_time,period)]#工况c,燃料电池给水箱蓄
        # z_d=[m.addVar(vtype=GRB.BINARY,name=f"z_d{t}")for t in range(begin_time,period)]#工况d,热泵给水箱蓄
        # z_e=[m.addVar(vtype=GRB.BINARY,name=f"z_e{t}")for t in range(begin_time,period)]#工况e,热泵和燃料电池一起给水箱蓄
        z_ht_de=[m.addVar(vtype=GRB.BINARY,name=f"z_ht_de{t}")for t in range(begin_time,period)]# 判断ht能不能给末端供的01量
        z_hp=[m.addVar(vtype=GRB.BINARY,name=f"z_e{t}")for t in range(begin_time,period)]
        z_b= [m.addVar(vtype=GRB.CONTINUOUS, name=f"z_b{t}") for t in range(begin_time,period)]# 电池充还是方，冲1方0,#if p_b>storageM, z_b=1,else z_b=0
    elif model_type==modelType['LP']:
        # z_a=z_file['z_a']
        # z_b=z_file['z_b']
        # z_c=z_file['z_c']
        # z_d=z_file['z_d']
        # z_e=z_file['z_e']
        z_ht_de=z_file['z_ht_de'][-period+begin_time:]
        z_hp=z_file['z_hp'][-period+begin_time:]
        z_b=z_file['z_b'][-period+begin_time:] 

    storageM=4000 #一个大数，用于把变量范围变成>=0
    #opex = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="opex")
    opex = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="opex_"+str(t)) for t in range(begin_time,period)]
    t_ht = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ht{t}") for t in range(begin_time,period)] # temperature of hot water tank
    t_ht_l = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ht_l{t}") for t in range(begin_time,period)] # temperature of hot water tank in last time
    g_ht=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_ht{t}") for t in range(begin_time,period)]#水箱给末端的供热量，这里用g_ht+storageM代替g_ht，使变量>=0
    # t_ct = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ct{t}") for t in range(begin_time,period)] # temperature of hot water tank
    # t_ct_l = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ct_l{t}") for t in range(begin_time,period)] # temperature of hot water tank in last time
    t_de=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_de{t}") for t in range(begin_time,period)]# average temperature of demand
    t_de_l=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_de_l{t}") for t in range(begin_time,period)]# average temperature of demand in last time
    
    
    g_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc{t}") for t in range(begin_time,period)] # heat generated by fuel cells
    p_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_fc{t}") for t in range(begin_time,period)]
    h_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_fc{t}") for t in range(begin_time,period)] # hydrogen used in fuel cells
    # z_fc_200=[m.addVar(vtype=GRB.BINARY,name=f"z_fc_200{t}")for t in range(begin_time,period)]
    # z_fc_400=[m.addVar(vtype=GRB.BINARY,name=f"z_fc_400{t}")for t in range(begin_time,period)]
    # z_fc_600=[m.addVar(vtype=GRB.BINARY,name=f"z_fc_600{t}")for t in range(begin_time,period)]


    
    # p_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_hp{t}") for t in range(begin_time,period)] # power consumption of heat pumps
    g_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_hp{t}") for t in range(begin_time,period)] # heat generated by heat pumps
    cop_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"cop_hp{t}") for t in range(begin_time,period)]
    t_gtw_out = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_gtw_out{t}") for t in range(begin_time,period)]
    g_gtw_l = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_gtw_l{t}") for t in range(begin_time,period)]
    g_gtw = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_gtw{t}") for t in range(begin_time,period)]
    t_gtw_in = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_gtw_in{t}") for t in range(begin_time,period)]
    t_b = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_b{t}") for t in range(begin_time,period)]
    
    # q_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"q_hp{t}") for t in range(begin_time,period)] # heat generated by heat pumps

    # h_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_el{t}") for t in range(begin_time,period)] # hydrogen generated by electrolyzer
    # p_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_el{t}") for t in range(begin_time,period)] # power consumption by electrolyzer

    # h_sto = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_sto{t}") for t in range(begin_time,period)] # hydrogen storage
    # h_sto_l = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_sto_l{t}") for t in range(begin_time,period)] # last time hydrogen storage
    h_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_pur{t}") for t in range(begin_time,period)] # hydrogen purchase

    p_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pur{t}") for t in range(begin_time,period)] # power purchase
    # p_demand_max=m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_demand_max")

    # p_pump = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump{t}") for t in range(begin_time,period)] 
    p_eb = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_eb{t}") for t in range(begin_time,period)] # power consumption by ele boiler
    g_eb = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_eb{t}") for t in range(begin_time,period)] # heat generated by ele boiler

    p_pv = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pv{t}") for t in range(begin_time,period)] # power generate by PV

    p_b=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_b{t}") for t in range(begin_time,period)] # battery charge or discharge,+放-充， 这里用p_b+storageM代替p_b，使变量>=0,
    
    z_p_b=[m.addVar(vtype=GRB.CONTINUOUS,lb=0, name=f"z_p_b{t}") for t in range(begin_time,period)] #z_p_b= z_b*(-p_b+storageM)
    soc_b=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"soc_b{t}") for t in range(begin_time,period)] #battery soc
    soc_b_l=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"soc_b_l{t}") for t in range(begin_time,period)]

    g_balance=[[] for _ in range(begin_time,period)]
    p_balance=[[] for _ in range(begin_time,period)]
    p_pv_rhs=[[] for _ in range(begin_time,period)]
    # if hydrogen_bottle_max_final - hydrogen_bottle_max_start>=-1:
    #     m.addConstr(gp.quicksum(h_pur) <= hydrogen_bottle_max_final - hydrogen_bottle_max_start)
    # else:
    #     m.addConstr(gp.quicksum(h_pur) == 0)
    #print(storage_end_json['end_slack'][0])
    # if storage_end_json['end_slack'][begin_time+time_scale] == False:
    #     m.addConstr(t_ht[-1] == t_ht_final)
    #     # m.addConstr(t_ct[-1] == t_ct_final)
    #     # m.addConstr(h_sto[-1] == hst_kg_final)
    # else:
    #     m.addConstr(t_ht[-1] >= t_ht_start * (1-slack_ht))
    #     m.addConstr(t_ht[-1] <= t_ht_start * (1+slack_ht))
    #     # m.addConstr(t_ct[-1] >= t_ct_start * (1-slack_ct))
    #     # m.addConstr(t_ct[-1] <= t_ct_start * (1+slack_ct))
    #     # m.addConstr(h_sto[-1] >= hst_kg_start * (1-slack_hsto))
    #     # m.addConstr(h_sto[-1] <= hst_kg_start * (1+slack_hsto))
    # # 储能约束
    m.addConstr(soc_b_l[0]==soc_b_start)
    m.addConstr(t_ht_l[0] == t_ht_start)
    m.addConstr(t_de_l[0] == t_de_start)
    m.addConstr(g_gtw_l[0] == 0)
    # m.addConstr(t_ct_l[0] == t_ct_start)
    # m.addConstr(h_sto_l[0] == hst_kg_start)
    ht_fin_tem_slack_var=m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"ht_fin_tem_slack_var")
    m.addConstr(-t_ht[-1] +ht_fin_tem_slack_var == -t_ht_final)

    m.addConstrs(t_ht[i] - t_ht_l[i+1]==0 for i in range(period-1-begin_time))
    # m.addConstrs(t_ct[i] == t_ct_l[i+1] for i in range(period-1))
    # m.addConstrs(h_sto[i] == h_sto_l[i+1] for i in range(period-1))
    m.addConstrs(t_de[i] - t_de_l[i+1]==0 for i in range(period-1-begin_time))
    m.addConstrs(g_gtw[i] - g_gtw_l[i+1]==0 for i in range(period-1-begin_time))
    m.addConstrs(soc_b[i] - soc_b_l[i+1]==0 for i in range(period-1-begin_time))

    ghp_open_num_slack_var=m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"ghp_open_num_slack_var")
    m.addConstr(gp.quicksum(z_hp)+ghp_open_num_slack_var==period*max_count_day/24-ghp_has_open)
    for i in range(period-begin_time):
        # 能量平衡
        # m.addConstr(p_fc[i] + p_pur[i] + p_pv[i] == p_el[i] + p_eb[i] + p_hp[i]  + p_pump[i] + p_load[i])
        p_balance[i]=m.addConstr(p_fc[i] + p_pur[i] + p_pv[i] -p_eb[i] - p_hp_max*z_hp[i] + (p_b[i]-storageM)==  p_load[i])
        #m.addConstr(c*m_ht*(t_ht[i] - t_ht_l[i] - ht_loss * (t_ht_l[i] - t_ht_wetbulb)) + g_load[i] == g_fc[i] + g_hp[i] + g_eb[i])
        # m.addConstr(g_load[i] == g_fc[i] + g_hp[i] + g_eb[i] + g_ht[i])

        #m.addConstr(c*m_ct*(t_ct[i] - t_ct_l[i] - ct_loss * (t_ct_l[i] - t_ct_wetbulb)) + q_hp[i] == q_load[i])
        # m.addConstr(c*m_ct*(t_ct[i] - t_ct_l[i]) + q_hp[i] == q_load[i])

        m.addConstr(h_pur[i] - h_fc[i] == 0)
        
        #最大需量
        # m.addConstr(p_demand_max-p_pur[i]>=0)



        # 工况约束
        # m.addConstr(z_a[i]*g_ht[i]>=0)
        # m.addConstr(g_ht[i]+z_b[i]*g_eb[i]+z_c[i]*g_fc[i]+z_d[i]*g_hp[i]+z_e[i]*(g_fc[i]+g_hp[i])>=0)
        # m.addConstr(z_a[i]+z_b[i]+z_c[i]+z_d[i]+z_e[i]==1)
        #燃料电池不能给水箱蓄
        # m.addConstr(z_c[i]==0)
        # m.addConstr(z_e[i]==0)

        #给末端供热的约束
        # g_balance[i] = m.addConstr(g_ht[i]*z_a[i]+g_eb[i]*(1-z_b[i])+g_fc[i]*(1-z_c[i]-z_e[i])+g_hp[i]*(1-z_d[i]-z_e[i])-de_loss*(t_de_l[i]-43)*m_de-c*m_de*(t_de[i]-t_de_l[i]) == g_load[i])
        g_balance[i] = m.addConstr(g_ht[i]-storageM+g_eb[i]+g_fc[i]+g_hp[i]-de_loss*(t_de_l[i]-43)*m_de-c*m_de*(t_de[i]-t_de_l[i]) == g_load[i])



    t_ht_cons=[0 for i in range(period-begin_time)]
    g_fc_h_cons=[0 for i in range(period-begin_time)]
    g_fc_p_cons=[0 for i in range(period-begin_time)]
    eb_ub_con=[0 for i in range(period-begin_time)]
    # 每一时段约束

    #松弛变量，约束全变==，lp变为标准型
    # t_ht_cons_ub_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ht_cons_ub_slack_var{t}") for t in range(begin_time,period)]
    # t_gtw_in_lb_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_gtw_in_lb_slack_var{t}") for t in range(begin_time,period)]
    # t_de_lb_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_de_lb_slack_var{t}") for t in range(begin_time,period)]
    # t_de_ub_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_de_ub_slack_var{t}") for t in range(begin_time,period)]
    # g_fc_ub_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc_ub_slack_var{t}") for t in range(begin_time,period)]
    # g_eb_ub_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_eb_ub_slack_var{t}") for t in range(begin_time,period)]
    # soc_b_ub_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"soc_b_ub_slack_var{t}") for t in range(begin_time,period)]
    # p_pv_ub_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pv_ub_slack_var{t}") for t in range(begin_time,period)]
    # ht_supply_tem1_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"ht_supply_tem1_slack_var{t}") for t in range(begin_time,period)]
    # ht_supply_val_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"ht_supply_val_slack_var{t}") for t in range(begin_time,period)]
    # batter_linear1_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"batter_linear1_slack_var{t}") for t in range(begin_time,period)]
    # batter_linear2_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"batter_linear2_slack_var{t}") for t in range(begin_time,period)]
    # batter_linear3_slack_var=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"batter_linear3_slack_var{t}") for t in range(begin_time,period)]
    
    for i in range(period-begin_time):
        # 上下限约束
        # m.addConstr(t_ht[i] >= t_ht_min)

        t_ht_cons[i]=m.addConstr(t_ht[i] <= t_ht_max)
        # t_ht_cons[i]=m.addConstr(t_ht[i] +t_ht_cons_ub_slack_var[i]== t_ht_max)

        # m.addConstr(t_ct[i] >= t_ct_min)
        # m.addConstr(t_ct[i] <= t_ct_max)

        # m.addConstr(-t_gtw_in[i]+t_gtw_in_lb_slack_var[i]==-t_gtw_in_min)
        m.addConstr(-t_gtw_in[i]<=-t_gtw_in_min)

        # m.addConstr(t_gtw_out[i]>=t_gtw_in_min)

        # m.addConstr(-t_de[i]+t_de_lb_slack_var[i] == -t_de_min)
        m.addConstr(-t_de[i]<= -t_de_min)

        # m.addConstr(t_de[i]+t_de_ub_slack_var[i] == t_de_max)
        m.addConstr(t_de[i]<= t_de_max)

        # g_fc_p_cons[i]=m.addConstr(g_fc[i] +g_fc_ub_slack_var[i]== p_fc_max*k_fc_g/k_fc_p)
        g_fc_p_cons[i]=m.addConstr(g_fc[i] <= p_fc_max*k_fc_g/k_fc_p)

        # m.addConstr(p_fc[i] <= p_fc_max)
        # m.addConstr(p_el[i] <= p_el_max)

        # eb_ub_con[i]=m.addConstr(g_eb[i] +g_eb_ub_slack_var[i]== p_eb_max*k_eb)
        eb_ub_con[i]=m.addConstr(g_eb[i] <= p_eb_max*k_eb)



        # t=m.addConstr(p_eb[i] <= p_eb_max)
        # m.addConstr(p_hp[i] <= p_hp_max)

        # m.addConstr(soc_b[i] +soc_b_ub_slack_var[i] == c_b_max)
        m.addConstr(soc_b[i] <= c_b_max)

        # 能量平衡

        # 设备约束
        ## fc
        # m.addConstr(p_fc[i] <= p_fc_max)
        m.addConstr(p_fc[i] - k_fc_p * h_fc[i] == 0)
        g_fc_h_cons[i]=m.addConstr(g_fc[i] - k_fc_g * h_fc[i] == 0)

        # m.addConstr(z_fc_200[i]+z_fc_400[i]+z_fc_600[i]<=1)
        # m.addConstr(p_fc[i] == 200*z_fc_200[i]+400*z_fc_400[i]+600*z_fc_600[i])        
        # m.addConstr(g_fc[i] == 200*z_fc_200[i]*g_p_ratio_200+400*z_fc_400[i]*g_p_ratio_400+600*z_fc_600[i]*g_p_ratio_600)
        # m.addConstr(p_fc[i] == k_fc_p * h_fc[i])
        
        ## hp
        # m.addConstr(p_hp[i] <= p_hp_max)
        # m.addConstr(q_hp[i] == k_hp_q * p_hp[i])
        
        m.addConstr(g_hp[i] == cop_hp[i] * p_hp_max*z_hp[i])
        m.addConstr(cop_hp[i]==2+0.1209*t_gtw_out[i])
        m.addConstr(g_gtw[i]==g_hp[i]-p_hp_max*z_hp[i])
        m.addConstr(g_gtw[i]==c*m_gtw*(t_gtw_out[i]-t_gtw_in[i]))
        m.addConstr(t_gtw_out[i]==k_gtw_fluid*(t_gtw_in[i]-t_b[i])+t_b[i])
        m.addConstr(t_b[i]==t_gtw_g-(1000/(2*np.pi*2.07*200*192))*gp.quicksum((g_gtw[j]-g_gtw_l[j])*g_func[i-j] for j in range(i+1)))



        ## el
        # m.addConstr(p_el[i] <= p_el_max)
        # m.addConstr(h_el[i] == k_el * p_el[i])
        ## eb
        # m.addConstr(p_eb[i] <= p_eb_max)
        m.addConstr(g_eb[i] - k_eb * p_eb[i] == 0)
        ## pump
        #m.addConstr(p_pump[i] == k_pump * mass_flow[i])
        ## pv
        # m.addConstr(p_pv[i] <= solar[i] * a_pv * k_pv)

        # p_pv_rhs[i]= m.addConstr(p_pv[i] +p_pv_ub_slack_var[i]== pv_generation[i])
        p_pv_rhs[i]= m.addConstr(p_pv[i] <= pv_generation[i])

        ## ht
        ### ht温度变化
        m.addConstr(c*m_ht*(t_ht[i]-t_ht_l[i])+g_ht[i]-storageM+ht_loss*(t_ht_l[i]-t_tem[i])*m_ht==0)
        ### ht供热温度约束
        # m.addConstr(-t_ht_l[i]+t_de_l[i]-tem_diff/2+100*(z_ht_de[i]-1)+ht_supply_tem1_slack_var[i]==0)
        # m.addConstr(g_ht[i]-storageM-c*m_de*(t_ht_l[i]-t_de_l[i])*z_ht_de[i]+ht_supply_val_slack_var[i]==0)
        m.addConstr(-t_ht_l[i]+t_de_l[i]-tem_diff/2+100*(z_ht_de[i]-1)<=0)
        m.addConstr(g_ht[i]-storageM-c*m_de*(t_ht_l[i]-t_de_l[i])*z_ht_de[i]<=0)

        # m.addConstr(t_ht_l[i]-45>=100*(z_ht_de[i]-1))
        # m.addConstr(t_ht_l[i]-45<=100*(z_ht_de[i]))
        # m.addConstr(g_ht[i]<=c*m_de*(t_ht_l[i]-45)*z_ht_de[i])


        #battery
        m.addConstr(soc_b[i]-soc_b_l[i]==k_b*z_p_b[i]+(-p_b[i]+storageM-z_p_b[i])/k_b)
        # m.addConstr(z_p_b[i]+batter_linear1_slack_var[i]==10000*z_b[i])
        # m.addConstr(z_p_b[i]+batter_linear2_slack_var[i]==10000*(1-z_b[i])-p_b[i]+storageM)
        # m.addConstr(-p_b[i]+storageM-z_p_b[i]+batter_linear3_slack_var[i]==0)
        m.addConstr(z_p_b[i]<=10000*z_b[i])
        m.addConstr(z_p_b[i]<=10000*(1-z_b[i])-p_b[i]+storageM)
        m.addConstr(-p_b[i]+storageM-z_p_b[i]<=0)

        ## opex 
        m.addConstr(opex[i] - hydrogen_price * h_pur[i] - p_pur[i] * lambda_ele_in[i] == 0)
    # set objective
    
    m.setObjective(gp.quicksum(opex), GRB.MINIMIZE)
    # m.setObjective(gp.quicksum(opex), GRB.MINIMIZE)
    # m.params.NonConvex = 2
    # m.params.MIPGap = 0.01
    # m.params.TimeLimit=300
    m.Params.LogFile = "testlog.log"

    try:
        m.write("Temp\model.LP")
        m.optimize()
        _logging.info("success optimize")
    except gp.GurobiError as e:
        print("Optimize failed due to non-convexity")
        _logging.error(e)
    if m.status == GRB.INFEASIBLE or m.status == 4:
        print('Model is infeasible')
        m.computeIIS()
        m.write('Temp\model.ilp')
        print("Irreducible inconsistent subsystem is written to file 'model.ilp'")
        exit(0)



    # 计算一些参数
    # opex_without_opt = [lambda_ele_in[i]*(p_load[i]+q_load[i]/k_hp_q+g_load[i]/k_eb) for i in range(period-begin_time)]
    dict_control={}
    z_file={}
    model_SAObj={}
    var_SALBUB={}
    constraint_SARHS={}
    judge_dict={}
    if model_type==modelType['MIP']:
        dict_control = {# 负荷
            # 'time':begin_time,
            # thermal binary
            # 'b_hp':[1 if p_hp[i].x > 0 else 0 for i in range(period-begin_time)],
            # 'b_eb':[1 if p_eb[i].x > 0 else 0 for i in range(period-begin_time)],
            # # -1代表储能，1代表供能
            # 'b_ht':[-1 if t_ht[i].x > t_ht_l[i].x else 1 if t_ht[i].x > t_ht_l[i].x else 0  for i in range(period-begin_time)],
            # # 'b_ct':[1 if t_ct[i].x > t_ct_l[i].x else -1 if t_ct[i].x > t_ht_l[i].x else 0  for i in range(period-begin_time)],
            # 'b_fc':[1 if p_fc[i].x > 0 else 0 for i in range(period-begin_time)],

            # ele
            'opex':[opex[i].x for i in range(period-begin_time)],
            # 'p_demand_price':p_demand_price*p_demand_max.x/24/30*time_scale,
            # 'operation_mode':[z_a[i].x*1+z_b[i].x*2+z_c[i].x*3+z_d[i].x*4+z_e[i].x*5 for i in range(period-begin_time)],
            'p_eb':[p_eb[i].x for i in range(period-begin_time)],
            'p_fc':[p_fc[i].x for i in range(period-begin_time)],
            'p_pv':[p_pv[i].x for i in range(period-begin_time)],
            'z_hp':[z_hp[i].x for i in range(period-begin_time)],
            'p_pur':[p_pur[i].x for i in range(period-begin_time)],
            'p_load':[p_load[i] for i in range(period-begin_time)],
            'p_b':[p_b[i].x-storageM for i in range(period-begin_time)],
            'lambda_ele_in':[lambda_ele_in[i]for i in range(period-begin_time)],
            'g_fc':[g_fc[i].x for i in range(period-begin_time)],
            'g_eb':[g_eb[i].x for i in range(period-begin_time)],
            'g_hp':[g_hp[i].x for i in range(period-begin_time)],
            'g_ht':[g_ht[i].x-storageM for i in range(period-begin_time)],
            'g_load':[g_load[i] for i in range(period-begin_time)],
            'z_ht_de':[z_ht_de[i].x for i in range(period-begin_time)],
            'h_pur':[h_pur[i].x for i in range(period-begin_time)],
            'cop_hp':[cop_hp[i].x for i in range(period-begin_time)],
            'g_gtw':[g_gtw[i].x for i in range(period-begin_time)],
            't_gtw_out':[t_gtw_out[i].x for i in range(period-begin_time)],
            't_b':[t_b[i].x for i in range(period-begin_time)],
            't_gtw_in':[t_gtw_in[i].x for i in range(period-begin_time)],
            't_ht':[t_ht[i].x for i in range(period-begin_time)],
            't_ht_l':[t_ht_l[i].x for i in range(period-begin_time)],
            't_de':[t_de[i].x for i in range(period-begin_time)],
            't_de_l':[t_de_l[i].x for i in range(period-begin_time)],
            'soc_b':[soc_b[i].x for i in range(period-begin_time)],
            'soc_b_l':[soc_b_l[i].x for i in range(period-begin_time)],
            'k_b':[k_b for i in range(period-begin_time)],
            'k_eb':[k_eb for i in range(period-begin_time)],
            'k_fc_g':[k_fc_g for i in range(period-begin_time)],
            'k_fc_p':[k_fc_p for i in range(period-begin_time)],
            # 'p_el':[p_el[i].x for i in range(period-begin_time)],
        }
        z_file={
            # 'z_a':[z_a[i].x for i in range(period-begin_time)],
            # 'z_b':[z_b[i].x for i in range(period-begin_time)],
            # 'z_c':[z_c[i].x for i in range(period-begin_time)],

            # 'z_d':[z_d[i].x for i in range(period-begin_time)],
            # 'z_e':[z_e[i].x for i in range(period-begin_time)],
            'z_b':[z_b[i].x for i in range(period-begin_time)],
            'z_ht_de':[z_ht_de[i].x for i in range(period-begin_time)],
            'z_hp':[z_hp[i].x for i in range(period-begin_time)],
        }
        model_SAObj={}
        var_SALBUB={}
        constraint_SARHS={}
        judge_dict={}
    elif model_type==modelType['LP']:

        # c=m.getConstrs()
        # constr_names_to_indices = {
        #     c.ConstrName: i for i, c in enumerate(c)
        # }
        # v=m.getVars()
        # vb=[]
        # for vv in v:
        #     if vv.VBasis==0: vb.append(vv)
        # r=[i.RHS for i in c]
        # B=extract_basis(m).A
        # B_inv=np.linalg.inv(B)
        # # B_inv[(B_inv<0.00001) & (B_inv>-0.00001)]=0 #这个逆矩阵比较精确，这里不洗数据
        # B_inv_r=np.dot(B_inv,r)
        # B_inv_r[(B_inv_r<0.000001) & (B_inv_r>-0.000001)]=0
        # B_inv_T=B_inv.T
        # B_inv_T[(B_inv_T<0.000001) & (B_inv_T>-0.000001)]=0

        # verr=[0 for vv in v]
        # basisNum=0
        # for i in range(len(v)):
        #     if v[i].VBasis==0:
        #         verr[i]=v[i].x-B_inv_r[basisNum]
        #         basisNum=basisNum+1

        # # mval=[vv.x for vv in v]
        # # valError=[mval[i]-v[i].x for i in len(v)]
        # cName=[cc.ConstrName for cc in c]
        # myRHSLB=[cc.RHS for cc in c]
        # myRHSUB=[cc.RHS for cc in c]
        # cRHSLow=[cc.SARHSLow for cc in c]
        # cRHSUP=[cc.SARHSUP for cc in c]
        # LBerror=[cc.SARHSLow for cc in c]
        # UBerror=[cc.SARHSUP for cc in c]
        # for constr in c:
        #     conindex=constr_names_to_indices[constr.ConstrName]
        #     zhengb=[-B_inv_r[i]/B_inv_T[conindex][i] if B_inv_T[conindex][i]<0 else 1000000 for i in range(len(B_inv_r))]
        #     fub=[-B_inv_r[i]/B_inv_T[conindex][i] if B_inv_T[conindex][i]>0 else -1000000 for i in range(len(B_inv_r))]
        #     # jiab_=[jiab[i] if jiab[i]>=0 else 10000 for i in range(len(jiab))]
        #     # jianb_=[jianb[i] if jianb[i]<=0 else -10000 for i in range(len(jianb))]
        #     min_zhengb=min(zhengb)
        #     max_fub=max(fub)
        #     myRHSLB[conindex]=constr.RHS+max_fub
        #     myRHSUB[conindex]=constr.RHS+min_zhengb
        #     LBerror[conindex]=myRHSLB[conindex]-constr.SARHSLow
        #     UBerror[conindex]=myRHSUB[conindex]-constr.SARHSUP
        #     if abs(LBerror[conindex])>0.01 or abs(UBerror[conindex])>0.01:
        #         if not((max_fub==-1000000 and constr.SARHSLow==float("-inf")) or(min_zhengb==1000000 and constr.SARHSUP==float("inf"))):
        #             print(conindex,constr.SARHSLow,constr.SARHSUP,myRHSLB[conindex],myRHSUB[conindex])
        #     #     []
        #     # if conindex in [204,229,254,329,629]:
        #     #     print('kk')
        # nplberr=np.array([myRHSLB,cRHSLow,LBerror]).T
        # nplberr[(nplberr<0.0001) & (nplberr>-0.0001)]=0
        # pd.DataFrame(nplberr,columns=['myRHSLB','cRHSLow','LBerror'],index=cName).to_csv('lberr.csv')
        # npuberr=np.array([myRHSUB,cRHSUP,UBerror]).T
        # npuberr[(npuberr<0.0001) & (npuberr>-0.0001)]=0
        # pd.DataFrame(npuberr,columns=['myRHSUB','cRHSUP','UBerror'],index=cName).to_csv('uberr.csv')

        # myvLBUP=[vv.x for vv in v]
        # vLBUP=[vv.SALBUP for vv in v]
        # vLBUPerr=[1 for vv in v]
        # vName=[vv.VarName for vv in v]
        # for i in range(len(v)):
        #     if v[i].VBasis!=BASIC:
        #         col= m.getCol(v[i])
        #         vv_range=[0 for j in range(col.size())]
        #         sumB_inv_col=[0 for rr in B_inv_T]
        #         for j in range(col.size()):
        #             constr = col.getConstr(j)
        #             conindex=constr_names_to_indices[constr.ConstrName]
        #             sumB_inv_col=[sumB_inv_col[t]+ B_inv_T[conindex][t] for t in range(len(sumB_inv_col))]
        #         # zhengv=[-B_inv_r[i]/sumB_inv_col[i] if sumB_inv_col[i]<0 else 1000000 for i in range(len(B_inv_r))]
        #         deltav=[B_inv_r[i]/sumB_inv_col[i] if sumB_inv_col[i]>0 else 1000000 for i in range(len(B_inv_r))]
        #         # jiab_=[jiab[i] if jiab[i]>=0 else 10000 for i in range(len(jiab))]
        #         # jianb_=[jianb[i] if jianb[i]<=0 else -10000 for i in range(len(jianb))]
        #         min_deltav=min(deltav)
        #         # max_fuv=max(fuv)
        #             # if coeff<0:
        #             #     vv_range[j]=(constr.RHS-myRHSUB[conindex])/coeff
        #             # else:
        #             #     vv_range[j]=(constr.RHS-myRHSLB[conindex])/coeff
        #         myvLBUP[i]=min_deltav
        #         vLBUPerr[i]=myvLBUP[i]-vLBUP[i]
        #         if vLBUPerr[i]<-0.01 or vLBUPerr[i]>0.01:
        #             print(i,myvLBUP[i],vLBUP[i])
        # npvLBUP=np.array([myvLBUP,vLBUP,vLBUPerr]).T
        # npvLBUP[(npvLBUP<0.0001) & (npvLBUP>-0.0001)]=0
        # pd.DataFrame(npvLBUP,columns=['myvLBUP','vLBUP','vLBUPerr'],index=vName).to_csv('npvLBUP.csv')
        # print('ll')



        dict_control = {# 负荷
            # 'time':begin_time,
            # thermal binary
            # 'b_hp':[1 if p_hp[i].x > 0 else 0 for i in range(period-begin_time)],
            # 'b_eb':[1 if p_eb[i].x > 0 else 0 for i in range(period-begin_time)],
            # # -1代表储能，1代表供能
            # 'b_ht':[-1 if t_ht[i].x > t_ht_l[i].x else 1 if t_ht[i].x > t_ht_l[i].x else 0  for i in range(period-begin_time)],
            # # 'b_ct':[1 if t_ct[i].x > t_ct_l[i].x else -1 if t_ct[i].x > t_ht_l[i].x else 0  for i in range(period-begin_time)],
            # 'b_fc':[1 if p_fc[i].x > 0 else 0 for i in range(period-begin_time)],

            # ele
            'opex':[opex[i].x for i in range(period-begin_time)],
            # 'p_demand_price':p_demand_price*p_demand_max.x/24/30*time_scale,
            # 'operation_mode':[z_a[i].x*1+z_b[i].x*2+z_c[i].x*3+z_d[i].x*4+z_e[i].x*5 for i in range(period-begin_time)],
            'p_eb':[p_eb[i].x for i in range(period-begin_time)],
            'p_fc':[p_fc[i].x for i in range(period-begin_time)],
            'p_pv':[p_pv[i].x for i in range(period-begin_time)],
            # 'z_hp':[z_hp[i].x for i in range(period-begin_time)],
            'p_pur':[p_pur[i].x for i in range(period-begin_time)],
            'p_load':[p_load[i] for i in range(period-begin_time)],
            'p_b':[p_b[i].x-storageM for i in range(period-begin_time)],
            'lambda_ele_in':[lambda_ele_in[i]for i in range(period-begin_time)],
            'g_fc':[g_fc[i].x for i in range(period-begin_time)],
            'g_eb':[g_eb[i].x for i in range(period-begin_time)],
            'g_hp':[g_hp[i].x for i in range(period-begin_time)],
            'g_ht':[g_ht[i].x-storageM for i in range(period-begin_time)],
            'g_load':[g_load[i] for i in range(period-begin_time)],
            # 'z_ht_de':[z_ht_de[i].x for i in range(period-begin_time)],
            'h_pur':[h_pur[i].x for i in range(period-begin_time)],
            'cop_hp':[cop_hp[i].x for i in range(period-begin_time)],
            'g_gtw':[g_gtw[i].x for i in range(period-begin_time)],
            't_gtw_out':[t_gtw_out[i].x for i in range(period-begin_time)],
            't_gtw_in':[t_gtw_in[i].x for i in range(period-begin_time)],
            't_b':[t_b[i].x for i in range(period-begin_time)],
            't_ht':[t_ht[i].x for i in range(period-begin_time)],
            't_ht_l':[t_ht_l[i].x for i in range(period-begin_time)],
            't_de':[t_de[i].x for i in range(period-begin_time)],
            't_de_l':[t_de_l[i].x for i in range(period-begin_time)],
            'soc_b':[soc_b[i].x for i in range(period-begin_time)],
            'soc_b_l':[soc_b_l[i].x for i in range(period-begin_time)],
            'k_b':[k_b for i in range(period-begin_time)],
            'k_eb':[k_eb for i in range(period-begin_time)],
            'k_fc_g':[k_fc_g for i in range(period-begin_time)],
            'k_fc_p':[k_fc_p for i in range(period-begin_time)],
            # 'p_el':[p_el[i].x for i in range(period-begin_time)],
        }
        z_file={
            # 'z_a':[z_a[i].x for i in range(period-begin_time)],
            # 'z_b':[z_b[i].x for i in range(period-begin_time)],
            # 'z_c':[z_c[i].x for i in range(period-begin_time)],

            # 'z_d':[z_d[i].x for i in range(period-begin_time)],
            # 'z_e':[z_e[i].x for i in range(period-begin_time)],
            'z_b':[z_b[i] for i in range(period-begin_time)],
            'z_ht_de':[z_ht_de[i] for i in range(period-begin_time)],
            'z_hp':[z_hp[i] for i in range(period-begin_time)],
        }
        model_SAObj={
            
        }
        var_SALBUB={
            
            'p_eb_UP':[p_eb[i].SALBUP for i in range(period-begin_time)],
            'p_eb':[p_eb[i].x for i in range(period-begin_time)],
            'p_eb_LOW':[p_eb[i].SAUBLow for i in range(period-begin_time)],
            'g_eb_UP':[g_eb[i].SALBUP for i in range(period-begin_time)],
            'g_eb':[g_eb[i].x for i in range(period-begin_time)],
            'g_eb_LOW':[g_eb[i].SAUBLow for i in range(period-begin_time)],
            'p_fc_UP':[p_fc[i].SALBUP for i in range(period-begin_time)],
            'p_fc':[p_fc[i].x for i in range(period-begin_time)],
            'p_fc_LOW':[p_fc[i].SAUBLow for i in range(period-begin_time)],
            'g_fc_UP':[g_fc[i].SALBUP for i in range(period-begin_time)],
            'g_fc':[g_fc[i].x for i in range(period-begin_time)],
            'g_fc_LOW':[g_fc[i].SAUBLow for i in range(period-begin_time)],
            'p_b_UP':[p_b[i].SALBUP-storageM for i in range(period-begin_time)],
            'p_b':[p_b[i].x-storageM for i in range(period-begin_time)],
            'p_b_LOW':[p_b[i].SAUBLow-storageM for i in range(period-begin_time)],
            'p_pv_UP':[p_pv[i].SALBUP for i in range(period-begin_time)],
            'p_pv':[p_pv[i].x for i in range(period-begin_time)],
            'p_pv_LOW':[p_pv[i].SAUBLow for i in range(period-begin_time)],

            'g_hp_UP':[g_hp[i].SALBUP for i in range(period-begin_time)],
            'g_hp':[g_hp[i].x for i in range(period-begin_time)],
            'g_hp_LOW':[g_hp[i].SAUBLow for i in range(period-begin_time)],
            't_ht_l_UP':[t_ht_l[i].SALBUP for i in range(period-begin_time)],
            't_ht_l':[t_ht_l[i].x for i in range(period-begin_time)],
            't_ht_l_LOW':[t_ht_l[i].SAUBLow for i in range(period-begin_time)],
            't_de_l_UP':[t_de_l[i].SALBUP for i in range(period-begin_time)],
            't_de_l':[t_de_l[i].x for i in range(period-begin_time)],
            't_de_l_LOW':[t_de_l[i].SAUBLow for i in range(period-begin_time)],
            'soc_b_l_UP':[soc_b_l[i].SALBUP for i in range(period-begin_time)],
            'soc_b_l':[soc_b_l[i].x for i in range(period-begin_time)],
            'soc_b_l_LOW':[soc_b_l[i].SAUBLow for i in range(period-begin_time)],
            'h_fc_UP':[h_fc[i].SALBUP for i in range(period-begin_time)],
            'h_fc':[h_fc[i].x for i in range(period-begin_time)],
            'h_fc_LOW':[h_fc[i].SAUBLow for i in range(period-begin_time)],
            
        }
        constraint_SARHS={
            'g_balance_SA_RHSUP':[g_balance[i].SARHSUP for i in range(period-begin_time)],
            'g_balance_RHS':[g_balance[i].RHS for i in range(period-begin_time)],
            'g_balance_SA_RHSLOW':[g_balance[i].SARHSLow for i in range(period-begin_time)],
            'p_balance_SA_RHSUP':[p_balance[i].SARHSUP for i in range(period-begin_time)],
            'p_balance_RHS':[p_balance[i].RHS for i in range(period-begin_time)],
            'p_balance_SA_RHSLOW':[p_balance[i].SARHSLow for i in range(period-begin_time)],
            # 'p_pv_rhs':[p_pv_rhs[i] for i in range(period-begin_time)],
            'p_pv_rhs_SA_RHSUP':[p_pv_rhs[i].SARHSUP for i in range(period-begin_time)],
            'p_pv_rhs':[p_pv_rhs[i].RHS for i in range(period-begin_time)],
            'p_pv_rhs_SA_RHSLOW':[p_pv_rhs[i].SARHSLow for i in range(period-begin_time)],

            'g_load_UP':[g_balance[i].SARHSUP-g_balance[i].RHS+g_load[i] for i in range(period-begin_time)],
            'g_load':[g_balance[i].RHS-g_balance[i].RHS+g_load[i] for i in range(period-begin_time)],
            'g_load_LOW':[g_balance[i].SARHSLow -g_balance[i].RHS+g_load[i]for i in range(period-begin_time)],
            'p_load_UP':[p_balance[i].SARHSUP-p_balance[i].RHS+p_load[i] for i in range(period-begin_time)],
            'p_load':[p_balance[i].RHS-p_balance[i].RHS+p_load[i] for i in range(period-begin_time)],
            'p_load_LOW':[p_balance[i].SARHSLow-p_balance[i].RHS+p_load[i] for i in range(period-begin_time)],
        }
        judge_dict={
            'begin_time':begin_time,
            'ghp_has_open':[ghp_has_open+sum(z_hp[:i]) for i in range(period-begin_time)],
            'g_load_UP':[g_balance[i].SARHSUP-g_balance[i].RHS+g_load[i] for i in range(period-begin_time)],
            'g_load':[g_balance[i].RHS-g_balance[i].RHS+g_load[i] for i in range(period-begin_time)],
            'g_load_LOW':[g_balance[i].SARHSLow -g_balance[i].RHS+g_load[i]for i in range(period-begin_time)],
            'p_load_UP':[p_balance[i].SARHSUP-p_balance[i].RHS+p_load[i] for i in range(period-begin_time)],
            'p_load':[p_balance[i].RHS-p_balance[i].RHS+p_load[i] for i in range(period-begin_time)],
            'p_load_LOW':[p_balance[i].SARHSLow-p_balance[i].RHS+p_load[i] for i in range(period-begin_time)],
            'k_eb_UP':[10000 if p_eb[i].x==0 else g_eb[i].SALBUP/p_eb[i].x for i in range(period-begin_time)],
            'k_eb':[k_eb if p_eb[i].x==0 else g_eb[i].x/p_eb[i].x for i in range(period-begin_time)],
            'k_eb_LOW':[0 if p_eb[i].x==0 else g_eb[i].SAUBLow/p_eb[i].x for i in range(period-begin_time)],
            # 'g_eb_UP':[g_eb[i].SALBUP for i in range(period-begin_time)],
            # 'g_eb':[g_eb[i].x for i in range(period-begin_time)],
            # 'g_eb_LOW':[g_eb[i].SAUBLow for i in range(period-begin_time)],
            'k_fc_p_UP':[10000 if h_fc[i].x==0 else p_fc[i].SALBUP/h_fc[i].x for i in range(period-begin_time)],
            'k_fc_p':[k_fc_p if h_fc[i].x==0 else p_fc[i].x/h_fc[i].x for i in range(period-begin_time)],
            'k_fc_p_LOW':[0 if h_fc[i].x==0 else p_fc[i].SAUBLow/h_fc[i].x for i in range(period-begin_time)],
            'k_fc_g_UP':[10000 if h_fc[i].x==0 else g_fc[i].SALBUP/h_fc[i].x for i in range(period-begin_time)],
            'k_fc_g':[k_fc_g if h_fc[i].x==0 else g_fc[i].x/h_fc[i].x for i in range(period-begin_time)],
            'k_fc_g_LOW':[0 if h_fc[i].x==0 else g_fc[i].SAUBLow/h_fc[i].x for i in range(period-begin_time)],
            
            'p_pv_UP':[p_pv[i].SALBUP for i in range(period-begin_time)],
            'p_pv':[p_pv[i].x for i in range(period-begin_time)],
            'p_pv_LOW':[p_pv[i].SAUBLow for i in range(period-begin_time)],
            't_ht_l_UP':[t_ht_l[i].SALBUP for i in range(period-begin_time)],
            't_ht_l':[t_ht_l[i].x for i in range(period-begin_time)],
            't_ht_l_LOW':[t_ht_l[i].SAUBLow for i in range(period-begin_time)],
            't_de_l_UP':[t_de_l[i].SALBUP for i in range(period-begin_time)],
            't_de_l':[t_de_l[i].x for i in range(period-begin_time)],
            't_de_l_LOW':[t_de_l[i].SAUBLow for i in range(period-begin_time)],
            'soc_b_l_UP':[soc_b_l[i].SALBUP for i in range(period-begin_time)],
            'soc_b_l':[soc_b_l[i].x for i in range(period-begin_time)],
            'soc_b_l_LOW':[soc_b_l[i].SAUBLow for i in range(period-begin_time)],
            'k_b_UP':[10000 if (soc_b[i].x-soc_b_l[i].x)==0 else min(p_b[i].SALBUP/((soc_b[i].x-soc_b_l[i].x)+0.001),(soc_b[i].x-soc_b_l[i].x)/(p_b[i].SALBUP+0.001)) for i in range(period-begin_time)],
            'k_b':[k_b if (soc_b[i].x-soc_b_l[i].x)==0 else min(p_b[i].SAUBLow/(soc_b[i].x-soc_b_l[i].x+0.001),(soc_b[i].x-soc_b_l[i].x)/(p_b[i].SALBUP+0.001)) for i in range(period-begin_time)],
            'k_b_LOW':[0 if (soc_b[i].x-soc_b_l[i].x)==0 else min(p_b[i].SAUBLow/(soc_b[i].x-soc_b_l[i].x+0.001),(soc_b[i].x-soc_b_l[i].x)/(p_b[i].SALBUP+0.001)) for i in range(period-begin_time)],
        }
    # dict_plot = {
    #     # 'hour':[i+1 for i in range(period-begin_time)],
    #     # # operational day cost
    #     # 'opex_without_opt':[h_pur[i].x*hydrogen_price+max(0,p_load[i]-p_pv[i].x)*lambda_ele_in[i] for i in range(period-begin_time)],# 未经优化的运行成本

    #     # #ele
    #     # 'p_fc':[p_fc[i].x for i in range(period-begin_time)],#燃料电池

    #     # 'p_hp':[z_hp[i].x for i in range(period-begin_time)],#热泵
    #     # 'p_eb':[p_eb[i].x for i in range(period-begin_time)],#电锅炉
    #     # # 'p_el':[p_el[i].x for i in range(period-begin_time)],
    #     # #hydrogen
    #     # # 'h_hst':[h_sto[i].x for i in range(period-begin_time)],
    #     # #thermal
    #     # 't_ht':[t_ht[i].x for i in range(period-begin_time)],  
    # }
    return dict_control,z_file,model_SAObj,var_SALBUB,constraint_SARHS,judge_dict




if __name__ == '__main__':
    OptimizationDay()


# period = len(g_de)
# # Create a new model
# m = gp.Model("bilinear")

# # Create variables
# ce_h = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="ce_h")

# m_ht = m.addVar(vtype=GRB.CONTINUOUS, lb=10, name="m_ht") # capacity of hot water tank

# t_ht = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ht{t}") for t in range(period-begin_time)] # temperature of hot water tank

# t_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_fc{t}") for t in range(begin_time,period)] # outlet temperature of fuel cells cooling circuits

# g_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc{t}") for t in range(begin_time,period)] # heat generated by fuel cells

# p_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_fc{t}") for t in range(begin_time,period)]

# fc_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="fc_max") # rated heat power of fuel cells

# el_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="el_max") # rated heat power of fuel cells

# t_de = [m.addVar(vtype=GRB.CONTINUOUS, lb=0,name=f"t_de{t}") for t in range(begin_time,period)] # outlet temparature of heat supply circuits

# h_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_fc{t}") for t in range(begin_time,period)] # hydrogen used in fuel cells

# m_fc = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_fc") # fuel cells water

# m_el = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_el") # fuel cells water


# g_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_el{t}") for t in range(begin_time,period)] # heat generated by Electrolyzer

# h_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_el{t}") for t in range(begin_time,period)] # hydrogen generated by electrolyzer

# p_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_el{t}") for t in range(begin_time,period)] # power consumption by electrolyzer

# t_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_el{t}") for t in range(begin_time,period)] # outlet temperature of electrolyzer cooling circuits

# h_sto = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_sto{t}") for t in range(begin_time,period)] # hydrogen storage

# h_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_pur{t}") for t in range(begin_time,period)] # hydrogen purchase

# p_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pur{t}") for t in range(begin_time,period)] # power purchase

# p_sol = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_sol{t}") for t in range(begin_time,period)] # power purchase

# area_pv = m.addVar(vtype=GRB.CONTINUOUS, lb=0, ub = 1000, name=f"area_pv")

# p_pump = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump{t}") for t in range(begin_time,period)] 

# hst = m.addVar(vtype=GRB.CONTINUOUS, lb=0, ub = 1000, name=f"hst")

# #m.addConstr(m_el+m_fc <= 0.001*m_ht)
# for i in range(int(period/24)-1):
#     m.addConstr(t_ht[i*24+24] == t_ht[24*i])
# m.addConstr(t_ht[-1] == t_ht[0])
# #m.addConstr(h_sto[0] == 0)
# m.addConstr(h_sto[-1] == h_sto[0])
# for i in range(period - 1):
#     m.addConstr(m_ht * (t_ht[i + 1] - t_ht[i]) == 
#         m_fc * (t_fc[i] - t_ht[i]) + m_el * (t_el[i] - t_ht[i]) - m_de[i] * (t_ht[i] - t_de[i]))
#     m.addConstr(h_sto[i+1] - h_sto[i] == h_pur[i] + h_el[i] - h_fc[i])
    
# m.addConstr(m_ht * (t_ht[0] - t_ht[i]) == m_fc * (t_fc[i] - t_ht[i]) + m_el * (t_el[i] - t_ht[i]) - m_de[i] * (t_ht[i] - t_de[i]))
# m.addConstr(h_sto[0] - h_sto[-1] == h_pur[-1] + h_el[-1] - h_fc[-1])
# m.addConstr(t_ht[0] == 55)
# for i in range(begin_time,period):
#     m.addConstr(t_de[i] >= 40)
#     m.addConstr(p_eb[i] + p_el[i] + p_sol[i] + p_pump[i] + p_load[i]== p_pur[i] + p_fc[i] + k_pv*area_pv*r[i])
#     m.addConstr(g_fc[i] <= 18 * h_fc[i])
#     m.addConstr(p_pump[i] == 3.5/1000 * (m_fc+m_de[i]+m_el))#热需求虽然低，水泵耗电高。
#     m.addConstr(p_fc[i] <= 18 * h_fc[i])#氢燃烧产电
#     m.addConstr(h_el[i] <= k_el * p_el[i])
#     m.addConstr(g_el[i] <= 0.2017*p_el[i])
#     m.addConstr(g_fc[i] == c_kWh * m_fc * (t_fc[i] - t_ht[i]))
#     m.addConstr(g_el[i] == c_kWh * m_el * (t_el[i] - t_ht[i]))
#     m.addConstr(t_fc[i] <= 75)
#     m.addConstr(t_el[i] <= 75)
#     m.addConstr(h_sto[i]<=hst)
#     m.addConstr(h_el[i]<=hst)
#     #m.addConstr(t_ht[i] >= 50)
#     m.addConstr(p_fc[i] <= fc_max)
#     m.addConstr(p_el[i] <= el_max)
#     m.addConstr(g_de[i] == c_kWh * m_de[i] * (t_ht[i] - t_de[i]))
#     #m.addConstr(m_fc <= m_ht)
# # m.addConstr(m_fc[i] == m_ht/3)
# # m.addConstr(m_ht >= 4200*100)
# # m.addConstr(t_ht[i] <= 80)#强化条件


# # m.setObjective( crf_pv * cost_pv*area_pv+ crf_el*cost_el*el_max
# #     +crf_hst * hst*cost_hst +crf_water* cost_water_hot*m_ht + crf_fc *cost_fc * fc_max + lambda_h*gp.quicksum(h_pur)*365+ 
# #     365*gp.quicksum([p_pur[i]*lambda_ele_in[i] for i in range(24)])-365*gp.quicksum(p_sol)*lambda_ele_out , GRB.MINIMIZE)
# m.setObjective( crf_pv * cost_pv*area_pv+ crf_el*cost_el*el_max
#     +crf_hst * hst*cost_hst +crf_water* cost_water_hot*m_ht + crf_fc *cost_fc * fc_max + lambda_h*gp.quicksum(h_pur)*365/7+ 
#     gp.quicksum([p_pur[i]*lambda_ele_in[i] for i in range(begin_time,period)])*365/7-gp.quicksum(p_sol)*lambda_ele_out*365/7, GRB.MINIMIZE)
# #-gp.quicksum(p_sol)*lambda_ele_out 
# # First optimize() call will fail - need to set NonConvex to 2
# m.params.NonConvex = 2
# m.params.MIPGap = 0.05
# # m.optimize()
# #m.computeIIS()
# try:
#     m.optimize()
# except gp.GurobiError:
#     print("Optimize failed due to non-convexity")

# # Solve bilinear model
# # m.params.NonConvex = 2
# # m.optimize()

# #m.printAttr('x')
# m.write('sol_winter.mst')
# # Constrain 'x' to be integral and solve again
# # x.vType = GRB.INTEGER
# # m.optimize()

# # m.printAttr('x')

# wb = xlwt.Workbook()
# result = wb.add_sheet('result')
# alpha_ele = 1.01
# alpha_heat = 0.351
# ce_c = np.sum(p_load)*alpha_ele + np.sum(g_de)*alpha_heat
# #c_cer == lambda_carbon*(ce_c - ce_h)
# p_pur_tmp = m.getAttr('x', p_pur)
# p_sol_tmp = m.getAttr('x', p_sol)
# ce_h_1 = np.sum(p_pur_tmp)*alpha_ele - np.sum(p_sol_tmp)*alpha_ele


# item1 = ['m_ht','m_fc','m_el','fc_max','el_max']
# item2 = [g_el,g_fc,p_el,p_fc,p_pur,p_pump,p_sol,t_ht,t_el,h_el,h_fc,t_fc,t_de,h_sto,h_pur]
# a_pv = m.getVarByName('area_pv').getAttr('x')
# item3 = [[k_pv*a_pv*r[i] for i in range(len(r))],p_load,g_de]
# item3_name = ['p_pv','p_load','g_de']
# print(m.getAttr('x', p_el))
# for i in range(len(item1)):
#     result.write(0,i,item1[i])
#     result.write(1,i,m.getVarByName(item1[i]).getAttr('x'))
# for i in range(len(item2)):
#     tmp = m.getAttr('x', item2[i])
#     result.write(0,i+len(item1),item2[i][0].VarName[:-1])
#     for j in range(len(tmp)):
#         result.write(j+1,i+len(item1),tmp[j])

# for i in range(3):
#     tmp = item3[i]
#     result.write(0,i+len(item1)+len(item2),item3_name[i])
#     for j in range(len(tmp)):
#         result.write(j+1,i+len(item1)+len(item2),tmp[j])

# t_ht = m.getAttr('x', t_ht)
# m_ht = m.getVarByName('m_ht').getAttr('x')
# res = []
# for i in range(len(t_ht)-1):
#     res.append(c*m_ht*(t_ht[i+1] - t_ht[i])/3.6/1000000)
# res.append(c*m_ht*(t_ht[0]-t_ht[-1])/3.6/1000000)
# result.write(0,3+len(item1)+len(item2),'g_ht')
# for j in range(len(res)):
#     result.write(j+1,3+len(item1)+len(item2),res[j])
# result.write(0,4+len(item1)+len(item2),'cer')
# result.write(1,4+len(item1)+len(item2),(ce_c - ce_h_1))

# wb.save("sol_season_12day_729.xls")
# #print(m.getJSONSolution())







