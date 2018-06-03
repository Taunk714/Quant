#交易标的螺纹钢、铁矿石、甲醇、镍、PTA、热卷、豆粕、橡胶
import talib as ta
def clearance(context,bar_dict,ID):#空仓函数
    l_RB=get_future_contracts(ID)
    f_list=l_RB
    for i in f_list:
        xxx=context.portfolio.positions[i].buy_quantity
        yyy=context.portfolio.positions[i].sell_quantity
        if xxx!=0:
            sell_close(i,xxx)
        if yyy!=0:
            buy_close(i,yyy)
def init(context):
    # context内引入全局变量s1
    context.s1 = 0
    context.fired = False
    context.instru=['RB','I','MA','TA','M','RU','HC','NI']
    context.instru2=['TA','M','RU','HC','NI']
    context.lot=10
    context.level='1d'
    context.chang=60
    context.major=0
    context.a=10
    context.b=20
    context.buy_qty1=0
    context.sell_qty1=0
    # 初始化时订阅合约行情。订阅之后的合约行情会在handle_bar中进行更新。
    subscribe([i+str(88) for i in context.instru])
    # 实时打印日志
    logger.info("RunInfo: {}".format(context.run_info))


# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    
    pass


# 你选择的期货数据更新将会触发此段逻辑，例如日线或分钟线更新
def handle_bar(context, bar_dict):
    
    for i in context.instru:
        context.major=i+str(88)
        context.s1=get_dominant_future(i)
        context.buy_qty1 = context.portfolio.positions[context.s1].buy_quantity
        context.sell_qty1 = context.portfolio.positions[context.s1].sell_quantity
        
        p0=history_bars(context.s1,2,context.level,'close')[-1]
        p1=history_bars(context.major,context.a,context.level,'close')
        p1=ta.MA(p1,context.a)[-1]
        p2=history_bars(context.major,context.b,context.level,'close')
        p2=ta.MA(p2,context.b)[-1]
        p3=history_bars(context.major,context.chang,context.level,'close')
        p3=ta.MA(p3,context.chang)[-1]
        
        if p1>p2 and p0>p3 and context.buy_qty1==0:
            buy_open(context.s1,context.lot)
        elif p1<p2 and p0<p3 and context.sell_qty1==0:
            sell_open(context.s1,context.lot)
        else:
            clearance(context,bar_dict,i)
        
        
# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    pass