import numpy as np
import pandas as pd
import math
from statsmodels import regression
import statsmodels.api as sm
import talib
import rqdatac

def init(context):
    context.flag = 0
    scheduler.run_monthly(rebalance,8) 

def handle_bar(context,bar_dict):
    if not context.flag:
        rebalance(context,bar_dict)
        context.flag = 1
    
def rebalance(context,bar_dict):
    stocks = filter_paused(all_instruments(type="CS").order_book_id)
    stocks = filter_st(stocks)
    stocks = filter_new(stocks)
    fundamental_df = get_fundamentals(
        query(
            fundamentals.eod_derivative_indicator.pb_ratio,
            fundamentals.eod_derivative_indicator.market_cap
        ).filter(
            fundamentals.income_statement.stockcode.in_(stocks)
        )
    ).T.dropna()
    
    fundamental_df['BP'] = 1/fundamental_df['pb_ratio']
    BP_no_extreme = filter_extreme_3sigma(fundamental_df['BP'])
    new_BP = neutralization(BP_no_extreme,fundamental_df['market_cap'])
    
    q = new_BP.quantile(0.99)
    stock_list = new_BP[new_BP >= q].index
    context.stock_list = stock_list
    context.last_main_symbol = context.portfolio.positions
    context.delete = set(context.last_main_symbol).difference(context.stock_list)
    if len(context.delete)!=0:
        print('调仓')
        for stk in context.delete:
            order_target_percent(stk,0)
    for stock in context.stock_list:
        order_target_percent(stock,0.99/len(context.stock_list))

# 过滤停牌股票
def filter_paused(stock_list):
    return [stock for stock in stock_list if not is_suspended(stock)] 

def filter_st(stock_list):
    return [stock for stock in stock_list if not is_st_stock(stock)]
    
def filter_new(stock_list):
    return [stock for stock in stock_list if instruments(stock).days_from_listed() >= 180]

#离群值处理
def filter_extreme_3sigma(series,n=3): #3 sigma
  mean = series.mean()
  std = series.std()
  max_range = mean + n*std
  min_range = mean - n*std
  return np.clip(series,min_range,max_range)
  
# 提供日期输入参数，在当前日期下，如果股票尚未上市，则行业暴露度为NaN
# 若股票无法在申万行业中找到分类，则行业暴露度设为NaN
def get_industry_exposure(order_book_ids):
    SHENWAN_INDUSTRY_MAP = {
        "801010.INDX": "农林牧渔",
        "801020.INDX": "采掘",
        "801030.INDX": "化工",
        "801040.INDX": "钢铁",
        "801050.INDX": "有色金属",
        "801080.INDX": "电子",
        "801110.INDX": "家用电器",
        "801120.INDX": "食品饮料",
        "801130.INDX": "纺织服装",
        "801140.INDX": "轻工制造",
        "801150.INDX": "医药生物",
        "801160.INDX": "公用事业",
        "801170.INDX": "交通运输",
        "801180.INDX": "房地产",
        "801200.INDX": "商业贸易",
        "801210.INDX": "休闲服务",
        "801230.INDX": "综合",
        "801710.INDX": "建筑材料",
        "801720.INDX": "建筑装饰",
        "801730.INDX": "电气设备",
        "801740.INDX": "国防军工",
        "801750.INDX": "计算机",
        "801760.INDX": "传媒",
        "801770.INDX": "通信",
        "801780.INDX": "银行",
        "801790.INDX": "非银金融",
        "801880.INDX": "汽车",
        "801890.INDX": "机械设备"
    }
    df = pd.DataFrame(index=SHENWAN_INDUSTRY_MAP.keys(), columns=order_book_ids)
    for stk in order_book_ids:
        try:
            df[stk][rqdatac.instruments(stk).shenwan_industry_code] = 1
            
        except:
            continue
    return df.fillna(0)#将NaN赋为0
  
# 需要传入单个因子值和总市值
def neutralization(factor,mkt_cap):
    y = factor
    LnMktCap = mkt_cap.apply(lambda x:math.log(x))
    dummy_industry = get_industry_exposure(factor.index)
    x = pd.concat([LnMktCap,dummy_industry.T],axis = 1)
    result = sm.OLS(y.astype(float),x.astype(float)).fit()
    return result.resid
