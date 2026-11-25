"""Turn cached 13F filings (scripts/fetch_13f.py) into fund analytics -> data/13f.json.

1. Map CUSIPs to our tickers: (a) issuer name matched to our company names (covered + parked), (b) confirmed or added by
   matching a fund's reported share count to the Yahoo top-holder share count for the same company and quarter.
2. Per fund and quarter: total 13F book, biotech book (our universe), positions.
3. Holding period: average length of each position's run of consecutive quarters (runs still open at the latest filing,
   or already open at the earliest, are censored, so the figure is a floor, shown with >=).
4. Turnover: new + exited positions per quarter / average positions.
5. Copy-the-book return: buy each quarter's reported biotech holdings (value-weighted) at that quarter-end and hold to the next
   quarter-end; chained over the last 4 and 8 quarters, vs XBI. The standard way to judge 13F skill without look-ahead.
6. Specialist pool: total biotech book of all specialist funds per quarter."""
import json, re, pathlib, difflib, collections, datetime as dt
root = pathlib.Path(__file__).resolve().parents[1]
C = root / "cache/13f"
CIK = json.load(open(C / "ciks.json"))
D = json.load(open(root / "data/data.json")); PK = json.load(open(root / "data/parked-data.json")); PK = PK["rows"] if isinstance(PK, dict) else PK
H = json.load(open(root / "data/holders-baked.json"))
PQ = json.load(open(root / "data/priceq-baked.json")); QL = PQ["quarters"]; PR = PQ["prices"]
tpl = (root / "pipeline/template.html").read_text(encoding="utf-8")
NICK = json.loads(re.search(r"const SPECIALIST_NICKNAMES=(\{.*?\});", tpl).group(1))

def qlab(period):  # 2026-09-30 -> 3Q26
    y, m = int(period[:4]), int(period[5:7]); return f"{(m - 1) // 3 + 1}Q{str(y)[2:]}"
