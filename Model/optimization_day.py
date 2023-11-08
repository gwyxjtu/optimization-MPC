'''
Author: gwyxjtu
Date: 2022-05-31 21:46:00
LastEditors: guo_MateBookPro 867718012@qq.com
LastEditTime: 2023-11-06 09:26:30
FilePath: /optimization/Model/optimization_day.py
Description: 人一生会遇到约2920万人,两个人相爱的概率是0.000049,所以你不爱我,我不怪你.

Copyright (c) 2022 by gwyxjtu 867718012@qq.com, All Rights Reserved. 
'''
#!/usr/bin/env python3.7


import gurobipy as gp
from gurobipy import GRB
import numpy as np
from pandas import period_range
import xlwt
import random

from cpeslog.log_code import _logging

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

def OptimizationDay(parameter_json,load_json,begin_time,time_scale,storage_begin_json,storage_end_json):
    """计算优化问题，时间尺度不定，输入包括末时刻储能。

    Args:
        parameter_json (_type_): 输入config文件中读取的参数
        load_json (_type_): 预测的负荷向量
        time_scale (_type_): 计算的小时
        storage_begin_json (_type_): 初始端储能状态
        storage_end_json (_type_): 末端储能状态
    """
    # 一些常熟参数
    c = 4200/3.6/1000000 #kwh/(kg*℃)
    period = time_scale

    # 初始化设备效率参数
    try:
        k_fc_p = parameter_json['device']['fc']['eta_fc_p']*parameter_json['device']['fc']['theta_ex']
        k_fc_g = parameter_json['device']['fc']['eta_fc_g']*parameter_json['device']['fc']['theta_ex']
        # k_el = parameter_json['device']['el']['beta_el']
        k_eb = parameter_json['device']['eb']['beta_eb']
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
        k_gtw_fluid=877/898*m_gtw/400-0.0297
        p_fc_max = parameter_json['device']['fc']['power_max']
        # p_el_max = parameter_json['device']['el']['power_max']
        p_eb_max = parameter_json['device']['eb']['power_max']
        # a_pv = parameter_json['device']['pv']['area_max']
        # hst_max = parameter_json['device']['hst']['sto_max']
        p_hp_max = parameter_json['device']['hp']['power_max']
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
        # lambda_ele_out = parameter_json['price']['power_sale']
        hydrogen_price = parameter_json['price']['hydrogen_price']
        p_demand_price=parameter_json['price']['demand_electricity_price']
    except BaseException as E:
        _logging.error('读取config.json中价格参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化负荷
    try:
        p_load = list(load_json['ele_load'])
        g_load = list(load_json['g_load'])
        # q_load = list(load_json['q_load'])
        pv_generation = list(load_json['pv_generation'])
        t_tem = list(load_json['ambient_temperature']) #读环境温度
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


        # hydrogen_bottle_max_final = storage_end_json['hydrogen_bottle_max'][begin_time+time_scale] #气瓶
        # hst_kg_final = storage_end_json['hst_kg'][begin_time+time_scale]  # 缓冲罐剩余氢气
        t_ht_final = storage_end_json['t_ht'][begin_time+time_scale]  # 热水罐
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
    z_a=[m.addVar(vtype=GRB.BINARY,name=f"z_a{t}")for t in range(period)]#工况a,水箱供给末端
    z_b=[m.addVar(vtype=GRB.BINARY,name=f"z_b{t}")for t in range(period)]#工况b,锅炉给水箱蓄
    z_c=[m.addVar(vtype=GRB.BINARY,name=f"z_c{t}")for t in range(period)]#工况c,燃料电池给水箱蓄
    z_d=[m.addVar(vtype=GRB.BINARY,name=f"z_d{t}")for t in range(period)]#工况d,热泵给水箱蓄
    z_e=[m.addVar(vtype=GRB.BINARY,name=f"z_e{t}")for t in range(period)]#工况e,热泵和燃料电池一起给水箱蓄

    #opex = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="opex")
    opex = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="opex_"+str(i)) for i in range(period)]
    t_ht = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ht{t}") for t in range(period)] # temperature of hot water tank
    t_ht_l = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ht_l{t}") for t in range(period)] # temperature of hot water tank in last time
    g_ht=[m.addVar(vtype=GRB.CONTINUOUS, lb=-10000, name=f"g_ht{t}") for t in range(period)]#水箱给末端的供热量
    # t_ct = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ct{t}") for t in range(period)] # temperature of hot water tank
    # t_ct_l = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ct_l{t}") for t in range(period)] # temperature of hot water tank in last time
    t_de=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_de{t}") for t in range(period)]# average temperature of demand
    t_de_l=[m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_de_l{t}") for t in range(period)]# average temperature of demand in last time
    z_ht_de=[m.addVar(vtype=GRB.BINARY,name=f"z_ht_de{t}")for t in range(period)]# 判断ht能不能给末端供的01量
    
    g_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc{t}") for t in range(period)] # heat generated by fuel cells
    p_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_fc{t}") for t in range(period)]
    h_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_fc{t}") for t in range(period)] # hydrogen used in fuel cells

    p_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_hp{t}") for t in range(period)] # power consumption of heat pumps
    g_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_hp{t}") for t in range(period)] # heat generated by heat pumps
    cop_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"cop_hp{t}") for t in range(period)]
    t_gtw_out = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_gtw_out{t}") for t in range(period)]
    g_gtw_l = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_gtw_l{t}") for t in range(period)]
    g_gtw = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_gtw{t}") for t in range(period)]
    t_gtw_in = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_hp{t}") for t in range(period)]
    t_b = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_b{t}") for t in range(period)]
    
    # q_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"q_hp{t}") for t in range(period)] # heat generated by heat pumps

    # h_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_el{t}") for t in range(period)] # hydrogen generated by electrolyzer
    # p_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_el{t}") for t in range(period)] # power consumption by electrolyzer

    # h_sto = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_sto{t}") for t in range(period)] # hydrogen storage
    # h_sto_l = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_sto_l{t}") for t in range(period)] # last time hydrogen storage
    h_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_pur{t}") for t in range(period)] # hydrogen purchase

    p_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pur{t}") for t in range(period)] # power purchase
    p_demand_max=m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_demand_max")

    # p_pump = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump{t}") for t in range(period)] 
    p_eb = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_eb{t}") for t in range(period)] # power consumption by ele boiler
    g_eb = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_eb{t}") for t in range(period)] # heat generated by ele boiler

    p_pv = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pv{t}") for t in range(period)] # power generate by PV





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
    m.addConstr(t_ht_l[0] == t_ht_start)
    m.addConstr(t_de_l[0] == t_de_start)
    m.addConstr(g_gtw_l[0] == 0)
    # m.addConstr(t_ct_l[0] == t_ct_start)
    # m.addConstr(h_sto_l[0] == hst_kg_start)
    m.addConstr(t_ht[-1] >= t_ht_final)

    m.addConstrs(t_ht[i] == t_ht_l[i+1] for i in range(period-1))
    # m.addConstrs(t_ct[i] == t_ct_l[i+1] for i in range(period-1))
    # m.addConstrs(h_sto[i] == h_sto_l[i+1] for i in range(period-1))
    m.addConstrs(t_de[i] == t_de_l[i+1] for i in range(period-1))
    m.addConstrs(g_gtw[i] == g_gtw_l[i+1] for i in range(period-1))

    for i in range(period):
        # 能量平衡
        # m.addConstr(p_fc[i] + p_pur[i] + p_pv[i] == p_el[i] + p_eb[i] + p_hp[i]  + p_pump[i] + p_load[i])
        m.addConstr(p_fc[i] + p_pur[i] + p_pv[i] == p_eb[i] + p_hp[i] + p_load[i])
        #m.addConstr(c*m_ht*(t_ht[i] - t_ht_l[i] - ht_loss * (t_ht_l[i] - t_ht_wetbulb)) + g_load[i] == g_fc[i] + g_hp[i] + g_eb[i])
        m.addConstr(g_load[i] == g_fc[i] + g_hp[i] + g_eb[i] + g_ht[i])

        #m.addConstr(c*m_ct*(t_ct[i] - t_ct_l[i] - ct_loss * (t_ct_l[i] - t_ct_wetbulb)) + q_hp[i] == q_load[i])
        # m.addConstr(c*m_ct*(t_ct[i] - t_ct_l[i]) + q_hp[i] == q_load[i])

        # m.addConstr(h_sto[i] - h_sto_l[i] == h_pur[i] + h_el[i] - h_fc[i])
        
        #最大需量
        m.addConstr(p_demand_max>=p_pur[i])



        # 工况约束
        m.addConstr(z_a[i]*g_ht[i]>=0)
        m.addConstr(g_ht[i]+z_b[i]*g_eb[i]+z_c[i]*g_fc[i]+z_d[i]*g_hp[i]+z_e[i]*(g_fc[i]+g_hp[i])==0)
        m.addConstr(z_a[i]+z_b[i]+z_c[i]+z_d[i]+z_e[i]<=1)

        #给末端供热的约束
        m.addConstr(c*m_de*(t_de[i]-t_de_l[i]) == g_ht[i]+g_eb[i]+g_fc[i]+g_hp[i]-g_load[i]-de_loss*(t_de_l[i]-t_tem[i]))





    # 每一时段约束
    for i in range(period):
        # 上下限约束
        # m.addConstr(t_ht[i] >= t_ht_min)
        m.addConstr(t_ht[i] <= t_ht_max)
        # m.addConstr(t_ct[i] >= t_ct_min)
        # m.addConstr(t_ct[i] <= t_ct_max)
        m.addConstr(t_de[i] >= t_de_min)
        m.addConstr(t_de[i] <= t_de_max)
        m.addConstr(p_fc[i] <= p_fc_max)
        # m.addConstr(p_el[i] <= p_el_max)
        m.addConstr(p_eb[i] <= p_eb_max)
        m.addConstr(p_hp[i] <= p_hp_max)

        # 能量平衡

        # 设备约束
        ## fc
        # m.addConstr(p_fc[i] <= p_fc_max)
        m.addConstr(p_fc[i] == k_fc_p * h_fc[i])
        m.addConstr(g_fc[i] == k_fc_g * h_fc[i])
        ## hp
        # m.addConstr(p_hp[i] <= p_hp_max)
        # m.addConstr(q_hp[i] == k_hp_q * p_hp[i])
        m.addConstr(g_hp[i] == cop_hp[i] * p_hp[i])
        m.addConstr(cop_hp[i]==4.8781+0.1209*t_gtw_out[i])
        m.addConstr(g_gtw[i]==g_hp[i]-p_hp[i])
        m.addConstr(g_gtw[i]==c*m_gtw*(t_gtw_out[i]-t_gtw_in[i]))
        m.addConstr(t_gtw_out[i]==k_gtw_fluid*(t_gtw_out[i]-t_b[i])+t_b[i])
        m.addConstr(t_b[i]==10-(1000/(2*np.pi*2.07*200*192))*gp.quicksum((g_gtw[j]-g_gtw_l[j])*g_func[i-j] for j in range(len(i+1))))



        ## el
        # m.addConstr(p_el[i] <= p_el_max)
        # m.addConstr(h_el[i] == k_el * p_el[i])
        ## eb
        m.addConstr(p_eb[i] <= p_eb_max)
        m.addConstr(g_eb[i] == k_eb * p_eb[i])
        ## pump
        #m.addConstr(p_pump[i] == k_pump * mass_flow[i])
        ## pv
        # m.addConstr(p_pv[i] <= solar[i] * a_pv * k_pv)
        m.addConstr(p_pv[i] == pv_generation[i] )

        ## ht
        ### ht温度变化
        m.addConstr(c*m_ht*(t_ht[i]-t_ht_l[i])==-g_ht[i]-ht_loss*(t_ht_l[i]-t_tem[i]))
        ### ht供热温度约束
        m.addConstr(t_ht_l[i]-t_de_l[i]+tem_diff/2>=100*(z_ht_de[i]-1))
        m.addConstr(g_ht[i]<=c*m_de*(t_ht_l[i]-t_de_l[i])*z_ht_de[i])

        ## opex 
        m.addConstr(opex[i] == hydrogen_price * h_pur[i] + p_pur[i] * lambda_ele_in[i]+p_demand_price*p_demand_max)
    # set objective
    
    m.setObjective(gp.quicksum(opex), GRB.MINIMIZE)
    m.params.MIPGap = 0.01
    m.Params.LogFile = "testlog.log"

    try:
        m.optimize()
        _logging.info("success optimize")
    except gp.GurobiError as e:
        print("Optimize failed due to non-convexity")
        _logging.error(e)
    if m.status == GRB.INFEASIBLE or m.status == 4:
        print('Model is infeasible')
        m.computeIIS()
        m.write('data_optimize/优化控制/Temp/model.ilp')
        print("Irreducible inconsistent subsystem is written to file 'model.ilp'")
        exit(0)

    # 计算一些参数
    # opex_without_opt = [lambda_ele_in[i]*(p_load[i]+q_load[i]/k_hp_q+g_load[i]/k_eb) for i in range(period)]
    dict_control = {# 负荷
        # 'time':begin_time,
        # thermal binary
        # 'b_hp':[1 if p_hp[i].x > 0 else 0 for i in range(period)],
        # 'b_eb':[1 if p_eb[i].x > 0 else 0 for i in range(period)],
        # # -1代表储能，1代表供能
        # 'b_ht':[-1 if t_ht[i].x > t_ht_l[i].x else 1 if t_ht[i].x > t_ht_l[i].x else 0  for i in range(period)],
        # # 'b_ct':[1 if t_ct[i].x > t_ct_l[i].x else -1 if t_ct[i].x > t_ht_l[i].x else 0  for i in range(period)],
        # 'b_fc':[1 if p_fc[i].x > 0 else 0 for i in range(period)],

        # ele
        'opex':gp.quicksum(opex),
        'p_demand_max':p_demand_max,
        'operation_mode':[z_a[i].x*1+z_b[i].x*2+z_c[i].x*3+z_d[i].x*4+z_e[i].x*5 for i in range(period)],
        'p_eb':[p_eb[i].x for i in range(period)],
        'p_fc':[p_fc[i].x for i in range(period)],
        'p_pv':[p_pv[i].x for i in range(period)],
        'p_hp':[p_hp[i].x for i in range(period)],
        'p_pur':[p_pur[i].x for i in range(period)],
        'p_load':[p_load[i].x for i in range(period)],
        'g_fc':[g_fc[i].x for i in range(period)],
        'g_eb':[g_eb[i].x for i in range(period)],
        'g_hp':[g_hp[i].x for i in range(period)],
        'g_ht':[g_ht[i].x for i in range(period)],
        'g_load':[g_load[i].x for i in range(period)],
        'h_pur':[h_pur[i].x for i in range(period)],
        'g_gtw':[g_gtw[i].x for i in range(period)],
        't_gtw_out':[t_gtw_out[i].x for i in range(period)],
        't_gtw_in':[t_gtw_in[i].x for i in range(period)],
        't_ht':[t_ht[i].x for i in range(period)],
        't_de':[t_de[i].x for i in range(period)],
        # 'p_el':[p_el[i].x for i in range(period)],
    }
    # dict_control = {# 负荷
    #     'time':[begin_time+i for i in range(period)],
    #     # 运行工况输出
    #     'status':[15 for i in range(period)], #设备运行别问，问就是全开
    # }
    # dict_plot = {
    #     # operational day cost
    #     'opex_without_system':sum(opex_without_opt),#没有能源站的运行成本，负荷直接加
    #     'opex_without_opt':sum([h_pur[i].x for i in range(period)])*hydrogen_price + sum([max(0,p_load[i]-p_pv[i].x)*lambda_ele_in[i] for i in range(period)]),# 未经优化的运行成本
    #     'opex':sum([opex[i].x for i in range(period)]),# 经优化的运行成本
    #     'op_save_part':sum([opex[i].x for i in range(period)])/sum(opex_without_opt),

    #     # 综合能效
    #     'renewable_energy_part':sum([p_pv[i].x + p_fc[i].x for i in range(period)])/sum([p_pv[i].x + p_fc[i].x + p_pur[i].x for i in range(period)]), #可再生能源占比
    #     'efficiency':sum(p_load+q_load+g_load)/sum([p_pv[i].x + 33.3 * h_fc[i].x for i in range(period)]),

    #     #ele
    #     'p_pur':[p_pur[i].x for i in range(period)],#电网下电
    #     'p_pv':[p_pv[i].x for i in range(period)],#光伏
    #     'p_fc':[p_fc[i].x for i in range(period)],#燃料电池

    #     'p_hp':[p_hp[i].x for i in range(period)],#热泵
    #     'p_eb':[p_eb[i].x for i in range(period)],#电锅炉
    #     'p_pump':[p_pump[i].x for i in range(period)],#水泵
    #     'p_el':[p_el[i].x for i in range(period)],
    #     'p_load':p_load,
    #     #hydrogen
    #     'h_hst':[h_sto[i].x for i in range(period)],
    #     'h_sto_l':[h_sto_l[i].x for i in range(period)],
    #     'h_pur':[h_pur[i].x for i in range(period)],
    #     'h_el':[h_el[i].x for i in range(period)],
    #     'h_fc':[h_fc[i].x for i in range(period)],
    #     'h_tube':[hydrogen_bottle_max_start - sum([h_pur[i].x for i in range(j)]) for j in range(period)],
    #     #thermal
    #     't_ht':[t_ht[i].x for i in range(period)],  
    #     'g_ht':[c*m_ht*(t_ht[i].x - t_ht_l[i].x) for i in range(period)],

    #     'g_load':g_load,
    #     'g_hp':[g_hp[i].x for i in range(period)],
    #     'g_eb':[g_eb[i].x for i in range(period)],
    #     'g_fc':[g_fc[i].x for i in range(period)],

    #     # cold
    #     't_ct':[t_ct[i].x for i in range(period)],
    #     'q_ct':[c * m_ct * (t_ct[i].x - t_ct_l[i].x) for i in range(period)],
    #     'q_hp':[q_hp[i].x for i in range(period)],
    #     'q_load':q_load,
    # }
    dict_plot = {
        'hour':[i+1 for i in range(period)],
        # operational day cost
        'opex_without_opt':[h_pur[i].x*hydrogen_price+max(0,p_load[i]-p_pv[i].x)*lambda_ele_in[i] for i in range(period)],# 未经优化的运行成本

        #ele
        'p_fc':[p_fc[i].x for i in range(period)],#燃料电池

        'p_hp':[p_hp[i].x for i in range(period)],#热泵
        'p_eb':[p_eb[i].x for i in range(period)],#电锅炉
        # 'p_el':[p_el[i].x for i in range(period)],
        #hydrogen
        # 'h_hst':[h_sto[i].x for i in range(period)],
        #thermal
        't_ht':[t_ht[i].x for i in range(period)],  
    }
    return dict_control,dict_plot




