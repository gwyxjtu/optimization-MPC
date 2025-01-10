'''
Author: gwyxjtu
Date: 2022-06-06 20:10:39
LastEditors: yxs 572412425@qq.com
LastEditTime: 2023-12-17 10:16:12
FilePath: \设备能效计算\mx\optimization-MPC\optimization_24h.py
Description: 人一生会遇到约2920万人,两个人相爱的概率是0.000049,所以你不爱我,我不怪你.

Copyright (c) 2022 by gwyxjtu 867718012@qq.com, All Rights Reserved. 
'''
'''
                       ::
                      :;J7, :,                        ::;7:
                      ,ivYi, ,                       ;LLLFS:
                      :iv7Yi                       :7ri;j5PL
                     ,:ivYLvr                    ,ivrrirrY2X,
                     :;r@Wwz.7r:                :ivu@kexianli.
                    :iL7::,:::iiirii:ii;::::,,irvF7rvvLujL7ur
                   ri::,:,::i:iiiiiii:i:irrv177JX7rYXqZEkvv17
                ;i:, , ::::iirrririi:i:::iiir2XXvii;L8OGJr71i
              :,, ,,:   ,::ir@mingyi.irii:i:::j1jri7ZBOS7ivv,
                 ,::,    ::rv77iiiriii:iii:i::,rvLq@huhao.Li
             ,,      ,, ,:ir7ir::,:::i;ir:::i:i::rSGGYri712:
           :::  ,v7r:: ::rrv77:, ,, ,:i7rrii:::::, ir7ri7Lri
          ,     2OBBOi,iiir;r::        ,irriiii::,, ,iv7Luur:
        ,,     i78MBBi,:,:::,:,  :7FSL: ,iriii:::i::,,:rLqXv::
        :      iuMMP: :,:::,:ii;2GY7OBB0viiii:i:iii:i:::iJqL;::
       ,     ::::i   ,,,,, ::LuBBu BBBBBErii:i:i:i:i:i:i:r77ii
      ,       :       , ,,:::rruBZ1MBBqi, :,,,:::,::::::iiriri:
     ,               ,,,,::::i:  @arqiao.       ,:,, ,:::ii;i7:
    :,       rjujLYLi   ,,:::::,:::::::::,,   ,:i,:,,,,,::i:iii
    ::      BBBBBBBBB0,    ,,::: , ,:::::: ,      ,,,, ,,:::::::
    i,  ,  ,8BMMBBBBBBi     ,,:,,     ,,, , ,   , , , :,::ii::i::
    :      iZMOMOMBBM2::::::::::,,,,     ,,,,,,:,,,::::i:irr:i:::,
    i   ,,:;u0MBMOG1L:::i::::::  ,,,::,   ,,, ::::::i:i:iirii:i:i:
    :    ,iuUuuXUkFu7i:iii:i:::, :,:,: ::::::::i:i:::::iirr7iiri::
    :     :rk@Yizero.i:::::, ,:ii:::::::i:::::i::,::::iirrriiiri::,
     :      5BMBBBBBBSr:,::rv2kuii:::iii::,:i:,, , ,,:,:i@petermu.,
          , :r50EZ8MBBBBGOBBBZP7::::i::,:::::,: :,:,::i;rrririiii::
              :jujYY7LS0ujJL7r::,::i::,::::::::::::::iirirrrrrrr:ii:
           ,:  :@kevensun.:,:,,,::::i:i:::::,,::::::iir;ii;7v77;ii;i,
           ,,,     ,,:,::::::i:iiiii:i::::,, ::::iiiir@xingjief.r;7:i,
        , , ,,,:,,::::::::iiiiiiiiii:,:,:::::::::iiir;ri7vL77rrirri::
         :,, , ::::::::i:::i:::i:i::,,,,,:,::i:i:::iir;@Secbone.ii:::
'''
import copy
import json
import pprint
import pandas as pd
from cpeslog.log_code import _logging
from Model.optimization_day import OptimizationDay,to_csv

