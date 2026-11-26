# Monthly refresh runbook

> Before starting, read `NORTH_STAR.md` (repo root). At the end of each refresh, update its table: move anything newly built out of "What's still missing" and keep the track-record answer current.

Target cadence: one full refresh mid-month (memo edition), plus a short close-out when quarterly filings land.

## Daily (or before any meeting): news, moves, the book
1. `python3 scripts/scan_8k.py` (~4 min): every 8-K since 10 days ago for covered companies, with the press-release headline; the Brief lists those that look like news. Read each one and patch outcomes (pipeline/patches/) before trusting that thesis. The first scan (Nov 25) found the Sanofi–Insmed deal, Arcus's PRISM-1 failure and Kymera's $1.5B offering.
2. `python3 scripts/fetch_prices.py && python3 scripts/moves_since.py && python3 scripts/trade_info.py` → prices, moves vs XBI, liquidity (ADV, days to build $10M), volatility and the market-move proxy.
3. `python3 scripts/mark_book.py` → data/book-marks.json (paper book P&L vs XBI). Then `python3 scripts/build.py` (now also runs the thesis audit; any AUDIT WARNING must be fixed).
At each monthly refresh, after build: `python3 tests/freeze_book.py` re-freezes the paper book from the page's calls (dated copy in ledger/book-YYYY-MM-DD.json); then mark_book.py.

### What moved since our review
- `python3 scripts/moves_since.py && python3 scripts/build.py` → data/moves.json; the Brief shows every name that beat or lagged XBI by 15%+ (or had a 15% day beyond XBI) since the snapshot. Research each one (news, 8-K) and patch outcomes before trusting its thesis. Built Nov 25 after KYMR's Nov 23 readout went unnoticed for two days.

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
- 13F holders: now from SEC EDGAR (see Capital below). Investors with < 5% who don't file 13F (most retail, non-US funds) remain unidentified.
- 13D/G parsing: pre-Dec-2024 text filings (SC 13D/G) are read with regexes and can miss the percent; new XML filings (SCHEDULE 13D/G) are exact.
- Oct 2026 frozen ledger (`ledger/2026-10.json`) was not recovered; the Oct memo's printed names stand in for it.
- Insight suggestions and lens scores cover ~65 names.

## December 2026 refresh checklist (from the Nov 23 review)
- Done Nov 25: CAPR (second CRL Nov 20), SVRA (FDA missed Nov 22, no new date), KYMR (BROADEN2 positive Nov 23), HELP (APPROACH positive Nov 16) in pipeline/patches/2026-11-25_*.py. Each refresh: search for readouts and FDA actions between the last snapshot and today before anything else; resolve the other ~60 "past due, verify" catalysts (list: run normalize_catalysts.py and grep st=late).
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

## Theses in three lines (Nov 25 2026; format approved by the PM)
- Each thesis renders as **View** (call + one fact with a number) / **What the market misses** (implied vs our odds or sales, plus the evidence) / **Catalyst & what would change our mind** (dated event + the specific result that flips us). Code: `thesis3()` / `thesis3Html()` in pipeline/template.html.
- Hand-written lines live in `data/theses.json` (th_view, th_miss, th_cat, ceo_notes), merged by ticker at page load so the data refresh never overwrites them. Use tokens, never typed numbers, for anything the market moves: {cap} {cash} {px} {imp} (market-implied odds) {ours} (our PoS) {mktsales} {oursales}. A hand-written th_view also replaces call_reason on the page.
- Without hand-written lines: View = pitch with "$X cap"/"$X cash" (and "N% of the cap") recomputed from today's data; Misses = variantView(); Catalyst = next dated event + a rule-based disconfirming result.
- CEO notes: 0-3, company-specific. Hand-written ceo_notes replace the rule-based ones. Rules no longer append the generic "Investors are asking…" line, compare only programs in the same indication (and only unapproved ones), and no longer suggest unrelated "under-served fields".
- Audit after every batch: `python3 /tmp/t/thaudit.py [TICKERS]` (copy in tests/thaudit.py) counts stale caps, missing misses/catalysts/risks, generic CEO lines and odd phrasing, and prints named companies in full. Batch 1 (40 priority names) done Nov 25; ~360 to go, next batch = remaining STRONG BUY / STRONG SHORT / SHORT, then LONG.
- Call reasons that contradicted their calls (COLL, MLYS, HRMY, CELC, NTLA, ZVRA, XNCR, ARVN, SLS, MLTX, RZLT) were rewritten through th_view; keep call and reason in step when either changes.

