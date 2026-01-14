from typing import List, Dict, Optional
from math import isnan
def _norm_date(s: Optional[str]) -> Optional[str]:
    if not isinstance(s, str):
        return None
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    import re
    m = re.match(r"(\d{4})[-/](\d{2})[-/](\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None
def calculate_fed_premium_both(hushen300_data: List[Dict], bond_yield_data: List[Dict]):
    if not isinstance(hushen300_data, list) or not isinstance(bond_yield_data, list):
        return {'ratio': None, 'diff': None}
    date_map: Dict[str, float] = {}
    peg_map: Dict[str, float] = {}
    for it in hushen300_data:
        d = _norm_date(it.get('date') or it.get('tradeDate'))
        close = it.get('close')
        peg = it.get('peg') or it.get('pe')
        if d and isinstance(close, (int, float)) and isinstance(peg, (int, float)) and close > 0 and peg > 0:
            date_map[d] = float(close)
            peg_map[d] = float(peg)
    by_map: Dict[str, float] = {}
    dates_ts: List[Dict] = []
    import datetime
    for it in bond_yield_data:
        d = _norm_date(it.get('date') or it.get('workTime') or it.get('tradeDate'))
        y = it.get('yield') or it.get('tenYear') or it.get('10年')
        try:
            yv = float(y) if y is not None else None
        except Exception:
            yv = None
        if d and isinstance(yv, (int, float)):
            by_map[d] = yv
            try:
                ts = datetime.datetime.strptime(d, '%Y-%m-%d').timestamp()
                dates_ts.append({'s': d, 't': ts})
            except Exception:
                pass
    dates_ts.sort(key=lambda x: x['t'])
    def nearest_bond(d: str) -> Optional[float]:
        import datetime
        try:
            tgt = datetime.datetime.strptime(d, '%Y-%m-%d').timestamp()
        except Exception:
            return None
        lo, hi = 0, len(dates_ts) - 1
        idx = -1
        while lo <= hi:
            mid = (lo + hi) >> 1
            if dates_ts[mid]['t'] <= tgt:
                idx = mid
                lo = mid + 1
            else:
                hi = mid - 1
        if idx == -1:
            return None
        cand = dates_ts[idx]
        if tgt - cand['t'] <= 5 * 24 * 60 * 60:
            return by_map.get(cand['s'])
        return None
    merged: List[Dict] = []
    for d, close in date_map.items():
        peg = peg_map.get(d)
        by = by_map.get(d)
        if by is None:
            by = nearest_bond(d)
        if by is None:
            continue
        if any([isnan(close), isnan(peg), isnan(by)]):
            continue
        if peg <= 0 or by <= 0:
            continue
        ey = 1.0 / peg
        by_dec = by / 100.0
        ratio = ey / by_dec - 1.0
        diff = ey - by_dec
        merged.append({'date': d, 'close': close, 'bondYield': by, 'peg': peg, 'fedPremium': round(ratio, 2), 'riskPremium': round(diff, 4)})
    if not merged:
        return {'ratio': None, 'diff': None}
    rvals = [x['fedPremium'] for x in merged]
    rmean = sum(rvals) / len(rvals)
    rvar = sum((v - rmean) ** 2 for v in rvals) / len(rvals)
    import math
    rstd = math.sqrt(rvar)
    dvals = [x['riskPremium'] for x in merged]
    dmean = sum(dvals) / len(dvals)
    dvar = sum((v - dmean) ** 2 for v in dvals) / len(dvals)
    dstd = math.sqrt(dvar)
    return {
        'ratio': {'data': [{'date': x['date'], 'close': x['close'], 'bondYield': x['bondYield'], 'peg': x['peg'], 'fedPremium': x['fedPremium']} for x in merged], 'mean': rmean, 'std': rstd},
        'diff': {'data': [{'date': x['date'], 'close': x['close'], 'bondYield': x['bondYield'], 'peg': x['peg'], 'riskPremium': x['riskPremium']} for x in merged], 'mean': dmean, 'std': dstd}
    }
