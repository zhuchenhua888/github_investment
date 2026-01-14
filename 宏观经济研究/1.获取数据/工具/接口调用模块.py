import yaml
import akshare as ak
import baostock as bs
import pandas as pd
import logging
import os
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import numpy as np
import mplfinance as mpf

# 配置常量定义
MAX_COLORS = 10  # 最大颜色数量
GRID_STYLE = '--'  # 网格线样式
GRID_ALPHA = 0.7  # 网格线透明度
DEFAULT_FONT = ["SimHei"]  # 默认字体
MPF_RC={'font.family':'SimHei'}
CONFIG_PATH = "./1.获取数据/工具/接口配置文件模板.yaml"  # 修正配置文件路径，移除./工具/前缀

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置全局字体支持中文
plt.rcParams["font.family"] = DEFAULT_FONT
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class ApiClient:
    """API客户端，支持akshare和baostock接口调用"""
    
    def __init__(self, interface_type: str):
        """初始化API客户端"""
        self.interface_type = interface_type
        self.initialized = False
        
        if interface_type == 'baostock':
            self._init_baostock()
        elif interface_type == 'akshare':
            self._init_akshare()
        else:
            raise ValueError(f"不支持的接口类型: {interface_type}")
    
    def _init_akshare(self):
        """初始化akshare"""
        logger.info("初始化akshare客户端")
        self.initialized = True
    
    def _init_baostock(self):
        """初始化baostock"""
        logger.info("初始化baostock客户端")
        lg = bs.login()
        if lg.error_code != '0':
            logger.error(f"baostock登录失败: {lg.error_msg}")
            raise ConnectionError(f"baostock登录失败: {lg.error_msg}")
        self.initialized = True
    
    def call(self, function_name: str, params: Dict[str, Any]) -> pd.DataFrame:
        """调用API接口"""
        if not self.initialized:
            raise RuntimeError("API客户端未初始化")
            
        try:
            if self.interface_type == 'akshare':
                return self._call_akshare(function_name, params)
            elif self.interface_type == 'baostock':
                return self._call_baostock(function_name, params)
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            raise
    
    def _call_akshare(self, function_name: str, params: Dict[str, Any]) -> pd.DataFrame:
        """调用akshare接口"""
        logger.info(f"调用akshare接口: {function_name}, 参数: {params}")
        
        if not hasattr(ak, function_name):
            raise AttributeError(f"akshare没有函数: {function_name}")
        
        func = getattr(ak, function_name)
        result = func(**params)
        
        if isinstance(result, pd.DataFrame):
            return result
        elif isinstance(result, dict):
            return pd.DataFrame.from_dict(result)
        else:
            raise TypeError(f"不支持的返回类型: {type(result)}")
    
    def _call_baostock(self, function_name: str, params: Dict[str, Any]) -> pd.DataFrame:
        """调用baostock接口"""
        logger.info(f"调用baostock接口: {function_name}, 参数: {params}")
        
        if not hasattr(bs, function_name):
            raise AttributeError(f"baostock没有函数: {function_name}")
        
        func = getattr(bs, function_name)
        result = func(**params)
        
        if result.error_code != '0':
            raise RuntimeError(f"baostock接口调用失败: {result.error_msg}")
        
        data_list = []
        while (result.error_code == '0') & result.next():
            data_list.append(result.get_row_data())
        
        df = pd.DataFrame(data_list, columns=result.fields)
        return df
    
    def close(self):
        """关闭API客户端"""
        if self.interface_type == 'baostock' and self.initialized:
            bs.logout()
            logger.info("baostock客户端已登出")


