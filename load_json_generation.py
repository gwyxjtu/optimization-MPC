# 2023110511201129
# 功能：读104的不同点位，不同时间
import pandas as pd
import psycopg2
import os
from datetime import datetime, timedelta
import requests
import json
import matplotlib.pyplot as plt

file_name1 = 'tmp.xls'
file_name2 = '104_excel.xls'
output_folder = 'data_obix'

# 输出位置
def create_output_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

# 起始时间、终止时间标准化
def time_standard(start_date, end_date):
    date_format = "%Y-%m-%d %H:%M:%S"

    try:
        start_date = datetime.strptime(start_date, date_format)
        end_date = datetime.strptime(end_date, date_format)
        return start_date, end_date
    except ValueError:
        print("Input date and time format is incorrect. Please use the format: YYYY-MM-DD HH:MM:SS")
        return None, None

# 获取数据库表名


def table(start_date, end_date):
    # start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
    # end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
    
    all_months = []
    
    while start_date <= end_date:
        # 计算当前月份的结束日期
        year = start_date.year
        month = start_date.month
        next_month = month % 12 + 1
        if next_month == 1:
            year += 1
        end_of_month = datetime(year, next_month, 1) - timedelta(days=1)
        
        # 计算当前月份的表名
        table_name = "ems_obix_" + start_date.strftime("%Y_%m")
        all_months.append(table_name)
        
        # 将日期设置为下个月的第一天
        start_date = end_of_month + timedelta(days=1)
    
    return all_months


def read_obix(start_date_str, end_date_str, item_addr_connections):
    create_output_folder(output_folder)

    connection = psycopg2.connect(
        # host="123.249.70.226",
        # port=7004,
        host="192.168.3.13",
        port=5432,
        database="ems_capture",
        user="postgres",
        password="postgres"
    )

    start_date, end_date = time_standard(start_date_str, end_date_str)
    if start_date is None or end_date is None:
        return

    # decimal_tuple = decimal(item_addr_connections)
    data = pd.DataFrame()
    all_months = table(start_date, end_date)

    cursor = connection.cursor()
    item_data = pd.DataFrame()

    for item_addr in item_addr_connections:
        result = []
        for year_month in all_months:
            sql = """
            SELECT create_time, item_addr, item_name, item_val 
            FROM {} 
            WHERE create_time 
            BETWEEN %s AND %s AND 
            item_addr = %s::varchar""".format(year_month)
            cursor.execute(sql, (start_date, end_date, item_addr))
            result += cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(result, columns=columns)

        df['create_time'] = pd.to_datetime(df['create_time'])
        df = df.set_index('create_time')
        df=df.replace({'True': 1, 'False': 0})
        df.index = pd.DatetimeIndex(df.index)
        item_data[item_addr] = df['item_val'].astype(float).resample('60min').mean()

    cursor.close()
    connection.close()
    return item_data

def read_plat_heat(start_date_str, end_date_str):
    create_output_folder(output_folder)

    connection = psycopg2.connect(
        # host="123.249.70.226",
        # port=7004,
        host="192.168.3.13",
        port=5432,
        database="ems_platform",
        user="postgres",
        password="postgres"
    )

    start_date, end_date = time_standard(start_date_str, end_date_str)
    if start_date is None or end_date is None:
        return

    # decimal_tuple = decimal(item_addr_connections)
    data = pd.DataFrame()
    # all_months = table(start_date, end_date)


    all_months = [] 
    while start_date <= end_date:
        # 计算当前月份的结束日期
        year = start_date.year
        month = start_date.month
        next_month = month % 12 + 1
        if next_month == 1:
            year += 1
        end_of_month = datetime(year, next_month, 1) - timedelta(days=1)
        
        # 计算当前月份的表名
        table_name = "ems_device_heat_" + start_date.strftime("%Y_%m")
        all_months.append(table_name)
        
        # 将日期设置为下个月的第一天
        start_date = end_of_month + timedelta(days=1)



    cursor = connection.cursor()
    item_data = pd.DataFrame()

    # for item_addr in item_addr_connections:
    result = []
    for year_month in all_months:
        sql = """SELECT * FROM """+year_month+""" WHERE create_time<=%s AND create_time<=%s"""
        cursor.execute(sql, (start_date, end_date))
        result += cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(result, columns=columns)

    df['create_time'] = pd.to_datetime(df['create_time'])
    df = df.set_index('create_time')
    df.replace({True: 1, False: 0})
    df.index = pd.DatetimeIndex(df.index)
    item_data = df.astype(float).resample('60min').mean()

    cursor.close()
    connection.close()
    return item_data




