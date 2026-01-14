import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import re

# 设置matplotlib中文显示
matplotlib.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
matplotlib.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 获取国内生产总值数据
try:
    data = ak.macro_china_gdp()
    print("成功获取国内生产总值数据，字段包括:", data.columns.tolist())
except Exception as e:
    print(f"获取数据失败: {e}")
    exit()

# 动态检测GDP字段
gdp_value_columns = [col for col in data.columns if '国内生产总值' in col and ('绝对值' in col or '值' in col)]
quarter_column = '季度' if '季度' in data.columns else data.columns[0]

if not gdp_value_columns:
    print("错误：数据中未找到GDP绝对值字段")
    print(f"可用字段: {data.columns.tolist()}")
    exit()

# 提取GDP字段并处理日期
gdp_data = data[[quarter_column, gdp_value_columns[0]]].copy()
gdp_data = gdp_data.rename(columns={
    quarter_column: '季度',
    gdp_value_columns[0]: 'GDP累计值(亿元)'
})

# 解析特殊累计季度格式（支持"2024年第1季度"、"2024年第1-2季度"等）
def parse_cumulative_quarter(quarter_str):
    # 匹配单季度和累计季度格式
    match = re.search(r'(\d{4})年第([1-4])(?:-([1-4])|)季度', quarter_str)
    if not match:
        return None, None, None, None
    
    year = int(match.group(1))
    start_q = int(match.group(2))
    end_q = int(match.group(3)) if match.group(3) else start_q
    
    # 计算累计季度数和代表季度（取结束季度）
    quarter_count = end_q - start_q + 1
    representative_q = end_q  # 用结束季度代表该累计段（如1-2季度代表Q2）
    
    return year, start_q, end_q, quarter_count, representative_q

# 应用解析并提取累计信息
parsed_results = gdp_data['季度'].apply(lambda x: parse_cumulative_quarter(x))
gdp_data[['年份', '起始季度', '结束季度', '累计季度数', '代表季度']] = pd.DataFrame(
    parsed_results.tolist(), index=gdp_data.index
)

# 数据清洗
gdp_data = gdp_data.dropna(subset=['年份', '起始季度', '结束季度', '累计季度数', '代表季度'])
gdp_data['GDP累计值(亿元)'] = pd.to_numeric(gdp_data['GDP累计值(亿元)'], errors='coerce')
gdp_data = gdp_data.dropna()

# 按年份分组，每组内按累计季度数升序排序（确保1→2→3→4季度的顺序）
gdp_data = gdp_data.sort_values(['年份', '累计季度数'], ascending=[True, True])

# 同一年度内按代表季度去重（保留最新的累计数据）
gdp_data = gdp_data.drop_duplicates(subset=['年份', '代表季度'], keep='last')

# 按年份分组计算差分
def calculate_actual_quarter(group):
    # 按累计季度数排序
    group = group.sort_values('累计季度数')
    
    # 计算差分（当前累计值 - 前一个累计值）
    group['季度增加值(亿元)'] = group['GDP累计值(亿元)'].diff()
    
    # 第一季度的增加值等于其累计值
    first_idx = group['累计季度数'].idxmin()
    group.loc[first_idx, '季度增加值(亿元)'] = group.loc[first_idx, 'GDP累计值(亿元)']
    
    # 创建标准季度映射
    quarter_mapping = {
        1: 'Q1',  # 1季度累计 → Q1
        2: 'Q2',  # 1-2季度累计 → Q2
        3: 'Q3',  # 1-3季度累计 → Q3
        4: 'Q4'   # 1-4季度累计 → Q4
    }
    
    # 映射代表季度到标准季度
    group['标准季度'] = group['代表季度'].map(quarter_mapping)
    group['标准季度'] = group['年份'].astype(str) + '-' + group['标准季度']
    
    return group

# 应用差分计算
gdp_calculated = gdp_data.groupby('年份', group_keys=False).apply(calculate_actual_quarter)

# 展开为完整季度序列
def expand_to_quarters(group):
    year = group['年份'].iloc[0]
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    quarter_data = {
        '标准季度': [f"{year}-{q}" for q in quarters],
        '年份': [year] * 4,
        '季度': quarters
    }
    
    # 创建完整季度框架
    df = pd.DataFrame(quarter_data)
    
    # 合并计算的增加值
    calculated_dict = dict(zip(gdp_calculated[gdp_calculated['年份'] == year]['标准季度'], 
                              gdp_calculated[gdp_calculated['年份'] == year]['季度增加值(亿元)']))
    
    df['实际季度值(亿元)'] = df['标准季度'].map(calculated_dict)
    return df

