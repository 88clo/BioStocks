"""Daily scan of 8-K filings (and their press-release exhibits) for every covered company -> data/8k.json.
Built Nov 25 2026 after Kymera's Nov 23 readout went unnoticed: the 8-K with the press release is filed the same day.
For each company: data.sec.gov submissions -> 8-Ks filed since --since (default: 10 days ago); for each, the filing index
-> the EX-99.x exhibit (the press release) -> its headline. Flags filings whose headline or items look like news we must
absorb (topline/data, FDA action, approval, CRL, deal, offering, delisting, executive change).
Run daily: python3 scripts/scan_8k.py && python3 scripts/build.py   (~3-5 minutes)"""
import json, re, sys, time, html, pathlib, datetime as dt, urllib.request
root = pathlib.Path(__file__).resolve().parents[1]
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
since = sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else (dt.date.today() - dt.timedelta(days=10)).isoformat()
tk = root / "cache/13dg/company_tickers.json"
if not tk.exists(): tk.parent.mkdir(parents=True, exist_ok=True); tk.write_text(get("https://www.sec.gov/files/company_tickers.json"))
CIK = {v["ticker"]: v["cik_str"] for v in json.loads(tk.read_text()).values()}
D = [r for r in json.load(open(root / "data/data.json")) if r.get("ta") != "Acquired / Inactive"]
ITEMS = {"1.01": "material agreement", "1.02": "agreement ended", "2.01": "acquisition/disposal", "2.02": "results", "2.05": "restructuring",
         "2.06": "impairment", "3.01": "listing notice", "3.02": "unregistered sale", "5.02": "officer/director change", "5.03": "charter change",
         "5.07": "shareholder vote", "7.01": "Reg FD / press release", "8.01": "other events", "9.01": "exhibits"}
NEWS = re.compile(r"topline|top-line|primary endpoint|met |did not meet|positive|negative|results from|data from|phase [123]|pivotal|FDA|approv|complete response|CRL|PDUFA|BLA|NDA|clinical hold|acqui|merger|license|collaborat|offering|private placement|pricing|delist|Nasdaq|reverse split|chief executive|CEO|resign|restructur|workforce|strategic alternatives|wind[- ]down", re.I)
CACHE = root / "cache/8k"; CACHE.mkdir(parents=True, exist_ok=True)
rows = []
for i, r in enumerate(D):
    t = r["ticker"]; cik = CIK.get(t)
    if not cik: continue
    s = get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")
    if not s: continue
    rc = json.loads(s)["filings"]["recent"]
    for j, form in enumerate(rc["form"]):
        if rc["filingDate"][j] < since: break
        if form not in ("8-K", "8-K/A"): continue
        acc = rc["accessionNumber"][j]; a = acc.replace("-", ""); cf = CACHE / f"{a}.json"
        if cf.exists():
            rows.append(json.load(open(cf))); continue
        items = rc.get("items", [""] * len(rc["form"]))[j] or ""
        base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a}/"
        title, exurl = "", None
        idx = get(base + "index.json")
        if idx:
            files = [f["name"] for f in json.loads(idx)["directory"]["item"]]
            ex = [f for f in files if re.search(r"ex-?99|ex99|exhibit99|pressrelease|press", f, re.I) and f.lower().endswith((".htm", ".html", ".txt"))]
            if ex:
                exurl = base + ex[0]; doc = get(exurl) or ""
                txt = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", doc)))).strip()
                # drop the exhibit preamble ("EX-99.1 2 file.htm EX-99.1 Exhibit 99.1"), then cut the headline at the first bullet or dateline
                txt = re.sub(r"^(?:\s*(?:EX-99\.?\d*|Exhibit 99\.?\d*|\d+|\S+\.html?|EXHIBIT 99\.?\d*)\s+)+", "", txt, flags=re.I)
                cut = re.split(r" [●•▪] | (?:[A-Z][a-z]+ ){0,2}[A-Z][a-z]+, (?:[A-Z][a-z]+\.?|[A-Z]{2}),? (?:[A-Z][a-z]+\.? )?\(?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d| -- | – ", txt, maxsplit=1)
                title = cut[0].strip()[:220]
                if len(title.split()) < 7: title = txt[:200].strip()
        if not title and idx:
            body = get(base + rc["primaryDocument"][j]) or ""
            bt = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)))
            m = re.search(r"Item (1\.01|2\.01|2\.05|3\.01|5\.02|8\.01)\.?\s+[^.]{3,140}\.\s+(.{30,260}?\.)(?= [A-Z]|$)", bt)
            if m: title = ("Item " + m.group(1) + ": " + m.group(2)).strip()[:240]
        prim = rc["primaryDocument"][j]
        rec = {"t": t, "date": rc["filingDate"][j], "form": form, "items": items, "item_l": [ITEMS.get(x, x) for x in items.split(",") if x and x != "9.01"],
               "title": title[:260], "url": exurl or (base + prim), "news": bool(NEWS.search(title) or re.search(r"\b(1\.01|2\.01|3\.01|5\.02|8\.01)\b", items))}
        json.dump(rec, open(cf, "w")); rows.append(rec)
    if i % 50 == 0: print(i, t, len(rows), flush=True)
rows.sort(key=lambda x: (x["date"], x["t"]), reverse=True)
json.dump({"since": since, "built": dt.date.today().isoformat(), "rows": rows}, open(root / "data/8k.json", "w"), separators=(",", ":"))
print(f"{len(rows)} 8-Ks since {since}; {sum(r['news'] for r in rows)} flagged as news")
for r in [x for x in rows if x["news"]][:25]: print(f"  {r['date']} {r['t']:6s} [{r['items']}] {r['title'][:120]}")
