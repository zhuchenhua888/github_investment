import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates

# 设置中文字体和负号正常显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

def get_hs300_data():
    """获取沪深300指数价格数据"""
    try:
        # 调用akshare接口获取沪深300指数日线数据
        hs300_df = ak.stock_zh_index_daily(symbol="sh000300")
        # 自动查找日期和收盘价列名
        date_cols = [col for col in hs300_df.columns if 'date' in col.lower() or '日期' in col]
        close_cols = [col for col in hs300_df.columns if 'close' in col.lower() or '收盘' in col]
        if not date_cols or not close_cols:
            raise ValueError("未找到日期列或收盘价列")
        # 只保留日期和收盘价，并重命名
        hs300_df = hs300_df[[date_cols[0], close_cols[0]]].copy()
        hs300_df[date_cols[0]] = pd.to_datetime(hs300_df[date_cols[0]])
        hs300_df.rename(columns={date_cols[0]: '日期', close_cols[0]: 'hs300_close'}, inplace=True)
        return hs300_df
    except Exception as e:
        print(f"获取沪深300价格数据失败: {e}")
        return None

def get_hs300_pe():
    """获取沪深300动态市盈率数据"""
    try:
        # 通过akshare接口获取沪深300市盈率数据
        pe_df = ak.stock_index_pe_lg(symbol="沪深300")
        pe_df['日期'] = pd.to_datetime(pe_df['日期'])
        pe_df.rename(columns={'滚动市盈率': '动态市盈率'}, inplace=True)
        print(pe_df)
        return pe_df[['日期', '动态市盈率']]
    except Exception as e:
        print(f"获取沪深300市盈率数据失败: {e}")
        return None

def get_treasury_yield():
    """获取中国十年期国债收益率"""
    try:
        # 获取中美国债收益率数据
        bond_df = ak.bond_zh_us_rate()
        # 查找中国10年期国债收益率列
        china_10y_col = [col for col in bond_df.columns if '中国' in col and '10年' in col]
        if not china_10y_col:
            raise ValueError("未找到中国十年期国债收益率列")
        # 查找日期列
        date_cols = [col for col in bond_df.columns if 'date' in col.lower() or '日期' in col]
        if not date_cols:
            raise ValueError("未找到日期列")
        # 只保留日期和收益率，并重命名
        china_10y = bond_df[[date_cols[0], china_10y_col[0]]].copy()
        china_10y[date_cols[0]] = pd.to_datetime(china_10y[date_cols[0]])
        china_10y.rename(columns={date_cols[0]: '日期', china_10y_col[0]: '国债收益率(%)'}, inplace=True)
        # 转换为小数形式
        china_10y['国债收益率'] = pd.to_numeric(china_10y['国债收益率(%)'], errors='coerce') / 100
        china_10y = china_10y.dropna(subset=['国债收益率'])
        return china_10y[['日期', '国债收益率']]
    except Exception as e:
        print(f"获取国债收益率数据失败: {e}")
        return None

def calculate_fed_premium(hs300_data, pe_data, bond_data):
    """合并数据并计算FED溢价及分位数"""
    try:
        if hs300_data is None or pe_data is None or bond_data is None:
            raise ValueError("输入数据不完整")
        # 按日期合并三份数据
        merged_df = hs300_data.merge(pe_data, on='日期', how='inner')
        merged_df = merged_df.merge(bond_data, on='日期', how='inner')
        # 计算FED溢价 = 1/(市盈率) / 国债收益率
        merged_df['FED溢价'] = (1 / merged_df['动态市盈率']) / merged_df['国债收益率']
        merged_df = merged_df.sort_values('日期')
        # 计算分位数和统计值
        q10 = merged_df['FED溢价'].quantile(0.1)
        q30 = merged_df['FED溢价'].quantile(0.3)
        q70 = merged_df['FED溢价'].quantile(0.7)
        q90 = merged_df['FED溢价'].quantile(0.9)
        mean_val = merged_df['FED溢价'].mean()
        std_val = merged_df['FED溢价'].std()
        # 按分位数区间打标签
        merged_df['区间'] = pd.cut(
            merged_df['FED溢价'],
            bins=[-np.inf, q10, q30, q70, q90, np.inf],
            labels=['极低', '偏低', '中等', '偏高', '极高']
        )
        return merged_df, q10, q30, q70, q90, mean_val, std_val
    except Exception as e:
        print(f"计算FED溢价失败: {e}")
        return None, None, None, None, None, None, None

