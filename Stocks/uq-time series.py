import numpy as np

start = '2014-01-01'
end   = '2015-01-01'
capital_base = 1000000
refresh_rate = 1
benchmark = 'HS300'
freq = 'd'
universe = ['601169.XSHG', '601328.XSHG']

def initialize(account):
    pass

def handle_data(account):
    
    longest_history = 1
    prices = account.get_attribute_history('closePrice', longest_history)
    stk1, stk2 = universe
    price1= prices[stk1][-1]
    price2= prices[stk2][-1]
    
    buy_list = []
    sell_list = []
    
    if price1-price2 > 1.7452:
        buy_list.append(stk2)
        sell_list.append(stk1)
    if price1-price2 < 1.4573:
        buy_list.append(stk1)
        sell_list.append(stk2)
    if price1-price2 < 0.01 and prc1-prc2 > -0.01 :
        sell_list.append(stk1)
        sell_list.append(stk2)
    hold = []
    buy = [] 
    
    
    for stk in account.valid_secpos:
        if stk in sell_list:
            order_to(stk, 0) 
        else:
            hold.append(stk)
            
    buy = hold
    for stk in buy_list:
        if stk not in hold:
            buy.append(stk)
            
    if len(buy) > 0:
        # 等仓位买入
        amout = account.referencePortfolioValue/len(buy) # 每只股票买入数量
        for stk in buy:
            num = int(amout/account.referencePrice[stk] / 100.0) * 100
            order_to(stk, num)   
             
    return
