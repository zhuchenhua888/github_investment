import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import random
from datetime import timedelta
import time

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
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
        # 如果本地文件不存在，尝试重新获取
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

# ---------------------- 定投策略模拟 ----------------------
def simulate_strategy(data, start_date, 定投金额=1000, 止盈比例=0.15, 最小周期=52):
    """
    模拟单一定投策略
    data: 完整数据
    start_date: 起始日期
    止盈比例: 止盈阈值
    最小周期: 最小定投周数(避免过早止盈)
    返回: 策略结果字典
    """
    # 截取起始日期后的数据
    df = data[data['date'] >= start_date].copy()
    if len(df) < 最小周期 * 2:  # 确保有足够数据
        return None
    
    # 设置每周一定投
    df['weekday'] = df['date'].dt.weekday
    定投日 = df[df['weekday'] == 0].copy()  # 每周一
    if len(定投日) < 最小周期:
        定投日 = df[df['weekday'] == 1].copy()  # 若无周一数据用周二
    
    # 初始化参数
    累计投入 = 0
    累计份额 = 0
    止盈次数 = 0
    交易记录 = []
    最大回撤 = 0
    历史最高市值 = 0
    
    for i, row in 定投日.iterrows():
        date = row['date']
        nav = row['nav']
        
        # 买入份额
        份额 = 定投金额 / nav
        累计投入 += 定投金额
        累计份额 += 份额
        当前市值 = 累计份额 * nav
        收益率 = (当前市值 - 累计投入) / 累计投入 if 累计投入 > 0 else 0
        
        # 记录历史最高市值和最大回撤
        if 当前市值 > 历史最高市值:
            历史最高市值 = 当前市值
        else:
            回撤 = (历史最高市值 - 当前市值) / 历史最高市值
            if 回撤 > 最大回撤:
                最大回撤 = 回撤
        
        # 记录交易
        交易记录.append({
            'date': date,
            'nav': nav,
            '累计投入': 累计投入,
            '当前市值': 当前市值,
            '收益率': 收益率,
            '止盈事件': False
        })
        
        # 止盈判断(需满足最小周期)
        if i >= 最小周期 and 收益率 >= 止盈比例:
            止盈次数 += 1
            交易记录[-1]['止盈事件'] = True
            累计投入 = 0
            累计份额 = 0
            历史最高市值 = 0  # 重置回撤计算
    
    # 计算最终指标
    最终记录 = 交易记录[-1] if 交易记录 else None
    if not 最终记录:
        return None
    
    return {
        'start_date': start_date,
        '总投入': 最终记录['累计投入'],
        '最终市值': 最终记录['当前市值'],
        '总收益率': 最终记录['收益率'],
        '止盈次数': 止盈次数,
        '定投周数': len(交易记录),
        '最大回撤': 最大回撤,
        '交易记录': 交易记录
    }

# ---------------------- 多策略对比 ----------------------
def multi_strategy_comparison(data, 止盈列表=[0.1, 0.15, 0.2], 样本数量=30, 最小周期=52):
    """
    多止盈策略对比
    data: 完整数据
    止盈列表: 多个止盈比例
    样本数量: 随机起始日期数量
    返回: 对比结果DataFrame
    """
    # 生成随机起始日期
    可用日期 = data['date'].unique()
    候选日期 = [d for d in 可用日期 if d <= 可用日期[-1] - timedelta(weeks=最小周期*2)]
    随机日期 = random.sample(list(候选日期), min(样本数量, len(候选日期)))
    
    结果列表 = []
    
    for start_date in 随机日期:
        for 止盈比例 in 止盈列表:
            res = simulate_strategy(
                data=data,
                start_date=start_date,
                止盈比例=止盈比例,
                最小周期=最小周期
            )
            if res:
                res['止盈比例'] = 止盈比例
                结果列表.append(res)
    
    # 转换为DataFrame
    结果df = pd.DataFrame(结果列表)
    # 计算风险调整后收益
    结果df['夏普比率'] = 结果df['总收益率'] / 结果df['最大回撤'].replace(0, 0.01)
    return 结果df

# ---------------------- 结果可视化 ----------------------
def plot_comparison(结果df):
    """绘制多策略对比图表"""
    # 1. 收益率箱线图
    plt.figure(figsize=(12, 6))
    结果df.boxplot(column='总收益率', by='止盈比例', grid=True)
    plt.title('不同止盈策略的收益率分布')
    plt.suptitle('')  # 移除默认标题
    plt.xlabel('止盈比例')
    plt.ylabel('总收益率')
    plt.tight_layout()
    plt.savefig('收益率分布对比.png', dpi=300)
    
    # 2. 止盈次数与收益率散点图
    plt.figure(figsize=(12, 6))
    for 止盈比例 in 结果df['止盈比例'].unique():
        子集 = 结果df[结果df['止盈比例'] == 止盈比例]
        plt.scatter(子集['止盈次数'], 子集['总收益率'], 
                   label=f'{int(止盈比例*100)}%止盈', alpha=0.6)
    plt.title('止盈次数与总收益率关系')
    plt.xlabel('止盈次数')
    plt.ylabel('总收益率')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('止盈次数与收益率.png', dpi=300)
    
    # 3. 典型策略收益曲线
    plt.figure(figsize=(12, 6))
    典型日期 = 结果df['start_date'].mode()[0]  # 最常见起始日期
    for 止盈比例 in [0.1, 0.15, 0.2]:
        记录 = 结果df[(结果df['start_date'] == 典型日期) & 
                      (结果df['止盈比例'] == 止盈比例)]['交易记录'].iloc[0]
        记录df = pd.DataFrame(记录)
        plt.plot(记录df['date'], 记录df['当前市值'], 
                 label=f'{int(止盈比例*100)}%止盈', linewidth=2)
    plt.title(f'典型起始日期({典型日期.strftime("%Y-%m-%d")})收益曲线')
    plt.xlabel('日期')
    plt.ylabel('累计市值(元)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('典型收益曲线.png', dpi=300)
    
    return ['收益率分布对比.png', '止盈次数与收益率.png', '典型收益曲线.png']

# ---------------------- 主函数 ----------------------
def main():
    # 1. 加载数据
    data = load_etf_data()
    if data is None:
        print("数据加载失败，程序退出")
        return
    
    # 2. 多策略模拟
    print("开始多止盈策略对比模拟...")
    结果df = multi_strategy_comparison(
        data=data,
        止盈列表=[0.1, 0.15, 0.2],
        样本数量=30,
        最小周期=52  # 至少定投1年才允许止盈
    )
    
    if len(结果df) == 0:
        print("模拟结果为空，程序退出")
        return
    
    # 3. 保存结果
    结果df.to_csv('多止盈策略对比结果.csv', index=False, encoding='utf-8-sig')
    
    # 4. 生成统计指标
    统计df = 结果df.groupby('止盈比例').agg({
        '总收益率': ['mean', 'median', 'std'],
        '止盈次数': ['mean', 'max'],
        '最大回撤': ['mean', 'min'],
        '夏普比率': ['mean']
    }).round(4)
    统计df.columns = ['_'.join(col).strip() for col in 统计df.columns.values]
    统计df.to_csv('多止盈策略统计指标.csv', encoding='utf-8-sig')
    
    # 5. 绘制图表
    图表列表 = plot_comparison(结果df)
    
    print("多止盈策略对比分析完成！")
    print("统计指标:")
    print(统计df)

if __name__ == "__main__":
    main()