"""Per-company call history for the company card: every frozen call set on file, with the price at the time.
Sources: Sep 12 snapshot, Oct 13 memo (printed names only), every ledger/*.json. Writes data/callhist-data.json."""
import json, re, pathlib, datetime as dt, bisect
root = pathlib.Path(__file__).resolve().parents[1]
def close(tk, d):
    f = root/"cache/prices"/f"{tk}.json"
    if not f.exists(): return None
    j = json.load(open(f))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
    p = [(dt.datetime.fromtimestamp(t, dt.timezone.utc).date(), c) for t, c in zip(j.get("timestamp") or [], q.get("close") or []) if c]
    ds = [x[0] for x in p]; i = bisect.bisect_right(ds, d) - 1
    return round(p[i][1], 2) if i >= 0 else None
H = {}
def add(tk, date, call, src, price=None):
    if not tk or not call: return
    H.setdefault(tk, []).append({"d": date, "c": call, "src": src, "p": price if price is not None else close(tk, dt.date.fromisoformat(date))})
s = (root/"biotech_idea_snapshot.html").read_text(encoding="utf-8")
for r in json.loads(re.search(r"const SIMPLE_ROWS=(\[.*?\]);\s*\n", s, re.S).group(1)): add(r["ticker"], "2026-09-11", r["call"], "Sep 12 snapshot")
M = json.load(open(root/"data/memo-baked.json"))["months"]
for mk, m in M.items():
    fr = m.get("frozen") or m; d = (m.get("asof") or mk + "-15")[:10]
    for l in fr.get("longs") or []: add(l["ticker"], d, l.get("call") or "LONG", mk + " memo: highest-conviction long")
for f in sorted((root/"ledger").glob("*.json")):
    L = json.load(open(f)); d = f.name[:10]
    for r in L["rows"]: add(r["ticker"], d, r["call"], "ledger " + f.stem, r.get("price"))
for tk in H: H[tk].sort(key=lambda x: x["d"])
json.dump(H, open(root/"data/callhist-data.json", "w"), separators=(",", ":"))
print(len(H), "tickers;", sum(len(v) for v in H.values()), "entries; e.g. CRSP", H.get("CRSP"))
