import pandas as pd
import numpy as np
from CAL.PyCAL import *

start = '2013-05-01'
end = u''
benchmark ='HS300'       
universe = ['510300.XSHG',   # 300 ETF 代替沪深300指数
                   '510500.XSHG',   # 500 ETF 代替中证500指数
                   '511880.XSHG']   # 银华日利
capital_base = 10000
refresh_rate = 1
commission = Commission(0.0, 0.0)

def initialize(account):
    pass

def handle_data(account):

    cal = Calendar('China.SSE')
    dt = Date.fromDateTime(account.current_date)
    last_day_str = cal.advanceDate(dt,'-1B',BizDayConvention.Preceding).strftime("%Y-%m-%d")  # 获取回测当日的前1天日期
    last_20day_str = cal.advanceDate(dt,'-22B',BizDayConvention.Preceding).strftime("%Y-%m-%d") # 获取回测当日的前21天日期
    
    info_1 = DataAPI.MktIdxdGet(ticker='000300',beginDate=last_20day_str,endDate=last_day_str,field='tradeDate,closeIndex')
    info_2 = DataAPI.MktIdxdGet(ticker='000905',beginDate=last_20day_str,endDate=last_day_str,field='tradeDate,closeIndex')
    signal_1 = (info_1['closeIndex'].iloc[-1]-info_1['closeIndex'].iloc[0])/info_1['closeIndex'].iloc[0]
    signal_2 = (info_2['closeIndex'].iloc[-1]-info_2['closeIndex'].iloc[0])/info_2['closeIndex'].iloc[0]
    
    if signal_1 < 0 and signal_2 < 0:
        order_pct_to('510300.XSHG',0)
        order_pct_to('510500.XSHG',0)
        order_pct_to('511880.XSHG',0.99)
    else:
        if signal_1 > signal_2:
            order_pct_to('510500.XSHG',0)
            order_pct_to('511880.XSHG',0)
            order_pct_to('510300.XSHG',0.99)
        if signal_2 > signal_1:
            order_pct_to('510300.XSHG',0)
            order_pct_to('511880.XSHG',0)
            order_pct_to('510500.XSHG',0.99) 