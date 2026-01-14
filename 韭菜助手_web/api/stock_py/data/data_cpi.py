import os
import json
import time
import requests
from typing import List, Dict
from .base_manager import BaseDataManager
class ChinaCPIDataManager(BaseDataManager):
    def __init__(self):
        super().__init__()
        self.cpi_data: List[Dict] = []
        self.cache_file = os.path.join(self.cache_dir, 'cpi_data.json')
    def init_data(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    self.cpi_data = cached if isinstance(cached, list) else []
            except Exception:
                self.cpi_data = []
        else:
            self.cpi_data = []
    def fetch_from_api(self) -> List[Dict]:
        try:
            url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
            params = {
                'columns': 'REPORT_DATE,TIME,NATIONAL_SAME',
                'pageNumber': '1',
                'pageSize': '2000',
                'sortColumns': 'REPORT_DATE',
                'sortTypes': '-1',
                'source': 'WEB',
                'client': 'WEB',
                'reportName': 'RPT_ECONOMY_CPI'
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
                month = it.get('TIME')
                yoy = it.get('NATIONAL_SAME')
                try:
                    yoy_v = float(yoy) if yoy is not None else None
                except Exception:
                    yoy_v = None
                if month and isinstance(month, str) and isinstance(yoy_v, (int, float)):
                    out.append({'month': month, 'national_yoy': float(yoy_v)})
            out.sort(key=lambda x: x['month'])
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
            mmap: Dict[str, Dict] = {it['month']: it for it in self.cpi_data if 'month' in it}
            for it in new_rows:
                mmap[it['month']] = it
            merged = list(mmap.values())
            merged.sort(key=lambda x: x['month'])
            self.cpi_data = merged
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cpi_data, f, ensure_ascii=False, indent=2)
            self.last_update_time = time.time()
        except Exception:
            pass
    def get_data(self) -> List[Dict]:
        return self.cpi_data
china_cpi_manager = ChinaCPIDataManager()
