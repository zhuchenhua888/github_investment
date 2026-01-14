import os
import json
import time
import requests
from typing import List, Dict
from .base_manager import BaseDataManager
class ChinaGDPDataManager(BaseDataManager):
    def __init__(self):
        super().__init__()
        self.gdp_data: List[Dict] = []
        self.cache_file = os.path.join(self.cache_dir, 'gdp_data.json')
    def init_data(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    self.gdp_data = cached if isinstance(cached, list) else []
            except Exception:
                self.gdp_data = []
        else:
            self.gdp_data = []
    def fetch_from_api(self) -> List[Dict]:
        try:
            url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
            params = {
                'columns': 'REPORT_DATE,TIME,DOMESTICL_PRODUCT_BASE,FIRST_PRODUCT_BASE,SECOND_PRODUCT_BASE,THIRD_PRODUCT_BASE,SUM_SAME,FIRST_SAME,SECOND_SAME,THIRD_SAME',
                'pageNumber': '1',
                'pageSize': '2000',
                'sortColumns': 'REPORT_DATE',
                'sortTypes': '-1',
                'source': 'WEB',
                'client': 'WEB',
                'reportName': 'RPT_ECONOMY_GDP',
                'p': '1',
                'pageNo': '1',
                'pageNum': '1'
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
                label = it.get('TIME')
                raw = it.get('DOMESTICL_PRODUCT_BASE')
                try:
                    val = float(raw) if raw is not None else None
                except Exception:
                    val = None
                if label and isinstance(label, str) and isinstance(val, (int, float)):
                    out.append({'quarter': label, 'gdp_abs': float(val)})
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
            qmap: Dict[str, Dict] = {}
            for it in self.gdp_data:
                if isinstance(it, dict) and 'quarter' in it:
                    qmap[it['quarter']] = it
            for it in new_rows:
                if isinstance(it, dict) and 'quarter' in it:
                    qmap[it['quarter']] = it
            def sort_key(item: Dict) -> tuple:
                import re
                label = str(item.get('quarter', ''))
                ym = re.search(r'(\d{4})', label)
                y = int(ym.group(1)) if ym else 0
                cov = 0
                m = re.search(r'第1(?:-([一二三四1234]))?季度', label)
                if m:
                    g = m.group(1)
                    if not g:
                        cov = 1
                    else:
                        mp = {'一': 1, '二': 2, '三': 3, '四': 4, '1': 1, '2': 2, '3': 3, '4': 4}
                        cov = mp.get(g, 0)
                return (y, cov)
            self.gdp_data = sorted(list(qmap.values()), key=sort_key)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.gdp_data, f, ensure_ascii=False, indent=2)
            self.last_update_time = time.time()
        except Exception:
            pass
    def get_data(self) -> List[Dict]:
        return self.gdp_data
china_gdp_manager = ChinaGDPDataManager()
