import talib
'''
---------------------------------------------------------------------------
        整体回测前：初始化参数，并定义全局变量
---------------------------------------------------------------------------
'''
def init(context):
    # context内引入全局变量s1
    context.symbol = 'J'
    context.continuous = context.symbol + '88' #平台提供的主力连续合约，但模拟交易中无法交易此合约
    context.s1 = get_dominant_future(context.symbol)#自制主力连续
    # 初始化context.last_main_symbol
    context.last_main_symbol = context.s1
    # 将判断主力是否更新的flag初始设置为False
    context.main_changed = False
    subscribe(context.s1)
    
    #定义策略相关参数
    context.FastLen = 9 #短期指数平均线参数
    context.SlowLen = 19 #长期指数平均线参数
    context.RSILen = 9 #RSI参数
    context.OverSold = 30 #超卖
    context.OverBought = 70 #超买
    context.sign1 = 0 #记录虚拟交易的买入价
    context.sign2 = 0
    context.flag1 = False #记录是否发生虚拟交易
    context.flag2 = False
    
'''
---------------------------------------------------------------------------
        每日开盘前
---------------------------------------------------------------------------
''' 
def before_trading(context):
# 1. 判断主力合约是否更新
    context.s1 = get_dominant_future('J')
    if context.last_main_symbol != context.s1:
        subscribe(context.s1)
        # 如果更新了，设置main_changed这个flag为True
        context.main_changed = True
        
# 2. 以'88'主力连续合约来计算指标
    close = history_bars(context.continuous,context.SlowLen + 1,'1d','close')
    high = history_bars(context.continuous,context.SlowLen + 1, '1d','high')
    low = history_bars(context.continuous,context.SlowLen + 1,'1d','low')
    
    #短期指数平均线
    context.AvgValue1 = talib.EMA(close,context.FastLen)
    #长期指数平均线
    context.AvgValue2 = talib.EMA(close,context.SlowLen)
    #计算RSI
    context.RSI = talib.RSI(close,context.RSILen)[-1]
    
    #唐奇安通道上轨：前N个Bar的最大最高价
    context.buyPoint = max(high[-20:])
    #唐奇安通道下轨：前N个Bar的最小最低价
    context.sellPoint = min(low[-20:])

# 主力合约发生切换时进行移仓
def change_to_newmain(context):
    # 主力合约发变化，平仓
    print ('Symbol Changed! before:', context.last_main_symbol, 'after: ', context.s1, context.now)
    # 空单平仓
    if context.portfolio.positions[context.last_main_symbol].sell_quantity !=0:
        buy_close(context.last_main_symbol,10)
        print ('close short:', context.now)
        sell_open(context.s1,10)
    # 多头平仓
    if context.portfolio.positions[context.last_main_symbol].buy_quantity!= 0:
        sell_close(context.last_main_symbol,10)
        print ('close long', context.now)
        buy_open(context.s1,10)
    context.main_changed = False
    context.last_main_symbol = context.s1
    
'''
---------------------------------------------------------------------------
        每日交易时
---------------------------------------------------------------------------
''' 
def handle_bar(context, bar_dict):

# 1. 先检测当前主力合约，如果发生变化，先对原有合约平仓
    if context.main_changed:
        change_to_newmain(context)

# 2. 根据开盘前计算得到指标，判断是否发出信号
    sell_qty = context.portfolio.positions[context.s1].sell_quantity
    buy_qty = context.portfolio.positions[context.s1].buy_quantity
    
# ------------------------------- 多头部分-------------------------------    
    if  buy_qty == 0 and sell_qty ==0 and context.AvgValue1[-1] > context.AvgValue2[-1] and context.RSI < context.OverBought and bar_dict[context.continuous].high > context.buyPoint:
        #多头虚拟开仓：短期均线在长期均线之上、RSI低于超卖值，并且创新高
        if context.flag1 == False:
            context.sign1 = bar_dict[context.continuous].close #设为当前的bar的收盘价
            context.flag1 = True  
        #多头开仓：虚拟交易发生过一次亏损、短期均线在长期均线之上、RSI低于超卖值，并且创新高
        elif context.sign1 < bar_dict[context.continuous].close:
            buy_open(context.s1,10)
            context.flag1 = False
    
    #多头平仓：下破唐奇安通道下轨
    if buy_qty !=0 and bar_dict[context.continuous].close <= context.sellPoint:
        sell_close(context.s1,10)
        
# ------------------------------- 空头部分-------------------------------            
    if  buy_qty == 0 and sell_qty ==0 and context.AvgValue1[-1] < context.AvgValue2[-1] and context.RSI > context.OverSold and bar_dict[context.continuous].low < context.sellPoint:
        #空头虚拟开仓：短期均线在长期均线之下、RSI高于超卖值，并且创新低
        if context.flag2 == False:
            context.sign2 = bar_dict[context.continuous].close #设为当前的bar的收盘价
            context.flag2 = True  
        #空头开仓：虚拟交易发生过一次亏损、短期均线在长期均线之下、RSI高于超买值，并且创新低
        elif context.sign2 > bar_dict[context.continuous].close :
            sell_open(context.s1,10)
            context.flag2 = False
    
    #空头平仓：上破唐奇安通道上轨
    if sell_qty!=0 and bar_dict[context.continuous].close >= context.buyPoint:
        buy_close(context.s1,10)