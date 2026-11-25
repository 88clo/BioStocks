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
                "best": sorted(({"t": x["t"], "r": x["v1"] / x["v0"] - 1} for x in L if x["v0"] > 2e6), key=lambda x: -x["r"])[:3]})
out.sort(key=lambda x: -x["v1"])

# who owns the covered universe (top-10 holder positions only)
cap = sum(r.get("mc") or 0 for r in D.values() if r.get("ta") != "Acquired / Inactive")
held = {"spec": 0, "passive": 0, "other": 0}
for f in out:
    held["spec" if f["spec"] else "passive" if f["passive"] else "other"] += f["v1"]

B = {}
for b in ["XBI", "IBB"]:
    S = series(b)
    if S:
        n = S[-1]; B[b] = {"r": n[1] / on(S, SNAP) - 1, "r12": n[1] / on(S, n[0] - dt.timedelta(days=365)) - 1}
ew = [P[t] for t in D if t in P and P[t]["snap"] and P[t]["now"]]
srt = lambda L: sorted(L)[len(L) // 2]
B["Median covered stock"] = {"r": srt([p["now"] / p["snap"] - 1 for p in ew]), "r12": srt([p["now"] / p["y1"] - 1 for p in ew if p["y1"]])}
json.dump({"bench": B, "asof_snap": "2026-09-11", "asof_now": asof_now, "holders_asof": "Sep 13 2026 (Yahoo; 13F positions, mostly Jun 30)", "cap": cap, "held": held,
           "funds": out}, open(root / "data/investors.json", "w"), separators=(",", ":"))
print(B); print(len(out), "holders;", sum(1 for f in out if f["spec"]), "specialists; cap", round(cap / 1e9), "B; held", {k: round(v / 1e9) for k, v in held.items()})
for f in [x for x in out if x["spec"] and x["n"] >= 5 and x["v1"] > 2e8][:5]: print(f["nick"], f["n"], round(f["v1"] / 1e9, 2), round((f["r"] or 0) * 100), round((f["r12"] or 0) * 100))
