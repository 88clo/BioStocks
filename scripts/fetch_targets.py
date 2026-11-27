"""Analyst price targets from stockanalysis.com (free; S&P Global data), replacing the Yahoo snapshot Yahoo stopped serving.

Reads each covered ticker's public forecast page (/stocks/<t>/forecast/, allowed by the site's robots.txt), one request
at a time with a pause between them and an honest user agent, and parses the consensus block embedded in the page:
  targets:{low,high,count,median,average,updated} and consensus:"<rating>".
Writes data/price-targets-baked.json as {ticker: {target (= average), median, low, high, analysts, rating, updated, src}}.
- A ticker whose page fails to load keeps its previous entry (marked keep:1) so one bad week never blanks the column.
- A ticker the site shows with no analyst targets, or whose latest target is over a year old, is dropped (no stale data).
Usage: python3 scripts/fetch_targets.py [--only T1,T2] [--pause 1.2]
"""
import json, re, sys, time, urllib.request, datetime as dt

ROOT = __file__.rsplit('/scripts/', 1)[0]
UA = 'BioStocks-dashboard/1.0 (weekly research script; low volume)'
OUT = ROOT + '/data/price-targets-baked.json'


def fetch(t):
    req = urllib.request.Request('https://stockanalysis.com/stocks/%s/forecast/' % t.lower(), headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, r.read().decode('utf-8', 'replace')


def parse(html):
    m = re.search(r'targets:\{low:([\d.]+|null),high:([\d.]+|null),count:(\d+),median:([\d.]+|null),average:([\d.]+|null),updated:"([\d-]+)"', html)
    if not m:
        return None
    num = lambda s: None if s == 'null' else float(s)
    lo, hi, n, med, avg, upd = num(m[1]), num(m[2]), int(m[3]), num(m[4]), num(m[5]), m[6]
    c = re.search(r'consensus:"([^"]+)"', html)
    if not n or not avg:
        return None
    return {'target': round(avg, 2), 'median': med, 'low': lo, 'high': hi, 'analysts': n,
            'rating': c[1] if c else None, 'updated': upd, 'src': 'stockanalysis.com'}


def main():
    a = sys.argv[1:]
    only = a[a.index('--only') + 1].split(',') if '--only' in a else None
    pause = float(a[a.index('--pause') + 1]) if '--pause' in a else 1.2
    D = json.load(open(ROOT + '/data/data.json'))
    tick = only or sorted({r['ticker'] for r in D if r.get('ta') != 'Acquired / Inactive' and r.get('ticker')})
    try:
        old = json.load(open(OUT))
    except Exception:
        old = {}
    new = dict(old) if only else {}
    cut = (dt.date.today() - dt.timedelta(days=365)).isoformat()
    ok = kept = none = 0
    for i, t in enumerate(tick):
        try:
            st, html = fetch(t)
            p = parse(html) if st == 200 else None
            if p and p['updated'] >= cut:
                new[t] = p; ok += 1
            else:
                new.pop(t, None); none += 1
        except Exception as e:
            if t in old:
                new[t] = dict(old[t], keep=1); kept += 1
            else:
                none += 1
            if '403' in str(e) or '429' in str(e):
                print('stopped: site refused (%s) at %s; kept previous targets for the rest' % (e, t))
                for u in tick[i + 1:]:
                    if u in old: new[u] = dict(old[u], keep=1); kept += 1
                break
        time.sleep(pause)
    json.dump(new, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    print('price targets: %d fetched, %d kept from last time, %d with no current targets; %d names in file' % (ok, kept, none, len(new)))


if __name__ == '__main__':
    main()
