import pandas as pd
import akshare as ak
import re
from datetime import datetime, timedelta
from chinese_calendar import is_workday
import time
import random
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 读取可转债数据
def read_convertible_bond_data():
    try:
        df = pd.read_excel("可转债整理0812.xlsx")
        if "正股代码" not in df.columns:
            logger.error("Excel中缺少'正股代码'列")
            return None
        df.columns = [col.strip() for col in df.columns]
        logger.info(f"成功读取到{len(df)}条可转债数据")
        return df
    except Exception as e:
        logger.error(f"读取Excel失败: {str(e)}")
        return None

# 获取前一交易日
def previous_trading_day(date_str):
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        for i in range(1, 11):
            date -= timedelta(days=1)
            if is_workday(date) and date.weekday() < 5:
                prev_date = date.strftime("%Y-%m-%d")
                logger.info(f"前一交易日: {prev_date}")
                return prev_date
        logger.warning(f"未找到前一交易日: {date_str}")
        return None
    except Exception as e:
        logger.error(f"获取前一交易日失败: {str(e)}")
        return None

# 获取下个交易日
def next_trading_day(date_str):
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        for i in range(1, 11):
            date += timedelta(days=1)
            if is_workday(date) and date.weekday() < 5:
                next_date = date.strftime("%Y-%m-%d")
                logger.info(f"下个交易日: {next_date}")
                return next_date
        logger.warning(f"未找到下个交易日: {date_str}")
        return None
    except Exception as e:
        logger.error(f"获取下个交易日失败: {str(e)}")
        return None

# 标准化日期
def standardize_date(date_str):
    try:
        if pd.isna(date_str):
            return None
        date_str = str(date_str).split()[0]
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y%m%d"]:
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        logger.warning(f"无法解析日期格式: {date_str}")
        return None
    except Exception as e:
        logger.error(f"日期处理错误: {str(e)}")
        return None

# 使用AKShare获取前复权数据
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=5),
    retry=retry_if_exception_type(Exception)
)
def get_akshare_data(stock_code, start_date, end_date):
    try:
        # 转换日期格式为YYYYMMDD
        start_str = start_date.replace("-", "")
        end_str = end_date.replace("-", "")
        
        # 使用AKShare接口获取前复权数据
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_str,
            end_date=end_str,
            adjust="qfq"  # 前复权
        )
        
        if df.empty:
            logger.warning(f"{stock_code}无历史数据")
            return None
            
        # 重命名列并格式化日期
        df["date"] = pd.to_datetime(df["日期"]).dt.strftime("%Y-%m-%d")
        result = df[["date", "开盘", "收盘"]].rename(columns={"开盘": "open", "收盘": "close"})
        logger.info(f"{stock_code}获取{len(result)}条前复权数据")
        return result
    except Exception as e:
        logger.error(f"获取{stock_code}数据失败: {str(e)}")
        raise

# 主函数
def main():
    df_bond = read_convertible_bond_data()
    if df_bond is None:
        logger.error("数据读取失败，程序终止")
        return

    result_cols = df_bond.columns.tolist() + [
        "同意注册日期_开盘价", "同意注册日期_收盘价",
        "上市委通过日期_开盘价", "上市委通过日期_收盘价",
        "申购日期_开盘价", "申购日期_收盘价",
        "申购日前一交易日_开盘价", "申购日前一交易日_收盘价",
        "上市时间_开盘价", "上市时间_收盘价"
    ]
    df_result = pd.DataFrame(columns=result_cols)

    # 处理前5条数据
    for idx, row in df_bond.iterrows():
        try:
            stock_code = str(row["正股代码"]).strip().zfill(6)
            if len(stock_code) != 6:
                logger.warning(f"无效代码: {stock_code}，跳过")
                continue

            date_cols = {
                "同意注册日期": ["同意注册日期_开盘价", "同意注册日期_收盘价"],
                "上市委通过日期": ["上市委通过日期_开盘价", "上市委通过日期_收盘价"],
                "申购日期": ["申购日期_开盘价", "申购日期_收盘价"],
                "上市时间": ["上市时间_开盘价", "上市时间_收盘价"]
            }

            dates = []
            subscription_date = standardize_date(row.get("申购日期"))
            if subscription_date:
                prev_sub_date = previous_trading_day(subscription_date)
                if prev_sub_date:
                    dates.append(prev_sub_date)
            
            for col in date_cols:
                dt = standardize_date(row[col])
                if dt:
                    date_obj = datetime.strptime(dt, "%Y-%m-%d")
                    if not is_workday(date_obj) or date_obj.weekday() >= 5:
                        dt = next_trading_day(dt)
                    if dt:
                        dates.append(dt)
            
            if not dates:
                logger.warning(f"无有效日期，跳过")
                continue

            # 扩展日期范围
            start_date = (datetime.strptime(min(dates), "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = (datetime.strptime(max(dates), "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
            
            # 使用AKShare获取数据
            stock_data = get_akshare_data(stock_code, start_date, end_date)
            if stock_data is None:
                continue

            result_row = row.copy()
            # 处理常规日期
            for col, price_cols in date_cols.items():
                dt = standardize_date(row[col])
                if not dt:
                    continue
                
                date_obj = datetime.strptime(dt, "%Y-%m-%d")
                if not is_workday(date_obj) or date_obj.weekday() >= 5:
                    dt = next_trading_day(dt)
                    if not dt:
                        continue
                
                mask = stock_data["date"] == dt
                if mask.any():
                    price = stock_data[mask].iloc[0]
                    result_row[price_cols[0]] = price["open"]
                    result_row[price_cols[1]] = price["close"]
                else:
                    logger.warning(f"{stock_code}在{dt}无交易数据")

            # 处理申购日前一交易日
            if subscription_date:
                prev_sub_date = previous_trading_day(subscription_date)
                if prev_sub_date:
                    mask = stock_data["date"] == prev_sub_date
                    if mask.any():
                        price = stock_data[mask].iloc[0]
                        result_row["申购日前一交易日_开盘价"] = price["open"]
                        result_row["申购日前一交易日_收盘价"] = price["close"]
                    else:
                        logger.warning(f"{stock_code}在申购日前一交易日{prev_sub_date}无数据")

            df_result = pd.concat([df_result, pd.DataFrame([result_row])], ignore_index=True)
            # 控制请求频率
            time.sleep(random.uniform(3, 5))
                
        except Exception as e:
            logger.error(f"处理第{idx}条数据错误: {str(e)}，跳过")
            continue

    df_result.to_csv("可转债股票价格数据.csv", index=False)
    logger.info(f"处理完成，共获取{len(df_result)}条有效数据")

if __name__ == "__main__":
    main()