def select_from_xj_json(input_dict,start_time,end_time):
    # now_time = datetime.datetime.now()
    # now_year = now_time.year
    # now_month = now_time.month
    # ago_datetime_hour = now_time - datetime.timedelta(days=100)
    # ago_month=(now_time-datetime.timedelta(days=30)).month
    tmp_time=start_time
    return_df = pd.DataFrame()
    url = 'http://192.168.3.13:5377/getdata'
    # url = 'http://123.249.70.226:7005/getdata'
    for key in input_dict:
        res_js=[]
        tmp_time=start_time
        while tmp_time<end_time:
            param = {'itemAddr': input_dict[key],"startTime": start_time, "endTime":end_time,'year': int(tmp_time.year), 'month': int(tmp_time.month)}
            res = requests.get(url, param, timeout=20)
            res_js =res_js+ json.loads(res.text)
            if tmp_time.month == 12:
                tmp_time = tmp_time.replace(year=tmp_time.year + 1, month=1)
            else:
                tmp_time = tmp_time.replace(month=tmp_time.month + 1)
            tmp_time=tmp_time.replace(day=1,hour=0,minute=0)

        res_df = pd.DataFrame(res_js)
        if not res_df.empty:
            res_df=res_df.sort_values(by='createtime').set_index('createtime')
            res_df.index=pd.DatetimeIndex(res_df.index)
            return_df[key]=res_df['itemval'].astype(float).resample('60min').mean()  
    # return_df['p_pv']=return_df.iloc[:,:].sum(axis=1)
    # return_df.to_csv('aaa.csv')  

        # res_df.to_csv("xj_db/data_xj/"+key+'_10'+".csv",encoding="utf_8_sig")
        # return_df = pd.concat([return_df,res_df],axi0s=1)
    return return_df

def jx_data(wlyb_now_data,start_time,end_time):
    # wlyb_now_data = {
    #     'i_hp': 17,
    #     'i_eb1':104,
    #     'i_eb2':148,
    #     'i_eb3':264,
    #     # 'jx1': 14,
    #     # 'jx2': 140,
    #     # 'jx3': 184, 
    #     # 'jx4': 300,
    #     'p_jx1':9,'p_jx2':135,'p_jx3':179,
    #     # 'i_ap1':27,'i_ap2':52,'i_ap3':192,'i_ap4':214,
    # }
    dbname = 'yulin_esms'
    db = psycopg2.connect(host='123.249.70.226', port=7004, user='postgres', password='postgres', database='iot_odata')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    ret_df=pd.DataFrame()
    for key,v in wlyb_now_data.items():
        # sql语句 建表
        # sql = """SELECT fvalue FROM iot_dm_devicedata where id = %s;"""
        sql="""SELECT fvalue,createdate FROM iot_dm_devicehisdata where factor = '"""+str(v)+"""' and deviceid = '总配电房' and createdate<='"""+end_time.strftime("%Y-%m-%d %H:%M:%S")+"""'::timestamp and createdate>='"""+start_time.strftime("%Y-%m-%d %H:%M:%S")+"""'::timestamp;"""

        params = (str(wlyb_now_data[key]),)
        cursor.execute(sql)
        # 这是查询表中所有的数据
        rest = cursor.fetchall()
        # wlyb_input[key] = float(rest[0])

        rest_list=[]
        for j in range(len(rest)):
            rest_list.append([rest[j][1].strftime("%Y-%m-%d %H:%M"),rest[j][0]])        
        # cocolumns_tmp=[key,'create_time']
        # issue #9 @gwyxjtu
        rest_df=pd.DataFrame(rest_list,columns=['create_time',key]).sort_values(by='create_time').set_index('create_time')
        rest_df.index=pd.DatetimeIndex(rest_df.index)
        ret_df[key]=rest_df[key].astype(float).resample('60min').mean()
        # rest_df=pd.DataFrame(rest_list,columns=cocolumns_tmp)
        # tmp_r_df=rest_df.sort_values(by='create_time')
        # tmp_r_df.set_index('create_time').to_excel(writer,sheet_name=key)
    theta = 1
    
    ret_df['pload_hp'] = ret_df['i_hp'].astype(float) * 1.73 * 380 * theta/1000
    ret_df['pload_eb'] = (ret_df['i_eb1'].astype(float) + ret_df['i_eb2'].astype(float) + ret_df['i_eb3'].astype(float)) * 1.73 * 380 * theta/1000
    ret_df['p_jx_sum']=ret_df['p_jx1'].astype(float)+ret_df['p_jx2'].astype(float)+ret_df['p_jx3'].astype(float)
    # ret_df.to_csv('sss.csv')
    
    # p_load_df = p_load_df.sort_values(by='create_time').set_index('create_time')
    return ret_df

