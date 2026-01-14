import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from .base_manager import BaseDataManager

def _parse_bond_response(resp_obj) -> List[Dict]:
    if not isinstance(resp_obj, dict):
        return []
    he_list = None
    if isinstance(resp_obj.get('heList'), list):
        he_list = resp_obj['heList']
    elif isinstance(resp_obj.get('data'), list):
        he_list = resp_obj['data']
    else:
        return []
    out = []
    for item in he_list:
        date = item.get('workTime')
        ten = item.get('tenYear')
        if date and ten is not None:
            try:
                out.append({'date': date, 'yield': float(ten)})
            except Exception:
                continue
    return out

class BondYieldDataManager(BaseDataManager):
    def __init__(self):
        super().__init__()
        self.bond_yield_data: List[Dict] = []
        self.cache_file = os.path.join(self.cache_dir, 'bond_yield_data.json')

    def init_data(self):
        self.update_last_update_time(self.cache_file)
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    self.bond_yield_data = cached_data if isinstance(cached_data, list) else []
            except Exception:
                self.bond_yield_data = []
        else:
            self.bond_yield_data = []

    def fetch_from_api(self, start_date: str, end_date: str) -> List[Dict]:
        try:
            url = 'https://yield.chinabond.com.cn/cbweb-czb-web/czb/historyQuery'
            rows: List[Dict] = []
            cur_start = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            while cur_start <= end_dt:
                cur_end = cur_start.replace(year=cur_start.year + 1) - timedelta(days=1)
                if cur_end > end_dt:
                    cur_end = end_dt
                params = {
                    'startDate': self.format_date(cur_start),
                    'endDate': self.format_date(cur_end),
                    'gjqx': 0,
                    'locale': 'cn_ZH',
                    'qxmc': 1
                }
                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    try:
                        data_obj = resp.json()
                        rows.extend(_parse_bond_response(data_obj))
                    except Exception:
                        pass
                cur_start = cur_start.replace(year=cur_start.year + 1)
                time.sleep(0.1)
            rows.sort(key=lambda x: x['date'])
            return rows
        except Exception:
            return []
    def update_data(self):
        if not self.should_update():
            return
        try:
            if self.bond_yield_data:
                last_item = self.bond_yield_data[-1] if self.bond_yield_data else None
                last_date = last_item['date'] if last_item else '2012-01-01'
            else:
                last_date = '2012-01-01'
            start_date = last_date
            end_date = self.format_date(self.get_yesterday_date())
            if datetime.strptime(start_date, '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
                return
            new_data = self.fetch_from_api(start_date, end_date)
            if not new_data:
                return
            date_map = {it['date']: it for it in self.bond_yield_data}
            for it in new_data:
                date_map[it['date']] = it
            self.bond_yield_data = sorted(list(date_map.values()), key=lambda x: x['date'])
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.bond_yield_data, f, ensure_ascii=False, indent=2)
            self.last_update_time = time.time()
        except Exception:
            pass
    def get_data(self) -> List[Dict]:
        return self.bond_yield_data
bond_yield_manager = BondYieldDataManager()
