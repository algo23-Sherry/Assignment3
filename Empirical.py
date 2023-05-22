# -*- coding: utf-8 -*-
"""
Created on Sat May 20 14:37:44 2023

@author: Sherry
"""
# import akshare as ak
import pandas as pd
import datetime 
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus']=False


# futures_zh_minute_sina_df = ak.futures_zh_minute_sina(symbol="TF2009", period="1")
# print(futures_zh_minute_sina_df)

# contract =  ak.match_main_contract(symbol="cffex") 


# futures_symbol_mark_df = ak.futures_symbol_mark()

# big_df = pd.DataFrame()
# for item in futures_symbol_mark_df['symbol']:
#     print(item)
#     futures_zh_realtime_df = ak.futures_zh_realtime(symbol=item)
#     big_df = pd.concat([big_df, futures_zh_realtime_df], ignore_index=True)

# print(big_df)

# futures_zh_minute_sina_df = ak.futures_zh_minute_sina(symbol="TF2009", period="1")

#交易所历史数据
# """
# 获取20150101-20200101期间的期货合约（沪深300股指期货）
# """
# get_futures_daily_df = ak.get_futures_daily(start_date="20150101", end_date="20200101", market="CFFEX")
# get_futures_daily_df.to_csv('futures_daily.csv')
# contracts = get_futures_daily_df.loc[get_futures_daily_df['variety']=='IF',:].copy()
# contracts = contracts['symbol'].unique().tolist()
# f = open("futures_contrtacts.txt","w")
# f.writelines(str(contracts))
# f.close()
# f = open("futures_contrtacts.txt","r")
# contracts = eval(f.readlines()[0])
# f.close()

# #新浪 历史分钟数据

# futures_zh_minute_sina_df = ak.futures_zh_minute_sina(symbol='IF2005', period="1")


#数据来源：通达信期货通

data = pd.read_csv('47#IF300.csv',encoding='ANSI',header=0,skiprows=1,names=['日期','时间','开盘','最高'	,'最低','收盘','成交量'	,'成交额'])



datelist = data['日期'].unique().tolist()[:-1]



stop_loss = -0.005
threshold_SMS = 0.0009
transacton_cost = 0.0002
start_time1 = 0  #开仓周期起点
start_time2 = 50  #开仓时间
end_time = 239#收盘时间，平仓时间




def strategy(date,P):
    stop_loss = P[0]
    threshold_SMS = P[1] 
    transacton_cost = P[2]
    start_time1 = P[3]  #开仓周期起点
    start_time2 = P[4]  #开仓时间
    end_time = P[5]#收盘时间，平仓时间
    # date = date
    data_day = data.loc[data['日期']==date,:].copy()
    if len(data_day)==240:#当日数据完整
        #最大回撤
        roll_max = data_day['收盘'].cummax()
        dd = 1-data_day['收盘']/roll_max
        maxDD = dd.cummax()
        maxDD_mean = maxDD[start_time1:start_time2].mean()
        #maxDD.rename(index={'收盘':'maxDD'},inplace=True)
        
        #反向最大回撤
        roll_min = data_day['收盘'].cummin()
        dd_re = data_day['收盘']/roll_min-1
        maxDD_reverse = dd_re.cummax()
        maxDD_reverse_mean = maxDD_reverse[start_time1:start_time2].mean()
        #maxDD_reverse.rename(index={'收盘':'maxDD_re'},inplace=True)
        #SMS short for Stability of market sentiment
        SMS = min(maxDD_mean,maxDD_reverse_mean)
        return_day = max((data_day['收盘'].values[end_time]-data_day['收盘'].values[start_time2])/data_day['收盘'].values[start_time2],stop_loss)#如果开仓，当时收益率取这两者的更大值
        #买卖方向
        if data_day['收盘'].values[start_time2-1]>data_day['收盘'].values[start_time1]:
            LorS = 1
        elif data_day['收盘'].values[start_time2-1]==data_day['收盘'].values[start_time1]:#第一分钟和第50分钟价格一样也无法判断趋势
            LorS = 0
        else:
            LorS = -1
        return SMS,return_day,LorS
    else:
        return 100,0,0
    
                     
