import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 获取沪深300指数数据（指数专用接口）
def get_index_data():
    try:
        print("获取沪深300指数数据...")
        df = ak.stock_zh_index_daily(symbol='sh000300')
        df = df[['date', 'close']].rename(columns={'close': '沪深300指数_close'})
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        print(f"指数数据获取失败: {str(e)}")
        return None

# 获取沪深300ETF数据（使用fund_etf_nav接口）
def get_etf_data():
    try:
        print("获取沪深300ETF净值数据...")
        # 使用ETF代码510310，获取净值数据
        df = ak.fund_etf_hist_em(symbol="510310", adjust="qfq")
        print("ETF数据列名:", df.columns.tolist())
        # 接口返回字段：净值日期,基金代码,基金名称,单位净值,累计净值,日增长率
        df = df[['日期', '收盘']].rename(columns={
            '日期': 'date',
            '收盘': '沪深300ETF_close'
        })
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        print(f"ETF数据获取失败: {str(e)}")
        return None

# 获取并检查数据
hs300_df = get_index_data()
print("hs300_df:", hs300_df)
etf_df = get_etf_data()
print("get_etf_data:", etf_df)

if hs300_df is None or etf_df is None:
    print("数据获取失败，程序退出")
    exit()

# 合并数据
merged_df = pd.merge(hs300_df, etf_df, on='date', how='inner')
merged_df.to_csv('沪深300及ETF收盘价数据.csv', index=False, encoding='utf-8-sig')
print("数据已保存到 '沪深300及ETF收盘价数据.csv'")

# 绘制图表
fig, ax1 = plt.subplots(figsize=(15, 7))

# 绘制指数
ax1.plot(merged_df['date'], merged_df['沪深300指数_close'], color='#1f77b4', label='沪深300指数', linewidth=2)
ax1.set_xlabel('日期', fontsize=12)
ax1.set_ylabel('沪深300指数收盘价', color='#1f77b4', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#1f77b4')
ax1.grid(True, linestyle='--', alpha=0.6)

# 绘制ETF
ax2 = ax1.twinx()
ax2.plot(merged_df['date'], merged_df['沪深300ETF_close'], color='#ff7f0e', label='沪深300ETF单位净值', linewidth=2, alpha=0.8)
ax2.set_ylabel('ETF单位净值', color='#ff7f0e', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#ff7f0e')

# 标题和图例（注明数据类型）
plt.title('沪深300指数与ETF净值走势对比', fontsize=16, pad=20)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12)

# 日期格式
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.xticks(rotation=45)
plt.tight_layout()

# 保存图表
chart_path = '沪深300指数与ETF走势对比图表.png'
plt.savefig(chart_path, dpi=300, bbox_inches='tight')
print(f"图表已保存到 '{chart_path}'")