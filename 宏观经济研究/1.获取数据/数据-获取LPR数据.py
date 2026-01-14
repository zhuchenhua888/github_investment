import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.font_manager import FontProperties

# 设置中文字体
matplotlib.rcParams["font.family"] = ["SimHei"]
matplotlib.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 获取LPR数据
lpr_df = ak.macro_china_lpr()
print("数据列名:", lpr_df.columns.tolist())

# 数据处理
# 转换日期格式
lpr_df["TRADE_DATE"] = pd.to_datetime(lpr_df["TRADE_DATE"])

# 查看数据基本信息
print("数据形状:", lpr_df.shape)
print("日期范围:", lpr_df["TRADE_DATE"].min(), "至", lpr_df["TRADE_DATE"].max())

# 提取需要展示的指标列
指标列 = ["LPR1Y", "LPR5Y", "RATE_1", "RATE_2"]
numeric_df = lpr_df[["TRADE_DATE"] + 指标列].copy()

# 将数值列转换为float并处理NaN
for col in 指标列:
    numeric_df[col] = pd.to_numeric(numeric_df[col], errors="coerce")

# 按日期排序
numeric_df = numeric_df.sort_values(by="TRADE_DATE")

# 创建2行1列的子图布局，不共享x轴
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 14), sharex=False)

# 上子图：LPR1Y和LPR5Y
ax1.plot(numeric_df["TRADE_DATE"], numeric_df["LPR1Y"], marker="o", linestyle="-", color="#1f77b4", label="LPR_1Y(%)", alpha=0.8)
ax1.plot(numeric_df["TRADE_DATE"], numeric_df["LPR5Y"], marker="s", linestyle="-", color="#ff7f0e", label="LPR_5Y(%)", alpha=0.8)
ax1.set_title("LPR利率走势", fontsize=14)
ax1.set_xlabel("日期", fontsize=12)
ax1.set_ylabel("利率(%)", fontsize=12)
ax1.legend(fontsize=10)
ax1.grid(True, linestyle="--", alpha=0.6)
ax1.tick_params(axis="x", rotation=45)  # x轴标签旋转45度避免重叠

# 下子图：短期和中长期贷款利率
ax2.plot(numeric_df["TRADE_DATE"], numeric_df["RATE_1"], marker="^", linestyle="--", color="#2ca02c", label="短期贷款利率(6个月至1年)(%)", alpha=0.7)
ax2.plot(numeric_df["TRADE_DATE"], numeric_df["RATE_2"], marker="D", linestyle="--", color="#d62728", label="中长期贷款利率(5年以上)(%)", alpha=0.7)
ax2.set_title("贷款利率走势", fontsize=14)
ax2.set_xlabel("日期", fontsize=12)
ax2.set_ylabel("利率(%)", fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, linestyle="--", alpha=0.6)
ax2.tick_params(axis="x", rotation=45)  # x轴标签旋转45度避免重叠

# 调整子图间距
plt.subplots_adjust(hspace=0.4)  # 增加垂直间距
plt.tight_layout()

# 保存图表
save_path = "数据-中国LPR及贷款利率.png"
plt.savefig(save_path, dpi=300, bbox_inches="tight")  # bbox_inches确保标签完整显示
print(f"分图图表已保存至: {save_path}")

# 保存为Excel文件
try:
    numeric_df.to_excel('数据-中国LPR及贷款利率.xlsx', index=False, engine='openpyxl')
    print("数据-中国LPR及贷款利率已保存到 '数据-中国LPR及贷款利率.xlsx'")
except Exception as e:
    print(f"保存Excel文件失败: {e}")
    exit()
    