'''
市场风格区分
要不要试着长短期
'''
	timeset_l = 20
	timeset_s = 5

def markettest(context,timeset)
	cl_price = context.history(symbol=current_universe, time_range=timeset, attribute=['closePrice'], style='sat') 
	El = 0
	for i in range timeset:
		El = El + abs(cl_price[i]-cl_price[i-1])
	E = abs(cl_price[-1]-cl_price[-2])/El
	return E

def initialize(context):                 # 初始化策略运行环境
    pass

def handle_data(context):                # 核心策略逻辑
	eff_l = markettest()
	eff_s = 
    current_universe = context.get_universe(exclude_halt=True)  #exclude_halt 去除停牌股票，默认为false