#更新i时刻的实时数据
def update_i_load_and_eff(event_table,load,input_json,sto,l):
    #负荷
    load.loc[event_table.at[l,'i'],'g_load']=event_table.at[l,'g_load']
    load.loc[event_table.at[l,'i'],'p_load']=event_table.at[l,'p_load']
    load.loc[event_table.at[l,'i'],'pv_generation']=event_table.at[l,'p_pv']
    #设备效率
    input_json['device']['fc']['k_fc_p'][event_table.at[l,'i']]=event_table.at[l,'k_fc_p']
    input_json['device']['fc']['k_fc_g'][event_table.at[l,'i']]=event_table.at[l,'k_fc_g']
    input_json['device']['eb']['k_eb'][event_table.at[l,'i']]=event_table.at[l,'k_eb']
    input_json['device']['battery']['k_b'][event_table.at[l,'i']]=event_table.at[l,'k_b']
    #初始状态
    sto.loc[event_table.at[l,'i'],'t_ht']=event_table.at[l,'t_ht_l'] #这里要的是l时刻的初始状态，也就是l-1时刻末状态
    sto.loc[event_table.at[l,'i'],'t_de']=event_table.at[l,'t_de_l']
    sto.loc[event_table.at[l,'i'],'soc_b']=event_table.at[l,'soc_b_l']
    sto.loc[event_table.at[l,'i'],'ghp_has_open']=event_table.at[l,'ghp_has_open']

#计算状态量，start：当前时刻。event_table：事件触发表。其余参数为优化得到的结果：功率，右端向量，上下限。。。
def calculate_storage_state(start,event_table,judge_dict2,dict_control2):
    #计算状态量，根据上一时刻的状态和充放功率计算储能状态，因为没有实际的事件触发的数据，只能通过这种方式得到触发时的初始状态。
    for ll in range(start+1,len(event_table)):
        last_index=event_table.at[ll-1,'i']-judge_dict2['begin_time']#上一时刻
        time_diff=event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time']#时间差

        event_table.loc[ll,'soc_b_l']=event_table.loc[ll-1,'soc_b_l']-dict_control2['p_b'][last_index]*(time_diff)*judge_dict2['k_b'][last_index] if dict_control2['p_b'][last_index]<=0 else event_table.loc[ll-1,'soc_b_l']-dict_control2['p_b'][last_index]*(time_diff)/judge_dict2['k_b'][last_index]
        event_table.loc[ll,'t_ht_l']=event_table.loc[ll-1,'t_ht_l']-dict_control2['g_ht'][last_index]*(time_diff)/(4200/3.6/1000)/input_json['device']['ht']['water_max']- input_json['device']['ht']['miu_loss']*(judge_dict2['t_ht_l'][last_index]-load['ambient_temperature'][event_table.at[ll-1,'i']])*(time_diff)/(4200/3.6/1000)
        event_table.loc[ll,'t_de_l']=event_table.loc[ll-1,'t_de_l']+(dict_control2['g_ht'][last_index]+dict_control2['g_eb'][last_index]+dict_control2['g_hp'][last_index]+dict_control2['g_fc'][last_index]-dict_control2['g_load'][last_index])*(time_diff)/(4200/3.6/1000)/input_json['device']['de']['water_max']-input_json['device']['de']['miu_loss']*(dict_control2['t_de_l'][last_index]-43)*(time_diff)/(4200/3.6/1000)
        event_table.loc[ll,'ghp_has_open']=event_table.loc[ll-1,'ghp_has_open']+z_file2['z_hp'][last_index]*(time_diff)
#保存结果，start：当前时刻。event_table：事件触发表。其余参数为优化得到的结果：功率，右端向量，上下限。。。
def store_result(start,event_table,judge_dict2,dict_control2,var_SALBUB2,constraint_SARHS2):    
    #将优化结果汇总至resultss，因为dict_control2中没有非整点的储能状态，所以写入的时候event_table放最后，这样重复的列可以直接覆盖，只保留最新的
    for ll in range(start,len(event_table)):
        for k in dict_control2.keys():
            resultss.loc[ll,k]=dict_control2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
        for k in var_SALBUB2.keys():
            resultss.loc[ll,k]=var_SALBUB2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
        for k in constraint_SARHS2.keys():
            resultss.loc[ll,k]=constraint_SARHS2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
        for k in event_table.columns[2:]:
            resultss.loc[ll,k]=event_table.loc[ll,k]



