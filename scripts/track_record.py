"""Score every time-stamped call set we still have against later prices (Yahoo daily closes).
Cohorts: Sep 12 snapshot (repo file biotech_idea_snapshot.html), Oct 13 memo (frozen longs + TA ideas),
Nov 17 ledger (ledger/2026-11-17_before-refresh.json) and Nov 18 memo longs (tracking starts).
Output: data/track-data.json, rendered by the Track record tab."""
import json, re, pathlib, statistics as st, datetime as dt, bisect
root = pathlib.Path(__file__).resolve().parents[1]
def pts(tk):
    f = root/"cache/prices"/f"{tk}.json"
    if not f.exists(): return None
    j = json.load(open(f))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    return [(dt.datetime.fromtimestamp(t, dt.timezone.utc).date(), c) for t, c in zip(j.get("timestamp") or [], q.get("close") or []) if c]
def close_on(p, d):
    ds = [x[0] for x in p]; i = bisect.bisect_right(ds, d) - 1
    return p[i][1] if i >= 0 and (d - p[i][0]).days <= 5 else None
def ret(tk, d0, d1):
    p = pts(tk)
    if not p: return None
    a, b = close_on(p, d0), close_on(p, d1)
    return (b/a - 1)*100 if a and b else None
def summ(xs):
    xs = [x for x in xs if x is not None]
    if not xs: return {"n": 0}
    return {"n": len(xs), "median": round(st.median(xs), 1), "mean": round(st.mean(xs), 1), "pct_pos": round(100*sum(x > 0 for x in xs)/len(xs))}
END = max(p[0] for p in pts("XBI"))
out = {"asof": str(END), "cohorts": [], "method": "Price-only returns from the close on the call date to the latest close; split-adjusted; equal-weighted; no dividends, costs or borrow. Universe = every covered name priced on both dates. Shorts are reported as stock returns (a falling stock is a winning short)."}
def cohort(label, d0, rows, groups, note, kind="snapshot"):
    xbi = ret("XBI", d0, END); ibb = ret("IBB", d0, END)
    for r in rows: r["ret"] = ret(r["ticker"], d0, END)
    uni = summ([r["ret"] for r in rows])
    G = []
    for gl, fn, side in groups:
        sel = [r for r in rows if fn(r)]; s = summ([r["ret"] for r in sel]); s.update({"label": gl, "side": side})
        if s["n"] and uni.get("n"):
            s["vs_universe"] = round(s["median"] - uni["median"], 1)
            s["beat_xbi_pct"] = round(100*sum((r["ret"] or 0) > (xbi or 0) for r in sel if r["ret"] is not None)/s["n"])
        G.append(s)
    named = sorted([r for r in rows if r["ret"] is not None and any(fn(r) for _, fn, _ in groups[:3])], key=lambda r: -r["ret"])
    out["cohorts"].append({"label": label, "date": str(d0), "days": (END - d0).days, "kind": kind, "note": note,
        "xbi": round(xbi, 1) if xbi is not None else None, "ibb": round(ibb, 1) if ibb is not None else None, "universe": uni, "groups": G,
        "best": [{"t": r["ticker"], "call": r.get("call"), "r": round(r["ret"], 1)} for r in named[:5]],
        "worst": [{"t": r["ticker"], "call": r.get("call"), "r": round(r["ret"], 1)} for r in named[-5:][::-1]]})
LONG = ("STRONG BUY", "LONG"); SHORT = ("SHORT", "STRONG SHORT")
# --- Sep 12 snapshot ---
s = (root/"biotech_idea_snapshot.html").read_text(encoding="utf-8")
sep = json.loads(re.search(r"const SIMPLE_ROWS=(\[.*?\]);\s*\n", s, re.S).group(1))
ideas = json.loads(re.search(r"const TA_IDEAS=(\[.*?\]);\s*\n", s, re.S).group(1))
prim = {i["ticker"] for i in ideas if i["rank"] == "primary"}
cohort("Sep 12 snapshot", dt.date(2026, 9, 11), sep, [
    ("Best ideas (primary)", lambda r: r["ticker"] in prim, "long"),
    ("Strong Buy", lambda r: r["call"] == "STRONG BUY", "long"),
    ("Long", lambda r: r["call"] == "LONG", "long"),
    ("Watch", lambda r: r["call"] == "WATCH", "neutral"), ("Hold", lambda r: r["call"] == "HOLD", "neutral"),
    ("Avoid", lambda r: r["call"] == "AVOID", "short"), ("Short", lambda r: r["call"] == "SHORT", "short"),
    ("Strong Short", lambda r: r["call"] == "STRONG SHORT", "short")],
    "Earliest full call set still on file (repo upload, 482 names). Calls were formula-driven off the then-current sheet; first five weeks overlap the rebuild of the baseline.")
