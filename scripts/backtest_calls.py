"""Backtest of our calls from the Sep 11 2026 snapshot (the oldest frozen call set) to the latest close -> data/backtest.json.
For each call bucket: equal-weight return and return vs XBI at every trading day since, hit rate (beat XBI), median, the
spread of outcomes, and the share of names down 30%+ (a buy can fall for non-fundamental reasons before it works, so a
short window can mislabel a good call). Also by our Sep upside (quintiles) and by the Sep starred picks.
Only ~2.5 months of history: read it as a check on direction, not proof."""
import json, re, pathlib, datetime as dt, bisect, statistics as st
root = pathlib.Path(__file__).resolve().parents[1]
s = (root / "biotech_idea_snapshot.html").read_text(encoding="utf-8")
R = json.loads(re.search(r"const SIMPLE_ROWS=(\[.*?\]);\s*\n", s, re.S).group(1))
D0 = dt.date(2026, 9, 11)
def series(t):
    f = root / f"cache/prices/{t}.json"
    try:
        j = json.load(open(f))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
        adj = (j["indicators"].get("adjclose") or [{}])[0].get("adjclose") or q["close"]
        return [(dt.datetime.fromtimestamp(ts, dt.timezone.utc).date(), c) for ts, c in zip(j["timestamp"], adj) if c]
    except Exception: return None
X = series("XBI"); days = [d for d, c in X if d >= D0]
def path(S):
    ds = [d for d, c in S]; i0 = bisect.bisect_right(ds, D0) - 1
    if i0 < 0: return None
    p0 = S[i0][1]; out = []
    for d in days:
        i = bisect.bisect_right(ds, d) - 1
        out.append(S[i][1] / p0 - 1)
    return out
xp = path(X)
BUCK = {"STRONG BUY": "Strong buy", "LONG": "Long", "WATCH": "Watch / hold", "HOLD": "Watch / hold", "AVOID": "Avoid", "SHORT": "Short", "STRONG SHORT": "Strong short"}
rows = []
for r in R:
    S = series(r["ticker"])
    if not S: continue
    p = path(S)
    if not p: continue
    rows.append({"t": r["ticker"], "call": r["call"], "b": BUCK.get(r["call"], r["call"]), "up": r.get("up"), "star": bool(r.get("starred") or r.get("favorite")), "p": p})
UNI = None
def agg(L, name, side):
    if not L: return None
    n = len(days); ew = [st.mean(x["p"][i] for x in L) for i in range(n)]
    uni = UNI or [0] * n
    fin = [x["p"][-1] for x in L]; ex = [f - xp[-1] for f in fin]
    eu = [f - uni[-1] for f in fin]; good = [e > 0 for e in eu] if side >= 0 else [e < 0 for e in eu]
    return {"name": name, "n": len(L), "side": side, "path": [round(v - xp[i], 4) for i, v in enumerate(ew)], "ret": round(st.mean(fin), 4), "vs_xbi": round(st.mean(ex), 4), "vs_uni": round(st.mean(fin) - uni[-1], 4), "upath": [round(v - uni[i], 4) for i, v in enumerate(ew)],
            "median_vs": round(st.median(ex), 4), "hit": round(sum(good) / len(good), 3), "down30": round(sum(1 for f in fin if f <= -.3) / len(fin), 3),
            "up50": round(sum(1 for f in fin if f >= .5) / len(fin), 3), "p10": round(sorted(ex)[len(ex) // 10], 4), "p90": round(sorted(ex)[len(ex) * 9 // 10], 4),
            "best": sorted(((x["t"], round(x["p"][-1], 3)) for x in L), key=lambda z: -z[1])[:3], "worst": sorted(((x["t"], round(x["p"][-1], 3)) for x in L), key=lambda z: z[1])[:3],
            "m1": round(st.mean(x["p"][min(20, n - 1)] for x in L) - xp[min(20, n - 1)], 4), "m2": round(st.mean(x["p"][min(41, n - 1)] for x in L) - xp[min(41, n - 1)], 4)}
UNI = [st.mean(x["p"][i] for x in rows) for i in range(len(days))]
side = {"Strong buy": 1, "Long": 1, "Watch / hold": 0, "Avoid": -1, "Short": -1, "Strong short": -1}
G = [agg([x for x in rows if x["b"] == b], b, side[b]) for b in ["Strong buy", "Long", "Watch / hold", "Avoid", "Short", "Strong short"]]
U = sorted([x for x in rows if x["up"] is not None], key=lambda x: x["up"]); q = len(U) // 5
Q = [agg(U[i * q:(i + 1) * q if i < 4 else len(U)], f"Upside quintile {i + 1} ({'lowest' if i == 0 else 'highest' if i == 4 else ''})".replace(" ()", ""), 1 if i >= 3 else -1 if i <= 1 else 0) for i in range(5)]
S_ = [agg([x for x in rows if x["star"]], "Starred picks", 1)]
out = {"from": D0.isoformat(), "to": days[-1].isoformat(), "days": [d.isoformat() for d in days], "xbi": round(xp[-1], 4), "uni": round(UNI[-1], 4), "n": len(rows),
       "calls": [g for g in G if g], "upside": [g for g in Q if g], "starred": [g for g in S_ if g]}
json.dump(out, open(root / "data/backtest.json", "w"), separators=(",", ":"))
print("from", D0, "to", days[-1], "names", len(rows), "XBI", round(xp[-1] * 100, 1), "% ; average covered stock", round(UNI[-1] * 100, 1), "%")
for g in out["calls"] + out["upside"] + out["starred"]:
    print(f"  {g['name']:28s} n={g['n']:3d} vs avg stock {g['vs_uni']*100:+6.1f}% | vs XBI {g['vs_xbi']*100:+6.1f}% (median {g['median_vs']*100:+6.1f}%) hit {g['hit']*100:3.0f}%  1m {g['m1']*100:+5.1f}% 2m {g['m2']*100:+5.1f}%  down30 {g['down30']*100:3.0f}% up50 {g['up50']*100:3.0f}%")