def baktest1(list_para):
    dict_backtest = dict()
    for date in datelist:
        SMS,return_day,LorS = strategy(date,list_para)
        dict_backtest[date] = [int(SMS<list_para[1]),return_day-list_para[2],LorS,SMS]
    
    df_backtest = pd.DataFrame(dict_backtest).T
    df_backtest.rename(columns={0:'开仓',1:'收益率',2:'做多做空',3:'平稳率'},inplace=True)
    df_backtest['net_re'] = df_backtest['开仓']*df_backtest['做多做空']*df_backtest['收益率']+1
    df_backtest['net_value'] = df_backtest['net_re'].cumprod()
    df_backtest = pd.merge(df_backtest,data.loc[data['时间']==1500,['日期','收盘']],left_index=True,right_on='日期',how='left')
    df_backtest['沪深300净值'] = df_backtest['收盘']/df_backtest['收盘'].values[0]
    df_backtest.reset_index(inplace=True,drop=True)
    return df_backtest

def baktest2(list_para1,list_para2):
    dict_backtest = dict()
    for date in datelist:
        SMS,return_day,LorS = strategy(date,list_para1)
        dict_backtest[date+'_A'] = [int(SMS<threshold_SMS),return_day-transacton_cost,LorS,SMS,1130]
        SMS,return_day,LorS = strategy(date,list_para2)
        dict_backtest[date+'_B'] = [int(SMS<threshold_SMS),return_day-transacton_cost,LorS,SMS,1500]
    
    df_backtest = pd.DataFrame(dict_backtest).T
    df_backtest.rename(columns={0:'开仓',1:'收益率',2:'做多做空',3:'平稳率',4:'时间'},inplace=True)
    df_backtest['日期'] = df_backtest.index.to_series().apply(lambda x:x[:10])
    df_backtest['time'] =  df_backtest['日期']+ df_backtest['时间'].apply(str)
    df_backtest['net_re'] = df_backtest['开仓']*df_backtest['做多做空']*df_backtest['收益率']+1
    df_backtest['net_value'] = df_backtest['net_re'].cumprod()
    df_backtest = pd.merge(df_backtest,data[['日期','时间','收盘']],left_on=['日期','时间'],right_on=['日期','时间'],how='left')
    df_backtest['沪深300净值'] = df_backtest['收盘']/df_backtest['收盘'].values[0]
    return df_backtest


def indicators(df):
    dict_statistic = dict()
    dict_statistic['交易总次数'] = sum(df['开仓'])
    dict_statistic['最大单次盈利'] = max(df['收益率'])
    dict_statistic['最大单次亏损'] = min(df['收益率'])
    df_temp = df.loc[df['开仓']==1,:].copy()
    df_temp['win'] = df_temp['收益率']*df_temp['做多做空']>0
    df_temp['lose'] = df_temp['收益率']*df_temp['做多做空']<0
    dict_statistic['获胜次数'] = sum(df_temp['win'])
    dict_statistic['失败次数'] = sum(df_temp['lose'])
    dict_statistic['胜率'] = dict_statistic['获胜次数']/(dict_statistic['获胜次数']+dict_statistic['失败次数'])
    #最大回撤
    roll_max = df['net_value'].cummax()
    dd = 1-df['net_value']/roll_max
    maxDD = dd.cummax()
    dict_statistic['最大回撤'] = maxDD.values.max()
    dict_statistic['累计收益率'] = df['net_value'].values[-1]
    return dict_statistic


# list_para = [stop_loss,threshold_SMS,transacton_cost,start_time1,start_time2,end_time]

list_para1 = [-0.005,0.0009,0.0002,0,50,239]
df_backtest1 = baktest1(list_para1)
dict_statistic1 = indicators(df_backtest1)

#画图
fig,axe= plt.subplots(1,1,figsize=(16,4))
fig.autofmt_xdate()
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(28)) 
axe.plot(df_backtest1['日期'],df_backtest1['net_value']*100,label='netvalue(%)')
# axe2 = axe.twinx()
axe.plot(df_backtest1['日期'],df_backtest1['沪深300净值']*100,label='沪深300净值(100%)')
# axe.set_ylabel('净值')
axe.set_xlabel('日期')
axe.set_title('平稳度指数交易模型资产累计收益1(单日最多一次开仓，阈值0.009，开仓时间：开盘50min)')
plt.legend()




"""
comment：
600多个交易日只开仓了11次，5次失败，6次获胜，开仓次数太少，尝试调高阈值
"""


