import akshare as ak
import pandas as pd

# 获取融资融券余额数据
margin_df = ak.stock_margin_account_info()
print(margin_df)