"""Flag stocks that moved sharply since our data snapshot (the KYMR lesson: a readout 3 days after the snapshot sat unnoticed).
For every covered ticker, fetch the last month of daily closes (Yahoo chart endpoint), compare the latest close with the
price in data/data.json, and record the largest one-day move since then. Writes data/moves.json; the Brief lists names
that beat or lagged XBI by >= 15% (or had a single day >= 15% beyond XBI's) as 'Check before trading: moved since our last review'.
Run daily (or before any meeting): python3 scripts/moves_since.py ; python3 scripts/build.py"""
import json, pathlib, time, urllib.request, concurrent.futures as cf, datetime as dt
root = pathlib.Path(__file__).resolve().parents[1]
D = [r for r in json.load(open(root / "data/data.json")) if r.get("ta") != "Acquired / Inactive" and r.get("price")]
def get(r):
    t = r["ticker"]; url = f"https://query1.finance.yahoo.com/v8/finance/chart/{t.replace('.', '-')}?range=1mo&interval=1d"
    for a in range(3):
        try:
            j = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read())
            res = j["chart"]["result"][0]; ts = res["timestamp"]; cl = res["indicators"]["quote"][0]["close"]
            pts = [(dt.datetime.fromtimestamp(a, dt.UTC).date().isoformat(), c) for a, c in zip(ts, cl) if c]
            return t, pts
        except Exception:
            time.sleep(1 + a)
    return t, None
snap = json.load(open(root / "data/asof-baked.json")) if (root / "data/asof-baked.json").exists() else {}
asof = "2026-11-20"
_, XB = get({'ticker': 'XBI'})
xb_after = {d: c for d, c in XB if d > asof}; xb_base = [c for d, c in XB if d <= asof][-1]; xb_last = XB[-1][1]
xb_day = {}
prevc = xb_base
for d, c in sorted(xb_after.items()): xb_day[d] = c / prevc - 1; prevc = c
xbi = xb_last / xb_base - 1
out = {}
with cf.ThreadPoolExecutor(8) as ex:
    for t, pts in ex.map(get, D):
        if not pts: continue
        r = next(x for x in D if x["ticker"] == t); p0 = r["price"]
        # moves are measured against XBI over the same days, so a sector rally does not flag every name
        # the snapshot price is the close on (or the last close before) the as-of date; patches may have refreshed it since
        last_d, last = pts[-1]
        after = [(d, c) for d, c in pts if d > asof]
        prev = [c for d, c in pts if d <= asof]
        base = prev[-1] if prev else p0
        seq = [base] + [c for d, c in after]
        day = max((abs(b / a - 1 - xb_day.get(d, 0)), d) for (a, b, d) in zip(seq, seq[1:], [d for d, c in after])) if len(seq) > 1 else (0, None)
        out[t] = {"p0": round(p0, 4), "base": round(base, 4), "last": round(last, 4), "last_d": last_d,
                  "chg": round(last / base - 1, 4), "xs": round(last / base - 1 - xbi, 4), "vs_data": round(last / p0 - 1, 4), "max_day": round(day[0], 4), "max_day_d": day[1]}
json.dump({"asof": asof, "xbi": round(xbi, 4), "built": dt.date.today().isoformat(), "moves": out}, open(root / "data/moves.json", "w"), separators=(",", ":"))
big = sorted([(t, m) for t, m in out.items() if abs(m["xs"]) >= .15 or m["max_day"] >= .15], key=lambda x: -abs(x[1]["xs"]))
print("XBI since", asof, f"{xbi*100:+.1f}%")
print(len(out), "tickers;", len(big), "moved >=15% (or a 12% day) since", asof)
for t, m in big[:30]: print(f"  {t:6s} {m['chg']*100:+6.1f}% (vs XBI {m['xs']*100:+6.1f}%)  max day {m['max_day']*100:4.1f}% on {m['max_day_d']}")
