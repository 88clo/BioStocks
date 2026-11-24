"""Point-in-time catalyst log: freeze every company's catalyst schedule as it stands on a date.

Writes ledger/catalysts_<YYYY-MM-DD>.json = {asof, rows: {ticker: [{lab, s, d, e, k, st}]}}.
Run at every refresh (after normalize_catalysts.py). The track record can then ask, for any big move,
"was this event on our calendar beforehand, and with what date?" instead of reconstructing it later.
Usage: python3 scripts/log_catalysts.py [YYYY-MM-DD]
"""
import json, sys, datetime as dt, os

asof = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
D = json.load(open('data/data.json'))
rows = {}
for r in D:
    ev = [{k: c.get(k) for k in ('lab', 's', 'd', 'e', 'k', 'st') if c.get(k) is not None} for c in (r.get('cat_sched') or [])]
    if ev:
        rows[r['ticker']] = ev
os.makedirs('ledger', exist_ok=True)
out = f'ledger/catalysts_{asof}.json'
json.dump({'asof': asof, 'rows': rows}, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print('wrote', out, '·', len(rows), 'companies ·', sum(len(v) for v in rows.values()), 'events')
