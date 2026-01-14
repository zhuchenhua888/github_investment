import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 解析特殊日期格式（如"2025年08月份"）
def parse_special_date(date_str):
    try:
        # 使用正则表达式提取年份和月份
        match = re.match(r'(\d{4})年(\d{2})月份', date_str)
        if match:
            year = match.group(1)
            month = match.group(2)
            return f"{year}-{month}-01"  # 转换为YYYY-MM-DD格式
        # 尝试其他常见格式
        return pd.to_datetime(date_str).strftime("%Y-%m-%d")
    except:
        return None

# 获取股市市值数据
def get_stock_data():
    try:
        # 调用akshare接口获取数据
        df = ak.macro_china_stock_market_cap()
        print("数据获取成功，原始数据列名:", df.columns.tolist())
        
        # 保留所需字段
        required_columns = [
            '数据日期', 
            '发行总股本-上海', '发行总股本-深圳',
            '市价总值-上海', '市价总值-深圳',
            '成交金额-上海', '成交金额-深圳',
            '成交量-上海', '成交量-深圳'
        ]
        df = df[required_columns].rename(columns={'数据日期': '日期'})
        
        # 解析日期
        df['日期'] = df['日期'].apply(parse_special_date)
        df = df.dropna(subset=['日期'])  # 删除无法解析的日期行
        df['日期'] = pd.to_datetime(df['日期'])
        
        # 计算总和列（保持与原始指标名称一致）
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)  # 填充数值列缺失值
        
        # 修正：总和列名添加"发行"前缀，与原始字段保持一致
        df['发行总股本'] = df['发行总股本-上海'] + df['发行总股本-深圳']
        df['市价总值'] = df['市价总值-上海'] + df['市价总值-深圳']
        df['成交金额'] = df['成交金额-上海'] + df['成交金额-深圳']
        df['成交量'] = df['成交量-上海'] + df['成交量-深圳']
        
        return df.sort_values('日期')
    except Exception as e:
        print(f"数据获取失败: {e}")
        return None

# 保存为Excel
def save_to_excel(df, filename):
    try:
        df.to_excel(filename, index=False)
        print(f"Excel文件保存成功: {filename}")
        return True
    except Exception as e:
        print(f"Excel保存失败: {e}")
        return False

# 绘制图表
def plot_charts(df, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 绘制分地区指标图表
    indicators = [
        ('发行总股本', '亿股'),
        ('市价总值', '亿元'),
        ('成交金额', '亿元'),
        ('成交量', '亿股')
    ]
    
    for indicator, unit in indicators:
        plt.figure(figsize=(12, 6))
        # 直接使用完整指标名访问数据，避免split操作
        plt.plot(df['日期'], df[f'{indicator}-上海'], label=f'{indicator}-上海', marker='o', linestyle='-')
        plt.plot(df['日期'], df[f'{indicator}-深圳'], label=f'{indicator}-深圳', marker='s', linestyle='--')
        plt.title(f'{indicator}地区对比趋势图 ({unit})')
        plt.xlabel('日期')
        plt.ylabel(f'{indicator} ({unit})')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/{indicator}_地区对比.png')
        plt.close()
    
    # 绘制总和指标图表
    for indicator, unit in indicators:
        plt.figure(figsize=(12, 6))
        # 直接使用完整指标名访问总和列，无需字符串分割
        plt.plot(df['日期'], df[indicator], label=f'{indicator}总和', marker='*', color='green')
        plt.title(f'{indicator}总和趋势图 ({unit})')
        plt.xlabel('日期')
        plt.ylabel(f'{indicator} ({unit})')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/{indicator}_总和.png')
        plt.close()
    
    print(f"图表保存成功，路径: {output_dir}")

# 主函数
def main():
    # 获取数据
    df = get_stock_data()
    if df is None or df.empty:
        print("无有效数据，终止任务")
        return
    
    plot_dir = './data/数据-获取全国股票交易统计表/'
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    # 保存为Excel
    excel_filename = '数据-中国股市数据汇总.xlsx'
    if not save_to_excel(df, plot_dir+excel_filename):
        return
    
    # 绘制图表
    plot_charts(df, plot_dir)
    
    # 输出结果文件路径
    print("任务完成，生成文件:")
    print(f"Excel文件: {os.path.abspath(plot_dir+ excel_filename)}")
    print(f"图表文件夹: {os.path.abspath(plot_dir)}")

if __name__ == "__main__":
    main()