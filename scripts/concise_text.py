"""Short forms of two long free-text fields for the Companies table.

eff_short  -- the lead program's efficacy in one or two sentences, by a fixed framework:
              [drug (dosing) + approval status]  ·  [trial, phase, population: primary result vs comparator, key stats]
              Sentences about catalysts, filings, deals, cash, other programs or commentary are dropped
              (they live in the Next column, the catalyst schedule and the card). Target <= ~230 characters.
ind_short  -- the lead indication with standard abbreviations (sHTG, NSCLC, mCRC, r/r ...) and no commentary.

The full texts stay in `efficacy` and `indication` and are shown on the company card.
Derived fields only: re-running gives the same result.  Usage: python3 scripts/concise_text.py [data/data.json]
"""
import json, re, sys

# ---------------------------------------------------------------- indication abbreviations
IND = [
    (r"metabolic dysfunction[- ]associated steatohepatitis", "MASH"), (r"non-?alcoholic steatohepatitis", "NASH"),
    (r"severe hypertriglyceridemia", "sHTG"), (r"hypertriglyceridemia", "HTG"), (r"familial chylomicronemia syndrome", "FCS"),
    (r"atherosclerotic cardiovascular disease", "ASCVD"), (r"heterozygous familial hypercholesterolemia", "HeFH"),
    (r"sickle[- ]cell disease", "SCD"), (r"von willebrand disease", "VWD"), (r"beta[- ]thalassemia", "β-thal"),
    (r"paroxysmal nocturnal hemoglobinuria", "PNH"), (r"immune thrombocytopenia", "ITP"), (r"graft[- ]versus[- ]host disease", "GVHD"),
    (r"chronic lymphocytic leukemia", "CLL"), (r"acute myeloid leukemia", "AML"), (r"acute lymphoblastic leukemia", "ALL"),
    (r"chronic myeloid leukemia", "CML"), (r"multiple myeloma", "MM"), (r"diffuse large b-cell lymphoma", "DLBCL"),
    (r"large b-cell lymphoma", "LBCL"), (r"follicular lymphoma", "FL"), (r"mantle cell lymphoma", "MCL"),
    (r"cutaneous t-cell lymphoma", "CTCL"), (r"peripheral t-cell lymphoma", "PTCL"), (r"myelodysplastic syndromes?", "MDS"),
    (r"lower-risk MDS", "LR-MDS"), (r"higher-risk MDS", "HR-MDS"), (r"polycythemia vera", "PV"), (r"myelofibrosis", "MF"),
    (r"essential thrombocythemia", "ET"), (r"systemic lupus erythematosus", "SLE"), (r"lupus nephritis", "LN"),
    (r"non-?small[- ]cell lung cancer", "NSCLC"), (r"small[- ]cell lung cancer", "SCLC"),
    (r"metastatic colorectal cancer", "mCRC"), (r"colorectal cancer", "CRC"), (r"hepatocellular carcinoma", "HCC"),
    (r"pancreatic ductal adenocarcinoma", "PDAC"), (r"metastatic pancreatic cancer", "mPDAC"), (r"pancreatic cancer", "PDAC"),
    (r"metastatic castration[- ]resistant prostate cancer", "mCRPC"), (r"castration[- ]resistant prostate cancer", "CRPC"),
    (r"metastatic hormone[- ]sensitive prostate cancer", "mHSPC"), (r"prostate cancer", "PCa"),
    (r"non-muscle[- ]invasive bladder cancer", "NMIBC"), (r"muscle[- ]invasive bladder cancer", "MIBC"),
    (r"metastatic urothelial (?:cancer|carcinoma)", "mUC"), (r"urothelial carcinoma", "urothelial cancer"),
    (r"clear[- ]cell renal cell carcinoma", "ccRCC"), (r"renal cell carcinoma", "RCC"),
    (r"triple[- ]negative breast cancer", "TNBC"), (r"metastatic breast cancer", "mBC"), (r"breast cancer", "BC"),
    (r"head and neck squamous cell carcinoma", "HNSCC"), (r"squamous cell carcinoma", "SCC"), (r"glioblastoma", "GBM"),
    (r"gastroesophageal junction", "GEJ"), (r"gastro-?esophageal", "GE"), (r"biliary tract cancer", "BTC"),
    (r"advanced solid tumou?rs", "adv. solid tumors"),
    (r"amyotrophic lateral sclerosis", "ALS"), (r"alzheimer'?s disease", "Alzheimer's"), (r"parkinson'?s disease", "Parkinson's"),
    (r"huntington'?s disease", "HD"), (r"spinal muscular atrophy", "SMA"), (r"duchenne muscular dystrophy", "DMD"),
    (r"myotonic dystrophy type 1", "DM1"), (r"facioscapulohumeral muscular dystrophy", "FSHD"), (r"myasthenia gravis", "MG"),
    (r"generalized MG", "gMG"), (r"multiple sclerosis", "MS"), (r"major depressive disorder", "MDD"), (r"schizophrenia", "SCZ"),
    (r"essential tremor", "ET"), (r"developmental and epileptic encephalopathies", "DEE"), (r"chronic inflammatory demyelinating polyneuropathy", "CIDP"),
    (r"atopic dermatitis", "AD"), (r"plaque psoriasis", "PsO"), (r"psoriatic arthritis", "PsA"), (r"rheumatoid arthritis", "RA"),
    (r"ulcerative colitis", "UC"), (r"crohn'?s disease", "CD"), (r"hidradenitis suppurativa", "HS"), (r"inflammatory bowel disease", "IBD"),
    (r"chronic spontaneous urticaria", "CSU"), (r"eosinophilic esophagitis", "EoE"), (r"generalized pustular psoriasis", "GPP"),
    (r"sjogren'?s|sjögren'?s", "Sjögren's"), (r"systemic sclerosis", "SSc"), (r"idiopathic pulmonary fibrosis", "IPF"),
    (r"chronic obstructive pulmonary disease", "COPD"), (r"pulmonary arterial hypertension", "PAH"), (r"cystic fibrosis", "CF"),
    (r"non-cystic fibrosis bronchiectasis", "NCFB"), (r"heart failure with preserved ejection fraction", "HFpEF"),
    (r"heart failure with reduced ejection fraction", "HFrEF"), (r"heart failure", "HF"), (r"obstructive hypertrophic cardiomyopathy", "oHCM"),
    (r"hypertrophic cardiomyopathy", "HCM"), (r"transthyretin amyloid cardiomyopathy", "ATTR-CM"), (r"atrial fibrillation", "AFib"),
    (r"type 2 diabetes", "T2D"), (r"type 1 diabetes", "T1D"), (r"chronic kidney disease", "CKD"), (r"iga nephropathy", "IgAN"),
    (r"focal segmental glomerulosclerosis", "FSGS"), (r"autosomal dominant polycystic kidney disease", "ADPKD"),
    (r"primary biliary cholangitis", "PBC"), (r"primary sclerosing cholangitis", "PSC"), (r"geographic atrophy", "GA"),
    (r"wet age-related macular degeneration", "wAMD"), (r"neovascular age-related macular degeneration", "nAMD"),
    (r"age-related macular degeneration", "AMD"), (r"diabetic macular edema", "DME"), (r"diabetic retinopathy", "DR"),
    (r"thyroid eye disease", "TED"), (r"retinitis pigmentosa", "RP"), (r"relapsed/refractory|relapsed or refractory|relapsed-refractory", "r/r"),
    (r"first[- ]line", "1L"), (r"second[- ]line", "2L"), (r"third[- ]line", "3L"), (r"\bmetastatic NSCLC", "mNSCLC"),
    (r"\bmetastatic\b", "met."), (r"\badvanced\b", "adv."), (r"\bdisease\b", "dz"),
]


