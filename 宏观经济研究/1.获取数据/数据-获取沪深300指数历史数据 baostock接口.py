import baostock as bs
import pandas as pd

# 初始化baostock
lg = bs.login()
if lg.error_code != '0':
    print(f"登录失败：{lg.error_msg}")
    exit()

# 获取沪深300全收益指数（CSI 300 Total Return Index）数据
fields = "date,code,open,high,low,close,volume,amount,pctChg"
start_date = "2005-04-08"  # 指数发布日期
end_date = pd.Timestamp.now().strftime("%Y-%m-%d")  # 当前日期

rs = bs.query_history_k_data_plus(
    code="sh.000300",  # 沪深300指数代码
    fields=fields,
    start_date=start_date,
    end_date=end_date,
    frequency="d",
    adjustflag="3"  # 后复权（全收益计算）
)

# 处理数据
data_list = []
while (rs.error_code == '0') & rs.next():
    data_list.append(rs.get_row_data())

df = pd.DataFrame(data_list, columns=rs.fields)
df = df.sort_values(by="date", ascending=True)

# 保存为CSV（覆盖或更新现有文件）
file_name = "数据-沪深300指数历史数据_baostock.csv"
df.to_csv(file_name, index=False, encoding="utf-8-sig")
print(f"已更新CSI 300 Total Return Index数据至{end_date}，保存至{file_name}")

# 登出
bs.logout()