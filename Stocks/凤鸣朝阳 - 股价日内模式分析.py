
# coding: utf-8

# # 1. 概述
# 
# 参考方正金工最近的研究报告『凤鸣朝阳：股价日内模式中蕴藏的选股因子』作者：魏建榕，在本文做了一些实现：
# 
# - 七年回测中，简单多头策略年化收益率39.8%，阿尔法25.6%，夏普比率1.21，信息比率2.89

# # 2. 因子计算

# 市场交易其实是在交易者基于已知信息的基础上达成的，而晚上闭市之后产生的各种信息，可能在第二天开盘时达到集中释放。如何去通过市场交易特征去掌握这种信息的集中释放，一篇文章[Exploring Market State and Stock Interactions on the Minute Timescale](http://journals.plos.org/plosone/article?id=10.1371/journal.pone.0149648)给了我们很大的启发。
# 作者在该文章中得到了如图的结果
# 
# ![image](http://odqb0lggi.bkt.clouddn.com/56951770228e5b18d9ba2982/99d10a18-a170-11e6-aa78-f8bc124ed898)
# 
# 中蓝线是个股之间相关系数的平均值，不难发现，下午个股之间的相关性要显著地高于上午。也就是说，上午会集中释放前夜的信息，上午是知情交易者最活跃的时候。怎么样利用这一特征呢，方正的研报中给出了一种方法[凤鸣朝阳](http://mp.weixin.qq.com/s?__biz=MzAwNTA4NTA0OQ==&mid=2653691928&idx=1&sn=a32f670381385add312aa5ac34fdd0e8&chksm=80fa820eb78d0b188c834ed5b9346dd870717ef3c8505a23510869880ef354227375d33d41d3&mpshare=1&scene=1&srcid=1018k7lC31mJarZZapj0ClMg#wechat_redirect)
# 
# 本文中就利用这种方法构造选股因子。

# In[ ]:

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib import rc
rc('mathtext', default='regular')
import seaborn as sns
sns.set_style('white')
from matplotlib import dates
import numpy as np
import pandas as pd
import statsmodels.api as sm
import time
import scipy.stats as st
from CAL.PyCAL import *    # CAL.PyCAL中包含font


# In[ ]:

# 已经将上下午的涨跌幅进行读取保存为文件，方便直接读取

apmret = pd.read_csv('APM_Ret.csv') #上下午涨跌幅

apmret = apmret.set_index(['tradeDate', 'secID']).stack().unstack(level=1) #猜测：set_index的意思是设置索引
apm = pd.DataFrame(index=apmret.index.levels[0], columns=apmret.columns)    #合并
apmret = apmret.apply(lambda x: [ np.NaN if (xx == np.inf) else xx for xx in x])

apmret['mktRet'] = apmret.mean(axis=1)


# **按照研报中的方法计算因子**

# In[ ]:

window = 20

count = 0
for dt in apm.index:
        
    count += 1
    if count % 100 == 0:
        print dt
        
    # 拿取20天的上下午涨跌幅度数据
    dt_data = apmret[apmret.index.get_level_values('tradeDate')<=dt].tail(window*2)
    if len(dt_data) < window*2:
        continue
        
    # 股票涨跌幅和市场涨跌幅
    # 市场涨跌幅为所有股票涨跌幅的简单平均
    stk_ret = dt_data.drop('mktRet', axis=1).values
    mkt_ret = dt_data['mktRet'].values
    
    # 上午、下午涨跌幅和市场数据进行回归
    aa = np.matrix([np.ones_like(range(window*2)), mkt_ret]).T
    bb = stk_ret
    xx = np.linalg.lstsq(aa, bb)[0]
    residuals = bb - aa.dot(xx)
    
    # 上午和下午的回归残差相减
    delta = residuals[0::2,:] - residuals[1::2,:]
    
    # stat衡量上下午残差的差异程度
    stat = np.nanmean(delta, axis=0) * np.sqrt(window) / np.nanstd(delta, axis=0)
    
    apm.ix[dt] = stat
    
apm.to_csv('APM_FullA.csv')


# # 3. 因子截面特征
# 
# ## 3.1 加载数据文件

