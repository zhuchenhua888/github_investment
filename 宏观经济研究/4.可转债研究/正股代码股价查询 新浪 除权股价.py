import pandas as pd
import requests
import re
from datetime import datetime, timedelta
from chinese_calendar import is_workday
import time
import random
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建会话
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    return session

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

# 处理股票代码
def process_stock_code(code):
    code = str(code).strip()
    if len(code) < 6:
        code = code.zfill(6)
    if code.startswith("6"):
        return f"sh{code}"
    elif code.startswith(("0", "3")):
        return f"sz{code}"
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

# 获取前复权股票数据
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, ValueError))
)
def get_stock_data(session, stock_code, start_date, end_date):
    try:
        url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={stock_code}&scale=240&ma=no&datalen=1023"
        
        delay = random.uniform(5, 10)
        logger.info(f"等待{delay:.2f}秒后请求{stock_code}...")
        time.sleep(delay)
        
        response = session.get(url, timeout=20)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 15))
            logger.warning(f"触发限流，{retry_after}秒后重试")
            time.sleep(retry_after)
            raise requests.exceptions.RequestException(f"Rate limited")
        
        response.raise_for_status()
        data = eval(response.text)
        if not data:
            logger.warning(f"{stock_code}无历史数据")
            return None
        
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["day"]).dt.strftime("%Y-%m-%d")
        result = df[(df["date"] >= start_date) & (df["date"] <= end_date)][["date", "open", "close"]]
        logger.info(f"{stock_code}获取{len(result)}条前复权数据")
        return result
    except Exception as e:
        logger.error(f"获取{stock_code}数据失败: {str(e)}")
        raise

# 主函数
def main():
    session = create_session()
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

    for idx, row in df_bond.iterrows():
        try:
            stock_code = str(row["正股代码"]).strip()
            market_code = process_stock_code(stock_code)
            if not market_code:
                logger.warning(f"无效代码: {stock_code}，跳过")
                continue

            date_cols = {
                "同意注册日期": ["同意注册日期_开盘价", "同意注册日期_收盘价"],
                "上市委通过日期": ["上市委通过日期_开盘价", "上市委通过日期_收盘价"],
                "申购日期": ["申购日期_开盘价", "申购日期_收盘价"],
                "上市时间": ["上市时间_开盘价", "上市时间_收盘价"]
            }

            dates = []
            # 修复缩进错误并使用英文变量名
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

            start_date = (datetime.strptime(min(dates), "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = (datetime.strptime(max(dates), "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
            
            stock_data = get_stock_data(session, market_code, start_date, end_date)
            if stock_data is None:
                continue

            result_row = row.copy()
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
                    logger.warning(f"{market_code}在{dt}无交易数据")

            if subscription_date:
                prev_sub_date = previous_trading_day(subscription_date)
                if prev_sub_date:
                    mask = stock_data["date"] == prev_sub_date
                    if mask.any():
                        price = stock_data[mask].iloc[0]
                        result_row["申购日前一交易日_开盘价"] = price["open"]
                        result_row["申购日前一交易日_收盘价"] = price["close"]
                    else:
                        logger.warning(f"{market_code}在申购日前一交易日{prev_sub_date}无数据")

            df_result = pd.concat([df_result, pd.DataFrame([result_row])], ignore_index=True)
                
        except Exception as e:
            logger.error(f"处理第{idx}条数据错误: {str(e)}，跳过")
            continue

    df_result.to_csv("可转债股票价格数据.csv", index=False)
    logger.info(f"处理完成，共获取{len(df_result)}条有效数据")

if __name__ == "__main__":
    main()