# --- Oct 13 memo ---
M = json.load(open(root/"data/memo-baked.json"))["months"]["2026-10"]
fr = M.get("frozen") or M
rows = [{"ticker": l["ticker"], "call": l.get("call"), "grp": "hc"} for l in fr["longs"]]
for i in fr["ideas"]:
    if i.get("long"): rows.append({"ticker": i["long"]["ticker"], "call": i["long"].get("call"), "grp": "talong"})
    if i.get("short"): rows.append({"ticker": i["short"]["ticker"], "call": i["short"].get("call"), "grp": "tashort"})
cohort("Oct 13 memo", dt.date(2026, 10, 13), rows, [
    ("Highest-conviction longs (memo §2)", lambda r: r["grp"] == "hc", "long"),
    ("Best long per TA (memo §3)", lambda r: r["grp"] == "talong", "long"),
    ("Best short per TA (memo §3)", lambda r: r["grp"] == "tashort", "short")],
    "Only the names printed in the memo are on file; the full Oct ledger (ledger/2026-10.json) was not recovered, so the universe here is just these names.", kind="memo")
# --- Nov 17 ledger (pre-refresh, page-computed calls) ---
L = json.load(open(root/"ledger/2026-11-17_before-refresh.json"))["rows"]
cohort("Nov 17 ledger", dt.date(2026, 11, 16), L, [
    ("Rule-based top picks", lambda r: r["top"], "long"),
    ("Strong Buy", lambda r: r["call"] == "STRONG BUY", "long"), ("Long", lambda r: r["call"] == "LONG", "long"),
    ("Short + Strong Short", lambda r: r["call"] in SHORT, "short"), ("Avoid", lambda r: r["call"] == "AVOID", "short")],
    "Full 402-name ledger frozen before this refresh (sha256 in the file). Four trading days old: a baseline, not evidence.", kind="ledger")