STOP = r"\b(inc|incorporated|corp|corporation|co|company|ltd|limited|plc|ag|sa|nv|n v|se|holdings?|group|the|class [a-z]|cl [a-z]|com|ord|shs|adr|ads|sponsored|new|de|del)\b"
def nn(s): return re.sub(r"\s+", " ", re.sub(STOP, " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()))).strip()

names = {}
for r in D + PK:
    for k in ("name", "nick"):
        if r.get(k): names.setdefault(nn(r[k]), r["ticker"])
NK = list(names)

# ---- load filings
F = {}   # fund -> {quarter: rows}
for fund, cik in CIK.items():
    if not cik: continue
    d = C / str(cik)
    if not d.exists(): continue
    for f in d.glob("*.json"):
        x = json.load(open(f)); F.setdefault(fund, {})[qlab(x["period"])] = x["rows"]

# ---- CUSIP -> ticker
cmap, cname = {}, {}
for fund, Q in F.items():
    for q, rows in Q.items():
        for nm, cu, sh, v in rows: cname.setdefault(cu, nm)
for cu, nm in cname.items():
    k = nn(nm)
    if k in names: cmap[cu] = names[k]; continue
    m = difflib.get_close_matches(k, NK, n=1, cutoff=0.92)
    if m: cmap[cu] = names[m[0]]
# share-count confirmation against Yahoo top holders: only for unmapped CUSIPs whose issuer name loosely matches the company
TN = {r["ticker"]: nn(r.get("name") or r.get("nick") or "") for r in D + PK}
added = 0
for t, h in H.items():
    for row in h.get("rows", []):
        fund, sh = row.get("name"), row.get("shares") or 0
        if fund not in F or not sh: continue
        for q in ("2Q26", "3Q26", "1Q26"):
            for nm, cu, s2, v in F[fund].get(q, []):
                if cu in cmap or not s2 or abs(s2 - sh) / sh > 0.001: continue
                if difflib.SequenceMatcher(None, nn(nm), TN.get(t, "")).ratio() >= 0.5:
                    cmap[cu] = t; added += 1
print(len(cname), "CUSIPs seen;", len(cmap), "mapped to our tickers;", added, "added by share-count match")

def px(t, q):
    p = PR.get(t); i = QL.index(q) if q in QL else None
    return p[i] if p and i is not None and i < len(p) else None
def nextq(q):
    n, y = int(q[0]), int(q[2:]); return f"{n % 4 + 1}Q{y + (1 if n == 4 else 0):02d}"

bench = (json.load(open(root / "data/investors.json")).get("xbi_q") or {})
TR = None
try: TR = None
except Exception: pass

out, pool = [], collections.Counter()
spec = set(json.loads(re.search(r"const SPECIALIST_INVESTORS=new Set\((\[.*?\])\);", tpl).group(1)))
for fund, Q in F.items():
    qs = sorted(Q, key=lambda q: (int(q[2:]), int(q[0])))
    qs = [q for q in qs if int(q[2:]) * 4 + int(q[0]) >= 24 * 4 + 3]       # last 9 quarters only (3Q24 on)
    if len(qs) < 4 or qs[-1] not in ("2Q26", "3Q26"): continue            # skip stale filers and one-off matches
    book = {}
    for q in qs:
        b = collections.Counter()
        for nm, cu, sh, v in Q[q]:
            t = cmap.get(cu)
            if t: b[t] += v
        book[q] = b
    aum = {q: sum(r[3] for r in Q[q]) for q in qs}
    bio = {q: sum(book[q].values()) for q in qs}
    if fund in spec:
        for q in qs: pool[q] += bio[q]
    # holding runs
    runs, cur = [], {}
    for i, q in enumerate(qs):
        held = set(t for t, v in book[q].items() if v > 0)
        for t in list(cur):
            if t not in held: runs.append((cur.pop(t), False))     # closed run
        for t in held:
            if t in cur: cur[t] += 1
            else: cur[t] = 1
    open_runs = [(n, True) for n in cur.values()]
    allr = runs + open_runs
    hold = sum(n for n, _ in allr) / len(allr) if allr else None
    # turnover
    tv = []
    for a, b in zip(qs, qs[1:]):
        A, B = set(book[a]), set(book[b]); avg = (len(A) + len(B)) / 2 or 1
        tv.append((len(B - A) + len(A - B)) / 2 / avg)
    turn = sum(tv) / len(tv) if tv else None
    # copy-the-book returns
    rq = {}
    for q in qs:
        n = nextq(q); w = book[q]; tot = 0; acc = 0
        for t, v in w.items():
            p0, p1 = px(t, q), px(t, n)
            if p0 and p1: acc += v * (p1 / p0 - 1); tot += v
        if tot > 0 and n in QL: rq[n] = acc / tot
    def chain(k):
        L = sorted(rq, key=lambda q: (int(q[2:]), int(q[0])))[-k:]
        if len(L) < k: return None, None
        r = 1; x = 1
        for q in L:
            r *= 1 + rq[q]
            p = [qq for qq in bench if qq == q]; pq = None
            for qq in bench:
                if nextq(qq) == q: pq = qq
            if pq and bench.get(q) and bench.get(pq): x *= bench[q] / bench[pq]
        return r - 1, x - 1
    r4, x4 = chain(4); r8, x8 = chain(8)
    last = qs[-1]
    out.append({"name": fund, "nick": NICK.get(fund), "spec": fund in spec, "cik": CIK[fund], "q": qs,
                "aum": {q: round(aum[q]) for q in qs}, "bio": {q: round(bio[q]) for q in qs}, "n": {q: len(book[q]) for q in qs},
                "hold": hold, "hold_cens": sum(1 for _, o in allr if o) / len(allr) if allr else None, "turn": turn,
                "rq": {q: round(v, 4) for q, v in rq.items()}, "r4": r4, "x4": x4, "r8": r8, "x8": x8,
                "top": [[t, round(v)] for t, v in book[last].most_common(10)], "pos": [[t, round(v)] for t, v in book[last].items()], "last": last})
out.sort(key=lambda f: -(f["bio"].get(f["last"]) or 0))
json.dump({"built": dt.date.today().isoformat(), "funds": out, "pool": {q: round(v) for q, v in pool.items()},
           "cusips_mapped": len(cmap)}, open(root / "data/13f.json", "w"), separators=(",", ":"))
print(len(out), "funds;", "pool by quarter ($B):", {q: round(v / 1e9) for q, v in sorted(pool.items(), key=lambda x: (int(x[0][2:]), int(x[0][0])))})
for f in out[:8]:
    print(f["nick"] or f["name"], f["last"], "bio $%.1fB" % (f["bio"][f["last"]] / 1e9), "of $%.1fB" % (f["aum"][f["last"]] / 1e9), "n", f["n"][f["last"]],
          "hold %.1fQ" % (f["hold"] or 0), "turn %.0f%%" % ((f["turn"] or 0) * 100), "r4", f["r4"] and round(f["r4"] * 100), "xbi4", f["x4"] and round(f["x4"] * 100))
