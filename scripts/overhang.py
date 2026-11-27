"""Financing overhang tracker -> data/overhang.json (Nov 26 2026).
From each company's SEC filing list (data.sec.gov submissions, cached in cache/8k/sub_<cik>.json):
  - shelf: latest S-3 / S-3ASR / F-3 (a shelf lets the company sell stock quickly); amount from the fee table when stated
  - ATM: latest prospectus supplement (424B5/424B3) that sets up an at-the-market program, with its size
  - last raise: latest priced deal (424B4/424B5/424B7 with a per-share price, or an 8-K item 3.02 private placement / PIPE),
    with gross size, price and discount to the prior close
Window: filings since Jan 1 2024. Documents are fetched once and cached (cache/overhang/<accession>.json)."""
import json, re, time, html, pathlib, urllib.request, datetime as dt
root = pathlib.Path(__file__).resolve().parents[1]
UA = {"User-Agent": "BioStocks research dashboard (88clo) contact@example.com"}
C = root / "cache/overhang"; C.mkdir(parents=True, exist_ok=True)
_last = [0.0]
def get(url, limit=None):
    for k in range(3):
        w = 0.12 - (time.time() - _last[0])
        if w > 0: time.sleep(w)
        _last[0] = time.time()
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30)
            b = r.read(limit) if limit else r.read()
            return b.decode("utf-8", "ignore")
        except Exception as e:
            if "404" in str(e): return None
            time.sleep(1.5 * (k + 1))
    return None
D = [r for r in json.load(open(root / "data/data.json")) if r.get("ta") != "Acquired / Inactive"]
CIK = {v["ticker"]: v["cik_str"] for v in json.load(open(root / "cache/13dg/company_tickers.json")).values()}
def subs(cik):
    f = root / f"cache/8k/sub_{cik}.json"
    if f.exists() and time.time() - f.stat().st_mtime < 86400 * 3: return json.load(open(f))
    s = get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")
    if s: f.write_text(s); return json.loads(s)
    return None
def text(cik, acc, prim):
    a = acc.replace("-", ""); f = C / f"{a}.json"
    if f.exists(): return json.load(open(f))["t"]
    raw = get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a}/{prim}", limit=400000) or ""
    t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", raw))))[:60000]
    json.dump({"t": t}, open(f, "w")); return t
def money(s):
    m = re.search(r"\$\s?([\d,]+(?:\.\d+)?)\s*(million|billion)?", s or "")
    if not m: return None
    v = float(m.group(1).replace(",", "")); u = m.group(2)
    return v * (1e9 if u == "billion" else 1e6 if u == "million" else 1)
def series(t):
    f = root / f"cache/prices/{t}.json"
    try:
        j = json.load(open(f))["chart"]["result"][0]
        return [(dt.datetime.fromtimestamp(ts, dt.timezone.utc).date(), c) for ts, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c]
    except Exception: return []
out = {}
for n, r in enumerate(D):
    t = r["ticker"]; cik = CIK.get(t); o = {}
    S = subs(cik) if cik else None
    if not S: out[t] = {"err": "no SEC filing list"}; continue
    rc = S["filings"]["recent"]
    F = [{"form": rc["form"][i], "date": rc["filingDate"][i], "acc": rc["accessionNumber"][i], "prim": rc["primaryDocument"][i], "items": (rc.get("items") or [""] * len(rc["form"]))[i] or ""} for i in range(len(rc["form"])) if rc["filingDate"][i] >= "2024-01-01"]
    sh = [f for f in F if f["form"] in ("S-3", "S-3ASR", "F-3", "S-3/A", "F-3ASR")]
    if sh:
        f = sh[0]; tx = text(cik, f["acc"], f["prim"])
        m = re.search(r"(?:aggregate (?:initial )?offering price|maximum aggregate|up to)[^$]{0,80}(\$\s?[\d,.]+\s*(?:million|billion)?)", tx, re.I)
        amt = money(m.group(1)) if m else None
        o["shelf"] = {"date": f["date"], "form": f["form"], "amt": amt if amt and amt >= 1e7 else None, "auto": f["form"].endswith("ASR")}
    sup = [f for f in F if f["form"] in ("424B5", "424B3", "424B4", "424B7", "424B2")][:12]
    raises, atm = [], None
    for f in sup:
        tx = text(cik, f["acc"], f["prim"])
        if re.search(r"at[- ]the[- ]market|sales agreement|equity distribution agreement|ATM", tx[:15000]):
            if atm is None:
                m = re.search(r"(?:aggregate offering price of up to|having an aggregate offering price of up to|up to)\s*(\$\s?[\d,.]+\s*(?:million|billion)?)", tx, re.I)
                aa = money(m.group(1)) if m else None
                atm = {"date": f["date"], "amt": aa if aa and aa >= 1e6 else None}
            continue
        tb = re.search(r"Public offering price(?: per share)?\s*\$\s?([\d.,]+)\s*\$\s?([\d,]{7,}(?:\.\d+)?)", tx)
        if tb:
            raises.append({"date": f["date"], "type": "public offering", "price": float(tb.group(1).replace(",", "")), "amt": float(tb.group(2).replace(",", ""))}); continue
        m = re.search(r"(?:public offering price|offering price)\s+(?:is|of|per share is|per share of)?\s*\$\s?([\d.]+)\s*per share", tx, re.I)
        g = re.search(r"(?:gross proceeds|aggregate gross proceeds)[^$]{0,60}(\$\s?[\d,.]+\s*(?:million|billion)?)", tx, re.I)
        sh_n = re.search(r"([\d,]{6,})\s+shares of (?:our )?common stock", tx)
        if m:
            p = float(m.group(1)); amt = money(g.group(1)) if g else (p * float(sh_n.group(1).replace(",", "")) if sh_n else None)
            raises.append({"date": f["date"], "type": "public offering", "price": p, "amt": amt})
    for f in [x for x in F if x["form"] == "8-K" and "3.02" in x["items"]][:3]:
        raises.append({"date": f["date"], "type": "private placement (8-K 3.02)", "price": None, "amt": None})
    if atm: o["atm"] = atm
    if raises:
        lr = sorted(raises, key=lambda x: x["date"])[-1]
        if lr.get("price"):
            ps = [c for d, c in series(t) if d < dt.date.fromisoformat(lr["date"])]
            if ps: lr["disc"] = round(lr["price"] / ps[-1] - 1, 3)
        o["last_raise"] = lr
        o["raises_12m"] = sum(1 for x in raises if x["date"] >= (dt.date.today() - dt.timedelta(days=365)).isoformat())
    out[t] = o
    if n % 50 == 0: print(n, t, json.dumps(o)[:200], flush=True)
json.dump({"built": dt.date.today().isoformat(), "rows": out}, open(root / "data/overhang.json", "w"), separators=(",", ":"))
print(len(out), "names;", sum(1 for o in out.values() if o.get("shelf")), "with a shelf;", sum(1 for o in out.values() if o.get("atm")), "with an ATM;", sum(1 for o in out.values() if o.get("last_raise")), "with a raise since 2024")
