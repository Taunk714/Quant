import talib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import quartz_futures as qf
from quartz_futures.api import *

all_perf = []
all_bt = []
backtest_universe = ['IH1612', 'IF1612', 'IC1612', 'rb1612', 'zn1612', 'cu1612']
multi= [300, 300, 200, 10, 5, 5]
for i in range(len(backtest_universe)):
    universe = [backtest_universe[i]]
    start = "2016-05-01"                 # 回测开始时间
    end   = "2016-08-05"                 # 回测结束时间
    capital_base = 1500000               # 初始可用资金
    refresh_rate = 1                     # 算法调用周期
    freq = 'd'
    commission = 0.3/10000
    len_window = 10
​
    def initialize(context):
        context.portfolio_value = []
​
    def handle_data(context):
        symbol = get_symbol(universe[0])
        #print '\n'
        context.portfolio_value.append(context.cash+context.position.get(symbol, dict()).get('long_margin', 0)+
                                           context.position.get(symbol, dict()).get('short_margin', 0))
        #print context.current_date, context.current_time, symbol
        #print(context.portfolio_value[-1])

        data = get_symbol_history(symbol=symbol, field='closePrice', time_range=len_window+1)
        closeprice_20 = np.array(data[symbol]['closePrice'], dtype='float') #20天的收盘价
        ma_20_1= talib.MA(closeprice_20,len_window)[-1]
        ma_20_2 = talib.MA(closeprice_20,len_window)[-2]
        std_20_1 = closeprice_20[1:].std()
        std_20_2 = closeprice_20[:-1].std()
    
        bolling_up_1 = ma_20_1+1*std_20_1
        bolling_down_1 = ma_20_1-1*std_20_1
        bolling_up_2 = ma_20_2+1*std_20_2
        bolling_down_2 = ma_20_2-1*std_20_2
        close_1 = closeprice_20[-1]
        close_2 = closeprice_20[-2]
​
        #print '布林线上通道:', bolling_up_1, ';', '布林线下通道：', bolling_down_1, ';', '昨日收盘：', close_1
        long_position = context.position.get(symbol, dict()).get('long_position', 0)
        short_position = context.position.get(symbol, dict()).get('short_position', 0)
        amount = int(context.cash/(closeprice_20[-1]*multi[i]*0.3))
        if close_1 > bolling_up_1 and close_2 < bolling_up_1 and bolling_up_1 > bolling_up_2 and bolling_down_1 > bolling_down_2:
            if short_position < amount :
                #print context.current_date, context.current_time, '卖出开仓'
                order(symbol, -amount, 'open')
            if long_position > 0:
                #print context.current_date, context.current_time, '卖出平仓'
                order(symbol, -long_position, 'close')
        if close_1 <= bolling_down_1 and close_2 > bolling_down_2 and bolling_up_1 < bolling_up_2 and bolling_down_1 < bolling_down_2:
            if short_position > 0:
                #print context.current_date, context.current_time,'买入平仓'
                order(symbol, short_position, 'close')
            if long_position < amount:
                #print context.current_date, context.current_time, '买入开仓'
                order(symbol, amount, 'open')
        #print '仓位：', context.position
        #print '现金：', context.cash
        #print '组合价值：', context.portfolio_value[-1]
    
        # 止盈止损
        if len(context.portfolio_value) >= 2:
            returns = context.portfolio_value[-1]/context.portfolio_value[-2]
            #print(returns)
            if returns > 1.01:
                if long_position > 0:
                    #print context.current_date, context.current_time,'止盈：卖出平仓'
                    order(symbol, -long_position, 'close')
                if short_position > 0:
                    #print context.current_date, context.current_time,'止盈：买入平仓'
                    order(symbol, short_position, 'close')
            if returns < 0.99:
                if long_position > 0:
                    #print context.current_date, context.current_time,'止损：卖出平仓'
                    order(symbol, -long_position, 'close')
                if short_position > 0:
                    #print context.current_date, context.current_time,'止损：买入平仓'
                    order(symbol, short_position, 'close')
        
    bt, perf = qf.backtest.backtest(universe=universe, start=start, end=end,
                                initialize=initialize, handle_data=handle_data,
                                capital_base=capital_base, refresh_rate=refresh_rate,
                                freq=freq)
    all_perf.append(perf)
    all_bt.append(bt)