# In[ ]:

# 提取数据
factor_data = pd.read_csv('APM_FullA.csv')                      # 选股因子
factor_data['tradeDate'] = map(Date.toDateTime, map(DateTime.parseISO, factor_data['tradeDate']))
factor_data = factor_data[factor_data.columns[:]].set_index('tradeDate')

mkt_value_data = pd.read_csv('MarketValues_FullA.csv')                    # 市值数据
mkt_value_data['tradeDate'] = map(Date.toDateTime, map(DateTime.parseISO, mkt_value_data['tradeDate']))
mkt_value_data = mkt_value_data[mkt_value_data.columns[1:]].set_index('tradeDate')

forward_20d_return_data = pd.read_csv('ForwardReturns_W20_FullA.csv')    # 未来20天收益率 
forward_20d_return_data['tradeDate'] = map(Date.toDateTime, map(DateTime.parseISO, forward_20d_return_data['tradeDate']))
forward_20d_return_data = forward_20d_return_data[forward_20d_return_data.columns[1:]].set_index('tradeDate')

backward_20d_return_data = pd.read_csv('BackwardReturns_W20_FullA.csv')  # 过去20天收益率 
backward_20d_return_data['tradeDate'] = map(Date.toDateTime, map(DateTime.parseISO, backward_20d_return_data['tradeDate']))
backward_20d_return_data = backward_20d_return_data[backward_20d_return_data.columns[1:]].set_index('tradeDate')

factor_data[factor_data.columns[0:5]].tail()


# ## 3.2 因子截面特征

# In[ ]:

# 因子历史表现

n_quantile = 10
# 统计十分位数
cols_mean = ['meanQ'+str(i+1) for i in range(n_quantile)]
cols = cols_mean
corr_means = pd.DataFrame(index=factor_data.index, columns=cols)

# 计算相关系数分组平均值
for dt in corr_means.index:
    qt_mean_results = []

    # 相关系数去掉nan
    tmp_factor = factor_data.ix[dt].dropna()
    
    pct_quantiles = 1.0/n_quantile
    for i in range(n_quantile):
        down = tmp_factor.quantile(pct_quantiles*i)
        up = tmp_factor.quantile(pct_quantiles*(i+1))
        mean_tmp = tmp_factor[(tmp_factor<=up) & (tmp_factor>=down)].mean()
        qt_mean_results.append(mean_tmp)
    corr_means.ix[dt] = qt_mean_results


# ------------- 因子历史表现作图 ------------------------

fig = plt.figure(figsize=(12, 6))
ax1 = fig.add_subplot(111)

lns1 = ax1.plot(corr_means.index, corr_means.meanQ1, label='Q1')
lns2 = ax1.plot(corr_means.index, corr_means.meanQ5, label='Q5')
lns3 = ax1.plot(corr_means.index, corr_means.meanQ10, label='Q10')

lns = lns1+lns2+lns3
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, bbox_to_anchor=[0.5, 0.1], loc='', ncol=3, mode="", borderaxespad=0., fontsize=12)
ax1.set_ylabel(u'因子', fontproperties=font, fontsize=16)
ax1.set_xlabel(u'日期', fontproperties=font, fontsize=16)
ax1.set_title(u"因子历史表现", fontproperties=font, fontsize=16)
ax1.grid()


# 可以发现，其实股灾时候这个因子的值也出现一些异常，毕竟是千古跌停奇观

# ## 3.3 因子预测能力初探
# 
# 接下来，我们计算了每一天的因子和之后20日收益的秩相关系数

# In[ ]:

# 计算了每一天的**因子**和**之后20日收益**的秩相关系数

ic_data = pd.DataFrame(index=factor_data.index, columns=['IC','pValue'])

