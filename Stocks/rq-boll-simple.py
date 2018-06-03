# 可以自己import我们平台支持的第三方python模块，比如pandas、numpy等。
import talib
import numpy as np
import pandas as pd
# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # 在context中保存全局变量
    context.s1 = "000002.XSHE"
    context.TIMEPERIOD = 12
    context.UP = 2
    context.DN = 2
    context.OBSERVATION = 100
    # 实时打印日志
    logger.info("RunInfo: {}".format(context.run_info))

# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    prices = history_bars(context.s1, context.OBSERVATION, '1d', 'close')
    upper,middle,lower = talib.BBANDS(prices,timeperiod=context.TIMEPERIOD,nbdevup=context.UP,nbdevdn=context.DN,matype=0)
    #logger.info(str(middle))
    #logger.info(history_bars(context.s1, 10, '1d', ['datetime','open','high','low','close','volume']))

# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    # 开始编写你的主要的算法逻辑
    price = history_bars(context.s1, 10, '1d', ['datetime','open','high','low','close','volume'])
    open = price['open']
    high = price['high']
    low = price['low']
    close = price['close']
    date_time = price['datetime']
    logger.info(open)
    #if current_price>=upper[-1] and current_position >=0:
    #    order_target(stock,0)
    #elif current_price<=lower[-1]and current_position<=0:
    #    number_of_shares = int(cash/)
    # bar_dict[order_book_id] 可以拿到某个证券的bar信息
    # context.portfolio 可以拿到现在的投资组合信息

    # 使用order_shares(id_or_ins, amount)方法进行落单

    # TODO: 开始编写你的算法吧！
    order_shares(context.s1, 1000)

# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    pass
    