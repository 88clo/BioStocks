"""First FDA approval of the lead program, for approvals between mid-2024 and today (approved_on, YYYY-MM-01).
Lets Record > What worked put a company in 'Ph3 / filed' for quarters before its first approval.
Found by a text parse of each row (stage, efficacy, pitch, catalysts) plus hand review; label expansions excluded."""
import json, sys
A = {'CELC': '2026-07-01', 'CYTK': '2025-12-01', 'DNLI': '2026-03-01', 'FBIO': '2026-01-01', 'INO': '2026-10-01',
     'KURA': '2025-11-01', 'LENZ': '2026-07-01', 'MIST': '2025-12-01', 'NRXP': '2026-10-01', 'OMER': '2025-12-01',
     'OTLK': '2026-07-01', 'PHAR': '2026-08-01', 'PTGX': '2026-03-01', 'REPL': '2026-08-01', 'VERA': '2026-07-01',
     'VRDN': '2026-06-01'}
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
for r in D:
    if r['ticker'] in A: r['approved_on'] = A[r['ticker']]
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('approved_on set', sum(1 for r in D if r.get('approved_on')))
