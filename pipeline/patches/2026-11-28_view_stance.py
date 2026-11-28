"""Hand-written views whose opening stance ("Long:", "Short:", "Avoid:") disagrees with the call the scenario model now
makes (Nov 28 2026). The call badge carries the stance; the stale stance word is removed so the card never says both, and
each name is flagged for the monthly input review, which decides whether the inputs or the old view were wrong.
"""
import json, re, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
STANCE = re.compile(r"^(strong\s+)?(long|short|hold|watch|avoid)\b[^:]{0,40}:\s*", re.I)
def side(s):
    s = re.sub(r'^strong\s+', '', s, flags=re.I)
    return 'L' if re.match(r'long', s, re.I) else 'S' if re.match(r'short', s, re.I) else 'N'
def cside(c): return 'L' if c in ('LONG', 'STRONG BUY') else 'S' if c in ('SHORT', 'STRONG SHORT') else 'N'
n = 0
for r in D:
    v = r.get('call_reason') or ''
    m = STANCE.match(v)
    if not m or side(v) == cside(r.get('call')): continue
    old = m.group(0).strip().rstrip(':')
    rest = v[m.end():]; r['call_reason'] = rest[:1].upper() + rest[1:]
    r['inp_review'] = (f"The hand-written view opened '{old}' but the scenario model now says {r.get('call')}; "
                       "check which is wrong (PoS, peak, launch odds, cash, burn) and rewrite the view.")
    n += 1; print(r['ticker'], r.get('call'), '<-', old)
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
# the hand-written source the build reads views from
tp = path.replace('data.json', 'theses.json'); T = json.load(open(tp)); calls = {r['ticker']: r.get('call') for r in D}; m2 = 0
for t, th in T['theses'].items():
    v = th.get('th_view') or ''; m = STANCE.match(v)
    if m and t in calls and side(v) != cside(calls[t]):
        rest = v[m.end():]; th['th_view'] = rest[:1].upper() + rest[1:]; m2 += 1
json.dump(T, open(tp, 'w'), ensure_ascii=False, indent=1)
print('view stance fixed on', n, 'names;', m2, 'in theses.json')