if __name__ == '__main__':
    s=datetime(2023,10,27,0,0,0)
    s_str=s.strftime("%Y-%m-%d %H:%M:%S")
    
    e=datetime.now()
    e_str=e.strftime("%Y-%m-%d %H:%M:%S")
    plt.rcParams['font.sans-serif'] = ['SimHei']
    obix_addr=['BH_DK1_A/LL/','BH_DK2_B/LL/','BH_DK_17_18/LL/','E_F/E3/E3_RL/','E_F/E2/E2_RL/','GL2/RW_T/','GL2/SW_T/','GL1/RW_T/','GL1/SW_T/','E_F/F19/F19_LL/','E_F/F17/F17_LL/','GL1/S/','GL2/S/']
    data_obix=read_obix(s_str, e_str, obix_addr)
    # data_obix.to_csv('ooo.csv')
     
    xj_pv={'dcdc1':'0x4004','dcdc2':'0x400A','dcdc3':'0x4010','dcdc4':'0x4016','dcdc5':'0x401C','dcdc6':'0x4022'}
    pv_df=select_from_xj_json(xj_pv,s,e)
    pv_df['p_pv']=pv_df.iloc[:,:].sum(axis=1)
    

    wlyb_now_data = {
        'i_hp': 17,
        'i_eb1':104,
        'i_eb2':148,
        'i_eb3':264,
        # 'jx1': 14,
        # 'jx2': 140,
        # 'jx3': 184, 
        # 'jx4': 300,
        'p_jx1':9,'p_jx2':135,'p_jx3':179,
        # 'i_ap1':27,'i_ap2':52,'i_ap3':192,'i_ap4':214,
    }
    p_wlyb_df=jx_data(wlyb_now_data,s,e)

    #系统能效
    system_cop_df=pd.DataFrame()
    system_cop_df['p_jx_sum']=p_wlyb_df['p_jx_sum']
    system_cop_df['p_pv']=pv_df['p_pv']
    system_cop_df['p_consum']=system_cop_df['p_pv']+system_cop_df['p_jx_sum']
    system_cop_df['gload_es']=data_obix['E_F/E2/E2_RL/']*277.77
    system_cop_df['gload_vi']=data_obix['E_F/E3/E3_RL/']*277.77
    system_cop_df['gload_sum']=system_cop_df['gload_es']+system_cop_df['gload_vi']
    system_cop_df['heat_system_cop']=system_cop_df['gload_sum']/(p_wlyb_df['pload_hp']+p_wlyb_df['pload_eb'])
    fig_sys,axes_sys=plt.subplots(ncols=1,nrows=3,sharex=True)
    # system_cop_df[['p_jx1','p_jx2','p_jx3']].plot(ax=axes[0])
    system_cop_df['p_jx_sum'].plot(ax=axes_sys[0],title='p_jx_sum',yticks=[0,500,1000,1500,2000])
    system_cop_df['p_pv'].plot(ax=axes_sys[1],title='p_pv',yticks=[0,500,1000,1500,2000])
    system_cop_df['p_consum'].plot(ax=axes_sys[2],title='p_consum',yticks=[0,500,1000,1500,2000])
    # p_wlyb_df['p_jx_sum'].plot()
    plt.show()
    fig_sys,axes_sys=plt.subplots(ncols=1,nrows=3,sharex=True)
    system_cop_df['gload_es'].plot(ax=axes_sys[0],title='gload_es')
    system_cop_df['gload_vi'].plot(ax=axes_sys[1],title='gload_vi')
    system_cop_df['gload_sum'].plot(ax=axes_sys[2],title='gload_sum')
    plt.show()
    system_cop_df['heat_system_cop'].plot(title='heat_system_cop')
    plt.show()


    # #fc能效
    xj_fc = {'p_fc_real':'0x421D','p_ac':'0x4253','p_fc_set':"0x6220",
             'total_t_fc_in':'0x425E','total_t_fc_out':'0x425F','total_m_fc':'0x4262'
             ,'Busbar_mf':'0x4068'}
    fc_df=select_from_xj_json(xj_fc,s,e)
    fc_df['g_fc']=(fc_df['total_t_fc_out']-fc_df['total_t_fc_in'])*fc_df['total_m_fc']*4200/3600
    fc_df['cop_fc']=(fc_df['g_fc']+fc_df['p_fc_real'])/(fc_df['Busbar_mf']*60*33)
    fc_df['g_p_ratio']=fc_df['g_fc']/fc_df['p_fc_real']

    fig_sys,axes_sys=plt.subplots(ncols=1,nrows=4,sharex=True)
    fc_df[['total_t_fc_in','total_t_fc_out']].plot(ax=axes_sys[0],title='进出水温度')
    fc_df[['g_fc','p_fc_real']].plot(ax=axes_sys[1],title='电热功率')
    fc_df['cop_fc'].plot(ax=axes_sys[2],title='fc效率')
    fc_df['g_p_ratio'].plot(ax=axes_sys[3],title='热电功率比')
    plt.show()

    #热泵能效
    heat_df=read_plat_heat(s_str,e_str)
    ghp_df=pd.DataFrame()
    ghp_df['p_load_ghp']=p_wlyb_df['pload_hp']
    ghp_df['t_hp_1_in']=heat_df['t_hp_1_in']
    ghp_df['t_hp_1_out']=heat_df['t_hp_1_out']
    ghp_df['m_hp_1']=heat_df['m_hp_1']-30
    ghp_df['m_hp_2']=heat_df['m_hp_2']
    ghp_df['t_hp_2_in']=heat_df['t_hp_2_in']
    ghp_df['t_hp_2_out']=heat_df['t_hp_2_out']
    ghp_df['g_ghp']=(ghp_df['t_hp_1_out']-ghp_df['t_hp_1_in'])*ghp_df['m_hp_1']*4200/3600
    ghp_df['cop_ghp']=ghp_df['g_ghp']/ghp_df['p_load_ghp']

    fig_sys,axes_sys=plt.subplots(ncols=1,nrows=5,sharex=True)
    ghp_df[['t_hp_1_in','t_hp_1_out']].plot(ax=axes_sys[0],title='一次侧进出水温度')
    ghp_df[['t_hp_2_in','t_hp_2_out']].plot(ax=axes_sys[1],title='井侧进出水温度')
    ghp_df['p_load_ghp'].plot(ax=axes_sys[2],title='热泵耗电')
    ghp_df['cop_ghp'].plot(ax=axes_sys[3],title='热泵效率')
    ghp_df['m_hp_2'].plot(ax=axes_sys[4],title='井侧流量')
    plt.show()

    #电锅炉能效
    eb_df=pd.DataFrame()
    eb_df['p_load_eb']=p_wlyb_df['pload_eb']
    eb_df['g_eb1']=data_obix['GL1/S/']*abs((data_obix['GL1/SW_T/']-data_obix['GL1/RW_T/'])*data_obix['E_F/F19/F19_LL/']*4200/3600)
    eb_df['g_eb2']=data_obix['GL2/S/']*abs((data_obix['GL2/SW_T/']-data_obix['GL2/RW_T/'])*data_obix['E_F/F17/F17_LL/']*4200/3600)
    eb_df['cop_eb']=(eb_df['g_eb1']+eb_df['g_eb2'])/eb_df['p_load_eb']

    fig_sys,axes_sys=plt.subplots(ncols=1,nrows=3,sharex=True)
    eb_df[['g_eb1','g_eb2']].plot(ax=axes_sys[0],title='电锅炉制热量')
    eb_df['p_load_eb'].plot(ax=axes_sys[1],title='电锅炉耗电')
    eb_df['cop_eb'].plot(ax=axes_sys[2],title='锅炉效率')
    plt.show()






    print('ll')
