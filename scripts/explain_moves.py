"""One-line causes for the best/worst stocks shown on Record › What worked -> data/move-why.json.
For every example card the page shows (all dimensions, quarters and hold periods; listed by the page's WW_CARDS hook):
  1. the window = close of the quarter before the start -> close at the end of the holding period (or today),
  2. the biggest one-day moves in that window from daily closes (cache/prices), and XBI over the same window,
  3. the company's 8-Ks filed within a few days of those big days (SEC submissions + the press-release exhibit headline,
     cached in cache/8k), and the 8-K that best explains the move (news-flagged first, then the closest date).
The line reads e.g. "+64% on Mar 3 '26: Positive topline Phase 3 results for X (8-K) · XBI +4%". When no filing sits near the
big day, the line says so and gives the share of the window's move that came on that day and XBI's move.
Hand-written drivers (retro-data / retro-2025) still take priority on the page.
Run: python3 scripts/build.py --no-audit && python3 scripts/explain_moves.py && python3 scripts/build.py   (~10 min first time)"""
import json, re, sys, time, html, pathlib, datetime as dt, asyncio, urllib.request
root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "scripts"))
UA = {"User-Agent": "BioStocks research dashboard (88clo) contact@example.com"}
_last = [0.0]
def get(url):
    for k in range(3):
        w = 0.12 - (time.time() - _last[0])
        if w > 0: time.sleep(w)
        _last[0] = time.time()
        try: return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "ignore")
        except Exception as e:
            if "404" in str(e): return None
            time.sleep(1.5 * (k + 1))
    return None

async def cards():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg = await b.new_page()
        await pg.goto("file://" + str(root / "index.html")); await pg.wait_for_timeout(2500)
        await pg.evaluate("navGo('record','track')"); await pg.wait_for_timeout(1500)
        C = await pg.evaluate("WW_CARDS()"); await b.close(); return C
C = asyncio.run(cards())
W = {}
for c in C: W.setdefault((c["t"], c["ql"], c["hold"]), c)
print(len(C), "cards,", len(W), "unique windows")

def qend(q):  # '1Q25' -> date of quarter end
    n, y = int(q[0]), 2000 + int(q[2:]); m = 3 * n
    return dt.date(y, m, [31, 30, 30, 31][n - 1])
def qadd(q, k):
    n, y = int(q[0]), int(q[2:]); i = (n - 1) + k; return f"{i % 4 + 1}Q{y + i // 4}"
def series(t):
    f = root / f"cache/prices/{t}.json"
    if not f.exists(): return None
    try: j = json.load(open(f))["chart"]["result"][0]
    except Exception: return None
    cl = (j["indicators"].get("adjclose") or [{}])[0].get("adjclose") or j["indicators"]["quote"][0]["close"]
    return [(dt.datetime.fromtimestamp(ts, dt.timezone.utc).date(), c) for ts, c in zip(j["timestamp"], cl) if c]
XBI = series("XBI")
def ret_between(S, d0, d1):
    a = [c for d, c in S if d <= d0]; b2 = [c for d, c in S if d <= d1]
    return (b2[-1] / a[-1] - 1) if a and b2 else None

tk = root / "cache/13dg/company_tickers.json"
CIK = {v["ticker"]: v["cik_str"] for v in json.loads(tk.read_text()).values()}
PARK = {}
try:
    for r in json.load(open(root / "data/parked-data.json")).get("rows", []): PARK[r.get("ticker") or r.get("t")] = r
except Exception: pass
SUB = {}
def filings(t):
    if t in SUB: return SUB[t]
    cik = CIK.get(t); out = []
    if cik:
        cf = root / f"cache/8k/sub_{cik}.json"
        if cf.exists() and time.time() - cf.stat().st_mtime < 86400 * 3: s = cf.read_text()
        else:
            s = get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")
            if s: cf.write_text(s)
        if s:
            rc = json.loads(s)["filings"]["recent"]
            for j, form in enumerate(rc["form"]):
                if form in ("8-K", "8-K/A", "6-K"):
                    out.append({"cik": cik, "acc": rc["accessionNumber"][j], "date": rc["filingDate"][j], "items": (rc.get("items") or [""] * len(rc["form"]))[j] or "", "prim": rc["primaryDocument"][j], "form": form})
    SUB[t] = out; return out
