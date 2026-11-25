"""Quarter-end market caps (data/mcq.json) from quarter-end adjusted closes x share counts at that date.
Share counts come from Yahoo (cache/shares via scripts/fetch_shares_hist.py), adjusted for splits (cache/prices events)
so they match split-adjusted prices, interpolated between reported dates, and calibrated so the latest point
matches today's market cap where the share class differs (ADRs, dual classes)."""
import json, pathlib, bisect, datetime as dt
root = pathlib.Path(__file__).resolve().parents[1]
PQ = json.load(open(root / "data/priceq-baked.json")); Q = PQ["quarters"]
D = {r["ticker"]: r for r in json.load(open(root / "data/data.json"))}
D.update({r["ticker"]: r for r in json.load(open(root / "data/parked-data.json"))["rows"] if r["ticker"] not in D})
import re as _re
_snap = (root / "biotech_idea_snapshot.html").read_text(encoding="utf-8")
SEP = {x["ticker"]: x for x in json.loads(_re.search(r"const SIMPLE_ROWS=(\[.*?\]);\s*\n", _snap, _re.S).group(1))}  # Sep 12 2026 point-in-time caps
TYPES = ["quarterlyOrdinarySharesNumber", "annualOrdinarySharesNumber", "quarterlyShareIssued", "annualShareIssued",
         "quarterlyDilutedAverageShares", "annualDilutedAverageShares"]
def qend(l): q, y = int(l[0]), 2000 + int(l[2:]); return dt.date(y, 3 * q, [31, 30, 30, 31][q - 1])
def close_on(t, d):
    f = root / "cache/prices" / f"{t}.json"
    try:
        j = json.load(open(f))["chart"]["result"][0]; ts = j["timestamp"]; ind = j["indicators"]
    except Exception: return None
    c = (ind.get("adjclose") or [{}])[0].get("adjclose") or ind["quote"][0]["close"]
    best = None
    for a, b in zip(ts, c):
        if b and dt.datetime.fromtimestamp(a, dt.UTC).date() <= d: best = b
    return best
SNAP_D = dt.date(2026, 9, 11)   # last close before the Sep 12 2026 snapshot
def splits(t):
    f = root / "cache/prices" / f"{t}.json"
    try: ev = json.load(open(f))["chart"]["result"][0].get("events", {}).get("splits", {})
    except Exception: return []
    return [(dt.datetime.fromtimestamp(v["date"], dt.UTC).date(), v["numerator"] / v["denominator"]) for v in ev.values()]
i0 = Q.index("4Q24"); out = {}; stats = {"ok": 0, "calibrated": 0, "none": 0}
for t, row in PQ["prices"].items():
    f = root / "cache/shares" / f"{t}.json"
    if not f.exists(): stats["none"] += 1; continue
    d = json.loads(f.read_text()); pts = {}
    for ty in TYPES:
        for k, v in (d.get(ty) or {}).items():
            if v and k not in pts: pts[k] = v
    if not pts: stats["none"] += 1; continue
    SP = splits(t)
    def variant(apply):
        a = {}
        for k, v in pts.items():
            kd = dt.date.fromisoformat(k); fct = 1.0
            if apply:
                for sd, r in SP:
                    if kd < sd: fct *= r      # reported before the split -> express in post-split shares
            a[kd] = v * fct
        return a
    r0 = D.get(t) or {}
    def err(a):   # how far the latest point is from today's market cap (Yahoo sometimes restates for splits already)
        k = max(a); est = (row[-1] or 0) * a[k]
        return abs(__import__("math").log(r0["mc"] / est)) if r0.get("mc") and est else 0
    adj = variant(True) if SP and err(variant(True)) <= err(variant(False)) else variant(False)
    ks = sorted(adj)
    def sh(e):
        if e <= ks[0]: return adj[ks[0]], ks[0] != e
        if e >= ks[-1]: return adj[ks[-1]], False
        j = bisect.bisect_right(ks, e); a, b = ks[j - 1], ks[j]
        if a == e: return adj[a], False
        return adj[a] + (adj[b] - adj[a]) * (e - a).days / max(1, (b - a).days), True
    r = D.get(t) or {}; cal = 1.0
    # calibrate the share class/split basis on a real point-in-time cap: the Sep 12 2026 snapshot, else today's cap
    q3 = Q.index("3Q26"); sp = SEP.get(t)
    px_s = close_on(t, SNAP_D) if sp and sp.get("mc") else None
    if px_s:
        est = px_s * sh(SNAP_D)[0]; ratio = sp["mc"] / est if est else 1
    elif r.get("mc") and row[-1]:
        est = row[-1] * adj[ks[-1]]; ratio = r["mc"] / est if est else 1
    else: ratio = 1
    if ratio > 1.6 or ratio < 0.625: cal = ratio; stats["calibrated"] += 1
    mc, shs, interp = [], [], []
    for i in range(len(Q)):
        if i < i0 or not row[i]: mc.append(None); shs.append(None); interp.append(0); continue
        s, it = sh(qend(Q[i])); s *= cal; m = row[i] * s; flag = 1 if it else 0
        if row[-1]:   # sanity: never more than 5x away from the price-scaled estimate (from the latest calibrated cap)
            est = row[-1] * adj[ks[-1]] * cal * row[i] / row[-1]
            if est and (m / est > 5 or m / est < 0.2): m, s, flag = est, est / row[i], 2
        mc.append(round(m)); shs.append(round(s)); interp.append(flag)
    out[t] = {"mc": mc, "sh": shs, "i": interp}; stats["ok"] += 1
json.dump({"quarters": Q, "from": Q[i0], "rows": out, "method": __doc__.strip()}, open(root / "data/mcq.json", "w"), separators=(",", ":"))
print(stats)
