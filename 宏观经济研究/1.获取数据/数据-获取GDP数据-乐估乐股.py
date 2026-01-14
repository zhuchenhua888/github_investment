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
    buffett_data = ak.stock_buffett_index_lg()
    print("成功获取巴菲特指数数据，字段包括:", buffett_data.columns.tolist())

except Exception as e:
    print(f"获取数据失败: {e}")
    exit()

# 提取GDP字段
if 'GDP' in buffett_data.columns:
    gdp_data = buffett_data[['日期', 'GDP']].copy()
    
    # 保存为Excel文件
    try:
        gdp_data.to_excel('数据-中国GDP.xlsx', index=False, engine='openpyxl')
        print("数据-中国GDP已保存到 '数据-中国GDP.xlsx'")
    except Exception as e:
        print(f"保存Excel文件失败: {e}")
        exit()
    
    # 绘制GDP趋势图
    try:
        plt.figure(figsize=(12, 6))
        plt.plot(gdp_data['日期'], gdp_data['GDP'], marker='o', color='b')
        plt.title('中国GDP趋势图')
        plt.xlabel('日期')
        plt.ylabel('GDP（亿元）')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 保存图表
        plt.savefig('数据-GDP趋势图.png')
        print("GDP趋势图已保存到 '数据-GDP趋势图.png'")
    except Exception as e:
        print(f"绘制图表失败: {e}")
else:
    print("错误：数据中未找到'GDP'字段")
    print(f"可用字段: {buffett_data.columns.tolist()}")