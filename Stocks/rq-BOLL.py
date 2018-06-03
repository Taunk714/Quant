# 可以自己import我们平台支持的第三方python模块，比如pandas、numpy等。
import numpy as np
import talib

# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    context.s1 = '000300.XSHG' #需要修改成期货
    update_universe([context.s1]) #更新股票池
    # 实时打印日志
    logger.info("Interested at stock: " + str(context.s1))

# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    # 开始编写你的主要的算法逻辑
    
    prices_close = bar_dict[context.s1].close #得到context.s1的bar信息。此处是收盘价
    prices_open = bar_dict[context.s1].open #开盘价
    curPosition =context.portfolio.positions[context.s1].quantity # 计算现在portfolio中股票的仓位
    data = history_bars(context.s1,20, '1d', 'close', skip_suspended=True, include_now=False) #20天收盘价
    change = data[19]/data[18]
    upper, middle, lower = talib.BBANDS(np.asarray(data), timeperiod=15, nbdevup=1, nbdevdn=1, matype=0)  #boll
    
    upper = upper[-1] #最后一组
    lower = lower[-1]
    if (prices_close+prices_open)/2 < lower and curPosition == 0 and change > 0.97:
        # 价格低于下限时买入
         order_target_percent(context.s1,1)
        
    elif ((prices_close+prices_open)/2 > upper and curPosition != 0) or change < 0.97 :
        # 价格高于上限时卖出
         order_target_percent(context.s1,0)
        
    # bar_dict[order_book_id] 可以拿到某个证券的bar信息
    # context.portfolio 可以拿到现在的投资组合状态信息