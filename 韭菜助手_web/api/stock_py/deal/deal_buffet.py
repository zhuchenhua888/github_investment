from typing import List, Dict, Any, Optional
from math import isnan
def to_num(value) -> float:
    try:
        num = float(value)
        return num if not (isnan(num) or num == float('inf') or num == float('-inf')) else float('nan')
    except (TypeError, ValueError):
        return float('nan')
def ym_from_date_str(date_str: str) -> str:
    if not date_str:
        return ''
    import re
    m = re.search(r'(\d{4}).*?(\d{1,2})', str(date_str))
    if m:
        y = m.group(1)
        mm = str(m.group(2)).zfill(2)
        return f"{y}-{mm}"
    return ''
def quarter_to_ym(quarter_str: str) -> str:
    import re
    y_m = re.search(r'(\d{4})', str(quarter_str))
    if not y_m:
        return ''
    y = y_m.group(1)
    q_m = re.search(r'Q([1-4])|([一二三四1234])季度', str(quarter_str))
    qn = 4
    if q_m:
        g1 = q_m.group(1)
        g2 = q_m.group(2)
        if g1:
            qn = int(g1)
        else:
            mp = {'一': 1, '二': 2, '三': 3, '四': 4, '1': 1, '2': 2, '3': 3, '4': 4}
            qn = mp.get(g2, 4)
    month_map = {1: '03', 2: '06', 3: '09', 4: '12'}
    return f"{y}-{month_map[qn]}"
def build_market_cap_map(stock_market_data: List[Dict]) -> Dict[str, float]:
    mp = {}
    if not isinstance(stock_market_data, list):
        return mp
    for item in stock_market_data:
        ym = ym_from_date_str(item.get('date', ''))
        sh = to_num(item.get('market_cap_shanghai', 0))
        sz = to_num(item.get('market_cap_shenzhen', 0))
        sh_v = not (isnan(sh) or sh == float('inf') or sh == float('-inf'))
        sz_v = not (isnan(sz) or sz == float('inf') or sz == float('-inf'))
        if ym and sh_v and sz_v:
            mp[ym] = sh + sz
    return mp
def get_nearest_cap(market_map: Dict[str, float], target_ym: str) -> Optional[float]:
    if target_ym in market_map:
        return market_map[target_ym]
    ty, tm = target_ym.split('-')
    tm_i = int(tm)
    best_cap = None
    best_m = -1
    for k, cap in market_map.items():
        y, m = k.split('-')
        if y == ty:
            mi = int(m)
            if mi <= tm_i and mi > best_m:
                best_m = mi
                best_cap = cap
    return best_cap
def parse_coverage(label: str) -> Optional[Dict[str, Any]]:
    import re
    y_m = re.search(r'(\d{4})', str(label))
    if not y_m:
        return None
    y = y_m.group(1)
    cov = None
    if '第1季度' in label:
        cov = 1
    else:
        m = re.search(r'第1-(\d)季度', str(label))
        if m:
            cov = int(m.group(1))
        else:
            m2 = re.search(r'第1-([一二三四])季度', str(label))
            mp = {'一': 1, '二': 2, '三': 3, '四': 4}
            if m2 and m2.group(1) in mp:
                cov = mp[m2.group(1)]
    return {'year': y, 'coverage': cov} if cov is not None else None
def build_buffet_data(gdp_data: List[Dict], stock_market_data: List[Dict]) -> List[Dict]:
    if not isinstance(gdp_data, list) or not isinstance(stock_market_data, list):
        return []
    market_map = build_market_cap_map(stock_market_data)
    year_cum = {}
    for item in gdp_data:
        label = item.get('quarter', '')
        info = parse_coverage(label)
        if not info:
            continue
        gdp_cum = to_num(item.get('gdp_abs', 0))
        gdp_v = not (isnan(gdp_cum) or gdp_cum == float('inf') or gdp_cum == float('-inf'))
        if not gdp_v:
            continue
        y = info['year']
        cov = info['coverage']
        if y not in year_cum:
            year_cum[y] = {}
        year_cum[y][cov] = gdp_cum
    results = []
    for y, m in year_cum.items():
        q1 = m.get(1)
        q2 = (m.get(2) - m.get(1)) if (m.get(2) is not None and m.get(1) is not None) else None
        q3 = (m.get(3) - m.get(2)) if (m.get(3) is not None and m.get(2) is not None) else None
        q4 = (m.get(4) - m.get(3)) if (m.get(4) is not None and m.get(3) is not None) else None
        quarters = [q1, q2, q3, q4]
        for idx, val in enumerate(quarters):
            qn = idx + 1
            if not isinstance(val, (int, float)):
                continue
            if isnan(val) or val == float('inf') or val == float('-inf') or val <= 0:
                continue
            label = f"{y}年第{qn}季度"
            ym = quarter_to_ym(label)
            cap = get_nearest_cap(market_map, ym) if ym else None
            if isinstance(cap, (int, float)):
                cap_v = not (isnan(cap) or cap == float('inf') or cap == float('-inf'))
                if cap_v:
                    results.append({'date': label, 'ratio': cap / val})
    def sort_key(it):
        import re
        m = re.match(r'(\d{4}).*?第(\d)季度', str(it.get('date', '')))
        if m:
            return (int(m.group(1)), int(m.group(2)))
        return (0, 0)
    results.sort(key=sort_key)
    return results
