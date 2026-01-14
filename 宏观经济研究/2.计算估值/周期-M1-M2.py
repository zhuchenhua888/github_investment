import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import os
import datetime

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 自定义中文日期解析函数
def parse_chinese_date(date_str):
    if pd.isna(date_str):
        return pd.NaT
    # 转换为字符串并移除特殊字符
    date_str = str(date_str).replace("份", "").replace("度", "").strip()
    # 尝试多种格式解析
    formats = ["%Y年%m月", "%Y-%m", "%Y/%m", "%Y年%m", "%Y%m", "%Y年%m月%d日", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except (ValueError, TypeError):
            continue
    # 如果所有格式都失败，使用dateutil.parser尝试自动解析
    try:
        return pd.to_datetime(date_str)
    except (ValueError, TypeError):
        return pd.NaT

# 获取货币供应量数据
def get_money_supply_data():
    try:
        # 获取全部货币供应数据
        df_money = ak.macro_china_money_supply()
        # 保存全部字段到Excel
        df_money.to_excel("货币供应量全量数据.xlsx", index=False, engine="openpyxl")
        print("货币供应量数据已保存至：货币供应量全量数据.xlsx")
        return df_money
    except Exception as e:
        print(f"获取货币供应数据失败: {e}")
        return None

# 获取中证全指数据
def get_index_data(start_date="20120831"):
    try:
        # 获取今天的日期
        today = datetime.datetime.today().strftime("%Y%m%d")
        # 获取中证全指(000985)的全量数据
        df_index = ak.stock_zh_index_hist_csindex(symbol="000985", start_date=start_date, end_date=today)
        # 保存全部字段到Excel
        df_index.to_excel("中证全指全量数据.xlsx", index=False, engine="openpyxl")
        print("中证全指数据已保存至：中证全指全量数据.xlsx")
        return df_index
    except Exception as e:
        print(f"获取指数数据失败: {e}")
        return None

# 数据处理与可视化
def process_and_visualize(df_money, df_index):
    if df_money is None or df_index is None:
        print("数据不完整，无法进行处理和可视化")
        return
    
    # 调试：打印数据日期范围
    print(f"货币数据日期范围: {df_money['date'].min()} to {df_money['date'].max()}")
    print(f"指数数据日期范围: {df_index['date'].min()} to {df_index['date'].max()}")
    
    # 将货币数据日期调整为当月最后一天
    df_money["date"] = df_money["date"] + pd.offsets.MonthEnd(0)
    print(f"调整后货币数据日期范围: {df_money['date'].min()} to {df_money['date'].max()}")
    
    # 提取M1和M2列（优先使用现成的同比增长率，如果没有则使用数量列计算）
    # M1和M2数量列名
    m1_quantity_columns = ["货币(M1)供应量", "M1", "m1", "货币(M1)", "M1供应量", "货币(M1)-数量(亿元)"]
    m2_quantity_columns = ["货币和准货币(M2)供应量", "M2", "m2", "货币和准货币(M2)", "M2供应量", "货币和准货币(M2)-数量(亿元)"]
    
    # M1和M2同比增长率列名
    m1_growth_columns = ["货币(M1)-同比增长", "M1同比", "m1_growth", "货币(M1)同比增长率"]
    m2_growth_columns = ["货币和准货币(M2)-同比增长", "M2同比", "m2_growth", "货币和准货币(M2)同比增长率"]
    
    # 查找增长率列
    m1_growth_col = next((col for col in m1_growth_columns if col in df_money.columns), None)
    m2_growth_col = next((col for col in m2_growth_columns if col in df_money.columns), None)
    
    # 如果没有增长率列，则查找数量列并计算增长率
    if not m1_growth_col or not m2_growth_col:
        m1_col = next((col for col in m1_quantity_columns if col in df_money.columns), None)
        m2_col = next((col for col in m2_quantity_columns if col in df_money.columns), None)
        
        if not m1_col or not m2_col:
            print(f"无法找到M1或M2列，可用列名: {df_money.columns.tolist()}")
            return
        
        # 计算同比增长率
        df_money["m1_growth"] = df_money[m1_col].pct_change(periods=12) * 100
        df_money["m2_growth"] = df_money[m2_col].pct_change(periods=12) * 100
        m1_growth_col = "m1_growth"
        m2_growth_col = "m2_growth"
    
    # 调试：检查增长率数据
    print(f"M1增长率非空数据量: {df_money[m1_growth_col].notna().sum()}")
    print(f"M2增长率非空数据量: {df_money[m2_growth_col].notna().sum()}")
    
    # 过滤掉增长率为NaN的行
    df_money = df_money.dropna(subset=[m1_growth_col, m2_growth_col])
    if df_money.empty:
        print("过滤后货币数据为空，无法继续处理")
        return
    
    # 处理指数数据：转换为月度数据（取每月最后一个交易日的收盘价）
    close_columns = ["close", "收盘价", "收盘"]
    close_col = next((col for col in close_columns if col in df_index.columns), None)
    if not close_col:
        print(f"无法找到收盘价列，可用列名: {df_index.columns.tolist()}")
        return
    df_index = df_index.rename(columns={close_col: "close"})
    
    df_index_monthly = df_index.resample("ME", on="date").last().reset_index()
    # 调试：检查月度指数数据
    print(f"月度指数数据形状: {df_index_monthly.shape}")
    print(f"月度指数日期范围: {df_index_monthly['date'].min()} to {df_index_monthly['date'].max()}")
    
    # 合并数据（按日期）
    df_merged = pd.merge(
        df_index_monthly[["date", "close"]],
        df_money[["date", m1_growth_col, m2_growth_col]],
        on="date",
        how="inner"
    )
    
    # 调试：检查合并后的数据
    print(f"合并后的数据形状: {df_merged.shape}")
    print("合并后的数据前5行:")
    print(df_merged.head())
    
    if df_merged.empty:
        # 如果精确日期匹配失败，尝试按年月匹配
        print("精确日期匹配失败，尝试按年月匹配...")
        df_money["year_month"] = df_money["date"].dt.to_period("M")
        df_index_monthly["year_month"] = df_index_monthly["date"].dt.to_period("M")
        
        df_merged = pd.merge(
            df_index_monthly[["year_month", "close"]],
            df_money[["year_month", m1_growth_col, m2_growth_col]],
            on="year_month",
            how="inner"
        )
        
        # 恢复日期列
        if not df_merged.empty:
            df_merged["date"] = df_merged["year_month"].dt.to_timestamp() + pd.offsets.MonthEnd(0)
            print(f"年月匹配后的数据形状: {df_merged.shape}")
            print("年月匹配后的数据前5行:")
            print(df_merged.head())
        else:
            print("年月匹配后的数据仍然为空，无法绘图")
            return
    
    # 重命名增长率列，统一为m1_growth和m2_growth
    df_merged = df_merged.rename(columns={
        m1_growth_col: "m1_growth",
        m2_growth_col: "m2_growth"
    })
    
    # 计算M1-M2差值
    df_merged["m1_m2_diff"] = df_merged["m1_growth"] - df_merged["m2_growth"]
    
    # 可视化
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # 上子图：中证全指收盘价 vs M1、M2增长率
    ax1.plot(df_merged["date"], df_merged["close"], color="blue", label="中证全指收盘价")
    ax1.set_ylabel("收盘价", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.legend(loc="upper left")
    
    ax1_right = ax1.twinx()
    ax1_right.plot(df_merged["date"], df_merged["m1_growth"], color="red", label="M1增长率(%)", linestyle="--")
    ax1_right.plot(df_merged["date"], df_merged["m2_growth"], color="green", label="M2增长率(%)", linestyle="-.")
    ax1_right.set_ylabel("增长率(%)")
    ax1_right.legend(loc="upper right")
    ax1.set_title("中证全指收盘价与货币供应量增长率对比")
    
    # 下子图：中证全指收盘价 vs M1-M2差值
    ax2.plot(df_merged["date"], df_merged["close"], color="blue", label="中证全指收盘价")
    ax2.set_ylabel("收盘价", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")
    ax2.legend(loc="upper left")
    
    ax2_right = ax2.twinx()
    ax2_right.plot(df_merged["date"], df_merged["m1_m2_diff"], color="purple", label="M1-M2增长率差(%)")
    ax2_right.set_ylabel("M1-M2差(%)", color="purple")
    ax2_right.tick_params(axis="y", labelcolor="purple")
    ax2_right.legend(loc="upper right")
    ax2.set_title("中证全指收盘价与M1-M2增长率差对比")
    
    # 设置日期格式
    date_format = DateFormatter("%Y-%m")
    ax2.xaxis.set_major_formatter(date_format)
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    # 保存图表
    plt.savefig("货币供应量与股市关系图表.png", dpi=300, bbox_inches="tight")
    print("图表已保存至：货币供应量与股市关系图表.png")

if __name__ == "__main__":
    # 获取数据
    df_money = get_money_supply_data()
    df_index = get_index_data()
    
    # 预处理货币数据日期列（根据用户反馈，日期列名为"月份"）
    date_columns = ["月份", "date", "datetime", "时间", "统计时间", "trade_date", "交易日", "日期"]
    if df_money is not None and not df_money.empty:
        # 处理货币数据日期列
        date_col_money = next((col for col in date_columns if col in df_money.columns), None)
        if date_col_money:
            df_money = df_money.rename(columns={date_col_money: "date"})
            df_money["date"] = df_money["date"].apply(parse_chinese_date)
            df_money = df_money.dropna(subset=["date"])
            df_money = df_money.sort_values("date")
            
            # 根据货币数据调整指数数据起始日期
            if not df_money.empty:
                min_money_date = df_money["date"].min().strftime("%Y%m%d")
                # 重新获取匹配日期范围的指数数据
                df_index = get_index_data(start_date=min_money_date)
    
    # 预处理指数数据日期列
    if df_index is not None and not df_index.empty:
        date_col_index = next((col for col in date_columns if col in df_index.columns), None)
        if date_col_index:
            df_index = df_index.rename(columns={date_col_index: "date"})
            df_index["date"] = pd.to_datetime(df_index["date"])
            df_index = df_index.sort_values("date")
        else:
            print(f"指数数据中无法找到日期列，可用列名: {df_index.columns.tolist()}")
    
    # 处理数据并可视化
    process_and_visualize(df_money, df_index)