def initials_match(phrase, ab):
    ini = ''.join(w[0].lower() for w in re.split(r'[\s/-]+', phrase) if w)
    letters = re.sub(r'[^a-z]', '', ab.lower())
    if len(letters) < 2:
        return False
    i = 0
    for ch in ini:
        if i < len(letters) and ch == letters[i]:
            i += 1
    return i == len(letters)


def abbr_sub(m):
    phrase, ab = m[1], m[2]
    words = phrase.split()
    for k in range(1, len(words) + 1):            # shortest tail of the phrase that the abbreviation spells
        tail = ' '.join(words[-k:])
        if initials_match(tail, ab):
            return ' '.join(words[:-k] + [ab])
    if ab.upper() == ab and len(words) <= 4 and words and words[0][0].lower() == ab[0].lower():
        return ab                                  # e.g. Nasopharyngeal carcinoma (NPC)
    return m[0]


def ind_short(s):
    s = (s or '').strip()
    if not s:
        return ''
    parts, depth, cur = [], 0, ''
    for ch in s:                                    # split on top-level semicolons only
        depth += (ch == '(') - (ch == ')')
        if ch == ';' and depth <= 0:
            parts.append(cur); cur = ''
        else:
            cur += ch
    parts = [p.strip() for p in parts + [cur] if p.strip()][:2]
    out = []
    for p in parts:
        p = re.split(r'\s+(?:—|--|–|-)\s+', p)[0]
        p = re.sub(r'\s*\([^)]*$', '', p)              # unbalanced trailing bracket                     # drop " — commentary"
        p = re.sub(r'([A-Za-z][\w\s\'/-]{4,}?)\s*\(([A-Za-z0-9+/\-]{2,9})\)', lambda m: abbr_sub(m), p)
        p = re.sub(r'\s*\((?:[^()]*\s[^()]*)\)', '', p)                # parenthetical commentary (has spaces)
        for rx, ab in IND:
            p = re.sub(rx, ab, p, flags=re.I)
        p = re.sub(r'\b(\S+)\s*\(\1\)', r'\1', p)
        p = re.sub(r'\s+', ' ', p).strip(' ,.')
        if out and (len(p.split()) > 5 or re.search(r'\b(?:is|are|program|secondary|pillar|not)\b', p)):
            continue                                  # second indication only if it is a short name
        out.append(p)
    return '; '.join(o for o in out if o)


