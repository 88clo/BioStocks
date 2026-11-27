"""Freeze what we expect from every name's next lead-program event -> data/expect/<date>.json (Nov 27 2026).
One row per covered name: call, price, conviction, Top-20 rank, and the next event with our probability of a good outcome
(pe), the move we expect if it goes well (up) or badly (dn), the expected return (ev), its date window and type.
These frozen expectations are what scripts/postmortem.py later grades against what happened. Run weekly (scripts/weekly.py)."""
import json, pathlib, datetime as dt
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parents[1]
JS = r"""(()=>{const T=TOP20(),rk={};T.allL.forEach((p,i)=>rk[p.x.t]='L'+(i+1));T.allS.forEach((p,i)=>rk[p.x.t]='S'+(i+1));const C=CONVICTION().m;
 return DATA.filter(r=>r.ta!=='Acquired / Inactive').map(r=>{const o=tocOf(r.ticker),c=C[r.ticker];return {t:r.ticker,call:r.call,price:r.price,mc:r.mc,rank:rk[r.ticker]||null,
  conv:c?{l:c.l,s:c.s}:null,sc:(function(){r._sc=undefined;const q=scen(r);return q?{p:q.p??null,pImp:q.pImp??null,pu:q.pu??null,Vs:q.Vs??null,Vf:q.Vf??null,ER:q.ER,ERo:q.ERo??null,W:q.W,bin:q.binary,stage:r.stage}:null;})(),ev:o?{pe:o.pe,pm:(o.up>0&&o.dn<0)?-o.dn/(o.up-o.dn):null,up:o.up,dn:o.dn,ev:o.ev,d:o.d,lab:o.lab,e:o.e,ty:o.ty,view:o.view}:null};});})()"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg = b.new_page()
    pg.goto((root / "index.html").resolve().as_uri(), wait_until="load", timeout=120000); pg.wait_for_timeout(3000)
    R = pg.evaluate(JS); b.close()
asof = json.load(open(root / "data/asof-baked.json"))["snapshot"]["asof"]
d = root / "data/expect"; d.mkdir(exist_ok=True)
json.dump({"asof": asof, "taken": dt.date.today().isoformat(), "rows": R}, open(d / f"{asof}.json", "w"), separators=(",", ":"))
print("expectations frozen for", len(R), "names as of", asof, "->", f"data/expect/{asof}.json")
