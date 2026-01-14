import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

def get_hs300_data():
    """获取沪深300指数价格数据"""
    try:
        # 沪深300指数代码：带市场标识
        hs300_df = ak.stock_zh_index_daily(symbol="sh000300")
        
        # 动态适配日期列和收盘价列
        date_cols = [col for col in hs300_df.columns if 'date' in col.lower() or '日期' in col]
        close_cols = [col for col in hs300_df.columns if 'close' in col.lower() or '收盘' in col]
        
        if not date_cols or not close_cols:
            raise ValueError("未找到日期列或收盘价列")
            
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
        # 通过指数名称获取市盈率数据
        pe_df = ak.stock_index_pe_lg(symbol="沪深300")
        print(f"市盈率数据列名: {pe_df.columns.tolist()}")

        pe_df['日期'] = pd.to_datetime(pe_df['日期'])
        pe_df.rename(columns={'滚动市盈率': '动态市盈率'}, inplace=True)
        return pe_df
    except Exception as e:
        print(f"获取沪深300市盈率数据失败: {e}")
        return None

def get_treasury_yield():
    """获取中国十年期国债收益率（修正版）"""
    try:
        # 获取中美国债收益率数据
        bond_df = ak.bond_zh_us_rate()
        print(f"国债收益率数据列名: {bond_df.columns.tolist()}")
        
        # 直接提取中国十年期国债收益率列
        china_10y_col = [col for col in bond_df.columns if '中国' in col and '10年' in col]
        
        if not china_10y_col:
            raise ValueError("未找到中国十年期国债收益率列")
            
        # 提取日期列和收益率列
        date_cols = [col for col in bond_df.columns if 'date' in col.lower() or '日期' in col]
        if not date_cols:
            raise ValueError("未找到日期列")
            
        # 构建数据框
        china_10y = bond_df[[date_cols[0], china_10y_col[0]]].copy()
        china_10y[date_cols[0]] = pd.to_datetime(china_10y[date_cols[0]])
        china_10y.rename(columns={date_cols[0]: '日期', china_10y_col[0]: '国债收益率(%)'}, inplace=True)
        
        # 转换为小数形式
        china_10y['国债收益率'] = pd.to_numeric(china_10y['国债收益率(%)'], errors='coerce') / 100
        # 去除无效值
        china_10y = china_10y.dropna(subset=['国债收益率'])
        
        return china_10y[['日期', '国债收益率']]
    except Exception as e:
        print(f"获取国债收益率数据失败: {e}")
        return None

def calculate_fed_premium(hs300_data, pe_data, bond_data):
    """合并数据并计算FED溢价"""
    try:
        if hs300_data is None or pe_data is None or bond_data is None:
            raise ValueError("输入数据不完整")
            
        # 合并数据
        merged_df = hs300_data.merge(pe_data, on='日期', how='inner')
        merged_df = merged_df.merge(bond_data, on='日期', how='inner')
        
        print(merged_df)
        # 计算FED溢价: 1/(市盈率) / 国债收益率
        merged_df['FED溢价'] = (1 / merged_df['动态市盈率']) / merged_df['国债收益率']
        
        # 按日期排序
        merged_df = merged_df.sort_values('日期')
        print(f"合并后数据量: {len(merged_df)} 条")
        print(merged_df)
        return merged_df
    except Exception as e:
        print(f"计算FED溢价失败: {e}")
        return None

def plot_fed_premium(data):
    """绘制沪深300指数与FED溢价双纵轴图表"""
    try:
        fig, ax1 = plt.subplots(figsize=(14, 7))
        
        # 左侧纵轴：沪深300指数
        ax1.plot(data['日期'], data['hs300_close'], color='#1f77b4', linewidth=2, label='沪深300指数')
        ax1.set_xlabel('日期', fontsize=12)
        ax1.set_ylabel('沪深300指数', fontsize=12, color='#1f77b4')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # 右侧纵轴：FED溢价
        ax2 = ax1.twinx()
        ax2.plot(data['日期'], data['FED溢价'], color='#ff7f0e', linewidth=2, label='FED溢价=1/(沪深300动态市盈率) / 十年期国债收益率')
        ax2.set_ylabel('FED溢价', fontsize=12, color='#ff7f0e')
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')
        
        # 设置日期格式
        ax1.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
        plt.xticks(rotation=45)
        
        # 添加图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.title('估值-沪深300指数与股债比趋势图', fontsize=16)
        plt.tight_layout()
        
        # 保存图表
        chart_file = '估值-沪深300指数与股债比趋势图.png'
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        print(f"图表已保存至: {chart_file}")
        return chart_file
    except Exception as e:
        print(f"绘制图表失败: {e}")
        return None

if __name__ == "__main__":
    # 获取数据
    hs300_data = get_hs300_data()
    pe_data = get_hs300_pe()
    bond_data = get_treasury_yield()
    
    # 打印各数据形状用于调试
    if hs300_data is not None:
        print(f"沪深300价格数据形状: {hs300_data.shape}")
    if pe_data is not None:
        print(f"市盈率数据形状: {pe_data.shape}")
    if bond_data is not None:
        print(f"国债收益率数据形状: {bond_data.shape}")
    
    if hs300_data is not None and pe_data is not None and bond_data is not None:
        # 计算FED溢价
        result_df = calculate_fed_premium(hs300_data, pe_data, bond_data)
        if result_df is not None and not result_df.empty:
            # 绘制图表
            chart_file = plot_fed_premium(result_df)
            if chart_file:
                print("FED溢价计算与可视化完成")
            else:
                print("FED溢价可视化失败")
        else:
            print("无法计算FED溢价，数据可能为空")
    else:
        print("获取数据失败，无法继续计算")