# 计算相关系数
for dt in ic_data.index:
    if dt not in forward_20d_return_data.index:
        continue
        
    tmp_factor = factor_data.ix[dt]
    tmp_ret = forward_20d_return_data.ix[dt]
    fct = pd.DataFrame(tmp_factor)
    ret = pd.DataFrame(tmp_ret)
    fct.columns = ['fct']
    ret.columns = ['ret']
    fct['ret'] = ret['ret']
    fct = fct[~np.isnan(fct['fct'])][~np.isnan(fct['ret'])]
    if len(fct) < 5:
        continue

    ic, p_value = st.spearmanr(fct['fct'],fct['ret'])   # 计算秩相关系数 RankIC
    ic_data['IC'][dt] = ic
    ic_data['pValue'][dt] = p_value
    
ic_data.dropna(inplace=True)    

print 'mean of IC: ', ic_data['IC'].mean(), '；',
print 'median of IC: ', ic_data['IC'].median()
print 'the number of IC(all, plus, minus): ', (len(ic_data), len(ic_data[ic_data.IC>0]), len(ic_data[ic_data.IC<0]))


# 每一天的**因子**和**之后20日收益**的秩相关系数作图

fig = plt.figure(figsize=(16, 6))
ax1 = fig.add_subplot(111)

lns1 = ax1.plot(ic_data[ic_data>0].index, ic_data[ic_data>0].IC, '.r', label='IC(plus)')
lns2 = ax1.plot(ic_data[ic_data<0].index, ic_data[ic_data<0].IC, '.b', label='IC(minus)')

lns = lns1+lns2
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, bbox_to_anchor=[0.6, 0.1], loc='', ncol=2, mode="", borderaxespad=0., fontsize=12)
ax1.set_ylabel(u'相关系数', fontproperties=font, fontsize=16)
ax1.set_xlabel(u'日期', fontproperties=font, fontsize=16)
ax1.set_title(u"因子和之后20日收益的秩相关系数", fontproperties=font, fontsize=16)
ax1.grid()


# 从上面计算结果可知，该因子和之后20日收益的秩相关系数在大部分时间为正，因子对之后20日收益有预测性

# # 4. 历史回测概述
# 
# 本节使用2009年以来的数据对于该选股因子进行回测，进一步简单涉及几个风险因子暴露情况
# 
# ## 4.1 该因子选股的分组超额收益（月度）

# In[ ]:

n_quantile = 10
# 统计十分位数
cols_mean = [i+1 for i in range(n_quantile)]
cols = cols_mean

excess_returns_means = pd.DataFrame(index=factor_data.index, columns=cols)

# 计算因子分组的超额收益平均值
for dt in excess_returns_means.index:
    if dt not in forward_20d_return_data.index:
        continue 
    qt_mean_results = []
    
    tmp_factor = factor_data.ix[dt].dropna()
    tmp_return = forward_20d_return_data.ix[dt].dropna()
    tmp_return = tmp_return[tmp_return<4.0]
    tmp_return_mean = tmp_return.mean()
    
    pct_quantiles = 1.0/n_quantile
    for i in range(n_quantile):
        down = tmp_factor.quantile(pct_quantiles*i)
        up = tmp_factor.quantile(pct_quantiles*(i+1))
        i_quantile_index = tmp_factor[(tmp_factor<=up) & (tmp_factor>=down)].index
        mean_tmp = tmp_return[i_quantile_index].mean() - tmp_return_mean
        qt_mean_results.append(mean_tmp)
        
    excess_returns_means.ix[dt] = qt_mean_results

excess_returns_means.dropna(inplace=True)

# 因子分组的超额收益作图
fig = plt.figure(figsize=(12, 6))
ax1 = fig.add_subplot(111)

excess_returns_means_dist = excess_returns_means.mean()
excess_dist_plus = excess_returns_means_dist[excess_returns_means_dist>0]
excess_dist_minus = excess_returns_means_dist[excess_returns_means_dist<0]
lns2 = ax1.bar(excess_dist_plus.index, excess_dist_plus.values, align='center', color='r', width=0.35)
lns3 = ax1.bar(excess_dist_minus.index, excess_dist_minus.values, align='center', color='g', width=0.35)

