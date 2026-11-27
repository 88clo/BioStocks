"""Mark the paper book to market every day since inception -> data/book-marks.json.
Reads data/book.json (frozen by tests/freeze_book.py; rebalanced by scripts/rebalance_book.py) and the daily price cache.
The book is a chain of segments: each rebalance closes the old positions at that day's close and opens the new ones with
the NAV carried forward, so returns compound across rebalances. Within a segment share counts are fixed. P&L per day per
position; NAV, long / short contribution and XBI over the same days. Price-only: no costs, borrow, dividends or interest."""
import json, pathlib, datetime as dt
root = pathlib.Path(__file__).resolve().parents[1]
B = json.load(open(root / "data/book.json"))
SEG = B.get("segments") or [{"start": B["inception"], "nav0": B["nav"], "positions": B["positions"]}]
def series(t):
    f = root / "cache/prices" / f"{t}.json"
    if not f.exists(): return {}
    j = json.load(open(f))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    return {dt.datetime.fromtimestamp(a, dt.timezone.utc).date().isoformat(): c for a, c in zip(j["timestamp"], q["close"]) if c}
inc = B["inception"]; NAV0 = B["nav"]
S = {}
for sg in SEG:
    for p in sg["positions"]:
        if p["t"] not in S: S[p["t"]] = series(p["t"])
XB = series("XBI")
days = sorted(d for d in XB if d >= inc)
marks, cum_l, cum_s, cum_h, pos = [], 0.0, 0.0, 0.0, []
for k, sg in enumerate(SEG):
    end = SEG[k + 1]["start"] if k + 1 < len(SEG) else "9999-12-31"
    sd = [d for d in days if sg["start"] <= d <= end]
    last = {p["t"]: p["px0"] for p in sg["positions"]}; base_l, base_s, base_h = cum_l, cum_s, cum_h
    for d in sd:
        pl_l = pl_s = pl_h = 0.0; pos = []
        for p in sg["positions"]:
            px = S[p["t"]].get(d, last[p["t"]]); last[p["t"]] = px
            sh = p["shares"] * (1 if p["w"] > 0 else -1); pl = sh * (px - p["px0"])
            if p["side"] == "h": pl_h += pl
            elif p["w"] > 0: pl_l += pl
            else: pl_s += pl
            pos.append([p["t"], round(px, 4), round(pl), p])
        cum_l, cum_s, cum_h = base_l + pl_l, base_s + pl_s, base_h + pl_h
        nav = NAV0 + cum_l + cum_s + cum_h
        m = {"d": d, "nav": round(nav), "ret": round(nav / NAV0 - 1, 5), "long": round(cum_l), "short": round(cum_s), "hedge": round(cum_h),
             "xbi": round(XB[d] / XB[inc] - 1, 5) if inc in XB else None, "seg": k}
        if marks and marks[-1]["d"] == d: marks[-1] = m          # rebalance day: the new segment starts at the old close
        else: marks.append(m)
contrib = sorted([{"t": t, "side": p["side"], "w": p["w"], "px0": p["px0"], "px": px, "pnl": pl, "ret": round(px / p["px0"] - 1, 4), "since": SEG[-1]["start"]}
                  for t, px, pl, p in pos], key=lambda x: -x["pnl"]) if marks else []
json.dump({"inception": inc, "asof": days[-1] if days else inc, "segments": [{"start": s["start"], "nav0": s["nav0"], "n": len(s["positions"]), "trades": s.get("trades", [])} for s in SEG],
           "marks": marks, "positions": contrib}, open(root / "data/book-marks.json", "w"), separators=(",", ":"))
print(f"marked {len(marks)} days from {inc} over {len(SEG)} segment(s); NAV {marks[-1]['nav']/1e6:.1f}M ({marks[-1]['ret']*100:+.2f}%) vs XBI {marks[-1]['xbi']*100:+.2f}%" if marks else "no marks yet")
