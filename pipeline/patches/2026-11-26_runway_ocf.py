"""Runway rechecked against SEC filings (scripts/runway_check.py, Nov 26 2026). Burn = operating cash outflow averaged over
the last two reported quarters (Q2-Q3 2026); cash = our cash figure (it includes long-term investments that the XBRL
'current' tags miss). Applied where the result differs from ours by >= 2 quarters and >= 40%. Not applied where the last two
quarters held one-off inflows that make burn look like zero or negative (VIR, ZURA, OBX) or the filing figure looks
distorted (MNKD), so those keep the earlier estimate. Replaces the hand estimate for NERV (4.7 -> 7.2)."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
RW = {'ZYME': 12.5, 'TNYA': 6.3, 'VRCA': 1.6, 'MGNX': 12.2, 'IRD': 6.8, 'NERV': 7.2, 'ANIX': 7.9, 'MIRM': 20.6, 'AUTL': 11.4,
      'INSM': 18.3, 'RGNX': 21.2, 'SPRO': 4.5, 'SRZN': 16.4, 'HRTX': 15.6, 'IOVA': 11.5, 'XNCR': 21.0, 'SGP': 14.0,
      'SABS': 18.0, 'PVLA': 17.4}
D = json.load(open(path))
for r in D:
    if r['ticker'] in RW: r['runway_q'] = RW[r['ticker']]; r['runway_src'] = '10-Q operating cash flow, Q2-Q3 2026'
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('runway updated for', len(RW), 'names')
