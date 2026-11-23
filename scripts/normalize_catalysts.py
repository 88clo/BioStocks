"""Clean every company's catalyst schedule so dates are honest and in order.

For each row in data/data.json:
  * split compound entries ("A 2H 2027; B Dec 2026") into one event per date,
    splitting only on top-level semicolons (not inside parentheses);
  * parse each event's timing into a window [s, d] and a label at the precision
    the company actually gave: exact day -> "Dec 2", month -> "Dec '26",
    quarter -> "4Q26", half -> "2H26", year-end -> "YE26", mid-year -> "mid-27",
    early -> "early 27", year -> "2027";
  * merge duplicates (same drug code, overlapping windows) keeping the more
    precise date;
  * mark status: up (still ahead), late (window passed, not marked done),
    done (achieved / occurred / resolved), und (ongoing / undated);
  * sort: upcoming by expected date, then undated, then late, then done;
  * add row fields next_cat (first upcoming event) and cat_lab (label of the
    key catalyst, replacing the false-precision cat_date such as Dec 31).

Idempotent: re-running on cleaned data gives the same result.
Usage: python3 scripts/normalize_catalysts.py [data/data.json] [--today YYYY-MM-DD]
"""
import json, re, sys, datetime as dt, calendar

MON = {m.lower(): i for i, m in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}
MONRE = r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?'
CONF = {'ash': 12, 'asco': 6, 'esmo': 10, 'aha': 11, 'eahad': 2, 'aacr': 4, 'easl': 5, 'aasld': 11, 'ada': 6, 'ean': 6, 'ctad': 12, 'aan': 4, 'sabcs': 12, 'ats': 5, 'ers': 9, 'acr': 11, 'eular': 6, 'ddw': 5}
SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def yr(s):
    y = int(s)
    return y + 2000 if y < 100 else y


def eom(y, m):
    return dt.date(y, m, calendar.monthrange(y, m)[1])


def win(kind, y, a=None, b=None, day=None):
    """Return (start, end, label, precision) for a parsed token."""
    yy = str(y)[2:]
    if kind == 'day':
        d = dt.date(y, a, day)
        return d, d, f"{SHORT[a-1]} {day}" + ('' if y == TODAY.year else f" '{yy}"), 5
    if kind == 'month':
        return dt.date(y, a, 1), eom(y, b or a), (f"{SHORT[a-1]}" + (f"–{SHORT[b-1]}" if b and b != a else '') + f" '{yy}"), 4
    if kind == 'q':
        return dt.date(y, 3 * a - 2, 1), eom(y, 3 * a), f"{a}Q{yy}", 3
    if kind == 'h':
        return dt.date(y, 6 * a - 5, 1), eom(y, 6 * a), f"{a}H{yy}", 2
    if kind == 'ye':
        return dt.date(y, 10, 1), dt.date(y, 12, 31), f"YE{yy}", 2
    if kind == 'mid':
        return dt.date(y, 4, 1), dt.date(y, 9, 30), f"mid-{yy}", 2
    if kind == 'early':
        return dt.date(y, 1, 1), dt.date(y, 4, 30), f"early {yy}", 2
    if kind == 'y':
        return dt.date(y, 1, 1), dt.date(y, 12, 31), f"{y}", 1
    raise ValueError(kind)


