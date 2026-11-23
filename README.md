# Biotech Landscape

A single-file dashboard (`index.html`) covering ~400 US-listed small and mid-cap biotechs (market cap $50M–$30B): the lead program for each company, a quantitative efficacy benchmark, risk-adjusted value vs market cap, a rule-based call, catalysts, cash runway, holders, a monthly memo, and a track record that scores every frozen call set against later prices.

Open `index.html` in a browser. Five pages, no sub-views; any ticker anywhere opens the **company card**, which is where you dive in.

| Page | What it answers | How |
| --- | --- | --- |
| Brief | What matters now | Best ideas, next 45 days, likely raises, whether calls worked. Switch to past monthly memos (Nov, Oct) in the top bar |
| Companies | Every company, every field, one table | Default columns + one-line thesis (valuation, Street, science, cash, raise, specialists, catalyst). Column groups: +Science, +Market model, +Financials, +Returns, +Ownership. Chips: Long/Short, Quality, Big disagreements, Likely raise, Below cash, Value-raising action, My portfolio, Include parked. Search a fund name to see its holdings. Chart: our upside vs Street upside, 12M or 3M return |
| Areas | Where to spend time | One row per therapeutic area (returns, valuation, science, calls, catalysts, supply, white space); click an area for its indication groups (players, best asset, prevalence, under-served/crowded, below-cash names, suggested actions); click a group to open those companies |
| What's next | What happens when, and what it costs | Monthly equity-supply chart, one timeline of catalysts (call, expected direction, follow-on raise), raise windows, IPOs and lock-ups, then the IPO market table |
| Record | Does it work | Scored frozen calls, factor attribution, the biggest moves joined with drivers and our calls |

**Company card:** Summary (call, our vs Street upside, one-line thesis, wrong-if, likely raise) · asset pipeline and commercial model · Valuation (DCF numbers and sales/cost curve) · efficacy vs benchmark · thesis, value driver, suggestion · catalysts and schedule · Catalysts & financing next 6 months · press releases · risks · ownership (top holders) · financials · regulatory · Our call history (every frozen call with price then and since) · price performance.

**ⓘ About** holds Methodology, Refresh status, Print, and **Full data tables**: every original table (all fields, DCF model and assumptions, value vs momentum, holders by company and by fund, company returns, calendar grid, raise and IPO lists, IPO detail, value-gaps lists, area notes, parked, portfolio editor, return tiles), so nothing the pages summarize is out of reach. Old links (`#companies/dcf`, `#deals/radar`, …) still resolve; `#legacy/<table>` opens a full table directly.

## Backups

`backups/backup-mmddyy-vX.html`, one file per published version:

| File | What it is |
| --- | --- |
| backup-111626-v1.html | Live dashboard before the Nov 22 rebuild (Nov 16 data, original navigation) |
| backup-112226-v1.html | Nov 22 refresh (Nov 20 prices) with the Brief overlay, original navigation |
| backup-112226-v2.html | Nov 22 six-view navigation with 19 lenses, before the merge to twelve |
| backup-112226-v3.html | Nov 22 twelve lenses (merged pages), before the synthesized pages |
| backup-112226-v4.html | Nov 22 synthesized pages with detail switches, before the five-page version |

## Layout

```
index.html                 built dashboard (do not edit by hand; run scripts/build.py)
pipeline/template.html     page markup, CSS and JS with {{DATA:x}} placeholders
pipeline/brief.html        Brief / Track record / Raise radar / White space pages (injected at build)
pipeline/synth.html        Companies table, Areas drill-down, What's next, record join, company-card additions (injected after brief.html)
pipeline/nav.html          the navigation bar (injected last)
pipeline/patches/          hand-verified edits, one dated file per run (reproducible)
pipeline/logs/             refresh change logs and event-check notes with sources
data/*.json                every data block in the page (one file per <script type="application/json">)
ledger/                    frozen call ledgers (page-computed calls, sha256), one per refresh
scripts/                   the pipeline (below); call_history.py builds the card's call history from ledgers
biotech_idea_snapshot.html Sep 12 2026 snapshot (from the old Biotech-stock-ideas repo), kept as the earliest call set for the track record
```

## Monthly refresh (runbook)

See `pipeline/RUNBOOK.md`. Short version:

```bash
python3 scripts/extract.py path/to/latest.html  # only if the HTML was edited/saved outside the repo
python3 scripts/snapshot_calls.py ledger/YYYY-MM-DD_before-refresh.json   # freeze calls before touching data
python3 scripts/fetch_prices.py                 # ~15 s, Yahoo daily history for every ticker
python3 scripts/fetch_fundamentals.py           # ~10 s, quarterly cash / debt / shares / cash flow
python3 scripts/refresh_apply.py                # prices, caps, returns, ADV, quarterly history, newer balance sheets
#   -> research the movers it prints; write pipeline/patches/YYYY-MM-DD_events.py; run it
python3 scripts/update_status.py                # refresh-status table, as-of stamps, header tape (edit dates at top)
python3 scripts/build.py
python3 scripts/snapshot_calls.py ledger/YYYY-MM-DD_refresh.json          # freeze the new calls
python3 scripts/track_record.py && python3 scripts/radar_gaps.py && python3 scripts/build.py
```

Requirements: Python 3.10+, `playwright` with a Chromium/Chrome binary (for `snapshot_calls.py`, which lets the page's own rules compute calls so nothing is re-implemented in Python).

## Method in one paragraph

Each company is valued on its lead program: probability-adjusted peak sales × a takeout P/S multiple, discounted by years to approval, plus cash (fNPV). Market cap ÷ fNPV gives a valuation band; the mean of efficacy-signal and differentiation scores (1–5) gives a science band; the grid of the two gives the call (Strong Buy … Strong Short; weak science is Avoid however cheap). Top picks add gates on upside, peak sales, PoS, runway, size and both scores. The Methodology button in the page has the full grid. The Track record tab shows how those calls have done so far, including where they have not worked.
