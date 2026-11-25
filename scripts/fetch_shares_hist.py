"""Quarterly + annual share counts from Yahoo's fundamentals-timeseries endpoint, for point-in-time market caps
(Record > What worked). Cached to cache/shares/<TICKER>.json (git-ignored); summarized into data/shares-hist.json."""
import json, pathlib, time, urllib.request, concurrent.futures as cf, sys
root = pathlib.Path(__file__).resolve().parents[1]
cache = root / "cache" / "shares"; cache.mkdir(parents=True, exist_ok=True)
TYPES = ["quarterlyOrdinarySharesNumber", "annualOrdinarySharesNumber", "quarterlyShareIssued", "annualShareIssued",
         "quarterlyDilutedAverageShares", "annualDilutedAverageShares"]
def get(tk):
    f = cache / f"{tk}.json"
    if f.exists() and f.stat().st_size > 20: return tk, "cached"
    url = ("https://query2.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/"
           f"{tk.replace('.','-')}?type={','.join(TYPES)}&period1=1690000000&period2=1800000000")
    for a in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as r: j = json.loads(r.read())
            out = {}
            for res in j["timeseries"]["result"] or []:
                ty = res["meta"]["type"][0]
                out[ty] = {v["asOfDate"]: v["reportedValue"]["raw"] for v in (res.get(ty) or []) if v}
            f.write_text(json.dumps(out)); return tk, "ok" if out else "empty"
        except Exception as e:
            time.sleep(3 + 4 * a)
    return tk, "fail"
def summarize():
    out = {}
    for f in cache.glob("*.json"):
        d = json.loads(f.read_text()); pts = {}
        for ty in TYPES:  # earliest type in the list wins for a date
            for k, v in (d.get(ty) or {}).items():
                if v and k not in pts: pts[k] = v
        if pts: out[f.stem] = dict(sorted(pts.items()))
    (root / "data" / "shares-hist.json").write_text(json.dumps(out, separators=(",", ":")))
    print("shares-hist.json:", len(out), "tickers")
if __name__ == "__main__":
    ts = sys.argv[1:] or sorted({r["ticker"] for r in json.load(open(root / "data/data.json"))})
    with cf.ThreadPoolExecutor(3) as ex: res = dict(ex.map(get, ts))
    bad = {k: v for k, v in res.items() if v not in ("ok", "cached")}
    print(f"{len(ts)} tickers, {len(ts)-len(bad)} ok; problems: {len(bad)} {list(bad.items())[:10]}")
    summarize()
