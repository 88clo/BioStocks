"""COLL peak input (Nov 25 2026): the $3.2B 'peak' exceeded the whole company's sales (~$865M in 2026, FY guide $825-855M;
JORNAY PM ~$200M/yr growing, pain portfolio shrinking ~18%). Peak set to $1.05B for the company (ADHD growth offsetting
pain decline). Model change alongside: equity is now valued off net cash (cash - debt), template netCash()."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
for r in D:
    if r['ticker'] == 'COLL':
        r['peak_sales'] = 1.05e9; r['probadj_sales'] = 1.05e9 * (r.get('pos') or 1)
        r['val_note'] = 'Peak cut $3.2B→$1.05B: total company sales ~$865M (2026); ADHD growth offsets the shrinking pain portfolio'
    if r['ticker'] == 'ACOG':
        r['peak_sales'] = 1.5e8; r['probadj_sales'] = 1.5e8 * (r.get('pos') or 1)
        r['val_note'] = 'Peak cut $0.96B→$0.15B: ZUNVEYL is a galantamine reformulation selling ~$31M/yr against generic donepezil'
    if r['ticker'] == 'BHC':  # $20B of debt belongs to Bausch Health's ~$10B/yr existing business, which the model doesn't value; the row values larsucosterol only
        r['debt_excl'] = True
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('COLL peak set')
