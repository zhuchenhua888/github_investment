import akshare as ak
import pandas as pd
import re

# 获取上海证券交易所数据
sse_data = ak.stock_sse_summary()
# 获取深圳证券交易所数据
szse_data = ak.stock_szse_summary()

print("上海证券交易所数据:\n", sse_data)
print("\n深圳证券交易所数据:\n", szse_data)

try:
    # 提取上海证券交易所总市值（项目列为'总市值'的股票列数值，单位：亿元）
    sse_market_cap_str = str(sse_data[sse_data['项目'] == '总市值']['股票'].iloc[0])
    sse_market_cap_clean = re.sub(r'[^0-9.]', '', sse_market_cap_str)
    sse_market_cap = float(sse_market_cap_clean)  # 单位：亿元
    
    # 提取深圳证券交易所总市值（证券类别为'股票'的总市值列数值，单位：元）
    szse_market_cap = szse_data[szse_data['证券类别'] == '股票']['总市值'].iloc[0]
    szse_market_cap = float(szse_market_cap) / 100000000  # 转换为亿元
    
    # 计算A股总市值
    total_market_cap = sse_market_cap + szse_market_cap
    
    # 保存结果，保留两位小数
    result = pd.DataFrame({
        '交易所': ['上海证券交易所', '深圳证券交易所', 'A股总计'],
        '总市值(亿元)': [round(sse_market_cap, 2), round(szse_market_cap, 2), round(total_market_cap, 2)]
    })
    result.to_csv('a股总市值数据.csv', index=False, encoding='utf-8')
    print("A股总市值数据已保存到 'a股总市值数据.csv'")
    print(result)
except IndexError as e:
    print(f"错误：未找到指定行 - {e}")
except KeyError as e:
    print(f"错误：未找到指定列 - {e}")
except Exception as e:
    print(f"处理数据时发生错误: {e}")
    print(f"sse_market_cap: {sse_market_cap}, szse_market_cap: {szse_market_cap}")