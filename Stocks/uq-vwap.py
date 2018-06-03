start = '2013-08-01'                     # 回测起始时间
end = '2016-08-01'                       # 回测结束时间
universe = DynamicUniverse('SH50')       # 证券池，支持股票和基金、期货
benchmark = 'SH50'                       # 策略参考基准
freq = 'd'                               # 'd'表示使用日频率回测，'m'表示使用分钟频率回测
refresh_rate = 1                         # 执行handle_data的时间间隔

threshold = 0.05
accounts = {
    'stock_account': AccountConfig(account_type='security', capital_base=100000) #security 股票和基金
}

def initialize(context):                 # 初始化策略运行环境
    pass

def handle_data(context):                # 核心策略逻辑
    current_universe = context.get_universe(exclude_halt=True)  #exclude_halt 去除停牌股票，默认为false
    
    data = context.history(symbol=current_universe, time_range=5, attribute=['turnoverValue', 'turnoverVol', 'lowPrice'], style='sat') #sat表示顺序，s为key
    
    stock_account = context.get_account('stock_account')    #现在的账户情况
    current_positions = stock_account.get_positions(exclude_halt=True) #账户所有资产组合的持仓情况 

'''
if get_position() 意味着某一种资产的持仓情况
'''
    
    for stock in current_universe:  #股票池循环
        hist = data[stock]
        vwap30 = sum(hist['turnoverValue']) / sum(hist['turnoverVol'])  #成交额之和/成交量之和
        if hist['lowPrice'][-1] < vwap30 * (1-threshold) and stock not in current_positions: #未持仓而且最低价低于平均成本的95%
            stock_account.order(stock, 100)
        elif hist['lowPrice'][-1] >= vwap30 and stock in current_positions: #持仓并且最低价大于平均成本
            stock_account.order_to(stock, 0)