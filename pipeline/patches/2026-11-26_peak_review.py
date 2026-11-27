"""Peak-sales review from the same-indication scan (Nov 26 2026). Large prevalence-driven peaks on early names mostly sit on
shorts and avoids (where they flatter the bull case, so they are conservative); the two longs that leaned on them are cut.
Low peaks on approved/filed names with strong data are raised where launch numbers or outside estimates support it.
- NUVB: IBTROZI net sales $27.5M in Q3 2026 (+18% q/q, ~920 starts); S&P consensus path ~$1B by 2035; peak 0.385 -> 0.8B.
- KURA: 0.1B looked like current run-rate. KOMZIFTI $9.1M Q2 2026 with majority share of new R/R NPM1 starts; Kura keeps
  ~half of US economics with Kyowa Kirin. R/R economics peak 0.3B; frontline combos (KOMET-017 Ph3) as a separate program
  at $1.0B Kura economics, 35% PoS, 3 years.
- VYGR: anti-tau Ph1 with efficacy 2/5 carried a $6B peak; scaled to 2.0B.
- ACIU: Ph2 vaccine with efficacy 2/5 carried 2.45B; scaled to 1.5B.
Still to review with fresh outside estimates: IDYA (0.5B), VERA (1.25B), GLSI (0.14B), IPHA (0.02B, royalty basis after the Sobi deal)."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
for r in D:
    t = r['ticker']
    if t == 'NUVB': r['peak_sales'] = 0.8e9; r['val_note'] = 'IBTROZI $27.5M Q3 2026 (+18% q/q); consensus path ~$1B by 2035'
    if t == 'KURA':
        r['peak_sales'] = 0.3e9
        r['programs'] = [p for p in (r.get('programs') or []) if 'frontline' not in p.get('name', '')] + [{'name': 'Ziftomenib frontline combos (KOMET-017)', 'peak': 1.0e9, 'pos': 0.35, 'y': 3}]
        r['val_note'] = 'R/R economics ~0.3B (half of US with Kyowa Kirin); frontline combos valued separately'
    if t == 'VYGR': r['peak_sales'] = 2.0e9; r['val_note'] = 'Peak scaled to Ph1 data quality (efficacy 2/5), not tau-AD prevalence'
    if t == 'ACIU': r['peak_sales'] = 1.5e9; r['val_note'] = 'Peak scaled to Ph2 data quality (efficacy 2/5)'
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('peaks patched: NUVB KURA VYGR ACIU')
