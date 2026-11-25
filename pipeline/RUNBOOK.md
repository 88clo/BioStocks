# Monthly refresh runbook

> Before starting, read `NORTH_STAR.md` (repo root). At the end of each refresh, update its table: move anything newly built out of "What's still missing" and keep the track-record answer current.

Target cadence: one full refresh mid-month (memo edition), plus a short close-out when quarterly filings land.

## 0. Freeze first
`python3 scripts/snapshot_calls.py ledger/<date>_before-refresh.json` — writes every name's page-computed call, upside, top/short-pick flags and a sha256. Never edit a ledger after writing it; the track record depends on it.

## 1. Market data (automatic, ~1 minute)
- `fetch_prices.py`: 5-year daily closes and volumes for every ticker in data, parked, portfolio, price history and IPO lists. Source: Yahoo chart endpoint (reachable from the Claude workspace shell; StockAnalysis, SEC and Nasdaq are not).
- `fetch_fundamentals.py`: quarterly cash + short-term investments, long-term investments, total debt, shares, net income, operating cash flow, revenue, stock issuance.
- `refresh_apply.py`:
  - market cap = price × curated fully diluted shares (warrants/pre-funded included); splits after the share date rescale shares
  - exact 1M/3M/12M/24M/36M returns, 63-day mean dollar volume (ADV)
  - balance sheet only if Yahoo has a **newer** quarter than the curated one; curated FD overlay is kept and scaled by the change in ordinary shares
  - prints every >25% mover and every name leaving the $50M–$30B band. Those prints are the to-do list for step 2.

## 2. Event check (judgement, ~20–40 searches)
For each printed mover and each flag carried from the last run: search the company's news for the period, read the release, and decide.
- Write edits in `pipeline/patches/<date>_events.py` (pitch, events note, share/cash changes for offerings, `veto` when a thesis is broken or the share count is unknown). Run it.
- Log findings and sources in `pipeline/logs/events_<date>.md`.
- Offerings: add shares and net proceeds pro forma (note whether the greenshoe is included).

## 3. Deep diligence (monthly edition only)
Re-verify the shortlist (top picks, shorts, highest-conviction longs) against filings, ClinicalTrials.gov and FDA; red-team each one. This is the expensive step (≈40–60k tokens per name). Edit rows via a dated patch file.

## 4. Status, build, freeze, score
`normalize_catalysts.py data/data.json` (after the event check: merges the key catalyst, the next-catalyst line and the schedule into one ordered list, splits compound entries, labels each at the precision given, e.g. 4Q26 not Dec 31, flags past-due dates to verify), `log_catalysts.py <date>` (freezes the catalyst schedule point-in-time into ledger/ so the track record can test what was knowable), `concise_text.py data/data.json` (short efficacy and indication for the Companies table; full text stays on the card), `update_status.py` (edit the `ASOF`/`RUN` dates at the top), `build.py`, `snapshot_calls.py ledger/<date>_refresh.json`, `track_record.py`, `radar_gaps.py`, `call_history.py`, `changes.py` (diff of the two latest ledgers for the Brief), `build.py`.

Also record each catalyst's date as it stands at the refresh (the ledger keeps `cat_date`), so the track record can later tell whether a big move was on the calendar beforehand.

## 5. Check
Open `index.html` headless (`snapshot_calls.py` prints page errors) and click through Brief, Track record, Raise radar, White space, Full table, TA summary and Monthly memo. Spot-check five prices against a quote page.

## Known gaps
- 13F holders: no reachable source from the workspace shell; lists date from Sep 13.
- Oct 2026 frozen ledger (`ledger/2026-10.json`) was not recovered; the Oct memo's printed names stand in for it.
- Insight suggestions and lens scores cover ~65 names.

## December 2026 refresh checklist (from the Nov 23 review)
- Re-check SVRA and CAPR Nov 22 PDUFA outcomes; resolve the other ~60 "past due, verify" catalysts (list: run normalize_catalysts.py and grep st=late).
- Fix source text where efficacy describes a non-lead program or has no numbers (concise_text.py prints the count; hand-written overrides live in data/eff-curated.json, remove an override once the source text is right).
- CGEM: benchmark text describes EGFR NSCLC but the lead is a CD19 engager in autoimmunity; rewrite.
- Run log_catalysts.py so the Dec ledger has a point-in-time calendar.

