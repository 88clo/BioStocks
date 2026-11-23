# Monthly refresh runbook

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
`update_status.py` (edit the `ASOF`/`RUN` dates at the top), `build.py`, `snapshot_calls.py ledger/<date>_refresh.json`, `track_record.py`, `radar_gaps.py`, `call_history.py`, `build.py`.

Also record each catalyst's date as it stands at the refresh (the ledger keeps `cat_date`), so the track record can later tell whether a big move was on the calendar beforehand.

## 5. Check
Open `index.html` headless (`snapshot_calls.py` prints page errors) and click through Brief, Track record, Raise radar, White space, Full table, TA summary and Monthly memo. Spot-check five prices against a quote page.

## Known gaps
- 13F holders: no reachable source from the workspace shell; lists date from Sep 13.
- Oct 2026 frozen ledger (`ledger/2026-10.json`) was not recovered; the Oct memo's printed names stand in for it.
- Insight suggestions and lens scores cover ~65 names.
