import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re  # 导入正则表达式模块

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# ---------------------- 日期解析函数 ----------------------
def parse_chinese_date(date_str):
    """从"2025年09月份"格式提取年月，转换为"2025-09" """
    match = re.search(r'(\d{4})年(\d{2})月', str(date_str))
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None

# ---------------------- 获取全部成交金额数据 ----------------------
try:
    # 获取股票市场成交金额数据
    market_cap_df = ak.macro_china_stock_market_cap()
    print("市场成交金额数据列名:", market_cap_df.columns.tolist())
    
    # 提取日期和分市场成交金额列
    if '数据日期' in market_cap_df.columns and '成交金额-上海' in market_cap_df.columns and '成交金额-深圳' in market_cap_df.columns:
        turnover_clean = market_cap_df[['数据日期', '成交金额-上海', '成交金额-深圳']].rename(columns={
            '数据日期': '日期',
            '成交金额-上海': '成交金额-上海(亿元)',
            '成交金额-深圳': '成交金额-深圳(亿元)'
        })
        # 计算全部成交金额（上海+深圳）
        turnover_clean['全部成交金额(亿元)'] = turnover_clean['成交金额-上海(亿元)'] + turnover_clean['成交金额-深圳(亿元)']
    else:
        raise ValueError("接口返回格式变化，未找到分市场成交金额列")
    
    # 处理中文日期格式
    turnover_clean['日期'] = turnover_clean['日期'].apply(parse_chinese_date)
    turnover_clean['日期'] = pd.to_datetime(turnover_clean['日期'])
    turnover_clean = turnover_clean.dropna(subset=['日期'])  # 移除解析失败的行
    
    # 数据类型转换
    for col in ['成交金额-上海(亿元)', '成交金额-深圳(亿元)', '全部成交金额(亿元)']:
        turnover_clean[col] = pd.to_numeric(turnover_clean[col], errors='coerce')
    turnover_clean = turnover_clean.dropna()
    
    # 按月度聚合（求和）
    turnover_monthly = turnover_clean.resample('M', on='日期').sum().reset_index()
    print(f"成交金额月度数据: {len(turnover_monthly)}条记录")

except Exception as e:
    print(f"获取成交金额数据失败: {e}")
    raise

# ---------------------- 获取融资买入额数据 ----------------------
try:
    # 获取融资融券数据中的融资买入额
    margin_df = ak.stock_margin_account_info()
    print("融资融券数据列名:", margin_df.columns.tolist())
    
    # 提取日期和融资买入额列
    if '融资买入额' in margin_df.columns:
        margin_purchase_clean = margin_df[['日期', '融资买入额']].rename(columns={
            '融资买入额': '融资买入额(亿元)'
        })
    else:
        raise ValueError("融资融券数据中未找到'融资买入额'列")
    
    # 数据类型转换
    margin_purchase_clean['日期'] = pd.to_datetime(margin_purchase_clean['日期'])
    margin_purchase_clean['融资买入额(亿元)'] = pd.to_numeric(margin_purchase_clean['融资买入额(亿元)'], errors='coerce')
    margin_purchase_clean = margin_purchase_clean.dropna()
    
    # 按月度聚合（求和）
    margin_monthly = margin_purchase_clean.resample('M', on='日期').sum().reset_index()
    print(f"融资买入额月度数据: {len(margin_monthly)}条记录")

except Exception as e:
    print(f"获取融资买入额数据失败: {e}")
    raise

# ---------------------- 数据合并与指标计算 ----------------------
merged_df = pd.merge(turnover_monthly, margin_monthly, on='日期', how='inner')
merged_df = merged_df.sort_values('日期')

# 新增：计算融资买入额占成交金额的百分比
merged_df['融资买入额占比(%)'] = (merged_df['融资买入额(亿元)'] / merged_df['全部成交金额(亿元)']) * 100
# 处理可能的除零问题
merged_df['融资买入额占比(%)'] = merged_df['融资买入额占比(%)'].replace([float('inf'), -float('inf')], None)
merged_df = merged_df.dropna(subset=['融资买入额占比(%)'])
print(f"合并后数据（含占比指标）: {len(merged_df)}条记录")

# ---------------------- 保存数据 ----------------------
turnover_monthly.to_csv("股票市场成交金额月度数据.csv", index=False, encoding="utf-8-sig")
margin_monthly.to_csv("融资买入额月度数据.csv", index=False, encoding="utf-8-sig")
merged_df.to_csv("成交金额与融资买入额合并数据.csv", index=False, encoding="utf-8-sig")
print("数据已保存至CSV文件")

# ---------------------- 绘制趋势对比图（含新子图） ----------------------
fig, (ax1, ax3) = plt.subplots(2, 1, figsize=(14, 12), dpi=100, sharex=True)

# ---------------------- 上图：成交金额与融资买入额趋势 ----------------------
# 左侧Y轴：全部成交金额
ax1.plot(merged_df['日期'], merged_df['全部成交金额(亿元)'], marker='o', linestyle='-', 
         color='#1f77b4', label='全部成交金额(亿元)', alpha=0.8)
ax1.set_ylabel('全部成交金额(亿元)', color='#1f77b4', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#1f77b4')
ax1.grid(True, linestyle='--', alpha=0.5)

# 右侧Y轴：融资买入额
ax2 = ax1.twinx()
line2, = ax2.plot(merged_df['日期'], merged_df['融资买入额(亿元)'], marker='s', linestyle='-', 
         color='#ff7f0e', label='融资买入额(亿元)', alpha=0.8)
ax2.set_ylabel('融资买入额(亿元)', color='#ff7f0e', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#ff7f0e')

# 上图图例和标题
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
start_date = merged_df['日期'].min().strftime('%Y-%m')
end_date = merged_df['日期'].max().strftime('%Y-%m')
ax1.set_title(f'股票市场成交金额与融资买入额趋势对比 ({start_date}至{end_date})', fontsize=14, pad=20)

# ---------------------- 下图：融资买入额占比 ----------------------
ax3.plot(merged_df['日期'], merged_df['融资买入额占比(%)'], marker='^', linestyle='-', 
         color='#9467bd', label='融资买入额占比(%)', alpha=0.8)
ax3.set_xlabel('日期', fontsize=12)
ax3.set_ylabel('融资买入额占比(%)', color='#9467bd', fontsize=12)
ax3.tick_params(axis='y', labelcolor='#9467bd')
ax3.grid(True, linestyle='--', alpha=0.5)
ax3.legend(loc='upper left', fontsize=10)
ax3.set_title('融资买入额占股票市场成交金额比例', fontsize=14, pad=20)

# 日期格式设置
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')

# ---------------------- 保存图表 ----------------------
plt.tight_layout(pad=5.0)
save_path = "估值-融资买入额与股票市场成交金额及占比趋势图.png"
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"图表已保存至: {save_path}")