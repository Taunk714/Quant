start = '2017-01-01'                       # 回测起始时间
end = '2018-01-01'                         # 回测结束时间
universe = DynamicUniverse('HS300')        # 证券池，支持股票、基金、期货、指数四种资产
benchmark = 'HS300'                        # 策略参考标准
freq = 'd'                                 # 策略类型，'d'表示日间策略使用日线回测，'m'表示日内策略使用分钟线回测
refresh_rate = 1                           # 调仓频率，表示执行handle_data的时间间隔，若freq = 'd'时间间隔的单位为交易日，若freq = 'm'时间间隔为分钟
  
# 配置账户信息，支持多资产多账户
accounts = {
    'fantasy_account': AccountConfig(account_type='security', capital_base=10000000)
}
  
def initialize(context):
    pass
  
# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context):    
    previous_date = context.previous_date.strftime('%Y-%m-%d')
     
    # 获取因子PE的的历史数据集，截止到前一个交易日
    hist = context.history(symbol=context.get_universe(exclude_halt=True), attribute='PE', time_range=1, style='tas')[previous_date]
     
    # 将因子值从小到大排序，并取前100支股票作为目标持仓
    signal = hist['PE'].order(ascending=True)
    target_position = signal[:100].index
     
    # 获取当前账户信息
    account = context.get_account('fantasy_account')   
    current_position = account.get_positions(exclude_halt=True)       
     
    # 卖出当前持有，但目标持仓没有的部分
    for stock in set(current_position).difference(target_position):
        account.order_to(stock, 0)
     
    # 根据目标持仓权重，逐一委托下单
    for stock in target_position:
        account.order(stock, 10000)