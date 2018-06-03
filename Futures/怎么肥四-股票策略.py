import talib
'''
---------------------------------------------------------------------------
        整体回测前：初始化参数，并定义全局变量
---------------------------------------------------------------------------
'''
def init(context):
    # context内引入全局变量s1
    context.symbol = 'J'
    context.s1 = get_dominant_future(context.symbol)#自制主力连续
    # 初始化context.last_main_symbol
    context.last_main_symbol = context.s1
    # 将判断主力是否更新的flag初始设置为False
    context.main_changed = False
    subscribe(context.s1)
    
    #定义策略相关参数
    context.sign1 = 0 #记录虚拟交易的买入价
    context.sign2 = 0
    context.flag1 = False #记录是否发生虚拟交易
    context.flag2 = False
    context.qty = True
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

    context.days = context.portfolio.positions[context.s1].sell_quantity
    context.dayb = context.portfolio.positions[context.s1].buy_quantity

        



# 主力合约发生切换时进行移仓
def change_to_newmain(context):
    # 主力合约发变化，平仓
    print ('Symbol Changed! before:', context.last_main_symbol, 'after: ', context.s1, context.now)
    # 空单平仓
    if context.portfolio.positions[context.last_main_symbol].sell_quantity !=0:
        buy_close(context.last_main_symbol,25)
        print ('close short:', context.now)
        sell_open(context.s1,25)
    # 多头平仓
    if context.portfolio.positions[context.last_main_symbol].buy_quantity!= 0:
        sell_close(context.last_main_symbol,25)
        print ('close long', context.now)
        buy_open(context.s1,25)
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
    ds1 = context.days
    db1 = context.dayb
    op0 = bar_dict[context.s1].open
    cl0 = bar_dict[context.s1].close
    cl = history_bars(context.s1,3,'1d','close')
    op = history_bars(context.s1,3,'1d','open')
    C = history_bars(context.s1,10, '1d','close')
    a1 = cl[0]
    a2 = cl[1]
    a3 = cl[2]

    
    #短期指数平均线
    context.AvgMa5 = talib.EMA(C,5)
    context.AvgMa10 = talib.EMA(C,10)
    
#-------------------多头持仓---------------------------------
    #多头空仓
    if op[0] > cl[0] and op[1] > cl[1] and  op[2] > cl[2] and buy_qty != 0:
        if cl0 > context.AvgMa5[-1]:
            sell_close(context.s1,25,price = bar_dict[context.s1].close)
            sell_open(context.s1,25,price = bar_dict[context.s1].close)
        elif cl0 < context.AvgMa5[-1] and cl0 > context.AvgMa10[-1]:
            pass
        else:
            sell_close(context.s1,25,price = bar_dict[context.s1].close)

#-------------------空头持仓---------------------------------
    #空头平仓

    if op[0] < cl[0] and op[1] < cl[1] and  op[2] < cl[2] and sell_qty != 0:
        if cl0 < context.AvgMa5[-1]:
            buy_close(context.s1,25,price = bar_dict[context.s1].close)
            buy_open(context.s1,25,price = bar_dict[context.s1].close)
        elif cl0 > context.AvgMa5[-1] and cl0 < context.AvgMa10[-1]:
            pass
        else:
            buy_close(context.s1,25,price = bar_dict[context.s1].close)
#-------------------开仓-------------------------------------
    #多头开仓
    if a1 < a2 and a2 < a3 and cl0 > context.AvgMa5[-1] and sell_qty == 0 and buy_qty == 0 and db1 ==0 and ds1 ==0:
        buy_open(context.s1,25,price = bar_dict[context.s1].close)    
    if a1 > a2 and a2 > a3 and cl0 < context.AvgMa5[-1] and sell_qty == 0 and buy_qty == 0 and db1 == 0 and ds1 == 0:
        sell_open(context.s1,25,price = bar_dict[context.s1].close)    

