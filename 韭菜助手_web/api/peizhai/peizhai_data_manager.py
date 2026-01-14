import os
import time
import json
import requests
from typing import List, Dict

class PeizhaiDataManager:
    def __init__(self):
        self.data = []

    def fetch_from_api(self) -> List[Dict]:
        ts = int(time.time() * 1000)
        url = f'https://www.jisilu.cn/data/cbnew/pre_list/?___jsl=LST___t={ts}'
        session = requests.Session()
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.jisilu.cn/data/cbnew/',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.jisilu.cn',
            'Connection': 'keep-alive'
        }
        cookie = os.environ.get('JISILU_COOKIE', '').strip()
        if cookie:
            headers['Cookie'] = cookie
        resp = session.get(url, headers=headers, timeout=15)
        rows = []
        if resp.status_code == 200:
            try:
                data = resp.json()
                rows = data.get('rows', [])
            except Exception:
                pass
        if not rows:
            try:
                proxy_url = 'https://r.jina.ai/http://www.jisilu.cn/data/cbnew/pre_list/'
                proxy_resp = session.get(proxy_url, headers=headers, timeout=15)
                if proxy_resp.status_code == 200:
                    txt = proxy_resp.text
                    data2 = json.loads(txt)
                    rows = data2.get('rows', [])
            except Exception:
                rows = []
        out = []
        for item in rows:
            cell = item.get('cell', {})
            code = cell.get('bond_id') or cell.get('id') or ''
            name = cell.get('bond_nm') or cell.get('stock_nm') or ''
            stock_code = cell.get('stock_id') or ''
            stock_name = cell.get('stock_nm') or ''
            progress_dt = cell.get('progress_dt') or cell.get('updated_at') or cell.get('apply_date') or ''
            progress_nm = cell.get('progress_nm') or cell.get('progress') or cell.get('status') or ''
            # 详情文本聚合
            progress_full = cell.get('progress_tip') or cell.get('remark') or ''
            price_raw = cell.get('price')
            price = None
            if isinstance(price_raw, (int, float)):
                price = float(price_raw)
            else:
                try:
                    price = float(str(price_raw)) if price_raw not in (None, '-', '') else None
                except Exception:
                    price = None
            # 配售10张所需股数
            apply10_raw = cell.get('apply10')
            apply10 = None
            if isinstance(apply10_raw, (int, float)):
                apply10 = float(apply10_raw)
            else:
                try:
                    apply10 = float(str(apply10_raw)) if apply10_raw not in (None, '-', '') else None
                except Exception:
                    apply10 = None
            # 发行规模（亿元）
            amount_raw = cell.get('amount')
            try:
                amount_val = float(amount_raw) if amount_raw not in (None, '-', '') else 0.0
            except Exception:
                amount_val = 0.0
            # 百元含权（元），如果有直接用；否则留空
            cb_amount_raw = cell.get('cb_amount')
            cb_amount = None
            if isinstance(cb_amount_raw, (int, float)):
                cb_amount = float(cb_amount_raw)
            else:
                try:
                    cb_amount = float(str(cb_amount_raw)) if cb_amount_raw not in (None, '-', '') else None
                except Exception:
                    cb_amount = None
            # 市场类型与配债策略估算
            market_type = 'sh' if str(stock_code).startswith('6') else 'sz'
            # 计算配债策略（模仿小程序逻辑）
            # 深市一手所需股数 = ceil(apply10)
            # 沪市一手党股数 = ceil(0.5 * apply10 / 100) * 100
            if apply10 is not None and apply10 > 0:
                base_shares = int(__import__('math').ceil(apply10))
                one_hand_shares = int(__import__('math').ceil(0.5 * apply10 / 100.0) * 100)
            else:
                base_shares = 100
                one_hand_shares = 100
            if price is not None:
                base_cost_val = base_shares * price
                one_hand_cost_val = one_hand_shares * price
                base_cost = f"{base_cost_val:.2f}元"
                one_hand_cost = f"{one_hand_cost_val:.2f}元"
            else:
                base_cost = "需补充股价"
                one_hand_cost = "需补充股价"
            opp = 'low'
            out.append({
                'code': code,
                'name': name,
                'stockCode': stock_code,
                'stockName': stock_name,
                'price': price if price is not None else 0.0,
                'opportunity': opp,
                'progress_dt': progress_dt,
                'progress_nm': progress_nm,
                'progress_full': progress_full,
                'amount': amount_val,
                'cb_amount': cb_amount,
                'market_type': market_type,
                'calcAllocation': {
                    'oneHandShares': one_hand_shares,
                    'oneHandCost': one_hand_cost,
                    'baseShares': base_shares,
                    'baseCost': base_cost
                }
            })
        self.data = out
        return out

peizhai_manager = PeizhaiDataManager()
