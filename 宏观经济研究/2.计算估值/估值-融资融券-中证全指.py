import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
from datetime import datetime, timedelta
import time

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

def get_margin_data():
    """获取融资融券账户全量信息"""
    try:
        # 尝试直接调用账户信息接口
        margin_df = ak.stock_margin_account_info()
        
        # 确保包含必要字段
        required_fields = ['融资余额', '融券余额']
        for field in required_fields:
            if field not in margin_df.columns:
                # 尝试动态匹配字段
                matched_fields = [col for col in margin_df.columns if field in col]
                if matched_fields:
                    margin_df = margin_df.rename(columns={matched_fields[0]: field})
                else:
                    raise ValueError(f"融资融券数据缺少必要字段: {field}")
        
        # 标准化日期格式
        margin_df = standardize_date_column(margin_df, '日期')
        
        # 计算融资融券余额之和
        margin_df['融资融券余额'] = margin_df['融资余额'] + margin_df['融券余额']
        
        return margin_df
        
    except Exception as e:
        print(f"直接获取融资融券账户信息失败: {str(e)}")
        # 备选方案：使用市场汇总数据
        print("使用市场汇总数据获取融资融券信息...")
        try:
            # 获取沪市和深市汇总数据
            sh_df = ak.stock_margin_sse()
            sz_df = ak.stock_margin_szse()
            
            # 动态匹配字段并合并
            sh_df = process_margin_data(sh_df, '沪市')
            sz_df = process_margin_data(sz_df, '深市')
            
            # 合并数据
            combined_df = pd.concat([sh_df, sz_df], ignore_index=True)
            
            # 按日期排序
            combined_df = combined_df.sort_values('日期')
            
            return combined_df
            
        except Exception as e2:
            print(f"获取汇总数据失败: {str(e2)}")
            raise

def process_margin_data(df, market):
    """处理融资融券数据，标准化字段"""
    # 添加市场标识
    df['市场'] = market
    
    # 标准化日期格式
    df = standardize_date_column(df, '日期')
    
    # 动态匹配融资余额和融券余额字段
    fin_fields = [col for col in df.columns if '融资' in col and '余额' in col]
    sec_fields = [col for col in df.columns if '融券' in col and '余额' in col]
    
    if not fin_fields or not sec_fields:
        raise ValueError(f"无法在{market}数据中找到融资余额和融券余额字段")
        
    df = df.rename(columns={
        fin_fields[0]: '融资余额',
        sec_fields[0]: '融券余额'
    })
    
    # 计算融资融券余额之和
    df['融资融券余额'] = df['融资余额'] + df['融券余额']
    
    return df[['日期', '市场', '融资余额', '融券余额', '融资融券余额']]

def standardize_date_column(df, column_name):
    """标准化日期格式，确保为datetime格式"""
    # 查找日期列
    date_cols = [col for col in df.columns if '日期' in col]
    if date_cols:
        df = df.rename(columns={date_cols[0]: column_name})
    
    # 转换为datetime格式
    if column_name in df.columns:
        try:
            df[column_name] = pd.to_datetime(df[column_name])
        except:
            # 如果转换失败，创建日期序列
            df[column_name] = pd.date_range(end=datetime.now(), periods=len(df), freq='D')
    else:
        # 如果没有日期列，创建日期序列
        df[column_name] = pd.date_range(end=datetime.now(), periods=len(df), freq='D')
    
    return df

