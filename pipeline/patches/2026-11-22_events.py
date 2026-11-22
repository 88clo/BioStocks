"""Hand-verified event patches, 2026-11-22 close-out (sources in pipeline/logs/events_2026-11-22.md)."""
import json, pathlib
root = pathlib.Path(__file__).resolve().parents[2]
D = json.load(open(root/"data/data.json")); by = {r["ticker"]: r for r in D}
PR = json.load(open(root/"data/pr-baked.json"))
def note(tk, ev): inp = by[tk].setdefault("inputs", {}); inp["events"] = (ev + " | " + (inp.get("events") or "")).strip(" |")
# SLS: $150M offering at $13.00 (11,538,462 sh) priced Nov 18, closing Nov 20; greenshoe (1.73M) not assumed
r = by["SLS"]; r["inputs"]["fd_shares_m"] = round(r["inputs"]["fd_shares_m"] + 11.538462, 4)
r["cash"] = (r.get("cash") or 0) + 141e6; r["mc"] = r["price"]*r["inputs"]["fd_shares_m"]*1e6; r["cash_pct_mc"] = round(r["cash"]/r["mc"], 4)
note("SLS", "Nov 18 2026: priced $150M follow-on at $13.00 (11.54M sh, JPM/TD Cowen), closed ~Nov 20; ~$141M net added pro forma; 30-day greenshoe 1.73M sh not included")
r["pitch_concise"] = "REGAL hit OS (24.0 vs 14.7 mo, HR 0.59, p=0.035, n=126) and the stock went +156% in a day, then SELLAS sold $150M at $13 the same night; the ~$2.9B cap is still ~6x our $500M peak, and BLA is 1H27."
PR["SLS"] = {"date": "11/18/26", "headline": "SELLAS prices $150.0M public offering at $13.00/share after positive REGAL Phase 3", "sentiment": "neutral"}
# CUE: -80% on Nov 17 after Q3 (EPS -$4.74 incl. Ascendant top-up share revaluation); no clinical failure found
note("CUE", "Nov 17 2026: stock -80% in one day after Q3 print; no clinical failure found; Q3 loss included Ascendant top-up share obligation revaluation -> check for large share issuance before trusting FD count")
by["CUE"]["pitch_concise"] = "CUE-221 CSU Ph2 still reads well (78% complete response at 4 mg/kg in high-IgE pts), but the stock fell 80% on Nov 17 with no clinical news; until the Ascendant top-up share count is confirmed, the $44M cap and LONG call are unreliable."
by["CUE"]["veto"] = True
PR["CUE"] = {"date": "11/17/26", "headline": "Shares fall ~80% after Q3; loss widened on Ascendant top-up share revaluation (share count under review)", "sentiment": "negative"}
# CRBP: -39% around ObesityWeek (CRB-913 12-wk weight loss 5% at 60 mg) — lead thesis (CRB-701) unchanged
note("CRBP", "Nov 10-20 2026: stock -39% around ObesityWeek; CRB-913 CANYON-1 showed 5% mean weight loss at 12 wk (60 mg); CRB-701 TEMPO-1 registrational dosing since Sep 29")
by["CRBP"]["pitch_concise"] = "CRB-701 (42.9% cORR in 2L OPSCC) is in a registrational trial since Sep 29, yet the stock fell 39% on a modest 5% obesity readout for CRB-913; $115M cash is ~2.7x the $42M cap."
PR["CRBP"] = {"date": "11/15/26", "headline": "CANYON-1 CRB-913 obesity data at ObesityWeek: 5% mean weight loss at 12 weeks (60 mg)", "sentiment": "negative"}
# GLSI: +40% sympathy with SELLAS peptide-vaccine Ph3 win; no FLAMINGO-01 interim yet
note("GLSI", "Nov 17-20 2026: +40% in sympathy with SELLAS peptide-vaccine Ph3 success; no FLAMINGO-01 interim reported; cash only ~$6M (9/30)")
PR["GLSI"] = {"date": "11/18/26", "headline": "Shares jump in sympathy with SELLAS peptide-vaccine Phase 3 win; FLAMINGO-01 interim still pending", "sentiment": "positive"}
for tk in ["SLS", "CUE", "CRBP", "GLSI", "ARTV", "GERN", "SION", "RGNX", "SANA", "SRPT", "BHVN", "LNTH", "DRUG", "IPHA", "ENTA"]:
    by[tk]["last_screened"] = "2026-11-22"
json.dump(D, open(root/"data/data.json", "w"), ensure_ascii=False, indent=1)
json.dump(PR, open(root/"data/pr-baked.json", "w"), ensure_ascii=False, indent=1)
print("patched SLS, CUE, CRBP, GLSI; screened 15")
