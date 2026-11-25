"""Fetch 13F-HR holdings for every specialist fund from SEC EDGAR -> cache/13f/ and data/13f-raw.json.

For each fund in SPECIALIST_INVESTORS (pipeline/template.html): find its CIK (EDGAR company search), list its 13F-HR filings
(data.sec.gov submissions), and download the last N quarters' information tables (www.sec.gov Archives).
Keeps every holding (issuer, CUSIP, shares, value, put/call). Mapping CUSIPs to our tickers is done in scripts/build_13f.py.
SEC fair-access: descriptive User-Agent, <= 8 requests a second. Re-runs reuse the cache."""
import json, re, time, pathlib, urllib.request, urllib.parse, sys
root = pathlib.Path(__file__).resolve().parents[1]
CACHE = root / "cache/13f"; CACHE.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "BioStocks research dashboard (88clo) contact@example.com"}
NQ = int(sys.argv[1]) if len(sys.argv) > 1 else 9
_last = [0.0]
def get(url, binary=False):
    for k in range(4):
        wait = 0.13 - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        _last[0] = time.time()
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
            return b if binary else b.decode("utf-8", "ignore")
        except Exception as e:
            if "404" in str(e): return None
            time.sleep(1.5 * (k + 1))
    return None

tpl = (root / "pipeline/template.html").read_text(encoding="utf-8")
SPEC = json.loads(re.search(r"const SPECIALIST_INVESTORS=new Set\((\[.*?\])\);", tpl).group(1))
cikf = CACHE / "ciks.json"; CIK = json.load(open(cikf)) if cikf.exists() else {}

def norm(n): return re.sub(r"[^a-z0-9 ]", "", re.sub(r",? (llc|l\.?p\.?|lp|inc\.?|ltd\.?|limited|corp\.?|co\.?|ag|plc|gp|l\.l\.c\.)\b", " ", n.lower())).split()
def find_cik(name):
    words = norm(name); q = " ".join(words[:3]) or name
    x = get("https://www.sec.gov/cgi-bin/browse-edgar?" + urllib.parse.urlencode({"company": q, "type": "13F-HR", "dateb": "", "owner": "include", "count": "40", "action": "getcompany", "output": "atom"}))
    if not x: return None
    m = re.search(r"<cik>(\d+)</cik>", x)
    if m and "<company-info>" in x and x.count("<entry>") <= 1 + x.count("<filing-type>"):
        return m.group(1).lstrip("0")
    # several companies: pick the best name match
    best, bs = None, 0
    for cik, nm in re.findall(r"<cik>(\d+)</cik>.*?<name>(.*?)</name>", x, re.S):
        a, b = set(words), set(norm(nm))
        sc = len(a & b) / max(1, len(a | b))
        if sc > bs: best, bs = cik.lstrip("0"), sc
    return best if bs >= 0.5 else (m.group(1).lstrip("0") if m else None)

def parse_info(xml):
    xml = re.sub(r"<(/?)\w+:", r"<\1", xml); out = []
    for blk in re.findall(r"<infoTable>(.*?)</infoTable>", xml, re.S):
        g = lambda k: (re.search(r"<%s>(.*?)</%s>" % (k, k), blk, re.S) or [None, ""])[1].strip()
        if g("putCall"): continue
        if (g("sshPrnamtType") or "SH") != "SH": continue
        try: out.append([g("nameOfIssuer"), g("cusip").upper(), float(g("sshPrnamt") or 0), float(g("value") or 0)])
        except ValueError: pass
    return out

done = 0
for name in SPEC:
    if name not in CIK:
        CIK[name] = find_cik(name); json.dump(CIK, open(cikf, "w"), indent=0)
    cik = CIK[name]
    if not cik: print("no CIK:", name); continue
    sub = get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")
    if not sub: print("no submissions:", name); continue
    s = json.loads(sub); r = s["filings"]["recent"]
    fil = [(r["reportDate"][i], r["accessionNumber"][i], r["filingDate"][i]) for i, f in enumerate(r["form"]) if f == "13F-HR"]
    seen = set(); keep = []
    for per, acc, fd in fil:            # newest first; one filing per period
        if per in seen: continue
        seen.add(per); keep.append((per, acc, fd))
        if len(keep) >= NQ: break
    fdir = CACHE / str(cik); fdir.mkdir(exist_ok=True)
    for per, acc, fd in keep:
        f = fdir / f"{per}.json"
        if f.exists(): continue
        a = acc.replace("-", ""); idx = get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a}/index.json")
        if not idx: continue
        items = [i["name"] for i in json.loads(idx)["directory"]["item"]]
        xmls = [i for i in items if i.lower().endswith(".xml") and "primary_doc" not in i.lower()]
        rows = None
        for xn in xmls:
            x = get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a}/{xn}")
            if x and "infoTable" in x: rows = parse_info(x); break
        if rows is not None: json.dump({"period": per, "filed": fd, "acc": acc, "rows": rows}, open(f, "w"))
    done += 1
    if done % 10 == 0: print(done, "funds done", flush=True)
print("finished", done, "funds")
