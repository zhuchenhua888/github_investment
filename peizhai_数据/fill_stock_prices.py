import pandas as pd
import akshare as ak
import time
from datetime import datetime, timedelta
import numpy as np

def get_close_price(stock_code, target_date):
    """
    Fetch the close price for a stock on a specific date.
    If the date is a non-trading day, returns the close price of the NEXT trading day within 10 days.
    """
    if pd.isna(target_date) or str(target_date).strip() == '' or str(target_date).strip() == '---':
        return None
    
    try:
        # Normalize date to datetime
        if isinstance(target_date, str):
            dt = pd.to_datetime(target_date, errors='coerce')
        else:
            dt = pd.to_datetime(target_date, errors='coerce')
        
        if pd.isna(dt):
            return None
        
        # Start date is the target date
        start_date_str = dt.strftime("%Y%m%d")
        
        # End date is 10 days AFTER to find the next trading day
        end_dt = dt + timedelta(days=10)
        end_date_str = end_dt.strftime("%Y%m%d")
        
        # Fetch history
        stock_df = ak.stock_zh_a_hist(symbol=str(stock_code), start_date=start_date_str, end_date=end_date_str, adjust="qfq")
        
        if stock_df.empty:
            return None
            
        # The result might contain multiple rows starting from the first trading day >= target_date
        # We want the FIRST one (which is the target date if it's a trading day, or the next one if not)
        first_row = stock_df.iloc[0]
        close_price = first_row['收盘']
        actual_date = first_row['日期']
        
        # Check if actual date is too far? (Should be within the range we queried)
        # print(f"Target: {start_date_str}, Found: {actual_date}")
        
        return close_price

    except Exception as e:
        print(f"Error fetching data for {stock_code} on {target_date}: {e}")
        return None

def get_index_close_price(target_date, index_symbol="sh000001"):
    """
    Fetch the close price for a market index on a specific date.
    If the date is a non-trading day, returns the close price of the NEXT trading day within 10 days.
    Default index: 上证指数 (sh000001)
    """
    if pd.isna(target_date) or str(target_date).strip() == '' or str(target_date).strip() == '---':
        return None
    
    try:
        # Normalize date to datetime
        if isinstance(target_date, str):
            dt = pd.to_datetime(target_date, errors='coerce')
        else:
            dt = pd.to_datetime(target_date, errors='coerce')
        
        if pd.isna(dt):
            return None
        
        start_date_str = dt.strftime("%Y%m%d")
        end_dt = dt + timedelta(days=10)
        end_date_str = end_dt.strftime("%Y%m%d")
        
        # Prefer robust daily index API; fallback on hist if needed
        try:
            index_daily = ak.stock_zh_index_daily(symbol=index_symbol)
            if index_daily is not None and not index_daily.empty and 'date' in index_daily.columns:
                index_daily['date'] = pd.to_datetime(index_daily['date'], errors='coerce')
                end_dt = dt + timedelta(days=10)
                sub = index_daily[(index_daily['date'] >= dt) & (index_daily['date'] <= end_dt)].sort_values('date')
                if not sub.empty:
                    return sub.iloc[0]['close']
        except Exception:
            pass
        
        # Fallback: older API
        index_df = ak.index_zh_a_hist(symbol=index_symbol, start_date=start_date_str, end_date=end_date_str)
        if index_df is None or len(getattr(index_df, "index", [])) == 0 or index_df.empty:
            return None
        
        possible_close_cols = ['收盘', '收盘价', 'close', 'Close']
        close_col = next((c for c in possible_close_cols if c in index_df.columns), None)
        if close_col is None:
            return None
        
        possible_date_cols = ['日期', 'date', 'Date']
        date_col = next((c for c in possible_date_cols if c in index_df.columns), None)
        if date_col is None:
            return None
        
        index_df[date_col] = pd.to_datetime(index_df[date_col], errors='coerce')
        end_dt = dt + timedelta(days=10)
        sub = index_df[(index_df[date_col] >= dt) & (index_df[date_col] <= end_dt)].sort_values(date_col)
        if sub.empty:
            return None
        return sub.iloc[0][close_col]
    except Exception as e:
        print(f"Error fetching index data {index_symbol} on {target_date}: {e}")
        return None

