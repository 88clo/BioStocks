# Biotech Landscape

A single-file dashboard (`index.html`) covering ~400 US-listed small and mid-cap biotechs (market cap $50M–$30B): the lead program for each company, a quantitative efficacy benchmark, risk-adjusted value vs market cap, a rule-based call, catalysts, cash runway, holders, a monthly memo, and a track record that scores every frozen call set against later prices.

Open `index.html` in a browser. Six pages, each opening on a synthesized view; the original detailed tables sit behind the switch in the top bar.

| Page | Synthesized view (what it answers) | Detail behind the switch |
| --- | --- | --- |
| Brief | What matters this week: best ideas, next 45 days, likely raises, whether calls worked | — |
| Companies | One row per company with a one-line thesis joining valuation, Street target, science, cash, likely raise, specialist ownership and next catalyst; chart of our upside vs the Street's, i.e. where we disagree with consensus | All fields, DCF model, value vs momentum, holders by company, holders by fund, area notes, parked names |
| Areas | Scorecard: one row per therapeutic area joining returns, valuation, science, calls, catalysts in 90 days, expected stock supply and white space; area momentum vs valuation chart. Value gaps: under-served and crowded fields, cash shells, one suggestion per company | Company returns 1M–36M |
| What's next | One timeline of catalysts (with our call, expected direction and the raise likely to follow), open raise windows, IPOs and lock-up expiries; monthly expected equity supply split by whether we would join | Calendar grid, raise and IPO lists, IPO detail |
| Memo & record | Monthly memo; track record of frozen calls, plus the biggest moves joined with what drove them and what we said | Evidence list of the 80 biggest moves with sources |
| Portfolio | My portfolio | — |

Methodology, Refresh status and Print sit under **ⓘ About**; valuation knobs behind **⚙ Model** on the detail tables. Links: `#companies/co`, `#areas/areas`, `#next/next`, `#record/track`, and `#page/lens/detail` for a detail table (e.g. `#companies/co/dcf`). Older links still resolve.

## Backups

`backups/backup-mmddyy-vX.html`, one file per published version:

| File | What it is |
| --- | --- |
| backup-111626-v1.html | Live dashboard before the Nov 22 rebuild (Nov 16 data, original navigation) |
| backup-112226-v1.html | Nov 22 refresh (Nov 20 prices) with the Brief overlay, original navigation |
| backup-112226-v2.html | Nov 22 six-view navigation with 19 lenses, before the merge to twelve |
| backup-112226-v3.html | Nov 22 twelve lenses (merged pages), before the synthesized pages |

## Layout

```
index.html                 built dashboard (do not edit by hand; run scripts/build.py)
pipeline/template.html     page markup, CSS and JS with {{DATA:x}} placeholders
pipeline/brief.html        Brief / Track record / Raise radar / White space pages (injected at build)
pipeline/synth.html        synthesized pages: Companies, Areas, What's next, record join (injected after brief.html)
pipeline/nav.html          the navigation bar (injected last)
pipeline/patches/          hand-verified edits, one dated file per run (reproducible)
pipeline/logs/             refresh change logs and event-check notes with sources
data/*.json                every data block in the page (one file per <script type="application/json">)
ledger/                    frozen call ledgers (page-computed calls, sha256), one per refresh
scripts/                   the pipeline (below)
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
