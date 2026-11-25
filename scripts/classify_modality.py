"""Tag each company's lead program with a broad modality (data.json and parked-data.json -> 'modality').
Rule-based on the mechanism and drug text; first match wins, most specific first."""
import json, re, pathlib, sys
root = pathlib.Path(__file__).resolve().parents[1]
RULES = [
    ("Cell therapy", r"\bCAR[- ]?T\b|CAR-NK|\bNK cell|T[- ]cell therapy|\bTIL\b|cell therap|autologous|allogeneic|\bTCR-T|stem cell|iPSC|\bTreg"),
    ("Gene therapy & editing", r"gene therap|\bAAV|lentivir|gene edit|base edit|prime edit|CRISPR|in vivo edit|meganuclease|epigenetic|transgene|adenoviral vector"),
    ("RNA (siRNA, ASO, mRNA)", r"siRNA|RNAi|antisense|\bASO\b|oligonucleotide|mRNA|RNA edit|exon skip|splice[- ]switch|GalNAc|microRNA|miRNA|saRNA"),
    ("ADC & radioconjugate", r"antibody[- ]drug conjugate|\bADC\b|radioligand|radiopharm|radioconjugate|\b177Lu|\b225Ac|Lu-177|Ac-225|\b212Pb|drug conjugate|peptide conjugate"),
    ("Bispecific & multispecific", r"bispecific|trispecific|multispecific|T[- ]cell engager|\bTCE\b|BiTE|×|dual-target(ing)? antibod"),
    ("Vaccine & microbiome", r"vaccine|oncolytic|microbiome|phage|bacterial (strain|consortium)"),
    ("Antibody & protein", r"antibod|\bmAb\b|nanobody|\bFc[- ]|fusion protein|ligand[- ]trap|enzyme replacement|\bERT\b|recombinant|biologic|\bprotein\b|immunoglobulin|\bIgG|decoy receptor|immunocytokine|\banti-(IG|CD|Fc|IL|TSLP|TL1A|IgE|FGF|VEGF|PD|C5|TNF|BAFF|APRIL|OX40|HER|TROP|B7|LAG|TIGIT|GPC|CLDN|DLL)"),
    ("Peptide", r"peptide|amylin analog"),
    ("Small molecule", r"small[- ]molecule|\boral\b|tablet|capsule|inhibitor|agonist|antagonist|modulator|activator|degrader|PROTAC|molecular glue|blocker|inhaled|topical|\bkinase\b|stabilizer|analog|deuterated|scavenger|\bTKI\b|stabilizer|analog|deuterated|scavenger|sustained-release|extended-release|delayed-release|intranasal|transdermal|patch|hydrogel|intravesical|omega-3|compound|miotic|epinephrine|prodrug|metformin|anesthetic|telomere|mTOR|PI3K|gemcitabine|mitomycin|EGFR"),
    ("Vaccine & microbiome", r"vaccine|oncolytic|virus-based|microbiome|phage|bacterial (strain|consortium)"),
    ("Device & other", r"implant|device|ablation|nanoparticle|microchip|generic|biosimilar|drug delivery|matrix"),
]
OVERRIDE = {"PTCT": "Small molecule", "GUTS": "Device & other", "ASND": "Peptide", "KOD": "Antibody & protein", "FBIO": "Small molecule", "OCUL": "Small molecule", "FHTX": "Small molecule"}  # hand checks
def classify(r):
    if r.get("ticker") in OVERRIDE: return OVERRIDE[r["ticker"]]
    for keys in (("moa",), ("drug", "drug_full"), ("stage_full", "pitch", "pitch_concise", "indication")):   # most specific text first
        t = " ".join(str(r.get(k) or "") for k in keys)
        if not t.strip(): continue
        for name, rx in RULES:
            if re.search(rx, t, re.I): return name
    return None
for f in ["data/data.json", "data/parked-data.json"]:
    p = root / f; D = json.load(open(p)); rows = D["rows"] if isinstance(D, dict) else D
    for r in rows: r["modality"] = classify(r)
    json.dump(D, open(p, "w"), ensure_ascii=False, separators=(",", ":"))
    from collections import Counter
    print(f, Counter(r["modality"] for r in rows).most_common())
