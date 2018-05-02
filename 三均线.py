def init(context):
    #配置策略参数
    context.future_list = ['CU']       #回测品种
    context.target_nums = 3            #回测单开仓手数
    context.fired = False              #是否发送order
    
    # 初始化时订阅合约行情。订阅之后的合约行情会在handle_bar中进行更新。
    # 单一期货策略必须订阅有效期货合约
    subscribe_all(context)
    

# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    context.fired = True
    subscribe_all(context)  #订阅行情
    
    
# 你选择的期货数据更新将会触发此段逻辑，例如日线或分钟线更新
def handle_bar(context, bar_dict):
    #每天记录一次开盘价
    if context.fired == True:
        context.openprice_dict ={}  #命名参数，开盘价
        for future in context.target_list:  #对回测品种中的期货进行循环操作
            context.openprice_dict[future]=bar_dict[future].open  #为什么需要这一步？下一个循环中不是有吗
        context.fired = False
    #主力换月，自行定义
    change_dominate_future(context)   #因为每个月主力合约都会变换，所以月份变化后把以前买的不是主力的换成主力合约
    #换月完成之后、现持仓与目标持仓标的一致
    for i in context.target_list:    #对目标池里的每一项进行测试
        C = history_bars(i,5,'1d','close')
        A4 = sum(C[-5:-1])/4
        A3 = sum(C[-4:-1])/3
        A2 = sum(C[-3:-1])/2
        A4_1 = sum(C[-6:-2])/4
        A3_1 = sum(C[-5:-2])/3
        A2_1 = sum(C[-4:-2])/2

        position = get_position(i,context)  #持仓仓位以及持仓情况
        
        if len(context.future_account.positions.keys())>0:  #已经有仓位
            try:
                if A2 > max(A3,A4) and A2_1 < min(A3_1,A4_1) and position['side'] == 'SELL':  #如果超过买入线，切当时是空头仓位，那么平空仓，买开
                    if position['quantity']>0:
                        buy_close(i,position['quantity'])
                        buy_open(i,position['quantity'])
                if A2 < min(A3,A4) and A2_1 > max(A3_1,A4_1) and position['side'] == 'BUY':  #如果低于卖出线，且当时的仓位是多头仓位，那么平多仓，卖开
                    if position['quantity']>0:
                        sell_close(i,position['quantity'])
                        sell_open(i,position['quantity'])
            except Exception as e:
                logger.error('[信号出现]下单异常:'+str(e))
        else:                                           #还没有仓位
            if A2 > max(A3,A4) and A2_1 < min(A3_1,A4_1):
                buy_open(i,context.target_nums)   #单仓开仓
            if A2 <min(A3,A4) and A2_1 > max(A3_1,A4_1):
                sell_open(i,context.target_nums)

#主力换月
def change_dominate_future(context):
    for future in list(context.future_account.positions.keys()):  #keys是dict的函数，此处是期货名，持仓的期货
        future_sige = future[:-4]  #现有的期货品种
        new_dominate_future = get_dominant_future(future_sige)  #主力合约代码！！！！
        if future == new_dominate_future:  #此处说明主力合约不变
            pass
        else:
            logger.info('[移仓换月]开始')  #打印日志，这是一项运行中打印出来方便观察每个月调仓的代码
            position = get_position(future,context)
            close_action = sell_close if position['side'] =='BUY' else buy_close  #只是一个命名而已！！！类似于typedef
            open_action = buy_open if position['side'] =='BUY' else sell_open
            try:
                close_order = close_action(future,position['quantity'])  #卖出/买入现有持仓
                open_order = open_action(new_dominate_future,position['quantity'])  #买入/卖出当月主力期货

            except Exception as e:
                logger.error('[移仓换月]平仓失败:'+str(e))
            logger.info('[移仓换月]结束')


#单品种持仓状况    
def get_position(future,context):
    position = context.future_account.positions[future]  #仓位情况
    
    if len(context.future_account.positions.keys())>0:  #？
        
        position_side ='SELL' if position.sell_quantity>0 else 'BUY'  #如果空头持仓>0，卖出，否则买入
        position_quantity = position.sell_quantity if position_side == 'SELL' else position.buy_quantity
        
        return {'side':position_side,'quantity':position_quantity}  #side:买卖仓位 quantity:持仓数量
        
    else:
        return {}

#订阅行情
def subscribe_all(context):  #订阅所有行情
    context.target_list = [get_dominant_future(i) for i in context.future_list]  #获取主力合约代码
    print(context.target_list)  #打印主力合约代码
    for future in context.target_list:  
        print(future)  #打印每一个代码
        subscribe(future)  #订阅的行情数据