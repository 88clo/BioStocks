"""Rebuild data/priceq-baked.json (quarter-end closes) from the daily split/dividend-adjusted Yahoo cache (cache/prices).
The old file was only ever gap-filled, so early values were not split-adjusted and some sat a quarter off.
Quarters covered by the daily cache are overwritten with the last adjusted close on or before quarter-end
(the current quarter = last close). Older quarters are kept but rescaled to splice at the first covered quarter."""
import json, pathlib, datetime as dt
root = pathlib.Path(__file__).resolve().parents[1]
PQ = json.load(open(root / "data/priceq-baked.json")); Q = PQ["quarters"]
def qend(l): q, y = int(l[0]), 2000 + int(l[2:]); return dt.date(y, 3 * q, [31, 30, 30, 31][q - 1])
def daily(t):
    f = root / "cache/prices" / f"{t}.json"
    if not f.exists(): return None
    try:
        j = json.load(open(f))["chart"]["result"][0]; ts = j["timestamp"]; ind = j["indicators"]
    except Exception: return None
    c = (ind.get("adjclose") or [{}])[0].get("adjclose") or ind["quote"][0]["close"]
    return [(dt.datetime.fromtimestamp(a, dt.UTC).date(), b) for a, b in zip(ts, c) if b]
n_upd = n_tk = 0
for t, row in PQ["prices"].items():
    S = daily(t)
    if not S: continue
    first = S[0][0]; new = list(row) + [None] * (len(Q) - len(row)); k0 = None
    for i, l in enumerate(Q):
        e = qend(l)
        if e < first: continue
        v = [b for a, b in S if a <= e]
        if v:
            new[i] = round(v[-1], 4); n_upd += 1
            if k0 is None: k0 = i
    if k0 is not None and k0 > 0:   # splice older values onto the adjusted series
        old0 = row[k0] if k0 < len(row) else None
        if old0 and new[k0]:
            f = new[k0] / old0
            for i in range(k0): new[i] = round(row[i] * f, 4) if row[i] else None
    PQ["prices"][t] = new; n_tk += 1
PQ["method"] = "Quarter-end adjusted closes from daily Yahoo data (scripts/rebuild_priceq.py); current quarter = last close."
json.dump(PQ, open(root / "data/priceq-baked.json", "w"), separators=(",", ":"))
print("rebuilt", n_tk, "tickers,", n_upd, "quarter values")
