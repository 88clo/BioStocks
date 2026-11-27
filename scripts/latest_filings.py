"""Latest news per company for the card (Nov 27 2026; replaces the never-refreshed press-release snapshot pr-baked).
Keeps, per ticker, the most recent item from: the weekly 8-K scan (data/8k.json, SEC EDGAR) and the old press-release
snapshot (data/pr-baked.json, Nov 22 and earlier, used only until a newer filing arrives). Writes data/latest-filings.json
as {ticker: {date: 'MM/DD/YY', headline, sentiment, url, src}} (date format kept for the card's sort). Run weekly after
scan_8k.py."""
import json, datetime as dt
ROOT = __file__.rsplit('/scripts/', 1)[0]
OUT = ROOT + '/data/latest-filings.json'
iso = lambda mdy: dt.datetime.strptime(mdy, '%m/%d/%y').date().isoformat()
try: cur = json.load(open(OUT))
except Exception:
    cur = {}
    for t, p in json.load(open(ROOT + '/data/pr-baked.json')).items():
        if p.get('date'): cur[t] = dict(p, src='press release (StockTitan, Nov 22 snapshot)')
k = json.load(open(ROOT + '/data/8k.json'))
n = 0
for r in k.get('rows', []):
    t, d = r.get('t'), r.get('date')
    if not t or not d: continue
    old = cur.get(t)
    if old and iso(old['date']) >= d: continue
    lab = ', '.join(r.get('item_l') or []) or 'filing'
    head = (r.get('title') or '').strip() or ('8-K: ' + lab)
    cur[t] = {'date': dt.date.fromisoformat(d).strftime('%m/%d/%y'), 'headline': head[:220], 'sentiment': r.get('form', '8-K'),
              'url': r.get('url'), 'src': 'SEC ' + r.get('form', '8-K') + ' (' + lab + ')'}
    n += 1
json.dump(cur, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'), sort_keys=True)
print('latest filings: %d updated from the 8-K scan; %d companies' % (n, len(cur)))
