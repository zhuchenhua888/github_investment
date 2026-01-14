# -*- coding: utf-8 -*-
"""
Created on Thu Mar  2 15:47:04 2023

@author: zch
"""

import akshare as ak    # 导入数据源
import pandas as pd    # 导入pandas库
import numpy as np
import matplotlib.pyplot as plt
import datetime
import time
from datetime import timedelta

# 配置参数
years = 10 # 5年
date_time = years * 244 #n年乘以244个交易日

# 1、获取股债利差，接口stock_index_pe_lg
hs300_pe_df = ak.stock_ebs_lg().iloc[-date_time:].set_index('日期')
print(hs300_pe_df)
hs300_pe_TTM = hs300_pe_df[['股债利差','沪深300指数']]
#hs300_pe_TTM.plot(figsize=(16,8),grid=True,title='股债利差')    # 画图
hs300_pe_TTM['股债利差'] *= 100
hs300_pe_TTM['股债利差'].plot(figsize=(16,8),grid=True,title='riskpremium').set_ylabel('riskpremium')
hs300_pe_TTM['沪深300指数'].plot(figsize=(16,8),grid=True,secondary_y=True,title='hs300').set_ylabel('hs300')

# riskpremium = pd.DataFrame((hs300_pe_TTM['股债利差']*100),\
#                            index=hs300_pe_TTM.index,columns=['riskpremium']).dropna()
riskpremium = pd.DataFrame((hs300_pe_TTM['股债利差']))
# 画图
plt.figure(figsize=(20,8))
plt.plot(list(hs300_pe_TTM.index),hs300_pe_TTM.loc[:,'沪深300指数'],linestyle='--',color='grey', label='HS300')
# plt.twinx()
plt.plot(list(riskpremium.index),riskpremium.values,color='darkblue', label='riskpremium')
df1 = riskpremium[riskpremium>riskpremium.quantile(0.9)]
plt.plot(list(df1.index),df1.values,color='green')
df2 = riskpremium[riskpremium<riskpremium.quantile(0.1)]
plt.plot(list(df2.index),df2.values,color='r')
df3 = riskpremium[(riskpremium<riskpremium.quantile(0.9))&(riskpremium>riskpremium.quantile(0.7))]
plt.plot(list(df3.index),df3.values,color='cyan')
df4 = riskpremium[(riskpremium<riskpremium.quantile(0.3))&(riskpremium>riskpremium.quantile(0.1))]
plt.plot(list(df4.index),df4.values,color='y')

plt.plot(list(riskpremium.index),[riskpremium.mean().values[0]]*len(riskpremium),linestyle='--',color='darkblue')
plt.plot(list(riskpremium.index),[riskpremium.mean().values[0]+riskpremium.std().values[0]]*len(riskpremium),linestyle='--',color='orange')
plt.plot(list(riskpremium.index),[riskpremium.mean().values[0]-riskpremium.std().values[0]]*len(riskpremium),linestyle='--',color='orange')
plt.plot(list(riskpremium.index),[riskpremium.mean().values[0]+2*riskpremium.std().values[0]]*len(riskpremium),linestyle='--',color='green')
plt.plot(list(riskpremium.index),[riskpremium.mean().values[0]-2*riskpremium.std().values[0]]*len(riskpremium),linestyle='--',color='r')
plt.show()


# chatgpt画的图
# # 绘制沪深300指数和股权溢价指数的折线图
# fig, ax1 = plt.subplots()
# ax2 = ax1.twinx()

# lns1 = ax1.plot(hs300_pe_TTM.index, hs300_pe_TTM['沪深300指数'], 'b-', label='沪深300指数')
# lns2 = ax2.plot(hs300_pe_TTM.index, hs300_pe_TTM['股债利差'], 'r-', label='股权溢价指数涨跌幅')

# ax1.set_xlabel('日期')
# ax1.set_ylabel('沪深300指数')
# ax2.set_ylabel('股权溢价指数涨跌幅')

# lns = lns1 + lns2
# labs = [l.get_label() for l in lns]
# ax1.legend(lns, labs, loc=0)

# plt.title('沪深300指数和股权溢价指数的关系')
# plt.show()