def plot_fed_premium(data, q10, q30, q70, q90, mean_val, std_val):
    """绘制双纵轴图表并添加分位数标记和参考线"""
    try:
        fig, ax1 = plt.subplots(figsize=(16, 8))
        # 左轴：沪深300指数
        ax1 = plt.gca()
        line1, = ax1.plot(data['日期'], data['hs300_close'], linestyle='--', color='lightgrey', linewidth=2, label='沪深300指数')
        ax1.set_xlabel('日期', fontsize=12)
        ax1.set_ylabel('沪深300指数', fontsize=12)
        ax1.tick_params(axis='y', labelcolor='grey')
        ax1.grid(True, linestyle='--', alpha=0.7)
        # 右轴：FED溢价
        ax2 = ax1.twinx()
        # FED溢价曲线
        line2, = ax2.plot(data['日期'], data['FED溢价'], color="#4751A5", linewidth=2, label='FED溢价=1/(沪深300动态市盈率) / 十年期国债收益率')
        # 按区间着色标记点
        colors = {'极低': 'green', '偏低': 'blue', '中等': 'yellow', '偏高': 'orange', '极高': 'red'}
        for label, color in colors.items():
            mask = data['区间'] == label
            ax2.scatter(data[mask]['日期'], data[mask]['FED溢价'], c=color, label=f'{label}区间', alpha=0.7, s=10)
        # 统计参考线
        ax2.axhline(y=mean_val + 2*std_val, linestyle='--', color='red', alpha=0.7, label=f'均值+2σ')
        ax2.axhline(y=mean_val + std_val, linestyle='--', color='orange', alpha=0.7, label=f'均值+1σ')
        ax2.axhline(y=mean_val, linestyle='--', color='yellow', alpha=0.7, label=f'均值({mean_val:.2f})')
        ax2.axhline(y=mean_val - std_val, linestyle='--', color='blue', alpha=0.7, label=f'均值-1σ')
        ax2.axhline(y=mean_val - 2*std_val, linestyle='--', color='green', alpha=0.7, label=f'均值-2σ')
        # 设置右轴标签
        ax2.set_ylabel('FED溢价', fontsize=12, color='#ff7f0e')
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')
        # 日期格式
        ax1.xaxis.set_major_formatter(DateFormatter('%Y'))
        plt.xticks(rotation=45)
        # 合并图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10, ncol=2)
        # 标题
        plt.title('估值-沪深300指数与股债比趋势图', fontsize=16, pad=20)
        # 调整布局并保存
        plt.tight_layout()
        chart_file = '估值-沪深300指数与股债比趋势图.png'
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        print(f"图表已保存至: {chart_file}")
        return chart_file
    except Exception as e:
        print(f"绘制图表失败: {e}")
        return None

if __name__ == "__main__":
    # 获取沪深300指数、PE和国债收益率数据
    hs300_data = get_hs300_data()
    pe_data = get_hs300_pe()
    bond_data = get_treasury_yield()
    if hs300_data is not None and pe_data is not None and bond_data is not None:
        # 计算FED溢价和分位数
        result_df, q10, q30, q70, q90, mean_val, std_val = calculate_fed_premium(hs300_data, pe_data, bond_data)
        if result_df is not None and not result_df.empty:
            # 绘制图表
            chart_file = plot_fed_premium(result_df, q10, q30, q70, q90, mean_val, std_val)
            if chart_file:
                print("FED溢价计算与可视化完成")
            else:
                print("FED溢价可视化失败")
        else:
            print("无法计算FED溢价，数据可能为空")
    else:
        print("获取数据失败，无法继续计算")