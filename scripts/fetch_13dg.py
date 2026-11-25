"""5%+ holders of every company we track, from Schedule 13D/13G filings (SEC EDGAR) -> data/13dg.json.

13F filings miss venture funds, crossovers that file only 13D/G, insiders and pharma partners. Anyone owning more than 5%
of a class must file a Schedule 13D (active) or 13G (passive); since Dec 2024 these are structured XML ("SCHEDULE 13D/G").
For each company: list its 13D/G filings from the last 30 months (data.sec.gov submissions), keep each filer's latest,
read the reporting person(s) and percent of class. Older text filings (SC 13D/G) are parsed with regexes (approximate).
A holder whose latest filing shows < 5% has sold below the threshold and is dropped. Cached in cache/13dg/."""
import json, re, time, pathlib, urllib.request, datetime as dt, html
root = pathlib.Path(__file__).resolve().parents[1]
C = root / "cache/13dg"; C.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "BioStocks research dashboard (88clo) contact@example.com"}
_last = [0.0]
def get(url):
    for k in range(4):
        w = 0.13 - (time.time() - _last[0])
        if w > 0: time.sleep(w)
        _last[0] = time.time()
        try: return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "ignore")
        except Exception as e:
            if "404" in str(e): return None
            time.sleep(1.5 * (k + 1))
    return None

tk = C / "company_tickers.json"
if not tk.exists(): tk.write_text(get("https://www.sec.gov/files/company_tickers.json"))
CIK = {v["ticker"]: v["cik_str"] for v in json.loads(tk.read_text()).values()}
D = [r for r in json.load(open(root / "data/data.json")) if r.get("ta") != "Acquired / Inactive"]
cut = (dt.date.today() - dt.timedelta(days=915)).isoformat()

def parse_xml(x):
    out = []
    for blk in re.findall(r"<coverPageHeaderReportingPersonDetails>(.*?)</coverPageHeaderReportingPersonDetails>", x, re.S) or [x]:
        n = re.search(r"<reportingPersonName>(.*?)</reportingPersonName>", blk, re.S)
        p = re.search(r"<(?:percentOfClass|classPercent)>\s*([\d.]+)", blk)
        a = re.search(r"<(?:aggregateAmountOwned|reportingPersonBeneficiallyOwnedAggregateNumberOfShares)>\s*([\d.,]+)", blk)
        if n: out.append([html.unescape(n.group(1).strip()), float(p.group(1)) if p else None, float(a.group(1).replace(",", "")) if a else None])
    return out
def parse_txt(x):
    t = re.sub(r"<[^>]+>", " ", x); t = html.unescape(re.sub(r"\s+", " ", t))
    out = []
    for m in re.finditer(r"NAMES? OF REPORTING PERSONS?\.?\s*(?:I\.R\.S\.[^A-Z]{0,80})?(?:\(ENTITIES ONLY\))?\s*([A-Z0-9][^\n]{2,80}?)\s+(?:\d\s|2\.|CHECK)", t, re.I):
        name = m.group(1).strip(" .:")
        rest = t[m.end(): m.end() + 2500]
        p = re.search(r"PERCENT OF CLASS REPRESENTED BY AMOUNT IN ROW \(?\d+\)?\s*:?\s*([\d.]+)\s*%", rest, re.I)
        out.append([name, float(p.group(1)) if p else None, None])
    return out[:4]

res = {}
for i, r in enumerate(D):
    t = r["ticker"]; cik = CIK.get(t)
    if not cik: continue
    f = C / f"{t}.json"
    if f.exists() and (time.time() - f.stat().st_mtime) < 20 * 86400:
        res[t] = json.load(open(f)); continue
    s = get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")
    if not s: continue
    rc = json.loads(s)["filings"]["recent"]; seen = {}
    for j, form in enumerate(rc["form"]):
        if not re.match(r"(SC |SCHEDULE )13[DG]", form) or rc["filingDate"][j] < cut: continue
        filer = rc["accessionNumber"][j].split("-")[0]
        if filer in seen: continue                       # newest first: first seen = latest by that filer (or filing agent)
        seen[filer] = (form, rc["filingDate"][j], rc["accessionNumber"][j], rc["primaryDocument"][j])
    holders = []
    for filer, (form, fd, acc, doc) in list(seen.items())[:25]:
        a = acc.replace("-", "")
        if form.startswith("SCHEDULE"):
            x = get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a}/primary_doc.xml"); rows = parse_xml(x) if x else []
        else:
            x = get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a}/{doc}"); rows = parse_txt(x) if x else []
        ENT = re.compile(r"\b(LLC|L\.?L\.?C|LP|L\.P|Inc|Corp|Ltd|Limited|plc|AG|SA|N\.V|GmbH|Fund|Funds|Trust|Partners|Capital|Management|Advisors|Advisers|Investments?|Holdings?|Group|Ventures?|Company|Co\.|Foundation|Bank|Asset|Master|Associates|Pharma|Therapeutics|Biotech)\b", re.I)
        ents = [x for x in rows if ENT.search(x[0])]
        rows = (ents[:1] if ents else rows[:1])
        for name, pct, sh in rows:
            holders.append({"name": name, "pct": pct, "sh": sh, "form": form.replace("SCHEDULE ", "").replace("SC ", ""), "date": fd})
    # one row per reporting person (latest), drop those below 5%
    best = {}
    for h in sorted(holders, key=lambda h: h["date"]):
        best[re.sub(r"\(\d+\)|[^a-z]|(inc|llc|lp|ltd|plc|corp|the)$", "", h["name"].lower())[:24]] = h
    out = [h for h in best.values() if h["pct"] is None or h["pct"] >= 5]
    out.sort(key=lambda h: -(h["pct"] or 0))
    json.dump(out, open(f, "w")); res[t] = out
    if i % 25 == 0: print(i, t, len(out), flush=True)
json.dump({"built": dt.date.today().isoformat(), "holders": res}, open(root / "data/13dg.json", "w"), separators=(",", ":"))
print("done", len(res), "companies;", sum(len(v) for v in res.values()), "5%+ holder rows")
