# North star: what this dashboard is for

Read this before any refresh or new feature. A change that doesn't help answer one of the questions below can wait.

## The goals

1. **Investing.** The clearest risk-adjusted long and short ideas across about 400 small and mid-cap biotechs, built the same way every month and scored against later prices, so the record is real and keeps improving.
2. **Buy-side healthcare ECM** (Balyasny, Citadel). Know who will raise before the call comes: roughly how much, when, and whether we take part, pass or short into the deal.
3. **Gaps.** Areas with many patients but no strong public drug, crowded areas where the weaker players get consolidated, and companies trading below cash.

One line: *a disciplined, scored biotech process that makes better long/short calls and sees supply coming before the Street does.*

## The questions a fund will ask (and where the answer lives)

| # | Question | Where the dashboard answers it today | What's still missing |
|---|---|---|---|
| 1 | What's your edge? | Fixed rubric across ~400 names: efficacy vs a numeric bar, one valuation formula, honest catalyst dates, frozen ledgers (Companies) | — |
| 2 | Show me your track record. | Record page: frozen calls scored vs universe and XBI, including what failed and what changed | **A portfolio, not just calls:** sizing, daily P&L, Sharpe, hit rate, drawdown |
| 3 | How do you size and manage risk? | Inputs only: catalysts, PoS, runway, ours vs Street | **Paper portfolio** with sizing rules, XBI beta hedge, kill criteria |
| 4 | Your top longs and shorts, and what's priced in? | What's next priority rows; ours vs Street | **Options-implied moves** and expected value per catalyst |
| 5 | How do you underwrite a binary event? | PoS, efficacy bar, Street gap, runway past the event | **Event trees** (up/down move × probability) scored after each readout |
| 6 | Who raises in the next 90 days, and do we take part? | Raise model on What's next: size, month, our view | **Past follow-on database** (discount, warrants, size vs volume, 1/30/90-day returns, lead banks); shelf and ATM capacity |
| 7 | How do you handle inside information from deals? | Process answer only | **Restricted-list / wall-cross flags** per company |
| 8 | How much capital can this run? | — | **Liquidity and short feasibility:** daily volume, days to exit, short interest, borrow cost, crowding |
| 9 | What did you get wrong, and what did you change? | Record page: valuation principles, Sep 12 backtest, separately frozen model change | — |
| 10 | What's your sector view? | Areas: cluster › area › indication › company drill-down, cheap/lagging map, crowded vs under-served | **Takeover likelihood** and deal comparables |
| 11 | Can I trust the data? | Frozen ledgers, logged input fixes with sources, scheduled refresh, rerunnable repo | — |

## Build priority (in order)

1. Paper portfolio from the frozen ledger: sizing, beta hedge, daily P&L vs XBI, Sharpe, hit rate, drawdown (answers 2, 3, 8).
2. Catalyst event trees with options-implied moves, scored after each event (4, 5).
3. Follow-on deal database plus shelf/ATM capacity (6).
4. Liquidity and short feasibility (8).
5. Takeover-likelihood score and deal comparables (10).
6. Compliance flags: restricted list and wall-cross log (7).

## How to use this file

- Every refresh: check the "What's still missing" column and move anything newly built into the middle column.
- Every new request: say which question it helps answer.
- Keep the honest version of question 2 current. The record is the first thing a fund will test.

_Set Nov 24 2026. Update the table rather than the goals unless the goals themselves change._
