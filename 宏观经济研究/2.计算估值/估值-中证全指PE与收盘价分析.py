import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def load_data(file_path):
    """加载数据"""
    try:
        df = pd.read_excel(file_path)
        df['日期'] = pd.to_datetime(df['日期'])
        print(f"成功加载数据，共{len(df)}条记录")
        return df
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None

def calculate_pe_percentile(df):
    """计算PE-TTM的历史分位点"""
    if df is None or 'PE-TTM' not in df.columns:
        print("数据不完整，无法计算分位点")
        return df
    
    # 计算PE-TTM的历史分位点
    df = df.sort_values('日期').copy()
    df['PE-TTM分位点'] = df['PE-TTM'].rank(pct=True) * 100
    
    # 获取最新的PE-TTM和分位点
    latest_pe = df.iloc[-1]['PE-TTM']
    latest_percentile = df.iloc[-1]['PE-TTM分位点']
    print(f"当前PE-TTM: {latest_pe:.2f}，历史分位点: {latest_percentile:.1f}%")
    
    return df

def plot_pe_and_price(df):
    """绘制PE-TTM和收盘价双Y轴图表"""
    if df is None or len(df) == 0:
        print("没有数据可绘制图表")
        return False
    
    try:
        fig, ax1 = plt.subplots(figsize=(16, 8))
        
        # 绘制收盘价
        ax1.plot(df['日期'], df['收盘价'], 'b-', linewidth=2, label='收盘价')
        ax1.set_xlabel('日期', fontsize=12)
        ax1.set_ylabel('收盘价', color='b', fontsize=12)
        ax1.tick_params('y', colors='b')
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # 创建第二个Y轴用于PE-TTM
        ax2 = ax1.twinx()
        ax2.plot(df['日期'], df['PE-TTM'], 'r-', linewidth=2, label='PE-TTM')
        ax2.set_ylabel('PE-TTM', color='r', fontsize=12)
        ax2.tick_params('y', colors='r')
        
        # 添加标题和图例
        title = f'中证全指PE-TTM与收盘价走势 (2005-2025)'
        plt.title(title, fontsize=16, pad=20)
        
        # 合并图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=12)
        
        # 添加PE-TTM分位点参考线
        current_percentile = df.iloc[-1]['PE-TTM分位点']
        color = 'green' if current_percentile < 30 else 'red' if current_percentile > 70 else 'orange'
        ax2.axhline(y=df.iloc[-1]['PE-TTM'], color=color, linestyle='--', 
                    label=f'当前PE-TTM: {df.iloc[-1]["PE-TTM"]:.2f} ({current_percentile:.1f}%)')
        
        # 优化X轴日期显示
        plt.xticks(rotation=45)
        fig.tight_layout()
        
        # 保存图表
        plt.savefig('中证全指PE与收盘价图表.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("图表生成成功: 中证全指PE与收盘价图表.png")
        return True
    except Exception as e:
        print(f"绘制图表失败: {e}")
        return False

def save_updated_data(df):
    """保存包含分位点的数据"""
    if df is None or len(df) == 0:
        print("没有数据可保存")
        return False
    
    try:
        df.to_excel('中证全指PE与收盘价数据.xlsx', index=False)
        print("包含分位点的数据已保存至: 中证全指PE与收盘价数据.xlsx")
        return True
    except Exception as e:
        print(f"保存数据失败: {e}")
        return False

if __name__ == "__main__":
    # 加载数据
    data = load_data('中证全指PE-TTM替代方案数据.xlsx')
    
    if data is not None:
        # 计算PE-TTM分位点
        data_with_percentile = calculate_pe_percentile(data)
        
        # 绘制图表
        plot_success = plot_pe_and_price(data_with_percentile)
        
        # 保存更新后的数据
        if plot_success:
            save_updated_data(data_with_percentile)