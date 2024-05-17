
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xlrd
from sklearn.linear_model import LinearRegression

day = [31,28,31,30,31,30,31,31,30,31,30,31]
month = [sum(day[:i]) for i in range(13)]
print(month)
# book = xlrd.open_workbook('season_hyd.xls')
book = xlrd.open_workbook('Output/dict_opt_plot_case5000.xls')

res = book.sheet_by_name('test')

def get_SSE(data):
    model = LinearRegression()
    model.fit(np.arange(0,len(data)).reshape(-1,1),data)
    SSE = np.sum((data-model.predict(np.arange(0,len(data)).reshape(-1,1)))**2)
    sum_yy = np.sum((data-np.mean(data))**2)
    return np.sqrt(SSE/len(data)) #SSE/sum_yy*np.mean(data
# heat_in = []
hydrogen = []
season_heat_io = []
work_hp = []
# print(res.cell(34,4).value)
for i in range(24*24):
    hydrogen.append(float(res.cell(i+1,30).value))
    season_heat_io.append(float(res.cell(i+1,23).value))
    work_hp.append(float(res.cell(i+1,4).value))
    # heat_in.append(float(res.cell(i+2,21).value))
# season_heat_sto = [sum(season_heat_io[:i]) for i in range(8760)]


# pd.DataFrame([data])
heat_mon = []
heat_mon_std = []
hydro_mon = []
hydro_mon_std = []
heat_in_mon = []
# for i in range(12):
#     heat_mon.append(np.mean(season_heat_io[month[i]*24:month[i+1]*24]))
#     hydro_mon_std.append(get_SSE(hydrogen[month[i]*24:month[i+1]*24]))#.append(np.std(hydrogen[month[i]*24:month[i+1]*24]))
    
#     hydro_mon.append(np.mean(hydrogen[month[i]*24:month[i+1]*24]))
#     # heat_in_mon.append(np.sum(heat_in[month[i]*24:month[i+1]*24]))

# season_heat_io_work = [season_heat_io[i] for i in range(12*24) if work_hp[i]>0]

for i in range(24):
    # 半个月算一次
    # non_idx = np.nonzero([season_heat_io[i*24:(i+1)*24][j] if work_hp[i*24:(i+1)*24][j]>0 else 0 for j in range(24)])
    # heat_mon.append(np.mean([season_heat_io[i*24:(i+1)*24][j] for j in non_idx[0]]))
    heat_mon.append(np.mean(season_heat_io[i*24:(i+1)*24]))
    heat_mon_std.append(np.std(season_heat_io[i*24:(i+1)*24]))
    # hydro_mon_std.append(np.std(hydrogen[i*15*24:(i+1)*15*24]))
    hydro_mon_std.append(get_SSE(hydrogen[i*24:(i+1)*24]))
    hydro_mon.append(np.mean(hydrogen[i*24:(i+1)*24]))
    
# heat_mon = [heat_mon[i]-min(heat_mon) for i in range(len(heat_mon))]


# week_hydro = []
# week_hydro_std = []

# for i in range(52):
#     # print(i*7,(i+1)*7)
#     week_hydro.append(np.mean(hydrogen[i*7*24:(i+1)*7*24]))
#     week_hydro_std.append(np.std(hydrogen[i*7*24:(i+1)*7*24]))

# print(heat_mon)
# print(hydro_mon_std)
# print(hydro_mon)
# print(heat_in_mon)

for i in range(len(heat_mon)):
    print(heat_mon[i])
print("----")
for i in range(len(heat_mon)):
    print(hydro_mon[i])
print("----")
for i in range(len(heat_mon)):
    print(hydro_mon_std[i])
print("----")

# for i in range(12):
#     print(heat_in_mon[i])
plt.plot(np.arange(0,24), heat_mon)
plt.plot(np.arange(0,24), heat_mon_std)
# plt.plot(np.arange(0,12), heat_mon)
plt.show()
print(res)