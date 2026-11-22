"""Build two derived views from data/*.json + cached fundamentals:
 1) Raise radar (ECM): who is likely to sell stock in the next ~6 months, how much, when, and whether we'd want an allocation.
 2) White space: indications where patients are many but public assets are weak or few; crowded fields; cash shells
    (negative-EV companies that are natural reverse-merger / pivot vehicles for private companies).
Writes data/radar-data.json and data/gaps-data.json."""
import json, pathlib, statistics as st, datetime as dt
root = pathlib.Path(__file__).resolve().parents[1]
D = json.load(open(root/"data/data.json"))
L = {r["ticker"]: r for r in json.load(open(root/"ledger/2026-11-22_refresh.json"))["rows"]} if (root/"ledger/2026-11-22_refresh.json").exists() else {}
TODAY = dt.date(2026, 11, 22)
def fund(tk):
    f = root/"cache/fund"/f"{tk}.json"
    return json.load(open(f)) if f.exists() else {}
def sci(r): return ((r.get("effsig") or 0) + (r.get("diffscore") or 0))/2 if r.get("effsig") is not None else None
LONGS = {"STRONG BUY", "LONG"}; SHORTS = {"SHORT", "STRONG SHORT"}
radar = []
for r in D:
    if r.get("ta") == "Acquired / Inactive": continue
    mc, cash, rw = r.get("mc") or 0, r.get("cash") or 0, r.get("runway_q")
    if mc < 75e6: continue
    approved = str(r.get("stage", "")).startswith("Approved")
    burn = cash/rw if rw and rw > 0 else None                       # quarterly cash burn
    F = fund(r["ticker"]); iss = F.get("IssuanceOfCapitalStock", {})
    raised_4q = sum(v for k, v in iss.items() if k >= "2025-10-01" and v and v > 0)
    call = (L.get(r["ticker"], {}).get("call") or r.get("call") or "").upper()
    cm = r.get("cat_mos"); r1, r3 = r.get("r1m"), r.get("r3m")
    # --- need: quarters of cash left ---
    need = 0 if rw is None else (3 if rw < 4 else 2 if rw < 6 else 1 if rw < 9 else 0)
    if rw is None and (r.get("net_income") or 0) >= 0: need = 0
    # --- window: a catalyst inside 4 months (companies sell stock into good data), or a run-up open now ---
    win = 0; why = []
    if cm is not None and 0 <= cm <= 4: win += 1; why.append(f"catalyst in ~{max(cm,0.1):.0f} mo")
    if (r1 or 0) > 0.30 or (r3 or 0) > 0.60: win += 2; why.append(f"stock {'+'+str(round((r1 or 0)*100))+'% 1M' if (r1 or 0)>0.30 else '+'+str(round((r3 or 0)*100))+'% 3M'}: window open now")
    if raised_4q > 0.10*mc: why.append(f"raised ${raised_4q/1e6:.0f}M in last 4 quarters (repeat issuer)")
    ev = (r.get("inputs") or {}).get("events") or ""
    if any(w in ev.lower() for w in ("offering", "received", "upfront", "placement", "atm ", "priced", "deal:")):
        why.append("since quarter-end: " + ev[:140])
    exec_ok = (r.get("adv") or 0) >= 1e6 and mc >= 150e6
    score = need*2 + win + (1 if raised_4q > 0.10*mc else 0) + (1 if exec_ok else -2)
    if score < 4 or approved and need < 2: continue
    size = None
    if burn: size = min(max(6*burn, 0.10*mc), 0.30*mc)            # ~18 months of burn, bounded 10-30% of cap
    else: size = 0.15*mc
    if need >= 2 and win == 0: timing = "Before runway gets short (next 1-2 quarters)"
    elif (r1 or 0) > 0.30 or (r3 or 0) > 0.60: timing = "Now — window open after run-up"
    elif cm is not None and 0 <= cm <= 4: timing = f"Right after the catalyst (~{(TODAY + dt.timedelta(days=int(30*max(cm,0)))).strftime('%b %Y')}), if positive"
    else: timing = "Opportunistic, next 6 months"
    s_ = sci(r)
    view = ("Participate" if call in LONGS and (s_ or 0) >= 3 else "Short into the deal" if call in SHORTS else "Pass" if call in {"AVOID"} or (s_ or 0) < 2.5 else "Price-sensitive")
    radar.append({"ticker": r["ticker"], "name": r.get("nick") or r.get("name"), "ta": r.get("ta"), "stage": r.get("stage"), "mc": mc, "cash": cash,
        "runway_q": rw, "burn_q": burn, "cat": r.get("nc") or r.get("catalyst"), "cat_mos": cm, "r1m": r1, "r3m": r3, "adv": r.get("adv"),
        "raised_4q": raised_4q, "score": score, "size": size, "size_pct": size/mc if mc else None, "timing": timing, "why": why,
        "call": call, "sci": s_, "view": view, "need": need})
