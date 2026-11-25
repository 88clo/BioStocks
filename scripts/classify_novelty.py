"""Tag each company's lead program by how new it is to the market (data.json and parked-data.json -> 'novelty').

Three buckets, which fold together 'novel vs validated target' and 'first-in-class vs follower':
  First-in-class         novel target or mechanism, nothing approved on it yet
  Next-gen, validated    a validated target or approved class, with a claimed edge (oral, longer-acting, better data)
  Late entrant           a crowded or entrenched class where the drug is behind, undifferentiated or a me-too

Rule-based on the written differentiation, competitive threat and pitch text, with hand overrides.
Order: explicit wording first, then a fallback on the differentiation score and whether the threat names an approved drug."""
import json, re, pathlib
from collections import Counter
root = pathlib.Path(__file__).resolve().parents[1]

FIC = r"first[- ]in[- ]class|\bfirst(?:[- ]ever)? (?:potential )?(?:[\w-]+ ){0,3}(?:approach|treatment|therapy|drug|agent|add-on|enzyme|degrader|inhibitor|modulator|antibody|mAb|option|medicine)\b|root[- ]cause|first[- ]and[- ]only|\bonly (approved|therapy|drug|oral|treatment|agent|disease)|first (approved|therapy|drug|oral|treatment|disease[- ]modifying|ever|to (target|show|treat))|novel (target|mechanism|biology|MoA)|no approved (therap|treatment|drug|option)|no (other )?(approved )?(therap|treatment)s? (exist|available)|unvalidated|untested mechanism|white[- ]space|pioneer|new mechanism|unprecedented|unmet need with no"
LATE = r"crowded|me[- ]too|late entrant|late to|behind (the )?(leader|lilly|novo|competit|peers)|trails?|lagging|generic|biosimilar|undifferentiated|commodit|many competitors|(several|multiple|numerous) (approved|competitors|rivals|players)|already (approved|crowded)|fourth|fifth|third[- ]to[- ]market|copycat|not differentiated|limited differentiation"
NEXT = r"best[- ]in[- ]class|reformulat|next[- ]gen|second[- ]gen|improved|more potent|longer[- ]acting|less frequent|(once|twice)[- ](monthly|quarterly|yearly|weekly)|oral (alternative|version|option)|differentiated (from|vs)|fast[- ]follower|validated (target|mechanism|pathway|class)|clinically validated|proven (target|mechanism|class)|vs\.? (approved|standard)|better (efficacy|safety|tolerab)|follow[- ]on"

OVERRIDE = {"AUTL": "Late entrant", "ARWR": "Next-gen, validated", "CYTK": "Next-gen, validated", "XFOR": "First-in-class",
            "BNTX": "Next-gen, validated", "INCY": "Next-gen, validated", "JAZZ": "Next-gen, validated", "HALO": "Next-gen, validated", "SYRE": "Next-gen, validated",
            "LNTH": "Next-gen, validated", "LQDA": "Next-gen, validated", "ALKS": "Next-gen, validated"}  # ticker -> bucket, for hand checks

def classify(r):
    t = r.get("ticker")
    if t in OVERRIDE: return OVERRIDE[t]
    dd = str(r.get("diff_detail") or ""); th = str(r.get("threat") or ""); pi = " ".join(str(r.get(k) or "") for k in ("pitch_concise", "pitch", "moa"))
    ds = r.get("diffscore") or 3
    if not (dd or th): return None   # no written competitive view (most dropped-out names)
    if re.search(FIC, dd, re.I): return "First-in-class"
    if re.search(LATE, dd, re.I) and ds <= 3: return "Late entrant"
    if re.search(r"entrenched", dd, re.I) and ds <= 2: return "Late entrant"
    if re.search(NEXT, dd, re.I): return "Next-gen, validated"
    if re.search(FIC, pi, re.I): return "First-in-class"
    if re.search(LATE, dd + " " + th, re.I) and ds <= 3: return "Late entrant"
    approved_rival = re.search(r"approved|marketed|standard of care|SoC|blockbuster|generic", th, re.I)
    if approved_rival: return "Next-gen, validated" if ds >= 3 else "Late entrant"
    return "First-in-class" if ds >= 3 else "Late entrant"

if __name__ == "__main__":
    for f in ["data/data.json", "data/parked-data.json"]:
        p = root / f; D = json.load(open(p)); rows = D["rows"] if isinstance(D, dict) else D
        for r in rows: r["novelty"] = classify(r)
        json.dump(D, open(p, "w"), ensure_ascii=False, separators=(",", ":"))
        print(f, Counter(r["novelty"] for r in rows).most_common())
