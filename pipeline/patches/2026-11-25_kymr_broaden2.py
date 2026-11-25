"""KYMR: BROADEN2 Ph2b read out positive on Nov 23 2026 (after the Nov 20 snapshot).
Source: Kymera press release / 8-K, Nov 23 2026 (investors.kymeratx.com). 244 patients, 16 weeks, 3 doses vs placebo.
Mid dose: EASI -72% vs -27% placebo (placebo-adjusted 45 points, p<0.0001); vIGA 0/1 38% vs 11% (p=0.0008); all doses met
primary and secondary endpoints; conjunctivitis 11.1-19.7% (mild-moderate, no discontinuations); 4 SAEs, judged unrelated.
Phase 3 in AD planned by mid-2027; BREADTH Ph2b asthma data late 2027. Stock: $115.31 (Nov 20) -> $171.55 (Nov 25)."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
for r in D:
    if r['ticker'] != 'KYMR': continue
    sh = r['mc'] / r['price']
    r['price'] = 171.55; r['mc'] = round(sh * 171.55)
    r['stage'] = 'Phase 2b complete (Phase 3 start by mid-2027)'
    r['eff_short'] = 'Ph2b BROADEN2 (244 AD pts, 16 wks): mid dose EASI -72% vs -27% placebo (45-pt placebo-adjusted, p<0.0001); vIGA 0/1 38% vs 11%; all 3 doses met primary and secondary endpoints.'
    r['efficacy'] = ('Ph2b BROADEN2 (moderate-to-severe AD, 244 patients incl. adolescents, 16 weeks, three once-daily oral doses vs placebo; '
                     'topline Nov 23 2026): mid dose mean EASI reduction 72% vs 27% placebo (placebo-adjusted 45 points, p<0.0001); '
                     'vIGA-AD 0/1 38% vs 11% (p=0.0008); EASI and itch improved from week 1; all three doses met primary and secondary endpoints. '
                     'Safety: conjunctivitis 11.1-19.7% on drug (mild to moderate, no discontinuations); 4 SAEs across arms, judged unrelated. '
                     'Earlier: Ph1b BroADen (22 AD patients) showed deep STAT6 degradation in blood and skin.')
    r['bench_short'] = 'AD at week 16: dupilumab EASI ~-70% (pbo-adj ~-40 pts), IGA 0/1 ~37%; KT-621 mid dose -72% EASI and 38% vIGA 0/1 = dupilumab-class from a once-daily pill.'
    r['effsig'] = 5; r['diffscore'] = 5
    r['pos'] = 0.6
    r['call_reason'] = ('BROADEN2 hit on Nov 23: dupilumab-class efficacy (EASI -72% vs -27%, vIGA 0/1 38% vs 11%) from a once-daily pill, '
                        'clean apart from mild conjunctivitis. The stock rose 49% to ~$17B, which now prices most of that; we moved PoS to 60% '
                        'and wait for Phase 3 design, dose choice and the asthma read before adding.')
    r['stage_full'] = 'Phase 2b BROADEN2 positive (topline Nov 23 2026); Phase 3 in AD targeted by mid-2027; BREADTH asthma Ph2b late 2027.'
    r['catalyst'] = 'KT-621 Phase 3 start in atopic dermatitis (by mid-2027)'; r['nc'] = '1H 2027 KT-621 Phase 3 start (AD)'
    r['diff_detail'] = 'High: first oral STAT6 degrader with dupilumab-class Ph2b efficacy (EASI -72% vs -27%, vIGA 0/1 38% vs 11%) in a once-daily pill.'
    r['value_driver'] = '"Oral dupilumab": BROADEN2 showed dupilumab-class efficacy in a pill; Phase 3 in AD and the asthma Ph2b decide how much of the ~$17B is earned.'
    r['pitch'] = r['pitch_concise'] = 'BROADEN2 hit on Nov 23 (EASI -72% vs -27%, vIGA 0/1 38% vs 11%); after a 49% move to ~$17B with $1.6B cash, the stock now prices a Phase 3 win in AD.'
    for c in r.get('cat_sched') or []:
        if 'BROADEN2' in c.get('e', ''):
            c['st'] = 'done'; c['d'] = '2026-11-23'; c['outcome'] = 'Positive: all doses met primary and secondary endpoints; mid dose EASI -72% vs -27% placebo, vIGA 0/1 38% vs 11%.'
    have = ' '.join(c.get('e', '') for c in r['cat_sched'])
    if 'Phase 3' not in have:
        r['cat_sched'].append({'d': '2027-06-30', 'e': 'KT-621 Phase 3 program start in atopic dermatitis (by mid-2027)', 'st': 'up', 'k': 1, 'p': 1})
    if 'BREADTH' not in have:
        r['cat_sched'].append({'d': '2027-12-31', 'e': 'KT-621 BREADTH Ph2b topline in eosinophilic asthma (late 2027)', 'st': 'up', 'p': 1})
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('KYMR updated')
