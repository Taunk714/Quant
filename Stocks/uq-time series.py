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
    
    longest_history = 1		#日期
    prices = account.get_attribute_history('closePrice', longest_history) #获取收盘价,自行定义了一个收盘价list
    stk1, stk2 = universe		#stk1 = ‘601169.XSHG’ stk2 = ‘601328.XSHG’
    price1= prices[stk1][-1]
    price2= prices[stk2][-1]
    
    buy_list = []		#定义了两个list
    sell_list = []
    
    if price1-price2 > 1.7452:		#stk1-stk2
        buy_list.append(stk2)	#增加元素，买列表
        sell_list.append(stk1)
    if price1-price2 < 1.4573:
        buy_list.append(stk1)
        sell_list.append(stk2)
    if price1-price2 < 0.01 and prc1-prc2 > -0.01 :
        sell_list.append(stk1)
        sell_list.append(stk2)
    hold = []	#定义持仓
    buy = [] 
    
    
    for stk in account.valid_secpos:
        if stk in sell_list:	#如果目前持仓股票
            order_to(stk, 0) 
        else:
            hold.append(stk) #如果不在卖出列表中，则将其添加到当前持仓list中
            
    buy = hold
    for stk in buy_list:		
        if stk not in hold:		#如果买入票不在现有持仓中，则添加到现有持仓中
            buy.append(stk)
            
    if len(buy) > 0:		
        # 等仓位买入
        amout = account.referencePortfolioValue/len(buy) # 每只股票买入数量
        for stk in buy:
            num = int(amout/account.referencePrice[stk] / 100.0) * 100
            order_to(stk, num)   
             
    return
