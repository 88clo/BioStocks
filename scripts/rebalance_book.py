"""Weekly rebalance of the paper book against the live Top-20 ranking (Nov 27 2026).
Rule (also shown on Record › Paper book):
  - Exit a long that has fallen below #25 in the live long ranking (or lost its Long / Strong Buy call), and a short below #8
    (or no longer a Short call). The buffer (25 vs 15, 8 vs 5) stops names flipping in and out on small score changes.
  - Fill empty slots with the highest-ranked live names not held, at their live size.
  - Resize a kept name when its live weight differs from its current weight by more than 2% of NAV.
  - Otherwise leave it alone. Run weekly (Monday, before the open, on Friday's close) and after a book name's catalyst resolves.
Each rebalance closes the current segment at the latest close and opens a new one with the NAV carried forward.
Usage: python3 scripts/rebalance_book.py [--dry]   (--dry prints the trades without changing data/book.json)"""
import json, sys, pathlib, datetime as dt
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parents[1]
DRY = "--dry" in sys.argv
JS = r"""(()=>{const R=TOP20();const f=(L,side)=>L.map((p,i)=>({t:p.x.t,rank:i+1,side:side,w:p.w,call:p.x.r.call,price:p.x.r.price,score:Math.round(p.score*100)/100,bind:p.bind,
  toc:p.o?{ev:Math.round(p.o.ev*1000)/1000,d:p.o.d,lab:p.o.lab,e:p.o.e,ty:p.o.ty}:null}));return {L:f(R.allL,'l'),S:f(R.allS,'s')};})()"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg = b.new_page()
    pg.goto((root / "index.html").resolve().as_uri(), wait_until="load", timeout=120000); pg.wait_for_timeout(3000)
    LIVE = pg.evaluate(JS); b.close()
B = json.load(open(root / "data/book.json"))
if "segments" not in B: B["segments"] = [{"start": B["inception"], "nav0": B["nav"], "positions": B["positions"], "trades": []}]
seg = B["segments"][-1]
marks = json.load(open(root / "data/book-marks.json"))
nav = marks["marks"][-1]["nav"] if marks.get("marks") else B["nav"]; asof = marks.get("asof") or B["inception"]
def close(t):
    f = root / f"cache/prices/{t}.json"
    j = json.load(open(f))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    S = [(dt.datetime.fromtimestamp(a, dt.timezone.utc).date().isoformat(), c) for a, c in zip(j["timestamp"], q["close"]) if c]
    S = [x for x in S if x[0] <= asof]; return S[-1][1] if S else None
held = {p["t"]: p for p in seg["positions"] if p["side"] in ("l", "s")}
rankL = {x["t"]: x for x in LIVE["L"]}; rankS = {x["t"]: x for x in LIVE["S"]}
trades, keep = [], {}
for t, p in held.items():
    live = (rankL if p["side"] == "l" else rankS).get(t); lim = 25 if p["side"] == "l" else 8
    cw = abs(p["shares"] * close(t)) / nav
    if not live or live["rank"] > lim:
        trades.append({"t": t, "act": "exit", "side": p["side"], "from": round(cw, 4), "to": 0, "why": ("ranked #%d" % live["rank"]) if live else "no longer a %s call" % ("Long" if p["side"] == "l" else "Short")})
        continue
    if abs(live["w"] - cw) > 0.02:
        trades.append({"t": t, "act": "resize", "side": p["side"], "from": round(cw, 4), "to": round(live["w"], 4), "why": "live size %.1f%% vs %.1f%% held" % (live["w"] * 100, cw * 100)})
        keep[t] = live["w"]
    else: keep[t] = cw
for side, L, n in (("l", LIVE["L"], 15), ("s", LIVE["S"], 5)):
    have = [t for t in keep if held[t]["side"] == side] if keep else []
    for x in L:
        if len(have) >= n: break
        if x["t"] in keep or x["w"] < 0.01: continue
        keep[x["t"]] = x["w"]; have.append(x["t"])
        trades.append({"t": x["t"], "act": "add", "side": side, "from": 0, "to": round(x["w"], 4), "why": "live rank #%d, score %.1f" % (x["rank"], x["score"])})
print(f"as of {asof}, NAV {nav/1e6:.1f}M: {len(trades)} trades")
for tr in trades: print(f"  {tr['act']:6} {tr['t']:6} {tr['side']} {tr['from']*100:5.1f}% -> {tr['to']*100:5.1f}%  ({tr['why']})")
json.dump({"asof": asof, "nav": nav, "trades": trades, "rule": __doc__.split("Rule (also shown on Record › Paper book):")[1].split("Each rebalance")[0].strip()},
          open(root / "data/rebalance.json", "w"), indent=1)
if DRY or not trades: sys.exit(0)
pos = []
for t, w in keep.items():
    side = held[t]["side"] if t in held else ("l" if t in rankL else "s"); px = close(t)
    info = (rankL if side == "l" else rankS).get(t, {})
    base = dict(held.get(t, {})); base.update({"t": t, "side": side, "w": round(w * (1 if side == "l" else -1), 4), "usd": round(w * nav), "px0": round(px, 4), "d0": asof,
                 "shares": round(w * nav / px), "call": info.get("call", base.get("call")), "conv": info.get("score", base.get("conv")), "toc": info.get("toc", base.get("toc"))})
    pos.append(base)
B["segments"].append({"start": asof, "nav0": nav, "positions": pos, "trades": trades})
B["positions"] = pos
json.dump(B, open(root / "data/book.json", "w"), indent=1)
print("book rebalanced: new segment from", asof)
