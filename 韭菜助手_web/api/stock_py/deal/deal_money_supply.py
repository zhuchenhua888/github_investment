from typing import List, Dict
def build_money_supply_data(rows: List[Dict]) -> List[Dict]:
    if not isinstance(rows, list):
        return []
    out: List[Dict] = []
    for it in rows:
        month = it.get('month')
        m1 = it.get('m1_yoy')
        m2 = it.get('m2_yoy')
        if isinstance(month, str) and isinstance(m1, (int, float)) and isinstance(m2, (int, float)):
            diff = m1 - m2
            out.append({'month': month, 'm1_yoy': m1, 'm2_yoy': m2, 'diff': diff})
    out.sort(key=lambda x: x['month'])
    return out