## Decision tools added Nov 25 2026
- **What worked, tested:** each group's average quarterly gap, its t-stat, and a pooled regression on all dimensions (synth2 `sig()`, `regress()`). A lesson is 'real' only if |t| ≥ 2.4, ≥ 2%/quarter and it survives the regression. Only the avoid side passes today (Preclinical/Ph1, cell therapy, late entrants). Keep data/backdrop.json calls honest about this.
- **Call scorecard** (scripts/track_record.py → track-data.json `scorecard`): Sep 12 calls by stage, size, modality, novelty, science and model upside vs the universe. Clearest lesson: our sub-$300M longs lost, $1–5B longs won.
- **Expected return to the next catalyst** (Companies › Trading › To catalyst; Brief Q2 ranking): our odds × success/failure moves for the next lead-program readout or FDA decision. **Move: ours vs mkt** compares the size of move we expect with the market's (options straddle when cdn.cboe.com is reachable; otherwise the average of the stock's 5 biggest days vs XBI, which understates binary events). What's next has a filter for events whose move we think the market under-prices.
- **Trading constraints:** ADV, days to build $10M at 20% of volume, 60-day vol (scripts/trade_info.py). Short interest and borrow need cdn.finra.org or a broker feed: blocked; shown as n/a.
- **Paper book** (Record › Paper book): $250M sleeve, 20 longs / ~12 shorts + XBI hedge to +20% net, sized by conviction, volatility and liquidity caps; book catalyst calendar with P&L per event.
- **Raise radar** keys timing off catalyst status: done/late catalysts no longer set the window; a recent CRL or miss gives "after the setback"; recent positive data gives "now"; price moves since the snapshot can open the window.
- cdn.finra.org is allowed (Nov 25): trade_info.py pulls 20 days of Reg SHO short-sale volume (Short vol column; not short interest, whose FINRA files return Access Denied). Options: cdn.cboe.com redirects to **cdn-api.cboe.com**, which must also be allowed before straddle-implied moves replace the historical proxy.

## Nov 25 2026 (evening) additions
- Catalyst hygiene (template, at page load): entries that describe a state (ramp, trajectory, runway, share gains, estimated lock-up, 'delivered'), fragments, and already-reported quarterly results become st:'note' (window.CAT_NOTES lists them, 63 on Nov 25); entries whose text says 'mid-2027' etc. move to that date. Raise windows are no longer listed as dated events. Fix the source text when you see a note that is really an event.
- What's next: 'The catalysts that matter most' panel (Major + clearly skewed, up to 8 positive / 4 negative, ranked by skew strength and swing) and a 'Major and skewed' filter.
- Companies: 'Strongest long in each area' panel + Top 12 overall + '★ Best long per area' filter (bestLongs() in synth.html; score and flags documented there). Trading group shows only ADV collapsed; Short vol column. 'What the market misses' is green/red by direction (thesis3().ms).
- Areas: every stock drawn faintly behind the clusters on both charts.
- Capital › Liquidity: 'Where takeover cash goes' table (break-even recycling, net demand at the ownership-weighted recycling rate). Investors page: filing-rules and copy-the-book explainer.
- Record: Paper book is the last lens; What worked next-quarter column min 440px.

## Net cash and model inputs (Nov 25 2026)
- Equity value now uses net cash (cash − debt; template `netCash()`), in Ours, rNPV/MC, implied odds and the variant text. 20 calls changed (e.g. COLL S.BUY→LONG, CELC S.BUY→LONG, ADCT/STRO/BHC worth ~nothing to equity). Set `debt_excl: true` when the debt belongs to a business the row does not value (BHC).
- COLL peak $3.2B→$1.05B and ACOG $0.96B→$0.15B (pipeline/patches/2026-11-25_valuation_coll.py).
- Batch 2 of the theses (102 remaining STRONG BUY / STRONG SHORT / SHORT names) is in data/theses.json; remaining ~260 LONG / WATCH / HOLD / AVOID names use the computed lines, whose catalyst line now names the real test (the next readout or FDA date within 18 months) and what flips us.

## 13D/13G holders (Nov 25 2026)
- `python3 scripts/fetch_13dg.py` (~25 min; cached 20 days in cache/13dg): for each company, its Schedule 13D/13G filings from the last 30 months via data.sec.gov submissions; one reporting entity per filing (the fund, not its co-filing principals); latest per holder; drops holders whose latest filing is < 5%. → data/13dg.json.
- `python3 scripts/build_13f.py` merges them into own_all: holders matching a 13F filer name are listed only; others count as vc (venture/family office/other entity), insider (individual) or strat (pharma). Stakes older than 18 months are listed but not counted.

