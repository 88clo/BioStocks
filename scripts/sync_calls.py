"""Write the page's live calls back into data/data.json (call, call_reason, call_synced), so scripts and offline
comparisons that read data.json never see stale calls. The page stays the source of truth: it recomputes calls at load.
Run by build.py after each build (skipped with --no-audit)."""
import json, pathlib, datetime as dt
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg = b.new_page()
    pg.goto((root / "index.html").resolve().as_uri(), wait_until="load", timeout=120000); pg.wait_for_timeout(2500)
    L = pg.evaluate("Object.fromEntries(DATA.map(r=>[r.ticker,[r.call,r.th_view||r.call_reason||'']]))"); b.close()
path = root / "data/data.json"; D = json.load(open(path)); n = 0
for r in D:
    if r["ticker"] in L:
        c, why = L[r["ticker"]]
        if r.get("call") != c or r.get("call_reason") != why: n += 1
        r["call"], r["call_reason"], r["call_synced"] = c, why, dt.date.today().isoformat()
json.dump(D, open(path, "w"), ensure_ascii=False, separators=(",", ":"))
print("sync_calls:", n, "stored calls/reasons updated from the page")
