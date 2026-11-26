"""Freeze the paper book from the live page's calls -> data/book.json (+ a dated copy in ledger/).
Run at each refresh after build.py: python3 tests/freeze_book.py [--date YYYY-MM-DD]
Rules (Nov 25 2026):
  NAV $250M. Longs: priority longs + Strong Buys; shorts: priority shorts + Strong Shorts. Must take a $10M position in <= 10 days.
  Conviction: priority rank 1-5 = 1.5, other priority = 1.25, strong call = 1.0; +0.25 if our expected return into the next
  lead-program event is >= +25% (longs) / <= -25% (shorts). Top 20 longs and 15 shorts by conviction, then model upside.
  Weight = base (longs 4%, shorts 3% of NAV) x conviction x vol scaler (median vol / own vol, 0.5-1.5),
  capped at 6% of NAV, at 5 days of 20% ADV, and at 2% of the company's market cap. Entry = latest close in the price cache.
  A short XBI hedge holds net exposure at +20%, so P&L is mostly stock selection. No costs, borrow or dividends."""
import asyncio, json, sys, pathlib, datetime as dt
from playwright.async_api import async_playwright
root = pathlib.Path(__file__).resolve().parents[1]
JS = r"""(()=>{const PR=SYN_PRIORITY(),A=SYN.rows(),X={};A.forEach(x=>X[x.t]=x);
 const out=[];const add=(t,side)=>{const x=X[t];if(!x||out.find(o=>o.t===t))return;const r=x.r,ti=TI(t),o=tocOf(t),p=PR[t];
   if(!ti||ti.days10==null||ti.days10>10)return;
   let conv=p?(p.rank<=5?1.5:1.25):1.0;if(o&&(side==='l'?o.ev>=.25:o.ev<=-.25))conv+=.25;
   out.push({t,side,call:r.call,conv,pri:p?p.rank:null,u:x.u,mc:r.mc,price:r.price,adv:ti.adv20,vol:ti.vol60,days10:ti.days10,
     toc:o?{ev:Math.round(o.ev*1000)/1000,d:o.d,lab:o.lab,ty:o.ty,e:o.e}:null,why:(r.th_view||r.call_reason||'').slice(0,240),name:r.name,ta:r.ta});};
 Object.keys(PR).forEach(t=>add(t,PR[t].side));A.forEach(x=>{if(x.r.call==='STRONG BUY')add(x.t,'l');if(x.r.call==='STRONG SHORT')add(x.t,'s');});
 return out;})()"""
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
for side, n, base in (("l", 20, .04), ("s", 15, .03)):
    L = sorted([c for c in C if c["side"] == side], key=lambda c: (-c["conv"], -(c["u"] or 0) if side == "l" else (c["u"] or 0)))[:n]
    for c in L:
        vs = min(1.5, max(.5, mv / c["vol"])) if c.get("vol") else 1
        w = base * c["conv"] * vs
        caps = {"6% NAV": .06, "5 days of 20% ADV": 5 * .2 * c["adv"] / NAV, "2% of market cap": .02 * c["mc"] / NAV}
        lim = min(caps, key=caps.get)
        if caps[lim] < w: w = caps[lim]; c["capped"] = lim
        d0, px = last_close(c["t"])
        if not px: continue
        c.update({"w": round(w * (1 if side == "l" else -1), 4), "usd": round(w * NAV), "px0": round(px, 4), "d0": d0, "shares": round(w * NAV / px)})
        book.append(c)
d = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else max(c["d0"] for c in book)
lw = sum(c["w"] for c in book if c["w"] > 0); sw = -sum(c["w"] for c in book if c["w"] < 0)
# XBI hedge: bring net exposure down to +20% so the book's P&L is mostly stock selection, not the sector
if lw - sw > .2:
    hw = round(lw - sw - .2, 4); d0, px = last_close("XBI")
    book.append({"t": "XBI", "side": "h", "call": "HEDGE", "conv": None, "w": -hw, "usd": round(hw * NAV), "px0": round(px, 4), "d0": d0, "shares": round(hw * NAV / px), "why": "Sector hedge: short XBI to hold net exposure at +20%."})
    sw += hw
out = {"inception": d, "nav": NAV, "long": round(lw, 4), "short": round(sw, 4), "gross": round(lw + sw, 4), "net": round(lw - sw, 4),
       "rules": __doc__.split("Rules (Nov 25 2026):")[1].strip(), "positions": book}
json.dump(out, open(root / "data/book.json", "w"), indent=1)
(root / "ledger").mkdir(exist_ok=True); json.dump(out, open(root / f"ledger/book-{d}.json", "w"), indent=1)
print(f"book {d}: {sum(c['w']>0 for c in book)} longs {lw:.0%}, {sum(c['w']<0 for c in book)} shorts {sw:.0%}, gross {lw+sw:.0%}, net {lw-sw:+.0%}")
for c in book: print(f"  {c['t']:6s} {c['side']} {c['w']*100:+5.1f}% conv {c['conv']} {c.get('capped','')}")
