"""Trading facts for every covered ticker -> data/tradeinfo.json (Nov 25 2026).

Per ticker, from the daily price cache (cache/prices, refreshed by fetch_prices.py):
  adv20     average daily dollar volume, last 20 sessions
  days10    days to build a $10M position trading 20% of daily volume (10e6 / (0.2 * adv20))
  vol60     annualised realised volatility, last 60 sessions
  bigday    average of the stock's 5 biggest absolute one-day moves vs XBI over the last ~2 years: what news has done
            to this stock. It stands in for the options market's expected move while no options source is reachable.
  bigday_n  sessions used
Options-implied moves: tried from Cboe's delayed quotes (cdn.cboe.com) for the nearest expiry after each company's next
lead-program readout or FDA date; at-the-money straddle / price = the market's expected move. Short interest: tried from
FINRA (cdn.finra.org). Both hosts are blocked by this workspace's network allowlist as of Nov 25 2026; the script records
`options: null` / `short: null` and the page says so, and it will fill them in once the hosts are allowed."""
import json, pathlib, datetime as dt, statistics as st, urllib.request
root = pathlib.Path(__file__).resolve().parents[1]
def series(tk):
    f = root / "cache/prices" / f"{tk}.json"
    if not f.exists(): return None
    j = json.load(open(f))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    out = []
    for t, c, v in zip(j.get("timestamp") or [], q.get("close") or [], q.get("volume") or []):
        if c: out.append((dt.datetime.fromtimestamp(t, dt.timezone.utc).date(), c, v or 0))
    return out
XB = {d: c for d, c, v in (series("XBI") or [])}
def reach(url):
    try:
        urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=8).read(200); return True
    except Exception:
        return False
CBOE = reach("https://cdn-api.cboe.com/api/global/delayed_quotes/options/XBI.json")  # cdn.cboe.com 307-redirects here
# FINRA Reg SHO daily short-sale volume (consolidated NMS file): share of each day's volume that was sold short. This is
# NOT short interest (open short positions): FINRA's short-interest files on cdn.finra.org return Access Denied, and exchange
# short interest is published via Nasdaq/NYSE, which this workspace cannot reach. Short-volume share is a flow signal:
# ~45-55% is normal (market makers short to fill buys); a sustained 60%+ suggests heavy shorting.
def finra_days(n=20):
    out, d = {}, dt.date.today()
    tries = 0
    while len(out) < n and tries < 40:
        d -= dt.timedelta(days=1); tries += 1
        if d.weekday() >= 5: continue
        try:
            txt = urllib.request.urlopen(urllib.request.Request(f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d:%Y%m%d}.txt", headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode()
        except Exception:
            continue
        day = {}
        for line in txt.splitlines()[1:]:
            p = line.split("|")
            if len(p) >= 5:
                try: day[p[1]] = (float(p[2]), float(p[4]))
                except ValueError: pass
        out[d.isoformat()] = day
    return out
SV = finra_days()
FINRA = bool(SV)
D = [r for r in json.load(open(root / "data/data.json")) if r.get("ta") != "Acquired / Inactive"]
nxt = {}
for r in D:
    ups = sorted([c for c in (r.get("cat_sched") or []) if c.get("st") == "up" and c.get("d")], key=lambda c: c["d"])
    if ups: nxt[r["ticker"]] = ups[0]["d"]
def options_move(tk, after):
    """ATM straddle / spot for the first expiry on or after `after` (Cboe delayed quotes)."""
    try:
        j = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://cdn-api.cboe.com/api/global/delayed_quotes/options/{tk}.json", headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read())
        dta = j["data"]; spot = dta["current_price"]; by = {}
        for o in dta["options"]:
            sym = o["option"]; exp = "20" + sym[-15:-9]; exp = f"{exp[:4]}-{exp[4:6]}-{exp[6:8]}"; cp = sym[-9]; k = int(sym[-8:]) / 1000
            mid = (o.get("bid", 0) + o.get("ask", 0)) / 2 or o.get("last_trade_price", 0)
            by.setdefault(exp, {}).setdefault(k, {})[cp] = mid
        exps = sorted(e for e in by if e >= after)
        if not exps: return None
        e = exps[0]; ks = [k for k in by[e] if "C" in by[e][k] and "P" in by[e][k]]
        k = min(ks, key=lambda k: abs(k - spot)); s = by[e][k]["C"] + by[e][k]["P"]
        return {"exp": e, "strike": k, "move": round(s / spot, 4)}
    except Exception:
        return None
out = {}
for r in D:
    t = r["ticker"]; s = series(t)
    if not s or len(s) < 30: continue
    last = s[-20:]; adv = st.mean(c * v for d, c, v in last)
    rets = [(s[i][0], s[i][1] / s[i - 1][1] - 1) for i in range(1, len(s))]
    r60 = [x for d, x in rets[-60:]]
    vol = st.pstdev(r60) * 252 ** .5 if len(r60) > 20 else None
    xs = []
    for i in range(max(1, len(s) - 504), len(s)):
        d0, d1 = s[i - 1][0], s[i][0]
        if d0 in XB and d1 in XB: xs.append(abs(s[i][1] / s[i - 1][1] - 1 - (XB[d1] / XB[d0] - 1)))
    xs.sort(); big = st.mean(xs[-5:]) if len(xs) > 100 else None  # average of its 5 biggest days vs XBI
    rec = {"adv20": round(adv), "days10": round(1e7 / (0.2 * adv), 1) if adv > 0 else None, "vol60": round(vol, 3) if vol else None,
           "bigday": round(big, 4) if big else None, "bigday_n": len(xs)}
    if CBOE and t in nxt: rec["opt"] = options_move(t, nxt[t])
    if SV:
        sh = sum(SV[d].get(t, (0, 0))[0] for d in SV); tv = sum(SV[d].get(t, (0, 0))[1] for d in SV)
        last5 = sorted(SV)[-5:]; sh5 = sum(SV[d].get(t, (0, 0))[0] for d in last5); tv5 = sum(SV[d].get(t, (0, 0))[1] for d in last5)
        if tv > 0: rec["svr20"] = round(sh / tv, 3); rec["svr5"] = round(sh5 / tv5, 3) if tv5 else None
    out[t] = rec
json.dump({"built": dt.date.today().isoformat(), "asof": str(max(XB)) if XB else None, "options_source": "cboe" if CBOE else None,
           "short_source": "finra_regsho_short_volume" if FINRA else None, "short_days": len(SV), "position_usd": 1e7, "participation": 0.2, "rows": out},
          open(root / "data/tradeinfo.json", "w"), separators=(",", ":"))
print(len(out), "tickers; options", "reachable" if CBOE else "blocked (allow cdn-api.cboe.com)", "; FINRA short volume", f"{len(SV)} days" if FINRA else "blocked")
L = sorted(out.items(), key=lambda kv: kv[1]["adv20"])
print("thinnest:", [(t, round(v["adv20"] / 1e3), v["days10"]) for t, v in L[:6]])
print("median ADV $M", round(st.median(v["adv20"] for v in out.values()) / 1e6, 1), "median big day", round(st.median(v["bigday"] for v in out.values() if v["bigday"]) * 100, 1), "%")
