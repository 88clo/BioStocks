"""Learn from history (Nov 27 2026, PM review: 'learn from historical lessons over time', no fixed formulas).
Reads the graded catalyst post-mortems (data/postmortems.json, built from frozen weekly expectations) and scores two
forecasters on every resolved event with a clear outcome:
  - ours: pe, our probability of a good outcome;
  - the market's: pm = -dn / (up - dn), the probability at which the price is fair given the moves we expected
    (if the price already balanced a good and a bad outcome, that is the odds it was paying for).
Brier score (mean squared error of a probability, lower = better) for each, overall and by event type and stage.
The weight on our view in the scenarios is set by relative accuracy (inverse Brier), shrunk toward 50/50 by a prior worth
PRIOR events, so a handful of readouts cannot swing it: w = (n*w_hat + PRIOR*0.5) / (n + PRIOR).
Also writes plain-language lessons: where we were over- or under-confident (our average pe vs how often it came good).
Writes data/calibration.json; the page reads w. Run monthly (and whenever post-mortems are rebuilt)."""
import json, pathlib, datetime as dt, collections
root = pathlib.Path(__file__).resolve().parents[1]
PRIOR = 20
pm_ = json.load(open(root / 'data/postmortems.json'))
ev = [e for e in pm_.get('events', []) if e.get('outcome') in ('good', 'bad')]
rows = []
for e in ev:
    x = e.get('expected') or e
    pe, up, dn = x.get('pe'), x.get('up'), x.get('dn')
    if pe is None: continue
    pmk = x.get('pm')
    if pmk is None and up and dn and up > 0 and dn < 0: pmk = -dn / (up - dn)
    y = 1.0 if e['outcome'] == 'good' else 0.0
    rows.append({'t': e.get('t'), 'ty': x.get('ty') or e.get('ty') or 'other', 'stage': e.get('stage') or '', 'pe': pe, 'pm': pmk, 'y': y})
def brier(L, k): 
    v = [(r[k] - r['y']) ** 2 for r in L if r.get(k) is not None]
    return (sum(v) / len(v), len(v)) if v else (None, 0)
bo, n = brier(rows, 'pe'); bm, nm = brier([r for r in rows if r['pm'] is not None], 'pm')
if bo is not None and bm is not None and n:
    w_hat = (1 / max(bo, 1e-4)) / ((1 / max(bo, 1e-4)) + (1 / max(bm, 1e-4)))
    w = (n * w_hat + PRIOR * 0.5) / (n + PRIOR)
else:
    w_hat, w = None, 0.5
by = collections.defaultdict(list)
for r in rows: by[r['ty']].append(r)
types, lessons = [], []
for ty, L in sorted(by.items(), key=lambda kv: -len(kv[1])):
    a, _ = brier(L, 'pe'); b, _ = brier([r for r in L if r['pm'] is not None], 'pm')
    mp = sum(r['pe'] for r in L) / len(L); hit = sum(r['y'] for r in L) / len(L)
    types.append({'type': ty, 'n': len(L), 'our_avg_p': round(mp, 3), 'came_good': round(hit, 3), 'brier_ours': a and round(a, 4), 'brier_market': b and round(b, 4)})
    if len(L) >= 5 and abs(mp - hit) >= 0.15:
        lessons.append('%s: we gave %d%% on average and %d%% came good (%d events): we were %s; shade new %s odds %s.' % (
            ty, round(mp * 100), round(hit * 100), len(L), 'over-confident' if mp > hit else 'under-confident', ty, 'down' if mp > hit else 'up'))
out = {'w': round(w, 3), 'n': n, 'brier_ours': bo and round(bo, 4), 'brier_market': bm and round(bm, 4), 'w_raw': w_hat and round(w_hat, 3),
       'prior_events': PRIOR, 'by_type': types, 'lessons': lessons, 'built': dt.date.today().isoformat(),
       'basis': ('%d resolved events: our Brier %.3f vs the market\'s %.3f.' % (n, bo, bm)) if n and bo is not None and bm is not None else
                'No resolved events with a clear outcome yet: our PoS and the market\'s implied PoS are weighted equally until the record builds.'}
json.dump(out, open(root / 'data/calibration.json', 'w'), indent=1)
print('calibration: w=%.2f from %d resolved events' % (w, n))
