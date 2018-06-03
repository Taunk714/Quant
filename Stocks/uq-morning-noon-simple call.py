start = '2009-03-01'                       # 回测起始时间
end = '2016-10-12'                         # 回测结束时间

benchmark = 'ZZ500'                        # 策略参考标准
universe = set_universe('A')               # 静态股票池，全A股
capital_base = 10000000                    # 起始资金
freq = 'd'                                 # 策略类型，'d'表示日间策略使用日线回测
refresh_rate = 10                           # 调仓频率，表示执行handle_data的时间间隔

factor_data = pd.read_csv('APM_FullA.csv')     # 读取因子数据
factor_data = factor_data[factor_data.columns[:]].set_index('tradeDate')
factor_dates = factor_data.index.values

quantile_ten = 10                           # 选取股票的因子十分位数，1表示选取股票池中因子最小的10%的股票
commission = Commission(0.0002,0.0002)     # 交易费率设为双边万分之二

def initialize(account):                   # 初始化虚拟账户状态
    pass

def handle_data(account):                  # 每个交易日的买入卖出指令
    pre_date = account.previous_date.strftime("%Y-%m-%d")
    if pre_date not in factor_dates:            # 因子只在每个月底计算，所以调仓也在每月最后一个交易日进行
        return
    
    # 拿取调仓日前一个交易日的因子，并按照相应十分位选择股票
    q = factor_data.ix[pre_date].dropna()
    q_min = q.quantile((quantile_ten-1)*0.1)
    q_max = q.quantile(quantile_ten*0.1)
    my_univ = q[q>=q_min][q<q_max].index.values
    
    # 调仓逻辑
    univ = [x for x in my_univ if x in account.universe]
    
    # 不在股票池中的，清仓
    for stk in account.valid_secpos:
        if stk not in univ:
            order_to(stk, 0)
    # 在目标股票池中的，等权买入
    for stk in univ:
        order_pct_to(stk, 1.1/len(univ))