## Valuation v2 (Nov 23 2026)
- Model rules live in `valParts()` in pipeline/template.html (cost to approval, existing business, evidence-matched PoS, differentiation haircut, timing for strong data). The Record page lists them as principles.
- Input fixes go in a dated patch (`pipeline/patches/2026-11-23_valuation_review.py` sets peak_sales, pos, probadj_sales, val_note; `book_add` marks companies whose product revenue is separate from the lead).
- Each refresh: list names where the upside disagrees with the drug (strong science with downside, weak science with >50% upside, failed primary with upside) and fix the inputs, not the call.
- Ledger globs read `ledger/2*.json` only; catalyst snapshots (`catalysts_*.json`) are not call ledgers.

## Theses, variant views and CEO notes (Nov 24 2026)
- Every thesis shows a computed *Variant view* (template `variantView()`): the odds or sales today's price implies vs ours, and why. When rewriting a written thesis, state the variant in words too: what the market believes, what we believe and the evidence, what proves us wrong and when.
- *What I'd tell the CEO* notes are rule-based (`ceoNotes()` in pipeline/synth.html, the 4 Ms: Money, Message, Moves, Milestones). Review the priority names' notes each refresh and refresh stale researched suggestions in data/sug-data.json.
- *What worked* (Record, 2025–26) reads quarterly prices plus `approved_on` (pipeline/patches/2026-11-24_approval_dates.py; add new first approvals there). Point-in-time market cap needs quarterly share counts (`scripts/fetch_fundamentals.py` → cache/fund) and point-in-time phase needs trial history; both still to wire in.

