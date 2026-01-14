import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# 设置matplotlib中文显示
matplotlib.rcParams["font.family"] = ["SimHei"]
matplotlib.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 登录baostock
lg = bs.login()
if lg.error_code != '0':
    raise ConnectionError(f"登录失败: {lg.error_msg}")
print('登录状态：', lg.error_code, lg.error_msg)

# 获取月度货币供应数据
rs = bs.query_money_supply_data_month()
if rs.error_code != '0':
    bs.logout()
    raise RuntimeError(f"数据获取失败: {rs.error_msg}")
print('数据获取状态：', rs.error_code, rs.error_msg)

# 解析数据为DataFrame
data_list = []
while (rs.error_code == '0') & rs.next():
    data_list.append(rs.get_row_data())
money_supply_df = pd.DataFrame(data_list, columns=rs.fields)

# 登出baostock
bs.logout()

# 查看数据列名
print("数据列名:", money_supply_df.columns.tolist())

# 明确指定列名（根据实际返回的列名）
year_col = 'statYear'    # 年份列
month_col = 'statMonth'  # 月份列
m1_col = 'm1Month'       # M1数量列（亿元）
m2_col = 'm2Month'       # M2数量列（亿元）

# 检查必要列是否存在
required_cols = [year_col, month_col, m1_col, m2_col]
missing_cols = [col for col in required_cols if col not in money_supply_df.columns]
if missing_cols:
    raise ValueError(f"数据中缺少必要的列: {missing_cols}")

# 合并年份和月份为日期列
money_supply_df['date'] = money_supply_df[year_col] + '-' + money_supply_df[month_col].str.zfill(2)
money_supply_df['date'] = pd.to_datetime(money_supply_df['date'])

# 转换数值列数据类型
money_supply_df[m1_col] = pd.to_numeric(money_supply_df[m1_col], errors='coerce')
money_supply_df[m2_col] = pd.to_numeric(money_supply_df[m2_col], errors='coerce')

# 筛选所需列并移除空值
m1m2_df = money_supply_df[['date', m1_col, m2_col]].copy()
m1m2_df = m1m2_df.dropna()

# 按日期排序
m1m2_df = m1m2_df.sort_values(by='date')

# 保存为Excel文件
try:
    m1m2_df.to_excel('数据-M1和M2月度数据.xlsx', index=False, engine='openpyxl')
    print("数据-M1和M2月度数据已保存到 '数据-M1和M2月度数据.xlsx'")
except Exception as e:
    print(f"保存Excel文件失败: {e}")
    exit()
    
# 绘制M1和M2对比图表
plt.figure(figsize=(14, 7))

# 绘制M1和M2曲线
plt.plot(m1m2_df['date'], m1m2_df[m1_col], marker="o", linestyle="-", color="blue", label="M1供应量(亿元)")
plt.plot(m1m2_df['date'], m1m2_df[m2_col], marker="s", linestyle="-", color="red", label="M2供应量(亿元)")

# 设置图表属性
plt.title("中国M1和M2月度供应量走势对比")
plt.xlabel("日期")
plt.ylabel("供应量(亿元)")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()

# 保存图表
save_path = '数据-M1和M2月度数据趋势图-baostock.png'
plt.savefig(save_path, dpi=300)
print(f"图表已保存至: {save_path}")