# ---------------------------------------------------------------- efficacy condenser
STAT = re.compile(r'(\d+(?:\.\d+)?\s*%|\bvs\.?\b|\bHR\s*[=:]?\s*0?\.\d|\bp\s*[<=]\s*0?\.\d|\bORR\b|\bPFS\b|\bOS\b|\bCR\b|\bmet (?:the|its|all|both)\b|\bmissed\b|\bfailed\b|reduction|response|remission|improv|endpoint|placebo|knockdown|\bLDL|\bTG\b|\bHbA1c|weight loss|seizure)', re.I)
NOTEFF = re.compile(r'(PDUFA|\bs?NDA\b|\bs?BLA\b|\bMAA\b|filing|filed|submission|priority review|STAR pilot|\bPRV\b|voucher|licen[cs]e|upfront|milestone|royalt|\$\d|cash|runway|financ|partner|dosing (?:started|began)|enrol+|\bIND\b|launch|sales|revenue|CEO|CFO|guidance|not previously|real (?:second|severity|corporate|technical)|also:|stock|analyst|shareholder|commercial|is the edge|reimburs|label expansion|accept)', re.I)
CATALYST_ONLY = re.compile(r'^(?:topline|data|readout|results?)\b.*\b(?:expected|due|by|in)\b.*(?:20\d\d|[12]H|Q[1-4])', re.I)
CAPS_KEEP = set('ORR PFS OS CR PR DCR HR ITT NDA BLA FDA EMA FCS SHTG TG LDL ASCO ESMO ASH ESC AHA AAN ACR EASI PASI IGA MRD BCG CAR CRISPR ADC PET MRI CT KRAS EGFR HER2 PD-1 PD-L1 CTLA-4 RNA DNA LNP APOC3 ANGPTL3 GLP-1 FXI TTR VEGF MASH NASH DMD ALS SMA AML CLL MM NSCLC SCLC CRC HCC PDAC RCC NMIBC CIS QOL KCCQ HFPEF CKD EGFR UACR IGAN FSGS'.split())
DOSE = [(r'once[- ]quarterly|every (?:three|3) months|quarterly dosing', 'Q3M'), (r'once[- ]monthly|every month', 'QM'),
        (r'once[- ]weekly', 'QW'), (r'once[- ]daily', 'QD'), (r'twice[- ]daily', 'BID'), (r'every (?:two|2) weeks', 'Q2W'),
        (r'every (?:six|6) months|twice[- ]yearly', 'Q6M'), (r'\bmonth (\d+)\b', r'M\1'), (r'\bweek (\d+)\b', r'wk \1'), (r'\bPhase\s*(\d(?:/\d)?[ab]?)\b', r'Ph\1'), (r'\bmonths?\b', 'mo'),
        (r'\bweeks?\b', 'wk'), (r'\bpatients\b', 'pts'),
        (r'\bstatistically significant\b', 'significant'), (r'\bapproximately\b', '~'), (r'\bcompared (?:with|to)\b', 'vs'),
        (r'\bversus\b', 'vs'), (r'\bplacebo\b', 'placebo'), (r'\s+—\s+', ' — ')]


def caps_fix(s):
    def f(m):
        w = m[0]
        if w in CAPS_KEEP or re.search(r'\d', w) or len(w) < 4:
            return w
        return w.lower()
    # shouted English words (STILL, QUARTERLY, NOT, SAME) -> lower case; keep acronyms/trial names with digits
    return re.sub(r'\b[A-Z]{4,}\b(?![-\d])', lambda m: f(m) if m[0].lower() in ENGLISH else m[0], s)


