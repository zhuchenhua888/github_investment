from typing import List, Dict

def _to_float(v):
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None

def build_margin_account_info_data(margin_rows: List[Dict], hushen300_rows: List[Dict]) -> Dict[str, List]:
    if not isinstance(margin_rows, list):
        return {"categories": [], "leftSeries": [], "rightSeries": []}

    hs_map: Dict[str, float] = {}
    for item in (hushen300_rows or []):
        d = item.get('date') or item.get('tradeDate')
        close = _to_float(item.get('close'))
        if isinstance(d, str) and close is not None:
            hs_map[d] = close

    categories: List[str] = []
    left_series: List[float] = []
    right_series: List[float] = []

    for row in margin_rows:
        d = row.get('date')
        if not isinstance(d, str) or not d:
            continue
        fin = _to_float(row.get('fin_balance'))
        loan = _to_float(row.get('loan_balance'))
        minus = None
        if fin is not None and loan is not None:
            minus = fin - loan

        categories.append(d)
        left_series.append(minus if minus is not None else None)
        right_series.append(hs_map.get(d))

    return {"categories": categories, "leftSeries": left_series, "rightSeries": right_series}
