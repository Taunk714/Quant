import talib
'''
---------------------------------------------------------------------------
        整体回测前：初始化参数，并定义全局变量
---------------------------------------------------------------------------
'''
def init(context):
    # context内引入全局变量s1
    context.s1 = "600318.XSHG"  #自制主力连续
    subscribe(context.s1)
    
    #定义策略相关参数
    context.qty = True
    context.longterm = 20
    context.k1 = 0
    context.k2 = 0
    context.p1 = 0
    context.p2 = 0
    context.k = 9000
'''
---------------------------------------------------------------------------
        每日开盘前
---------------------------------------------------------------------------
''' 
def before_trading(context):
    context.dayq = context.portfolio.positions[context.s1].quantity
    High = history_bars(context.s1,context.longterm,'1d','high')
    Low = history_bars(context.s1,context.longterm,'1d','low')
    Close = history_bars(context.s1,context.longterm,'1d','close')
    Open = history_bars(context.s1,1,'1d','open')
    context.high = 0
    context.low = 10000
    context.p1 = 0
    context.p2 = 0
    for i in range(0,19):
        if High[i] > context.high:
            context.high = High[i]
            context.k1 = i
        if Low[i] < context.low:
            context.low = Low[i]
            context.k2 = i
    context.maxclose = Close[context.k1]
    context.minclose = Close[context.k2]
    context.AlrBuyRange = abs(High[-1] - Open[-1])/abs(Open[-1]-Close[-1])
    context.AlSellRange = abs(Low[-1] - Open[-1])/abs(Open[-1]-Close[-1])

    
'''
---------------------------------------------------------------------------
        每日交易时
---------------------------------------------------------------------------
''' 
def handle_bar(context, bar_dict):


# 2. 根据开盘前计算得到指标，判断是否发出信号
    qty = context.portfolio.positions[context.s1].quantity
    ds1 = context.dayq
    op0 = bar_dict[context.s1].open
    cl0 = bar_dict[context.s1].close
    cl = history_bars(context.s1,3,'1d','close')
    op = history_bars(context.s1,3,'1d','open')
    C = history_bars(context.s1,10, '1d','close')
    a1 = cl[0]
    a2 = cl[1]
    a3 = cl[2]

    
    #短期指数平均线
    context.AvgMa5 = sum(C[5:10])/5
    context.AvgMa10 = sum(C[0:10])/10

    #卖出
    if op[0] > cl[0] and op[1] > cl[1] and  op[2] > cl[2]:
        if cl0 > context.AvgMa5:
            order_shares(context.s1,-context.k)
        elif cl0 < context.AvgMa5 and cl0 > context.AvgMa10:
            pass
        else:
            order_lots(context.s1,-context.k)
    elif context.AlrBuyRange < 4 and context.AlrBuyRange > 3.5 and ds1 != 0 and op[-1] > cl[-1]:
        order_shares(context.s1,-context.k)

    #买入
    if op[0] < cl[0] and op[1] < cl[1] and  op[2] < cl[2] and cl0 > context.AvgMa5 and qty == 0 and ds1 ==0:
        order_shares(context.s1,context.k)