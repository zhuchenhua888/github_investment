import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os

# 设置matplotlib中文显示
matplotlib.rcParams["font.family"] = ["SimHei"]
matplotlib.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 获取巴菲特指数数据
try:
    macro_china_fx_reserves_yearly_df = ak.macro_china_fx_reserves_yearly()
    print("成功获取巴菲特指数数据，字段包括:", macro_china_fx_reserves_yearly_df.columns.tolist())

except Exception as e:
    print(f"获取数据失败: {e}")
    exit()

# 提取GDP字段
if '今值' in macro_china_fx_reserves_yearly_df.columns:
    data = macro_china_fx_reserves_yearly_df[['日期', '今值']].copy()
    
    # 保存为Excel文件
    try:
        data.to_excel('数据-中国外汇储备.xlsx', index=False, engine='openpyxl')
        print("数据-中国外汇储备已保存到 '数据-中国外汇储备.xlsx'")
    except Exception as e:
        print(f"保存Excel文件失败: {e}")
        exit()
    
    # 绘制GDP趋势图
    try:
        plt.figure(figsize=(12, 6))
        plt.plot(data['日期'], data['今值'], linestyle="-", color="b", label="中国外汇储备趋势图（亿美元）")

        plt.title('中国外汇储备趋势图')
        plt.xlabel('日期')
        plt.ylabel('今值（亿美元）')
        plt.xticks(rotation=45)
        plt.tight_layout()
      
        # 保存图表
        plt.savefig('数据-中国外汇储备趋势图.png')
        print("中国外汇储备趋势图已保存到 '数据-中国外汇储备趋势图.png'")
    except Exception as e:
        print(f"绘制图表失败: {e}")
else:
    print("错误：数据中未找到'今值'字段")
    print(f"可用字段: {macro_china_fx_reserves_yearly_df.columns.tolist()}")
    

