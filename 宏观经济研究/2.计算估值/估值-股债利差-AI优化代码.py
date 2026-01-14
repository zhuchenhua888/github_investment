# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime, timedelta

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

def process_and_plot():
    try:
        # 配置参数
        years = 10  # 10年数据
        date_time = years * 244  # n年乘以244个交易日
        
        # 1、获取股债利差数据
        hs300_pe_df = ak.stock_ebs_lg().iloc[-date_time:].set_index('日期')
        hs300_pe_TTM = hs300_pe_df[['股债利差', '沪深300指数']].copy()
        
        # 处理股债利差（放大100倍）
        hs300_pe_TTM['股债利差'] *= 100
        riskpremium = pd.DataFrame(hs300_pe_TTM['股债利差'])
        
        # 计算分位数和统计值
        q10 = riskpremium.quantile(0.1).values[0]
        q30 = riskpremium.quantile(0.3).values[0]
        q70 = riskpremium.quantile(0.7).values[0]
        q90 = riskpremium.quantile(0.9).values[0]
        mean_val = riskpremium.mean().values[0]
        std_val = riskpremium.std().values[0]
        
        # 划分区间
        df1 = riskpremium[riskpremium > q90]  # 极高
        df2 = riskpremium[(riskpremium > q70) & (riskpremium <= q90)]  # 偏高
        df3 = riskpremium[(riskpremium > q30) & (riskpremium <= q70)]  # 中等
        df4 = riskpremium[(riskpremium > q10) & (riskpremium <= q30)]  # 偏低
        df5 = riskpremium[riskpremium <= q10]  # 极低
        
        # 2、画图
        plt.figure(figsize=(20, 8))
        
        # 绘制沪深300指数（ax1）
        ax1 = plt.gca()
        line1, = ax1.plot(hs300_pe_TTM.index, hs300_pe_TTM['沪深300指数'], 
                         linestyle='--', color='lightgrey', linewidth=2, label='沪深300指数')
        ax1.set_xlabel('日期', fontsize=12)
        ax1.set_ylabel('沪深300指数', fontsize=12)
        ax1.tick_params(axis='y', labelcolor='grey')
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # 创建双纵轴（ax2）
        ax2 = plt.twinx()
        
        # 绘制股债利差曲线
        line2, = ax2.plot(riskpremium.index, riskpremium.values, 
                         color='#4751A5', linewidth=2, label='股债利差')
        
        # 绘制分位数区间点
        scatter1 = ax2.scatter(df1.index, df1.values, color='red', s=30, label='极高(>90%)')
        scatter2 = ax2.scatter(df2.index, df2.values, color='orange', s=20, label='偏高(70%-90%)')
        scatter3 = ax2.scatter(df3.index, df3.values, color='yellow', s=20, label='中等(30%-70%)')
        scatter4 = ax2.scatter(df4.index, df4.values, color='green', s=20, label='偏低(10%-30%)')
        scatter5 = ax2.scatter(df5.index, df5.values, color='blue', s=30, label='极低(<10%)')
        
        # 绘制参考线
        line_p2 = ax2.axhline(y=mean_val + 2*std_val, linestyle='--', color='red', alpha=0.7, label=f'均值+2σ')
        line_p1 = ax2.axhline(y=mean_val + std_val, linestyle='--', color='orange', alpha=0.7, label=f'均值+1σ')
        line_mean = ax2.axhline(y=mean_val, linestyle='--', color='yellow', alpha=0.7, label=f'均值({mean_val:.2f})')
        line_m1 = ax2.axhline(y=mean_val - std_val, linestyle='--', color='green', alpha=0.7, label=f'均值-1σ')
        line_m2 = ax2.axhline(y=mean_val - 2*std_val, linestyle='--', color='blue', alpha=0.7, label=f'均值-2σ')
        
        # 设置右侧纵轴标签
        ax2.set_ylabel('股债利差(%)', fontsize=12)
        
        # 合并图例（只保留唯一标签）
        handles = [line1, line2, scatter1, scatter2, scatter3, scatter4, scatter5, line_mean, line_p1, line_m1, line_p2, line_m2]
        labels = [h.get_label() for h in handles]
        
        # 添加图例
        ax1.legend(handles, labels, loc='upper left', fontsize=10, ncol=2)
        
        plt.title('估值-沪深300指数与股债利差趋势图', fontsize=16, pad=20)
        plt.tight_layout()
        
        # 保存图表（注意：先保存再show，否则会导致保存空白图片）
        plt.savefig('估值-股债利差.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("优化后的图表已保存至: 估值-股债利差.png")
        return '估值-股债利差.png'
        
    except Exception as e:
        print(f"处理过程中出错: {e}")
        return None

if __name__ == "__main__":
    process_and_plot()