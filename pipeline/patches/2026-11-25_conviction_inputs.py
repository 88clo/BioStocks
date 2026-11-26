"""Inputs revisited after the PM's review of strong buys (Nov 25 2026).
UPB: verekitug cut annualized exacerbations 56% vs placebo at 100 mg every 12 weeks (VALIANT), in line with tezepelumab's
56% in NAVIGATOR on monthly dosing, with less frequent dosing. Efficacy 3 -> 4. The stock fell ~50% on the day because the
every-24-week arm did not clearly beat Tezspire; it now trades below net cash while Generate (GB-0895, Ph1 biomarkers only,
Ph3 started) is valued at ~$1.2B and GSK paid $1B upfront for Aiolos's Ph1 long-acting anti-TSLP.
APMD: efficacy stays 4/5 (two positive Ph3s), but insomnia and reduced total sleep time from atomoxetine are the known
tolerability risk for chronic nightly use; noted on the valuation."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
for r in D:
    if r['ticker'] == 'UPB':
        r['effsig'] = 4
        r['val_note'] = 'Trades below net cash; peers: Generate ~$1.2B on Ph1 biomarkers, GSK paid $1B upfront for Aiolos (Ph1 anti-TSLP)'
    if r['ticker'] == 'APMD':
        r['val_note'] = 'Risk: atomoxetine causes insomnia and shortens total sleep in some patients; nightly-use tolerability is the main launch question'
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('patched UPB efficacy, APMD risk note')
