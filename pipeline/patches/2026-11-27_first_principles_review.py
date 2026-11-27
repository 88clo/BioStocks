"""First-principles input review of the top of the new ranking (Nov 27 2026, PM: 'check that our long ideas are truly
attractive'; keep first principles, never just adopt someone else's peak). Peak = patients actually treated per year x
net price; for one-time therapies that is the yearly flow through the eligible pool, not the whole pool every year. PoS is
the chance of approval (pipeline) or of the launch reaching our peak (approved). Every value below replaces one that
failed that check; the reason is written next to it and into the card (val_note).
"""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
CH = {
 # one-time gene / cell therapies: yearly flow through a limited pool
 'NGNE': dict(peak_sales=1.5e9, pos=0.35, val_note="Peak $1.5B: one-time AAV for Rett (~6-9K US patients, similar ex-US); ~500-600 treated a year at ~$2.5M at peak, not 4,000 a year. PoS 35%: registrational on very small numbers (n=10 Ph1/2)."),
 'NTLA': dict(peak_sales=1.5e9, val_note="Peak $1.5B: one-time CRISPR cure for HAE (~6-7K US patients, a $3-4B chronic prophylaxis market). ~500-600 patients a year at ~$2.5-3M; 4,000 a year would exhaust the US pool in under two years."),
 'RGNX': dict(peak_sales=1.5e9, pos=0.65, val_note="Peak $1.5B: one-time micro-dystrophin gene therapy; ~5-6K ambulatory US DMD boys eligible, ~600 a year at ~$2.5M. PoS 65%: accelerated approval on micro-dystrophin has precedent (Elevidys), but the class's safety record makes FDA stricter."),
 'ABEO': dict(peak_sales=2.5e8, val_note="Peak $250M: ZEVASKYN for RDEB wounds (~1,500 US patients), $3.1M per treatment, ~70-80 treatments a year at peak; run-rate today $54M. The old $1.35B assumed 1,500 treatments a year."),
 'AUTL': dict(peak_sales=1.0e9, pos=0.20, inp_review_done=1, val_note="SLE: peak $1.0B, PoS 20% (was 45%, set by a removed rule). Autologous CD19 CAR-T in refractory SLE / lupus nephritis: ~1,500-2,000 treated a year at ~$450K; crowded by other CD19 CAR-Ts and off-the-shelf CD19xCD3 engagers. AUCATZYL in ALL is the existing business."),
 'SPRB': dict(peak_sales=2.0e8, val_note="Peak $200M: MPS IIIB is ultra-rare (a few hundred US patients); chronic ERT at ~$750K for ~250-300 patients worldwide at peak."),
 'RNAC': dict(peak_sales=1.0e9, val_note="Peak $1.0B: gMG ~80K US; the refractory / CAR-T-willing slice is ~15K; ~2,000 courses a year at ~$450K (retreatment needed) against entrenched FcRn and complement drugs and other CD19 CAR-Ts."),
 # crowded or generic markets entered by small companies
 'CING': dict(peak_sales=2.5e8, val_note="Peak $250M: another once-daily dexmethylphenidate in a generic-crowded stimulant market; recent branded ADHD launches (Azstarys, Qelbree) took years to reach $200-400M with big sales forces."),
 'UNCY': dict(peak_sales=1.5e8, val_note="Peak $150M: hyperphosphatemia binders are generic (sevelamer, lanthanum); a lower pill burden earns a niche at a branded price, not $500M."),
 'MLYS': dict(peak_sales=1.2e9, val_note="Peak $1.2B: resistant hypertension is huge, but lorundrostat is second to AstraZeneca's baxdrostat with a big-pharma launch; ~150K patients at ~$8K."),
 'ALMS': dict(peak_sales=8.0e8, pos=0.50, val_note="Peak $800M, PoS 50%: oral TYK2 psoriasis behind deucravacitinib, Takeda's zasocitinib and J&J's oral IL-23R peptide icotrokinra; a late oral entrant without clear superiority."),
 'LYEL': dict(peak_sales=7.0e8, pos=0.60, val_note="Peak $700M, PoS 60%: 3L+ LBCL is served by Yescarta, Breyanzi and CD20xCD3 bispecifics; a single-arm pivotal for a next-gen CAR-T needs clearly better durability."),
 'APMD': dict(peak_sales=1.2e9, val_note="Peak $1.2B: OSA is huge (~30M US, far fewer diagnosed), but AD109's effect is moderate (AHI -47-56%) and tirzepatide is approved for OSA with obesity; ~350K patients at ~$3.5K net."),
 'HELP': dict(peak_sales=1.0e9, pos=0.55, val_note="Peak $1.0B, PoS 55%: psychedelic MDD needs supervised sessions (capacity-limited); ~100K courses a year at ~$10K drug revenue. One positive Ph3; the second and the REMS are ahead."),
 'ENTX': dict(peak_sales=1.5e9, pos=0.40, val_note="Peak $1.5B, PoS 40%: an oral PTH would expand the anabolic osteoporosis market (injectables ~$1-2B), ~150K patients at ~$9K; a Ph3 on BMD is still ahead."),
 'VTVT': dict(peak_sales=5.0e8, pos=0.40, val_note="Peak $500M, PoS 40%: oral T1D adjuncts have struggled (sotagliflozin was not approved for T1D); ~100K patients at ~$5K if hypoglycaemia benefit holds in Ph3."),
 'NERV': dict(peak_sales=1.0e9, pos=0.20, val_note="Peak $1.0B, PoS 20%: negative symptoms of schizophrenia have no approved drug (real need), but roluperidone already received a refusal; ~80K patients at ~$12K."),
 # device / procedure and local products
 'GUTS': dict(peak_sales=3.0e8, val_note="Peak $300M: an endoscopic procedure (~30K a year at ~$10K) keeping 80% vs 67% (sham) of GLP-1 weight loss; device reimbursement and GI capacity limit uptake. Cash runway only into Q2 2027."),
 'PYPD': dict(peak_sales=2.5e8, val_note="Peak $250M: a local antibiotic implant for colorectal surgery is paid inside hospital DRG budgets; ~150K procedures at ~$1.7K."),
 # China pricing
 'GYRE': dict(peak_sales=5.0e8, val_note="Peak $500M: hydronidone is a China launch (CHB liver fibrosis) at China / NRDL prices (~$3K a year), not $40K; ETUARY (China IPF) is the existing business."),
 # rule-set PoS in early or niche oncology / immunology
 'SPRO': dict(peak_sales=5.0e8, pos=0.12, inp_review_done=1, val_note="SP001 IgG4-RD: peak $500M, PoS 12% (was 38%, set by a removed rule, for a Ph2-ready asset). Inebilizumab is approved and obexelimab has positive Ph3 data, so an anti-CD40L arrives third."),
 'ACRV': dict(peak_sales=3.0e8, pos=0.30, inp_review_done=1, val_note="Peak $300M, PoS 30% (was 42%, set by a removed rule): biomarker-selected 2L+ endometrial niche (~2,500 US patients a year); accelerated approval possible on the Q4 2026 interim."),
 'VRCA': dict(peak_sales=3.0e8, pos=0.20, inp_review_done=1, val_note="VP-315: peak $300M, PoS 20% (was 45%, set by a removed rule). Most BCC is cured by surgery (Mohs); the market is the advanced / hard-to-operate slice. Cash ~$3M: financing first."),
 'BBOT': dict(peak_sales=1.0e9, val_note="Peak $1.0B: the realistic market is 2L+ G12C-inhibitor-experienced NSCLC (~5K US patients a year, ~2x worldwide) at ~$150K per treated patient, plus first-line optionality that Lilly and Merck lead."),
 # approved launches: odds of reaching our peak
 'LENZ': dict(pos_comm=0.40, val_note="Launch odds 40%: presbyopia drops are cash-pay and elective; Vuity flopped commercially. Peak $300M stays."),
 # mature / declining / indebted commercial businesses: a lower sales multiple
 'EBS': dict(ps_mult=1.0, val_note="Sales multiple 1x: mature, low-margin government / Narcan business facing generic naloxone, with heavy debt."),
 'AMRN': dict(ps_mult=1.0, val_note="Sales multiple 1x: Vascepa is genericized in the US and sales are declining."),
 'HRTX': dict(ps_mult=1.5, val_note="Sales multiple 1.5x: slow-growing, unprofitable hospital products with convertible debt."),
 'SRPT': dict(ps_mult=1.5, val_note="Sales multiple 1.5x: Elevidys sales are shrinking after safety restrictions; heavy debt."),
 # second pass (the next names up the ranking once the first batch was fixed)
 'BEAM': dict(peak_sales=2.5e9, val_note="Peak $2.5B: one-time base editing for severe AATD (PiZZ; ~100K US, most undiagnosed); ~1,000-1,500 treated a year worldwide at ~$1.5-2M, not $12B."),
 'TSHA': dict(peak_sales=1.5e9, pos=0.45, val_note="Peak $1.5B, PoS 45%: same Rett arithmetic as NGNE (one-time, ~500-600 patients a year at ~$2.5M); two AAV programs will split it."),
 'TNYA': dict(peak_sales=1.0e9, pos=0.12, val_note="Peak $1.0B, PoS 12%: MYBPC3 HCM (~50K diagnosed US) via high-dose cardiac AAV; n=6 so far and adult cardiac AAV carries real safety risk; ~600 a year at ~$1.7M."),
 'NKTR': dict(peak_sales=1.5e9, pos=0.35, val_note="Peak $1.5B, PoS 35%: AD and alopecia areata are crowded (dupilumab, lebrikizumab, OX40s, JAKs); rezpeg's Ph2b effects were moderate."),
 'FDMT': dict(peak_sales=2.0e9, val_note="Peak $2.0B: wet AMD is ~1.5M US patients on anti-VEGF; a one-time intravitreal gene therapy could treat ~15K a year at ~$130K, competing with long-acting TKIs and other gene therapies."),
 'OCUL': dict(peak_sales=2.5e9, pos=0.75, val_note="Peak $2.5B, PoS 75%: superiority win in SOL-1 is real; wet AMD is a $10B+ market but crowded with long-acting entrants (Eylea HD, Vabysmo, EYP-1901)."),
 'CADL': dict(peak_sales=1.0e9, val_note="Peak $1.0B: ~100K localized intermediate/high-risk prostate cancers a year in the US; an adjunct viral immunotherapy with radiation reaching ~7-8K patients a year at ~$130K."),
 'ALT': dict(peak_sales=8.0e8, val_note="Peak $800M: MASH now has semaglutide and resmetirom approved and several FGF21s and dual agonists coming; pemvidutide missed its 24-week fibrosis endpoint."),
 'AVTX': dict(peak_sales=8.0e8, val_note="Peak $800M: HS biologics are crowded (secukinumab, bimekizumab, sonelokimab coming); an IL-1b antibody with a positive Ph2 earns a share, not $2B."),
 'IMUX': dict(peak_sales=1.0e9, val_note="Peak $1.0B: relapsing MS is crowded with generic orals and high-efficacy antibodies; vidofludimus's edge (tolerability, possible neuroprotection) needs the Ph3 to show it."),
 'QTTB': dict(peak_sales=7.0e8, pos=0.25, val_note="Peak $700M, PoS 25%: alopecia areata has three approved JAKs; an IL-7R antibody in Ph2."),
 'LBRX': dict(peak_sales=1.2e9, pos=0.60, val_note="Peak $1.2B, PoS 60%: a US amisulpride in a crowded, mostly generic antipsychotic market; new mechanisms (KarXT) show ~$1B is achievable, not $3.8B."),
 'XBIT': dict(peak_sales=6.0e8, val_note="Peak $600M: axSpA is crowded (TNFs, IL-17s, JAKs); a Ph2 asset with a niche mechanism."),
 'CMPX': dict(peak_sales=3.0e8, pos=0.20, effsig=3, inp_review_done=1, val_note="Peak $300M, PoS 20% (was 38%, set by a removed rule), efficacy 3: 2L biliary tract cancer (~10K US a year); ORR 18% vs 5% and PFS HR 0.44, but overall survival not significant."),
 'HUMA': dict(pos_comm=0.35, val_note="Launch odds 35%: vascular-trauma sales run at ~$4M a year; reaching our $900M peak needs the dialysis-access label, itself uncertain."),
 # third pass
 'PROK': dict(peak_sales=1.2e9, val_note="Peak $1.2B: autologous kidney cell therapy for advanced diabetic CKD; the pool is huge but it needs biopsies and repeat injections at specialist centres; ~25K patients a year at ~$45K."),
 'CABA': dict(peak_sales=1.0e9, val_note="Peak $1.0B: myositis CAR-T (~70K US myositis, refractory slice ~10K); ~2,000 a year at ~$450K, competing with other CD19 CAR-Ts and T-cell engagers."),
 'AGMB': dict(peak_sales=2.0e9, val_note="Peak $2.0B: fibrostenosing Crohn's has no drug (surgery is the answer) and affects ~30% of ~800K US Crohn's patients; ~15K treated at ~$130K if an anti-fibrotic works. PoS 20% stays (Ph2, new mechanism)."),
 'OLMA': dict(peak_sales=1.0e9, val_note="Peak $1.0B: oral SERDs are a crowded class (elacestrant approved; camizestrant, imlunestrant, vepdegestrant coming); palazestrant needs a combination edge."),
 'OCGN': dict(peak_sales=1.0e9, val_note="Peak $1.0B: one-time, mutation-agnostic RP gene therapy (~100K US RP); ~3,000 a year at ~$300K if the Ph3 shows benefit on its own LDNA endpoint."),
 'MDWD': dict(peak_sales=5.0e8, val_note="Peak $500M: enzymatic debridement for venous leg ulcers competes with cheap mechanical debridement; ~40K courses a year at ~$12K."),
}
D = json.load(open(path)); n = 0
for r in D:
    c = CH.get(r['ticker'])
    if not c: continue
    for k, v in c.items():
        if r.get(k) != v: r[k] = v; n += 1
    if c.get('inp_review_done'): r.pop('inp_review', None)
    if 'peak_sales' in c and r.get('pos') is not None: r['probadj_sales'] = c['peak_sales'] * r['pos']
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('first-principles review:', n, 'fields on', len(CH), 'names')