radar.sort(key=lambda x: (-x["score"], x["runway_q"] if x["runway_q"] is not None else 99))
json.dump({"asof": str(TODAY), "rows": radar, "method": "Score = 2 x need (runway <4Q=3, <6Q=2, <9Q=1) + window (catalyst within 4 months = 1; 1M run-up >30% or 3M >60% = 2) + 1 if the company sold stock worth >10% of its cap in the last four reported quarters + 1 if executable (cap >=$150M and ADV >=$1M; else -2). Shown if score >=4. Size = ~18 months of burn, bounded to 10-30% of market cap. View: Participate = our call is Long/Strong Buy with science >=3; Short into the deal = Short call; Pass = Avoid or weak science."},
          open(root/"data/radar-data.json", "w"), indent=1)
# ---------------- white space ----------------
groups = {}
for r in D:
    if r.get("ta") == "Acquired / Inactive": continue
    g = r.get("indgroup") or "Other"
    groups.setdefault(g, []).append(r)
gaps = []
for g, rs in groups.items():
    pts = max([x.get("treated") or 0 for x in rs] + [0]); prev = max([x.get("prevalence") or 0 for x in rs] + [0])
    best = max(rs, key=lambda x: (sci(x) or 0, x.get("pos") or 0))
    strong = [x for x in rs if (sci(x) or 0) >= 3.5]
    late = [x for x in rs if str(x.get("stage", "")).startswith(("Approved", "Filed", "Phase 3"))]
    gaps.append({"group": g, "ta": rs[0].get("ta"), "n": len(rs), "n_strong": len(strong), "n_late": len(late), "prevalence": prev, "treated": pts,
        "best": {"t": best["ticker"], "sci": sci(best), "stage": best.get("stage"), "drug": (best.get("drug") or "")[:60], "eff": (best.get("efficacy") or "")[:160]},
        "cap": sum(x.get("mc") or 0 for x in rs), "tickers": [x["ticker"] for x in sorted(rs, key=lambda x: -(x.get("mc") or 0))]})
BIG_PHARMA = {"Type 2 diabetes", "Obesity", "Cosmetic derm", "COVID"}   # fields led by >$30B companies outside our coverage
under = sorted([x for x in gaps if x["group"] not in BIG_PHARMA and x["prevalence"] >= 100000 and (x["best"]["sci"] or 0) < 3.5 and x["n"] <= 3], key=lambda x: -x["prevalence"])
crowded = sorted([x for x in gaps if x["n"] >= 6], key=lambda x: -x["n"])
shells = []
for r in D:
    mc, cash, debt = r.get("mc") or 0, r.get("cash") or 0, r.get("debt") or 0
    if mc and cash - debt > mc and mc >= 20e6:
        shells.append({"ticker": r["ticker"], "name": r.get("nick") or r.get("name"), "ta": r.get("ta"), "mc": mc, "net_cash": cash - debt, "ev": mc + debt - cash,
            "stage": r.get("stage"), "drug": (r.get("drug") or "")[:70], "sci": sci(r), "runway_q": r.get("runway_q"),
            "status": "strategic review" if "strategic" in ((r.get("catalyst") or "") + (r.get("inputs") or {}).get("events", "")).lower() else ""})
shells.sort(key=lambda x: x["ev"])
json.dump({"asof": str(TODAY), "under": under[:25], "crowded": crowded[:15], "shells": shells,
    "method": "Indication groups from the lead program of each covered company. Under-served = >=100K US prevalence, <=3 public companies, and no public asset with science >=3.5. Crowded = >=6 public companies with the same lead indication group. Fields led by companies above our $30B coverage cap (type 2 diabetes, obesity, cosmetic derm, COVID) are left out of Under-served because they only look empty here. Cash shells = net cash (cash - debt) above market cap (negative EV), cap >=$20M."},
    open(root/"data/gaps-data.json", "w"), indent=1)
print("radar", len(radar), "| top:", [(x["ticker"], x["score"], x["view"]) for x in radar[:12]])
print("under-served", [(x["group"], x["prevalence"], x["n"]) for x in under[:10]])
print("crowded", [(x["group"], x["n"], x["n_strong"]) for x in crowded[:8]])
print("shells", len(shells), [(x["ticker"], round(x["ev"]/1e6)) for x in shells[:10]])