list_para2 = [-0.005,0.0010,0.0002,0,50,239]
list_para3 = [-0.005,0.0011,0.0002,0,50,239]
list_para4 = [-0.005,0.0012,0.0002,0,50,239]
list_para5 = [-0.005,0.0013,0.0002,0,50,239]
df_backtest2 = baktest1(list_para2)
dict_statistic2 = indicators(df_backtest2)
df_backtest3 = baktest1(list_para3)
dict_statistic3 = indicators(df_backtest3)
df_backtest4 = baktest1(list_para4)
dict_statistic4 = indicators(df_backtest4)
df_backtest5 = baktest1(list_para5)
dict_statistic5 = indicators(df_backtest5)


fig,axe= plt.subplots(1,1,figsize=(16,4))
fig.autofmt_xdate()
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(28)) 
axe.plot(df_backtest1['日期'],df_backtest1['net_value']*100,label='阈值=0.0009(%)')
# axe2 = axe.twinx()
axe.plot(df_backtest1['日期'],df_backtest2['net_value']*100,label='阈值=0.0010(%)')
axe.plot(df_backtest1['日期'],df_backtest3['net_value']*100,label='阈值=0.0011(%)')
axe.plot(df_backtest1['日期'],df_backtest4['net_value']*100,label='阈值=0.0012(%)')
axe.plot(df_backtest1['日期'],df_backtest5['net_value']*100,label='阈值=0.0013(%)')
# axe.set_ylabel('净值')
axe.set_xlabel('日期')
axe.set_title('平稳度指数交易模型资产累计收益1(单日最多一次开仓，多阈值，开仓时间：开盘50min)')
plt.legend()


"""
comment：
阈值越高，最大回撤越高，综合选0.0012比较好
"""
#改变开仓时间


list_para6 = [-0.005,0.0012,0.0002,0,48,239]
list_para7 = [-0.005,0.0012,0.0002,0,49,239]
list_para8 = [-0.005,0.0012,0.0002,0,51,239]
list_para9 = [-0.005,0.0012,0.0002,0,52,239]
df_backtest6 = baktest1(list_para6)
dict_statistic6 = indicators(df_backtest6)
df_backtest7 = baktest1(list_para7)
dict_statistic7 = indicators(df_backtest7)
df_backtest8 = baktest1(list_para8)
dict_statistic8 = indicators(df_backtest8)
df_backtest9 = baktest1(list_para9)
dict_statistic9 = indicators(df_backtest9)


fig,axe= plt.subplots(1,1,figsize=(16,4))
fig.autofmt_xdate()
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(28)) 
axe.plot(df_backtest1['日期'],df_backtest6['net_value']*100,label='开仓时间=48(%)')
# axe2 = axe.twinx()
axe.plot(df_backtest1['日期'],df_backtest7['net_value']*100,label='开仓时间=49(%)')
axe.plot(df_backtest1['日期'],df_backtest4['net_value']*100,label='开仓时间=50(%)')
axe.plot(df_backtest1['日期'],df_backtest8['net_value']*100,label='开仓时间=51(%)')
axe.plot(df_backtest1['日期'],df_backtest9['net_value']*100,label='开仓时间=52(%)')
# axe.set_ylabel('净值')
axe.set_xlabel('日期')
axe.set_title('平稳度指数交易模型资产累计收益1(单日最多一次开仓，阈值=0.0012，多开仓时间)')
plt.legend()


"""
comment：
开仓时间延后比较好些，51，52表现都提升了
"""




#日内多次开仓模型


list_para10 = [-0.005,0.0012,0.0002,0,50,120]
list_para11 = [-0.005,0.0012,0.0002,95,145,239]
df_backtest10 = baktest2(list_para10,list_para11)
dict_statistic10 = indicators(df_backtest10)


fig,axe= plt.subplots(1,1,figsize=(16,4))
fig.autofmt_xdate()
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(28)) 
axe.plot(df_backtest10['日期'],df_backtest10['net_value']*100,label='net_value(%)')
# axe2 = axe.twinx()
# axe.set_ylabel('净值')
axe.set_xlabel('日期')
axe.set_title('平稳度指数交易模型资产累计收益1(单日多次开仓，阈值=0.0012，开仓时间：开盘50min)')
plt.legend()
