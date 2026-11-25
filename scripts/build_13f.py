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

BIGC = json.load(open(C / "big_ciks.json")) if (C / "big_ciks.json").exists() else {}
BIG = {}
for fund, cik in BIGC.items():
    d = C / str(cik)
    if not d.exists(): continue
    fs = sorted(d.glob("*.json"))
    if fs: x = json.load(open(fs[-1])); BIG[fund] = (qlab(x["period"]), x["rows"])
# ---- CUSIP -> ticker
cmap, cname = {}, {}
for fund, Q in F.items():
    for q, rows in Q.items():
        for nm, cu, sh, v in rows: cname.setdefault(cu, nm)
for fund, (q, rows) in BIG.items():
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
    steps = [q for q in qs if nextq(q) in QL][-4:]
    pr4 = {}
    for t in set().union(*[set(book[q]) for q in steps]) if steps else []:
        acc, ok = 1.0, False
        for q in steps:
            if book[q].get(t):
                p0, p1 = px(t, q), px(t, nextq(q))
                if p0 and p1: acc *= p1 / p0; ok = True
        if ok: pr4[t] = round(acc - 1, 4)
    last = qs[-1]
    out.append({"name": fund, "nick": NICK.get(fund), "spec": fund in spec, "cik": CIK[fund], "q": qs,
                "aum": {q: round(aum[q]) for q in qs}, "bio": {q: round(bio[q]) for q in qs}, "n": {q: len(book[q]) for q in qs},
                "hold": hold, "hold_cens": sum(1 for _, o in allr if o) / len(allr) if allr else None, "turn": turn,
                "rq": {q: round(v, 4) for q, v in rq.items()}, "r4": r4, "x4": x4, "r8": r8, "x8": x8,
                "top": [[t, round(v), pr4.get(t)] for t, v in book[last].most_common(10)], "pos": [[t, round(v), pr4.get(t)] for t, v in book[last].items()], "last": last})
out.sort(key=lambda f: -(f["bio"].get(f["last"]) or 0))
# ---- who owns each company: shares held by type / shares outstanding (latest 13Fs, mostly Sep 30 2026)
PASS = {"BlackRock Inc (new)", "State Street", "Geode Capital", "Northern Trust", "Dimensional Fund Advisors", "Charles Schwab Investment Mgmt", "Norges Bank", "Vanguard Capital Management", "Vanguard Portfolio Management"}
BANK = {"Morgan Stanley", "Goldman Sachs", "JPMorgan Chase", "Bank of America", "Wells Fargo", "UBS Group"}
MQ = json.load(open(root / "data/mcq.json"))
def shares_out(t):
    r = MQ["rows"].get(t)
    if r:
        for v in reversed(r["sh"]):
            if v: return v
    d = next((x for x in D if x["ticker"] == t), None)
    return d["mc"] / d["price"] if d and d.get("mc") and d.get("price") else None
HOLD = collections.defaultdict(lambda: collections.Counter())   # ticker -> {category: shares}
WHO = collections.defaultdict(list)                              # ticker -> [(holder, shares, category)]
def add(fund, rows, cat):
    agg = collections.Counter()
    for nm, cu, sh, v in rows:
        t = cmap.get(cu)
        if t: agg[t] += sh
    for t, sh in agg.items(): HOLD[t][cat] += sh; WHO[t].append((NICK.get(fund) or fund, sh, cat))
GEN = {"Wellington Management Group, LLP", "Citadel Advisors Llc", "Balyasny Asset Management LP"}
for f in out:
    if f["spec"]: add(f["name"], F[f["name"]][f["last"]], "act" if f["name"] in GEN else "spec")
for fund, (q, rows) in BIG.items():
    add(fund, rows, "pass" if fund in PASS else "bank" if fund in BANK else "act")