if __name__ == '__main__':

    _logging.info('start')
    time_end=24

    try:
        with open("Config/cacET/config.json", "rb") as f:
            input_json = json.load(f)
    except BaseException as E:
        _logging.error('读取config失败,错误原因为{}'.format(E))
        raise Exception
    # 读取输入excel
    try:
        load = pd.read_excel('input_720/cacET/input_720h.xls')
    except BaseException as E:
        _logging.error('读取input_720h的excel失败,错误原因为{}'.format(E))
        raise Exception
    try:
        sto = pd.read_excel('input_720/cacET/input_now.xls')
    except BaseException as E:
        _logging.error('读取input_now的excel失败,错误原因为{}'.format(E))
        raise Exception
    try:
        sto_end = pd.read_excel('input_720/cacET/input_end.xls')
    except BaseException as E:
        _logging.error('读取input_end的excel失败,错误原因为{}'.format(E))
        raise Exception
    try:
        event_table=pd.read_excel('input_720/cacET/event-triggered.xlsx')
    except BaseException as E:
        _logging.error('读取event_table的excel失败,错误原因为{}'.format(E))
        raise Exception

    sto_end['time']=time_end
    sto_end.index = [time_end]
    # 优化主函数
    # try:
    dict_control,z_file,model_SAObj,var_SALBUB,constraint_SARHS,judge_dict = OptimizationDay(parameter_json=input_json, load_json=load, begin_time = 0, time_scale=time_end, storage_begin_json=sto, storage_end_json=sto_end,model_type='MIP',z_file={})
    dict_control2,z_file2,model_SAObj2,var_SALBUB2,constraint_SARHS2,judge_dict2 = OptimizationDay(parameter_json=input_json, load_json=load, begin_time = 0, time_scale=time_end, storage_begin_json=sto, storage_end_json=sto_end,model_type='LP',z_file=z_file)
    
    to_csv(dict_control2,"cacET/day_ahead_scheduling")
    to_csv(var_SALBUB2,"cacET/day_ahead_scheduling_varUBLB")
    to_csv(constraint_SARHS2,"cacET/day_ahead_scheduling_RHSUBLB")

    #resulitss用来存结果，每循环一次都将结果保存，将所有列加入resultss，重复列加个“__z”后缀再去重
    resultss=copy.deepcopy(event_table)
    resultss=resultss.join(pd.DataFrame(dict_control2),rsuffix='__z')
    resultss=resultss.join(pd.DataFrame(var_SALBUB2),rsuffix='___z')
    resultss=resultss.join(pd.DataFrame(constraint_SARHS2),rsuffix='____z')
    resultss.drop(resultss.loc[:,resultss.columns.str.endswith('__z')].columns,axis=1,inplace=True)
    resultss['etm']=[0 for _ in range(len(resultss))]

    #计算状态量，根据上一时刻的状态和充放功率计算储能状态
    calculate_storage_state(0,event_table,judge_dict2,dict_control2)
    store_result(0,event_table,judge_dict2,dict_control2,var_SALBUB2,constraint_SARHS2)
   
    etm=0 #etm=0则结果直接用，etm=1线性规划灵敏度分析，etm=2重新解

    for l in event_table.index:
        #event_table的前两列为时间，因此从第三列开始循环，时间为便于计算采用10进制，如i=1，time=0.2表示1：12。
        for c in event_table.columns[2:]:
            #如果是储能，需要计算再比较，如8：20判断是否水箱温度触发，需先根据8：00的水箱温度和充放功率计算出8：20的温度，再和实际数据比较，电池和管道同理
            if c in ['t_ht_l','t_de_l','soc_b_l']:
                if event_table.at[l,'time']!=0:
                    #非整点的储能需要计算，计算方法同calculate_storage_state
                    last_index=event_table.at[l-1,'i']-judge_dict2['begin_time']#上一时刻
                    time_diff=event_table.at[l,'i']-event_table.at[l-1,'i']+event_table.at[l,'time']-event_table.at[l-1,'time']#时间差
                    if c=='t_ht_l':
                        jd=event_table.loc[l-1,'t_ht_l']-dict_control2['g_ht'][last_index]*(time_diff)/(4200/3.6/1000)/input_json['device']['ht']['water_max']- input_json['device']['ht']['miu_loss']*(judge_dict2['t_ht_l'][last_index]-load['ambient_temperature'][event_table.at[l-1,'i']])*(time_diff)/(4200/3.6/1000)
                    elif c=='t_de_l':
                        jd=event_table.loc[l-1,'t_de_l']+(dict_control2['g_ht'][last_index]+dict_control2['g_eb'][last_index]+dict_control2['g_hp'][last_index]+dict_control2['g_fc'][last_index]-dict_control2['g_load'][last_index])*(time_diff)/(4200/3.6/1000)/input_json['device']['de']['water_max']-input_json['device']['de']['miu_loss']*(dict_control2['t_de_l'][last_index]-43)*(time_diff)/(4200/3.6/1000)
                    elif c=='soc_b_l':
                        jd=event_table.loc[l-1,'soc_b_l']-dict_control2['p_b'][last_index]*(time_diff)*judge_dict2['k_b'][last_index] if dict_control2['p_b'][last_index]<=0 else event_table.loc[l-1,'soc_b_l']-dict_control2['p_b'][last_index]*(time_diff)/judge_dict2['k_b'][last_index]

                else:
                    #整点的储能直接比较
                    jd=judge_dict2[c][(int)(event_table.at[l,'i'])-judge_dict2['begin_time']]
                if  event_table.at[l,c]<=jd+0.01 and event_table.at[l,c]>=jd-0.01:
                    etm=etm
                else:
                    etm=2
                    break
            #如果是设备，判断上下限。ghp_has_open记录到当前时间为止今天开了多长时间热泵，单位小时
            elif c != 'ghp_has_open':
                if  event_table.at[l,c]<=judge_dict2[c][(int)(event_table.at[l,'i'])-judge_dict2['begin_time']]+0.01 and event_table.at[l,c]>=judge_dict2[c][(int)(event_table.at[l,'i'])-judge_dict2['begin_time']]-0.01:
                    etm=etm
                elif event_table.at[l,c]<=judge_dict2[c+'_UP'][(int)(event_table.at[l,'i'])-judge_dict2['begin_time']] and event_table.at[l,c]>=judge_dict2[c+'_LOW'][(int)(event_table.at[l,'i'])-judge_dict2['begin_time']]:
                    etm=1
                else:
                    etm=2
                    break

        if etm==1:
            update_i_load_and_eff(event_table,load,input_json,sto,l)
            #线性规划灵敏度分析比较麻烦，这里直接重解线性规划，和灵敏度分析效果一样，都是秒解
            dict_control2,z_file2,model_SAObj2,var_SALBUB2,constraint_SARHS2,judge_dict2 = OptimizationDay(parameter_json=input_json, load_json=load, begin_time = event_table.at[l,'i'], time_scale=time_end, storage_begin_json=sto, storage_end_json=sto_end,model_type='LP',z_file=z_file)

            calculate_storage_state(l,event_table,judge_dict2,dict_control2)
            store_result(l,event_table,judge_dict2,dict_control2,var_SALBUB2,constraint_SARHS2)
        elif etm==2:
            
            update_i_load_and_eff(event_table,load,input_json,sto,l)
            dict_control,z_file,model_SAObj,var_SALBUB,constraint_SARHS,judge_dict = OptimizationDay(parameter_json=input_json, load_json=load, begin_time = event_table.at[l,'i'], time_scale=time_end, storage_begin_json=sto, storage_end_json=sto_end,model_type='MIP',z_file={})
            dict_control2,z_file2,model_SAObj2,var_SALBUB2,constraint_SARHS2,judge_dict2 = OptimizationDay(parameter_json=input_json, load_json=load, begin_time = event_table.at[l,'i'], time_scale=time_end, storage_begin_json=sto, storage_end_json=sto_end,model_type='LP',z_file=z_file)

            calculate_storage_state(l,event_table,judge_dict2,dict_control2)
            store_result(l,event_table,judge_dict2,dict_control2,var_SALBUB2,constraint_SARHS2)
            
        resultss.loc[l,'etm']=etm
        etm=0
    #结果保存
    resultss.to_csv('Output/cacET/tmp.csv',float_format='%.3f')

    # 写入输出Excel
    # try:
    #     to_csv(dict_control,"cacET/ht300_hydrogen1792_de150_eb82_ghp95_test30_nozppi0mipbb")
    #     to_csv(dict_control2,"cacET/ht300_hydrogen1792_de150_eb82_ghp95_test30_nozppi0bb")
    #     to_csv(var_SALBUB2,"cacET/ht300_hydrogen1792_de150_eb82_ghp95_test_var_SALBUB330_nozppi0bb")
    #     to_csv(constraint_SARHS2,"cacET/ht300_hydrogen1792_de150_eb82_ghp95_test_constraint_SARHS330_nozppi0bb")

    # except BaseException as E:
    #     _logging.error('excel输出失败,错误原因为{}'.format(E))
    #     raise Exception