"""Events found by the first 8-K scan (scripts/scan_8k.py, filings Nov 19-25 2026).
INSM: Sanofi agreed to acquire Insmed for $175/share in cash, $41.0B total (8-K and press release Nov 24 2026). Now merger
      arbitrage: call held at HOLD (override), price $170.31 (Nov 25), spread ~2.8% to deal price.
RCUS: Phase 3 PRISM-1 (quemliclustat + gem/nab-pac, 1L metastatic pancreatic cancer) discontinued Nov 23 2026 after an
      interim OS analysis showed no benefit (IDMC). Lead casdatifan is unaffected; noted in the record. Price $17.84.
KYMR: proposed $1.5B underwritten public offering (+$225M option) announced Nov 23-24 2026 after BROADEN2; cash shown
      before proceeds until the pricing 8-K."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
for r in D:
    t = r['ticker']
    if t == 'INSM':
        r['mc'] = round(r['mc'] / r['price'] * 170.31); r['price'] = 170.31
        r['call_override'] = 'HOLD'
        r['call_reason'] = r['pitch'] = r['pitch_concise'] = ('Sanofi agreed on Nov 24 to acquire Insmed for $175 a share in cash ($41.0B). '
            'The stock trades at ~$170, a ~2.8% spread; this is now merger arbitrage, so we hold no fundamental view.')
        cs = r.get('cat_sched') or []
        if not any('Sanofi' in c.get('e', '') for c in cs):
            cs.insert(0, {'d': '2027-03-31', 'e': 'Sanofi acquisition of Insmed: regulatory clearances and close ($175/share cash)', 'st': 'up', 'k': 1})
        r['cat_sched'] = cs
    if t == 'RCUS':
        r['mc'] = round(r['mc'] / r['price'] * 17.84); r['price'] = 17.84
        cs = r.get('cat_sched') or []
        if not any('PRISM-1' in c.get('e', '') for c in cs):
            cs.append({'d': '2026-11-23', 'e': 'PRISM-1 Ph3 (quemliclustat, 1L metastatic pancreatic cancer) interim OS analysis', 'st': 'done',
                       'outcome': 'Negative: discontinued after the interim analysis showed no OS benefit (IDMC, Nov 23 2026).'})
        r['cat_sched'] = cs
        r['pipeline_note'] = 'PRISM-1 (quemliclustat, pancreatic) discontinued Nov 23 2026 for futility on OS; casdatifan (HIF-2α, ccRCC) remains the lead.'
    if t == 'RARE':  # 8-K Nov 23: the FAYUVI priority review voucher sale closed on Nov 20
        for c in r.get('cat_sched') or []:
            if 'PRV sale' in c.get('e', '') and c.get('st') != 'done': c['st'] = 'done'; c['d'] = '2026-11-20'; c['outcome'] = 'Closed Nov 20 2026 (8-K Nov 23).'
    if t == 'QURE':  # uniQure release Nov 2 2026: BLA accepted with priority review, PDUFA May 1 2027, advisory committee tentatively planned
        for c in r.get('cat_sched') or []:
            if 'BLA acceptance' in c.get('e', '') and c.get('st') != 'done':
                c['st'] = 'done'; c['d'] = '2026-11-02'; c['outcome'] = 'Accepted with priority review (Nov 2 2026); PDUFA May 1 2027; FDA tentatively plans an advisory committee.'
        if not any('advisory committee' in c.get('e', '').lower() for c in r['cat_sched']):
            r['cat_sched'].append({'d': '2027-03-31', 'e': 'FDA advisory committee on AMT-130 (tentative; before the May 1 2027 PDUFA)', 'st': 'up', 'k': 1})
    if t == 'KYMR':
        r['offering_note'] = 'Proposed $1.5B public offering (+$225M underwriter option) announced Nov 23 2026; cash shown before proceeds.'
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('patched INSM, RCUS, KYMR')