ax1.set_xlim(left=0.5, right=len(excess_returns_means_dist)+0.5)
# ax1.set_ylim(-0.008, 0.008)
ax1.set_ylabel(u'超额收益', fontproperties=font, fontsize=16)
ax1.set_xlabel(u'十分位分组', fontproperties=font, fontsize=16)
ax1.set_xticks(excess_returns_means_dist.index)
ax1.set_xticklabels([int(x) for x in ax1.get_xticks()], fontproperties=font, fontsize=14)
ax1.set_yticklabels([str(x*100)+'0%' for x in ax1.get_yticks()], fontproperties=font, fontsize=14)
ax1.set_title(u"因子选股分组超额收益", fontproperties=font, fontsize=16)
ax1.grid()


# 可以看到，该因子选股不同分位数组合的超额收益呈很好的单调性；因子空头收益更显著

# ## 4.2 因子选股的市值分布特征
# 
# 检查因子的小市值暴露情况。因为很多策略因为小市值暴露在A股市场表现优异。

# In[ ]:

# 计算因子分组的市值分位数平均值
def quantile_mkt_values(signal_df, mkt_df):
    n_quantile = 10
    # 统计十分位数
    cols_mean = [i+1 for i in range(n_quantile)]
    cols = cols_mean

    mkt_value_means = pd.DataFrame(index=signal_df.index, columns=cols)

    # 计算相关系数分组的市值分位数平均值
    for dt in mkt_value_means.index:
        if dt not in mkt_df.index:
            continue 
        qt_mean_results = []

        # 相关系数去掉nan和绝对值大于0.97的
        tmp_factor = signal_df.ix[dt].dropna()
        tmp_mkt_value = mkt_df.ix[dt].dropna()
        tmp_mkt_value = tmp_mkt_value.rank()/len(tmp_mkt_value)

        pct_quantiles = 1.0/n_quantile
        for i in range(n_quantile):
            down = tmp_factor.quantile(pct_quantiles*i)
            up = tmp_factor.quantile(pct_quantiles*(i+1))
            i_quantile_index = tmp_factor[(tmp_factor<=up) & (tmp_factor>=down)].index
            mean_tmp = tmp_mkt_value[i_quantile_index].mean()
            qt_mean_results.append(mean_tmp)
        mkt_value_means.ix[dt] = qt_mean_results
    mkt_value_means.dropna(inplace=True)
    return mkt_value_means.mean()
    
# 计算因子分组的市值分位数平均值
origin_mkt_means = quantile_mkt_values(factor_data, mkt_value_data)

# 因子分组的市值分位数平均值作图
fig = plt.figure(figsize=(12, 6))
ax1 = fig.add_subplot(111)

width = 0.3
lns1 = ax1.bar(origin_mkt_means.index, origin_mkt_means.values, align='center', width=width)

ax1.set_ylim(0.3,0.6)
ax1.set_xlim(left=0.5, right=len(origin_mkt_means)+0.5)
ax1.set_ylabel(u'市值百分位数', fontproperties=font, fontsize=16)
ax1.set_xlabel(u'十分位分组', fontproperties=font, fontsize=16)
ax1.set_xticks(origin_mkt_means.index)
ax1.set_xticklabels([int(x) for x in ax1.get_xticks()], fontproperties=font, fontsize=14)
ax1.set_yticklabels([str(x*100)+'0%' for x in ax1.get_yticks()], fontproperties=font, fontsize=14)
ax1.set_title(u"因子分组市值分布特征", fontproperties=font, fontsize=16)
ax1.grid()


# 上图展示，该选股因子并没有明显的小市值暴露；倒是多头组合（第十分位组合）市值略大

# ## 4.3 因子分组选股的一个月反转分布特征

# In[ ]:

n_quantile = 10
# 统计十分位数
cols_mean = [i+1 for i in range(n_quantile)]
cols = cols_mean
hist_returns_means = pd.DataFrame(index=factor_data.index, columns=cols)

# 因子分组的一个月反转分布特征
for dt in hist_returns_means.index:
    if dt not in backward_20d_return_data.index:
        continue 
    qt_mean_results = []
    
    # 去掉nan
    tmp_factor = factor_data.ix[dt].dropna()
    tmp_return = backward_20d_return_data.ix[dt].dropna()
    tmp_return_mean = tmp_return.mean()
    
    pct_quantiles = 1.0/n_quantile
    for i in range(n_quantile):
        down = tmp_factor.quantile(pct_quantiles*i)
        up = tmp_factor.quantile(pct_quantiles*(i+1))
        i_quantile_index = tmp_factor[(tmp_factor<=up) & (tmp_factor>=down)].index
        mean_tmp = tmp_return[i_quantile_index].mean() - tmp_return_mean
        qt_mean_results.append(mean_tmp)
        
    hist_returns_means.ix[dt] = qt_mean_results

