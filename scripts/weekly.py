"""Weekly run (Nov 27 2026): refresh, close the loop, write a digest -> data/weekly-digest.md
Order: moves since the last review and 8-K scan (what changed before we reprice) -> fresh prices -> apply them -> overhang
-> build -> mark the paper book -> rebalance it by the rule -> mark again -> thesis watch -> freeze this week's expectations
-> grade post-mortems -> backtest -> why-lines -> full build (audit + stored-call sync) -> digest.
Run: python3 scripts/weekly.py            (about 25-40 minutes, mostly SEC and price fetches)
     python3 scripts/weekly.py --digest   (only rewrite the digest from what is on disk)"""
import json, subprocess, sys, pathlib, datetime as dt
root = pathlib.Path(__file__).resolve().parents[1]
def run(*a, t=2400):
    print("$", " ".join(a), flush=True)
    r = subprocess.run([sys.executable, *a], cwd=root, capture_output=True, text=True, timeout=t)
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    print("  ", tail if r.returncode == 0 else "FAILED: " + (r.stderr.strip().splitlines() or [""])[-1], flush=True)
    return r.returncode == 0, r.stdout
def set_asof():
    # the snapshot date = the latest XBI close in the price cache (snapshot_expect files are keyed by it)
    try:
        j = json.load(open(root / "cache/prices/XBI.json"))["chart"]["result"][0]
        d = max(dt.datetime.fromtimestamp(a, dt.timezone.utc).date() for a, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c).isoformat()
        A = json.load(open(root / "data/asof-baked.json")); A["snapshot"]["asof"] = d; json.dump(A, open(root / "data/asof-baked.json", "w"), ensure_ascii=False); print("   snapshot date", d)
    except Exception as e: print("   set_asof skipped:", e)
D_before = {r["ticker"]: r.get("call") for r in json.load(open(root / "data/data.json"))}
B_before = json.load(open(root / "data/book-marks.json")) if (root / "data/book-marks.json").exists() else {}
if "--digest" not in sys.argv:
    run("scripts/moves_since.py"); run("scripts/scan_8k.py")
    run("scripts/fetch_prices.py", t=3600); run("scripts/refresh_apply.py"); set_asof(); run("scripts/rebuild_priceq.py")
    run("scripts/fetch_targets.py", t=1200)  # analyst consensus targets (stockanalysis.com), Nov 27 2026
    run("scripts/trade_info.py", t=3600); run("scripts/fetch_13dg.py", t=3600); run("scripts/price_check.py", t=1800)
    run("scripts/overhang.py", t=3600)
    run("scripts/build.py", "--no-audit")
    run("scripts/stale_scan.py", t=3600); run("scripts/build.py", "--no-audit")
    run("scripts/mark_book.py"); ok, rb = run("scripts/rebalance_book.py"); run("scripts/mark_book.py")
    run("scripts/thesis_watch.py"); run("scripts/snapshot_expect.py"); run("scripts/postmortem.py")
    run("scripts/backtest_calls.py"); run("scripts/explain_moves.py", t=3600)
    run("scripts/build.py")
# ---- digest
D = {r["ticker"]: r for r in json.load(open(root / "data/data.json"))}
MK = json.load(open(root / "data/book-marks.json")); last = MK["marks"][-1] if MK.get("marks") else {}
wk = next((m for m in reversed(MK.get("marks", [])) if m["d"] <= (dt.date.fromisoformat(last["d"]) - dt.timedelta(days=7)).isoformat()), MK["marks"][0] if MK.get("marks") else {}) if last else {}
RB = json.load(open(root / "data/rebalance.json")) if (root / "data/rebalance.json").exists() else {"trades": []}
TW = json.load(open(root / "data/thesis-watch.json")); PM = json.load(open(root / "data/postmortems.json"))
K8 = json.load(open(root / "data/8k.json")) if (root / "data/8k.json").exists() else {}
book = {p["t"] for p in MK.get("positions", [])}
def pc(v): return ("+" if v >= 0 else "−") + f"{abs(v) * 100:.1f}%"
L = [f"# Weekly digest, prices as of {last.get('d', '?')}", ""]
if last:
    wret = (1 + last["ret"]) / (1 + wk.get("ret", 0)) - 1 if wk else last["ret"]
    wx = (1 + (last["xbi"] or 0)) / (1 + (wk.get("xbi") or 0)) - 1 if wk else (last["xbi"] or 0)
    L += [f"**Paper book:** {pc(wret)} this week vs XBI {pc(wx)}; {pc(last['ret'])} since {MK['inception']} vs XBI {pc(last['xbi'] or 0)} (NAV ${last['nav']/1e6:.1f}M).", ""]
    pos = sorted(MK.get("positions", []), key=lambda p: -abs(p["pnl"]))[:4]
    if pos: L += ["Biggest contributors since the last rebalance: " + ", ".join(f"{p['t']} {'+' if p['pnl'] >= 0 else '−'}${abs(p['pnl'])/1e6:.1f}M ({pc(p['ret'])})" for p in pos), ""]
