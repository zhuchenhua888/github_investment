import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 获取并处理大宗商品价格指数数据
commodity_df = ak.macro_china_commodity_price_index()
print("大宗商品价格指数数据列名:", commodity_df.columns.tolist())

# 数据清洗与重命名
commodity_df['日期'] = pd.to_datetime(commodity_df['日期'])
commodity_clean = commodity_df[['日期', '最新值']].rename(columns={
    '最新值': '大宗商品价格指数'
})
commodity_clean['大宗商品价格指数'] = pd.to_numeric(commodity_clean['大宗商品价格指数'], errors='coerce')
commodity_clean = commodity_clean.dropna()

# 获取并处理沪深300指数数据
hs300_df = ak.stock_zh_index_daily(symbol="sh000300")
hs300_df['日期'] = pd.to_datetime(hs300_df['date'])
hs300_clean = hs300_df[['日期', 'close']].rename(columns={'close': '沪深300收盘价'})
hs300_clean = hs300_clean.dropna()

# 确定共同时间范围
start_date = max(commodity_clean['日期'].min(), hs300_clean['日期'].min())
end_date = min(commodity_clean['日期'].max(), hs300_clean['日期'].max())

# 过滤并合并数据
commodity_filtered = commodity_clean[(commodity_clean['日期'] >= start_date) & (commodity_clean['日期'] <= end_date)]
hs300_filtered = hs300_clean[(hs300_clean['日期'] >= start_date) & (hs300_clean['日期'] <= end_date)]
merged_data = pd.merge(commodity_filtered, hs300_filtered, on='日期', how='inner')

# 保存合并后的数据
merged_data.to_csv("数据-大宗商品价格指数与沪深300数据.csv", index=False, encoding="utf-8-sig")
print(f"数据已保存，共{len(merged_data)}条有效记录")

# 创建图表
fig, ax1_left = plt.subplots(figsize=(20, 8))
ax1_right = ax1_left.twinx()

# 绘制大宗商品价格指数（左Y轴）
line1, = ax1_left.plot(merged_data['日期'], merged_data['大宗商品价格指数'], 
                      linestyle='-', color='#1f77b4', 
                      label='大宗商品价格指数', alpha=0.8)
ax1_left.set_ylabel('大宗商品价格指数', color='#1f77b4', fontsize=12)
ax1_left.tick_params(axis='y', labelcolor='#1f77b4')
ax1_left.grid(True, linestyle='--', alpha=0.5)

# 绘制沪深300指数（右Y轴）
line2, = ax1_right.plot(merged_data['日期'], merged_data['沪深300收盘价'], 
                       linestyle='-', color='#ff7f0e', 
                       label='沪深300收盘价', alpha=0.8)
ax1_right.set_ylabel('沪深300指数(点)', color='#ff7f0e', fontsize=12)
ax1_right.tick_params(axis='y', labelcolor='#ff7f0e')

# 设置图表标题和图例
ax1_left.set_title(f'大宗商品价格指数与沪深300指数走势对比 ({start_date.year}-{end_date.year})', fontsize=16, pad=20)
ax1_left.set_xlabel('日期', fontsize=12)
ax1_left.legend(handles=[line1, line2], loc='upper left', fontsize=12)

# 设置X轴日期格式
ax1_left.xaxis.set_major_locator(mdates.YearLocator())
ax1_left.xaxis.set_minor_locator(mdates.MonthLocator())
ax1_left.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.setp(ax1_left.get_xticklabels(), rotation=45, ha='right')

# 保存图表
save_path = "估值-大宗商品价格指数与沪深300指数对比趋势图.png"
plt.tight_layout(pad=5.0)
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"图表已保存至: {save_path}")