NEWS = re.compile(r"topline|top-line|primary endpoint|met |did not meet|positive|negative|results|data|phase [123]|pivotal|FDA|approv|complete response|CRL|PDUFA|BLA|NDA|clinical hold|acqui|merger|license|collaborat|offering|private placement|pricing|delist|reverse split|chief executive|CEO|resign|restructur|workforce|strategic alternatives|wind[- ]down|discontinu|halt|terminat", re.I)
JUNKRE = r"corporate presentation|for immediate release|media contact|investor contact|contact:|inquiries|forward ?[- ] ?looking|filed herewith|presentation dated|annual healthcare conference|no assurance|^\S+_\S+"
def headline(t, f):
    a = f["acc"].replace("-", ""); cf = root / f"cache/8k/{a}.json"
    if cf.exists():
        try:
            o = json.load(open(cf))
            if not (re.search(JUNKRE, o.get("title", ""), re.I) and not o.get("v2")): return o.get("title", "")
        except Exception: pass
    base = f"https://www.sec.gov/Archives/edgar/data/{int(f['cik'])}/{a}/"; title = ""
    idx = get(base + "index.json")
    if idx:
        files = [x["name"] for x in json.loads(idx)["directory"]["item"]]
        ex = [x for x in files if re.search(r"ex-?99|ex99|exhibit99|pressrelease|press", x, re.I) and x.lower().endswith((".htm", ".html", ".txt"))]
        if ex:
            doc = get(base + ex[0]) or ""
            txt = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", doc)))).strip()
            txt = re.sub(r"^(?:\s*(?:EX-99\.?\d*|Exhibit 99\.?\d*|\d+|\S+\.html?|EXHIBIT 99\.?\d*)\s+)+", "", txt, flags=re.I)
            cut = re.split(r" [●•▪] | (?:[A-Z][a-z]+ ){0,2}[A-Z][a-z]+, (?:[A-Z][a-z]+\.?|[A-Z]{2}),? (?:[A-Z][a-z]+\.? )?\(?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d| -- | – ", txt, maxsplit=1)
            title = cut[0].strip()[:220]
            if len(title.split()) < 7: title = txt[:200].strip()
            if re.search(JUNKRE, title, re.I):
                sents = re.split(r"(?<=[.!?])\s+", txt[:6000])
                BOIL = r"risks|uncertaint|guarantee|forward|statements|estimates and other|this presentation|undue reliance|assurance|safe harbor|securities act"
                ok = [x for x in sents if 30 < len(x) < 400 and not re.search(JUNKRE, x, re.I) and not re.search(BOIL, x, re.I)]
                hit = next((x for x in ok if re.search(r"\bannounced\b", x)), "") or next((x for x in ok if re.search(r"topline|top-line|results|approv|acqui|agreement|FDA|data|offering", x, re.I)), "")
                title = re.sub(r"^.*?\b(?:today )?announced(?: that)?\s+", "", hit)[:220] if hit else ""
        if not title:
            body = get(base + f["prim"]) or ""
            bt = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)))
            m = re.search(r"Item (1\.01|2\.01|2\.05|3\.01|5\.02|8\.01)\.?\s+[^.]{3,140}\.\s+(.{30,260}?\.)(?= [A-Z]|$)", bt)
            if m: title = ("Item " + m.group(1) + ": " + m.group(2)).strip()[:240]
    json.dump({"t": t, "date": f["date"], "items": f["items"], "title": title[:260], "url": base, "v2": 1}, open(cf, "w"))
    return title
ITEMS = {"1.01": "material agreement", "2.01": "deal closed", "2.02": "quarterly results", "2.05": "restructuring", "3.01": "listing notice", "3.02": "share sale", "5.02": "management change", "5.07": "shareholder vote", "8.01": "company news filed (no press-release headline)"}
def tidy(t, title, name):
    s = re.sub(r"\s+", " ", title or "").strip()
    s = re.sub(r"(Exhibit|EX)[- ]?99\.?\d*[:\s]*", "", s, flags=re.I)
    s = re.sub(r"[\u200b\u00a0\ufeff]", " ", s); s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^[A-Za-z]*\d{3,}\S*\s+", "", s)
    s = re.sub(r"^(Document|PRESS RELEASE|News Release|FOR IMMEDIATE RELEASE)\s+", "", s, flags=re.I)
    s = re.sub(r"^(PRESS RELEASE|FOR IMMEDIATE RELEASE)\s+", "", s, flags=re.I)
    s = re.sub(r"^Item \d\.\d\d:\s*(On [A-Z][a-z]+\.? \d{1,2}, \d{4},?\s*)?(the Company|[A-Z][\w.,& ]{1,40}?)\s+(announced|issued a press release announcing|reported|entered into|received)\s+(that\s+)?", "", s)
    s = re.split(r",? (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2}, \d{4}", s)[0] if not re.match(r"^(On |Item )", s) else s
    if re.search(r"corporate presentation|for immediate release|media contact|investor contact|contact:|inquiries|forward ?[- ] ?looking|filed herewith|presentation dated|annual healthcare conference|no assurance|^\S+_\S+", s, re.I): return ""
    s = re.sub(r"^(?:[A-Z][a-z]+\.? \d{1,2}, \d{4},?\s*)", "", s)
    s = re.sub(r"\s+[A-Z]{3,}(?: [A-Z]{2,})*$", "", s)
    s = re.split(r" ?[—–] | -- |(?<=[a-z0-9)]) [A-Z]{3,}(?: [A-Z]{2,})*, (?:[A-Z][a-z]+\.? )?(?:[A-Z][a-z]+|[A-Z]{2,})?,? ?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|(?<=[a-z0-9)]) [A-Z]{3,}(?: [A-Z]{2,})*, ", s)[0]
    for nm in [name, (name or "").split(" ")[0]]:
        if nm and len(nm) > 2: s = re.sub(r"^" + re.escape(nm) + r"[\w.,&\- ]{0,30}?(?= (Announces|Reports|Provides|Receives|Enters|Presents|Completes|Prices|Achieves|Highlights|Shares|Initiates|to ))", "", s, flags=re.I)
    s = re.sub(r"^\s*(Announces|Reports|Provides|Highlights|Shares)\s+", "", s, flags=re.I).strip(" :-–,")
    s = re.sub(r"[\s,]+[A-Z]{3,}(?: [A-Z]{2,})*,?$", "", s).strip(" :-–,")
    if re.search(r"VOLUNTARY ANNOUNCEMENT|HONG KONG STOCK EXCHANGE", s, re.I): return ""
    s = s[:1].upper() + s[1:]
    return (s[:115].rsplit(" ", 1)[0] + "…") if len(s) > 115 else s