# --- signal check on the Sep cohort: does cheapness (model upside) predict returns? ---
q = [r for r in sep if isinstance(r.get("up"), (int, float)) and r["ret"] is not None]
q.sort(key=lambda r: r["up"]); n = len(q); quint = []
for k in range(5):
    part = q[k*n//5:(k+1)*n//5]; ss = summ([r["ret"] for r in part]); ss["label"] = ["Richest 20%", "2", "3", "4", "Cheapest 20%"][k]
    ss["up_range"] = [round(part[0]["up"]), round(part[-1]["up"])]; quint.append(ss)
out["bench"] = {"xbi_1m": ret("XBI", END - dt.timedelta(days=30), END), "xbi_3m": ret("XBI", END - dt.timedelta(days=91), END), "ibb_1m": ret("IBB", END - dt.timedelta(days=30), END)}
out["signal"] = {"cohort": "Sep 12 snapshot", "by_model_upside": quint}

# --- what actually explained the Sep->Nov move (size, stage, funding, science) ---
D = {r["ticker"]: r for r in json.load(open(root/"data/data.json"))}
def fac(name, f, note=""):
    g = {}
    for r in sep:
        if r.get("ret") is None: continue
        k = f(r, D.get(r["ticker"], {}))
        if k is not None: g.setdefault(k, []).append(r["ret"])
    return {"factor": name, "note": note, "buckets": [dict(summ(v), label=k) for k, v in sorted(g.items())]}
sci = lambda x: ((x.get("effsig") or 0) + (x.get("diffscore") or 0))/2 if x.get("effsig") is not None else None
out["factors"] = [
    fac("Market cap at call", lambda r, x: "1 <$150M" if r["mc"] < 150e6 else "2 $150-500M" if r["mc"] < 500e6 else "3 $0.5-2B" if r["mc"] < 2e9 else "4 >$2B"),
    fac("Stage at call", lambda r, x: "1 Approved" if str(r["stage"]).startswith("Approved") else "2 Ph3/Filed" if re.search("3|Filed", str(r["stage"])) else "3 Earlier"),
    fac("Model cheapness x size", lambda r, x: ("1 cheap" if (r.get("up") or 0) > 200 else "2 not cheap") + (" <$500M" if r["mc"] < 500e6 else " >$500M")),
    fac("Runway (current data)", lambda r, x: None if x.get("runway_q") is None else "1 <6Q" if x["runway_q"] < 6 else "2 6-12Q" if x["runway_q"] < 12 else "3 12Q+", "uses today's runway, small look-ahead"),
    fac("Quality screen (current scores)", lambda r, x: "1 pass" if (sci(x) or 0) >= 3.5 and r["mc"] >= 500e6 and (x.get("runway_q") or 0) >= 8 else "2 fail", "science >=3.5, cap >=$500M, runway >=8Q; science scores are today's, so some look-ahead"),
]
json.dump(out, open(root/"data/track-data.json", "w"), indent=1)

# --- join the hindsight list (biggest moves per quarter, researched drivers) with our calls ---
RT = json.load(open(root/"data/retro-data.json"))
sepcall = {r["ticker"]: r["call"] for r in sep}
def fore(d):
    f = (d.get("foreseeable") or "").lower()
    return "scheduled" if f.startswith("scheduled") else "guided" if "guided" in f else "unscheduled" if f.startswith("unscheduled") else "unverified"
by = {}
rows4 = []
for q in RT["quarters"]:
    for side in ("longs", "shorts"):
        for x in q.get(side, []):
            d = x.get("drv") or {}; ty = d.get("driver_type") or "unverified"; fo = fore(d)
            b = by.setdefault(ty, {"type": ty, "up": 0, "down": 0, "scheduled": 0, "guided": 0, "unscheduled": 0, "unverified": 0})
            b["up" if side == "longs" else "down"] += 1; b[fo] += 1
            if q["q"].startswith("4Q26"):
                c = sepcall.get(x["t"]); right = None
                if c: right = (c in LONG) if side == "longs" else (c in SHORT or c == "AVOID")
                rows4.append({"t": x["t"], "side": "up" if side == "longs" else "down", "ret": x["ret"], "type": ty, "fore": fo, "sep_call": c, "right": right, "note": (d.get("note") or "")[:160]})
tot = sum(b["up"] + b["down"] for b in by.values())
for b in by.values():
    n = b["up"] + b["down"]; b["n"] = n; b["share"] = round(100*n/tot); b["knowable_pct"] = round(100*(b["scheduled"] + b["guided"])/n) if n else None
had = [r for r in rows4 if r["sep_call"]]
out["misses"] = {"quarters": [q["q"] for q in RT["quarters"]], "n": tot, "by_type": sorted(by.values(), key=lambda b: -b["n"]),
    "knowable_pct": round(100*sum(b["scheduled"] + b["guided"] for b in by.values())/tot),
    "q4": {"window": RT["quarters"][-1]["start"] + " to " + RT["quarters"][-1]["end"], "rows": rows4, "covered": len(had),
           "right": sum(1 for r in had if r["right"]), "up_right": sum(1 for r in had if r["right"] and r["side"] == "up"), "up_n": sum(1 for r in had if r["side"] == "up"),
           "down_right": sum(1 for r in had if r["right"] and r["side"] == "down"), "down_n": sum(1 for r in had if r["side"] == "down")}}
json.dump(out, open(root/"data/track-data.json", "w"), indent=1)
for c in out["cohorts"]:
    print(f"\n{c['label']} ({c['days']}d) XBI {c['xbi']} IBB {c['ibb']} universe {c['universe']}")
    for g in c["groups"]: print("  ", g)
    print("  best", c["best"]); print("  worst", c["worst"])
print("\nquintiles", [(x["label"], x.get("median"), x.get("n")) for x in quint])
