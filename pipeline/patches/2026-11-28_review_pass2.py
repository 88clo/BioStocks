"""Second first-principles review (Nov 28 2026): the best-ranked names still resting on values a removed rule set, and the
short book. Each change carries its reason (val_note, shown on the card). inp_review_done marks names judged.
"""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
CH = {
 # stale-data catch: the removed 'strong early data' rule had lifted a discontinued program back to 25%
 'ARTV': dict(pos=0, val_note="Cash shell: AlloNK was discontinued after patient deaths; the removed rule had lifted PoS from 0% to 25% on the old data. Valued on cash only."),
 # longs: kept after review (judged, reason recorded)
 'UPB': dict(val_note="Kept: PoS 38% for a positive Ph2 (56% fewer exacerbations) on a pathway tezepelumab has validated; Ph3 starts Q1 2027, approval ~4 years."),
 'ZNTL': dict(val_note="Kept: PoS 38%. Read-through: the WEE1 class showed efficacy with poor tolerability (adavosertib); azenosertib's biomarker-selected ORR of 37% in Cyclin E1+ PROC with better tolerability supports an accelerated path. Peak $700M: ~4K Cyclin E1+ PROC patients a year in the US/EU at ~$180K."),
 'CTMX': dict(val_note="Kept: PoS 25%, peak $3B. A 32% confirmed ORR in 3L+ colorectal cancer is unprecedented (approved options give low single digits); EpCAM was historically limited by on-target toxicity, which masking addresses. Randomized data and ADC safety are the risks."),
 'IMMX': dict(val_note="Kept: PoS 55%, peak ~$880M. 89% CR in relapsed AL amyloidosis is far above anything approved; a single-arm BLA is plausible in this rare setting."),
 'XBIT': dict(val_note="Kept: PoS 11%, no efficacy data yet."), 'NKTX': dict(val_note="Kept: PoS 10%; striking early responses but very small numbers."),
 'ZURA': dict(val_note="Kept: PoS 12%; HS failed, SSc readout 1H27 with no validated IL-17 role in SSc."), 'TENX': dict(val_note="Kept: PoS 10%; Ph3 missed, a subgroup needs a new trial."),
 'RNA': dict(val_note="Kept: PoS 10%; preclinical PRKAG2 program."), 'OCS': dict(val_note="Kept: PoS 25%; Ph2 biomarker and visual-acuity signals, Ph3 ahead."),
 'SION': dict(val_note="Kept: PoS 8%; CF is well served by Trikafta and Alyftrek, and an earlier add-on failed."), 'LKFT': dict(val_note="Kept: PoS 8%; early autoimmune T-cell engager data."),
 'PALI': dict(pos=0.12, val_note="PoS 12%: Ph1 exposure and PD only; no efficacy yet."), 'QTTB': dict(val_note="Peak $700M, PoS 25% (set in the Nov 27 review)."),
 'ASMB': dict(pos=0.35, val_note="PoS 35%: strong Ph1b shedding reductions; helicase-primase inhibition is validated (pritelivir), but suppressive therapy competes with cheap generics."),
 # longs: changed
 'ENGN': dict(pos=0.45, val_note="PoS 45%: BCG-unresponsive NMIBC is crowded (TAR-200, cretostimogene, Anktiva, Adstiladrin) and ENGN's 24% 12-month CR is below the leaders."),
 'CRDL': dict(pos=0.20, peak_sales=2.5e8, val_note="PoS 20%, peak $250M: an oral CBD formulation in a withdrawal-design trial against an entrenched IL-1 blocker (Arcalyst); limited mechanistic evidence."),
 'NRIX': dict(pos=0.50, val_note="PoS 50%: 83% ORR with durable PFS after BTK inhibitors; degradation also covers kinase-dead resistance mutations. Pivotal single-arm and Ph3 vs pirtobrutinib running; the BTK market supports $3.5B."),
 'VYGR': dict(pos=0.05, val_note="PoS 5%. Read-through: anti-tau antibodies have failed repeatedly (gosuranemab, semorinemab, tilavonemab); no efficacy yet."),
 'WVE': dict(pos=0.45, peak_sales=1.0e9, val_note="PoS 45%, peak $1.0B: exon-53 dystrophin of 7.8% beats approved exon skippers, supporting accelerated approval; ~1,000 amenable US boys at ~$800K. Huntington's and obesity are options outside this value."),
 'COYA': dict(pos=0.10, val_note="PoS 10%: ALS Phase 2 programs have a very poor record; no efficacy data yet."),
 'ACIU': dict(pos=0.08, val_note="PoS 8%: alpha-synuclein approaches have mixed clinical results (prasinezumab) and there is no efficacy yet."),
 'MPLT': dict(pos=0.35, effsig=3, peak_sales=2.0e9, val_note="PoS 35%, efficacy 3, peak $2B: Ph2 met its PANSS primary; KarXT's approval validates muscarinic agonism (emraclidine's failure was an M4-only PAM). The removed rule had capped PoS at 15% on a stale weak-data score."),
 'ATHE': dict(pos=0.30, val_note="PoS 30%: a 48% slowing in MSA is a rare positive signal in a fatal disease with no therapy, but n=77 and a Ph3 is needed."),
 'TECX': dict(pos=0.15, val_note="PoS 15%. Read-through: TENX's levosimendan Ph3 in the same PH-HFpEF population just failed; relaxin is unproven here."),
 'OKYO': dict(pos=0.15, val_note="PoS 15%: neuropathic corneal pain data come from 12 patients."),
 'ETRA': dict(pos=0.45, val_note="PoS 45%: 100% 8-week survival vs ~50% historically in malignancy-associated HLH is unprecedented in a rare, poorly served setting; registrational Ph2/3."),
 'CRSP': dict(pos=0.15, peak_sales=3.0e9, val_note="PoS 15%, peak $3B (were 30% / $9B via a removed rule): ANGPTL3 is validated (evinacumab), but TG -63% / LDL -16% competes with approved and late-stage APOC3 siRNA and antisense drugs; a one-time edit's ASCVD use would need outcomes data."),
 'ABCL': dict(pos=0.30, peak_sales=1.5e9, val_note="PoS 30%, peak $1.5B: positive Ph2, but a monthly injection arrives third behind two approved oral NK3 antagonists (fezolinetant, elinzanetant)."),
 'ELDN': dict(pos=0.30, peak_sales=6.0e8, val_note="PoS 30%, peak $600M: the best eGFR reported in a larger rejection-prevention trial, but a Ph3 against tacrolimus is ahead."),
 # shorts: inputs that made a real business look worthless
 'IPHA': dict(peak_sales=1.5e8, val_note="Peak $150M (was $20M): lacutamab in Sezary syndrome / CTCL (ORR 43%, mDOR ~26 months) is a credible orphan product; a $20M peak understated it."),
 'NBTX': dict(peak_sales=6.0e8, val_note="Peak $600M sales-equivalent (was $150M): J&J holds NBTXR3; Nanobiotix's royalties on a ~$1.5B product are cost-free income, valued like ~$600M of own sales. Ph3 NANORAY-312 is the binary."),
 'CTY': dict(peak_sales=3.0e9, pos=0.10, val_note="Peak $3B, PoS 10%: factor XI is a validated anticoagulation target in a very large market; a quarterly siRNA with >80% knockdown is credible but early."),
 # shorts: kept, with the reason
 'SLBT': dict(val_note="Short kept: preclinical, ~$7M cash against a $277M value. Squeeze risk in a thin float."),
 'CNXU': dict(val_note="Short kept: preclinical device, ~$2M cash, 510(k) path untested for this use."),
 'ARMP': dict(val_note="Short kept: ~$220M of debt ahead of equity even if the Ph3 phage trial works."),
 'MENS': dict(val_note="Short kept: botanical BPH drug after a Ph3 failure; strategy unclear."),
 'ATYR': dict(val_note="Short kept: Ph3 EFZO-FIT missed its primary endpoint; ~$480M value with ~$38M net cash."),
}
D = json.load(open(path)); n = 0
for r in D:
    c = CH.get(r['ticker'])
    if not c: continue
    for k, v in c.items():
        if r.get(k) != v: r[k] = v; n += 1
    r['inp_review_done'] = 1; r.pop('inp_review', None)
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('review pass 2:', n, 'fields on', len(CH), 'names')