hist_returns_means.dropna(inplace=True)

# 一个月反转分布特征作图
fig = plt.figure(figsize=(12, 6))
ax1 = fig.add_subplot(111)
ax2 = ax1.twinx()

hist_returns_means_dist = hist_returns_means.mean()
lns1 = ax1.bar(hist_returns_means_dist.index, hist_returns_means_dist.values, align='center', width=0.35)
lns2 = ax2.plot(excess_returns_means_dist.index, excess_returns_means_dist.values, 'o-r')

ax1.legend(lns1, ['20 day return(left axis)'], loc=2, fontsize=12)
ax2.legend(lns2, ['excess return(right axis)'], fontsize=12)
ax1.set_xlim(left=0.5, right=len(hist_returns_means_dist)+0.5)
ax1.set_ylabel(u'历史一个月收益率', fontproperties=font, fontsize=16)
ax2.set_ylabel(u'超额收益', fontproperties=font, fontsize=16)
ax1.set_xlabel(u'十分位分组', fontproperties=font, fontsize=16)
ax1.set_xticks(hist_returns_means_dist.index)
ax1.set_xticklabels([int(x) for x in ax1.get_xticks()], fontproperties=font, fontsize=14)
ax1.set_yticklabels([str(x*100)+'%' for x in ax1.get_yticks()], fontproperties=font, fontsize=14)
ax2.set_yticklabels([str(x*100)+'0%' for x in ax2.get_yticks()], fontproperties=font, fontsize=14)
ax1.set_title(u"因子选股一个月历史收益率（一个月反转因子）分布特征", fontproperties=font, fontsize=16)
ax1.grid()


# 可以看出，因子和反转因子的相关性较强

# # 5. 因子历史回测净值表现
# 
# ## 5.1 简单做多策略
# 
# 接下来，考察**因子**的选股能力的回测效果。历史回测的基本设置如下：
# 
# - 回测时段为2009年3月1日至2016年10月12日
# - 股票池为A股全部股票，剔除上市未满60日的新股（计算因子时已剔除）；
# - 组合每10个交易日调仓，交易费率设为双边万分之二
# - 调仓时，涨停、停牌不买入，跌停、停牌不卖出；
# - 每次调仓时，选择股票池中**因子最大的10%**的股票；

# In[ ]:

start = '2009-03-01'                       # 回测起始时间
end = '2016-10-12'                         # 回测结束时间

benchmark = 'ZZ500'                        # 策略参考标准
universe = set_universe('A')               # 证券池，支持股票和基金
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


# In[ ]:

fig = plt.figure(figsize=(12,5))
fig.set_tight_layout(True)
ax1 = fig.add_subplot(111)
ax2 = ax1.twinx()
ax1.grid()

bt_quantile_ten = bt
data = bt_quantile_ten[[u'tradeDate',u'portfolio_value',u'benchmark_return']]
data['portfolio_return'] = data.portfolio_value/data.portfolio_value.shift(1) - 1.0
data['portfolio_return'].ix[0] = data['portfolio_value'].ix[0]/	10000000.0 - 1.0
data['excess_return'] = data.portfolio_return - data.benchmark_return
data['excess'] = data.excess_return + 1.0
data['excess'] = data.excess.cumprod()
data['portfolio'] = data.portfolio_return + 1.0
data['portfolio'] = data.portfolio.cumprod()
data['benchmark'] = data.benchmark_return + 1.0
data['benchmark'] = data.benchmark.cumprod()
# ax.plot(data[['portfolio','benchmark','excess']], label=str(qt))
ax1.plot(data['tradeDate'], data[['portfolio']], label='portfolio(left)')
ax1.plot(data['tradeDate'], data[['benchmark']], label='benchmark(left)')
ax2.plot(data['tradeDate'], data[['excess']], label='hedged(right)', color='r')

