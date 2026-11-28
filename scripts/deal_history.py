"""Post-deal returns dataset (Nov 27 2026) -> data/deal-history.json.

Every priced equity deal by a covered company since Jan 1 2023, from SEC EDGAR (public filings, declared user agent):
  - public offerings: final prospectus supplements / prospectuses (424B4, 424B5, 424B7); ATM programs and preliminary
    ("Subject to Completion") documents are skipped
  - private placements: 8-Ks with item 3.02 that state a per-share price
For each deal: pricing date (the prospectus date, else the filing date), offer price, gross size, discount to the last close
on or before pricing (public) / before the 8-K (PIPEs), size in days of 20-day average dollar volume, structure flags
(common warrants, pre-funded warrants, existing-holder / insider participation language, IPO), lead banks named on the
cover, and returns from the offer price at +1, +30 and +90 trading days, raw and in excess of XBI over the same window.
Prices: cache/prices (Yahoo daily, fetched by fetch_prices.py). Documents: cache/overhang/<accession>.json (shared with
overhang.py). Summary statistics are medians, with counts, so a handful of outliers cannot drive them.
Usage: python3 scripts/deal_history.py"""
import json, re, time, html, pathlib, urllib.request, datetime as dt, statistics as st
root = pathlib.Path(__file__).resolve().parents[1]
UA = {"User-Agent": "BioStocks research dashboard (88clo) contact@example.com"}
C = root / "cache/overhang"; C.mkdir(parents=True, exist_ok=True)
SINCE = "2023-01-01"
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
def subs(cik):
    f = root / f"cache/8k/sub_{cik}.json"
    if f.exists() and time.time() - f.stat().st_mtime < 86400 * 7: return json.load(open(f))
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
    try:
        j = json.load(open(root / f"cache/prices/{t}.json"))["chart"]["result"][0]; q = j["indicators"]["quote"][0]
        return [(dt.datetime.fromtimestamp(ts, dt.timezone.utc).date(), c, v or 0) for ts, c, v in zip(j["timestamp"], q["close"], q["volume"]) if c]
    except Exception: return []
BANKS = ["J.P. Morgan", "Goldman Sachs", "Morgan Stanley", "BofA Securities", "Jefferies", "Leerink", "TD Cowen", "Cowen", "Piper Sandler",
         "Evercore", "Guggenheim", "Citigroup", "Barclays", "Stifel", "RBC Capital", "Cantor", "Raymond James", "William Blair", "Truist",
         "Needham", "LifeSci Capital", "Oppenheimer", "H.C. Wainwright", "Mizuho", "UBS", "Deutsche Bank", "Wells Fargo", "Baird", "Chardan",
         "Lucid Capital", "Citizens JMP", "JMP", "Canaccord", "B. Riley", "Ladenburg", "Roth", "Maxim", "ThinkEquity", "BTIG", "Van Leeuwen"]
MON = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1)}
def pdate(tx, fallback):
    """Pricing date = the date of the prospectus supplement (not of the base shelf prospectus it attaches), kept only if it
    falls within two weeks before the filing; otherwise the filing date."""
    fd = dt.date.fromisoformat(fallback)
    def mk(mo, dd, yy):
        try: return dt.date(int(yy), MON[mo], int(dd)) if mo in MON else None
        except ValueError: return None
    m = re.search(r"On ([A-Z][a-z]+) (\d{1,2}), (\d{4}),? the last reported (?:sale|closing) price", tx[:15000])
    if m:
        d = mk(*m.groups())
        if d and dt.timedelta(0) <= fd - d <= dt.timedelta(days=14): return d
    m = re.search(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})\s+TABLE OF CONTENTS", tx[:15000])
    if m:
        d = mk(*m.groups())
        if d and dt.timedelta(0) <= fd - d <= dt.timedelta(days=14): return d
    pats = [r"The date of this prospectus supplement is\s+([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})", r"Prospectus Supplement dated\s+([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})",
            r"The date of this prospectus is\s+([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})"]
    for pat in pats:
        for m in re.finditer(pat, tx):
            if m.group(1) not in MON: continue
            try: d = dt.date(int(m.group(3)), MON[m.group(1)], int(m.group(2)))
            except ValueError: continue
            if dt.timedelta(0) <= fd - d <= dt.timedelta(days=14): return d
    b = fd - dt.timedelta(days=1)
    while b.weekday() >= 5: b -= dt.timedelta(days=1)
    return b
