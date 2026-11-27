"""Price sanity check against an independent source (Nov 26 2026). Cboe quotes are blocked to automated requests, so:
(1) quarter-end check: SEC's bulk 13F data gives value and share count for every holding at Jun 30 2026; the median
    value/shares across filers is an independent Jun 30 price. Compared with our cached close for Jun 30 (a gap usually
    means a split or reverse split since, a ticker mapped to the wrong company, or a bad price series);
(2) staleness: the last date in each cached price series vs the newest date across all series;
(3) consistency: the price in data.json vs the last cached close.
Writes data/price-check.json."""
import csv, json, pathlib, statistics, datetime as dt, collections
root = pathlib.Path(__file__).resolve().parents[1]; csv.field_size_limit(10**9)
D = json.load(open(root / "data/data.json")); cov = {r["ticker"]: r for r in D if r.get("ta") != "Acquired / Inactive"}
cmap = json.load(open(root / "cache/13f/cusip_map.json"))
B = root / "cache/13f_bulk/q2"
acc = {r["ACCESSION_NUMBER"] for r in csv.DictReader(open(B / "SUBMISSION.tsv"), delimiter="\t") if r["PERIODOFREPORT"] == "30-JUN-2026"}
px = collections.defaultdict(list)
with open(B / "INFOTABLE.tsv") as fh:
    rd = csv.reader(fh, delimiter="\t"); ix = {h: i for i, h in enumerate(next(rd))}
    for row in rd:
        if row[ix["ACCESSION_NUMBER"]] not in acc or row[ix["PUTCALL"]] or row[ix["SSHPRNAMTTYPE"]] != "SH": continue
        t = cmap.get(row[ix["CUSIP"]].upper())
        if t not in cov: continue
        try:
            v, sh = float(row[ix["VALUE"]]), float(row[ix["SSHPRNAMT"]])
            if sh > 0 and v > 0: px[t].append(v / sh)
        except ValueError: pass
def series(t):
    f = root / f"cache/prices/{t}.json"
    if not f.exists(): return None
    try: j = json.load(open(f))["chart"]["result"][0]
    except Exception: return None
    return [(dt.datetime.fromtimestamp(ts, dt.timezone.utc).date(), c) for ts, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c]
S = {t: series(t) for t in cov}
newest = max(s[-1][0] for s in S.values() if s)
out = []
for t, r in cov.items():
    s = S.get(t); o = {"t": t}
    if not s: o["flag"] = "no price series"; out.append(o); continue
    o["last_date"] = s[-1][0].isoformat(); o["last"] = s[-1][1]
    if (newest - s[-1][0]).days > 4: o["flag"] = f"stale: last close {s[-1][0]}"
    if r.get("price") and abs(r["price"] / s[-1][1] - 1) > .15: o.setdefault("flag", f"data.json price {r['price']:.2f} vs last close {s[-1][1]:.2f}")
    if len(px.get(t, [])) >= 3:
        m = statistics.median(px[t]); c = [c for d, c in s if d <= dt.date(2026, 6, 30)]
        if c:
            o["jun30_13f"], o["jun30_ours"] = round(m, 3), round(c[-1], 3)
            g = c[-1] / m - 1
            if abs(g) > .10: o.setdefault("flag", f"Jun 30 close {c[-1]:.2f} vs 13F-implied {m:.2f} ({g:+.0%}): split since, wrong mapping or bad series")
    out.append(o)
json.dump({"newest": newest.isoformat(), "rows": out}, open(root / "data/price-check.json", "w"), indent=0)
fl = [o for o in out if o.get("flag")]
print(len(out), "names; newest close", newest, ";", sum(1 for o in out if "jun30_13f" in o), "checked against 13F;", len(fl), "flagged")
for o in fl: print("  ", o["t"], "-", o["flag"])
