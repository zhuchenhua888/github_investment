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

# 提取A股总市值字段
if '总市值' in buffett_data.columns:
    total_market_value = buffett_data[['日期', '总市值']].copy()
    
    # 保存为Excel文件
    try:
        total_market_value.to_excel('数据-A股总市值数据.xlsx', index=False, engine='openpyxl')
        print("A股总市值数据已保存到 '数据-A股总市值数据.xlsx'")
    except Exception as e:
        print(f"保存Excel文件失败: {e}")
        exit()
    
    # 绘制A股总市值趋势图
    try:
        plt.figure(figsize=(12, 6))
        plt.plot(total_market_value['日期'], total_market_value['总市值'], marker='o', color='b')
        plt.title('中国A股总市值趋势图')
        plt.xlabel('日期')
        plt.ylabel('总市值（亿元）')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 保存图表
        plt.savefig('A股总市值趋势图.png')
        print("A股总市值趋势图已保存到 'A股总市值趋势图.png'")
    except Exception as e:
        print(f"绘制图表失败: {e}")
else:
    print("错误：数据中未找到总市值'字段")
    print(f"可用字段: {buffett_data.columns.tolist()}")