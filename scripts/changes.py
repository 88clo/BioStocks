"""What changed between the two latest frozen ledgers: call changes, biggest price moves, catalyst date changes.
Writes data/changes-data.json for the Brief's 'Changed since last refresh' strip."""
import json, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
L = sorted((root/"ledger").glob("2*.json"))
if len(L) < 2: raise SystemExit("need two ledgers")
a, b = (json.load(open(f))["rows"] for f in L[-2:])
A = {r["ticker"]: r for r in a}; out = {"from": L[-2].stem, "to": L[-1].stem, "calls": [], "moves": [], "catalysts": [], "new": [], "dropped": []}
for r in b:
    o = A.get(r["ticker"])
    if not o: out["new"].append(r["ticker"]); continue
    if o["call"] != r["call"]: out["calls"].append({"t": r["ticker"], "from": o["call"], "to": r["call"], "up": r.get("up")})
    if o.get("price") and r.get("price"): out["moves"].append({"t": r["ticker"], "r": round((r["price"]/o["price"] - 1)*100, 1), "call": r["call"]})
    if (o.get("cat_date") or "") != (r.get("cat_date") or ""): out["catalysts"].append({"t": r["ticker"], "from": o.get("cat_date"), "to": r.get("cat_date"), "cat": (r.get("cat") or "")[:120]})
out["dropped"] = [t for t in A if t not in {r["ticker"] for r in b}]
out["moves"].sort(key=lambda x: -abs(x["r"])); out["moves"] = out["moves"][:12]
json.dump(out, open(root/"data/changes-data.json", "w"), indent=1)
print(out["from"], "->", out["to"], "| call changes", len(out["calls"]), "| catalyst date changes", len(out["catalysts"]), "| top moves", [(m["t"], m["r"]) for m in out["moves"][:6]])
