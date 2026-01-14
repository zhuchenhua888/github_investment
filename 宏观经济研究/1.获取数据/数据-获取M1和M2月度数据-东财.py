import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import re
from matplotlib.font_manager import FontProperties

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 获取所有货币供应量数据
money_supply_df = ak.macro_china_money_supply()
print("成功获取货币供应量数据，字段包括:", money_supply_df.columns.tolist())
print(money_supply_df)
# 定义M1和M2数据列名
m1_column = "货币(M1)-数量(亿元)"  # M1数量列
m2_column = "货币和准货币(M2)-数量(亿元)"  # M2数量列
date_column = "月份"  # 日期列

# 检查必要列是否存在
required_columns = [date_column, m1_column, m2_column]
missing_columns = [col for col in required_columns if col not in money_supply_df.columns]
if missing_columns:
    raise ValueError(f"数据中缺少必要的列: {missing_columns}")

# 提取M1和M2数据
m1m2_df = money_supply_df[[date_column, m1_column, m2_column]].copy()

# 处理日期格式：从"2025年07月份"提取为"2025-07"
def parse_date(date_str):
    match = re.search(r'(\d{4})年(\d{2})月', date_str)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None

m1m2_df[date_column] = m1m2_df[date_column].apply(parse_date)
m1m2_df = m1m2_df.dropna(subset=[date_column])  # 移除解析失败的行
m1m2_df[date_column] = pd.to_datetime(m1m2_df[date_column])

# 转换数值列为数值类型
m1m2_df[m1_column] = pd.to_numeric(m1m2_df[m1_column], errors='coerce')
m1m2_df[m2_column] = pd.to_numeric(m1m2_df[m2_column], errors='coerce')
m1m2_df = m1m2_df.dropna()  # 移除数值为空的行

# 按日期排序
m1m2_df = m1m2_df.sort_values(by=date_column)

# 保存为Excel文件
try:
    m1m2_df.to_excel('数据-M1和M2月度数据-akshare.xlsx', index=False, engine='openpyxl')
    print("数据-M1和M2月度数据已保存到 '数据-M1和M2月度数据-akshare.xlsx'")
except Exception as e:
    print(f"保存Excel文件失败: {e}")
    exit()
    
# 绘制M1和M2对比图表
plt.figure(figsize=(14, 7))

# 绘制M1和M2曲线
plt.plot(m1m2_df[date_column], m1m2_df[m1_column], marker="o", linestyle="-", color="blue", label="M1供应量(亿元)")
plt.plot(m1m2_df[date_column], m1m2_df[m2_column], marker="s", linestyle="-", color="red", label="M2供应量(亿元)")

# 设置图表属性
plt.title("中国M1和M2月度供应量走势对比")
plt.xlabel("日期")
plt.ylabel("供应量(亿元)")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()

# 保存图表
save_path = "数据-M1和M2月度数据趋势图-akshare.png"
plt.savefig(save_path, dpi=300)
print(f"图表已保存至: {save_path}")