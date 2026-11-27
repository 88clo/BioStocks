"""Catalyst post-mortems -> data/postmortems.json (Nov 27 2026).
For every event in a frozen expectation snapshot (data/expect/*.json, earliest snapshot that saw it) whose window has closed:
  - what we expected: probability of a good outcome (pe), move if good (up) / bad (dn), expected return (ev), our call;
  - what happened: the biggest one-day move inside the event window (+3 trading days), the company's 8-K filed near it
    (press-release headline), and the stock's move from the snapshot to 3 trading days after the window, vs XBI;
  - the grade: outcome read from the move (good if the biggest day was up 10%+, bad if down 10%+, else unclear), whether our
    direction was right, and the size of the move vs what we expected.
Calibration: by event type, average pe vs the share that turned out good, and average |move| vs our expected |move|.
Events with no 8-K and no big day are listed as "no clear news yet" (dates slip; the next snapshot carries them forward)."""
import json, re, pathlib, datetime as dt, glob, html, time, urllib.request, statistics as st
root = pathlib.Path(__file__).resolve().parents[1]
UA = {"User-Agent": "BioStocks research dashboard (88clo) contact@example.com"}
CIK = {v["ticker"]: v["cik_str"] for v in json.load(open(root / "cache/13dg/company_tickers.json")).values()}
def get(url):
    for k in range(3):
        try:
            time.sleep(0.12); return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "ignore")
        except Exception as e:
            if "404" in str(e): return None
            time.sleep(1.5)
    return None
def series(t):
    f = root / f"cache/prices/{t}.json"
    try:
        j = json.load(open(f))["chart"]["result"][0]
        return [(dt.datetime.fromtimestamp(a, dt.timezone.utc).date(), c) for a, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c]
    except Exception: return []
XB = series("XBI"); LAST = XB[-1][0] if XB else dt.date.today()
def filings(t):
    cik = CIK.get(t)
    if not cik: return []
    f = root / f"cache/8k/sub_{cik}.json"
    if not f.exists() or time.time() - f.stat().st_mtime > 86400 * 3:
        s = get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")
        if s: f.write_text(s)
    try: rc = json.load(open(f))["filings"]["recent"]
    except Exception: return []
    return [{"cik": cik, "acc": rc["accessionNumber"][i], "date": rc["filingDate"][i], "items": (rc.get("items") or [""] * len(rc["form"]))[i] or ""} for i in range(len(rc["form"])) if rc["form"][i] in ("8-K", "6-K")]
def headline(f):
    a = f["acc"].replace("-", ""); cf = root / f"cache/8k/{a}.json"
    if cf.exists():
        try: return json.load(open(cf)).get("title", "")
        except Exception: pass
    base = f"https://www.sec.gov/Archives/edgar/data/{int(f['cik'])}/{a}/"; title = ""
    idx = get(base + "index.json")
    if idx:
        files = [x["name"] for x in json.loads(idx)["directory"]["item"]]
        ex = [x for x in files if re.search(r"ex-?99|ex99|press", x, re.I) and x.lower().endswith((".htm", ".html", ".txt"))]
        if ex:
            doc = get(base + ex[0]) or ""
            txt = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", doc)))).strip()
            title = re.split(r" [—–] | -- ", txt[:400])[0][:200]
    json.dump({"title": title, "date": f["date"], "url": base, "v2": 1}, open(cf, "w")); return title
snaps = sorted(glob.glob(str(root / "data/expect/*.json")))
seen, out = {}, []
for fn in snaps:
    S = json.load(open(fn))
    for r in S["rows"]:
        e = r.get("ev")
        if not e or not e.get("d"): continue
        key = (r["t"], e.get("e", "")[:60])
        if key in seen: continue
        seen[key] = (S["asof"], r)
for (t, _), (asof, r) in seen.items():
    e = r["ev"]; d1 = dt.date.fromisoformat(e["d"][:10]); d0 = dt.date.fromisoformat(asof)
    if d1 > LAST: continue                                  # window still open
    P = series(t)
    if not P: continue
    win = [(d, c) for d, c in P if d0 <= d]
    idx_end = next((i for i, (d, c) in enumerate(win) if d > d1), len(win) - 1)
    win = win[:min(len(win), idx_end + 4)]
    if len(win) < 3: continue
    days = [(win[i][0], win[i][1] / win[i - 1][1] - 1) for i in range(1, len(win))]
    bd, br = max(days, key=lambda x: abs(x[1]))
    tot = win[-1][1] / win[0][1] - 1
    xb = [c for d, c in XB if d0 <= d <= win[-1][0]]; xr = xb[-1] / xb[0] - 1 if len(xb) > 1 else 0
    near = [f for f in filings(t) if -1 <= (dt.date.fromisoformat(f["date"]) - bd).days <= 3]
    hl = next((h for h in (headline(f) for f in near) if h), "")
    outcome = "good" if br >= 0.10 else "bad" if br <= -0.10 else "unclear"
    exp_dir = 1 if (e.get("ev") or 0) > 0 else -1 if (e.get("ev") or 0) < 0 else 0
    right = None if outcome == "unclear" or exp_dir == 0 else ((outcome == "good") == (exp_dir > 0))
    exp_abs = (e["pe"] * abs(e["up"]) + (1 - e["pe"]) * abs(e["dn"])) if e.get("pe") is not None and e.get("up") is not None else None
    out.append({"t": t, "asof": asof, "event": e.get("e", ""), "lab": e.get("lab"), "ty": e.get("ty"), "d": e["d"][:10], "call": r.get("call"), "rank": r.get("rank"),
                "pe": e.get("pe"), "up": e.get("up"), "dn": e.get("dn"), "ev": e.get("ev"), "big_day": bd.isoformat(), "big": round(br, 4), "move": round(tot, 4),
                "xbi": round(xr, 4), "headline": hl[:200], "outcome": outcome, "right": right, "exp_abs": round(exp_abs, 4) if exp_abs is not None else None,
                "news": bool(hl) or abs(br) >= 0.10})
cal = {}
for ty in sorted({o["ty"] for o in out if o["ty"]}):
    L = [o for o in out if o["ty"] == ty and o["outcome"] != "unclear" and o["pe"] is not None]
    if not L: continue
    cal[ty] = {"n": len(L), "pe": round(st.mean(o["pe"] for o in L), 3), "good": round(sum(o["outcome"] == "good" for o in L) / len(L), 3),
               "exp_abs": round(st.mean(o["exp_abs"] for o in L if o["exp_abs"] is not None), 3) if any(o["exp_abs"] is not None for o in L) else None,
               "act_abs": round(st.mean(abs(o["big"]) for o in L), 3), "right": round(sum(1 for o in L if o["right"]) / max(1, sum(1 for o in L if o["right"] is not None)), 3)}
out.sort(key=lambda o: o["d"], reverse=True)
json.dump({"built": dt.date.today().isoformat(), "snapshots": [pathlib.Path(s).stem for s in snaps], "events": out, "calibration": cal},
          open(root / "data/postmortems.json", "w"), separators=(",", ":"))
print(len(snaps), "snapshot(s);", len(out), "events graded;", sum(1 for o in out if o["news"]), "with news;", {k: (v["n"], v["pe"], v["good"]) for k, v in cal.items()})
