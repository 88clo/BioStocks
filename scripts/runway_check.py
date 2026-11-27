"""Recompute cash and burn from SEC XBRL filings (10-Q / 10-K) for names with under 10 quarters of runway.
burn = −(operating cash flow) per quarter, averaged over the last two reported quarters (quarterly values are derived from
the year-to-date figures companies report). Cash = cash & equivalents + short-term / current marketable securities at the
latest balance-sheet date. Writes data/runway-check.json; does not change data.json (apply fixes with a dated patch).
Operating cash flow is used instead of net loss because net loss swings with non-cash items (warrant and derivative
revaluation, impairments, stock comp)."""
import json, time, pathlib, urllib.request, datetime as dt, sys
root = pathlib.Path(__file__).resolve().parents[1]
UA = {"User-Agent": "BioStocks research dashboard (88clo) contact@example.com"}
D = json.load(open(root / "data/data.json"))
CIK = {v["ticker"]: v["cik_str"] for v in json.load(open(root / "cache/13dg/company_tickers.json")).values()}
cache = root / "cache/xbrl"; cache.mkdir(exist_ok=True)
def facts(cik):
    f = cache / f"{cik}.json"
    if f.exists() and time.time() - f.stat().st_mtime < 86400 * 5: return json.load(open(f))
    for k in range(3):
        try:
            time.sleep(0.12)
            s = urllib.request.urlopen(urllib.request.Request(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", headers=UA), timeout=40).read()
            f.write_bytes(s); return json.loads(s)
        except Exception as e:
            if "404" in str(e): return None
            time.sleep(2)
    return None
def series(fx, tags):
    for t in tags:
        for ns in ("us-gaap", "ifrs-full"):
            u = fx.get("facts", {}).get(ns, {}).get(t, {}).get("units", {})
            v = u.get("USD")
            if v: return v
    return []
def latest_instant(fx, tags):
    best = {}
    for t in tags:
        for x in series(fx, [t]):
            if x.get("form", "").startswith(("10-Q", "10-K", "20-F", "6-K")) and "end" in x:
                best.setdefault(x["end"], {})[t] = x["val"]
    if not best: return None, None
    end = max(best); return end, best[end]
def quarterly_ocf(fx):
    v = [x for x in series(fx, ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations", "CashFlowsFromUsedInOperatingActivities"]) if "start" in x and x.get("form", "").startswith(("10-Q", "10-K", "20-F"))]
    # keep one value per (start, end)
    d = {}
    for x in v: d[(x["start"], x["end"])] = x["val"]
    # build quarterly values: a 3-month span directly, else YTD(end) − YTD(previous end, same start)
    q = {}
    for (s, e), val in d.items():
        days = (dt.date.fromisoformat(e) - dt.date.fromisoformat(s)).days
        if 80 <= days <= 100: q[e] = val
    for (s, e), val in d.items():
        days = (dt.date.fromisoformat(e) - dt.date.fromisoformat(s)).days
        if days > 100 and e not in q:
            prev = [(e2, v2) for (s2, e2), v2 in d.items() if s2 == s and e2 < e and 80 <= (dt.date.fromisoformat(e) - dt.date.fromisoformat(e2)).days <= 100]
            if prev: q[e] = val - prev[0][1]
    return sorted(q.items())
out = []
todo = [r for r in D if r.get("ta") != "Acquired / Inactive" and r.get("runway_q") is not None and r["runway_q"] < 10]
print(len(todo), "names under 10 quarters")
for r in todo:
    t = r["ticker"]; cik = CIK.get(t)
    if not cik: out.append({"t": t, "err": "no CIK"}); continue
    fx = facts(cik)
    if not fx: out.append({"t": t, "err": "no XBRL facts (foreign filer or new listing)"}); continue
    end, cv = latest_instant(fx, ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "Cash", "ShortTermInvestments", "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesDebtSecuritiesCurrent", "CashAndCashEquivalents"])
    cash = None
    if cv:
        c0 = cv.get("CashAndCashEquivalentsAtCarryingValue") or cv.get("CashAndCashEquivalents") or cv.get("Cash") or cv.get("CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents") or 0
        cash = c0 + (cv.get("ShortTermInvestments") or cv.get("MarketableSecuritiesCurrent") or cv.get("AvailableForSaleSecuritiesDebtSecuritiesCurrent") or 0)
    q = quarterly_ocf(fx)
    last2 = [v for e, v in q[-2:]]
    burn = -sum(last2) / len(last2) if last2 else None
    rw = (cash / burn) if (cash and burn and burn > 0) else (99 if burn is not None and burn <= 0 else None)
    out.append({"t": t, "end": end, "cash": cash, "burn": burn, "rw": rw, "q_end": q[-1][0] if q else None,
                "ours_cash": r.get("cash"), "ours_rw": r.get("runway_q")})
json.dump(out, open(root / "data/runway-check.json", "w"), indent=0)
big = [o for o in out if o.get("rw") is not None and o.get("ours_rw") is not None and (abs(min(o["rw"], 40) - o["ours_rw"]) >= max(2, .4 * o["ours_rw"]))]
print(len(out), "checked;", sum(1 for o in out if o.get("err")), "without XBRL;", len(big), "differ by ≥2 quarters and ≥40%")
for o in sorted(big, key=lambda o: o["ours_rw"]):
    print(f"  {o['t']:6} ours {o['ours_rw']:.1f}q cash {(o['ours_cash'] or 0)/1e6:.0f}M | 10-Q {o['end']}: cash {(o['cash'] or 0)/1e6:.0f}M, burn {(o['burn'] or 0)/1e6:.1f}M/q -> {min(o['rw'],99):.1f}q")
