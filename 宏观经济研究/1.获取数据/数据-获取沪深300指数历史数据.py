import akshare as ak
import pandas as pd

# 获取沪深300指数历史数据（代码sh000300）
df = ak.stock_zh_index_daily(symbol="sh000300")
print(df)
# 确保数据按日期升序排列
df = df.sort_index(ascending=True)

# 保存数据到CSV文件
df.to_csv("数据-沪深300指数历史数据_新浪.csv", encoding="utf-8-sig")
print("数据已成功保存至沪深300指数历史数据.csv")