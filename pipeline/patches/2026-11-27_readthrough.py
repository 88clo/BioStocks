"""Read-through review (Nov 27 2026, after the PM asked that every judgement use historical, competitive and adjacent
data, not only the company's own trials). Changes, each with the outside evidence behind it:
- BBOT efficacy 4 -> 3 (reverses this morning's upgrade). The 63% monotherapy ORR in G12C-inhibitor-naive NSCLC is in line
  with the next-generation class (divarasib ~56%, elisrasib ~59%), not ahead of it; divarasib has already beaten
  sotorasib/adagrasib head to head (Krascendo 1), and first-line G12C + pembrolizumab is being led by Lilly (olomorasib, Ph3
  SUNRAY-01 data 1H27) and Merck (calderasib: ORR 71%, mPFS 28.8 mo). BBOT itself now prioritises the G12C-inhibitor-
  experienced combination (75% ORR at 500 mg, 53% across doses, n=17), where elironrasib monotherapy gives ~42%: promising
  but small. Differentiation stays 4 on that niche.
- BIOA efficacy 4 -> 3. BGE-102's case is hsCRP lowering. Novo's ZEUS (IL-6, n=6,376, AHA Nov 2026) cut hsCRP but not
  cardiovascular events (HR 0.99), so CRP lowering alone is weaker evidence than it looked; CANTOS (IL-1b, upstream like
  NLRP3) is still the supporting case.
- ARVN PoS 0.12 -> 0.07. Biogen/Denali's LRRK2 inhibitor BIIB122 failed Ph2b LUMA in early Parkinson's (n=648) despite
  >90% peripheral LRRK2 inhibition and CSF exposure; ARV-102's evidence is the same kind of target engagement. A degrader
  also removes scaffolding function, which keeps some optionality.
- OCGN PoS 0.40 -> 0.30. No mutation-agnostic RP therapy has proven efficacy; the Ph3 liMeliGhT primary endpoint (LDNA) is
  Ocugen's own test, and the Ph1/2 gains were small and uncontrolled. Topline 1Q27.
- CRBP and GPCR re-checked, unchanged: CRB-701's confirmed HNSCC ORR at 3.6 mg/kg (24%) is about enfortumab vedotin's,
  with less neuropathy but more keratitis (efficacy stays 3); aleniglipron's 16.3% placebo-adjusted loss at 44 weeks beats
  approved orforglipron's ~9-11% at 72 weeks (efficacy stays 4)."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
D = json.load(open(path))
CH = {'BBOT': {'effsig': 3}, 'BIOA': {'effsig': 3}, 'ARVN': {'pos': 0.07}, 'OCGN': {'pos': 0.30}}
RT = {
 'BBOT': 'Read-through: naive monotherapy ORR is in line with next-gen G12C drugs (divarasib ~56%, elisrasib ~59%); 1L G12C+IO is led by Lilly and Merck (calderasib+pembro ORR 71%, mPFS 28.8 mo). The edge is the G12C-experienced combination (elironrasib alone ~42%).',
 'BIOA': 'Read-through: Novo\'s ZEUS (IL-6) lowered hsCRP but not CV events (HR 0.99, Nov 2026), so CRP lowering alone is weaker evidence; CANTOS (IL-1b, upstream like NLRP3) still supports the pathway.',
 'ARVN': 'Read-through: BIIB122 (LRRK2 kinase inhibitor) failed Ph2b LUMA in early PD despite >90% LRRK2 inhibition, so target engagement alone now counts for less; a degrader also removes scaffolding function.',
 'OCGN': 'Read-through: no mutation-agnostic RP therapy has proven efficacy; Ph3 uses Ocugen\'s own LDNA endpoint (topline 1Q27).',
}
for r in D:
    t = r['ticker']
    if t in CH: r.update(CH[t])
    if t in RT and 'Read-through:' not in str(r.get('eff_short') or ''):
        r['eff_short'] = (str(r.get('eff_short') or '').rstrip() + ' ' + RT[t]).strip()
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('read-through applied:', CH)
