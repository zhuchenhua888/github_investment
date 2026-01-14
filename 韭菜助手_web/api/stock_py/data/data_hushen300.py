import os
import json
import requests
import time
from datetime import datetime
from typing import List, Dict
from .base_manager import BaseDataManager
class Hushen300DataManager(BaseDataManager):
    def __init__(self):
        super().__init__()
        self.hushen300_data: List[Dict] = []
        self.cache_file = os.path.join(self.cache_dir, 'hushen300_data.json')
        self.INIT_START_DATE = '2012-01-04'
    def init_data(self):
        if os.path.exists(self.cache_file):
            try:
                self.last_update_time = os.path.getmtime(self.cache_file)
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    if isinstance(cached_data, list):
                        sane = []
                        for it in cached_data:
                            try:
                                peg_v = float(it.get('peg', 0)) if it.get('peg') is not None else 0.0
                                close_v = float(it.get('close', 0)) if it.get('close') is not None else 0.0
                                if 0 <= peg_v <= 100 and close_v > 0:
                                    sane.append({'date': it.get('date'), 'close': close_v, 'peg': peg_v})
                            except Exception:
                                continue
                        self.hushen300_data = sane if len(sane) >= max(1, int(len(cached_data) * 0.5)) else []
                    else:
                        self.hushen300_data = []
            except Exception:
                self.hushen300_data = []
        else:
            self.hushen300_data = []
    def fetch_from_api(self, start_date: str, end_date: str) -> List[Dict]:
        try:
            start_date_str = start_date.replace('-', '')
            end_date_str = end_date.replace('-', '')
            url = 'https://www.csindex.com.cn/csindex-home/perf/index-perf'
            params = {'indexCode': 'H00300', 'startDate': start_date_str, 'endDate': end_date_str}
            resp = requests.get(url, params=params)
            if resp.status_code != 200:
                return []
            data = resp.json()
            return self.parse(data)
        except Exception:
            return []
    def parse(self, response: Dict) -> List[Dict]:
        if not isinstance(response, dict):
            return []
        data_list = None
        if isinstance(response.get('data'), list):
            data_list = response['data']
        elif isinstance(response.get('result'), list):
            data_list = response['result']
        else:
            return []
        date_map: Dict[str, Dict] = {}
        for item in data_list:
            trade_date = item.get('tradeDate')
            if not isinstance(trade_date, str):
                continue
            formatted_date = '-'.join([trade_date[:4], trade_date[4:6], trade_date[6:8]]) if len(trade_date) == 8 else trade_date
            close_raw = item.get('close')
            peg_raw = item.get('peg')
            try:
                close_val = float(close_raw) if close_raw is not None else None
            except Exception:
                close_val = None
            try:
                peg_val = float(peg_raw) if peg_raw is not None else None
            except Exception:
                peg_val = None
            if (close_val is None) or (peg_val is None):
                continue
            date_map[formatted_date] = {'date': formatted_date, 'close': close_val, 'peg': peg_val}
        parsed = list(date_map.values())
        parsed.sort(key=lambda x: x['date'])
        return parsed
    def merge_by_date(self, old_arr: List[Dict], new_arr: List[Dict]) -> List[Dict]:
        date_map: Dict[str, Dict] = {}
        if old_arr:
            for it in old_arr:
                if it and 'date' in it:
                    date_map[it['date']] = it
        if new_arr:
            for it in new_arr:
                if it and 'date' in it:
                    date_map[it['date']] = it
        result = list(date_map.values())
        result.sort(key=lambda x: x['date'])
        return result
    def update_data(self):
        if not self.should_update():
            return
        try:
            if self.hushen300_data:
                last_item = self.hushen300_data[-1] if self.hushen300_data else None
                last_date = last_item['date'] if last_item else self.INIT_START_DATE
            else:
                last_date = self.INIT_START_DATE
            start_date = last_date
            end_date = self.format_date(self.get_yesterday_date())
            if datetime.strptime(start_date, '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
                return
            new_data = self.fetch_from_api(start_date, end_date)
            if not new_data:
                return
            self.hushen300_data = self.merge_by_date(self.hushen300_data, new_data)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.hushen300_data, f, ensure_ascii=False, indent=2)
            self.last_update_time = time.time()
        except Exception:
            pass
    def get_data(self) -> List[Dict]:
        return self.hushen300_data
hushen300_manager = Hushen300DataManager()
