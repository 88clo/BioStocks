# North star: what this dashboard is for

Read this before any refresh or new feature. A change that doesn't help answer one of the questions below can wait.

## The goals

1. **Investing.** The clearest risk-adjusted long and short ideas across about 400 small and mid-cap biotechs, built the same way every month and scored against later prices, so the record is real and keeps improving.
2. **Buy-side healthcare ECM** (Balyasny, Citadel). Know who will raise before the call comes: roughly how much, when, and whether we take part, pass or short into the deal.
3. **Gaps.** Areas with many patients but no strong public drug, crowded areas where the weaker players get consolidated, and companies trading below cash.

One line: *a disciplined, scored biotech process that makes better long/short calls and sees supply coming before the Street does.*

## The three questions we must answer best

The **Brief** page opens with a panel that answers all three from live data; each answer links to the page behind it.

1. **What kind of stocks did best and worst, in which periods, and what did we learn?** → Brief panel (consistent winners and losers, the lesson, next quarter's call) and Record › *What worked, 2025–2026*: each stock grouped as it stood at the start of each quarter, 1/2/4-quarter holds, best and worst group per quarter, top 5 examples plus an exception each way, and a written call for next quarter (data/backdrop.json).
2. **What are our top longs and shorts, and what do we see that the market doesn't?** → Brief panel (top 5 priority longs and shorts with the variant view) and the *Variant view* line in every thesis: the odds (or sales) today's price implies vs ours, and why we differ.
3. **What are the key catalysts and likely raises over 6 months, how do we take part, and what would we tell the CEO?** → Brief panel (Major catalysts with positive and negative skew, likely raises, how we take part), What's next (every catalyst: how much it can move the stock, which way the risk skews, ★ written views), Capital (who owns each stock, specialist flows, issuance vs takeover cash) and the *What I'd tell the CEO* notes on every company card.

## What I'd tell the CEO: the 4 Ms

CEOs are running the company; investors see the whole field, the tape and how holders price the stock. Every note fits one of four Ms:

| M | What investors see that the CEO may not | Examples |
|---|---|---|
| **Money** | When the window is open, how big a raise, who should anchor it, where to cut spend | Raise after a run-up rather than into a binary readout; narrow spend to the lead when cash is short |
| **Message** | The odds or sales the price implies vs the evidence, and the details and analyses investors are asking for | Disclose the numbers and the target bar; dose-response and durability; launch metrics; date the catalysts |
| **Moves** | Pivots, acquisitions and in-licensing, partners, strategic review, positioning against the field leader | Pivot a drug that failed in metastatic disease to the neoadjuvant setting where it worked; acquire a lower-risk, higher-reward asset to replace a failed lead; strategic review below cash |
| **Milestones** | The path to approval and launch that the market will reward | Breakthrough designation and an early end-of-Phase 2 meeting; an FDA-agreed path after a miss; quarterly launch metrics |

## The questions a fund will ask (and where the answer lives)

| # | Question | Where the dashboard answers it today | What's still missing |
|---|---|---|---|
| 1 | What's your edge? | Fixed rubric across ~400 names: efficacy vs a numeric bar, one valuation formula, honest catalyst dates, frozen ledgers (Companies) | — |
| 2 | Show me your track record. | Record page: frozen calls scored vs universe and XBI, what worked each quarter of 2025–26 | **A portfolio, not just calls:** sizing, daily P&L, Sharpe, hit rate, drawdown |
| 3 | How do you size and manage risk? | Inputs only: catalysts, PoS, runway, ours vs Street, catalyst impact | **Paper portfolio** with sizing rules, XBI beta hedge, kill criteria |
| 4 | Your top longs and shorts, and what's priced in? | Brief panel; variant view (market-implied odds vs ours) in every thesis | **Options-implied moves** to check our event sizes |
| 5 | How do you underwrite a binary event? | What's next: impact (value riding on the event), skew (our odds vs typical, valuation, expectations, prior data), ★ written views | **Score each call after the event** (did the skew call work?) |
| 6 | Who raises in the next 90 days, and do we take part? | Raise model (What's next, Brief), Capital › Liquidity (supply vs takeover cash), specialist flows | **Past follow-on database** (discount, warrants, size vs volume, 1/30/90-day returns, lead banks); shelf and ATM capacity |
| 7 | How do you handle inside information from deals? | Process answer only | **Restricted-list / wall-cross flags** per company |
| 8 | How much capital can this run? | Daily volume per name; 13F ownership by type (specialists own ~30% of $300M–5B names) | **Short feasibility:** short interest, borrow cost, days to cover; days to exit at 10–20% of volume |
| 9 | What did you get wrong, and what did you change? | Record page: valuation principles, Sep 12 backtest, frozen model changes; catalyst audit log in the runbook | — |
| 10 | What's your sector view? | Areas drill-down; What worked next-quarter calls with a written backdrop | **Takeover likelihood** and deal comparables |
| 11 | Can I trust the data? | Frozen ledgers, logged input fixes with sources, monthly scheduled refresh, rerunnable repo, SEC 13F data | — |
| 12 | What would you tell management? | What I'd tell the CEO notes (the 4 Ms) on every card | Notes written by hand for the priority names |
| 13 | Who owns these stocks, and where is the crowding? | Capital › Investors: ownership by type for every company (SEC 13F data set), 173 specialist funds' books, holding period, turnover, style, last quarter's buying and selling; holders on every card | **Crowding score** per name (specialist % × number of overlapping top funds) used in sizing |
| 14 | How would you run the ECM book? | Raise model + our participate / price-sensitive / pass view; net supply vs specialist capital | **Deal participation record:** deals we would have joined, allocation, pricing vs our value, returns after; which banks and which funds anchor which deals |
| 15 | What's your portfolio's factor risk? | — | **Factor exposures** of the paper book: XBI beta, size, stage, cash-rich microcap, momentum; correlation clusters (many longs can be one bet) |
| 16 | How do you compare with Baker, RA, Avoro? | Capital leaderboard: 4Q/8Q copy-the-book returns, style vs peers, holding period | Our paper book shown on the same leaderboard |
| 17 | What macro and policy risks matter? | Next-quarter backdrop (rates, M&A, supply, policy) | **Policy tracker:** FDA leadership and review behaviour, drug pricing (MFN/IRA), tariffs, China licensing share of deals |
| 18 | How do you source ideas and run the team? | Process answer; monthly refresh and runbook show the machine | Coverage plan: who covers which areas, conference calendar, expert-network log |

## Build priority (in order)

1. Paper portfolio from the frozen ledger: sizing (catalyst impact and skew, liquidity, crowding), beta hedge, daily P&L vs XBI, Sharpe, hit rate, drawdown; put it on the Capital leaderboard next to the specialist funds (answers 2, 3, 15, 16).
2. Score every catalyst skew call after the event, and calibrate the rules (5).
3. Follow-on deal database and deal participation record (6, 14).
4. Short feasibility and crowding score (8, 13).
5. Takeover-likelihood score and deal comparables (10).
6. Policy tracker and China-licensing share (17).
7. Compliance flags: restricted list and wall-cross log (7).

## How to use this file

- Every refresh: check the "What's still missing" column and move anything newly built into the middle column.
- Every new request: say which question it helps answer.
- Keep the honest version of question 2 current. The record is the first thing a fund will test.

_Set Nov 24 2026. Update the table rather than the goals unless the goals themselves change._
