"""Valuation review, 2026-11-23: inputs that disagreed with the profile of the lead drug.
Sources: company Q3 2026 results (GERN, LENZ, VNDA), Merck's $6.7B purchase of Terns (TERN-701, CML, Mar 2026),
and the row's own revenue/peak-basis fields. Model-level rules (valuation v2) live in pipeline/template.html valParts().
Sets peak_sales / pos (and probadj_sales = peak x PoS) plus a one-line val_note; book_add marks companies whose
product revenue is separate from the lead program. Re-running is harmless."""
import json, sys

FIX = {
    # ticker: (peak_sales, pos, note)
    'VNDA': (500e6, None, 'Peak cut $3.75B→$0.5B: BYSANTI is bioequivalent to Fanapt (Q2 Fanapt sales $36M) in a generic class'),
    'LENZ': (300e6, 0.7, 'Peak cut $0.9B→$0.3B, launch PoS 70%: VIZZ sold $2.6M in Q3, sales force cut, CEO leaving'),
    'GERN': (450e6, None, 'Peak cut $0.7B→$0.45B: RYTELO guided $220-240M for 2026, MF trial stopped Oct 28'),
    'OTLK': (150e6, 0.7, 'Peak cut $0.5B→$0.15B: competes with cheap off-label Avastin; $9K sales in the quarter'),
    'MIST': (200e6, None, 'Peak cut $0.42B→$0.2B: CARDAMYST sold <$1M in the quarter'),
    'ALT':  (2.5e9, 0.25, 'Peak $4.5B→$2.5B, PoS 40%→25%: 24-wk fibrosis biopsy missed; obesity/MASH is crowded'),
    'SRPT': (1.0e9, 0.9, 'Peak $2.4B→$1.0B: ELEVIDYS label restricted after deaths; current sales now set the value'),
    'ELVN': (2.5e9, 0.35, 'Peak $0.45B→$2.5B, PoS 16%→35%: validated CML target, Ph3 starting; Merck paid $6.7B for Terns\' rival'),
    'KNSA': (1.8e9, None, 'Peak $0.9B→$1.8B: ARCALYST already guided ~$1B for 2026 and growing'),
}
BOOK = ['INCY', 'EXEL', 'UTHR', 'MIRM', 'ALKS', 'ZLAB', 'IRWD']

path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
n = 0
for r in D:
    t = r['ticker']
    if t in FIX:
        pk, pos, note = FIX[t]
        r['peak_sales'] = pk
        if pos is not None:
            r['pos'] = pos
        if isinstance(r.get('pos'), (int, float)):
            r['probadj_sales'] = pk * r['pos']
        r['val_note'] = note
        n += 1
    if t in BOOK:
        r['book_add'] = True
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('valuation inputs fixed', n, '· book_add', len(BOOK))
