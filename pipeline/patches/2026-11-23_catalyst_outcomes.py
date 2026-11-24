"""Resolve past-due catalysts checked on 2026-11-23 (sources in pipeline/logs/2026-11-23_catalyst_check.md).
Marks the event done and appends the outcome. Re-running is harmless."""
import json, sys

OUT = {
    'CYTK': ('MAPLE-HCM sNDA', 'Approved Nov 16: label now includes head-to-head MAPLE-HCM vs metoprolol; indication unchanged'),
    'SMMT': ('ivonescimab BLA', 'CRL Nov 16 for ivonescimab + chemo in EGFRm NSCLC post-TKI (HARMONi met PFS, missed OS)'),
    'CLDX': ('EMBARQ', 'Met primary and all key secondaries in both Ph3s (Sep 22); BLA planned 2027'),
    'KOD':  ('DAYBREAK', 'Met primary (non-inferior to aflibercept, Sep 28); 54% of tarcocimab pts on 24-wk dosing at Y1'),
}

path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
n = 0
for r in D:
    o = OUT.get(r['ticker'])
    if not o:
        continue
    for c in r.get('cat_sched') or []:
        if o[0].lower() in c['e'].lower() and c.get('st') != 'done':
            c['st'] = 'done'
            if 'outcome:' not in c['e']:
                c['e'] = c['e'].rstrip('. ') + ' — outcome: ' + o[1]
            n += 1
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('resolved', n, 'events')
