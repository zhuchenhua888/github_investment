import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

def plot_buffett_indicator():
    # 获取巴菲特指数数据
    try:
        buffett_data = ak.stock_buffett_index_lg()
        required_columns = ['日期', '收盘价', '总市值', 'GDP', '近十年分位数', '总历史分位数']
        if not all(col in buffett_data.columns for col in required_columns):
            missing = [col for col in required_columns if col not in buffett_data.columns]
            print(f"错误：缺少必要字段: {missing}")
            return None
        data = buffett_data[required_columns].copy()
        return data
    except Exception as e:
        print(f"获取数据失败: {e}")
        return None

def plot_combined_chart(data):
    try:
        # 数据处理
        data["日期"] = pd.to_datetime(data["日期"])
        data = data.sort_values("日期")
        
        # 计算巴菲特指标
        data["巴菲特指标(总市值/GDP)"] = data["总市值"] / data["GDP"]
        
        # 创建包含两个子图的图表
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(2, 1, height_ratios=[2, 2], hspace=0.3)
        
        # 上子图：巴菲特指标和分位数
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(data["日期"], data["巴菲特指标(总市值/GDP)"], color="#1f77b4", linewidth=2, label="巴菲特指标(总市值/GDP)")
        ax1.set_ylabel("巴菲特指标", fontsize=12, color="#1f77b4")
        ax1.tick_params(axis="y", labelcolor="#1f77b4")
        ax1.grid(True, linestyle="--", alpha=0.7)
        
        ax2 = ax1.twinx()
        ax2.plot(data["日期"], data["近十年分位数"], color="#ff7f0e", label="近十年分位数(%)", alpha=0.8)
        ax2.plot(data["日期"], data["总历史分位数"], color="#2ca02c", label="总历史分位数(%)", alpha=0.8)
        ax2.set_ylabel("分位数(%)", fontsize=12)
        ax2.tick_params(axis="y")
        
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
        ax1.set_title("巴菲特指标与分位数趋势", fontsize=14)
        
        # 下子图：GDP与总市值
        ax3 = fig.add_subplot(gs[1])
        ax3.plot(data['日期'], data['GDP'], marker='o', color='b', label='GDP')
        ax3.set_xlabel('日期', fontsize=12)
        ax3.set_ylabel('GDP（亿元）', color='b', fontsize=12)
        ax3.tick_params(axis='y', labelcolor='b')
        ax3.grid(True, linestyle="--", alpha=0.7)
        
        ax4 = ax3.twinx()
        ax4.plot(data['日期'], data['总市值'], marker='s', color='r', label='总市值')
        ax4.set_ylabel('总市值（亿元）', color='r', fontsize=12)
        ax4.tick_params(axis='y', labelcolor='r')
        
        lines3, labels3 = ax3.get_legend_handles_labels()
        lines4, labels4 = ax4.get_legend_handles_labels()
        ax3.legend(lines3 + lines4, labels3 + labels4, loc="upper left")
        ax3.set_title("GDP与总市值趋势", fontsize=14)
        
        # 展示图表
        # plt.show()
        
        # 调整布局并保存
        # plt.tight_layout()
        plt.subplots_adjust(hspace=0.5)  # 手动调整子图之间的间距
        combined_file = "估值-巴菲特指标-合并图表.png"
        plt.savefig(combined_file, dpi=300, bbox_inches="tight")
        print(f"合并图表已保存至{combined_file}")
        
        # 打印最后一条数据
        print(f"近十年分位数: {data['日期'].iloc[-1].strftime('%Y-%m-%d')} : {data['近十年分位数'].iloc[-1]}")
        print(f"总历史分位数: {data['日期'].iloc[-1].strftime('%Y-%m-%d')} : {data['总历史分位数'].iloc[-1]}")
        return combined_file
    except Exception as e:
        print(f"绘制合并图表失败: {e}")
        return None

if __name__ == "__main__":
    data = plot_buffett_indicator()
    if data is not None:
        combined_file = plot_combined_chart(data)
        if combined_file:
            print(f"成功生成合并图表: {combined_file}")
        else:
            print("合并图表生成失败")
    else:
        print("未能获取或处理巴菲特指标数据")