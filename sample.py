def init(context):
    #配置策略参数
    context.future_list = ['CU','M']   #回测品种
    context.target_nums = 3            #回测单开仓手数
    context.K1=0.5                     #回测参数K1——决定上界的参数
    context.K2=0.5                     #回测参数K2——决定下界的参数
    context.fired = False              #是否发送order
    
    # 初始化时订阅合约行情。订阅之后的合约行情会在handle_bar中进行更新。
    # 单一期货策略必须订阅有效期货合约
    subscribe_all(context)
    

# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    context.fired = True
    subscribe_all(context)
    
    
# 你选择的期货数据更新将会触发此段逻辑，例如日线或分钟线更新
def handle_bar(context, bar_dict):
    K1 = context.K1    #决定上届的参数
    K2 = context.K2    #决定下届的参数
    #每天记录一次开盘价
    if context.fired == True:
        context.openprice_dict ={}  #命名参数，开盘价
        for future in context.target_list:  #对回测品种中的期货进行循环操作
            context.openprice_dict[future]=bar_dict[future].open
        context.fired = False
    #主力换月，自行定义
    change_dominate_future(context)
    #换月完成之后、现持仓与目标持仓标的一致
    for i in context.target_list:    #对目标池里的每一项进行测试
        range = cal_range(i,4)  #自己定义的函数
        open_price = context.openprice_dict[i]
        current_price = bar_dict[i].close
        buy_line = open_price+K1*range
        sell_line = open_price-K2*range
        position = get_position(i,context)
        
        if len(context.future_account.positions.keys())>0:
            try:
                if current_price > buy_line and position['side'] == 'SELL':
                    if position['quantity']>0:
                        buy_close(i,position['quantity'])
                        buy_open(i,position['quantity'])
                if current_price < sell_line and position['side'] == 'BUY':
                    if position['quantity']>0:
                        sell_close(i,position['quantity'])
                        sell_open(i,position['quantity'])
            except Exception as e:
                logger.error('[信号出现]下单异常:'+str(e))
        else:
            if current_price >buy_line:
                buy_open(i,context.target_nums)
            if current_price <sell_line:
                sell_open(i,context.target_nums)
#计算Range    
def cal_range(stock,N):
    
    High = history_bars(stock,N,'1d','high')
    Low = history_bars(stock,N,'1d','low')
    Open = history_bars(stock,N,'1d','open')
    Close = history_bars(stock,N,'1d','close')
    
    HH = max(High[:-1])
    LL = min(Low[:-1])
    LC = min(Close[:-1])
    HC = max(Close[:-1])
    
    range = max((HH-LC),(HC-LL))

    return range

#主力换月
def change_dominate_future(context):
    for future in list(context.future_account.positions.keys()):
        future_sige = future[:-4]
        new_dominate_future = get_dominant_future(future_sige)
        if future == new_dominate_future:
            pass
        else:
            logger.info('[移仓换月]开始')
            position = get_position(future,context)
            close_action = sell_close if position['side'] =='BUY' else buy_close
            open_action = buy_open if position['side'] =='BUY' else sell_open
            try:
                close_order = close_action(future,position['quantity'])
                open_order = open_action(new_dominate_future,position['quantity'])

            except Exception as e:
                logger.error('[移仓换月]平仓失败:'+str(e))
            logger.info('[移仓换月]结束')


#单品种持仓状况    
def get_position(future,context):
    position = context.future_account.positions[future]
    
    if len(context.future_account.positions.keys())>0:
        
        position_side ='SELL' if position.sell_quantity>0 else 'BUY'
        position_quantity = position.sell_quantity if position_side == 'SELL' else position.buy_quantity
        
        return {'side':position_side,'quantity':position_quantity}
        
    else:
        return {}

#订阅行情
def subscribe_all(context):
    context.target_list = [get_dominant_future(i) for i in context.future_list]
    print(context.target_list)
    for future in context.target_list:
        print(future)
        subscribe(future)