## Quarterly prices, market caps and What worked (Nov 24 2026)
- `python3 scripts/rebuild_priceq.py` after fetching daily prices: rebuilds quarter-end adjusted closes from cache/prices (the old file was only gap-filled and partly unadjusted).
- `python3 scripts/fetch_shares_hist.py` (Yahoo share counts → cache/shares) then `python3 scripts/build_mcq.py` → data/mcq.json, point-in-time quarter-end market caps (split-adjusted, calibrated on the Sep 12 2026 snapshot).
- data/retro-2025.json holds researched drivers of the biggest 2025 moves; data/stage-sep12.json the Sep 12 snapshot stages.
- Point-in-time clinical phase needs ClinicalTrials.gov, which the workspace allowlist blocks; allow clinicaltrials.gov to add it.
- `python3 scripts/classify_modality.py` tags each lead program with a broad modality (data.json and parked rows; hand overrides inside); What worked uses it.
- `python3 scripts/classify_novelty.py` tags each lead program First-in-class / Next-gen, validated / Late entrant from diff_detail, threat and pitch (hand overrides inside; checked by hand for the 45 largest). Rerun after rewriting differentiation text. Modality and Novelty rows in What worked are benchmarked against classified names only, since dropped-out names are mostly unclassified.
- Point-in-time clinical phase needs clinicaltrials.gov, which the workspace network allowlist blocks; once allowed, fetch each lead drug's trial history and feed it to DIMS.stage.
- Catalyst setups (What's next, synth.html `setups()`): event tree per lead-program binary catalyst in the next six months. Failure value = 85% cash + existing business + 10% of the market's pipeline value; success value = price-implied at historical step odds (FDA 85%, Ph3 55%, Ph2 35%, Ph1 60%) tilted halfway in log terms toward our model, capped 2×. Our odds from PoS by step. IPO placeholder calls are excluded. Retune `QM`/`CTP` if base rates change.
- What worked holding period (1/2/4 quarters): cohorts formed at quarter start, held N quarters; longer holds overlap.
- Capital tab: `python3 scripts/build_investors.py` (after fetch_prices) → data/investors.json: holder books from holders-baked.json priced at the Sep 11 snapshot and now, 12M look-back, XBI/IBB/median benchmarks, ownership split. data/capital-markets.json is hand-entered from William Blair's Quarterly Rx (follow-ons, PIPEs, venture, M&A, funds by quarter; IPOs by quarter): add the new quarter each time a recap comes out. Equity supply and the IPO market table moved from What's next to Capital › Liquidity.
- What's next: setup numbers sit on each catalyst row; filter Best setups = expected ≥ +25% or ≤ −15%. Filing/acceptance/submission events are not binary and are skipped.
- What's next numbers by method: tree (lead readout/FDA), o (other program: 25% of pipeline value at historical odds), r (filing/acceptance: 92%, refusal −30% of program), c (sales/launch update: ±12% approved, ±8% others). 'What we expect' comes from the event's expected return (±10%); ⚑ flags events pointing against the stock call.
- Capital › Investors: ownership by company size, average position, median stake, top-5 concentration and style vs all specialists (book-weighted size, stage, area, modality, novelty; ≥10pt gaps). Holding period needs 13F history from sec.gov (blocked in this workspace).
- Capital › Liquidity › Net equity supply = (IPOs + follow-ons + PIPEs) − 70% of M&A value, as % of covered cap at quarter start (XBI-scaled before 4Q24), vs XBI same and next quarter.
- Catalyst scoring is one rule per event class (synth.html `EVC`, `evcOf`): lead readout/FDA decision = event tree (our view); other-program readout, data update, filing, FDA meeting, trial start = priced fair on a program stake; sales updates, corporate and other = symmetric % of cap. Only the tree carries expected return. The class table is under the setups chart.
- Liquidity chart: raised (stacked) and M&A bars on one axis, net equity supply line = IPO + follow-on + PIPE − 70% of M&A. The correlation note sits under the chart.
- SEC: data.sec.gov works (filing lists); 13F holdings documents need www.sec.gov allowed as well.
- Catalyst views: data/cat-views.json holds our judged view per important catalyst (odds, expected move each way, why), matched by ticker + a text fragment of the event; it overrides the rules (★ in What's next, filter ★ Our views). At each refresh: delete views whose events happened, add views for new key catalysts (start with the largest caps and our Long/Short names), and re-check odds against new data.
- 13F: `python3 scripts/fetch_13f.py 9` (SEC EDGAR: data.sec.gov + www.sec.gov must be allowed; ~45 min for ~160 funds, cached in cache/13f, re-runs only fetch new filings) then `python3 scripts/build_13f.py` → data/13f.json (CUSIP→ticker by issuer name + share-count match; biotech book, holding period, turnover, copy-the-book 4Q/8Q returns vs XBI, specialist pool). Capital › Investors shows the 13F leaderboard; the Yahoo snapshot stays in a fold-out.
- What's next shows Moves the stock? (Major ≥30% / Moderate 10–30% / Minor, from the value riding on the event) and Skew (positive if our odds ≥ typical step odds +10pt and the stock trades below our value; negative if our odds ≤ typical −10pt or the stock is 25%+ above our value; balanced otherwise; ★ written views override). Duplicate catalyst lines for the same event in the same month are merged.
- Ownership: `python3 scripts/fetch_13f.py --big` pulls the latest 13F for the 31 largest index funds, banks and generalists (cache/13f/big_ciks.json; Vanguard now files as Vanguard Capital Management and Vanguard Portfolio Management); build_13f.py combines them with the specialist books into own[ticker] = share of shares outstanding by type.
- Skew (What's next) = four ±1 signals: our odds vs typical step odds (10pt gap for FDA/Ph3, 20pt for Ph1–2); valuation once (25%+ above our value −, else cash ≥70% of cap or ≥100% upside +); 3-month move (≥+75% −; ≤−40% + unless prior data weak); prior data strength for readouts. ±2 = skewed. For approved companies only events naming the lead drug count as lead. Events whose text points to 2H/year-end 2027 or 2028 are treated as undated.
- Complete ownership: download SEC's quarterly Form 13F data set (sec.gov/data-research/sec-markets-data/form-13f-data-sets; newest zip) to cache/13f_bulk/q2 and run build_13f.py → own_all (every 13F filer, by type) and flow (specialist buys/sells, value ÷ point-in-time cap, 2026 IPOs excluded). The Sep 30 data set appears after November; swap it in when it does.
- What worked: the "Next quarter" column blends each group's hit rate, last quarter and a hand-written backdrop (CTX in synth2.html): update CTX each quarter.
- Public-target M&A cash (proposal for net supply): tag each M&A deal in the William Blair/BioPharma Dive deal lists as public or private target and cash vs stock, sum cash paid to public holders per quarter (equity value × cash share). Cross-check with our own coverage: names leaving coverage as "acquired" × their last market cap.