# 应用展开
all_years = gdp_calculated['年份'].unique()
gdp_quarters = pd.concat([expand_to_quarters(gdp_calculated[gdp_calculated['年份'] == y]) for y in all_years])

# 生成标准日期
def quarter_to_date(quarter_str):
    year, q = quarter_str.split('-')
    q_num = int(q[1])
    month = q_num * 3
    return f"{year}-{month:02d}-01"

gdp_quarters['日期'] = pd.to_datetime(gdp_quarters['标准季度'].apply(quarter_to_date))

# 验证年度累计是否等于四个季度之和
annual_verify = gdp_quarters.groupby('年份').agg({
    '实际季度值(亿元)': 'sum',
    '标准季度': 'count'
})

# 获取年度累计值进行对比
yearly_cumulative = gdp_calculated[gdp_calculated['代表季度'] == 4].set_index('年份')['GDP累计值(亿元)']
annual_verify = annual_verify.join(yearly_cumulative, how='left')
annual_verify = annual_verify.rename(columns={
    '实际季度值(亿元)': '季度实际累加',
    'GDP累计值(亿元)': '接口年度累计',
    '标准季度': '有效季度数'
})
annual_verify['差异率(%)'] = ((annual_verify['季度实际累加'] - annual_verify['接口年度累计']) / annual_verify['接口年度累计']).abs() * 100
print("年度数据验证（季度实际累加 vs 接口年度累计）:")
print(annual_verify[['季度实际累加', '接口年度累计', '有效季度数', '差异率(%)']])

# 保存修正后的数据
try:
    with pd.ExcelWriter('数据-中国GDP-东财.xlsx', engine='openpyxl', mode='w') as writer:
        # 标准季度数据
        gdp_quarters[['标准季度', '日期', '实际季度值(亿元)']].to_excel(
            writer, sheet_name='标准季度数据', index=False
        )
        # 累计计算过程
        gdp_calculated[['年份', '季度', 'GDP累计值(亿元)', '季度增加值(亿元)', '标准季度']].to_excel(
            writer, sheet_name='累计计算过程', index=False
        )
        # 年度验证数据
        annual_verify.to_excel(writer, sheet_name='年度验证')
    print("修正后数据已保存到: 数据-中国GDP-东财.xlsx")
except Exception as e:
    print(f"保存Excel文件失败: {e}")
    exit()

# 绘制修正后的图表
try:
    # 按日期排序
    gdp_sorted = gdp_quarters.sort_values('日期')
    
    fig, ax1 = plt.subplots(figsize=(14, 8))
    ax2 = ax1.twinx()
    
    # 绘制季度数据（左侧Y轴）
    ax1.plot(gdp_sorted['日期'], gdp_sorted['实际季度值(亿元)'], 
             marker='o', color='#1f77b4', linewidth=2, label='实际季度GDP')
    ax1.set_xlabel('日期', fontsize=12)
    ax1.set_ylabel('季度GDP（亿元）', color='#1f77b4', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#1f77b4')
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # 绘制年度数据（右侧Y轴）
    annual_data = gdp_quarters.groupby('年份')['实际季度值(亿元)'].sum().reset_index()
    annual_data['日期'] = pd.to_datetime(annual_data['年份'].astype(str) + '-12-31')
    ax2.plot(annual_data['日期'], annual_data['实际季度值(亿元)'], 
             marker='s', color='#ff7f0e', linewidth=3, label='年度GDP（季度累加）')
    ax2.set_ylabel('年度GDP（亿元）', color='#ff7f0e', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#ff7f0e')
    
    # 添加标题和图例
    plt.title('中国GDP季度实际值与年度趋势图（差分修正版）', fontsize=16)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # 保存修正后的图表
    chart_path = '数据-GDP季度实际与年度趋势对比图-东财.png'
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    print(f"修正后的图表已保存到: {chart_path}")
except Exception as e:
    print(f"绘制图表失败: {e}")
    exit()

print("GDP累计数据差分修正完成，已按累计值减去前值方法计算实际季度值")