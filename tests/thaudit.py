import asyncio, json, re, sys
from playwright.async_api import async_playwright
JS = r"""(()=>{const out=[];const strip=h=>{const d=document.createElement('div');d.innerHTML=h||'';return d.textContent;};
for(const r of DATA){ if(r.ta==='Acquired / Inactive')continue; let t3={},ceo=[];
 try{t3=thesis3(r);}catch(e){t3={err:String(e)};}
 try{ceo=(window.ceoNotes?ceoNotes(r):[]).map(n=>({c:n.cat,t:strip(n.t)}));}catch(e){ceo=[{c:'err',t:String(e)}];}
 out.push({t:r.ticker,call:r.call,mc:r.mc,cash:r.cash,hand:!!r.th_view,view:strip(t3.view),miss:strip(t3.miss),cat:strip(t3.cat),ceo});}
return out;})()"""
def B(x):
    m = re.match(r"\$([\d.,]+)\s?([BM])", x); v = float(m.group(1).replace(',', '')); return v * (1e9 if m.group(2) == 'B' else 1e6)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file:///home/claude/biostocks/index.html'); await pg.wait_for_timeout(2500)
        await pg.evaluate("navGo('companies','co')"); await pg.wait_for_timeout(1200)
        R = await pg.evaluate(JS); await b.close()
    json.dump(R, open('/tmp/t/thaudit.json', 'w'), indent=0)
    P = {k: [] for k in ['stale_cap', 'no_miss', 'no_cat', 'no_risk', 'generic_ceo', 'odd_phrase', 'err', 'long_view', 'call_mismatch']}
    for x in R:
        txt = ' '.join([x['view'], x['miss'], x['cat']])
        for m in re.finditer(r"\$[\d.,]+\s?[BM](?=\s*(?:market\s+)?cap\b)", txt):
            if x['mc'] and abs(B(m.group(0)) / x['mc'] - 1) > .2: P['stale_cap'].append(x['t']); break
        if not x['miss']: P['no_miss'].append(x['t'])
        if not x['cat']: P['no_cat'].append(x['t'])
        if not re.search(r"risk|miss|fail|wrong|change our mind|if |unless|downside|dilut|would (cover|cut|exit|turn)|the check|sidelines|next call|act on new data", txt, re.I): P['no_risk'].append(x['t'])
        if any('Investors are asking' in n['t'] for n in x['ceo']): P['generic_ceo'].append(x['t'])
        if re.search(r"in ~\d+ yrs?", txt): P['odd_phrase'].append(x['t'])
        if any(n['c'] == 'err' for n in x['ceo']) or 'err' in x: P['err'].append(x['t'])
        if len(x['view'].split()) > 75: P['long_view'].append(x['t'])
        if x['hand']:
            v0 = re.sub(r'^strong\s+', '', x['view'], flags=re.I); d = 'L' if re.match(r'long', v0, re.I) else 'S' if re.match(r'short', v0, re.I) else 'N'
            c = 'L' if x['call'] in ('LONG', 'STRONG BUY') else 'S' if x['call'] in ('SHORT', 'STRONG SHORT') else 'N'
            if d != c: P['call_mismatch'].append(x['t'] + ':' + x['call'])
    print('companies', len(R), 'hand-written', sum(x['hand'] for x in R), 'page errors', errs[:3])
    for k, v in P.items(): print(f"{k:12s} {len(v):4d}  {' '.join(v[:12])}")
    if len(sys.argv) > 1:
        for t in sys.argv[1:]:
            x = next(y for y in R if y['t'] == t); print('\n==', t, x['call']); print('VIEW:', x['view']); print('MISS:', x['miss']); print('CAT:', x['cat'])
            for n in x['ceo']: print('  CEO', n['c'], ':', n['t'])
asyncio.run(main())
