"""Investor holdings and returns -> data/investors.json.

Source: data/holders-baked.json (top ~10 holders per company from Yahoo/13F, snapshot Sep 13 2026; positions mostly as of the Jun 30 filings).
For every holder: positions in names we have prices for, dollar value at the snapshot (Sep 11 close) and now (latest close),
value-weighted return since the snapshot, and a look-back: how today's book would have done over the last 12 months had it been held
(a hypothetical, not the fund's realised return: 13F shows holdings, not trades)."""
import json, re, pathlib, datetime as dt
root = pathlib.Path(__file__).resolve().parents[1]

def series(t):
    f = root / "cache/prices" / f"{t}.json"
    try:
        j = json.load(open(f))["chart"]["result"][0]; ind = j["indicators"]
        c = (ind.get("adjclose") or [{}])[0].get("adjclose") or ind["quote"][0]["close"]
        return [(dt.datetime.fromtimestamp(a, dt.UTC).date(), b) for a, b in zip(j["timestamp"], c) if b]
    except Exception:
        return None
def on(S, d):
    best = None
    for a, b in S:
        if a <= d: best = b
        else: break
    return best

tpl = (root / "pipeline/template.html").read_text(encoding="utf-8")
SPEC = set(json.loads(re.search(r"const SPECIALIST_INVESTORS=new Set\((\[.*?\])\);", tpl).group(1)))
NICK = json.loads(re.search(r"const SPECIALIST_NICKNAMES=(\{.*?\});", tpl).group(1))
PASSIVE = re.compile(r"Vanguard|Blackrock|BlackRock|State Street|Geode|Northern Trust|Dimensional|Invesco|Schwab|iShares|SSgA|Fidelity Index|Russell|Morgan Stanley|Goldman Sachs|UBS|JPMorgan|Bank of America|Wells Fargo|Charles", re.I)

H = json.load(open(root / "data/holders-baked.json"))
D = {r["ticker"]: r for r in json.load(open(root / "data/data.json"))}
SNAP = dt.date(2026, 9, 11)
P = {}
for t in H:
    S = series(t)
    if not S: continue
    now_d, now_p = S[-1]
    P[t] = {"snap": on(S, SNAP), "now": now_p, "y1": on(S, now_d - dt.timedelta(days=365)), "q": now_d}
asof_now = max(v["q"] for v in P.values()).isoformat()

F = {}
for t, h in H.items():
    p = P.get(t)
    if not p or not p["snap"] or not p["now"]: continue
    for row in h.get("rows", []):
        n, sh = row.get("name"), row.get("shares") or 0
        if not n or sh <= 0: continue
        f = F.setdefault(n, {"name": n, "nick": NICK.get(n), "spec": n in SPEC, "passive": bool(PASSIVE.search(n)) and n not in SPEC, "pos": []})
        f["pos"].append({"t": t, "sh": sh, "pct": row.get("pct"), "v0": sh * p["snap"], "v1": sh * p["now"], "vy": sh * p["y1"] if p["y1"] else None, "cov": t in D})

out = []
for f in F.values():
    L = f["pos"]; v0 = sum(x["v0"] for x in L); v1 = sum(x["v1"] for x in L)
    Ly = [x for x in L if x["vy"]]; vy = sum(x["vy"] for x in Ly); v1y = sum(x["v1"] for x in Ly)
    L.sort(key=lambda x: -x["v1"])
    out.append({"name": f["name"], "nick": f["nick"], "spec": f["spec"], "passive": f["passive"], "n": len(L), "v0": round(v0), "v1": round(v1),
                "r": (v1 / v0 - 1) if v0 else None, "r12": (v1y / vy - 1) if vy else None,
                "top": [{"t": x["t"], "v1": round(x["v1"]), "r": x["v1"] / x["v0"] - 1, "pct": x["pct"]} for x in L[:8]],
                "pos": [[x["t"], round(x["v1"]), round(x["v1"] / x["v0"] - 1, 4), x["pct"]] for x in L],
                "best": sorted(({"t": x["t"], "r": x["v1"] / x["v0"] - 1} for x in L if x["v0"] > 2e6), key=lambda x: -x["r"])[:3]})
