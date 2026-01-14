import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 获取并处理CPI数据
cpi_df = ak.macro_china_cpi_yearly()
print("CPI数据列名:", cpi_df.columns.tolist())
cpi_df['日期'] = pd.to_datetime(cpi_df['日期'])
cpi_df = cpi_df[['日期', '今值']].rename(columns={'今值': 'CPI年率(%)'})
cpi_df['CPI年率(%)'] = pd.to_numeric(cpi_df['CPI年率(%)'], errors='coerce')

# 获取并处理PPI数据
ppi_df = ak.macro_china_ppi_yearly()
ppi_df['日期'] = pd.to_datetime(ppi_df['日期'])
ppi_df = ppi_df[['日期', '今值']].rename(columns={'今值': 'PPI年率(%)'})
ppi_df['PPI年率(%)'] = pd.to_numeric(ppi_df['PPI年率(%)'], errors='coerce')

# 获取并处理沪深300指数数据
hs300_df = ak.stock_zh_index_daily(symbol="sh000300")
hs300_df['date'] = pd.to_datetime(hs300_df['date'])
hs300_df = hs300_df.set_index('date')
hs300_df = hs300_df.reset_index().rename(columns={'date': '日期'})
hs300_df = hs300_df.rename(columns={'close': '沪深300收盘价'})

# 确定沪深300指数的时间范围
hs300_start_date = hs300_df['日期'].min()
hs300_end_date = hs300_df['日期'].max()

# 过滤CPI和PPI数据，仅保留沪深300指数时间范围内的数据
cpi_filtered = cpi_df[(cpi_df['日期'] >= hs300_start_date) & (cpi_df['日期'] <= hs300_end_date)]
cpi_filtered.to_csv("数据-获取CPI.csv", index=False, encoding="utf-8-sig")
ppi_filtered = ppi_df[(ppi_df['日期'] >= hs300_start_date) & (ppi_df['日期'] <= hs300_end_date)]
ppi_filtered.to_csv("数据-获取PPI.csv", index=False, encoding="utf-8-sig")

# 创建图表
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 16), dpi=100, sharex=False)

# ---------------------- 上子图：CPI与沪深300指数（双Y轴） ----------------------
ax1_left = ax1
ax1_right = ax1.twinx()

# 绘制CPI（左Y轴）
line1, = ax1_left.plot(cpi_filtered['日期'], cpi_filtered['CPI年率(%)'], 
                      marker='o', linestyle='-', color='#1f77b4', 
                      label='CPI年率(%)', alpha=0.8)
# 自动调整Y轴范围以显示所有数据
ax1_left.autoscale(enable=True, axis='y', tight=True)
ax1_left.set_ylabel('CPI年率(%)', color='#1f77b4', fontsize=12)
ax1_left.tick_params(axis='y', labelcolor='#1f77b4')
ax1_left.grid(True, linestyle='--', alpha=0.5)

# 绘制沪深300指数（右Y轴）
line2, = ax1_right.plot(hs300_df['日期'], hs300_df['沪深300收盘价'], 
                       marker='s', linestyle='-', color='#ff7f0e', 
                       label='沪深300收盘价', alpha=0.8)
# 自动调整Y轴范围以显示所有数据
ax1_right.autoscale(enable=True, axis='y', tight=True)
ax1_right.set_ylabel('沪深300指数(点)', color='#ff7f0e', fontsize=12)
ax1_right.tick_params(axis='y', labelcolor='#ff7f0e')

# 合并图例
ax1.legend(handles=[line1, line2], loc='upper left', fontsize=10)
ax1.set_title(f'CPI与沪深300指数走势对比 ({hs300_start_date.year}-{hs300_end_date.year})', fontsize=14, pad=20)
ax1.set_xlabel('日期', fontsize=12)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

# ---------------------- 下子图：PPI与沪深300指数（双Y轴） ----------------------
ax2_left = ax2
ax2_right = ax2.twinx()

# 绘制PPI（左Y轴）
line3, = ax2_left.plot(ppi_filtered['日期'], ppi_filtered['PPI年率(%)'], 
                      marker='^', linestyle='-', color='#2ca02c', 
                      label='PPI年率(%)', alpha=0.8)
# 自动调整Y轴范围以显示所有数据
ax2_left.autoscale(enable=True, axis='y', tight=True)
ax2_left.set_ylabel('PPI年率(%)', color='#2ca02c', fontsize=12)
ax2_left.tick_params(axis='y', labelcolor='#2ca02c')
ax2_left.grid(True, linestyle='--', alpha=0.5)

# 绘制沪深300指数（右Y轴）
line4, = ax2_right.plot(hs300_df['日期'], hs300_df['沪深300收盘价'], 
                       marker='D', linestyle='-', color='#d62728', 
                       label='沪深300收盘价', alpha=0.8)
# 自动调整Y轴范围以显示所有数据
ax2_right.autoscale(enable=True, axis='y', tight=True)
ax2_right.set_ylabel('沪深300指数(点)', color='#d62728', fontsize=12)
ax2_right.tick_params(axis='y', labelcolor='#d62728')

# 合并图例
ax2.legend(handles=[line3, line4], loc='upper left', fontsize=10)
ax2.set_title(f'PPI与沪深300指数走势对比 ({hs300_start_date.year}-{hs300_end_date.year})', fontsize=14, pad=20)
ax2.set_xlabel('日期', fontsize=12)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')

# 调整布局
plt.tight_layout(pad=5.0)
save_path = "估值-CPI_PPI与沪深300指数对比趋势图.png"
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"调整后的图表已保存至: {save_path}")