def call_api(config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """调用API接口的统一入口"""
    try:
        interface_type = config['type']
        function_name = config['function']
        params = config.get('params', {})
        fields = config.get('fields', [])
        # 获取x轴字段和是否解析为日期的配置
        chart_config = config.get('chart', {})
        x_col = chart_config.get('x', '数据日期')  # 默认使用'数据日期'作为x轴字段
        parse_x_as_date = chart_config.get('parse_x_as_date', True)  # 新增配置：是否将x轴字段解析为日期
        
        client = ApiClient(interface_type)
        df = client.call(function_name, params)
        client.close()
        
        # 字段过滤
        if fields and not df.empty:
            # 显示接口返回的所有字段，帮助调试
            logger.info(f"接口返回的字段: {df.columns.tolist()}")
            
            df.columns = [col.lower() for col in df.columns]
            fields_lower = [field.lower() for field in fields]
            valid_fields = [field for field in fields_lower if field in df.columns]
            
            if not valid_fields:
                logger.warning("配置中的字段与接口返回数据不匹配")
                return None
                
            df = df[valid_fields]
            df.columns = [fields[fields_lower.index(field)] for field in valid_fields]
        
        # 如果需要将x轴字段解析为日期，则进行日期转换和排序
        if parse_x_as_date and not df.empty and x_col in df.columns:
            try:
                # 处理"2025年08月份"这种格式
                if any('年' in str(date) and '月' in str(date) for date in df[x_col]):
                    df[x_col] = pd.to_datetime(df[x_col].str.replace('份', ''), format='%Y年%m月', errors='coerce')
                else:
                    df[x_col] = pd.to_datetime(df[x_col], errors='coerce')
                
                # 按日期升序排序
                df = df.sort_values(by=x_col)
                logger.info("数据已按日期升序排序")
            except Exception as e:
                logger.warning(f"日期排序失败: {str(e)}")
        elif not df.empty and x_col in df.columns:
            # 如果不解析为日期，按原始值升序排序
            df = df.sort_values(by=x_col)
            logger.info("数据已按x轴字段升序排序")
        
        logger.info(f"API调用成功，返回{len(df)}条数据")
        
        # 调试：打印返回数据的前几行
        if not df.empty:
            logger.info(f"返回数据预览:\n{df.head()}")
        else:
            logger.warning("返回数据为空")
            
        return df
    
    except Exception as e:
        logger.error(f"API调用总入口错误: {str(e)}")
        raise


def save_data(df: pd.DataFrame, storage_config: Dict[str, Any], file_name: str) -> str:
    """保存数据到文件"""
    try:
        path = storage_config.get('path', './data/')
        if not os.path.exists(path):
            os.makedirs(path)
        
        file_format = storage_config.get('format', 'csv')
        file_ext = file_format if file_format in ['csv', 'excel'] else 'csv'
        full_file_name = f"{file_name.replace(' ', '_')}.{file_ext}"
        file_path = os.path.join(path, full_file_name)
        
        if file_ext == 'csv':
            df.to_csv(file_path, index=False, encoding='utf-8')
        elif file_ext == 'excel':
            df.to_excel(file_path, index=False, engine='openpyxl')
        
        logger.info(f"数据已保存至: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"数据保存失败: {str(e)}")
        raise


def generate_chart(df: pd.DataFrame, chart_config: Dict[str, Any], file_path: str) -> str:
    """生成图表并保存，支持单Y轴多数据和双Y轴多数据展示"""
    
    # 检查数据是否为空
    if df.empty:
        logger.warning("数据为空，无法生成图表")
        return ""
        
    try:
        # 创建图表保存目录
        chart_dir = os.path.join(os.path.dirname(file_path), 'charts')
        if not os.path.exists(chart_dir):
            os.makedirs(chart_dir)
        
        # 图表文件名
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        chart_file = os.path.join(chart_dir, f"{base_name}_chart.png")
        
        chart_type = chart_config.get('type', 'line')
        # 如果未配置x轴，使用数据的index作为x轴
        x_col = chart_config.get('x')
        if x_col is None:
            logger.info("未配置x轴，使用数据index作为x轴")
            x_col = 'index'
            df = df.reset_index()  # 重置索引，以便使用index作为x轴
        
        if chart_type == 'line':
            # 获取基础配置
            title = chart_config.get('title', '数据趋势图')
            x_label = chart_config.get('x_label', 'X轴')
            
            if not x_col:
                logger.error("折线图配置缺少x字段")
                return ""
                
            if x_col not in df.columns:
                logger.error(f"数据中不存在x={x_col}字段")
                return ""
            
            # 生成颜色序列
            colors = plt.cm.tab10(np.linspace(0, 1, MAX_COLORS))  # 生成10种不同颜色
            
            # 单Y轴多数据配置 (y为列表)
            if 'y' in chart_config and isinstance(chart_config['y'], list):
                y_fields = chart_config['y']
                y_label = chart_config.get('y_label', 'Y轴')
                
                # 绘制单Y轴多数据折线图
                plt.figure(figsize=(12, 6))
                
                for i, y_col in enumerate(y_fields):
                    if y_col not in df.columns:
                        logger.warning(f"数据中不存在y={y_col}字段，已跳过")
                        continue
                        
                    # 转换Y轴数据为数值类型
                    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                    df_clean = df.dropna(subset=[y_col])
                    
                    if df_clean.empty:
                        logger.warning(f"y={y_col}数据转换后为空，已跳过")
                        continue
                        
                    # 绘制折线图，使用不同颜色和标签
                    plt.plot(df_clean[x_col], df_clean[y_col], 
                             label=f"{y_col} ({y_label})", 
                             color=colors[i % len(colors)])
                
                # 设置x轴刻度间隔，解决标签密集问题
                ax = plt.gca()
                ax.xaxis.set_major_locator(MaxNLocator(prune='both', nbins=10))  # 限制最多显示10个刻度
                
                # 添加网格线 - 只显示Y轴网格线，使用虚线样式
                ax.yaxis.grid(True, linestyle=GRID_STYLE, alpha=GRID_ALPHA)
                
                plt.title(title)
                plt.xlabel(x_label)
                plt.ylabel(y_label)
                plt.xticks(rotation=45)
                plt.legend()
                plt.tight_layout()
                plt.savefig(chart_file)
                plt.close()
                
            # 双Y轴多数据配置 (left_y和right_y)
            elif 'left_y' in chart_config and 'right_y' in chart_config:
                left_series = chart_config['left_y']
                right_series = chart_config['right_y']
                
                # 确保left_y和right_y是列表
                if not isinstance(left_series, list) or not isinstance(right_series, list):
                    logger.error("双Y轴配置中left_y和right_y必须是列表")
                    return ""
                
                # 创建图形和左侧Y轴
                fig, ax1 = plt.subplots(figsize=(12, 6))
                ax2 = ax1.twinx()  # 创建右侧Y轴
                
                # 绘制左侧Y轴数据
                for i, series in enumerate(left_series):
                    y_col = series.get('name')
                    y_label = series.get('label', '左侧Y轴')
                    
                    if not y_col or y_col not in df.columns:
                        logger.warning(f"左侧Y轴数据中不存在name={y_col}字段，已跳过")
                        continue
                        
                    # 转换数据为数值类型
                    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                    df_clean = df.dropna(subset=[y_col])
                    
                    if df_clean.empty:
                        logger.warning(f"左侧Y轴y={y_col}数据转换后为空，已跳过")
                        continue
                        
                    # 绘制折线图，使用不同颜色
                    ax1.plot(df_clean[x_col], df_clean[y_col], 
                             label=f"{y_col} ({y_label})", 
                             color=colors[i % len(colors)])
                
                # 绘制右侧Y轴数据
                for i, series in enumerate(right_series):
                    y_col = series.get('name')
                    y_label = series.get('label', '右侧Y轴')
                    
                    if not y_col or y_col not in df.columns:
                        logger.warning(f"右侧Y轴数据中不存在name={y_col}字段，已跳过")
                        continue
                        
                    # 转换数据为数值类型
                    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                    df_clean = df.dropna(subset=[y_col])
                    
                    if df_clean.empty:
                        logger.warning(f"右侧Y轴y={y_col}数据转换后为空，已跳过")
                        continue
                        
                    # 绘制折线图，使用不同颜色
                    ax2.plot(df_clean[x_col], df_clean[y_col], 
                             label=f"{y_col} ({y_label})", 
                             color=colors[(i + len(left_series)) % len(colors)],
                             linestyle='--')  # 右侧数据使用虚线区分
                
                # 设置x轴刻度间隔，解决标签密集问题
                ax1.xaxis.set_major_locator(MaxNLocator(prune='both', nbins=10))  # 限制最多显示10个刻度
                
                # 添加网格线 - 只显示左侧Y轴网格线，使用虚线样式
                ax1.yaxis.grid(True, linestyle=GRID_STYLE, alpha=GRID_ALPHA)
                
                # 设置标题和标签
                plt.title(title)
                ax1.set_xlabel(x_label)
                ax1.set_ylabel(left_series[0].get('label', '左侧Y轴') if left_series else '左侧Y轴')
                ax2.set_ylabel(right_series[0].get('label', '右侧Y轴') if right_series else '右侧Y轴')
                
                # 合并图例
                lines1, labels1 = ax1.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(chart_file)
                plt.close()
                
            # 传统单Y轴单数据配置
            elif 'y' in chart_config and isinstance(chart_config['y'], str):
                y_col = chart_config['y']
                y_label = chart_config.get('y_label', 'Y轴')
                
                if y_col not in df.columns:
                    logger.error(f"数据中不存在y={y_col}字段")
                    return ""
                    
                # 转换Y轴数据为数值类型
                df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                df_clean = df.dropna(subset=[y_col])
                
                if df_clean.empty:
                    logger.warning("Y轴数据转换后为空，无法生成图表")
                    return ""
                    
                # 绘制传统单Y轴折线图
                plt.figure(figsize=(12, 6))
                plt.plot(df_clean[x_col], df_clean[y_col], label=f"{y_col} ({y_label})")
                
                # 设置x轴刻度间隔，解决标签密集问题
                ax = plt.gca()
                ax.xaxis.set_major_locator(MaxNLocator(prune='both', nbins=10))  # 限制最多显示10个刻度
                
                # 添加网格线 - 只显示Y轴网格线，使用虚线样式
                ax.yaxis.grid(True, linestyle=GRID_STYLE, alpha=GRID_ALPHA)
                
                plt.title(title)
                plt.xlabel(x_label)
                plt.ylabel(y_label)
                plt.xticks(rotation=45)
                plt.legend()
                plt.tight_layout()
                plt.savefig(chart_file)
                plt.close()
                
            else:
                logger.error("折线图配置错误，请使用y列表(单Y轴多数据)或left_y/right_y(双Y轴多数据)")
                return ""
            
        elif chart_type == 'candle':
            # K线图
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 按日期升序排序（从历史到现在）
            df = df.sort_index(ascending=True)
            
            # 转换数据类型为数值
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
            
            if df.empty:
                logger.warning("K线图数据转换后为空，无法生成图表")
                return ""
                
            # K线图添加网格线和优化x轴刻度
            mc = mpf.make_marketcolors(up='red', down='green', inherit=True)
            # 修复gridaxis参数错误，将'y'改为'vertical'
            s = mpf.make_mpf_style(rc=MPF_RC, marketcolors=mc, gridaxis='vertical', gridstyle=GRID_STYLE, gridcolor='gray')
            
            # 设置x轴刻度间隔
            fig, axlist = mpf.plot(
                df, 
                type='candle', 
                title=chart_config.get('title', 'K线图'),
                ylabel=chart_config.get('y_label', '价格'),
                figratio=(12, 6), 
                style=s,
                savefig=chart_file, 
                returnfig=True,
                warn_too_much_data=0  # 禁用数据量过大警告
            )
            
            # 限制x轴刻度数量
            axlist[0].xaxis.set_major_locator(MaxNLocator(prune='both', nbins=10))
            
            mpf.show()
        
        logger.info(f"图表已保存至: {chart_file}")
        return chart_file
    
    except Exception as e:
        logger.error(f"图表生成失败: {str(e)}")
        raise


def process_all_interfaces(config_path: str) -> None:
    """处理配置文件中的所有接口"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config or not config.get('interfaces'):
            logger.warning("配置文件中没有接口定义")
            return
            
        print(f"开始处理{len(config['interfaces'])}个接口...")
        
        for i, interface in enumerate(config['interfaces'], 1):
            print(f"\n处理接口 {i}/{len(config['interfaces'])}: {interface['name']}")
            
            # 调用API
            data = call_api(interface)
            if data is not None and not data.empty:
                print("返回数据预览:")
                print(data.head())
                
                # 保存数据
                file_path = save_data(data, interface.get('storage', {}), interface['name'])
                print(f"数据已保存至: {file_path}")
                
                # 生成图表
                if 'chart' in interface:
                    chart_path = generate_chart(data, interface['chart'], file_path)
                    if chart_path:
                        print(f"图表已保存至: {chart_path}")
                    else:
                        print("图表生成失败")
            else:
                print("接口调用失败或返回数据为空")
                
        print("\n所有接口处理完毕")
        
    except Exception as e:
        print(f"处理接口失败: {str(e)}")


# 主程序入口
if __name__ == "__main__":
    # 可以通过命令行参数指定配置文件路径，默认为"接口配置文件模板.yaml"
    import sys
    config_file = sys.argv[1] if len(sys.argv) > 1 else CONFIG_PATH
    process_all_interfaces(config_file)
