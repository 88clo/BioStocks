"""Mark the paper book to market every day since inception -> data/book-marks.json.
Reads data/book.json (positions frozen by tests/freeze_book.py) and the daily price cache (run fetch_prices.py or
moves_since.py first). Fixed share counts from inception (no rebalancing until the next freeze); P&L per day per position;
NAV, long and short contribution, and XBI over the same days. Price-only: no costs, borrow, dividends or cash interest."""
import json, pathlib, datetime as dt
root = pathlib.Path(__file__).resolve().parents[1]
B = json.load(open(root / "data/book.json"))
def series(t):
    f = root / "cache/prices" / f"{t}.json"
    if not f.exists(): return {}
    j = json.load(open(f))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    return {dt.datetime.fromtimestamp(a, dt.timezone.utc).date().isoformat(): c for a, c in zip(j["timestamp"], q["close"]) if c}
inc = B["inception"]; NAV0 = B["nav"]
S = {p["t"]: series(p["t"]) for p in B["positions"]}
XB = series("XBI")
days = sorted(d for d in XB if d >= inc)
marks, last = [], {p["t"]: p["px0"] for p in B["positions"]}
for d in days:
    pnl_l = pnl_s = pnl_h = 0.0; pos = []
    for p in B["positions"]:
        px = S[p["t"]].get(d, last[p["t"]]); last[p["t"]] = px
        sh = p["shares"] * (1 if p["w"] > 0 else -1)
        pl = sh * (px - p["px0"])
        if p["side"] == "h": pnl_h += pl
        elif p["w"] > 0: pnl_l += pl
        else: pnl_s += pl
        pos.append([p["t"], round(px, 4), round(pl)])
    nav = NAV0 + pnl_l + pnl_s + pnl_h
    marks.append({"d": d, "nav": round(nav), "ret": round(nav / NAV0 - 1, 5), "long": round(pnl_l), "short": round(pnl_s), "hedge": round(pnl_h),
                  "xbi": round(XB[d] / XB[inc] - 1, 5) if inc in XB else None})
lastpos = {t: (px, pl) for t, px, pl in pos} if marks else {}
contrib = sorted([{"t": p["t"], "side": p["side"], "w": p["w"], "px0": p["px0"], "px": lastpos[p["t"]][0], "pnl": lastpos[p["t"]][1],
                   "ret": round((lastpos[p["t"]][0] / p["px0"] - 1), 4)} for p in B["positions"]], key=lambda x: -x["pnl"]) if marks else []
json.dump({"inception": inc, "asof": days[-1] if days else inc, "marks": marks, "positions": contrib}, open(root / "data/book-marks.json", "w"), separators=(",", ":"))
print(f"marked {len(marks)} days from {inc}; NAV {marks[-1]['nav']/1e6:.1f}M ({marks[-1]['ret']*100:+.2f}%) vs XBI {marks[-1]['xbi']*100:+.2f}%" if marks else "no marks yet")