ax1.legend(loc=2)
ax2.legend(loc=0)
ax2.set_ylim(bottom=1.0, top=5)
ax1.set_ylabel(u"净值", fontproperties=font, fontsize=16)
ax2.set_ylabel(u"对冲指数净值", fontproperties=font, fontsize=16)
ax2.set_ylabel(u"对冲指数净值", fontproperties=font, fontsize=16)
ax1.set_title(u"因子最小的10%股票月度调仓走势", fontproperties=font, fontsize=16)


# 上图显示了简单做多因子最大的10%的股票之后的对冲净值走势，需要注意这里对冲基准为中证500指数

# ## 5.2 因子选股 —— 不同五分位数组合回测走势比较

# In[ ]:

# 可编辑部分与 strategy 模式一样，其余部分按本例代码编写即可

# -----------回测参数部分开始，可编辑------------
start = '2009-03-01'                       # 回测起始时间
end = '2016-10-12'                         # 回测结束时间
benchmark = 'ZZ500'                        # 策略参考标准
universe = set_universe('A')           # 证券池，支持股票和基金
capital_base = 10000000                     # 起始资金
freq = 'd'                                 # 策略类型，'d'表示日间策略使用日线回测
refresh_rate = 10                           # 调仓频率，表示执行handle_data的时间间隔

factor_data = pd.read_csv('APM_FullA.csv')     # 读取因子数据
factor_data = factor_data[factor_data.columns[:]].set_index('tradeDate')
q_dates = factor_data.index.values

quantile_five = 1                           # 选取股票的因子十分位数，1表示选取股票池中因子最小的10%的股票
commission = Commission(0.0002,0.0002)     # 交易费率设为双边万分之二
# ---------------回测参数部分结束----------------


# 把回测参数封装到 SimulationParameters 中，供 quick_backtest 使用
sim_params = quartz.SimulationParameters(start, end, benchmark, universe, capital_base)
# 获取回测行情数据
idxmap, data = quartz.get_daily_data(sim_params)
# 运行结果
results = {}

# 调整参数(选取股票的Q因子五分位数)，进行快速回测
for quantile_five in range(1, 6):
    
    # ---------------策略逻辑部分----------------
    refresh_rate = 1
    commission = Commission(0.0002, 0.0002)
    
    def initialize(account):                   # 初始化虚拟账户状态
        pass

    def handle_data(account):                  # 每个交易日的买入卖出指令
        pre_date = account.previous_date.strftime("%Y-%m-%d")
        if pre_date not in q_dates:            # 因子只在每个月底计算，所以调仓也在每月最后一个交易日进行
            return

        # 拿取调仓日前一个交易日的因子，并按照相应十分位选择股票
        q = factor_data.ix[pre_date].dropna()
        # q = q[q>0]
        q_min = q.quantile((quantile_five-1)*0.2)
        q_max = q.quantile(quantile_five*0.2)
        my_univ = q[q>=q_min][q<q_max].index.values

        # 调仓逻辑
        univ = [x for x in my_univ if x in account.universe]
        # 不在股票池中的，清仓
        for stk in account.valid_secpos:
            if stk not in univ:
                order_to(stk, 0)
        # 在目标股票池中的，等权买入
        for stk in univ:
            order_pct_to(stk, 1.01/len(univ))
    # ---------------策略逻辑部分结束----------------

    # 把回测逻辑封装到 TradingStrategy 中，供 quick_backtest 使用
    strategy = quartz.TradingStrategy(initialize, handle_data)
    # 回测部分
    bt, acct = quartz.quick_backtest(sim_params, strategy, idxmap, data, refresh_rate=refresh_rate, commission=commission)

    # 对于回测的结果，可以通过 perf_parse 函数计算风险指标
    perf = quartz.perf_parse(bt, acct)

    # 保存运行结果
    tmp = {}
    tmp['bt'] = bt
    tmp['annualized_return'] = perf['annualized_return']
    tmp['volatility'] = perf['volatility']
    tmp['max_drawdown'] = perf['max_drawdown']
    tmp['alpha'] = perf['alpha']
    tmp['beta'] = perf['beta']
    tmp['sharpe'] = perf['sharpe']
    tmp['information_ratio'] = perf['information_ratio']
    
    results[quantile_five] = tmp
    print str(quantile_five),
