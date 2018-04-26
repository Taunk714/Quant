# 均线策略虽然比较简单，但是常常在期货市场具有很好的效果。这是由于趋势在市场的广泛存在：
# 1.期货市场的fat tail 特征，从而跟随趋势能得到超过随机分布的收益率
# 2.基本面信息，尤其是政策具有延续性，使资产的价格也具有延续性趋势
# 3.市场非有效，信息扩散需要时间，因此达到合理价格也需要一定时间
# 4.资金推动，加大趋势延续时间

# 可以自己import我们平台支持的第三方python模块，比如pandas、numpy等。
import talib         #talib是用来计算行情数据技术指标的库

# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    context.symbol = 'J'   #选取交易品种
    context.s1 = get_dominant_future(context.symbol)#自制主力连续
    context.last_main_symbol = context.s1  
    context.len_long=120   #长均线周期
    context.len_short=30   #短均线周期  
    # 将判断主力是否更新的flag初始设置为False
    context.main_changed = False
    
    # 初始化时订阅合约行情。订阅之后的合约行情会在handle_bar中进行更新。
    subscribe(context.s1)
    # 实时打印日志
    logger.info("RunInfo: {}".format(context.run_info))

# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context): #每天开盘前判断主力合约是否更新。
    context.s1 = get_dominant_future(context.symbol)
    if context.last_main_symbol != context.s1:
        subscribe(context.s1)
        # 如果更新了，设置main_changed这个flag为True
        context.main_changed = True

#定义更换主力合约的函数
def change_to_newmain(context):
    # 主力合约发变化，平仓
    print ('Symbol Changed! before:', context.last_main_symbol, 'after: ', context.s1, context.now)
    # 空单平仓，并在新的主力合约上开空单
    if context.portfolio.positions[context.last_main_symbol].sell_quantity !=0:
        buy_close(context.last_main_symbol,1)
        print ('close short:', context.now)
        sell_open(context.s1,1)
    # 多头平仓，并在新的主力合约上开多单
    if context.portfolio.positions[context.last_main_symbol].buy_quantity!= 0:
        sell_close(context.last_main_symbol,1)
        print ('close long', context.now)
        buy_open(context.s1,1)
    context.main_changed = False
    context.last_main_symbol = context.s1

# 你选择的期货数据更新将会触发此段逻辑，例如日线或分钟线更新
def handle_bar(context, bar_dict):
    
    # 检测当前主力合约，如果发生变化，先对原有合约平仓
    if context.main_changed:
        change_to_newmain(context)
    
    
    #计算长短均线
    close=history_bars(context.s1,context.len_long,'1m','close')
    longMA=talib.MA(close,context.len_long)
    shortMA=talib.MA(close,context.len_short)
    
    #获取当前持有的多仓和空仓
    buy_qty=context.portfolio.positions[context.s1].buy_quantity
    sell_qty=context.portfolio.positions[context.s1].sell_quantity
    
    #若短均线高于长均线，则保持仓位为1手多仓
    if shortMA[-1]>longMA[-1] and buy_qty==0:
        order_to(context.s1,1)
    #若短均线低于长均线，则保持仓位为1手空仓
    if shortMA[-1]<longMA[-1] and sell_qty==0:
        order_to(context.s1,-1)

# after_trading函数会在每天交易结束后被调用，当天只会被调用一次    
def after_trading(context):
    pass
