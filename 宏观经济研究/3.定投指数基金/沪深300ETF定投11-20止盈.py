import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import random
from datetime import timedelta
import time
import seaborn as sns
from 自定义XIRR计算函数 import custom_xirr  # 导入自定义XIRR函数

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# ---------------------- 数据加载 ----------------------
def load_etf_data(file_path='沪深300及ETF收盘价数据.csv'):
    """从CSV文件加载ETF数据"""
    try:
        df = pd.read_csv(file_path, parse_dates=['date'])
        df = df.sort_values('date').reset_index(drop=True)
        print(f"成功加载数据: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")
        return df[['date', 'nav']]
    except Exception as e:
        print(f"加载数据失败: {e}")
        return get_etf_data()

def get_etf_data(max_retries=3):
    """获取沪深300ETF历史数据"""
    etf_code = "510310"
    retry_count = 0
    while retry_count < max_retries:
        try:
            df = ak.fund_etf_hist_em(symbol=etf_code, adjust="qfq")
            if '日期' not in df.columns or '收盘' not in df.columns:
                print(f"字段不匹配: {df.columns.tolist()}")
                retry_count +=1
                time.sleep(2)
                continue
            df['date'] = pd.to_datetime(df['日期'])
            df = df[['date', '收盘']].rename(columns={'收盘': 'nav'})
            df = df.sort_values('date').reset_index(drop=True)
            df.to_csv('沪深300及ETF收盘价数据.csv', index=False, encoding='utf-8-sig')
            return df
        except Exception as e:
            print(f"获取失败: {str(e)[:50]}...")
            retry_count +=1
            time.sleep(2)
    return None

# ---------------------- 定投策略模拟（含现金流跟踪） ----------------------
def simulate_strategy(data, start_date, 定投金额=1000, 止盈比例=0.15, 最小周期=52):
    """
    模拟单一定投策略，计算XIRR和累计收益率
    返回包含现金流的策略结果
    """
    # 截取起始日期后的数据
    df = data[data['date'] >= start_date].copy()
    if len(df) < 最小周期 * 2:  # 确保有足够数据
        return None
    
    # 设置每周一定投
    df['weekday'] = df['date'].dt.weekday == 0  # 周一标记
    定投日 = df[df['weekday']].copy()
    
    # 若无周一数据用周二
    if len(定投日) < int(len(df)/5):
        df['weekday'] = df['date'].dt.weekday == 1
        定投日 = df[df['weekday']].copy()
    
    if len(定投日) < 最小周期:
        return None
    
    # ---------------------- 初始化参数 ----------------------
    累计投入 = 0
    累计份额 = 0
    止盈次数 = 0
    现金流 = []  # 记录现金流：(日期, 金额)，负数为投入，正数为止盈
    
    # ---------------------- 模拟定投和止盈 ----------------------
    for i, row in 定投日.iterrows():
        date = row['date']
        nav = row['nav']
        
        # 定投投入（现金流出）
        累计投入 += 定投金额
        累计份额 += 定投金额 / nav
        现金流.append((date, -定投金额))  # 负号表示支出
        
        # 当前市值
        当前市值 = 累计份额 * nav
        
        # 检查止盈(至少定投最小周期后)
        if i >= 最小周期 and (当前市值 / 累计投入 - 1) >= 止盈比例:
            # 触发止盈（现金流入）
            止盈金额 = 当前市值
            现金流.append((date, 止盈金额))  # 正数表示收入
            止盈次数 += 1
            
            # 重置累计值，准备下一轮定投
            累计份额 = 0
            累计投入 = 0
    
    # 最后剩余市值作为最终现金流
    if 累计份额 > 0:
        最终日期 = 定投日.iloc[-1]['date']
        最终市值 = 累计份额 * 定投日.iloc[-1]['nav']
        现金流.append((最终日期, 最终市值))
    
    # ---------------------- 计算指标 ----------------------
    # 总投入 = 所有负现金流之和的绝对值
    总投入 = sum(abs(amount) for date, amount in 现金流 if amount < 0)
    # 总产出 = 所有正现金流之和
    总产出 = sum(amount for date, amount in 现金流 if amount > 0)
    
    # 累计收益率
    累计收益率 = (总产出 - 总投入) / 总投入 if 总投入 > 0 else 0
    
    # XIRR计算（使用自定义函数）
    dates = [date for date, amount in 现金流]
    amounts = [amount for date, amount in 现金流]
    xirr = custom_xirr(amounts, dates)
    
    return {
        'start_date': start_date,
        '止盈比例': 止盈比例,
        '总投入': round(总投入, 2),
        '总产出': round(总产出, 2),
        '累计收益率': round(累计收益率, 4),
        'XIRR': round(xirr, 6) if not np.isnan(xirr) else None,
        '止盈次数': 止盈次数,
        '定投周数': len(定投日),
        '现金流': 现金流
    }