STRAT = re.compile(r"\b(plc|pharma|pharmaceutical|novartis|roche|sanofi|gilead|amgen|abbvie|lilly|bristol|merck|pfizer|johnson & johnson|takeda|astellas|regeneron|biogen|astrazeneca|gsk|bayer|daiichi|eisai|otsuka|vertex|novo nordisk|servier|ipsen|lundbeck|ono|chugai|jazz|incyte)\b", re.I)
own = {}
for r in D:
    t = r["ticker"]
    if r.get("ta") == "Acquired / Inactive" or not r.get("mc"): continue
    so = shares_out(t)
    if not so: continue
    c = HOLD.get(t, {})
    strat = 0
    for row in (H.get(t) or {}).get("rows", []):
        if STRAT.search(row.get("name") or "") and (row.get("name") not in spec): strat += (row.get("pct") or 0) / 100 * so
    o = {k: min(1, v / so) for k, v in c.items()}; o["strat"] = min(1, strat / so)
    tot = sum(o.values())
    if tot > 1: o = {k: v / tot for k, v in o.items()}
    top = sorted(WHO.get(t, []), key=lambda x: -x[1])[:6]
    own[t] = {"mc": r["mc"], **{k: round(v, 4) for k, v in o.items()}, "top": [[n, round(sh / so * 100, 1), c] for n, sh, c in top]}

# ---- complete institutional ownership from SEC's quarterly 13F data set (every filer), if downloaded to cache/13f_bulk/q2
BULK = root / "cache/13f_bulk/q2"; own_all = {}; bulk_period = None
if (BULK / "INFOTABLE.tsv").exists():
    import csv
    csv.field_size_limit(10**9)
    sub = {}
    for r in csv.DictReader(open(BULK / "SUBMISSION.tsv"), delimiter="\t"):
        if r["SUBMISSIONTYPE"] == "13F-HR": sub[r["ACCESSION_NUMBER"]] = (r["CIK"].lstrip("0"), r["PERIODOFREPORT"])
    per = collections.Counter(v[1] for v in sub.values()).most_common(1)[0][0]; bulk_period = per
    sub = {a: c for a, (c, p) in sub.items() if p == per}
    nm = {r["ACCESSION_NUMBER"]: r["FILINGMANAGER_NAME"] for r in csv.DictReader(open(BULK / "COVERPAGE.tsv"), delimiter="\t")}
    SPECCIK = {str(CIK[f["name"]]) for f in out if f["spec"] and f["name"] not in GEN}
    PASSRE = re.compile(r"vanguard|blackrock|state street|geode|northern trust|dimensional fund|charles schwab|norges|ishares|ssga", re.I)
    BANKRE = re.compile(r"morgan stanley|goldman sachs|jpmorgan|bank of america|wells fargo|ubs |citigroup|barclays|bnp|deutsche bank|royal bank of canada|td |raymond james|lpl financial|ameriprise", re.I)
    # map every bulk CUSIP to our tickers by issuer name (adds to cmap)
    acc = collections.defaultdict(collections.Counter); holders = collections.Counter(); seen = set()
    with open(BULK / "INFOTABLE.tsv") as fh:
        rd = csv.reader(fh, delimiter="\t"); hdr = next(rd); ix = {h: i for i, h in enumerate(hdr)}
        for row in rd:
            a = row[ix["ACCESSION_NUMBER"]]
            if a not in sub or row[ix["PUTCALL"]] or row[ix["SSHPRNAMTTYPE"]] != "SH": continue
            cu = row[ix["CUSIP"]].upper(); t = cmap.get(cu)
            if not t:
                if cu in seen: continue
                k = nn(row[ix["NAMEOFISSUER"]])
                if k in names: t = names[k]; cmap[cu] = t
                else: seen.add(cu); continue
            try: sh = float(row[ix["SSHPRNAMT"]] or 0)
            except ValueError: continue
            cik = sub[a]; fn = nm.get(a, "")
            cat = "spec" if cik in SPECCIK else "pass" if PASSRE.search(fn) else "bank" if BANKRE.search(fn) else "inst"
            acc[t][cat] += sh; holders[(t, cik)] += 1
    nh = collections.Counter(t for t, c in holders)
    qi = MQ["quarters"].index("2Q26") if "2Q26" in MQ["quarters"] else None
    for r in D:
        t = r["ticker"]
        if r.get("ta") == "Acquired / Inactive" or not r.get("mc") or t not in acc: continue
        so = (MQ["rows"].get(t, {}).get("sh") or [None] * 99)[qi] if qi is not None else None
        so = so or shares_out(t)
        if not so: continue
        o = {k: v / so for k, v in acc[t].items()}
        strat = (own.get(t) or {}).get("strat", 0); o["strat"] = strat
        tot = sum(o.values())
        if tot > 1: o = {k: v / tot for k, v in o.items()}
        own_all[t] = {"mc": r["mc"], "n": nh[t], **{k: round(v, 4) for k, v in o.items()}}
    print("bulk 13F", per, ":", len(sub), "filers;", len(own_all), "companies; CUSIPs mapped now", len(cmap))
