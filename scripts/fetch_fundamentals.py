"""Fetch quarterly balance-sheet / cash-flow lines from Yahoo's fundamentals-timeseries endpoint.
Cached to cache/fund/<TICKER>.json (git-ignored)."""
import json, pathlib, time, urllib.request, concurrent.futures as cf, sys
root = pathlib.Path(__file__).resolve().parents[1]
cache = root / "cache" / "fund"; cache.mkdir(parents=True, exist_ok=True)
TYPES = ["quarterlyCashCashEquivalentsAndShortTermInvestments", "quarterlyCashAndCashEquivalents",
         "quarterlyOtherShortTermInvestments", "quarterlyLongTermInvestments", "quarterlyTotalDebt",
         "quarterlyOrdinarySharesNumber", "quarterlyShareIssued", "quarterlyNetIncome", "quarterlyOperatingCashFlow",
         "quarterlyFreeCashFlow", "quarterlyTotalRevenue", "quarterlyDilutedAverageShares",
         "quarterlyIssuanceOfCapitalStock"]
def get(tk):
    url = ("https://query2.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/"
           f"{tk.replace('.','-')}?type={','.join(TYPES)}&period1=1690000000&period2=1800000000")
    for a in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as r: j = json.loads(r.read())
            out = {}
            for res in j["timeseries"]["result"] or []:
                ty = res["meta"]["type"][0]
                vals = [v for v in res.get(ty) or [] if v]
                out[ty.replace("quarterly", "")] = {v["asOfDate"]: v["reportedValue"]["raw"] for v in vals}
            (cache/f"{tk}.json").write_text(json.dumps(out)); return tk, "ok" if out else "empty"
        except Exception as e:
            time.sleep(2 + 3*a)
    return tk, "fail"
if __name__ == "__main__":
    ts = sys.argv[1:] or sorted({r["ticker"] for r in json.load(open(root/"data/data.json"))})
    with cf.ThreadPoolExecutor(6) as ex: res = dict(ex.map(get, ts))
    bad = {k: v for k, v in res.items() if v != "ok"}
    print(f"{len(ts)} tickers, {len(ts)-len(bad)} ok; problems: {bad}")
