import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties

# 设置中文字体，避免缺失SimHei的问题
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# ---------------------- 获取融资融券余额数据 ----------------------
try:
    # 获取沪深市场融资融券合计数据
    margin_df = ak.stock_margin_account_info()
    print("融资融券数据列名:", margin_df.columns.tolist())
    
    # 提取所需列（日期、融资余额、融券余额）并计算合计
    margin_clean = margin_df[['日期', '融资余额', '融券余额']].rename(columns={
        '融资余额': '融资余额(亿元)',
        '融券余额': '融券余额(亿元)'
    })
    # 计算融资融券余额合计
    margin_clean['融资融券余额(亿元)'] = margin_clean['融资余额(亿元)'] + margin_clean['融券余额(亿元)']
    
    # 数据类型转换
    margin_clean['日期'] = pd.to_datetime(margin_clean['日期'])
    for col in ['融资余额(亿元)', '融券余额(亿元)', '融资融券余额(亿元)']:
        margin_clean[col] = pd.to_numeric(margin_clean[col], errors='coerce')
    margin_clean = margin_clean.dropna()
    
    # 按月度聚合，取每月最后一个交易日数据
    margin_monthly = margin_clean.resample('M', on='日期').last().reset_index()
    print(f"融资融券月度数据: {len(margin_monthly)}条记录")

except Exception as e:
    print(f"获取融资融券数据失败: {e}")
    raise

# ---------------------- 获取A股总市值数据 ----------------------
try:
    # 获取A股总市值数据（使用巴菲特指数接口）
    buffett_df = ak.stock_buffett_index_lg()
    print("巴菲特指数数据列名:", buffett_df.columns.tolist())
    
    # 提取日期和总市值列（适配中文列名）
    if '总市值' in buffett_df.columns:
        market_cap_clean = buffett_df[['日期', '总市值']].rename(columns={
            '总市值': 'A股总市值(万亿元)'
        })
    elif 'total_market_value' in buffett_df.columns:
        market_cap_clean = buffett_df[['日期', 'total_market_value']].rename(columns={
            '日期': '日期',
            'total_market_value': 'A股总市值(万亿元)'
        })
    else:
        numeric_cols = buffett_df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        if numeric_cols and '日期' in buffett_df.columns:
            market_cap_clean = buffett_df[['日期', numeric_cols[0]]].rename(columns={
                numeric_cols[0]: 'A股总市值(万亿元)'
            })
            print(f"警告：使用默认列 {numeric_cols[0]} 作为总市值数据")
        else:
            raise ValueError("无法从stock_buffett_index_lg提取总市值数据")
    
    # 数据类型转换
    market_cap_clean['日期'] = pd.to_datetime(market_cap_clean['日期'])
    market_cap_clean['A股总市值(万亿元)'] = pd.to_numeric(market_cap_clean['A股总市值(万亿元)'], errors='coerce')
    market_cap_clean = market_cap_clean.dropna()
    
    # 按月度聚合
    market_cap_monthly = market_cap_clean.resample('M', on='日期').last().reset_index()
    print(f"总市值月度数据: {len(market_cap_monthly)}条记录")

except Exception as e:
    print(f"获取总市值数据失败: {e}")
    raise

# ---------------------- 数据合并与时间对齐 ----------------------
merged_df = pd.merge(margin_monthly, market_cap_monthly, on='日期', how='inner')
print(f"合并后数据: {len(merged_df)}条记录")
merged_df = merged_df.sort_values('日期')

# ---------------------- 保存数据 ----------------------
margin_monthly.to_csv("融资融券余额月度数据.csv", index=False, encoding="utf-8-sig")
market_cap_monthly.to_csv("A股总市值月度数据.csv", index=False, encoding="utf-8-sig")
merged_df.to_csv("融资融券与总市值合并数据.csv", index=False, encoding="utf-8-sig")
print("数据已保存至CSV文件")

# ---------------------- 绘制趋势对比图 ----------------------
fig, ax1 = plt.subplots(figsize=(14, 7), dpi=100)

# 左侧Y轴：融资融券余额
ax1.plot(merged_df['日期'], merged_df['融资融券余额(亿元)'], marker='o', linestyle='-', 
         color='#1f77b4', label='融资融券余额(亿元)', alpha=0.8)
ax1.set_xlabel('日期', fontsize=12)
ax1.set_ylabel('融资融券余额(亿元)', color='#1f77b4', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#1f77b4')
ax1.grid(True, linestyle='--', alpha=0.5)

# 右侧Y轴：总市值
ax2 = ax1.twinx()
ax2.plot(merged_df['日期'], merged_df['A股总市值(万亿元)'], marker='s', linestyle='-', 
         color='#ff7f0e', label='A股总市值(万亿元)', alpha=0.8)
ax2.set_ylabel('A股总市值(万亿元)', color='#ff7f0e', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#ff7f0e')

# 标题和图例
start_date = merged_df['日期'].min().strftime('%Y-%m')
end_date = merged_df['日期'].max().strftime('%Y-%m')
plt.title(f'融资融券余额与A股总市值趋势对比 ({start_date}至{end_date})', fontsize=14, pad=20)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)

# 日期格式设置
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

# 保存图表
plt.tight_layout(pad=3.0)
save_path = "融资融券余额与A股总市值趋势对比图.png"
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"图表已保存至: {save_path}")