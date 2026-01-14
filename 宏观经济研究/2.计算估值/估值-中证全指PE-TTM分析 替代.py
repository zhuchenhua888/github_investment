import akshare as ak
import pandas as pd
import os

# 设置中文显示
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

def get_csi_all_index_data():
    """获取中证全指收盘价数据"""
    try:
        # 中证全指代码为000985，移除adjust参数
        df_close = ak.index_zh_a_hist(
            symbol="000985",
            period="daily",
            start_date="20050101",
            end_date="20250826"
        )
        # 保留日期和收盘价列
        df_close = df_close[['日期', '收盘']].rename(columns={'收盘': '收盘价'})
        print(f"成功获取中证全指收盘价数据，共{len(df_close)}条记录")
        return df_close
    except Exception as e:
        print(f"获取收盘价数据失败: {e}")
        return None

def get_market_pe_data():
    """获取全市场PE-TTM数据"""
    try:
        # 使用stock_a_ttm_lyr替代stock_a_pe
        df_pe = ak.stock_a_ttm_lyr()
        print(df_pe)
        
        # 保留日期和PE-TTM列
        df_pe = df_pe[['date', 'middlePETTM']].rename(columns={
            'date': '日期',
            'middlePETTM': 'PE-TTM'
        })
        print(f"成功获取市场PE-TTM数据，共{len(df_pe)}条记录")
        return df_pe
    except Exception as e:
        print(f"获取PE-TTM数据失败: {e}")
        return None

def merge_data(df_close, df_pe):
    """合并收盘价和PE-TTM数据"""
    if df_close is None or df_pe is None:
        print("数据不完整，无法合并")
        return None
    
    # 转换日期格式
    df_close['日期'] = pd.to_datetime(df_close['日期'])
    df_pe['日期'] = pd.to_datetime(df_pe['日期'])
    
    # 合并数据
    df_merged = pd.merge(df_close, df_pe, on='日期', how='inner')
    print(f"数据合并完成，共{len(df_merged)}条匹配记录")
    return df_merged

def save_data(df, file_name):
    """保存数据到Excel文件"""
    if df is None or len(df) == 0:
        print("没有数据可保存")
        return False
    
    try:
        df.to_excel(file_name, index=False)
        print(f"数据已保存至{file_name}")
        return True
    except Exception as e:
        print(f"保存文件失败: {e}")
        return False

if __name__ == "__main__":
    # 获取收盘价数据
    df_close = get_csi_all_index_data()
    
    # 获取PE-TTM数据
    df_pe = get_market_pe_data()
    
    # 合并数据
    df_merged = merge_data(df_close, df_pe)
    
    # 保存结果
    if df_merged is not None:
        save_data(df_merged, "中证全指PE-TTM替代方案数据.xlsx")