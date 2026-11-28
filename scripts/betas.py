"""Betas to XBI (Nov 27 2026) -> data/betas.json.
Weekly returns over the last two years (cache/prices, Yahoo daily closes). Raw OLS beta and its standard error per name,
then a Bayesian (Vasicek) estimate that pulls each raw beta toward the cross-sectional average in proportion to its own
estimation error: a noisy beta moves a lot, a precise one barely moves. No fixed haircut. Also idiosyncratic volatility
(annualised residual), R-squared and the number of weeks used. Names with under 26 weeks of history get the prior.
Usage: python3 scripts/betas.py"""
import json, pathlib, datetime as dt, statistics as st, math
root = pathlib.Path(__file__).resolve().parents[1]
def weekly(t):
    try:
        j = json.load(open(root / f"cache/prices/{t}.json"))["chart"]["result"][0]
        px = [(dt.datetime.fromtimestamp(ts, dt.timezone.utc).date(), c) for ts, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c]
    except Exception: return {}
    cut = dt.date.today() - dt.timedelta(days=730); w = {}
    for d, c in px:
        if d >= cut: w[d.isocalendar()[:2]] = c  # last close of each ISO week
    k = sorted(w); return {k[i]: w[k[i]] / w[k[i - 1]] - 1 for i in range(1, len(k))}
X = weekly("XBI")
D = [r for r in json.load(open(root / "data/data.json")) if r.get("ta") != "Acquired / Inactive"]
raw = {}
for r in D:
    y = weekly(r["ticker"]); ks = [k for k in y if k in X and abs(y[k]) < 1.5]
    if len(ks) < 26: continue
    xs = [X[k] for k in ks]; ys = [y[k] for k in ks]; mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((a - mx) ** 2 for a in xs); b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sxx
    res = [c - my - b * (a - mx) for a, c in zip(xs, ys)]; s2 = sum(e * e for e in res) / (len(ks) - 2)
    se = math.sqrt(s2 / sxx); syy = sum((c - my) ** 2 for c in ys)
    raw[r["ticker"]] = {"b": b, "se": se, "idio": math.sqrt(s2 * 52), "r2": 1 - sum(e * e for e in res) / syy if syy else None, "n": len(ks)}
bs = [v["b"] for v in raw.values()]; prior = st.median(bs)
# spread of true betas = observed cross-sectional variance less average sampling variance
var_true = max(0.05, st.pvariance(bs) - st.mean(v["se"] ** 2 for v in raw.values()))
out = {}
for t, v in raw.items():
    w = var_true / (var_true + v["se"] ** 2)
    out[t] = {"beta": round(w * v["b"] + (1 - w) * prior, 3), "raw": round(v["b"], 3), "se": round(v["se"], 3), "idio": round(v["idio"], 3), "r2": round(v["r2"], 3) if v["r2"] is not None else None, "n": v["n"]}
xv = st.pstdev(X.values()) * math.sqrt(52)
json.dump({"built": dt.date.today().isoformat(), "xbi_vol": round(xv, 3), "prior": round(prior, 3), "spread": round(math.sqrt(var_true), 3), "rows": out}, open(root / "data/betas.json", "w"), separators=(",", ":"))
print("betas: %d names; cross-sectional prior %.2f; true-beta spread %.2f" % (len(out), prior, math.sqrt(var_true)))