out.sort(key=lambda x: -x["v1"])

# who owns the covered universe (top-10 holder positions only)
cap = sum(r.get("mc") or 0 for r in D.values() if r.get("ta") != "Acquired / Inactive")
held = {"spec": 0, "passive": 0, "other": 0}
for f in out:
    held["spec" if f["spec"] else "passive" if f["passive"] else "other"] += f["v1"]

# ownership by company size: share of each company's market cap held by specialists / index & banks / other active (top-10 holders only)
own = {}
def bucket(mc): return "< $300M" if mc < 3e8 else "$300M–1B" if mc < 1e9 else "$1–5B" if mc < 5e9 else "$5–20B" if mc < 2e10 else "> $20B"
cat = {f["name"]: ("spec" if f["spec"] else "passive" if f["passive"] else "other") for f in out}
for t, h in H.items():
    r = D.get(t); p = P.get(t)
    if not r or not r.get("mc") or r.get("ta") == "Acquired / Inactive" or not p or not p["now"]: continue
    bk = bucket(r["mc"]); o = own.setdefault(bk, {"cap": 0, "n": 0, "spec": 0, "passive": 0, "other": 0, "spec_eq": []})
    o["cap"] += r["mc"]; o["n"] += 1; sp = 0
    for row in h.get("rows", []):
        c = cat.get(row.get("name"))
        if c: o[c] += (row.get("shares") or 0) * p["now"]
        if c == "spec": sp += row.get("pct") or 0
    o["spec_eq"].append(sp)
for o in own.values():
    L = sorted(o.pop("spec_eq")); o["spec_med_pct"] = L[len(L) // 2] if L else None
# quarter-end XBI and covered-universe market cap, for the net-supply view
xs = series("XBI"); XQ = {}
for y in (2023, 2024, 2025, 2026):
    for qn, (m, d) in enumerate([(3, 31), (6, 30), (9, 30), (12, 31)], 1):
        dd = min(dt.date(y, m, d), xs[-1][0]); XQ[f"{qn}Q{str(y)[2:]}"] = round(on(xs, dd), 2)
MQ = json.load(open(root / "data/mcq.json")); UC = {}
for k, q in enumerate(MQ["quarters"]):
    v = sum((r["mc"][k] or 0) for r in MQ["rows"].values())
    if v: UC[q] = round(v)
B = {}
for b in ["XBI", "IBB"]:
    S = series(b)
    if S:
        n = S[-1]; B[b] = {"r": n[1] / on(S, SNAP) - 1, "r12": n[1] / on(S, n[0] - dt.timedelta(days=365)) - 1}
ew = [P[t] for t in D if t in P and P[t]["snap"] and P[t]["now"]]
srt = lambda L: sorted(L)[len(L) // 2]
B["Median covered stock"] = {"r": srt([p["now"] / p["snap"] - 1 for p in ew]), "r12": srt([p["now"] / p["y1"] - 1 for p in ew if p["y1"]])}
json.dump({"own": own, "xbi_q": XQ, "ucap_q": UC, "bench": B, "asof_snap": "2026-09-11", "asof_now": asof_now, "holders_asof": "Sep 13 2026 (Yahoo; 13F positions, mostly Jun 30)", "cap": cap, "held": held,
           "funds": out}, open(root / "data/investors.json", "w"), separators=(",", ":"))
print(B); print(len(out), "holders;", sum(1 for f in out if f["spec"]), "specialists; cap", round(cap / 1e9), "B; held", {k: round(v / 1e9) for k, v in held.items()})
for f in [x for x in out if x["spec"] and x["n"] >= 5 and x["v1"] > 2e8][:5]: print(f["nick"], f["n"], round(f["v1"] / 1e9, 2), round((f["r"] or 0) * 100), round((f["r12"] or 0) * 100))