def flags(tx):
    cover = tx[:8000]; full = tx
    offered = re.search(r"(?<!pre-funded )(?<!pre-funded\s)(?:accompanying|common|series [a-c]|tranche [a-c]|investor) warrants?\b|(?<!pre-funded )warrants to purchase up to", cover, re.I)
    return {"warrants": bool(offered),
            "prefunded": bool(re.search(r"pre[-\u2010\u2011 ]?funded warrants?", cover, re.I)),
            "insiders": bool(re.search(r"(?:existing (?:stockholders|shareholders)|affiliated with (?:certain of )?our (?:directors|officers)|certain of our directors|insiders)[^.]{0,450}(?:indicated an interest|have agreed to purchase|purchase an aggregate)", full, re.I)),
            "banks": [b for b in BANKS if b in cover][:4]}
def main():
    D = [r for r in json.load(open(root / "data/data.json")) if r.get("ta") != "Acquired / Inactive"]
    tk = root / "cache/company_tickers.json"
    if not tk.exists() or time.time() - tk.stat().st_mtime > 86400 * 30:
        s = get("https://www.sec.gov/files/company_tickers.json"); tk.write_text(s)
    CIK = {v["ticker"]: v["cik_str"] for v in json.loads(tk.read_text()).values()}
    xbi = {d: c for d, c, v in series("XBI")}; xd = sorted(xbi)
    rows = []
    for n, r in enumerate(D):
        t = r["ticker"]; cik = CIK.get(t); S = subs(cik) if cik else None
        if not S: continue
        rc = S["filings"]["recent"]; px = series(t)
        if not px: continue
        dates = [d for d, c, v in px]
        F = [{"form": rc["form"][i], "date": rc["filingDate"][i], "acc": rc["accessionNumber"][i], "prim": rc["primaryDocument"][i],
              "items": (rc.get("items") or [""] * len(rc["form"]))[i] or ""} for i in range(len(rc["form"])) if rc["filingDate"][i] >= SINCE]
        seen = set()
        for f in F:
            pub = f["form"] in ("424B4", "424B5", "424B7"); pipe = f["form"] == "8-K" and "3.02" in f["items"]
            if not (pub or pipe): continue
            tx = text(cik, f["acc"], f["prim"])
            if not tx: continue
            if pub and (re.search(r"Subject to Completion", tx[:6000], re.I) or re.search(r"at[- ]the[- ]market|sales agreement|equity distribution agreement", tx[:15000], re.I)): continue
            price = amt = None
            if pub:
                tb = re.search(r"Public offering price(?: per share)?\s*\$\s?([\d.,]+)\s*\$\s?([\d,]{7,}(?:\.\d+)?)", tx)
                if tb: price, amt = float(tb.group(1).replace(",", "")), float(tb.group(2).replace(",", ""))
                else:
                    m = re.search(r"(?:public offering price|offering price)\s+(?:is|of|per share is|per share of)?\s*\$\s?([\d.]+)\s*per share", tx, re.I)
                    g = re.search(r"(?:gross proceeds|aggregate gross proceeds)[^$]{0,60}(\$\s?[\d,.]+\s*(?:million|billion)?)", tx, re.I)
                    if m: price = float(m.group(1)); amt = money(g.group(1)) if g else None
                pd = pdate(tx, f["date"])
            else:
                m = re.search(r"(?:purchase|offering|subscription) price of \$\s?([\d.]+) per share", tx, re.I) or re.search(r"at a price of \$\s?([\d.]+) per share", tx, re.I)
                g = re.search(r"(?:aggregate )?gross proceeds[^$]{0,60}(\$\s?[\d,.]+\s*(?:million|billion)?)", tx, re.I)
                if m: price = float(m.group(1)); amt = money(g.group(1)) if g else None
                pd = dt.date.fromisoformat(f["date"]) - dt.timedelta(days=1)
            if not price or price <= 0: continue
            key = (pd.isoformat(), round(price, 3))
            if key in seen: continue
            seen.add(key)
            i0 = max([i for i, d in enumerate(dates) if d <= pd], default=None)
            if i0 is None and pub and f["form"] == "424B4":  # IPO priced the evening before its first trade
                i0 = 0 if dates and dates[0] > pd and (dates[0] - pd).days <= 7 else None
            if i0 is None: continue
            ipo = pub and i0 < 20  # under a month of trading before pricing: an IPO, which has no prior close to discount from
            ref = px[i0][1]
            ls = re.search(r"the last reported (?:sale|closing) price of our common stock[^$]{0,160}\$\s?([\d.,]+)", tx[:15000]) if pub else None
            if ls:
                try:
                    v = float(ls.group(1).replace(",", "").rstrip("."))
                    if 0.5 < v / ref < 2: ref = v
                except ValueError: pass
            disc = None if ipo else price / ref - 1
            if disc is not None and abs(disc) > 0.6: continue  # parse error or reverse split around the deal
            if ipo:  # returns for an IPO run from the first close after pricing back to the IPO price
                i0 = max([i for i, d in enumerate(dates) if d <= pd], default=-1)
            adv = [px[j][1] * px[j][2] for j in range(max(0, i0 - 20), i0)]; adv = sum(adv) / len(adv) if adv else None
            def ret(k):
                j = i0 + k
                if j >= len(px): return None, None
                rr = px[j][1] / price - 1
                xa = xbi.get(dates[i0]); xb = xbi.get(dates[j])
                return round(rr, 4), (round(rr - (xb / xa - 1), 4) if xa and xb else None)
            r1, x1 = ret(1); r30, x30 = ret(30); r90, x90 = ret(90)
            fl = flags(tx) if pub else {"warrants": bool(re.search(r"warrants? to purchase", tx[:20000], re.I)), "prefunded": bool(re.search(r"pre-funded", tx[:20000], re.I)), "insiders": False, "banks": []}
            rows.append({"t": t, "date": pd.isoformat(), "type": ("IPO" if ipo else "non-shelf follow-on (424B4)" if f["form"] == "424B4" else "secondary (424B7)" if f["form"] == "424B7" else "follow-on / RD") if pub else "PIPE (8-K 3.02)",
                         "price": price, "amt": amt, "disc": round(disc, 4) if disc is not None else None, "size_adv": round(amt / adv, 1) if amt and adv and not ipo else None,
                         "r1": r1, "x1": x1, "r30": r30, "x30": x30, "r90": r90, "x90": x90, **fl, "acc": f["acc"]})
        if n % 50 == 0: print(n, t, len(rows), flush=True)
    def med(v): v = [x for x in v if x is not None]; return (round(st.median(v), 4), len(v)) if v else (None, 0)
    def grp(name, pred):
        R = [x for x in rows if pred(x)]
        a, n30 = med([x["x30"] for x in R]); b, n90 = med([x["x90"] for x in R]); c, n1 = med([x["x1"] for x in R])
        hit = [x["x30"] for x in R if x["x30"] is not None]
        return {"group": name, "n": len(R), "x1": c, "x30": a, "x90": b, "n90": n90, "hit30": round(sum(1 for v in hit if v > 0) / len(hit), 3) if hit else None,
                "disc": med([x["disc"] for x in R if x["disc"] is not None])[0]}
    G = [grp("All deals", lambda x: True),
         grp("Public follow-ons and registered directs", lambda x: x["type"] in ("follow-on / RD", "non-shelf follow-on (424B4)")), grp("IPOs (returns from the IPO price)", lambda x: x["type"] == "IPO"), grp("PIPEs", lambda x: x["type"].startswith("PIPE")),
         grp("Discount under 5% (incl. at or above market)", lambda x: x["disc"] is not None and x["disc"] > -0.05), grp("Discount 5-15%", lambda x: x["disc"] is not None and -0.15 < x["disc"] <= -0.05), grp("Discount over 15%", lambda x: x["disc"] is not None and x["disc"] <= -0.15),
         grp("With common warrants", lambda x: x["warrants"]), grp("No warrants", lambda x: not x["warrants"]),
         grp("With pre-funded warrants", lambda x: x["prefunded"]), grp("Insider / existing-holder participation named", lambda x: x["insiders"]),
         grp("Size < 5 days of volume", lambda x: x["size_adv"] is not None and x["size_adv"] < 5), grp("Size 5-20 days", lambda x: x["size_adv"] is not None and 5 <= x["size_adv"] < 20), grp("Size 20+ days", lambda x: x["size_adv"] is not None and x["size_adv"] >= 20)]
    for y in sorted({x["date"][:4] for x in rows}): G.append(grp("Priced in " + y, lambda x, y=y: x["date"].startswith(y)))
    json.dump({"built": dt.date.today().isoformat(), "since": SINCE, "n": len(rows), "stats": G, "rows": sorted(rows, key=lambda x: x["date"], reverse=True)},
              open(root / "data/deal-history.json", "w"), separators=(",", ":"))
    print("deal history:", len(rows), "deals since", SINCE)
if __name__ == "__main__": main()