## Conviction scores, program values and specialist views (Nov 25 2026, night)
- Companies › Conv. column and the "Strong buys" / "Strong shorts" chips (synth.html `conviction()`, also `window.CONVICTION`). Long score = efficacy and differentiation vs 3/5 (±0.8 a point) + our value (log, ±2) + EV vs the median EV of same-stage peers in the cluster (skipped for approved companies) + peak size + next-event expected return + balance sheet + 0.5 for a 40%+ three-month fall with efficacy ≥ 4/5. No penalty for a drawdown; liquidity and size are not scored. Short score mirrors it, plus runway < 4 quarters, a 75%+ three-month run-up and late entry. Strong buys = top 20 long scores ≥ 6 with efficacy + differentiation ≥ 7 or an approved product; strong shorts = top 20 short scores ≥ 4.5. Hover a score for its parts. The old best-long-per-area panel and the What's next top-catalysts panel are gone (use the "Major and skewed" filter).
- Other programs: `r.programs = [{name, peak, pos, y}]` adds value in valParts beyond the lead (patch 2026-11-25_value_pairs.py: CRVS AD, ZBIO SLE, DNLI Sanfilippo A, IMCR brenetafusp, KYTX gMG/LN). When a pair looks wrong (weaker data, higher value), check first whether the stronger company's second program is unvalued and whether the weaker one's peak came from prevalence rather than its data.
- Inputs revisited: patch 2026-11-25_conviction_inputs.py (UPB efficacy 4; APMD insomnia risk note).
- Specialist coverage: `python3 scripts/spec_coverage.py` scans every filer in cache/13f_bulk/q2 for concentrated biotech holders not on our list (data/spec_coverage.json; shown under Capital › Investors). Rerun after each new bulk 13F download; add real specialists to data/specialists-extra.json and rerun fetch_13f/build_13f.
- Specialist flows by quarter and P&L concentration (Capital › Investors) come from data/13f.json: flows = end book − start book × (1 + book return), per fund; concentration uses the new per-position `pnl4` (dollar P&L over the last four quarters) written by build_13f.py.
- What's next month tables share one colgroup (table-layout fixed) so columns line up across months. What worked: the next-quarter column has 40% of the table width.
- Options-implied moves: cdn-api.cboe.com returns 403 to automated requests; do not work around it. The move column keeps the big-day proxy (h).

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
- Public-target M&A cash (proposal for net supply): tag each M&A deal in the William Blair/BioPharma Dive deal lists as public or private target and cash vs stock, sum cash paid to public holders per quarter (equity value × cash share). Cross-check with our own coverage: names leaving coverage as "acquired" × their last market cap.

## Next-quarter backdrop (What worked › "Next quarter: our call") — every quarter, and check monthly

The calls live in `data/backdrop.json`: `backdrop` (4–6 plain sentences on the market), `calls` (one per What-worked dimension: `favour`, `avoid`, `why`), `sources`. They are judgment, not a formula. The page shows each group's 2025–26 record next to the call.

1. **Gather the evidence** (30 minutes):
   - XBI level and quarter-to-date move; clinical- vs commercial-stage and small- vs large-cap performance (latest William Blair / Jefferies recap, or our quarter-end prices).
   - Rates: last Fed move and what the market expects next.
   - Capital: our Capital › Liquidity page (IPOs, follow-ons, public-target M&A cash, net supply) and the specialist pool trend.
   - The next quarter's catalyst calendar (What's next: Major events by area and stage) and conferences (JPM in January, AACR/AAN in April, ASCO in June, ESMO/EASD in the autumn, ASH in December).
   - Policy: FDA leadership and review behaviour, drug pricing, vaccines, tariffs, China licensing.
   - The What-worked strip: each group's record and its last two quarters.
2. **Write the backdrop**: 4–6 sentences, each a fact with a number, from the evidence above. No predictions in the backdrop itself.
3. **Make the calls**: for each dimension (stage, size, momentum, share price, modality, novelty, area) name the group to favour and the group to avoid, and say why in one or two sentences, quoting the record where it supports the call. A call may go against the record only if the backdrop has changed, and the `why` must say so (e.g. vaccines in 1Q27).
4. **Sanity checks**: every number in a `why` must match the page (record and last quarter); favour and avoid must be different groups; no group is favoured on record alone without a reason from the backdrop.
5. **Monthly refresh**: re-read the calls; if the backdrop has shifted (a rate surprise, a big sell-off, an M&A pause, a policy shock), edit the affected calls and update `written`. At quarter-end, score last quarter's calls (did the favoured group beat the avoided one?) in a line at the top of the backdrop, then write the new quarter.
- Catalyst stakes (after the Nov 25 audit): unapproved lead = market's pipeline value; approved company = 15% of cap for a new indication of the lead, 6% for another program; other programs at unapproved companies = 15% of pipeline value (max 20% of cap). Only lead readouts/FDA decisions can be Major.
- Specialist set = SPECIALIST_INVESTORS + data/specialists-extra.json (biotech-focused filers found in the SEC data set: ≥30% of book and ≥$200M in our names). Re-scan each new data set (see the scan in the Nov 25 session: rank filers by $ in our names and biotech share of book) and add new ones; `watch` lists large generalists to know.
- Net supply uses public-target M&A cash: data/capital-markets.json ma_pub_usd (yearly public share from William Blair's private-target totals; exact where a recap gives the split) × 90% cash.
- Brief › The three questions (synth2.html BRIEF_Q3): built from What worked (WW_SUMMARY + backdrop calls), the priority trades with variant views, Major catalysts with skew (written views first) and the raise model. Each refresh, open Brief and check every answer still reads true.
- Scheduled task "BioStocks monthly refresh" runs on the 14th at 2:40 PM ET with a general prompt covering all of the above.