if __name__ == '__main__':
    OptimizationDay()


# period = len(g_de)
# # Create a new model
# m = gp.Model("bilinear")

# # Create variables
# ce_h = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="ce_h")

# m_ht = m.addVar(vtype=GRB.CONTINUOUS, lb=10, name="m_ht") # capacity of hot water tank

# t_ht = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ht{t}") for t in range(period)] # temperature of hot water tank

# t_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_fc{t}") for t in range(period)] # outlet temperature of fuel cells cooling circuits

# g_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc{t}") for t in range(period)] # heat generated by fuel cells

# p_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_fc{t}") for t in range(period)]

# fc_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="fc_max") # rated heat power of fuel cells

# el_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="el_max") # rated heat power of fuel cells

# t_de = [m.addVar(vtype=GRB.CONTINUOUS, lb=0,name=f"t_de{t}") for t in range(period)] # outlet temparature of heat supply circuits

# h_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_fc{t}") for t in range(period)] # hydrogen used in fuel cells

# m_fc = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_fc") # fuel cells water

# m_el = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_el") # fuel cells water


# g_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_el{t}") for t in range(period)] # heat generated by Electrolyzer

# h_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_el{t}") for t in range(period)] # hydrogen generated by electrolyzer

# p_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_el{t}") for t in range(period)] # power consumption by electrolyzer

# t_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_el{t}") for t in range(period)] # outlet temperature of electrolyzer cooling circuits

# h_sto = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_sto{t}") for t in range(period)] # hydrogen storage

# h_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_pur{t}") for t in range(period)] # hydrogen purchase

# p_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pur{t}") for t in range(period)] # power purchase

# p_sol = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_sol{t}") for t in range(period)] # power purchase

# area_pv = m.addVar(vtype=GRB.CONTINUOUS, lb=0, ub = 1000, name=f"area_pv")

# p_pump = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump{t}") for t in range(period)] 

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
# for i in range(period):
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
#     gp.quicksum([p_pur[i]*lambda_ele_in[i] for i in range(period)])*365/7-gp.quicksum(p_sol)*lambda_ele_out*365/7, GRB.MINIMIZE)
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







