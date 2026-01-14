import akshare as ak
import pandas as pd

try:
    # 调用akshare接口获取全量可转债数据
    bond_cov_df = ak.bond_zh_cov()
    
    # 检查数据是否获取成功
    if bond_cov_df.empty:
        print("获取到的可转债数据为空，请检查接口是否正常")
    else:
        # 保存数据到CSV文件
        file_name = "数据-全量可转债数据-东财.csv"
        bond_cov_df.to_csv(file_name, index=False, encoding="utf-8-sig")
        print(f"成功获取并保存全量可转债数据，文件名为：{file_name}")
except Exception as e:
    print(f"获取可转债数据时发生错误：{str(e)}")