ENGLISH = set('''still not same only real actual quarterly monthly weekly daily approved failed missed imminent active new now
this that these those first second third major minor clear clearly entire entirely genuine fully complete completed underway
before after ahead behind strong weak very much more most less least also both all none never ever every any some other
disappointment cratering stock beat beats rejected accepted filed planned started start ongoing enrolling durable
deep deeper higher lower double single half full total positive negative significant superior inferior same without with
requires required lifelong months weeks years days data results topline breakthrough transformational modest small large
removed added confirmed dual commercial licensed oral sustained overwhelming not unconfirmed indefinitely technically preclinical clinical interim final early late emerging'''.split())


def sentences(t):
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'\bvs\.', 'vs', t)
    parts = re.split(r'(?<=[.;])\s+(?=[A-Z(\[])|(?<=\.)\s+(?=\d)', t)
    out = []
    for p in parts:
        p = p.strip()
        if p:
            out.append(p)
    return out


def score(s, kw=()):
    st = len(STAT.findall(s))
    ne = len(NOTEFF.findall(s))
    sc = min(st, 4) * 2 - ne * 2.5
    if re.search(r'\bapproved\b|\bFDA[- ]approved\b', s, re.I) and len(s) < 160:
        sc += 2           # approval status of the lead
    if kw and any(re.search(r'\b' + re.escape(k) + r'\b', s, re.I) for k in kw):
        sc += 2           # about the lead indication
    if CATALYST_ONLY.search(s):
        sc -= 4
    return sc


def clean_sentence(s):
    s = re.sub(r'\s*\((?:[A-Z][A-Za-z]*(?:,\s*|\s+and\s+|\)))+', lambda m: '' if m[0].count(',') >= 2 else m[0], s)   # (US, EU, China, ...) lists
    s = re.sub(r'\s*\((?:company|source|per)[^)]*\)', '', s, flags=re.I)
    s = re.sub(r',?\s*and now (?:in|approved in) \d+ countries', '', s, flags=re.I)
    s = re.split(r'\s+—\s+(?=(?:the|a|an|this|real|not|which|and|but|already|so|now)\b)', s)[0]   # trailing commentary after a dash
    for rx, rep in DOSE:
        s = re.sub(rx, rep, s, flags=re.I)
    s = caps_fix(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def eff_short(t, ind='', limit=250):
    t = (t or '').strip()
    if not t:
        return ''
    S = sentences(t)
    lead = (ind or '').split(';')[0]
    kw = [w for w in re.findall(r"[A-Za-z][\w'/+-]{2,}", lead) if w.lower() not in ('with', 'and', 'the', 'adv.', 'met.', 'acute', 'chronic', 'refractory')]
    scored = [(i, s, score(s, kw)) for i, s in enumerate(S)]
    keep = [x for x in scored if x[2] > 0]
    if not keep:                                   # no efficacy statement: first sentence, trimmed
        keep = scored[:1]
    # always keep the best-scoring sentence; add others in order while they fit
    best = max(keep, key=lambda x: (x[2], -x[0]))
    chosen = {best[0]}
    total = len(clean_sentence(best[1]))
    for i, s, sc in sorted(keep, key=lambda x: (-x[2], x[0])):
        if i in chosen:
            continue
        L = len(clean_sentence(s))
        if total + L + 1 <= limit:
            chosen.add(i)
            total += L + 1
    out = ' '.join(clean_sentence(S[i]) for i in sorted(chosen))
    out = re.sub(r'\s*[;,]\s*$', '.', out)
    if len(out) > limit:                            # drop wordy asides without numbers
        out = re.sub(r'\s*\((?=[^()]*\s[^()]*\s[^()]*\s)[^()\d]*\)', '', out)
    if len(out) > limit + 30:                       # one very long sentence: cut at a clause boundary
        cut = out[:limit + 40]
        j = max(cut.rfind('; '), cut.rfind(', '), cut.rfind(' ('))
        out = (cut[:j] if j > limit * 0.6 else cut.rsplit(' ', 1)[0]) + '…'
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'data/data.json'
    D = json.load(open(path))
    for r in D:
        r['ind_short'] = ind_short(r.get('indication'))
        r['eff_short'] = eff_short(r.get('efficacy'), r['ind_short'])
    json.dump(D, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
    import statistics
    print('eff_short median', statistics.median(len(r['eff_short']) for r in D), 'chars (full text median',
          statistics.median(len(r.get('efficacy') or '') for r in D), ') · ind_short median',
          statistics.median(len(r['ind_short']) for r in D), 'chars (full', statistics.median(len(r.get('indication') or '') for r in D), ')')


if __name__ == '__main__':
    main()
