import os
import json
import time
import requests
from typing import List, Dict
from .base_manager import BaseDataManager
class ChinaStockMarketDataManager(BaseDataManager):
    def __init__(self):
        super().__init__()
        self.stock_market_data: List[Dict] = []
        self.cache_file = os.path.join(self.cache_dir, 'stock_market_data.json')
    def init_data(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    self.stock_market_data = cached if isinstance(cached, list) else []
            except Exception:
                self.stock_market_data = []
        else:
            self.stock_market_data = []
    def fetch_from_api(self) -> List[Dict]:
        try:
            url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
            params = {
                'reportName': 'RPT_ECONOMY_STOCK_STATISTICS',
                'columns': 'REPORT_DATE,TIME,TOTAL_MARKE_SH,TOTAL_MARKE_SZ',
                'sortColumns': 'REPORT_DATE',
                'sortTypes': '-1',
                'pageNumber': '1',
                'pageSize': '1000',
                'source': 'WEB',
                'client': 'WEB'
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                return []
            try:
                obj = resp.json()
            except Exception:
                return []
            data_list = []
            if isinstance(obj, dict):
                if isinstance(obj.get('result'), dict) and isinstance(obj['result'].get('data'), list):
                    data_list = obj['result']['data']
                elif isinstance(obj.get('data'), list):
                    data_list = obj['data']
            out: List[Dict] = []
            for it in data_list:
                date = it.get('TIME')
                sh = it.get('TOTAL_MARKE_SH')
                sz = it.get('TOTAL_MARKE_SZ')
                try:
                    sh_v = float(sh) if sh is not None else None
                except Exception:
                    sh_v = None
                try:
                    sz_v = float(sz) if sz is not None else None
                except Exception:
                    sz_v = None
                if date and isinstance(date, str) and isinstance(sh_v, (int, float)) and isinstance(sz_v, (int, float)):
                    out.append({'date': date, 'market_cap_shanghai': float(sh_v), 'market_cap_shenzhen': float(sz_v)})
            out.sort(key=lambda x: x['date'])
            return out
        except Exception:
            return []
    def update_data(self):
        if not self.should_update():
            return
        try:
            new_rows = self.fetch_from_api()
            if not new_rows:
                return
            dmap: Dict[str, Dict] = {it['date']: it for it in self.stock_market_data if 'date' in it}
            for it in new_rows:
                dmap[it['date']] = it
            merged = list(dmap.values())
            merged.sort(key=lambda x: x['date'])
            self.stock_market_data = merged
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.stock_market_data, f, ensure_ascii=False, indent=2)
            self.last_update_time = time.time()
        except Exception:
            pass
    def get_data(self) -> List[Dict]:
        return self.stock_market_data
china_stock_market_manager = ChinaStockMarketDataManager()