tr = RB.get("trades", [])
L += ["**Rebalance:** " + ("; ".join(f"{x['act']} {x['t']} {x['from']*100:.1f}%→{x['to']*100:.1f}% ({x['why']})" for x in tr) if tr else "no trades (every holding inside the buffer and at size)"), ""]
fl = [o for o in TW["rows"] if o["status"] != "intact"]
L += ["**Thesis watch:** " + ("; ".join(f"{o['t']} {o['status']}: {', '.join(o['flags'])}" for o in fl) if fl else "all 20 intact"), ""]
new_pm = [e for e in PM.get("events", []) if e["d"] >= (dt.date.today() - dt.timedelta(days=8)).isoformat()]
L += ["**Post-mortems graded this week:** " + ("; ".join(f"{e['t']} ({e['lab']}): {e['outcome']}, biggest day {pc(e['big'])}" + (" — we were right" if e['right'] else " — we were wrong" if e['right'] is False else "") for e in new_pm) if new_pm else "none (no event windows closed)"), ""]
ch = [(t, D_before.get(t), r.get("call")) for t, r in D.items() if D_before.get(t) and r.get("call") and D_before.get(t) != r.get("call")]
L += ["**Call changes:** " + (", ".join(f"{t} {a}→{b}" for t, a, b in ch[:25]) + (f" (+{len(ch)-25} more)" if len(ch) > 25 else "") if ch else "none"), ""]
news = [x for x in (K8.get("rows") or K8.get("filings") or []) if isinstance(x, dict) and x.get("t") in book]
if news: L += ["**8-Ks for book names:** " + "; ".join(f"{x.get('t')} {x.get('date','')}: {str(x.get('title') or x.get('headline') or '')[:90]}" for x in news[:10]), ""]
OV = json.load(open(root / "data/overhang.json"))["rows"]
raises = [(t, o["last_raise"]) for t, o in OV.items() if o.get("last_raise") and o["last_raise"]["date"] >= (dt.date.today() - dt.timedelta(days=8)).isoformat()]
if raises: L += ["**New raises this week:** " + "; ".join(f"{t} {('$%.0fM' % (lr['amt']/1e6)) if lr.get('amt') else ''} {lr['date']}" + (f" at {lr['disc']*100:+.0f}%" if lr.get('disc') is not None else "") for t, lr in raises[:15]), ""]
ST = json.load(open(root / "data/stale-flags.json")).get("flags", {}) if (root / "data/stale-flags.json").exists() else {}
L += ["**Possibly stale inputs (held out of the book until updated):** " + ("; ".join(f"{t} {v[0]['date']} {v[0]['what']}: {v[0]['headline'][:80]}" for t, v in ST.items()) if ST else "none"), ""]
PCK = json.load(open(root / "data/price-check.json")).get("rows", []) if (root / "data/price-check.json").exists() else []
pf = [o for o in PCK if o.get("flag")]
if pf: L += ["**Price-data flags:** " + "; ".join(f"{o['t']}: {o['flag'][:70]}" for o in pf[:10]), ""]
(root / "data/weekly-digest.md").write_text("\n".join(L))
print("\n".join(L))
