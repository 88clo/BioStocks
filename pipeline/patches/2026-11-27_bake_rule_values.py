"""Bake the old rule adjustments into explicit inputs (Nov 27 2026).
The valuation used to change PoS, peak and timing mechanically from the efficacy/differentiation scores (PoS floors for
strong early data, caps for weak data, x0.4/x0.7 peak haircuts, approval two years sooner). The PM asked for no stiff rules,
so those rules were removed from valParts. To avoid a silent jump in 116 valuations, the values the rules produced today
are written here as the inputs themselves, each flagged with inp_review so the judgement can be redone name by name
(the monthly run works through them, best-ranked first). Idempotent: only writes when the value differs."""
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
B = {
"CRSP": {
"pos": 0.3,
"y": 6
},
"COAG": {
"pos": 0.1
},
"KROS": {
"pos": 0.15,
"pk": 420000000
},
"AUTL": {
"pos": 0.45,
"y": 4
},
"NRIX": {
"pos": 0.38,
"y": 3
},
"SLBT": {
"pk": 210000000
},
"IMMX": {
"y": 4
},
"ELVN": {
"y": 6
},
"CTMX": {
"pos": 0.25,
"y": 6
},
"XLO": {
"pos": 0.1
},
"CMPX": {
"pos": 0.38,
"y": 3
},
"RXRX": {
"pos": 0.38,
"y": 4
},
"AKTS": {
"pos": 0.08,
"pk": 510299999.99999994
},
"ENGN": {
"pk": 208250000
},
"XNCR": {
"pos": 0.08,
"pk": 1049999999.9999999
},
"OKUR": {
"pos": 0.06
},
"ACRV": {
"y": 4
},
"MGNX": {
"pos": 0.08,
"pk": 132999999.99999999
},
"ZNTL": {
"pos": 0.38
},
"CGEN": {
"pos": 0.08
},
"GNLX": {
"pos": 0.25,
"pk": 168000000
},
"PYXS": {
"pos": 0.1
},
"AVBP": {
"pk": 251999999.99999997
},
"CBIO": {
"pk": 714000000
},
"STRO": {
"pos": 0.08
},
"WHWK": {
"pk": 273000000
},
"MOLN": {
"pos": 0.1
},
"HURA": {
"pk": 140000000
},
"DRTS": {
"pos": 0.25
},
"NTHI": {
"pos": 0.15,
"pk": 28000000
},
"KZIA": {
"pk": 168000000
},
"PBLS": {
"pos": 0.1
},
"RCKT": {
"pos": 0.15
},
"RNA": {
"pos": 0.1,
"pk": 147000000
},
"LGVN": {
"pk": 105000000
},
"DMAC": {
"pk": 630000000
},
"TECX": {
"pk": 1487500000
},
"TENX": {
"pk": 192000000
},
"IKT": {
"pos": 0.25,
"pk": 378000000
},
"GOSS": {
"pk": 441000000
},
"MANE": {
"pk": 2450000000
},
"ABSI": {
"pos": 0.1,
"pk": 1750000000
},
"CNXU": {
"pos": 0.06
},
"VRCA": {
"y": 4
},
"LCTX": {
"pos": 0.1
},
"OCS": {
"pos": 0.25
},
"SRZN": {
"pk": 1049999999.9999999
},
"SEPN": {
"pos": 0.08,
"pk": 1049999999.9999999
},
"EVMN": {
"pos": 0.15,
"pk": 560000000
},
"TRAX": {
"pk": 1680000000
},
"STTK": {
"pos": 0.1,
"pk": 1197000000
},
"EPRX": {
"pos": 0.15
},
"ODTX": {
"pos": 0.15
},
"PALI": {
"pos": 0.15
},
"EQ": {
"pk": 700000000
},
"SANA": {
"pos": 0.06
},
"IPSC": {
"pk": 800000000
},
"SABS": {
"pos": 0.15
},
"MAZE": {
"pos": 0.38,
"y": 4
},
"JBIO": {
"pos": 0.15,
"pk": 1049999999.9999999
},
"NKTX": {
"pos": 0.1,
"pk": 524999999.99999994
},
"ELOX": {
"pos": 0.15
},
"GENB": {
"pos": 0.25
},
"UPB": {
"pos": 0.38,
"y": 4
},
"ATYR": {
"pk": 210000000
},
"LKFT": {
"pos": 0.08
},
"CRDL": {
"pk": 560000000
},
"ROIV": {
"y": 3
},
"ELDN": {
"pos": 0.38,
"y": 4
},
"QTTB": {
"pos": 0.38,
"y": 4
},
"ZURA": {
"pk": 420000000
},
"ORKA": {
"y": 4
},
"XBIT": {
"pk": 2099999999.9999998
},
"ARTV": {
"pos": 0.25,
"y": 5
},
"ARMP": {
"pos": 0.15
},
"SPRO": {
"pos": 0.38,
"y": 4
},
"ABUS": {
"pk": 1889999999.9999998
},
"IVVD": {
"pos": 0.25
},
"ASMB": {
"pos": 0.38,
"y": 4
},
"VXRT": {
"pos": 0.08,
"pk": 264599999.99999997
},
"SION": {
"pk": 224000000
},
"CTNM": {
"pos": 0.15,
"pk": 1750000000
},
"EDIT": {
"pk": 800000000
},
"PLYX": {
"pos": 0.15
},
"RZLT": {
"pos": 0.25
},
"MBX": {
"pk": 2352000000
},
"ARCT": {
"pos": 0.15
},
"VKTX": {
"pk": 2800000000
},
"WVE": {
"pos": 0.22
},
"VANI": {
"pos": 0.08
},
"EWTX": {
"y": 4
},
"MENS": {
"pos": 0.25,
"pk": 60000000
},
"OVID": {
"pos": 0.15
},
"CAMP": {
"pos": 0.1,
"pk": 612500000
},
"ABCL": {
"pos": 0.38
},
"DSGN": {
"pk": 612500000
},
"VYGR": {
"pos": 0.08
},
"COYA": {
"pos": 0.22,
"pk": 787500000
},
"MNOV": {
"pk": 72000000
},
"CGTX": {
"pos": 0.15,
"pk": 94500000
},
"ALEC": {
"pos": 0.06,
"pk": 1200000000
},
"ATHE": {
"y": 4
},
"ACIU": {
"pos": 0.15
},
"ACAD": {
"pos": 0.25
},
"OKYO": {
"pos": 0.25
},
"NTRB": {
"pos": 0.06
},
"SPTX": {
"pos": 0.15,
"pk": 3150000000
},
"MPLT": {
"pos": 0.15,
"pk": 2625000000
},
"BRVE": {
"pos": 0.25,
"pk": 700000000
},
"LTGO": {
"pk": 840000000
},
"OBX": {
"pos": 0.38,
"y": 4
},
"ATTO": {
"pos": 0.08
},
"VRXA": {
"pk": 180000000
},
"ETRA": {
"pos": 0.38,
"y": 3
},
"CTY": {
"pk": 1049999999.9999999
},
"RTSN": {
"pk": 420000000
}
}
N = {
"CRSP": "PoS raised 12%\u219230% (strong early data); approval 8\u21926 yrs (strong data); \u2212 $120M expected spend to approval",
"COAG": "PoS capped 28%\u219210% (weak data); \u2212 $79M expected spend to approval",
"KROS": "PoS capped 20%\u219215% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $72M expected spend to approval",
"AUTL": "PoS raised 10%\u219245% (strong early data); approval 6\u21924 yrs (strong data); \u2212 $96M expected spend to approval",
"NRIX": "PoS raised 35%\u219238% (strong early data); approval 4\u21923 yrs (strong data); \u2212 $72M expected spend to approval",
"SLBT": "peak \u00d70.7 (undifferentiated); \u2212 $168M expected spend to approval",
"IMMX": "approval 6\u21924 yrs (strong data); \u2212 $58M expected spend to approval",
"ELVN": "approval 8\u21926 yrs (strong data); \u2212 $72M expected spend to approval",
"CTMX": "PoS raised 16%\u219225% (strong early data); approval 8\u21926 yrs (strong data); \u2212 $120M expected spend to approval",
"XLO": "PoS capped 12%\u219210% (weak data); \u2212 $132M expected spend to approval",
"CMPX": "PoS raised 12%\u219238% (strong early data); approval 4\u21923 yrs (strong data); \u2212 $43M expected spend to approval",
"RXRX": "PoS raised 24%\u219238% (strong early data); approval 6\u21924 yrs (strong data); \u2212 $96M expected spend to approval",
"AKTS": "PoS capped 42%\u21928% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $150M expected spend to approval",
"ENGN": "peak \u00d70.7 (undifferentiated); \u2212 $120M expected spend to approval",
"XNCR": "PoS capped 15%\u21928% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $150M expected spend to approval",
"OKUR": "PoS capped 11%\u21926% (weak data); \u2212 $101M expected spend to approval",
"ACRV": "approval 6\u21924 yrs (strong data); \u2212 $96M expected spend to approval",
"MGNX": "PoS capped 9%\u21928% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $90M expected spend to approval",
"ZNTL": "PoS raised 30%\u219238% (strong early data); \u2212 $58M expected spend to approval",
"CGEN": "PoS capped 11%\u21928% (weak data); \u2212 $90M expected spend to approval",
"GNLX": "PoS capped 30%\u219225% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $43M expected spend to approval",
"PYXS": "PoS capped 30%\u219210% (weak data); \u2212 $132M expected spend to approval",
"AVBP": "peak \u00d70.7 (undifferentiated); \u2212 $43M expected spend to approval",
"CBIO": "peak \u00d70.7 (undifferentiated); \u2212 $132M expected spend to approval",
"STRO": "PoS capped 9%\u21928% (weak data); \u2212 $150M expected spend to approval",
"WHWK": "peak \u00d70.7 (undifferentiated); \u2212 $150M expected spend to approval",
"MOLN": "PoS capped 11%\u219210% (weak data); \u2212 $79M expected spend to approval",
"HURA": "peak \u00d70.7 (undifferentiated); \u2212 $43M expected spend to approval",
"DRTS": "PoS capped 45%\u219225% (weak data); \u2212 $43M expected spend to approval",
"NTHI": "PoS capped 15%\u219215% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $72M expected spend to approval",
"KZIA": "peak \u00d70.7 (undifferentiated); \u2212 $58M expected spend to approval",
"PBLS": "PoS capped 30%\u219210% (weak data); \u2212 $79M expected spend to approval",
"RCKT": "PoS capped 27%\u219215% (weak data); \u2212 $72M expected spend to approval",
"RNA": "PoS capped 11%\u219210% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $79M expected spend to approval",
"LGVN": "peak \u00d70.7 (undifferentiated); \u2212 $72M expected spend to approval",
"DMAC": "peak \u00d70.7 (undifferentiated); \u2212 $96M expected spend to approval",
"TECX": "peak \u00d70.7 (undifferentiated); \u2212 $120M expected spend to approval",
"TENX": "peak \u00d70.4 (undifferentiated); \u2212 $72M expected spend to approval",
"IKT": "PoS capped 29%\u219225% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $72M expected spend to approval",
"GOSS": "peak \u00d70.7 (undifferentiated); \u2212 $30M expected spend to approval",
"MANE": "peak \u00d70.7 (undifferentiated); \u2212 $108M expected spend to approval",
"ABSI": "PoS capped 13%\u219210% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $198M expected spend to approval",
"CNXU": "PoS capped 10%\u21926% (weak data); \u2212 $168M expected spend to approval",
"VRCA": "approval 6\u21924 yrs (strong data); \u2212 $144M expected spend to approval",
"LCTX": "PoS capped 18%\u219210% (weak data); \u2212 $132M expected spend to approval",
"OCS": "PoS capped 35%\u219225% (weak data); \u2212 $43M expected spend to approval",
"SRZN": "peak \u00d70.7 (undifferentiated); \u2212 $198M expected spend to approval",
"SEPN": "PoS capped 18%\u21928% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $150M expected spend to approval",
"EVMN": "PoS capped 18%\u219215% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $180M expected spend to approval",
"TRAX": "peak \u00d70.7 (undifferentiated); \u2212 $132M expected spend to approval",
"STTK": "PoS capped 14%\u219210% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $132M expected spend to approval",
"EPRX": "PoS capped 27%\u219215% (weak data); \u2212 $120M expected spend to approval",
"ODTX": "PoS capped 20%\u219215% (weak data); \u2212 $120M expected spend to approval",
"PALI": "PoS capped 25%\u219215% (weak data); \u2212 $120M expected spend to approval",
"EQ": "peak \u00d70.7 (undifferentiated); \u2212 $225M expected spend to approval",
"SANA": "PoS capped 13%\u21926% (weak data); \u2212 $168M expected spend to approval",
"IPSC": "peak \u00d70.4 (undifferentiated); \u2212 $168M expected spend to approval",
"SABS": "PoS capped 27%\u219215% (weak data); \u2212 $120M expected spend to approval",
"MAZE": "PoS raised 29%\u219238% (strong early data); approval 6\u21924 yrs (strong data); \u2212 $96M expected spend to approval",
"JBIO": "PoS capped 18%\u219215% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $120M expected spend to approval",
"NKTX": "PoS capped 12%\u219210% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $132M expected spend to approval",
"ELOX": "PoS capped 18%\u219215% (weak data); \u2212 $72M expected spend to approval",
"GENB": "PoS capped 35%\u219225% (weak data); \u2212 $72M expected spend to approval",
"UPB": "PoS raised 35%\u219238% (strong early data); approval 6\u21924 yrs (strong data); \u2212 $96M expected spend to approval",
"ATYR": "peak \u00d70.7 (undifferentiated); \u2212 $72M expected spend to approval",
"LKFT": "PoS capped 12%\u21928% (weak data); \u2212 $150M expected spend to approval",
"CRDL": "peak \u00d70.7 (undifferentiated); \u2212 $43M expected spend to approval",
"ROIV": "approval 4\u21923 yrs (strong data); \u2212 $72M expected spend to approval",
"ELDN": "PoS raised 29%\u219238% (strong early data); approval 6\u21924 yrs (strong data); \u2212 $58M expected spend to approval",
"QTTB": "PoS raised 15%\u219238% (strong early data); approval 6\u21924 yrs (strong data); \u2212 $96M expected spend to approval",
"ZURA": "peak \u00d70.7 (undifferentiated); \u2212 $120M expected spend to approval",
"ORKA": "approval 6\u21924 yrs (strong data); \u2212 $144M expected spend to approval",
"XBIT": "peak \u00d70.7 (undifferentiated); \u2212 $120M expected spend to approval",
"ARTV": "PoS raised 0%\u219225% (strong early data); approval 7\u21925 yrs (strong data); \u2212 $108M expected spend to approval",
"ARMP": "PoS capped 25%\u219215% (weak data); \u2212 $120M expected spend to approval",
"SPRO": "PoS raised 13%\u219238% (strong early data); approval 6\u21924 yrs (strong data); \u2212 $96M expected spend to approval",
"ABUS": "peak \u00d70.7 (undifferentiated); \u2212 $120M expected spend to approval",
"IVVD": "PoS capped 32%\u219225% (weak data); \u2212 $72M expected spend to approval",
"ASMB": "PoS raised 31%\u219238% (strong early data); approval 6\u21924 yrs (strong data); \u2212 $144M expected spend to approval",
"VXRT": "PoS capped 12%\u21928% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $225M expected spend to approval",
"SION": "peak \u00d70.7 (undifferentiated); \u2212 $150M expected spend to approval",
"CTNM": "PoS capped 18%\u219215% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $120M expected spend to approval",
"EDIT": "peak \u00d70.4 (undifferentiated); \u2212 $132M expected spend to approval",
"PLYX": "PoS capped 18%\u219215% (weak data); \u2212 $72M expected spend to approval",
"RZLT": "PoS capped 50%\u219225% (weak data); \u2212 $43M expected spend to approval",
"MBX": "peak \u00d70.7 (undifferentiated); \u2212 $72M expected spend to approval",
"ARCT": "PoS capped 22%\u219215% (weak data); \u2212 $72M expected spend to approval",
"VKTX": "peak \u00d70.7 (undifferentiated); \u2212 $108M expected spend to approval",
"WVE": "PoS capped 38%\u219222% (weak data); \u2212 $144M expected spend to approval",
"VANI": "PoS capped 11%\u21928% (weak data); \u2212 $225M expected spend to approval",
"EWTX": "approval 6\u21924 yrs (strong data); \u2212 $58M expected spend to approval",
"MENS": "PoS capped 26%\u219225% (weak data); peak \u00d70.4 (undifferentiated); \u2212 $108M expected spend to approval",
"OVID": "PoS capped 28%\u219215% (weak data); \u2212 $120M expected spend to approval",
"CAMP": "PoS capped 12%\u219210% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $79M expected spend to approval",
"ABCL": "PoS raised 27%\u219238% (strong early data); \u2212 $180M expected spend to approval",
"DSGN": "peak \u00d70.7 (undifferentiated); \u2212 $79M expected spend to approval",
"VYGR": "PoS capped 13%\u21928% (weak data); \u2212 $225M expected spend to approval",
"COYA": "PoS capped 23%\u219222% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $58M expected spend to approval",
"MNOV": "peak \u00d70.4 (undifferentiated); \u2212 $72M expected spend to approval",
"CGTX": "PoS capped 22%\u219215% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $120M expected spend to approval",
"ALEC": "PoS capped 15%\u21926% (weak data); peak \u00d70.4 (undifferentiated); \u2212 $101M expected spend to approval",
"ATHE": "approval 6\u21924 yrs (strong data); \u2212 $96M expected spend to approval",
"ACIU": "PoS capped 23%\u219215% (weak data); \u2212 $120M expected spend to approval",
"ACAD": "PoS capped 85%\u219225% (weak data); \u2212 $108M expected spend to approval",
"OKYO": "PoS capped 34%\u219225% (weak data); \u2212 $72M expected spend to approval",
"NTRB": "PoS capped 15%\u21926% (weak data); \u2212 $168M expected spend to approval",
"SPTX": "PoS capped 23%\u219215% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $180M expected spend to approval",
"MPLT": "PoS capped 22%\u219215% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $180M expected spend to approval",
"BRVE": "PoS capped 28%\u219225% (weak data); peak \u00d70.7 (undifferentiated); \u2212 $72M expected spend to approval",
"LTGO": "peak \u00d70.7 (undifferentiated); \u2212 $108M expected spend to approval",
"OBX": "PoS raised 30%\u219238% (strong early data); approval 6\u21924 yrs (strong data); \u2212 $58M expected spend to approval",
"ATTO": "PoS capped 25%\u21928% (weak data); \u2212 $225M expected spend to approval",
"VRXA": "peak \u00d70.4 (undifferentiated); \u2212 $168M expected spend to approval",
"ETRA": "PoS raised 35%\u219238% (strong early data); approval 4\u21923 yrs (strong data); \u2212 $43M expected spend to approval",
"CTY": "peak \u00d70.7 (undifferentiated); \u2212 $150M expected spend to approval",
"RTSN": "peak \u00d70.7 (undifferentiated); \u2212 $180M expected spend to approval"
}
D = json.load(open(path)); n = 0
for r in D:
    t = r['ticker']
    if t not in B or r.get('inp_review_done'): continue
    b = B[t]
    if 'pos' in b and r.get('pos') != b['pos']: r['pos'] = b['pos']; n += 1
    if 'pk' in b and r.get('peak_sales') != b['pk']: r['peak_sales'] = b['pk']; n += 1
    if 'y' in b and r.get('yrs_appr') != b['y']: r['yrs_appr'] = b['y']; n += 1
    r['inp_review'] = 'Set by a removed rule on Nov 27 2026 (' + N[t] + '); re-judge PoS, peak and timing on the evidence.'
json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('baked rule values into inputs:', n, 'fields across', len(B), 'names')
