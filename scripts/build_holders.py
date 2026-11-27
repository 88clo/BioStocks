"""Top holders per company from SEC's quarterly bulk 13F data set (cache/13f_bulk/q2) -> data/holders-baked.json (Nov 27 2026).
Replaces the Sep 13 Yahoo snapshot so the Companies table (Specialists column, top holders) can be refreshed whenever SEC
publishes a new data set (the monthly task downloads it). Per company: the 7 largest 13F filers by shares (long common, no
options), with % of shares outstanding (shares from our market cap / price). Filers are named as they file."""
import csv, json, pathlib, collections, datetime as dt
root = pathlib.Path(__file__).resolve().parents[1]; csv.field_size_limit(10**9)
B = root / "cache/13f_bulk/q2"
cmap = json.load(open(root / "cache/13f/cusip_map.json"))
D = {r["ticker"]: r for r in json.load(open(root / "data/data.json"))}
sub = {}
for r in csv.DictReader(open(B / "SUBMISSION.tsv"), delimiter="\t"):
    if r["SUBMISSIONTYPE"] in ("13F-HR", "13F-HR/A"): sub[r["ACCESSION_NUMBER"]] = (r["CIK"], r["PERIODOFREPORT"], r["SUBMISSIONTYPE"])
per = collections.Counter(v[1] for v in sub.values()).most_common(1)[0][0]
nm = {r["ACCESSION_NUMBER"]: r["FILINGMANAGER_NAME"] for r in csv.DictReader(open(B / "COVERPAGE.tsv"), delimiter="\t")}
H = collections.defaultdict(lambda: collections.defaultdict(float)); NAME = {}
with open(B / "INFOTABLE.tsv") as fh:
    rd = csv.reader(fh, delimiter="\t"); ix = {h: i for i, h in enumerate(next(rd))}
    for row in rd:
        a = row[ix["ACCESSION_NUMBER"]]; s = sub.get(a)
        if not s or s[1] != per or s[2] != "13F-HR" or row[ix["PUTCALL"]] or row[ix["SSHPRNAMTTYPE"]] != "SH": continue
        t = cmap.get(row[ix["CUSIP"]].upper())
        if t not in D: continue
        try: H[t][s[0]] += float(row[ix["SSHPRNAMT"]])
        except ValueError: continue
        NAME[s[0]] = nm.get(a, s[0])
F13 = {str(f["cik"]).lstrip("0"): f for f in json.load(open(root / "data/13f.json"))["funds"]}
asof = dt.datetime.strptime(per, "%d-%b-%Y").date()
out = {}
for t, h in H.items():
    r = D[t]; so = (r["mc"] / r["price"]) if r.get("mc") and r.get("price") else None
    top = sorted(h.items(), key=lambda x: -x[1])[:7]
    out[t] = {"asof": asof.strftime("%m.%d.%y"), "src": "SEC 13F data set", "rows": [dict({"name": NAME[c].title(), "shares": round(v), "pct": round(v / so * 100, 2) if so else None}, **({"spec": True, "nick": F13[c.lstrip("0")].get("nick") or F13[c.lstrip("0")]["name"].split(" ")[0]} if F13.get(c.lstrip("0"), {}).get("spec") else {})) for c, v in top]}
old = json.load(open(root / "data/holders-baked.json")) if (root / "data/holders-baked.json").exists() else {}
for t, v in old.items():
    if t not in out: out[t] = v                                  # keep older rows for names not in this data set
json.dump(out, open(root / "data/holders-baked.json", "w"), separators=(",", ":"))
print(len(out), "companies; holders as of", asof)
