import requests
import json
import time
import os
from typing import List, Dict, Any

def fetch_lof_detail_data(fund_id: str) -> Dict[str, Any]:
    """获取LOF基金历史数据 - 移植自小程序 get_lof_detail.js"""
    timestamp = int(time.time() * 1000)
    
    # 特殊处理国投白银LOF(161226)
    if fund_id == '161226':
        url = f"https://www.jisilu.cn/data/lof/hist_list/161226?___jsl=LST___t={timestamp}"
        method = "GET"
        request_data = None
        referer = 'https://www.jisilu.cn/data/lof/'
    else:
        url = f"https://www.jisilu.cn/data/qdii/detail_hists/?___jsl=LST___t={timestamp}"
        method = "POST"
        request_data = {
            'is_search': 1,
            'fund_id': fund_id,
            'rp': 50,
            'page': 1
        }
        referer = 'https://www.jisilu.cn/data/qdii/'
    
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': referer,
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.jisilu.cn',
        'Connection': 'keep-alive'
    }
    
    if method == "POST":
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    
    cookie = os.environ.get('JISILU_COOKIE', '').strip()
    if cookie:
        headers['Cookie'] = cookie

    try:
        if method == "POST":
            response = requests.post(url, data=request_data, headers=headers, timeout=15)
        else:
            response = requests.get(url, headers=headers, timeout=15)
            
        if response.status_code == 200:
            return response.json()
        else:
            # 如果直接请求失败，尝试使用 jina 代理
            proxy_url = f"https://r.jina.ai/{url}"
            # 对于 GET 请求，代理通常更容易成功
            if method == "GET":
                proxy_resp = requests.get(proxy_url, headers=headers, timeout=15)
                if proxy_resp.status_code == 200:
                    try:
                        return json.loads(proxy_resp.text)
                    except:
                        pass
            return {"error": f"HTTP {response.status_code}", "rows": []}
    except Exception as e:
        return {"error": str(e), "rows": []}

def process_lof_detail_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """处理LOF详情数据"""
    if not data or 'rows' not in data or not isinstance(data['rows'], list):
        return []

    processed_list = []
    for row in data['rows']:
        cell = row.get('cell', {})
        
        # 处理数值字段
        def safe_float(val, precision=3):
            try:
                return f"{float(val):.{precision}f}" if val is not None and val != '-' else '-'
            except (ValueError, TypeError):
                return '-'

        price = safe_float(cell.get('price'), 3)
        net_value = safe_float(cell.get('net_value'), 4)
        est_val = safe_float(cell.get('est_val'), 4)
        
        # 处理百分比
        def format_pct(val):
            try:
                if val is None or val == '-':
                    return '-'
                return f"{float(val):.2f}%"
            except (ValueError, TypeError):
                return '-'

        discount_rt = format_pct(cell.get('discount_rt'))
        
        # 处理份额
        def format_int(val):
            try:
                return f"{int(val):,}" if val is not None and val != '-' else '-'
            except (ValueError, TypeError):
                return '-'

        amount = format_int(cell.get('amount'))
        amount_incr = cell.get('amount_incr')
        if amount_incr is not None and amount_incr != '-':
            try:
                val = int(amount_incr)
                amount_incr_str = f"+{val:,}" if val >= 0 else f"{val:,}"
            except (ValueError, TypeError):
                amount_incr_str = '-'
        else:
            amount_incr_str = '-'

        processed_list.append({
            'id': row.get('id'),
            'fundId': cell.get('fund_id'),
            'priceDt': cell.get('price_dt'),
            'price': price,
            'netValueDt': cell.get('net_value_dt'),
            'netValue': net_value,
            'estValDt': cell.get('est_val_dt'),
            'estVal': est_val,
            'discountRt': discount_rt,
            'amount': amount,
            'amountIncr': amount_incr_str,
            'isEst': cell.get('is_est') == 1
        })
    
    return processed_list
