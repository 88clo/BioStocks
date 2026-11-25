"""Events between the Nov 20 snapshot and Nov 25 2026 (besides KYMR, in 2026-11-25_kymr_broaden2.py).
CAPR: second CRL for deramiocel on Nov 20 (after close): insufficient evidence of effectiveness, plus an FDA BIMO
      inspection that found HOPE-3 conduct/data-integrity deficiencies the agency says cannot be fixed retrospectively.
      Stock $7.59 -> $2.01 (Nov 25). Capricor press release Nov 20; FDA statement Nov 20.
SVRA: FDA said on Nov 20 it will miss the Nov 22 PDUFA for molgramostim; review ongoing, no new date (already in the
      $4.26 Nov 20 price; $4.45 Nov 25). Lowered PoS 0.97 -> 0.80 while the reason is unknown.
HELP: APPROACH Ph3 read out positive on Nov 16 (already in the call); mark the catalyst done. $6.11 -> $8.07."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
PX = {'CAPR': 2.01, 'SVRA': 4.45, 'HELP': 8.07}
for r in D:
    t = r['ticker']
    if t not in PX: continue
    r['mc'] = round(r['mc'] / r['price'] * PX[t]); r['price'] = PX[t]
    cs = r.get('cat_sched') or []
    if t == 'CAPR':
        r['pos'] = 0.05; r['stage'] = 'CRL (Nov 2026)'
        r['call_reason'] = ('Second CRL on Nov 20: FDA found HOPE-3 did not show substantial evidence of effectiveness and its '
                            'inspection flagged trial-conduct and data-integrity problems it says cannot be corrected after the fact. '
                            'The stock trades near cash, but a new controlled trial is the only path and cash burn makes that '
                            'a financing story; no edge either way.')
        for c in cs:
            if 'PDUFA' in c.get('e', '') or 'BLA decision' in c.get('e', ''):
                c['st'] = 'done'; c['outcome'] = 'CRL (Nov 20 2026): insufficient evidence of effectiveness; HOPE-3 data-integrity findings.'
        r['pitch'] = r['pitch_concise'] = 'Second CRL on Nov 20: FDA cited insufficient evidence of effectiveness and HOPE-3 data-integrity findings it says cannot be fixed retrospectively; the stock fell ~74% to near cash, and only a new trial reopens the path.'
        if not any('second CRL' in c.get('e','') for c in cs): cs.append({'d': '2027-03-31', 'e': 'Capricor response plan after second CRL (Type A meeting / new trial design)', 'st': 'up', 'k': 1})
    if t == 'SVRA':
        r['pos'] = 0.8
        r['call_reason'] = ('FDA missed the Nov 22 PDUFA (said Nov 20) with no new date and no stated reason; IMPALA-2 hit every '
                            'endpoint, so the miss is more likely CMC or process than efficacy, but until FDA acts we cut PoS to 80% '
                            'and stay on WATCH. Approval also unlocks ~$150M of non-dilutive capital.')
        for c in cs:
            if 'PDUFA' in c.get('e', ''):
                c['st'] = 'late'; c['outcome'] = 'FDA missed the Nov 22 goal date (announced Nov 20); review ongoing, no new date.'
        r['pitch'] = r['pitch_concise'] = 'FDA missed the Nov 22 PDUFA for molgramostim with no new date or stated reason; IMPALA-2 hit every endpoint, so we expect a delayed approval, but cash of ~$130M and approval-contingent financing make timing matter.'
        if not any('missed Nov 22' in c.get('e','') for c in cs): cs.append({'d': '2027-02-28', 'e': 'FDA action on molgramostim BLA (aPAP) after missed Nov 22 goal date', 'st': 'up', 'k': 1, 'p': 1})
    if t == 'HELP':
        for c in cs:
            if 'APPROACH' in c.get('e', ''):
                c['st'] = 'done'; c['d'] = '2026-11-16'; c['outcome'] = 'Positive: MADRS -7.6 vs placebo at week 6 (n=222); remission 50.9% vs 18.2%.'
    r['cat_sched'] = cs
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('patched', list(PX))
