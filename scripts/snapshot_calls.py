"""Load index.html headless, let the page's own rules compute calls/picks, and dump them.
Usage: snapshot_calls.py OUT.json [index.html]. This is the call ledger writer: the page is
the single source of truth for the call grid, so nothing is re-implemented in Python."""
import json, sys, pathlib, hashlib
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parents[1]
out = pathlib.Path(sys.argv[1]); html = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else root/"index.html")
JS = """() => { try{ if(typeof refreshCalls==='function') refreshCalls(); }catch(e){}
 return DATA.map(r => ({ticker:r.ticker, name:r.nick||r.name, ta:r.ta, stage:r.stage, drug:r.drug,
   indication:r.indication, price:r.price, mc:r.mc, call:r.call,
   up:(typeof callUpPct==='function'?callUpPct(r):null), pv:(typeof pvVal==='function'?pvVal(r):null),
   top:(typeof topPick==='function'?topPick(r):false), short:(typeof shortPick==='function'?shortPick(r):false),
   elite:(typeof eliteLong==='function'?!!eliteLong(r):false),
   effsig:r.effsig, diffscore:r.diffscore, pos:r.pos, peak:r.peak_sales, cash:r.cash, runway_q:r.runway_q,
   cat:r.catalyst, cat_date:r.cat_date, pitch:r.pitch_concise||r.pitch||''})); }"""
errs = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(html.resolve().as_uri(), wait_until="load", timeout=120000); pg.wait_for_timeout(2500)
    rows = pg.evaluate(JS); b.close()
body = json.dumps(rows, ensure_ascii=False, sort_keys=True)
out.write_text(json.dumps({"names": len(rows), "sha256": hashlib.sha256(body.encode()).hexdigest(), "rows": rows}, ensure_ascii=False, indent=0))
from collections import Counter
print(out.name, len(rows), Counter(r["call"] for r in rows).most_common(), "top", sum(r["top"] for r in rows), "short", sum(r["short"] for r in rows), "elite", sum(r["elite"] for r in rows))
print("page errors:", errs[:5] or "none")
