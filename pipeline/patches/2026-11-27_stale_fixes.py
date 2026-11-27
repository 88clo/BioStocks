"""Stale inputs found by scripts/stale_scan.py (Nov 27 2026).
- ZURA: Ph2 TibuSHIELD in HS missed its primary and key secondary endpoints (Nov 9 2026; AN count -56%/-58% vs -52.5% placebo);
  HS discontinued. Tibulizumab continues in SSc (TibuSURE, n=91, topline H1 2027) and PMR (NEXUS-PMR start YE2026).
  Cash $187.7M (runway through 2028). Lead -> SSc: efficacy 1 (no SSc data; the shared mechanism just failed in HS),
  differentiation 2, PoS 0.12, peak 0.6B.
- ADCT: Oct 8 2026 restructuring: $86.6M PIPE (Bain, Redmile, TCGX, Nantahala at $1.42), senior loan cut to $50M (bullet
  Aug 2029), HCR royalty deal amended (no change-of-control payment). Debt incl. the HCR obligation ~ $350M (was $420M);
  cash ~ $206M pro forma; runway into 2029.
- RCUS: PRISM-1 (quemliclustat, pancreatic) Ph3 discontinued Nov 23 2026 for futility; casdatifan stays the lead (note only)."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
for r in D:
    t = r['ticker']
    if t == 'ZURA':
        r.update({'indication': 'Systemic sclerosis (SSc); polymyalgia rheumatica (PMR). HS discontinued after Ph2 failure (Nov 2026)', 'effsig': 1, 'diffscore': 2, 'pos': 0.12, 'peak_sales': 0.6e9,
                  'eff_short': 'Ph2 TibuSHIELD (HS, n=247) missed primary and key secondary endpoints (AN count -56%/-58% vs -52.5% placebo); HS discontinued. SSc (TibuSURE, n=91) topline H1 2027.',
                  'catalyst': 'TibuSURE Ph2 SSc topline (H1 2027); NEXUS-PMR Ph2 start (YE2026)', 'val_note': 'HS failed Nov 9 2026; value now SSc/PMR optionality plus $188M cash vs ~$108M cap'})
    if t == 'ADCT':
        r['debt'] = 349.6e6; r['cash'] = 205.8e6; r['runway_q'] = 10.0
        r['val_note'] = 'Oct 2026 restructuring: $86.6M PIPE, loan cut to $50M, HCR royalty obligation remains'
    if t == 'RCUS':
        r['val_note'] = 'PRISM-1 (quemliclustat, pancreatic) Ph3 discontinued Nov 23 2026 for futility; casdatifan is the lead'
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('patched ZURA ADCT RCUS')