Y = r"'?(20\d\d|\d\d)"
PATS = [
    # exact days
    ('day', re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b'), lambda m: (yr(m[3]), int(m[1]), None, int(m[2]))),
    ('day', re.compile(r'\b' + MONRE + r'\s+(\d{1,2})(?:\s*[-–]\s*\d{1,2})?,?\s+(20\d\d)\b', re.I), lambda m: (int(m[3]), MON[m[1][:3].lower()], None, int(m[2]))),
    # month ranges and months
    ('month', re.compile(r'\b' + MONRE + r'\s*[-–/]\s*' + MONRE + r'\s+(20\d\d)\b', re.I), lambda m: (int(m[3]), MON[m[1][:3].lower()], MON[m[2][:3].lower()], None)),
    ('month', re.compile(r'\b' + MONRE + r'\s+(20\d\d)\b', re.I), lambda m: (int(m[2]), MON[m[1][:3].lower()], None, None)),
    # quarters / halves
    ('q', re.compile(r'\bQ([1-4])\s*' + Y + r'\b', re.I), lambda m: (yr(m[2]), int(m[1]), None, None)),
    ('q', re.compile(r'\b([1-4])Q\s*' + Y + r'\b', re.I), lambda m: (yr(m[2]), int(m[1]), None, None)),
    ('h', re.compile(r'\bH([12])\s*' + Y + r'\b', re.I), lambda m: (yr(m[2]), int(m[1]), None, None)),
    ('h', re.compile(r'\b([12])H\s*' + Y + r'\b', re.I), lambda m: (yr(m[2]), int(m[1]), None, None)),
    ('h', re.compile(r'\b(?:fall|autumn)\s+(20\d\d)\b', re.I), lambda m: (int(m[1]), 2, None, None)),
    ('h', re.compile(r'\bsummer\s+(20\d\d)\b', re.I), lambda m: (int(m[1]), 2, None, None)),
    # conferences with a year
    ('month', re.compile(r'\b(' + '|'.join(CONF) + r')\s+(20\d\d)\b', re.I), lambda m: (int(m[2]), CONF[m[1].lower()], None, None)),
    ('ye', re.compile(r'\b(?:YE|year[- ]end|end[- ]of[- ]|end[- ]|late[- ]|by end )\s*(20\d\d|\d\d)\b', re.I), lambda m: (yr(m[1]), None, None, None)),
    ('mid', re.compile(r'\bmid[- ]?(20\d\d|\d\d)\b', re.I), lambda m: (yr(m[1]), None, None, None)),
    ('early', re.compile(r'\bearly[- ](20\d\d)\b', re.I), lambda m: (int(m[1]), None, None, None)),
    ('y', re.compile(r'(?<![\w/])(20[2-3]\d)\b(?!\s*[-–]\s*\d)'), lambda m: (int(m[1]), None, None, None)),
]
CONF_NOYEAR = re.compile(r'\b(' + '|'.join(CONF) + r')\b', re.I)
DONE = re.compile(r'achieved|occurred|resolved|cleared|reported|\bcompleted\b', re.I)
UND = re.compile(r'^(ongoing|context|undated|tbd|n/?a)?$', re.I)


def strip_parens(s):
    return re.sub(r'\([^()]*\)', ' ', s)


def tokens(s):
    """All timing tokens in s as (start, end, label, precision, pos)."""
    out, used = [], []
    for kind, rx, f in PATS:
        for m in rx.finditer(s):
            if any(a < m.end() and m.start() < b for a, b in used):
                continue
            if kind == 'y' and re.search(r'FY\s*$', s[max(0, m.start() - 3):m.start()], re.I):
                continue
            try:
                y, a, b, day = f(m)
                w = win(kind, y, a, b, day)
            except (ValueError, KeyError):
                continue
            used.append((m.start(), m.end()))
            out.append(w + (m.start(),))
    return sorted(out, key=lambda w: w[4])


def best(toks, prefer_future=True):
    """The most precise token; ignore ones whose window already passed if any future one exists."""
    if not toks:
        return None
    fut = [t for t in toks if t[1] >= TODAY]
    pool = fut if (prefer_future and fut) else toks
    return max(pool, key=lambda t: (t[3], -t[4]))


def parse_timing(t):
    """Timing string from the curated 't' field -> window or None."""
    t = (t or '').strip()
    if UND.match(t):
        return None
    toks = tokens(t)
    if not toks:
        m = CONF_NOYEAR.search(t)
        if m:
            mo = CONF[m[1].lower()]
            y = TODAY.year if mo >= TODAY.month else TODAY.year + 1
            return win('month', y, mo)[:4]
        return None
    # ranges: "2026-27", "End 2026 / Q1 2027", "H2 2026-H1 2027"
    if len(toks) >= 2 and re.search(r'[/–-]|\bor\b', t) and not re.search(r'achieved|occurred', t, re.I):
        a, b = toks[0], toks[-1]
        if b[1] > a[1]:
            return (a[0], b[1], a[2] + '–' + b[2], min(a[3], b[3]))
    m = re.match(r'^(20\d\d)\s*[-–]\s*(\d\d)$', t)
    if m:
        y1, y2 = int(m[1]), yr(m[2])
        return (dt.date(y1, 1, 1), dt.date(y2, 12, 31), f"{y1}–{str(y2)[2:]}", 0)
    w = best(toks, prefer_future=False)
    return w[:4]


def split_top(s):
    parts, depth, cur = [], 0, ''
    for ch in s:
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth = max(0, depth - 1)
        if ch == ';' and depth == 0:
            parts.append(cur.strip())
            cur = ''
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return [p for p in parts if p]


def code(s):
    m = re.match(r'\s*([A-Za-z]{2,}[-‐]?\d{2,}[A-Za-z0-9-]*|[A-Z][A-Za-z0-9-]{3,})', s)
    return m[1].lower() if m and re.search(r'\d', m[1]) else None


def status(e, w, raw_t):
    if DONE.search(raw_t or '') or DONE.search((e or '')[:0]):
        return 'done'
    if w is None:
        return 'und'
    return 'up' if w[1] >= TODAY else 'late'


def mk(t, e, w, k, st):
    o = {'t': t, 'e': e}
    if k:
        o['k'] = 1
    if w:
        o['s'], o['d'], o['lab'] = w[0].isoformat(), w[1].isoformat(), w[2]
        o['p'] = w[3]
    o['st'] = st
    return o


STOP = set('data topline update initial results with from that this will planned expected phase trial study start'.split())


def words(s):
    return {w for w in re.findall(r'[a-z0-9][a-z0-9-]{2,}', re.sub(r'\([^()]*\)', ' ', s.lower())) if w not in STOP and not re.fullmatch(r'20\d\d|\d+', w)}


def similar(a, b):
    if a['e'] == b['e']:
        return True
    if 'd' not in a or 'd' not in b or a['st'] != b['st']:
        return False
    if not (a['s'] <= b['d'] and b['s'] <= a['d']):
        return False
    ca, cb = code(a['e']), code(b['e'])
    if ca and ca == cb:
        return True
    CR = r'\b[A-Za-z]{2,}[-‐]?\d{2,}[A-Za-z0-9-]*\b'
    sa, sb = {x.lower() for x in re.findall(CR, a['e'])}, {x.lower() for x in re.findall(CR, b['e'])}
    if sa & sb and a.get('p', 0) >= 4 and b.get('p', 0) >= 4 and a['d'] == b['d']:
        return True                                   # same drug code, same exact date

    wa, wb = words(a['e']), words(b['e'])
    if not wa or not wb:
        return False
    return len(wa & wb) / min(len(wa), len(wb)) >= 0.75


def events_from(text, timing, key, nc=False):
    """Split one curated text into dated events."""
    text = (text or '').strip()
    if not text:
        return []
    raw_t = timing or ''
    base = parse_timing(raw_t) if timing else None
    st0 = 'done' if DONE.search(raw_t) else None
    segs = split_top(text) if not st0 else [text]
    if nc:
        segs = [x for sg in segs for x in (re.split(r'\s+\+\s+', sg) if all(len(p.split()) >= 3 for p in re.split(r'\s+\+\s+', sg)) else [sg])]
        lead = tokens(strip_parens(text))
        if lead and lead[0][4] == 0:          # "2H 2026 A + B": the leading date applies to both
            base = lead[0][:4]
    if len(segs) > 1:                        # a segment without its own date stays with the one before
        g = []
        for seg in segs:
            if g and not tokens(strip_parens(seg)) and not nc:
                g[-1] += '; ' + seg
            else:
                g.append(seg)
        segs = g
    out = []
    for i, seg in enumerate(segs):
        tk = tokens(seg)
        fut = [t for t in tk if t[1] >= TODAY]       # a future date counts even in brackets ("(PDUFA 11/27/26)")
        own = best(fut) if fut else best(tokens(strip_parens(seg)))   # past dates in brackets are context
        if own and (len(segs) > 1 or base is None or own[3] >= base[3]):
            w = own[:4]
        else:
            w = base if base is not None else (own[:4] if own else None)
        st = st0 or status(seg, w, '')
        if nc and w is None:
            continue
        seg2 = re.sub(r'^\s*(?:%s)\s*[:-]?\s*' % '|'.join(['[12]H\\s*20\\d\\d', 'H[12]\\s*20\\d\\d', 'Q[1-4]\\s*20\\d\\d', '[1-4]Q\\s*\\d\\d', MONRE + '\\s+20\\d\\d', '20\\d\\d:']), '', seg, flags=re.I) if nc else seg
        out.append(mk((w[2] if (w and len(segs) > 1) else raw_t), seg2 or seg, w, key and i == 0, st))
    return out


def normalize(r):
    cand = []
    # 1. the row's key catalyst (most current; refreshed every month) carries the key flag
    cand += events_from(r.get('catalyst'), r.get('cat_timing'), True)
    # 2. the curated "next catalyst" line
    cand += events_from(r.get('nc'), None, False, nc=True)
    # 3. the older schedule (keeps its own windows once normalized; the key flag now comes from 1)
    for c in r.get('cat_sched') or []:
        if 'st' in c:
            o = dict(c)
            o.pop('k', None) if not c.get('k') else None
            if o['st'] != 'done':
                o['st'] = 'und' if 'd' not in o else ('up' if dt.date.fromisoformat(o['d']) >= TODAY else 'late')
            cand.append(o)
        else:
            cand += [dict(e, k=0) if False else {k2: v for k2, v in e.items() if k2 != 'k'} for e in events_from(c.get('e'), c.get('t'), False)]
    out = []
    for o in cand:
        dup = next((p for p in out if similar(p, o)), None)
        if dup is None:
            out.append(o)
            continue
        if o.get('p', -1) > dup.get('p', -1):
            for f in ('s', 'd', 'lab', 'p', 't'):
                if f in o:
                    dup[f] = o[f]
        if len(o['e']) > len(dup['e']) and not dup.get('k'):
            dup['e'] = o['e']
        if o.get('k'):
            dup['k'] = 1
    rank = {'up': 0, 'und': 1, 'late': 2, 'done': 3}

    def key(o):
        if o['st'] == 'up':
            s = max(dt.date.fromisoformat(o['s']), TODAY)
            d = dt.date.fromisoformat(o['d'])
            return (0, (s + (d - s) / 2).isoformat(), -o.get('p', 0))
        if o['st'] == 'late':
            return (2, o['d'], 0)
        return (rank[o['st']], '', 0)
    out.sort(key=key)
    return out


def main():
    global TODAY
    args = [a for a in sys.argv[1:]]
    TODAY = dt.date.today()
    if '--today' in args:
        i = args.index('--today')
        TODAY = dt.date.fromisoformat(args[i + 1])
        del args[i:i + 2]
    path = args[0] if args else 'data/data.json'
    D = json.load(open(path))
    n_split = n_late = 0
    for r in D:
        before = len(r.get('cat_sched') or [])
        r['cat_sched'] = normalize(r)
        n_split += len(r['cat_sched']) - before
        up = [c for c in r['cat_sched'] if c['st'] == 'up']
        r['next_cat'] = ({'lab': up[0]['lab'], 'd': up[0]['d'], 's': up[0]['s'], 'e': up[0]['e'], 'k': up[0].get('k', 0), 'n': len(up)} if up else None)
        n_late += sum(1 for c in r['cat_sched'] if c['st'] == 'late')
        kw = parse_timing(r.get('cat_timing'))
        if kw is None and r.get('cat_date'):
            kw = None
        r['cat_lab'] = kw[2] if kw else (r.get('cat_timing') or '')
    json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f"normalized {len(D)} rows: +{n_split} events from splitting/merging, {n_late} past-due events flagged, "
          f"{sum(1 for r in D if r['next_cat'])} rows have an upcoming catalyst")


TODAY = dt.date.today()
if __name__ == '__main__':
    main()