print 'done'


# In[ ]:

fig = plt.figure(figsize=(10,8))
fig.set_tight_layout(True)
ax1 = fig.add_subplot(211)
ax2 = fig.add_subplot(212)
ax1.grid()
ax2.grid()

for qt in results:
    bt = results[qt]['bt']

    data = bt[[u'tradeDate',u'portfolio_value',u'benchmark_return']]
    data['portfolio_return'] = data.portfolio_value/data.portfolio_value.shift(1) - 1.0   # 总头寸每日回报率
    data['portfolio_return'].ix[0] = data['portfolio_value'].ix[0]/	10000000.0 - 1.0
    data['excess_return'] = data.portfolio_return - data.benchmark_return                 # 总头寸每日超额回报率
    data['excess'] = data.excess_return + 1.0
    data['excess'] = data.excess.cumprod()                # 总头寸对冲指数后的净值序列
    data['portfolio'] = data.portfolio_return + 1.0     
    data['portfolio'] = data.portfolio.cumprod()          # 总头寸不对冲时的净值序列
    data['benchmark'] = data.benchmark_return + 1.0
    data['benchmark'] = data.benchmark.cumprod()          # benchmark的净值序列
    results[qt]['hedged_max_drawdown'] = max([1 - v/max(1, max(data['excess'][:i+1])) for i,v in enumerate(data['excess'])])  # 对冲后净值最大回撤
    results[qt]['hedged_volatility'] = np.std(data['excess_return'])*np.sqrt(252)
    results[qt]['hedged_annualized_return'] = (data['excess'].values[-1])**(252.0/len(data['excess'])) - 1.0
    # data[['portfolio','benchmark','excess']].plot(figsize=(12,8))
    # ax.plot(data[['portfolio','benchmark','excess']], label=str(qt))
    ax1.plot(data['tradeDate'], data[['portfolio']], label=str(qt))
    ax2.plot(data['tradeDate'], data[['excess']], label=str(qt))
    

ax1.legend(loc=0)
ax2.legend(loc=0)
ax1.set_ylabel(u"净值", fontproperties=font, fontsize=16)
ax2.set_ylabel(u"对冲净值", fontproperties=font, fontsize=16)
ax1.set_title(u"因子不同五分位数分组选股净值走势", fontproperties=font, fontsize=16)
ax2.set_title(u"因子不同五分位数分组选股对冲中证500指数后净值走势", fontproperties=font, fontsize=16)

# results 转换为 DataFrame
import pandas
results_pd = pandas.DataFrame(results).T.sort_index()

results_pd = results_pd[[u'alpha', u'beta', u'information_ratio', u'sharpe', 
                        u'annualized_return', u'max_drawdown', u'volatility', 
                         u'hedged_annualized_return', u'hedged_max_drawdown', u'hedged_volatility']]

for col in results_pd.columns:
    results_pd[col] = [np.round(x, 3) for x in results_pd[col]]
    
cols = [(u'风险指标', u'Alpha'), (u'风险指标', u'Beta'), (u'风险指标', u'信息比率'), (u'风险指标', u'夏普比率'),
        (u'纯股票多头时', u'年化收益'), (u'纯股票多头时', u'最大回撤'), (u'纯股票多头时', u'收益波动率'), 
        (u'对冲后', u'年化收益'), (u'对冲后', u'最大回撤'), 
        (u'对冲后', u'收益波动率')]
results_pd.columns = pd.MultiIndex.from_tuples(cols)
results_pd.index.name = u'五分位组别'
results_pd


# 上图显示出，因子选股不同五分位构建等权组合，在uqer进行真实回测的净值曲线；显示出因子很强的选股能力，不同五分位组合净值曲线随时间推移逐渐散开。

# 参考资料：方正金工专题报告《凤鸣朝阳：股价日内模式中蕴藏的选股因子》，作者：魏建榕
