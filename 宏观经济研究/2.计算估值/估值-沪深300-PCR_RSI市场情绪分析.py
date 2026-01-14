import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import re

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# ---------------------- 辅助函数 ----------------------
def calculate_rsi(close_prices, window=14):
    """计算RSI指标"""
    delta = close_prices.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()
    avg_loss = avg_loss.replace(0, 1e-10)  # 避免除零
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def parse_contract_date(symbol):
    """从合约代码提取到期月（如io2509 -> 2025-09-01）"""
    match = re.match(r'io(\d{2})(\d{2})', symbol)
    if match:
        year = int(f"20{match.group(1)}")
        month = int(match.group(2))
        return pd.to_datetime(f"{year}-{month}-01")
    return None

def generate_quarterly_contracts(count=3):
    """生成沪深300期权季度合约代码（3,6,9,12月到期）"""
    contracts = []
    current = datetime.now()
    quarters = [3, 6, 9, 12]  # 沪深300期权标准到期月
    
    # 找到当前季度
    current_quarter = ((current.month - 1) // 3) * 3 + 3
    start_idx = quarters.index(current_quarter)
    
    # 生成未来count个季度合约
    for i in range(count):
        idx = (start_idx + i) % 4
        month = quarters[idx]
        year = current.year + ((start_idx + i) // 4)
        # 修复f-string格式错误，使用正确的占位符分隔
        symbol = f"io{str(year)[-2:]}{month:02d}"  # 格式: io2509
        contracts.append(symbol)
    
    return contracts

# ---------------------- 获取PCR数据（新接口） ----------------------
try:
    # 生成最近3个季度合约代码
    contracts = generate_quarterly_contracts(count=3)
    print(f"生成合约代码: {contracts}")
    
    pcr_list = []
    for symbol in contracts:
        try:
            # 获取指定合约的期权数据
            option_df = ak.option_cffex_hs300_spot_sina(symbol=symbol)
            print(f"合约 {symbol} 数据列名: {option_df.columns.tolist()}")
            
            # 提取持仓量数据
            if '看涨合约-持仓量' in option_df.columns and '看跌合约-持仓量' in option_df.columns:
                call_oi = option_df['看涨合约-持仓量'].sum()
                put_oi = option_df['看跌合约-持仓量'].sum()
                
                # 计算PCR（看跌持仓量/看涨持仓量）
                if call_oi > 0 and put_oi > 0:
                    pcr = put_oi / call_oi
                    date = parse_contract_date(symbol)
                    pcr_list.append({
                        '日期': date,
                        'PCR': pcr,
                        '合约代码': symbol,
                        '看涨持仓量': call_oi,
                        '看跌持仓量': put_oi
                    })
                    print(f"合约 {symbol} PCR: {pcr:.4f} (看涨持仓: {call_oi}, 看跌持仓: {put_oi})")
                else:
                    print(f"合约 {symbol} 持仓量为零，跳过")
            else:
                print(f"合约 {symbol} 缺少持仓量字段")
                
        except Exception as e:
            print(f"获取合约 {symbol} 失败: {e}")
            continue
    
    if not pcr_list:
        raise ValueError("未获取到有效PCR数据")
    
    pcr_df = pd.DataFrame(pcr_list)
    print(f"PCR数据: {len(pcr_df)}条记录")
    print(f"PCR数据范围: {pcr_df['日期'].min()} ~ {pcr_df['日期'].max()}")

except Exception as e:
    print(f"获取PCR数据失败: {e}")
    raise

# ---------------------- 获取RSI数据 ----------------------
try:
    # 获取沪深300指数日度数据
    hs300_df = ak.stock_zh_index_daily(symbol="sh000300")
    hs300_df['日期'] = pd.to_datetime(hs300_df['date'])
    
    # 计算14天RSI
    hs300_df['RSI_14'] = calculate_rsi(hs300_df['close'])
    rsi_df = hs300_df[['日期', 'RSI_14']].dropna()
    
    # 按月度聚合（取每月最后一个交易日的RSI值）
    rsi_monthly = rsi_df.resample('M', on='日期').last().reset_index()
    print(f"RSI月度数据: {len(rsi_monthly)}条记录")
    print(f"RSI数据范围: {rsi_monthly['日期'].min()} ~ {rsi_monthly['日期'].max()}")

except Exception as e:
    print(f"获取RSI数据失败: {e}")
    raise

# ---------------------- 数据合并与可视化 ----------------------
try:
    # 合并PCR和RSI数据（按月度对齐）
    merged_df = pd.merge(
        pcr_df[['日期', 'PCR', '合约代码']],
        rsi_monthly,
        on='日期',
        how='inner'
    )
    
    if merged_df.empty:
        print("警告：PCR与RSI数据无重叠时间范围，使用左连接保留数据")
        merged_df = pd.merge(
            pcr_df[['日期', 'PCR', '合约代码']],
            rsi_monthly,
            on='日期',
            how='left'
        )
    
    print(f"合并后数据: {len(merged_df)}条记录")
    merged_df.to_csv("沪深300_PCR_RSI_新接口情绪指标.csv", index=False, encoding="utf-8-sig")

    # 绘制市场情绪分析图
    fig, ax1 = plt.subplots(figsize=(14, 7), dpi=100)
    
    # 左侧Y轴：PCR
    ax1.bar(merged_df['日期'], merged_df['PCR'], width=15, color='#1f77b4', alpha=0.6, label='PCR (看跌/看涨持仓比)')
    ax1.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='PCR=1.0 参考线')
    ax1.set_xlabel('日期', fontsize=12)
    ax1.set_ylabel('PCR', color='#1f77b4', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#1f77b4')
    ax1.grid(True, linestyle='--', alpha=0.5, axis='y')
    
    # 右侧Y轴：RSI
    ax2 = ax1.twinx()
    ax2.plot(merged_df['日期'], merged_df['RSI_14'], 'o-', color='#ff7f0e', label='14天RSI', alpha=0.8)
    ax2.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='RSI=70 超买线')
    ax2.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='RSI=30 超卖线')
    ax2.set_ylabel('14天RSI', color='#ff7f0e', fontsize=12)
    ax2.set_ylim(0, 100)
    ax2.tick_params(axis='y', labelcolor='#ff7f0e')
    
    # 标题和图例
    start_date = merged_df['日期'].min().strftime('%Y-%m') if not merged_df['日期'].isna().all() else 'N/A'
    end_date = merged_df['日期'].max().strftime('%Y-%m') if not merged_df['日期'].isna().all() else 'N/A'
    plt.title(f'沪深300 PCR与RSI市场情绪分析（新接口） ({start_date}至{end_date})', fontsize=14, pad=20)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    # 日期格式设置
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
    
    # 保存图表
    plt.tight_layout(pad=3.0)
    save_path = "沪深300_PCR_RSI_新接口市场情绪分析图.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存至: {save_path}")

except Exception as e:
    print(f"数据合并或绘图失败: {e}")
    raise