start = '2013-06-01'                     # 回测起始时间
end = '2018-06-01'                       # 回测结束时间
universe = DynamicUniverse('A')          # 证券池，支持股票和基金、期货
benchmark = 'A'                          # 策略参考基准
freq = 'd'                               # 'd'表示使用日频率回测，'m'表示使用分钟频率回测
refresh_rate = 1                         # 执行handle_data的时间间隔
commission = Commission(0.0002,0.0002)   # trade 
slid

threshold = 0.05
accounts = {
    'stock_account': AccountConfig(account_type='security', capital_base=100000) #security 股票和基金
}


'''
市场风格区分
要不要试着长短期
'''
	timeset_l = 20
	timeset_s = 5

def markettest(context,timeset):  		#examine the global situation,choose which to run
	context.cl_price = context.history(symbol=current_universe, time_range=timeset, attribute=['closePrice'], style='sat') 
	El = 0
	for i in range timeset:
		El = El + abs(context.cl_price['closePrice'][i]-context.cl_price['closePrice'][i-1])
	E = abs(context.cl_price['closePrice'][-1]-context.cl_price['closePrice'][0])/El
	return E

def initialize(context):                 # 初始化策略运行环境
    pass

def handle_data(context):                # 核心策略逻辑
	eff_l = markettest(context,timeset_l)
	eff_s = markettest(context,timeset_s)
    current_universe = context.get_universe(exclude_halt=True)  #exclude_halt 去除停牌股票，默认为false
    univ = [x for x in my_univ if x in account.universe]
    if eff_s < 0.25 and eff_l < 0.10:		#long term waving
    	stgy_waving(current_universe)
    elif eff_l >0.25 and eff_s >0.10:
    	stgy_efficient(current_universe)
    elif eff_s >0.25 and eff_l < 0.05:
    	stgy_box(current_universe)
    else:
    	pass


def stgy_waving(context):

def stgy_efficient(context):

def stgy_box(context):
	if context.cl_price['closePrice'][-1]-context.cl_price['closePrice'][0] > 0:
		if 
		order_pct_to(current_universe,accounts[capital_base]/10)


