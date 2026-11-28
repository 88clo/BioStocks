"""Fetch daily price history (5y) for every ticker in the dashboard from Yahoo's chart endpoint.
Raw responses are cached in cache/prices/<TICKER>.json (git-ignored)."""
import json, pathlib, time, urllib.request, concurrent.futures as cf, sys
root = pathlib.Path(__file__).resolve().parents[1]
cache = root / "cache" / "prices"; cache.mkdir(parents=True, exist_ok=True)
def tickers():
    t = {r["ticker"] for r in json.load(open(root/"data/data.json"))}
    t |= {r["ticker"] for r in json.load(open(root/"data/parked-data.json"))["rows"]}
    t |= set(json.load(open(root/"data/portfolio-baked.json")))
    t |= set(json.load(open(root/"data/priceq-baked.json"))["prices"])
    ipo = json.load(open(root/"data/ipo-data.json"))
    t |= {r["ticker"] for r in ipo.get("recent", []) + ipo.get("upcoming", []) if r.get("ticker")}
    return sorted(x for x in t if x)
def yq(tk): return tk.replace(".", "-")
def get(tk, rng="5y"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yq(tk)}?range={rng}&interval=1d&events=splits"
    for a in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BioStocks-dashboard/1.0 (weekly research script; low volume)"})  # honest UA (Nov 27 2026); no browser impersonation
            with urllib.request.urlopen(req, timeout=20) as r: body = r.read()
            j = json.loads(body)
            if j["chart"]["result"]:
                (cache/f"{tk}.json").write_bytes(body); return tk, "ok"
            return tk, "empty"
        except urllib.error.HTTPError as e:
            if e.code == 404: return tk, "404"
            time.sleep(2 + 3*a)
        except Exception as e:
            time.sleep(2 + 3*a)
    return tk, "fail"
if __name__ == "__main__":
    ts = sys.argv[1:] or tickers()
    res = {}
    with cf.ThreadPoolExecutor(2) as ex:  # gentle: 2 at a time (Nov 27 2026)
        for tk, st in ex.map(get, ts): res[tk] = st
    bad = {k: v for k, v in res.items() if v != "ok"}
    print(f"{len(ts)} tickers, {len(ts)-len(bad)} ok; problems: {bad}")
