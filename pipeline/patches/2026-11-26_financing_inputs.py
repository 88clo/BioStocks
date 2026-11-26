"""Inputs checked while adding the financing penalty (Nov 26 2026).
NERV: runway was 0.6 quarters because the burn was taken from GAAP loss swung by warrant revaluation; Q3 2026 adjusted
net loss was $5.6M, R&D is rising with the Ph3, and outside estimates put runway at ~14 months on $77M -> 4.7 quarters.
KOD: $88.7M cash at Sep 30 plus $69M net raised on the ATM after the quarter (Q3 report, going-concern language) -> $157.7M;
burn ~$67M a quarter -> 2.4 quarters.
SLS: efficacy 3 -> 4. REGAL hit overall survival (HR 0.59, p=0.035, n=126); the short is on valuation, not the science,
so the formula gives SHORT (rich, good data) rather than STRONG SHORT (rich, weak data)."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
for r in D:
    if r['ticker'] == 'NERV': r['runway_q'] = 4.7
    if r['ticker'] == 'KOD': r['cash'] = 157.7e6; r['runway_q'] = 2.4
    if r['ticker'] == 'SLS': r['effsig'] = 4
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('patched NERV runway, KOD cash, SLS efficacy')
