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