# ---- who is buying and selling: specialist position changes between each fund's last two 13Fs,
# measured as position value / company market cap at each quarter-end (split-proof; mcq.json has point-in-time caps)
IPO = {r.get("ticker") for r in (json.load(open(root / "data/ipo-data.json")).get("recent") or []) if (r.get("first_trade_date") or "") >= "2026-01-01"}
def mcq(t, q):
    r = MQ["rows"].get(t)
    if not r or q not in MQ["quarters"]: return None
    return r["mc"][MQ["quarters"].index(q)]
flow = collections.defaultdict(lambda: {"new": [], "add": [], "cut": [], "exit": [], "net": 0.0})
for f in out:
    if not f["spec"] or len(f["q"]) < 2: continue
    q1, q0 = f["q"][-1], f["q"][-2]
    def vbook(q):
        c = collections.Counter()
        for nm_, cu, sh, v in F[f["name"]][q]:
            t = cmap.get(cu)
            if t: c[t] += v
        return c
    a, b = vbook(q0), vbook(q1); who = f["nick"] or f["name"]
    for t in set(a) | set(b):
        m0, m1 = mcq(t, q0), mcq(t, q1)
        if not m0 or not m1: continue
        p0, p1 = a.get(t, 0) / m0, b.get(t, 0) / m1
        if p0 > 0.6 or p1 > 0.6: continue                       # bad match or unit error
        d = p1 - p0
        if p0 == 0 and p1 > 0: flow[t]["new"].append([who, round(p1 * 100, 2)])
        elif p1 == 0 and p0 > 0: flow[t]["exit"].append([who, round(p0 * 100, 2)])
        elif d > 0.001: flow[t]["add"].append([who, round(d * 100, 2)])
        elif d < -0.001: flow[t]["cut"].append([who, round(d * 100, 2)])
        flow[t]["net"] += d
for t, v in flow.items():
    v["net"] = round(v["net"] * 100, 2); v["ipo"] = t in IPO
    for k in ("new", "add", "cut", "exit"): v[k].sort(key=lambda x: -abs(x[1]))
json.dump({"built": dt.date.today().isoformat(), "funds": out, "pool": {q: round(v) for q, v in pool.items()},
           "cusips_mapped": len(cmap), "own": own, "own_all": own_all, "bulk_period": bulk_period, "flow": flow, "big_funds": sorted(BIG)}, open(root / "data/13f.json", "w"), separators=(",", ":"))
import statistics
for lo, hi, lab in [(0, 3e8, "<$300M"), (3e8, 1e9, "$300M-1B"), (1e9, 5e9, "$1-5B"), (5e9, 2e10, "$5-20B"), (2e10, 1e13, ">$20B")]:
    L = [o for o in own.values() if lo <= o["mc"] < hi]
    if L: print(lab, len(L), {k: round(statistics.median([o.get(k, 0) for o in L]) * 100) for k in ("spec", "pass", "act", "bank", "strat")})
print(len(out), "funds;", "pool by quarter ($B):", {q: round(v / 1e9) for q, v in sorted(pool.items(), key=lambda x: (int(x[0][2:]), int(x[0][0])))})
for f in out[:8]:
    print(f["nick"] or f["name"], f["last"], "bio $%.1fB" % (f["bio"][f["last"]] / 1e9), "of $%.1fB" % (f["aum"][f["last"]] / 1e9), "n", f["n"][f["last"]],
          "hold %.1fQ" % (f["hold"] or 0), "turn %.0f%%" % ((f["turn"] or 0) * 100), "r4", f["r4"] and round(f["r4"] * 100), "xbi4", f["x4"] and round(f["x4"] * 100))