def fmtd(d): return d.strftime("%b %-d '%y")
def P(x):
    v = round(x * 100)
    return ("+" if v > 0 else "−" if v < 0 else "") + str(abs(v)) + "%"

out = {}
today = dt.date.today()
for n, ((t, ql, hold), c) in enumerate(sorted(W.items())):
    S = series(t)
    d0 = qend(qadd(ql, -1)); d1 = min(qend(qadd(ql, hold - 1)), today)
    key = f"{t}|{ql}|{hold}"
    if not S: continue
    win = [(d, cl) for d, cl in S if d0 <= d <= d1]
    if len(win) < 5: continue
    days = [(win[i][0], win[i][1] / win[i - 1][1] - 1) for i in range(1, len(win))]
    tot = c["ret"]; xr = ret_between(XBI, d0, d1) if XBI else None
    # the days that moved it most in the direction of the total
    sgn = 1 if tot >= 0 else -1
    big = sorted(days, key=lambda x: -x[1] * sgn)[:2]
    fl = [f for f in filings(t) if d0.isoformat() <= f["date"] <= (d1 + dt.timedelta(days=3)).isoformat()]
    parts = []; xday = dict((d, r) for d, r in ((XBI[i][0], XBI[i][1] / XBI[i - 1][1] - 1) for i in range(1, len(XBI)))) if XBI else {}
    used = []
    for bd, br in big:
        if br * sgn < 0.08: continue
        near = [f for f in fl if -1 <= (dt.date.fromisoformat(f["date"]) - bd).days <= 3]
        best, bt = None, ""
        for f in sorted(near, key=lambda f: abs((dt.date.fromisoformat(f["date"]) - bd).days)):
            ttl = tidy(t, headline(t, f), c.get("name"))
            if ttl and (NEWS.search(ttl) or re.search(r"\b(1\.01|2\.01|8\.01)\b", f["items"])): best, bt = f, ttl; break
            if best is None and (ttl or re.search(r"\b(1\.01|2\.01|2\.02|2\.05|3\.01|3\.02|5\.02|8\.01)\b", f["items"])): best, bt = f, ttl
        xd = xday.get(bd)
        if best and any(best['acc'] == u for u in used): break
        if best: used.append(best['acc'])
        if best:
            txt = bt or ", ".join(ITEMS.get(x, x) for x in best["items"].split(",") if x and x not in ("9.01", "7.01")) or "8-K filed"
            if re.search(r"positive|met |achiev|success", txt, re.I) and br < -0.08: txt += " (sold off on the news)"
            parts.append(f"{P(br)} on {fmtd(bd)}: {txt}")
        elif xd is not None and abs(xd) >= 0.03 and xd * br > 0:
            parts.append(f"{P(br)} on {fmtd(bd)}, a sector-wide day (XBI {P(xd)})")
        elif not parts:
            parts.append(f"{P(br)} on {fmtd(bd)}, no company filing that week")
        if len(parts) == 2 or abs(big[0][1]) >= abs(tot) * .6: break
    lead = ""
    if xr is not None and abs(tot) < 0.6 and abs(tot - xr) <= max(0.1, abs(tot) * 0.35):
        lead = f"Mostly the sector (XBI {P(xr)})"
    elif not parts or all("no company filing" in x for x in parts):
        lead = "No single news event: a steady " + ("climb" if tot >= 0 else "slide") + (f" vs XBI {P(xr)}" if xr is not None else "")
    if lead:
        parts = [lead] + [x for x in parts if "no company filing" not in x][:1]
        line = " · ".join(parts)
    else:
        line = " · ".join(parts) + (f" · XBI {P(xr)}" if xr is not None else "")
    if PARK.get(t) and re.search(r"acqui", str(PARK[t].get("reason", "")), re.I) and tot > 0.2 and not re.search(r"acqui|merger|tender", line, re.I):
        line += f" · since {str(PARK[t]['reason'])[:70]}"
    out[key] = line
    if n % 100 == 0: print(n, key, line[:150], flush=True)
json.dump({"built": today.isoformat(), "n": len(out), "why": out}, open(root / "data/move-why.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "explanations written to data/move-why.json")
