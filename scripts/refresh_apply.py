"""Apply cached Yahoo prices + fundamentals to data/*.json.
- prices, market caps (fully diluted shares x price), 1M/3M/12M/24M/36M returns, ADV (63-day mean $ volume)
- quarterly price history (current quarter = latest close; fills blanks)
- balance sheets: only where Yahoo has a NEWER quarter than the curated inputs (curated FD shares/cash kept)
- parked list, IPO prices
Writes a change log to pipeline/logs/refresh_<date>.json."""
import json, pathlib, datetime as dt, bisect
root = pathlib.Path(__file__).resolve().parents[1]
P = lambda n: root/"data"/n
def load(n): return json.load(open(P(n)))
def save(n, o): P(n).write_text(json.dumps(o, ensure_ascii=False, indent=1))
def series(tk):
    f = root/"cache/prices"/f"{tk}.json"
    if not f.exists(): return None
    j = json.load(open(f))["chart"]["result"][0]
    ts = j.get("timestamp") or []; q = j["indicators"]["quote"][0]
    pts = [(dt.datetime.fromtimestamp(t, dt.timezone.utc).date(), c, v) for t, c, v in zip(ts, q.get("close") or [], q.get("volume") or []) if c]
    splits = [(dt.datetime.fromtimestamp(s["date"], dt.timezone.utc).date(), s["numerator"]/s["denominator"]) for s in (j.get("events") or {}).get("splits", {}).values()]
    return {"pts": pts, "splits": splits}
def close_on(pts, day):
    ds = [p[0] for p in pts]; i = bisect.bisect_right(ds, day) - 1
    return pts[i][1] if i >= 0 and (day - pts[i][0]).days <= 7 else None
def rets(pts):
    last_d, last = pts[-1][0], pts[-1][1]; out = {}
    for k, days in [("r1m", 30), ("r3m", 91), ("r12m", 365), ("r24m", 730), ("r36m", 1095)]:
        if pts[0][0] <= last_d - dt.timedelta(days=days):
            b = close_on(pts, last_d - dt.timedelta(days=days)); out[k] = (last/b - 1) if b else None
        else: out[k] = None
    return out
def adv(pts): w = pts[-63:]; return sum(c*(v or 0) for _, c, v in w)/len(w)
log = {"prices": {}, "bs": {}, "splits": [], "band": [], "big_moves": []}
DATA = load("data.json"); asof = None
for r in DATA:
    s = series(r["ticker"])
    if not s or not s["pts"]: log["prices"][r["ticker"]] = "no data"; continue
    pts = s["pts"]; px = round(pts[-1][1], 4); asof = max(asof or pts[-1][0], pts[-1][0])
    old_px, old_mc = r.get("price"), r.get("mc"); inp = r.get("inputs") or {}
    ref = dt.date.fromisoformat((inp.get("date") or "2026-11-05")[:10])
    for sd, ratio in s["splits"]:          # split after the share count was set -> rescale shares
        if sd > ref and inp.get("fd_shares_m"):
            inp["fd_shares_m"] = round(inp["fd_shares_m"]*ratio, 4); log["splits"].append([r["ticker"], str(sd), ratio])
    if inp.get("fd_shares_m"): r["mc"] = px*inp["fd_shares_m"]*1e6
    elif old_px and old_mc: r["mc"] = old_mc*px/old_px
    if old_px and abs(px/old_px - 1) > 0.25: log["big_moves"].append([r["ticker"], old_px, px, round((px/old_px-1)*100, 1)])
    r["price"] = px; r.update(rets(pts)); r["adv"] = adv(pts)
    if r.get("cash") and r.get("mc"): r["cash_pct_mc"] = round(r["cash"]/r["mc"], 4)
    if r.get("ev") is not None: r["ev"] = r["mc"] + (r.get("debt") or 0) - (r.get("cash") or 0)
    if r["mc"] < 50e6 or r["mc"] > 30e9: log["band"].append([r["ticker"], "leaves band", round(r["mc"]/1e6)])
    # ---- balance sheet: only newer periods ----
    f = root/"cache/fund"/f"{r['ticker']}.json"
    if f.exists():
        F = json.load(open(f)); cashS = F.get("CashCashEquivalentsAndShortTermInvestments") or F.get("CashAndCashEquivalents") or {}
        if cashS:
            new_bs = max(cashS); old_bs = inp.get("bs_date") or "0000"
            if new_bs > old_bs:
                c = cashS[new_bs] + (F.get("LongTermInvestments", {}).get(new_bs) or 0)
                debt = F.get("TotalDebt", {}).get(new_bs)
                ocf = [F.get("OperatingCashFlow", {}).get(k) for k in sorted(F.get("OperatingCashFlow", {}))[-2:]]
                ocf = [x for x in ocf if x is not None]; burn = -sum(ocf)/len(ocf) if ocf else None
                sh_new = F.get("OrdinarySharesNumber", {}).get(new_bs); sh_old = F.get("OrdinarySharesNumber", {}).get(old_bs)
                ch = {"from": old_bs, "to": new_bs, "cash_old": r.get("cash"), "cash_new": c}
                r["cash_prev"] = r.get("cash"); r["cash"] = c
                if debt is not None: r["debt"] = debt
                ni = F.get("NetIncome", {}).get(new_bs)
                if ni is not None: r["net_income"] = ni
                rev = F.get("TotalRevenue", {}).get(new_bs)
                if rev is not None: r["rev_q"] = rev
                r["runway_q"] = round(c/burn, 1) if burn and burn > 0 else None
                if inp.get("fd_shares_m") and sh_new and sh_old and sh_new/sh_old > 1.02:   # keep curated warrants overlay
                    inp["fd_shares_m"] = round(inp["fd_shares_m"]*sh_new/sh_old, 4); r["mc"] = px*inp["fd_shares_m"]*1e6; ch["shares_x"] = round(sh_new/sh_old, 3)
                elif not inp.get("fd_shares_m") and sh_new: inp["fd_shares_m"] = round(sh_new/1e6, 4); r["mc"] = px*sh_new
                inp.update({"bs_date": new_bs, "date": str(dt.date.today()), "conf": "medium", "src": "Yahoo fundamentals timeseries (auto; curated FD overlay scaled)"})
                r["cash_pct_mc"] = round(c/r["mc"], 4) if r.get("mc") else None
                log["bs"][r["ticker"]] = ch
    r["inputs"] = inp
