"""Short interest per covered company from stockanalysis.com statistics pages (free; exchange-reported short interest,
updated twice a month). Same etiquette as fetch_targets.py: one request at a time, a pause, an honest user agent; a page
that fails keeps last week's row (keep:1). Writes data/short-interest.json as
{ticker: {si, si_prev, pct_out, pct_float, dtc, fetched}}. Borrow fees are not available free.
Usage: python3 scripts/fetch_shortint.py [--only T1,T2] [--pause 0.8]"""
import json, re, sys, time, urllib.request, datetime as dt
ROOT = __file__.rsplit('/scripts/', 1)[0]
UA = 'BioStocks-dashboard/1.0 (weekly research script; low volume)'
OUT = ROOT + '/data/short-interest.json'
def num(h):
    if h is None or h == 'n/a': return None
    h = h.replace(',', '').replace('%', '')
    try: return float(h)
    except ValueError: return None
def parse(html):
    g = lambda k: (re.search(r'\{id:"%s",title:"[^"]*",value:"[^"]*",hover:"([^"]*)"' % k, html) or [None, None])[1]
    si = num(g('shortInterest'))
    if si is None: return None
    return {'si': si, 'si_prev': num(g('shortPriorMonth')), 'pct_out': num(g('shortShares')), 'pct_float': num(g('shortFloat')), 'dtc': num(g('shortRatio'))}
def main():
    a = sys.argv[1:]
    only = a[a.index('--only') + 1].split(',') if '--only' in a else None
    pause = float(a[a.index('--pause') + 1]) if '--pause' in a else 0.8
    D = json.load(open(ROOT + '/data/data.json'))
    tick = only or sorted({r['ticker'] for r in D if r.get('ta') != 'Acquired / Inactive' and r.get('ticker')})
    try: old = json.load(open(OUT))
    except Exception: old = {}
    new = dict(old) if only else {}
    ok = kept = 0; today = dt.date.today().isoformat()
    for i, t in enumerate(tick):
        try:
            req = urllib.request.Request('https://stockanalysis.com/stocks/%s/statistics/' % t.lower(), headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=25) as r: html = r.read().decode('utf-8', 'replace')
            p = parse(html)
            if p: p['fetched'] = today; new[t] = p; ok += 1
            else: new.pop(t, None)
        except Exception as e:
            if t in old: new[t] = dict(old[t], keep=1); kept += 1
            if '403' in str(e) or '429' in str(e):
                print('stopped: site refused (%s) at %s' % (e, t))
                for u in tick[i + 1:]:
                    if u in old: new[u] = dict(old[u], keep=1)
                break
        time.sleep(pause)
    json.dump(new, open(OUT, 'w'), separators=(',', ':'), sort_keys=True)
    print('short interest: %d fetched, %d kept from last time; %d names in file' % (ok, kept, len(new)))
if __name__ == '__main__': main()
