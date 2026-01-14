from typing import List, Dict
def build_cpi_data(rows: List[Dict]) -> List[Dict]:
    if not isinstance(rows, list):
        return []
    out: List[Dict] = []
    for it in rows:
        month = it.get('month')
        yoy = it.get('national_yoy')
        if isinstance(month, str) and isinstance(yoy, (int, float)):
            out.append({'month': month, 'national_yoy': yoy})
    out.sort(key=lambda x: x['month'])
    return out
def build_ppi_data(rows: List[Dict]) -> List[Dict]:
    if not isinstance(rows, list):
        return []
    out: List[Dict] = []
    for it in rows:
        month = it.get('month')
        yoy = it.get('yoy')
        if isinstance(month, str) and isinstance(yoy, (int, float)):
            out.append({'month': month, 'yoy': yoy})
    out.sort(key=lambda x: x['month'])
    return out
