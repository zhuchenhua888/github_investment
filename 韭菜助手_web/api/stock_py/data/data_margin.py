import os
import json
import requests
import time
from typing import List, Dict
from .base_manager import BaseDataManager
class MarginAccountDataManager(BaseDataManager):
    def __init__(self):
        super().__init__()
        self.margin_data: List[Dict] = []
        self.cache_file = os.path.join(self.cache_dir, 'margin_account_data.json')
    def init_data(self):
        if os.path.exists(self.cache_file):
            try:
                self.last_update_time = os.path.getmtime(self.cache_file)
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    self.margin_data = cached if isinstance(cached, list) else []
            except Exception:
                self.margin_data = []
        else:
            self.margin_data = []
    def fetch_from_api(self) -> List[Dict]:
        try:
            url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
            base_params = {
                'reportName': 'RPTA_WEB_MARGIN_DAILYTRADE',
                'columns': 'ALL',
                'sortColumns': 'STATISTICS_DATE',
                'sortTypes': '-1',
                'pageSize': '500',
                'source': 'WEB',
                'client': 'WEB'
            }
            # first request to get total pages
            first = requests.get(url, params={**base_params, 'pageNumber': '1'}, timeout=10)
            if first.status_code != 200:
                return []
            try:
                first_obj = first.json()
            except Exception:
                return []
            total_pages = 1
            if isinstance(first_obj, dict) and isinstance(first_obj.get('result'), dict):
                pages_val = first_obj['result'].get('pages')
                try:
                    total_pages = int(pages_val) if pages_val is not None else 1
                except Exception:
                    total_pages = 1
            # collect all pages
            all_raw: List[Dict] = []
            for page in range(1, max(1, total_pages) + 1):
                resp = requests.get(url, params={**base_params, 'pageNumber': str(page)}, timeout=10)
                if resp.status_code != 200:
                    continue
                try:
                    obj = resp.json()
                except Exception:
                    continue
                if isinstance(obj, dict) and isinstance(obj.get('result'), dict) and isinstance(obj['result'].get('data'), list):
                    all_raw.extend(obj['result']['data'])
                elif isinstance(obj, dict) and isinstance(obj.get('data'), list):
                    all_raw.extend(obj['data'])
            # map to normalized rows
            out: List[Dict] = []
            for it in all_raw:
                ds = it.get('STATISTICS_DATE')
                fin = it.get('FIN_BALANCE')
                loan = it.get('LOAN_BALANCE')
                try:
                    fin_v = float(fin) if fin is not None else None
                except Exception:
                    fin_v = None
                try:
                    loan_v = float(loan) if loan is not None else None
                except Exception:
                    loan_v = None
                if isinstance(ds, str) and fin_v is not None and loan_v is not None:
                    if len(ds) == 8 and ds.isdigit():
                        date = f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
                    else:
                        date = ds[:10]
                    out.append({'date': date, 'fin_balance': fin_v, 'loan_balance': loan_v})
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
            dmap: Dict[str, Dict] = {it['date']: it for it in self.margin_data if 'date' in it}
            for it in new_rows:
                dmap[it['date']] = it
            merged = list(dmap.values())
            merged.sort(key=lambda x: x['date'])
            self.margin_data = merged
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.margin_data, f, ensure_ascii=False, indent=2)
            self.last_update_time = time.time()
        except Exception:
            pass
    def get_data(self) -> List[Dict]:
        return self.margin_data
margin_manager = MarginAccountDataManager()
