"""Freeze the paper book from the live page's calls -> data/book.json (+ a dated copy in ledger/).
Run at each refresh after build.py: python3 tests/freeze_book.py [--date YYYY-MM-DD]
Rules (Nov 27 2026; replaces the Nov 25 book, kept as data/book-v1-2026-11-25.json):
  The paper book is a frozen copy of Record › Top-20 book, so the Brief, Companies filters, What's next highlights and the
  tracked book are one list. NAV $250M. 15 longs + 5 shorts ranked on the conviction score plus a tilt for the next catalyst.
  Weight = base (longs 5%, shorts 3% of NAV) x conviction (score / median pick, 0.6-1.6) x catalyst skew (0.8-1.3) x vol
  scaler (0.6-1.4), capped at 8% / 5% of NAV, 10 days of 20% ADV and 4.9% of the company; names that cannot reach 1% of NAV
  are skipped. Long-biased by design (no XBI hedge); P&L is shown against XBI and the average covered stock.
  Entry = latest close in the price cache. No costs, borrow or dividends."""
import asyncio, json, sys, pathlib, datetime as dt
from playwright.async_api import async_playwright
root = pathlib.Path(__file__).resolve().parents[1]
JS = r"""(()=>{const R=TOP20();return R.P.map(p=>{const r=p.x.r,o=p.o,ti=TI(p.x.t)||{};return {t:p.x.t,side:p.side>0?'l':'s',call:r.call,conv:Math.round(p.score*100)/100,u:p.x.u,mc:r.mc,price:r.price,adv:ti.adv20,vol:ti.vol60,days10:ti.days10,w0:p.w,bind:p.bind,
   toc:o?{ev:Math.round(o.ev*1000)/1000,d:o.d,lab:o.lab,ty:o.ty,e:o.e}:null,why:(r.th_view||r.call_reason||'').slice(0,240),name:r.name,ta:r.ta};});})()"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox']); pg = await b.new_page()
        await pg.goto('file://' + str(root / 'index.html')); await pg.wait_for_timeout(2500)
        await pg.evaluate("navGo('companies','co')"); await pg.wait_for_timeout(1500)
        C = await pg.evaluate(JS); await b.close()
    return C
C = asyncio.run(main())
import statistics as st
def last_close(t):
    f = root / "cache/prices" / f"{t}.json"
    if not f.exists(): return None, None
    j = json.load(open(f))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    pts = [(tt, c) for tt, c in zip(j["timestamp"], q["close"]) if c]
    return (dt.datetime.fromtimestamp(pts[-1][0], dt.timezone.utc).date().isoformat(), pts[-1][1]) if pts else (None, None)
NAV = 2.5e8  # a $250M sleeve: the size a new PM is likely to run first, and one these small caps can absorb
vols = [c["vol"] for c in C if c.get("vol")]; mv = st.median(vols) if vols else .8
book = []
for c in C:
    w = c["w0"]; d0, px = last_close(c["t"])
    if not px: continue
    c["capped"] = c.get("bind") if c.get("bind") != "conviction" else None
    c.update({"w": round(w * (1 if c["side"] == "l" else -1), 4), "usd": round(w * NAV), "px0": round(px, 4), "d0": d0, "shares": round(w * NAV / px)})
    book.append(c)
d = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else max(c["d0"] for c in book)
lw = sum(c["w"] for c in book if c["w"] > 0); sw = -sum(c["w"] for c in book if c["w"] < 0)
out = {"inception": d, "nav": NAV, "long": round(lw, 4), "short": round(sw, 4), "gross": round(lw + sw, 4), "net": round(lw - sw, 4),
       "rules": __doc__.split("Rules (Nov 27 2026")[1].strip(), "positions": book}
json.dump(out, open(root / "data/book.json", "w"), indent=1)
(root / "ledger").mkdir(exist_ok=True); json.dump(out, open(root / f"ledger/book-{d}.json", "w"), indent=1)
print(f"book {d}: {sum(c['w']>0 for c in book)} longs {lw:.0%}, {sum(c['w']<0 for c in book)} shorts {sw:.0%}, gross {lw+sw:.0%}, net {lw-sw:+.0%}")
for c in book: print(f"  {c['t']:6s} {c['side']} {c['w']*100:+5.1f}% conv {c['conv']} {c.get('capped','')}")