# ---------------------- 多策略对比 ----------------------
def multi_strategy_comparison(data, 止盈列表=[0.15], 样本数量=30):
    """多止盈策略对比，计算XIRR和累计收益率"""
    # 获取候选日期
    可用日期 = data['date'].unique() 
    候选日期 = [d for d in 可用日期 if d <= 可用日期[-1] - timedelta(weeks=52*3)]
    if len(候选日期) < 样本数量:
        样本数量 = len(候选日期)
    随机日期 = random.sample(list(候选日期), 样本数量)
    
    结果列表 = []
    
    for start_date in 随机日期:
        子数据 = data[data['date'] >= start_date].copy()
        if len(子数据) < 52*3:
            continue
            
        for 止盈比例 in 止盈列表:
            res = simulate_strategy(
                data=子数据,
                start_date=start_date,
                止盈比例=止盈比例
            )
            if res:
                结果列表.append(res)
    
    return pd.DataFrame(结果列表)

# ---------------------- 结果可视化 ----------------------
def plot_results(结果df):
    """绘制收益率对比图表"""
    # 过滤掉XIRR为空的数据
    有效数据 = 结果df.dropna(subset=['XIRR'])
    
    if len(有效数据) < 5:
        print("有效数据不足，无法绘图")
        return []
    
    # 1. 不同止盈策略的XIRR箱线图
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=有效数据, x='止盈比例', y='XIRR')
    plt.title('不同止盈策略的XIRR分布')
    plt.xlabel('止盈比例')
    plt.ylabel('XIRR真实收益率')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('XIRR箱线图.png', dpi=300)
    
    # 2. XIRR与累计收益率对比散点图
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=有效数据, x='累计收益率', y='XIRR', hue='止盈比例', s=80)
    plt.title('XIRR与累计收益率对比')
    plt.xlabel('累计收益率')
    plt.ylabel('XIRR真实收益率')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('XIRR与累计收益率对比.png', dpi=300)
    
    return ['XIRR箱线图.png', 'XIRR与累计收益率对比.png']

# ---------------------- 主函数 ----------------------
def main():
    # 1. 加载数据
    data = load_etf_data()
    if data is None:
        print("数据加载失败")
        return
    
    # 2. 多策略模拟（11%-20%整数止盈比例）
    止盈列表 = [round(0.11 + i*0.01, 2) for i in range(10)]  # 11%到20%
    print(f"开始计算{len(止盈列表)}个止盈策略的XIRR指标...")
    结果df = multi_strategy_comparison(
        data=data,
        止盈列表=止盈列表,
        样本数量=100  # 用户要求样本数为100
    )
    
    if len(结果df) < 10:
        print("模拟结果不足")
        return
    
    # 3. 保存结果
    结果df.to_csv('多止盈策略对比结果.csv', index=False, encoding='utf-8-sig')
    
    # 4. 生成统计指标
    统计df = 结果df.groupby('止盈比例').agg({
        '累计收益率': ['mean', 'median', 'std'],
        'XIRR': ['mean', 'median', 'std'],
        '止盈次数': 'mean'
    }).round(6)
    统计df.columns = ['_'.join(col) for col in 统计df.columns]
    统计df.to_csv('多止盈策略统计指标.csv', encoding='utf-8-sig')
    
    # 5. 绘制图表
    图表列表 = plot_results(结果df)
    
    print("11%-20%止盈策略对比完成!")
    print("XIRR统计结果:")
    print(统计df[['XIRR_mean', 'XIRR_median', 'XIRR_std']])

if __name__ == "__main__":
    main()