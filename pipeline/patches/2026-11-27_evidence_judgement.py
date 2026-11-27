"""Evidence scores re-judged on the totality of the data (Nov 27 2026), replacing the stage discount the PM rejected:
an unprecedented early result in a big, poorly served market should score high, and biomarker-only or mixed data lower,
whatever the phase.
- BBOT 2 -> 4: Ph1 ONKORAS-101 BBO-8520 monotherapy 63% ORR / 100% DCR in KRAS G12C-inhibitor-naive NSCLC (n=41) with no
  grade 3 liver enzyme rises, above the approved G12C inhibitors' single-agent response rates, plus activity after prior G12C
  inhibitors.
- ARVN 4 -> 2: ARV-102 has target engagement only (>50% LRRK2 knockdown in CSF); no clinical efficacy yet. Differentiation
  (a brain-penetrant degrader) stays 4.
- ALT 4 -> 3: pemvidutide missed the 24-week MASH fibrosis biopsy endpoint; weight loss without plateau at 48 weeks is real
  but the data are mixed."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path)); E = {'ARVN': 2, 'ALT': 3}  # BBOT's 2 -> 4 here was reversed to 3 by 2026-11-27_readthrough.py
for r in D:
    if r['ticker'] in E: r['effsig'] = E[r['ticker']]
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('efficacy re-judged:', E)
