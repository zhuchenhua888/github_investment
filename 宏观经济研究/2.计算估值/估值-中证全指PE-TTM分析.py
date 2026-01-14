import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from matplotlib.dates import DateFormatter

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 从stock_zh_index_hist_csindex接口获取市盈率和收盘价数据
def get_combined_data():
    try:
        # 获取尽可能长的历史数据
        end_date = datetime.datetime.today().strftime("%Y%m%d")
        start_date = "20120831"  # 中证全指成立时间
        
        # 调用接口获取包含市盈率的指数数据
        df = ak.stock_zh_index_hist_csindex(
            symbol="000985",
            start_date=start_date,
            end_date=end_date
        )
        print(df)
        # 保存原始数据
        df.to_excel("中证全指历史数据.xlsx", index=False, engine="openpyxl")
        print("原始数据已保存至：中证全指历史数据.xlsx")
        
        # 识别市盈率和收盘价列
        pe_cols = [col for col in df.columns if "市盈率" in col or "PE" in col.upper()]
        close_cols = [col for col in df.columns if "收盘" in col or "close" in col.lower()]
        
        if not pe_cols or not close_cols:
            print(f"无法识别市盈率或收盘价列，可用列名: {df.columns.tolist()}")
            return None
        
        # 提取所需列并重命名
        date_col = next((col for col in df.columns if "日期" in col), df.columns[0])
        df_combined = df[[date_col, pe_cols[0], close_cols[0]]].rename(
            columns={
                date_col: "date",
                pe_cols[0]: "pe_ttm",
                close_cols[0]: "close"
            }
        )
        
        # 数据清洗
        df_combined["date"] = pd.to_datetime(df_combined["date"])
        df_combined["pe_ttm"] = pd.to_numeric(df_combined["pe_ttm"], errors="coerce")
        df_combined["close"] = pd.to_numeric(df_combined["close"], errors="coerce")
        df_combined = df_combined.dropna().sort_values("date")
        
        # 打印数据范围
        print(f"数据日期范围: {df_combined['date'].min().strftime('%Y-%m-%d')} to {df_combined['date'].max().strftime('%Y-%m-%d')}")
        print(f"有效数据量: {len(df_combined)}条记录")
        
        # 保存处理后的数据
        df_combined.to_excel("中证全指PE与收盘价数据.xlsx", index=False, engine="openpyxl")
        print("处理后数据已保存至：中证全指PE与收盘价数据.xlsx")
        return df_combined
    except Exception as e:
        print(f"获取数据失败: {e}")
        return None

# 计算分位点并绘制图表
def analyze_and_plot(df):
    if df is None or len(df) < 1:
        print("无数据可分析")
        return
    
    # 计算十年分位点（最近10年数据）
    ten_years_ago = datetime.datetime.today() - datetime.timedelta(days=365*10)
    df_recent = df[df["date"] >= ten_years_ago]
    
    if len(df_recent) < 120:  # 至少需要10年*12个月=120个数据点
        print(f"警告：十年数据不足，仅{len(df_recent)}条记录，使用全部可用数据计算分位点")
        df_recent = df.copy()
    
    # 计算分位点
    current_pe = df["pe_ttm"].iloc[-1]
    percentile = (df_recent["pe_ttm"] <= current_pe).mean() * 100
    print(f"当前市盈率: {current_pe:.2f}，分位点: {percentile:.1f}% (基于{len(df_recent)}条记录)")
    
    # 绘制双Y轴图表
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    
    # 绘制市盈率
    ax1.plot(df["date"], df["pe_ttm"], 'b-', label='市盈率', alpha=0.7)
    ax1.set_xlabel('日期')
    ax1.set_ylabel('市盈率', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.legend(loc='upper left')
    
    # 绘制收盘价
    ax2.plot(df["date"], df["close"], 'r--', label='收盘价', alpha=0.7)
    ax2.set_ylabel('收盘价', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    ax2.legend(loc='upper right')
    
    # 添加标题和分位点标注
    data_range = f"{df['date'].min().strftime('%Y')}-{df['date'].max().strftime('%Y')}"
    plt.title(f'中证全指市盈率与收盘价 ({data_range})')
    
    ax1.axhline(y=current_pe, color='blue', linestyle=':', alpha=0.7)
    ax1.annotate(f'当前PE: {current_pe:.2f}\n分位点: {percentile:.1f}%',
                 xy=(df["date"].iloc[-1], current_pe),
                 xytext=(-150, 50), textcoords='offset points',
                 arrowprops=dict(arrowstyle='->', color='blue'),
                 bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.5))
    
    # 设置日期格式
    ax1.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig("中证全指PE与收盘价图表.png", dpi=300, bbox_inches='tight')
    print("图表已保存至：中证全指PE与收盘价图表.png")

if __name__ == "__main__":
    df_combined = get_combined_data()
    analyze_and_plot(df_combined)