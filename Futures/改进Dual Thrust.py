# 可以自己import我们平台支持的第三方python模块，比如pandas、numpy等。
import numpy as np
import talib

# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # context内引入全局变量s1
    context.s1 = "RM88"
    context.s2 = "SR88"
    context.s3 = "I88"
    context.s4 = "RB88"
    context.s5 = "NI88"
    context.s6 = "RU88"
    context.s7 = "TA88"
    context.s8 = "FG88"
    context.s9 = "CS88"
    context.s10 = "MA88"
    
    context.marin_rate = 10
    
    context.day_num = 10
    
    context.init_money = 1000000
    context.per_pinzhong_rate = 0.025
    
    context.pinzhong=[context.s1,context.s2,context.s3,context.s4,context.s5,context.s6,context.s7,context.s8,context.s9,context.s10]
    
    context.money_unit=[10,10,100,10,1,10,5,20,10,10]
    
    context.stdList = []
    context.rangeList = []
    context.openList = []
    
    #dual thrust设置
    context.dual_day = 1
    context.k_high = 0.7
    context.k_low = 0.65
    
    # 初始化时订阅合约行情。订阅之后的合约行情会在handle_bar中进行更新。
    subscribe(context.pinzhong)
    
    # 实时打印日志
    #logger.info("RunInfo: {}".format(context.run_info))


# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):

    context.stdList=[]
    context.rangeList=[]
    #context.openList=[]
    context.openList = []

    for i in range(len(context.pinzhong)):
        close_list=history_bars(context.pinzhong[i],context.day_num,'1d','close')
        # logger.info(close_list)
        context.stdList.append(np.std(close_list))
        
        #计算range
        HH = max(history_bars(context.pinzhong[i],context.dual_day,'1d','high'))
        LL = min(history_bars(context.pinzhong[i],context.dual_day,'1d','low'))
        HC = max(history_bars(context.pinzhong[i],context.dual_day,'1d','close'))
        LC = min(history_bars(context.pinzhong[i],context.dual_day,'1d','close'))
        
        context.rangeList.append(max((HH-LC),(HC-LL)))
        #context.openList.append(np.mean(history_bars(context.pinzhong[i],1,'1d','close')))
        
        
    #logger.info(context.rangeList)


# 你选择的期货数据更新将会触发此段逻辑，例如日线或分钟线更新
def handle_bar(context, bar_dict):
    
    context.openList=[]
    
    for m in range(len(context.pinzhong)):
        
        context.openList.append(history_bars(context.pinzhong[m],1,'1d', 'open'))
        
        price = history_bars(context.pinzhong[m], 2, '1m', 'close')
        
        
        #KD计算
        #price_kdj_high = history_bars(context.pinzhong[m],30,'1m','high')
        #price_kdj_low = history_bars(context.pinzhong[m],30,'1m','low')
        #price_kdj_close = history_bars(context.pinzhong[m],30,'1m','close')
        
        #k,d = talib.STOCH(price_kdj_high,price_kdj_low,price_kdj_close,fastk_period=9,slowk_period=3,slowk_matype=0,slowd_period=3,slowd_matype=0)
        
        #MACD计算
        price_macd = history_bars(context.pinzhong[m], 50, '1m', 'close')
        macd,singal,hist = talib.MACD(price_macd, 12, 26, 9)
        
        #上升趋势中
        if macd[-1]>=singal[-1]*1.01 and macd[-2]-singal[-2]<0:
            if price[-2]<context.openList[m]+context.rangeList[m]*context.k_low and price[-1] >= context.openList[m]+context.rangeList[m]*context.k_low:

                if context.portfolio.positions[context.pinzhong[m]].closable_buy_quantity <=0:
                
                    buy_open(context.pinzhong[m],int(context.init_money*context.per_pinzhong_rate/(context.stdList[m]*context.money_unit[m])))
                
            if price[-2]>context.openList[m]+context.rangeList[m]*context.k_low and price[-1] <= context.openList[m]+context.rangeList[m]*context.k_low:    
            
                sell_close(context.pinzhong[m],context.portfolio.positions[context.pinzhong[m]].closable_buy_quantity)
            
            
            if price[-2] > context.openList[m]-context.rangeList[m]*context.k_high and price[-1] <= context.openList[m]-context.rangeList[m]*context.k_high:
                
                if context.portfolio.positions[context.pinzhong[m]].closable_sell_quantity <=0:
                
                    sell_open(context.pinzhong[m],int(context.init_money*context.per_pinzhong_rate/(context.stdList[m]*context.money_unit[m])))
                
            if price[-2] < context.openList[m]-context.rangeList[m]*context.k_high and price[-1] >= context.openList[m]-context.rangeList[m]*context.k_high:
                
                buy_close(context.pinzhong[m],context.portfolio.positions[context.pinzhong[m]].closable_sell_quantity)

        
        #下降趋势中
        if macd[-1]<=singal[-1]*0.99 and macd[-2]-singal[-2]>0:
            if price[-2]<context.openList[m]+context.rangeList[m]*context.k_high and price[-1] >= context.openList[m]+context.rangeList[m]*context.k_high:

                if context.portfolio.positions[context.pinzhong[m]].closable_buy_quantity <=0:
                
                    buy_open(context.pinzhong[m],int(context.init_money*context.per_pinzhong_rate/(context.stdList[m]*context.money_unit[m])))
            
            if price[-2]>context.openList[m]+context.rangeList[m]*context.k_high and price[-1] <= context.openList[m]+context.rangeList[m]*context.k_high:    
                sell_close(context.pinzhong[m],context.portfolio.positions[context.pinzhong[m]].closable_buy_quantity)
            
        
            if price[-2] > context.openList[m]-context.rangeList[m]*context.k_low and price[-1] <= context.openList[m]-context.rangeList[m]*context.k_low:
                
                if context.portfolio.positions[context.pinzhong[m]].closable_sell_quantity <=0:
                
                    sell_open(context.pinzhong[m],int(context.init_money*context.per_pinzhong_rate/(context.stdList[m]*context.money_unit[m])))
                
            if price[-2] < context.openList[m]-context.rangeList[m]*context.k_low and price[-1] >= context.openList[m]-context.rangeList[m]*context.k_low:
                
                buy_close(context.pinzhong[m],context.portfolio.positions[context.pinzhong[m]].closable_sell_quantity)
        
        #logger.info(context.portfolio.positions[context.pinzhong[m]].buy_pnl)
        
    logger.info(context.portfolio.cash)    
        #止赢条件
        
        
        
            
# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    pass