def process_excel(file_path, output_path):
    print(f"Reading {file_path}...")
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return

    # Identify the date columns and their target price columns
    date_keywords = ["交易所受理时间", "上市委通过时间", "同意注册时间", "申购时间", "上市日期"]
    
    # We will track which columns need filling per date: {date_col_name: (stock_price_col, index_price_col)}
    cols_to_fill = {}
    
    index_symbol = "sh000001"
    index_dates = None
    index_closes = None
    lookup_index = None
    try:
        idx = ak.stock_zh_index_daily(symbol=index_symbol)
        if idx is not None and not idx.empty and "date" in idx.columns and "close" in idx.columns:
            idx["date"] = pd.to_datetime(idx["date"], errors="coerce")
            idx = idx.dropna(subset=["date"]).sort_values("date")
            index_dates = idx["date"].to_numpy()
            index_closes = idx["close"].to_numpy()
    except Exception:
        pass
    if index_dates is None or index_closes is None:
        try:
            idx2 = ak.index_zh_a_hist(symbol=index_symbol, start_date="19900101", end_date=datetime.today().strftime("%Y%m%d"))
            if idx2 is not None and not idx2.empty:
                dcol = "日期" if "日期" in idx2.columns else ("date" if "date" in idx2.columns else None)
                ccol = "收盘" if "收盘" in idx2.columns else ("收盘价" if "收盘价" in idx2.columns else ("close" if "close" in idx2.columns else None))
                if dcol is not None and ccol is not None:
                    idx2[dcol] = pd.to_datetime(idx2[dcol], errors="coerce")
                    idx2 = idx2.dropna(subset=[dcol]).sort_values(dcol)
                    index_dates = idx2[dcol].to_numpy()
                    index_closes = idx2[ccol].to_numpy()
        except Exception:
            pass
    if index_dates is not None and index_closes is not None:
        def lookup_index(date_val):
            if pd.isna(date_val) or str(date_val).strip() == "" or str(date_val).strip() == "---":
                return None
            dt = pd.to_datetime(date_val, errors="coerce")
            if pd.isna(dt):
                return None
            end_dt = dt + timedelta(days=10)
            pos = np.searchsorted(index_dates, np.datetime64(dt), side="left")
            if pos >= len(index_dates):
                return None
            d0 = index_dates[pos]
            if d0 <= np.datetime64(end_dt):
                return float(index_closes[pos])
            return None
    
    # 1. Insert new columns if they don't exist
    print("Preparing columns...")
    # We iterate over a copy of columns or just look up by name, because inserting changes indices
    for col in date_keywords:
        if col in df.columns:
            stock_price_col = f"{col}_收盘价"
            index_price_col = f"{col}_大盘收盘价"
            
            # Insert stock price column right after date column if missing
            if stock_price_col not in df.columns:
                loc_date = df.columns.get_loc(col)
                df.insert(loc_date + 1, stock_price_col, None)
                print(f"  Inserted column: {stock_price_col}")
            else:
                print(f"  Column already exists: {stock_price_col}")
            
            # Insert index price column right after stock price column if missing
            # Ensure we get latest location after potential insertion
            loc_stock = df.columns.get_loc(stock_price_col)
            if index_price_col not in df.columns:
                df.insert(loc_stock + 1, index_price_col, None)
                print(f"  Inserted column: {index_price_col}")
            else:
                print(f"  Column already exists: {index_price_col}")
            
            cols_to_fill[col] = (stock_price_col, index_price_col)
    
    if not cols_to_fill:
        print("No matching date columns found to process.")
        return

    # 2. Iterate through rows and fill data
    print("Processing rows...")
    total_rows = len(df)
    
    for idx, row in df.iterrows():
        stock_code = row['股票代码']
        if pd.isna(stock_code):
            continue
            
        # Ensure stock code is 6 digits
        stock_code = str(stock_code).split('.')[0] 
        stock_code = stock_code.zfill(6)
        
        # Optional: Print progress every 10 rows
        if idx % 10 == 0:
            print(f"  Processing row {idx + 1}/{total_rows}...")

        for date_col, (stock_price_col, index_price_col) in cols_to_fill.items():
            date_val = row[date_col]
            
            # Fill stock price if empty
            current_stock = df.at[idx, stock_price_col]
            if (pd.isna(current_stock) or str(current_stock).strip() == '') and pd.notna(date_val):
                price_stock = get_close_price(stock_code, date_val)
                if price_stock is not None:
                    df.at[idx, stock_price_col] = price_stock
            
            # Fill index price if empty
            current_index = df.at[idx, index_price_col]
            if (pd.isna(current_index) or str(current_index).strip() == '') and pd.notna(date_val):
                price_index = None
                if lookup_index is not None:
                    price_index = lookup_index(date_val)
                else:
                    price_index = get_index_close_price(date_val, index_symbol=index_symbol)
                if price_index is not None:
                    df.at[idx, index_price_col] = price_index
            
            # Optional polite sleep
            # time.sleep(0.02)

    print(f"Saving to {output_path}...")
    df.to_excel(output_path, index=False)
    print("Done.")

if __name__ == "__main__":
    # You can change the file name here
    input_file = "cb_data.xlsx"  # Replace with your actual file name, e.g., "cb_data.xlsx"
    output_file = "cb_data_filled.xlsx"
    process_excel(input_file, output_file)
