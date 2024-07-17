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


def update_i_load_and_eff(event_table,load,input_json,sto,l):
    load.loc[event_table.at[l,'i'],'g_load']=event_table.at[l,'g_load']
    load.loc[event_table.at[l,'i'],'p_load']=event_table.at[l,'p_load']
    load.loc[event_table.at[l,'i'],'pv_generation']=event_table.at[l,'p_pv']
    input_json['device']['fc']['k_fc_p']=event_table.at[l,'k_fc_p']
    input_json['device']['fc']['k_fc_g']=event_table.at[l,'k_fc_g']
    input_json['device']['eb']['k_eb']=event_table.at[l,'k_eb']
    input_json['device']['battery']['k_b']=event_table.at[l,'k_b']
    sto.loc[event_table.at[l,'i'],'t_ht']=event_table.at[l,'t_ht_l']
    sto.loc[event_table.at[l,'i'],'t_de']=event_table.at[l,'t_de_l']
    sto.loc[event_table.at[l,'i'],'soc_b']=event_table.at[l,'soc_b_l']
    sto.loc[event_table.at[l,'i'],'ghp_has_open']=event_table.at[l,'ghp_has_open']

if __name__ == '__main__':


    # g_load={'g_load_18':([3800]*11+[2200]*7+[3800]*6)*60,
    # #         'g_load_26':([2500]*11+[1600]*7+[2500]*6)*60,
    #         # 'g_load_32':([3200]*11+[2000]*7+[3200]*6)*60
    
    #         }
    # pd.DataFrame(g_load).to_csv('hh38.csv')
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
    
    # event_table=pd.read_excel('')


    sto_end['time']=time_end
    sto_end.index = [time_end]
    # 优化主函数
    # try:
    dict_control,z_file,model_SAObj,var_SALBUB,constraint_SARHS,judge_dict = OptimizationDay(parameter_json=input_json, load_json=load, begin_time = 0, time_scale=time_end, storage_begin_json=sto, storage_end_json=sto_end,model_type='MIP',z_file={})
    dict_control2,z_file2,model_SAObj2,var_SALBUB2,constraint_SARHS2,judge_dict2 = OptimizationDay(parameter_json=input_json, load_json=load, begin_time = 0, time_scale=time_end, storage_begin_json=sto, storage_end_json=sto_end,model_type='LP',z_file=z_file)
    
    # to_csv(dict_control,"cacET/ht300_hydrogen1792_de150_eb82_ghp95_test30_nozppi0mipbb")
    to_csv(dict_control2,"cacET/day_ahead_scheduling")
    to_csv(var_SALBUB2,"cacET/day_ahead_scheduling_varUBLB")
    # to_csv(model_SAObj2,"1216_fc不能蓄热/1800_1200/ht300_hydrogen1792_de150_eb82_ghp95_test_")
    to_csv(constraint_SARHS2,"cacET/day_ahead_scheduling_RHSUBLB")

    event_table=pd.read_excel('input_720/cacET/event-triggered.xlsx')
    resultss=copy.deepcopy(event_table)
    resultss=resultss.join(pd.DataFrame(dict_control2),rsuffix='__z')
    resultss=resultss.join(pd.DataFrame(var_SALBUB2),rsuffix='___z')
    resultss=resultss.join(pd.DataFrame(constraint_SARHS2),rsuffix='____z')
    resultss.drop(resultss.loc[:,resultss.columns.str.endswith('__z')].columns,axis=1,inplace=True)
    resultss['etm']=[0 for _ in range(len(resultss))]
    for ll in range(1,len(event_table)):
        event_table.loc[ll,'soc_b_l']=event_table.loc[ll-1,'soc_b_l']-dict_control2['p_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])*judge_dict2['k_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']] if dict_control2['p_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]<=0 else event_table.loc[ll-1,'soc_b_l']-dict_control2['p_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/judge_dict2['k_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]
        # event_table.loc[ll,'soc_b_l']=dict_control2['soc_b_l'][event_table.at[ll,'i']-l]
        event_table.loc[ll,'t_ht_l']=event_table.loc[ll-1,'t_ht_l']-dict_control2['g_ht'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)/input_json['device']['ht']['water_max']- input_json['device']['ht']['miu_loss']*(judge_dict2['t_ht_l'][event_table.at[ll-1,'i']]-load['ambient_temperature'][event_table.at[ll-1,'i']])*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)
        event_table.loc[ll,'t_de_l']=event_table.loc[ll-1,'t_de_l']+(dict_control2['g_ht'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]+dict_control2['g_eb'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]+dict_control2['g_hp'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]+dict_control2['g_fc'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]-dict_control2['g_load'][event_table.at[ll-1,'i']-judge_dict2['begin_time']])*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)/input_json['device']['de']['water_max']-input_json['device']['de']['miu_loss']*(dict_control2['t_de_l'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]-43)*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)
        event_table.loc[ll,'ghp_has_open']=event_table.loc[ll-1,'ghp_has_open']+z_file2['z_hp'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])
    for ll in range(len(event_table)):
        for k in dict_control2.keys():
            resultss.loc[ll,k]=dict_control2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
        for k in var_SALBUB2.keys():
            resultss.loc[ll,k]=var_SALBUB2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
        for k in constraint_SARHS2.keys():
            resultss.loc[ll,k]=constraint_SARHS2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
        for k in event_table.columns[2:]:
            resultss.loc[ll,k]=event_table.loc[ll,k]
    # event_triggered_s=event_table[:,:]
    etm=0
    for l in event_table.index:
        for c in event_table.columns[2:]:
            if  event_table.at[l,c]<=judge_dict2[c][(int)(event_table.at[l,'i'])-judge_dict2['begin_time']]+0.01 and event_table.at[l,c]>=judge_dict2[c][(int)(event_table.at[l,'i'])-judge_dict2['begin_time']]-0.01:
                etm=etm
            elif event_table.at[l,c]<=judge_dict2[c+'_UP'][(int)(event_table.at[l,'i'])-judge_dict2['begin_time']] and event_table.at[l,c]>=judge_dict2[c+'_LOW'][(int)(event_table.at[l,'i'])-judge_dict2['begin_time']]:
                etm=1
            else:
                etm=2
                break
        if etm==1:

            update_i_load_and_eff(event_table,load,input_json,sto,l)
            dict_control2,z_file2,model_SAObj2,var_SALBUB2,constraint_SARHS2,judge_dict2 = OptimizationDay(parameter_json=input_json, load_json=load, begin_time = event_table.at[l,'i'], time_scale=time_end, storage_begin_json=sto, storage_end_json=sto_end,model_type='LP',z_file=z_file)
            # for k in resultss.keys():
            #     for ll in range(judge_dict2['begin_time'],time_end):
            #         resultss[k][ll]=dict_control2[k][ll-judge_dict2['begin_time']]
            for ll in range(l+1,len(event_table)):
                event_table.loc[ll,'soc_b_l']=event_table.loc[ll-1,'soc_b_l']-dict_control2['p_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])*judge_dict2['k_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']] if dict_control2['p_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]<=0 else event_table.loc[ll-1,'soc_b_l']-dict_control2['p_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/judge_dict2['k_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]
                # event_table.loc[ll,'soc_b_l']=dict_control2['soc_b_l'][event_table.at[ll,'i']-l]
                event_table.loc[ll,'t_ht_l']=event_table.loc[ll-1,'t_ht_l']-dict_control2['g_ht'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)/input_json['device']['ht']['water_max']- input_json['device']['ht']['miu_loss']*(judge_dict2['t_ht_l'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]-load['ambient_temperature'][event_table.at[ll-1,'i']])*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)
                event_table.loc[ll,'t_de_l']=event_table.loc[ll-1,'t_de_l']+(dict_control2['g_ht'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]+dict_control2['g_eb'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]+dict_control2['g_hp'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]+dict_control2['g_fc'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]-dict_control2['g_load'][event_table.at[ll-1,'i']-judge_dict2['begin_time']])*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)/input_json['device']['de']['water_max']-input_json['device']['de']['miu_loss']*(dict_control2['t_de_l'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]-43)*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)
                event_table.loc[ll,'ghp_has_open']=event_table.loc[ll-1,'ghp_has_open']+z_file2['z_hp'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])
            for ll in range(l,len(event_table)):
                for k in dict_control2.keys():
                    resultss.loc[ll,k]=dict_control2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
                for k in var_SALBUB2.keys():
                    resultss.loc[ll,k]=var_SALBUB2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
                for k in constraint_SARHS2.keys():
                    resultss.loc[ll,k]=constraint_SARHS2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
                for k in event_table.columns[2:]:
                    resultss.loc[ll,k]=event_table.loc[ll,k]
        elif etm==2:
            
            update_i_load_and_eff(event_table,load,input_json,sto,l)
            dict_control,z_file,model_SAObj,var_SALBUB,constraint_SARHS,judge_dict = OptimizationDay(parameter_json=input_json, load_json=load, begin_time = event_table.at[l,'i'], time_scale=time_end, storage_begin_json=sto, storage_end_json=sto_end,model_type='MIP',z_file={})
            dict_control2,z_file2,model_SAObj2,var_SALBUB2,constraint_SARHS2,judge_dict2 = OptimizationDay(parameter_json=input_json, load_json=load, begin_time = event_table.at[l,'i'], time_scale=time_end, storage_begin_json=sto, storage_end_json=sto_end,model_type='LP',z_file=z_file)
            # for k in resultss.keys():
            #     for ll in range(judge_dict2['begin_time'],time_end):
            #         resultss[k][ll]=dict_control2[k][ll-judge_dict2['begin_time']]
            for ll in range(l+1,len(event_table)):
                event_table.loc[ll,'soc_b_l']=event_table.loc[ll-1,'soc_b_l']-dict_control2['p_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])*judge_dict2['k_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']] if dict_control2['p_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]<=0 else event_table.loc[ll-1,'soc_b_l']-dict_control2['p_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/judge_dict2['k_b'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]
                # event_table.loc[ll,'soc_b_l']=dict_control2['soc_b_l'][event_table.at[ll,'i']-l]
                event_table.loc[ll,'t_ht_l']=event_table.loc[ll-1,'t_ht_l']-dict_control2['g_ht'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)/input_json['device']['ht']['water_max']- input_json['device']['ht']['miu_loss']*(judge_dict2['t_ht_l'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]-load['ambient_temperature'][event_table.at[ll-1,'i']])*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)
                event_table.loc[ll,'t_de_l']=event_table.loc[ll-1,'t_de_l']+(dict_control2['g_ht'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]+dict_control2['g_eb'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]+dict_control2['g_hp'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]+dict_control2['g_fc'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]-dict_control2['g_load'][event_table.at[ll-1,'i']-judge_dict2['begin_time']])*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)/input_json['device']['de']['water_max']-input_json['device']['de']['miu_loss']*(dict_control2['t_de_l'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]-43)*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])/(4200/3.6/1000)
                event_table.loc[ll,'ghp_has_open']=event_table.loc[ll-1,'ghp_has_open']+z_file2['z_hp'][event_table.at[ll-1,'i']-judge_dict2['begin_time']]*(event_table.at[ll,'i']-event_table.at[ll-1,'i']+event_table.at[ll,'time']-event_table.at[ll-1,'time'])
            for ll in range(l,len(event_table)):
                for k in dict_control2.keys():
                    resultss.loc[ll,k]=dict_control2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
                for k in var_SALBUB2.keys():
                    resultss.loc[ll,k]=var_SALBUB2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
                for k in constraint_SARHS2.keys():
                    resultss.loc[ll,k]=constraint_SARHS2[k][event_table.at[ll,'i']-judge_dict2['begin_time']]
                for k in event_table.columns[2:]:
                    resultss.loc[ll,k]=event_table.loc[ll,k]
        resultss.loc[l,'etm']=etm
        etm=0

    resultss.to_csv('Output/cacET/renewnew.csv',float_format='%.3f')



    # for index in event_table.index:
    #     et=0
    #     for c in event_table.columns:
    #         if dict_control[c][event_table.at[index,'i']]!=event_table.at[index,c]:
    #             et=1
    #             break
    #     if et==1:
    #         for c in event_table.columns:
    #             if dict_control[c][event_table.at[index,'i']]!=event_table.at[index,c]:
    #                 et=1
    #                 break
    
    
    
    
    
    
    # except BaseException as E:
    #     _logging.error('优化主函数执行失败，错误原因为{}'.format(E))
    #     raise Exception
    #print(dict_control)
    #print(dict_plot)
    
    # 写入输出Excel
    try:
        to_csv(dict_control,"cacET/ht300_hydrogen1792_de150_eb82_ghp95_test30_nozppi0mipbb")
        to_csv(dict_control2,"cacET/ht300_hydrogen1792_de150_eb82_ghp95_test30_nozppi0bb")
        to_csv(var_SALBUB2,"cacET/ht300_hydrogen1792_de150_eb82_ghp95_test_var_SALBUB330_nozppi0bb")
        # to_csv(model_SAObj2,"1216_fc不能蓄热/1800_1200/ht300_hydrogen1792_de150_eb82_ghp95_test_")
        to_csv(constraint_SARHS2,"cacET/ht300_hydrogen1792_de150_eb82_ghp95_test_constraint_SARHS330_nozppi0bb")

        # to_csv(dict_plot,"dict_opt_plot_24h")
    except BaseException as E:
        _logging.error('excel输出失败,错误原因为{}'.format(E))
        raise Exception