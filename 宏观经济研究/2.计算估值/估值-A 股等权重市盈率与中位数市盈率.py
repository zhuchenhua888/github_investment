import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

def get_a_stock_pe():
    """获取A股等权重市盈率与中位数市盈率"""
    try:
        # 调用接口
        df = ak.stock_a_ttm_lyr()
        print(f"接口返回列名: {df.columns.tolist()}")
        
        # 确认日期列和数据列（根据实际返回调整）
        date_col = "date"  # 接口返回列名为'date'
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 重命名列：映射英文/拼音字段到目标列名
        df = df.rename(columns={
            date_col: "date",
            "averagePETTM": "equal_weight_pe",  # 平均市盈率TTM -> 等权重市盈率
            "middlePETTM": "median_pe"          # 中位数市盈率TTM -> 中位数市盈率
        })
        
        # 检查必要列是否存在
        required_cols = ["date", "equal_weight_pe", "median_pe"]
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"接口返回数据缺少必要列，当前列名: {df.columns.tolist()}")
            
        return df[required_cols].sort_values("date")
    except Exception as e:
        print(f"获取数据失败: {e}")
        return None

def plot_pe_chart(df):
    """绘制市盈率图表并保存为图片"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制等权重市盈率
    ax.plot(df["date"], df["equal_weight_pe"], color="#1f77b4", label="等权重市盈率(TTM)")
    # 绘制中位数市盈率
    ax.plot(df["date"], df["median_pe"], color="#ff7f0e", label="中位数市盈率(TTM)")
    
    ax.set_xlabel("日期")
    ax.set_ylabel("市盈率")
    ax.set_title("A股等权重与中位数市盈率趋势对比")
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.legend()
    
    # 保存图表为图片
    file_name = "估值-A股等权重与中位数市盈率趋势对比.png"
    plt.savefig(file_name, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"图表已保存至{file_name}")

def main():
    pe_df = get_a_stock_pe()
    if pe_df is not None:
        plot_pe_chart(pe_df)

if __name__ == "__main__":
    main()