import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import time

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# ---------------------- 数据获取 ----------------------
def get_etf_data(max_retries=3):
    """获取沪深300ETF历史数据，适配实际返回字段"""
    etf_code = "510310"  # ETF代码
    retry_count = 0
    while retry_count < max_retries:
        try:
            print(f"第{retry_count+1}次尝试获取ETF数据...")
            # 尝试使用东方财富接口
            df = ak.fund_etf_hist_em(
                symbol=etf_code,
                adjust="qfq"  # 前复权
            )
            
            # 适配实际返回字段（['日期', '收盘']）
            if '日期' not in df.columns or '收盘' not in df.columns:
                print(f"数据字段不匹配: {df.columns.tolist()}")
                retry_count += 1
                time.sleep(2)
                continue
                
            # 数据预处理
            df['date'] = pd.to_datetime(df['日期'])
            df = df[['date', '收盘']].rename(columns={'收盘': 'nav'})
            df = df.sort_values('date').reset_index(drop=True)
            
            # 检查数据量
            if len(df) < 100:
                print(f"数据量不足: {len(df)}条记录")
                retry_count += 1
                time.sleep(2)
                continue
                
            print(f"成功获取数据: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")
            return df
        except Exception as e:
            print(f"获取失败: {str(e)[:50]}...")
            retry_count += 1
            time.sleep(2)
    
    print(f"已尝试{max_retries}次，均失败，请检查网络或接口")
    return None

# ---------------------- 定投策略模拟 ----------------------
def simulate定投策略(data, 定投金额=1000, 止盈比例=0.15):
    """
    模拟周定投策略
    data: DataFrame，包含date和nav字段
    定投金额: 每次定投金额
    止盈比例: 止盈阈值(如0.15表示15%)
    返回: 策略结果DataFrame, 止盈次数
    """
    if data is None or len(data) < 100:
        print("数据不足，无法模拟")
        return None, 0
    
    # 设置每周一定投
    data['weekday'] = data['date'].dt.weekday  # 0=周一, 6=周日
    定投日数据 = data[data['weekday'] == 0]  # 每周一定投
    
    # 如果周一数据过少，改用周二
    if len(定投日数据) < len(data) / 10:
        定投日数据 = data[data['weekday'] == 1]  # 每周二定投
        print("周一数据不足，使用周二定投")
    
    if len(定投日数据) == 0:
        print("没有合适的定投日数据")
        return None, 0
    
    # 初始化结果列表
    result = []
    累计投入 = 0
    累计份额 = 0
    止盈次数 = 0
    
    for _, row in 定投日数据.iterrows():
        date = row['date']
        nav = row['nav']
        
        # 买入份额
        份额 = 定投金额 / nav
        累计投入 += 定投金额
        累计份额 += 份额
        
        # 计算当前市值和收益率
        当前市值 = 累计份额 * nav
        收益率 = (当前市值 - 累计投入) / 累计投入 if 累计投入 > 0 else 0
        
        # 记录状态
        记录 = {
            'date': date,
            'nav': nav,
            '投入金额': 定投金额,
            '累计投入': 累计投入,
            '累计份额': 累计份额,
            '当前市值': 当前市值,
            '收益率': 收益率,
            '止盈事件': False
        }
        result.append(记录)
        
        # 检查止盈条件
        if 止盈比例 > 0 and 收益率 >= 止盈比例:
            # 触发止盈
            止盈次数 += 1
            result[-1]['止盈事件'] = True
            result[-1]['止盈次数'] = 止盈次数
            # 重置累计值，开始新一轮定投
            累计投入 = 0
            累计份额 = 0
    
    # 转换为DataFrame
    result_df = pd.DataFrame(result)
    return result_df, 止盈次数

# ---------------------- 结果可视化 ----------------------
def plot_result(result_df, 止盈次数):
    """绘制定投收益图表"""
    if result_df is None or len(result_df) == 0:
        print("没有可绘制的数据")
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制累计投入和当前市值
    ax.plot(result_df['date'], result_df['累计投入'], label='累计投入', color='blue', linestyle='--')
    ax.plot(result_df['date'], result_df['当前市值'], label='当前市值', color='red')
    
    # 标记止盈点
    止盈点 = result_df[result_df['止盈事件'] == True]
    if not 止盈点.empty:
        ax.scatter(止盈点['date'], 止盈点['当前市值'], color='green', s=100, marker='^', label=f'止盈点({止盈次数}次)')
    
    # 设置图表属性
    ax.set_title('沪深300ETF周定投收益模拟(1000元/周，15%止盈)', fontsize=14)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('金额(元)', fontsize=12)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # 格式化日期标签
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    # 保存图表
    save_path = '沪深300ETF定投收益图表.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存: {save_path}")
    return fig

# ---------------------- 主函数 ----------------------
def main():
    # 1. 获取数据
    etf_data = get_etf_data()
    if etf_data is None:
        print("无法获取数据，程序退出")
        return
    
    # 2. 模拟定投策略
    策略结果, 止盈次数 = simulate定投策略(etf_data, 定投金额=1000, 止盈比例=0.15)
    if 策略结果 is None:
        print("策略模拟失败")
        return
    
    # 3. 计算最终收益
    最终记录 = 策略结果.iloc[-1]
    最终投入 = 最终记录['累计投入']
    最终市值 = 最终记录['当前市值']
    最终收益率 = 最终记录['收益率']
    
    print("\n===== 定投策略结果 =====")
    print(f"定投周期: {策略结果['date'].min().strftime('%Y-%m-%d')} 至 {策略结果['date'].max().strftime('%Y-%m-%d')}")
    print(f"定投次数: {len(策略结果)}次")
    print(f"止盈次数: {止盈次数}次")
    print(f"累计投入: {最终投入:.2f}元")
    print(f"最终市值: {最终市值:.2f}元")
    print(f"最终收益率: {最终收益率:.2%}")
    
    # 4. 保存策略结果
    策略结果.to_csv('沪深300ETF定投模拟结果.csv', index=False, encoding='utf-8-sig')
    print("策略数据已保存: 沪深300ETF定投模拟结果.csv")
    
    # 5. 绘制图表
    plot_result(策略结果, 止盈次数)

if __name__ == "__main__":
    main()