save("data.json", DATA)
# ---- quarterly price history ----
PQ = load("priceq-baked.json"); qs = PQ["quarters"]
def qend(q): n, y = int(q[0]), 2000+int(q[2:]); m = 3*n; return (dt.date(y+ (m==12), (m%12)+1, 1) - dt.timedelta(days=1))
filled = 0
for tk in set(PQ["prices"]) | {r["ticker"] for r in DATA}:
    s = series(tk)
    if not s or not s["pts"]: continue
    row = PQ["prices"].get(tk) or [None]*len(qs); row += [None]*(len(qs)-len(row))
    for i, q in enumerate(qs):
        e = qend(q)
        if e >= s["pts"][-1][0]: row[i] = round(s["pts"][-1][1], 2); continue
        if row[i] is None:
            v = close_on(s["pts"], e)
            if v: row[i] = round(v, 2); filled += 1
    PQ["prices"][tk] = row
save("priceq-baked.json", PQ)
# ---- parked ----
PK = load("parked-data.json")
for r in PK["rows"]:
    s = series(r["ticker"])
    if s and s["pts"] and r.get("price"):
        px = s["pts"][-1][1]; r["mc"] = r["mc"]*px/r["price"] if r.get("mc") else r.get("mc"); r["price"] = round(px, 4); r["last_seen"] = str(asof)
        if r.get("mc") and PK["lo"] <= r["mc"] <= PK["hi"]: log["band"].append([r["ticker"], "back in band (parked)", round(r["mc"]/1e6)])
PK["asof"] = str(asof); save("parked-data.json", PK)
# ---- IPOs ----
IPO = load("ipo-data.json")
for r in IPO.get("recent", []):
    s = series(r.get("ticker") or "")
    if s and s["pts"]:
        px = s["pts"][-1][1]; r["latest_price"] = round(px, 2)
        if r.get("offer_price"): r["return_since_ipo_pct"] = round((px/r["offer_price"]-1)*100, 1)
IPO["asof"] = str(asof); save("ipo-data.json", IPO)
log["asof"] = str(asof); log["quarter_fills"] = filled
(root/"pipeline/logs").mkdir(parents=True, exist_ok=True)
(root/f"pipeline/logs/refresh_{asof}.json").write_text(json.dumps(log, indent=1))
print("prices as of", asof, "| balance sheets updated:", len(log["bs"]), "| splits:", log["splits"], "| quarter fills:", filled)
print("big moves >25% since last price:", sorted(log["big_moves"], key=lambda x: x[3]))
print("band:", log["band"])
