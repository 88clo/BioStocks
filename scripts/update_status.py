"""Update the Refresh-status table, as-of stamps and header tape after a refresh run."""
import json, pathlib, re, collections
root = pathlib.Path(__file__).resolve().parents[1]
D = json.load(open(root/"data/data.json")); n = len(D)
ASOF = "2026-11-20"; RUN = "2026-11-22"
cov = lambda k: sum(1 for r in D if r.get(k) is not None)
bs = collections.Counter((r.get("inputs") or {}).get("bs_date") for r in D)
q3 = sum(v for k, v in bs.items() if k and k >= "2026-08-31")
R = json.load(open(root/"data/refresh-data.json"))
def upd(sec, **kw):
    for row in R["rows"]:
        if row["sec"] == sec: row.update(kw); return
upd("Prices and market caps", asof=ASOF, cov=round(cov("price")/n, 3), how="fetch_prices.py pulls 5y daily history per name from Yahoo's chart endpoint (one bulk run, ~15 s); refresh_apply.py rewrites price, market cap (FD shares x price), labels", src="Yahoo Finance chart API (shell)", tok="~0", wall="~1 min", note=f"{cov('price')} of {n} names; closes as of Fri {ASOF}.")
upd("1M return", asof=ASOF, cov=round(cov("r1m")/n, 3), how="Exact: close 30 days earlier from the same daily history", src="Yahoo daily closes", est=0)
upd("3M return", asof=ASOF, cov=round(cov("r3m")/n, 3), est=0, how="Exact: close 91 days earlier from 5y daily history (replaces month-end interpolation)", src="Yahoo daily closes", tok="0", wall="included", note=f"{cov('r3m')}/{n}; blanks are recent listings.")
upd("12M return", asof=ASOF, cov=round(cov("r12m")/n, 3), est=0, how="Exact: close 365 days earlier (split-adjusted)", src="Yahoo daily closes", note=f"{n-cov('r12m')} names blank (listed <12 months).")
upd("Cash, debt, shares (inputs)", asof=RUN, cov=round(q3/n, 3), how="fetch_fundamentals.py pulls quarterly balance sheet/cash flow lines; refresh_apply.py updates only names whose curated quarter is older (curated FD share overlay kept and scaled)", src="Yahoo fundamentals timeseries + curated FD overlay", tok="0", wall="~1 min", note=f"{q3} of {n} names on Aug-Sep 2026 quarters; 20 rolled forward on Nov 22; SLS pro forma for its Nov 18 $150M deal.")
upd("Event check, rest of universe (headline level)", asof=RUN, adj=0, note="Nov 22: every >25% mover since Nov 16 plus last cycle's 9 flags checked against releases (see pipeline/logs/events_2026-11-22.md). Flags cleared; CUE vetoed pending share count.")
upd("Calls and top picks", asof=RUN, note="Recomputed by the page on Nov 20 prices; frozen to ledger/2026-11-22_refresh.json.")
upd("Returns, Board, Map, Catalysts views", asof=ASOF, cov=0.98, note="Quarterly history back-filled from Yahoo (270 blanks filled); current quarter = Nov 20 close.")
upd("Holders (13F)", note="Most lists date from Sep 13 (Q2 13Fs). Q3 13Fs were due Nov 16; not re-pulled (no reachable source from the pipeline).")
upd("Monthly memo", note="November edition (Nov 18) unchanged; December edition due mid-December. Track record tab now scores every frozen call set to date.")
have = {row["sec"] for row in R["rows"]}
for sec, row in [("Track record", dict(asof=ASOF, cov=1.0, est=0, adj=0, how="track_record.py scores Sep 12 snapshot, Oct 13 memo, Nov 17 ledger vs later closes", src="Repo files + Yahoo closes", tok="0", wall="~10 s", cap="-", note="Out-of-sample: calls were frozen before the returns.")),
                 ("Raise radar + White space", dict(asof=RUN, cov=1.0, est=1, adj=0, how="radar_gaps.py: runway, catalyst window, run-up, issuance history; indication groups; negative-EV shells", src="Local + Yahoo fundamentals", tok="0", wall="~5 s", cap="-", note="Rule-based screen; verify a deal's terms before acting."))]:
    if sec not in have: R["rows"].insert(1, dict(sec=sec, **row))
json.dump(R, open(root/"data/refresh-data.json", "w"), indent=1)
A = json.load(open(root/"data/asof-baked.json"))
A["snapshot"]["asof"] = ASOF; A["clinical"]["asof"] = RUN; A["pr"]["asof"] = RUN
A["priceq"]["asof"] = "4Q26 (partial, to Nov 20)"
json.dump(A, open(root/"data/asof-baked.json", "w"), indent=1)
t = (root/"pipeline/template.html").read_text(encoding="utf-8")
t = re.sub(r'(<span class="tape" title=")[^"]*(")', r'\g<1>Prices and market caps as of 11.20.26 (Yahoo daily closes); exact 1M/3M/12M returns; Q3 cash/shares for most names (20 rolled forward 11.22.26); event check of every >25% mover and last cycle flags 11.22.26; top-pick diligence 11.04.26; clinical data re-checked vs Q3 reports 11.17.26; 13F holders mostly Sep\2', t, 1)
t = re.sub(r'(<span id="tapelabel">Data as of <span class="asof">)[^<]*', r'\g<1>11.20.26', t, 1)
(root/"pipeline/template.html").write_text(t, encoding="utf-8")
print("status updated; Q3-or-later balance sheets:", q3, "of", n)
