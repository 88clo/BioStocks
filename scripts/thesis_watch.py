"""Thesis-break watch for the paper book -> data/thesis-watch.json (Nov 27 2026).
For each book name: the condition that would make us wrong (from the thesis: 'what would change our mind' / memo 'wrong if'),
its move since entry vs XBI, and every 8-K since entry with its headline, sorted into:
  BREAK  words that usually end or badly dent a thesis: discontinued, terminated, did not meet / failed, complete response
         letter, clinical hold, going concern, delisting, CEO / CMO departure, restructuring or wind-down, strategic alternatives;
  CHECK  words that change the setup without ending it: offering / placement, delay or postpone, amendment, guidance cut, recall;
  plus a price check (down 25%+ vs XBI since entry) and a timing check (the next event's window has closed with no news).
Status: 'break?' (a BREAK filing), 'check' (CHECK filing, price or timing flag), 'intact'. A flag is a prompt to reread the
thesis, not a sell signal: the point is to tell 'the thesis broke' apart from 'only the price fell'."""
import json, re, pathlib, datetime as dt, time, html, urllib.request
root = pathlib.Path(__file__).resolve().parents[1]
UA = {"User-Agent": "BioStocks research dashboard (88clo) contact@example.com"}
CIK = {v["ticker"]: v["cik_str"] for v in json.load(open(root / "cache/13dg/company_tickers.json")).values()}
B = json.load(open(root / "data/book.json")); TH = json.load(open(root / "data/theses.json"))["theses"]
D = {r["ticker"]: r for r in json.load(open(root / "data/data.json"))}
try: V2 = json.load(open(root / "data/v2-data.json"))
except Exception: V2 = {}
def get(url):
    for k in range(3):
        try:
            time.sleep(0.12); return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "ignore")
        except Exception as e:
            if "404" in str(e): return None
            time.sleep(1.5)
    return None
def series(t):
    try:
        j = json.load(open(root / f"cache/prices/{t}.json"))["chart"]["result"][0]
        return [(dt.datetime.fromtimestamp(a, dt.timezone.utc).date(), c) for a, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c]
    except Exception: return []
def filings(t, since):
    cik = CIK.get(t)
    if not cik: return []
    f = root / f"cache/8k/sub_{cik}.json"
    if not f.exists() or time.time() - f.stat().st_mtime > 86400 * 2:
        s = get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")
        if s: f.write_text(s)
    try: rc = json.load(open(f))["filings"]["recent"]
    except Exception: return []
    return [{"cik": cik, "acc": rc["accessionNumber"][i], "date": rc["filingDate"][i], "items": (rc.get("items") or [""] * len(rc["form"]))[i] or ""}
            for i in range(len(rc["form"])) if rc["form"][i] in ("8-K", "6-K") and rc["filingDate"][i] >= since]
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
            title = re.split(r" [—–] | -- ", html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", doc))).strip()[:400])[0][:200]
    json.dump({"title": title, "date": f["date"], "url": base, "v2": 1}, open(cf, "w")); return title
BRK = re.compile(r"discontinu|terminat|did not meet|not meet (?:its|the) primary|failed to|complete response|\bCRL\b|clinical hold|going concern|delist|chief executive officer.{0,40}(?:resign|depart|step)|(?:resign|depart).{0,40}chief (?:executive|medical)|restructur|wind[- ]down|strategic alternatives|reduction in force", re.I)
CHK = re.compile(r"offering|private placement|pricing|delay|postpone|amend|guidance|recall|warning letter|refuse to file|extension of (?:the )?PDUFA", re.I)
ITEM_BRK = {"2.05": "restructuring / layoffs (item 2.05)", "3.01": "listing notice (item 3.01)", "5.02": "officer change (item 5.02)"}
XB = series("XBI"); LAST = XB[-1][0]
out = []
for p in B["positions"]:
    t = p["t"]; d0 = p.get("d0") or B["inception"]; r = D.get(t, {}); th = TH.get(t, {})
    wrong = th.get("th_cat") or (V2.get(t) or {}).get("wcm") or th.get("th_miss") or r.get("eff_caveat") or ""
    m = re.search(r"(?:would change our mind|wrong if|we would (?:exit|cover|go back)[^.]*)[^.]*\.?", wrong, re.I)
    S = series(t); px0 = p["px0"]; px = S[-1][1] if S else px0
    xb0 = next((c for d, c in reversed(XB) if d.isoformat() <= d0), XB[0][1])
    vs = (px / px0 - 1) - (XB[-1][1] / xb0 - 1)
    if p["side"] == "s": vs = -vs
    flags, items = [], []
    for f in filings(t, d0):
        h = re.sub(r"^(?:exhibit\s?99\.?\d*|ex-?99\.?\d*|exhibit\d+)\s*", "", headline(f), flags=re.I); it = [ITEM_BRK[x] for x in f["items"].split(",") if x in ITEM_BRK]
        kind = "break" if (h and BRK.search(h)) or any("restructuring" in x for x in it) else "check" if (h and CHK.search(h)) or it else "news"
        items.append({"date": f["date"], "headline": h[:200], "items": it, "kind": kind})
    lbl = lambda x: (x["items"][0] if x["items"] else x["headline"][:90]) + " (" + x["date"] + ")"
    for x in items:
        if x["kind"] == "break": flags.append("thesis-break language: " + lbl(x))
        elif x["kind"] == "check": flags.append("setup change: " + lbl(x))
    if vs <= -0.25: flags.append("%s %.0f%% vs XBI since entry" % ("down" if p["side"] == "l" else "up", abs(vs) * 100))
    toc = p.get("toc") or {}
    if toc.get("d") and toc["d"][:10] < LAST.isoformat() and not any(x["date"] >= toc["d"][:10] for x in items):
        flags.append("next event window (%s) closed with no 8-K" % (toc.get("lab") or toc["d"][:10]))
    status = "break?" if any(x["kind"] == "break" for x in items) else "check" if flags else "intact"
    out.append({"t": t, "side": p["side"], "d0": d0, "px0": px0, "px": px, "vs_xbi": round(vs, 4), "wrong_if": (m.group(0) if m else wrong)[:300], "status": status, "flags": flags, "filings": items[-6:]})
json.dump({"asof": LAST.isoformat(), "rows": out}, open(root / "data/thesis-watch.json", "w"), separators=(",", ":"))
print("thesis watch:", {s: sum(1 for o in out if o["status"] == s) for s in ("break?", "check", "intact")})
for o in out:
    if o["status"] != "intact": print("  ", o["t"], o["status"], "|", "; ".join(o["flags"]))
