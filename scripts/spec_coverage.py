"""Are we missing significant specialist funds? Scans every 13F-HR filer in SEC's quarterly bulk data set
(cache/13f_bulk/q2) and lists filers whose stock book is concentrated in our covered biotech names but who are not in
our specialist list. Writes data/spec_coverage.json.
Concentration = value of covered biotech holdings / total 13F long-equity value. A filer is a candidate when
covered biotech >= $50M and >= 25% of its book, excluding passive managers, banks and the funds we already track."""
import csv, json, re, collections, pathlib
root = pathlib.Path(__file__).resolve().parents[1]; B = root / "cache/13f_bulk/q2"
csv.field_size_limit(10**9)
F = json.load(open(root / "data/13f.json"))
D = json.load(open(root / "data/data.json"))
cov = {r["ticker"] for r in D if r.get("ta") != "Acquired / Inactive"}
tracked_cik = {str(f["cik"]).lstrip("0") for f in F["funds"]}
tracked_names = {re.sub(r"[^a-z]", "", f["name"].lower())[:12] for f in F["funds"]}
cmap = json.load(open(root / "cache/13f/cusip_map.json")) if (root / "cache/13f/cusip_map.json").exists() else {}
cov |= set(cmap.values())   # same biotech universe as build_13f (includes a few large biotechs we don't cover)
names = {}
def nn(s): return re.sub(r"\s+", " ", re.sub(r"\b(inc|corp|corporation|ltd|plc|co|holdings|therapeutics|pharmaceuticals|bio|n v|sa|ag|com|new)\b", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()))).strip()
for r in D: names[nn(r.get("name"))] = r["ticker"]
sub = {}
for r in csv.DictReader(open(B / "SUBMISSION.tsv"), delimiter="\t"):
    if r["SUBMISSIONTYPE"] == "13F-HR": sub[r["ACCESSION_NUMBER"]] = (r["CIK"].lstrip("0"), r["PERIODOFREPORT"])
per = collections.Counter(v[1] for v in sub.values()).most_common(1)[0][0]
sub = {a: c for a, (c, p) in sub.items() if p == per}
nm = {r["ACCESSION_NUMBER"]: r["FILINGMANAGER_NAME"] for r in csv.DictReader(open(B / "COVERPAGE.tsv"), delimiter="\t")}
tot = collections.Counter(); bio = collections.Counter(); nb = collections.Counter(); seen = {}
with open(B / "INFOTABLE.tsv") as fh:
    rd = csv.reader(fh, delimiter="\t"); ix = {h: i for i, h in enumerate(next(rd))}
    for row in rd:
        a = row[ix["ACCESSION_NUMBER"]]
        if a not in sub or row[ix["PUTCALL"]]: continue
        try: v = float(row[ix["VALUE"]] or 0)
        except ValueError: continue
        tot[a] += v
        cu = row[ix["CUSIP"]].upper()
        t = cmap.get(cu) if cu in cmap else seen.get(cu)
        if t is None and cu not in seen: t = names.get(nn(row[ix["NAMEOFISSUER"]])); seen[cu] = t
        if t in cov: bio[a] += v; nb[a] += 1
by = {}
for a, cik in sub.items():
    o = by.setdefault(cik, {"name": nm.get(a, ""), "tot": 0, "bio": 0, "n": 0})
    o["tot"] = max(o["tot"], tot[a]); o["bio"] = max(o["bio"], bio[a]); o["n"] = max(o["n"], nb[a])
PASS = re.compile(r"vanguard|blackrock|state street|geode|northern trust|dimensional|schwab|norges|ishares|ssga|morgan stanley|goldman|jpmorgan|bank of america|wells fargo|ubs|citigroup|barclays|royal bank|raymond james|lpl|ameriprise|invesco|franklin|t\. ?rowe|fmr|fidelity|capital research|capital world|wellington|janus|millennium|citadel|jane street|susquehanna|two sigma|renaissance|d\. ?e\. ?shaw|aqr|point72|balyasny|hrt|virtu|optiver|ark invest", re.I)
cand, trk = [], []
for cik, o in by.items():
    sh = o["bio"] / o["tot"] if o["tot"] else 0
    row = {"cik": cik, "name": o["name"].title(), "bio": round(o["bio"]), "tot": round(o["tot"]), "share": round(sh, 3), "n": o["n"]}
    if cik in tracked_cik: trk.append(row); continue
    if o["bio"] >= 5e7 and sh >= .25 and not PASS.search(o["name"]): cand.append(row)
cand.sort(key=lambda r: -r["bio"]); trk.sort(key=lambda r: -r["bio"])
big = [r for r in by.values() if r["bio"] >= 1.5e8 and r["tot"] and r["bio"] / r["tot"] >= .35]
out = {"tracked_rows": trk, "period": per, "filers": len(by), "tracked": len(trk), "tracked_bio": sum(r["bio"] for r in trk), "candidates": cand,
       "cand_bio": sum(r["bio"] for r in cand), "rule": "covered biotech >= $50M and >= 25% of the 13F book; not passive, bank or multi-strategy"}
json.dump(out, open(root / "data/spec_coverage.json", "w"), separators=(",", ":"))
print(per, len(by), "filers; tracked", len(trk), "with $%.1fB covered biotech;" % (out["tracked_bio"] / 1e9), len(cand), "untracked concentrated filers with $%.2fB" % (out["cand_bio"] / 1e9))
for r in cand[:40]: print("  ", r["name"][:45], "$%.0fM" % (r["bio"] / 1e6), "%.0f%%" % (r["share"] * 100), r["n"])
