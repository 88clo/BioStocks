"""Paired-comparison fixes (Nov 25 2026), after the PM's spot check that EVMN's rNPV exceeded CRVS's.
Cause 1: the model valued only each company's lead. CRVS's lead is PTCL ($660M peak); its atopic dermatitis program
(soquelitinib, oral ITK inhibitor: Ph1 n=72, EASI -72% vs -40% placebo, EASI-75 ~75% in small n, also active in
dupilumab-refractory patients) carried no value. Now added via r.programs: AD peak $2.5B (oral, differentiated), PoS 15%
(Ph1 -> approval for a differentiated oral in AD), 6 years.
Cause 2: EVMN's EVO301 peak was set from AD prevalence ($3.2B). Its Ph2a showed EASI-75 29% vs 9% at week 12, below
dupilumab's ~45-50%, and the oral MRGPRX2 (EVO756) failed in AD and CSU. Peak cut to $0.8B (a sub-dupilumab injectable
in a crowded market); the model's weak-data PoS cap and undifferentiated haircut still apply.
BRVE: BHB-1893 would be the third cardiac myosin inhibitor after mavacamten and aficamten, with a 42-patient OLE; peak
$3.0B -> $1.0B. AVXL: blarcamesine's subgroup-based Ph2/3 was found insufficient by FDA/EMA; peak $6.0B -> $2.0B."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
for r in D:
    t = r['ticker']
    if t == 'CRVS':
        r['programs'] = [{'name': 'Soquelitinib in atopic dermatitis (Ph1)', 'peak': 2.5e9, 'pos': 0.15, 'y': 6}]
    if t == 'EVMN':
        r['peak_sales'] = 8e8; r['probadj_sales'] = 8e8 * r['pos']
        r['val_note'] = 'Peak cut $3.2B→$0.8B: EASI-75 29% at wk 12 is below dupilumab (~45-50%); EVO756 failed in AD and CSU'
    if t == 'BRVE':
        r['peak_sales'] = 1e9; r['probadj_sales'] = 1e9 * r['pos']
        r['val_note'] = 'Peak cut $3.0B→$1.0B: third cardiac myosin inhibitor behind mavacamten and aficamten'
    if t == 'AVXL':
        r['peak_sales'] = 2e9; r['probadj_sales'] = 2e9 * r['pos']
        r['val_note'] = 'Peak cut $6.0B→$2.0B: FDA/EMA found the subgroup-based Ph2/3 insufficient; confirmatory trial needed'
    # Second programs the lead-only model left at zero (from each company's own description; conservative odds)
    if t == 'ZBIO': r['programs'] = [{'name': 'Obexelimab in SLE (Ph2)', 'peak': 1.5e9, 'pos': 0.10, 'y': 6}]
    if t == 'DNLI': r['programs'] = [{'name': 'Sanfilippo A (BLA planned 2027)', 'peak': 4e8, 'pos': 0.5, 'y': 2}]
    if t == 'IMCR': r['programs'] = [{'name': 'Brenetafusp (PRAME) Ph3 in melanoma', 'peak': 1e9, 'pos': 0.3, 'y': 3}]
    if t == 'KYTX': r['programs'] = [{'name': 'Miv-cel in myasthenia gravis and lupus nephritis', 'peak': 6e8, 'pos': 0.15, 'y': 5}]
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('patched CRVS, EVMN, BRVE, AVXL; second programs ZBIO, DNLI, IMCR, KYTX')
