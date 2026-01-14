import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re
from matplotlib.font_manager import FontProperties

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# ---------------------- 获取并处理CPI数据 ----------------------
cpi_df = ak.macro_china_cpi()
print("CPI原始数据列名:", cpi_df.columns.tolist())

# 处理日期格式：从"2025年07月份"提取为"2025-07"
def parse_cpi_date(date_str):
    match = re.search(r'(\d{4})年(\d{2})月', date_str)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None

cpi_df['日期'] = cpi_df['月份'].apply(parse_cpi_date)
cpi_df = cpi_df.dropna(subset=['日期'])  # 移除解析失败的行
cpi_df['日期'] = pd.to_datetime(cpi_df['日期'])

# 提取所需列并重命名
cpi_clean = cpi_df[['日期', '全国-当月']].rename(columns={
    '全国-当月': 'CPI年率(%)'
})
cpi_clean['CPI年率(%)'] = pd.to_numeric(cpi_clean['CPI年率(%)'], errors='coerce')
cpi_clean = cpi_clean.dropna()

# ---------------------- 获取并处理PPI数据 ----------------------
ppi_df = ak.macro_china_ppi_yearly()
print("PPI原始数据列名:", ppi_df.columns.tolist())

ppi_df['日期'] = pd.to_datetime(ppi_df['日期'])
ppi_clean = ppi_df[['日期', '今值']].rename(columns={'今值': 'PPI年率(%)'})
ppi_clean['PPI年率(%)'] = pd.to_numeric(ppi_clean['PPI年率(%)'], errors='coerce')
ppi_clean = ppi_clean.dropna()

# ---------------------- 获取并处理沪深300指数数据 ----------------------
hs300_df = ak.stock_zh_index_daily(symbol="sh000300")
hs300_df['日期'] = pd.to_datetime(hs300_df['date'])
hs300_clean = hs300_df[['日期', 'close']].rename(columns={'close': '沪深300收盘价'})
hs300_clean = hs300_clean.dropna()

# ---------------------- 数据时间范围对齐 ----------------------
# 确定共同时间范围
start_date = max(cpi_clean['日期'].min(), ppi_clean['日期'].min(), hs300_clean['日期'].min())
end_date = min(cpi_clean['日期'].max(), ppi_clean['日期'].max(), hs300_clean['日期'].max())

# 筛选数据
cpi_filtered = cpi_clean[(cpi_clean['日期'] >= start_date) & (cpi_clean['日期'] <= end_date)]
ppi_filtered = ppi_clean[(ppi_clean['日期'] >= start_date) & (ppi_clean['日期'] <= end_date)]
hs300_filtered = hs300_clean[(hs300_clean['日期'] >= start_date) & (hs300_clean['日期'] <= end_date)]

# 保存CPI和PPI数据
cpi_filtered.to_csv("数据-获取CPI.csv", index=False, encoding="utf-8-sig")
ppi_filtered.to_csv("数据-获取PPI.csv", index=False, encoding="utf-8-sig")
print(f"CPI数据保存: {len(cpi_filtered)}条记录, PPI数据保存: {len(ppi_filtered)}条记录")

# 合并数据用于绘图（按日期对齐）
cpi_hs300 = pd.merge(cpi_filtered, hs300_filtered, on='日期', how='inner')
ppi_hs300 = pd.merge(ppi_filtered, hs300_filtered, on='日期', how='inner')

# ---------------------- 创建图表 ----------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 16), dpi=100, sharex=False)

# ---------------------- 上子图：CPI与沪深300指数（双Y轴） ----------------------
ax1_left = ax1
ax1_right = ax1.twinx()

# 绘制CPI（左Y轴）
line1, = ax1_left.plot(cpi_hs300['日期'], cpi_hs300['CPI年率(%)'], 
                      marker='o', linestyle='-', color='#1f77b4', 
                      label='CPI年率(%)', alpha=0.8)
ax1_left.set_ylabel('CPI年率(%)', color='#1f77b4', fontsize=12)
ax1_left.tick_params(axis='y', labelcolor='#1f77b4')
ax1_left.grid(True, linestyle='--', alpha=0.5)

# 绘制沪深300指数（右Y轴）
line2, = ax1_right.plot(cpi_hs300['日期'], cpi_hs300['沪深300收盘价'], 
                       marker='s', linestyle='-', color='#ff7f0e', 
                       label='沪深300收盘价', alpha=0.8)
ax1_right.set_ylabel('沪深300指数(点)', color='#ff7f0e', fontsize=12)
ax1_right.tick_params(axis='y', labelcolor='#ff7f0e')

ax1.legend(handles=[line1, line2], loc='upper left', fontsize=10)
ax1.set_title(f'CPI与沪深300指数走势对比 ({start_date.year}-{end_date.year})', fontsize=14, pad=20)
ax1.set_xlabel('日期', fontsize=12)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

# ---------------------- 下子图：PPI与沪深300指数（双Y轴） ----------------------
ax2_left = ax2
ax2_right = ax2.twinx()

# 绘制PPI（左Y轴）
line3, = ax2_left.plot(ppi_hs300['日期'], ppi_hs300['PPI年率(%)'], 
                      marker='^', linestyle='-', color='#2ca02c', 
                      label='PPI年率(%)', alpha=0.8)
ax2_left.set_ylabel('PPI年率(%)', color='#2ca02c', fontsize=12)
ax2_left.tick_params(axis='y', labelcolor='#2ca02c')
ax2_left.grid(True, linestyle='--', alpha=0.5)

# 绘制沪深300指数（右Y轴）
line4, = ax2_right.plot(ppi_hs300['日期'], ppi_hs300['沪深300收盘价'], 
                       marker='D', linestyle='-', color='#d62728', 
                       label='沪深300收盘价', alpha=0.8)
ax2_right.set_ylabel('沪深300指数(点)', color='#d62728', fontsize=12)
ax2_right.tick_params(axis='y', labelcolor='#d62728')

ax2.legend(handles=[line3, line4], loc='upper left', fontsize=10)
ax2.set_title(f'PPI与沪深300指数走势对比 ({start_date.year}-{end_date.year})', fontsize=14, pad=20)
ax2.set_xlabel('日期', fontsize=12)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')

# ---------------------- 保存图表 ----------------------
plt.tight_layout(pad=5.0)
save_path = "估值-CPI_PPI与沪深300指数对比趋势图.png"
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"图表已保存至: {save_path}")