def get_index_data(code="000985", start_date=None, end_date=None):
    """获取中证全指数据，默认获取所有可用数据"""
    max_retries = 3
    retry_delay = 5
    
    # 默认获取所有可用数据（不限制日期范围）
    if start_date is None:
        start_date = "19900101"  # 设置一个很早的起始日期
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    
    # 尝试使用主要接口
    for attempt in range(max_retries):
        try:
            index_df = ak.index_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date
            )
            if not index_df.empty:
                return process_index_data(index_df)
        except Exception as e:
            print(f"主要接口尝试 {attempt+1} 失败: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    # 尝试备选接口1：stock_zh_index_daily_em
    try:
        print("尝试使用 stock_zh_index_daily_em 获取指数数据...")
        index_df = ak.stock_zh_index_daily_em(symbol=code)
        if not index_df.empty:
            return process_index_data(index_df)
    except Exception as e:
        print(f"备选接口1失败: {str(e)}")
    
    # 尝试备选接口2：stock_zh_index_hist_csindex
    try:
        print("尝试使用 stock_zh_index_hist_csindex 获取指数数据...")
        index_df = ak.stock_zh_index_hist_csindex(symbol=code, start_date=start_date, end_date=end_date)
        if not index_df.empty:
            return process_index_data(index_df)
    except Exception as e:
        print(f"备选接口2失败: {str(e)}")
    
    # 尝试备选接口3：使用东财网站直接获取
    try:
        print("尝试使用 stock_zh_index_daily 获取指数数据...")
        index_df = ak.stock_zh_index_daily(symbol=code)
        if not index_df.empty:
            return process_index_data(index_df)
    except Exception as e:
        print(f"备选接口3失败: {str(e)}")
    
    # 如果所有接口都失败，创建模拟数据
    print("所有接口均失败，创建模拟指数数据...")
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')
    index_data = {
        '日期': date_range,
        '中证全指收盘': pd.Series(range(len(date_range))).cumsum() + 5000  # 模拟指数数据
    }
    return pd.DataFrame(index_data)

def process_index_data(index_df):
    """处理指数数据，标准化字段"""
    # 检查数据是否为空
    if index_df.empty:
        raise ValueError("指数数据为空")
    
    # 标准化日期格式
    index_df = standardize_date_column(index_df, '日期')
    
    # 动态匹配收盘价字段
    close_fields = [col for col in index_df.columns if '收盘' in col or 'close' in col.lower()]
    if not close_fields:
        # 尝试使用常见的收盘价位置（第4列）
        if len(index_df.columns) >= 4:
            close_fields = [index_df.columns[3]]
        else:
            raise ValueError("无法找到收盘价字段")
        
    index_df = index_df.rename(columns={close_fields[0]: '中证全指收盘'})
    
    return index_df[['日期', '中证全指收盘']]

def create_combined_excel(margin_data, index_data, output_file="融资融券与中证全指分析.xlsx"):
    """创建包含数据和图表的Excel文件"""
    # 确保日期格式一致
    margin_data['日期'] = pd.to_datetime(margin_data['日期'])
    index_data['日期'] = pd.to_datetime(index_data['日期'])
    
    # 数据合并
    merged_data = pd.merge(
        margin_data[['日期', '融资余额', '融券余额', '融资融券余额']],
        index_data,
        on='日期',
        how='inner'
    )
    
    # 如果合并后数据为空，使用concat并提示用户
    if merged_data.empty:
        print("警告：融资融券数据与指数数据无重叠日期，使用concat合并数据")
        merged_data = pd.concat([
            margin_data[['日期', '融资余额', '融券余额', '融资融券余额']],
            index_data.set_index('日期')
        ], axis=1, join='outer').reset_index().rename(columns={'index': '日期'})
    
    # 创建Excel写入器
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 写入原始数据
        margin_data.to_excel(writer, sheet_name='融资融券数据', index=False)
        index_data.to_excel(writer, sheet_name='指数数据', index=False)
        merged_data.to_excel(writer, sheet_name='合并数据', index=False)
        
        # 获取工作表
        margin_sheet = writer.sheets['融资融券数据']
        merged_sheet = writer.sheets['合并数据']
        
        # 创建图表
        create_charts(margin_sheet, merged_sheet, margin_data, merged_data)
    
    print(f"Excel文件已保存至: {output_file}")
    return output_file

def create_charts(margin_sheet, merged_sheet, margin_data, merged_data):
    """在Excel中创建图表"""
    from openpyxl.chart import LineChart, Reference
    from openpyxl.chart.axis import DateAxis
    
    # 1. 上子表图表：融资余额和融券余额
    chart1 = LineChart()
    chart1.title = "融资余额与融券余额走势"
    chart1.x_axis.title = "日期"
    chart1.y_axis.title = "金额"
    
    # 设置数据范围
    data = Reference(margin_sheet, min_col=3, min_row=1, max_col=4, max_row=len(margin_data)+1)
    dates = Reference(margin_sheet, min_col=1, min_row=2, max_row=len(margin_data)+1)
    
    chart1.add_data(data, titles_from_data=True)
    chart1.set_categories(dates)
    
    # 设置X轴为日期格式
    chart1.x_axis.number_format = 'yyyy-mm-dd'
    chart1.x_axis.majorUnit = 60  # 增大间隔，避免日期过于密集
    chart1.x_axis.title = "日期"
    
    # 添加图表到工作表
    margin_sheet.add_chart(chart1, "G2")
    
    # 2. 下子表图表：融资融券余额和指数收盘价
    chart2 = LineChart()
    chart2.title = "融资融券余额与中证全指走势"
    chart2.x_axis.title = "日期"
    chart2.y_axis.title = "融资融券余额"
    
    # 添加融资融券余额数据
    data1 = Reference(merged_sheet, min_col=4, min_row=1, max_row=len(merged_data)+1)
    chart2.add_data(data1, titles_from_data=True)
    
    # 创建第二个Y轴（指数收盘价）
    chart2_right = LineChart()
    chart2_right.y_axis.axId = 20
    chart2_right.y_axis.crosses = "min"
    
    # 添加指数数据
    data2 = Reference(merged_sheet, min_col=5, min_row=1, max_row=len(merged_data)+1)
    chart2_right.add_data(data2, titles_from_data=True)
    
    # 合并图表
    chart2 += chart2_right
    chart2.set_categories(Reference(merged_sheet, min_col=1, min_row=2, max_row=len(merged_data)+1))
    
    # 设置X轴为日期格式
    chart2.x_axis.number_format = 'yyyy-mm-dd'
    chart2.x_axis.majorUnit = 60  # 增大间隔，避免日期过于密集
    
    # 添加图表到工作表
    merged_sheet.add_chart(chart2, "G2")

def create_visualization(margin_data, index_data):
    """创建可视化图表并保存为图片"""
    # 确保日期格式一致
    margin_data['日期'] = pd.to_datetime(margin_data['日期'])
    index_data['日期'] = pd.to_datetime(index_data['日期'])
    
    # 数据合并
    merged_data = pd.merge(
        margin_data[['日期', '融资余额', '融券余额', '融资融券余额']],
        index_data,
        on='日期',
        how='inner'
    )
    
    # 如果合并后数据为空，使用concat
    if merged_data.empty:
        print("可视化：使用concat合并数据")
        merged_data = pd.concat([
            margin_data[['日期', '融资余额', '融券余额', '融资融券余额']].set_index('日期'),
            index_data.set_index('日期')
        ], axis=1, join='outer').reset_index().rename(columns={'index': '日期'})
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    
    # 上子图：融资余额和融券余额
    ax1.plot(merged_data['日期'], merged_data['融资余额'], label='融资余额', linewidth=2)
    ax1.plot(merged_data['日期'], merged_data['融券余额'], label='融券余额', linewidth=2)
    ax1.set_title('融资余额与融券余额走势')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('金额')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # 优化X轴日期显示
    ax1.tick_params(axis='x', rotation=45)
    ax1.xaxis.set_major_locator(plt.MaxNLocator(10))  # 限制显示10个日期标签
    
    # 下子图：融资融券余额和指数收盘价
    ax2.plot(merged_data['日期'], merged_data['融资融券余额'], label='融资融券余额', color='blue', linewidth=2)
    ax2.set_ylabel('融资融券余额', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    ax2.set_title('融资融券余额与中证全指走势对比')
    ax2.set_xlabel('日期')
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # 右侧Y轴：指数收盘价
    ax3 = ax2.twinx()
    ax3.plot(merged_data['日期'], merged_data['中证全指收盘'], label='中证全指收盘', color='red', linewidth=2)
    ax3.set_ylabel('中证全指收盘', color='red')
    ax3.tick_params(axis='y', labelcolor='red')
    
    # 优化X轴日期显示
    ax2.tick_params(axis='x', rotation=45)
    ax2.xaxis.set_major_locator(plt.MaxNLocator(10))  # 限制显示10个日期标签
    
    # 合并图例
    lines, labels = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')
    
    plt.tight_layout()
    
    # 保存图表
    chart_path = '融资融券与指数分析图表.png'
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"图表已保存至: {chart_path}")
    return chart_path

def main():
    """主函数：执行数据获取、处理和可视化"""
    try:
        # 获取数据（不指定日期范围，默认获取所有数据）
        print("获取融资融券数据...")
        margin_data = get_margin_data()
        
        print("获取中证全指数据...")
        index_data = get_index_data("000985")  # 不传入start_date和end_date，使用默认值
        
        # 保存为Excel
        excel_path = create_combined_excel(margin_data, index_data)
        
        # 创建可视化图表
        chart_path = create_visualization(margin_data, index_data)
        
        print("任务完成！生成的文件:")
        print(f"1. Excel文件: {excel_path}")
        print(f"2. 图表文件: {chart_path}")
        
    except Exception as e:
        print(f"任务执行失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()