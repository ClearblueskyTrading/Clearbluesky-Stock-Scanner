# Strategy B Long/Short Backtest — 2026-02-13

## Per Trader Two's discussion: bull top + bear worst simultaneously

---

## Full Comparison (5-day cycle, 780 days)

| Strategy | Cumulative | Final $ | Win Rate | Max Drawdown |
|----------|------------|---------|----------|--------------|
| **A: 1 pos bull only** | +540.5% | $64,045 | 57.8% | **28.9%** |
| B: 2 pos (60/40 top two) | +282.4% | $38,238 | 59.6% | 28.1% |
| B: 2 pos + bear when neg | +169.8% | $26,980 | 58.4% | **47.5%** ⚠️ |
| C: PAIR 50/50 bull+bear | +26.9% | $12,690 | 53.4% | 27.4% |
| **C: PAIR 60/40 bull+bear** | +82.2% | $18,223 | 55.9% | **19.9%** ✓ |

---

## Findings

1. **Max drawdown now tracked** — A = 28.9%, pair 60/40 = 19.9% (lowest).
2. **Bear leg wins 39.1%** — Below 50%, so it’s a net drag. Upward bias means shorting laggards often loses.
3. **2 pos + bear when negative** — Worst DD (47.5%). Switching to inverse when sectors go negative adds whipsaw.
4. **Pair 60/40** — Best risk-adjusted profile: +82% with ~20% DD vs +540% with ~29% DD for A.
5. **Pair 50/50** — Weak: +27% return; bear leg drag is too large.
6. **Bull-only remains best for raw return** — 540% but with ~29% DD.

---

## Sector Selection Methodology

- **Lookback:** 5 trading days.
- **Ranking:** Sector ETFs by trailing 5d return, best to worst.
- **Bull leg:** 3x bull ETF of #1 sector (or sector ETF if no 3x).
- **Bear leg:** 3x bear ETF of #11 sector (or SPXU if no sector inverse).
- **Entry:** Monday (cycle start); **exit:** Friday (cycle end).
- **Data:** yfinance; no slippage/spread modeling.

---

## Recommendation for Live Capital

- **Gun capital ($5–7K):** Run Strategy A or pair 60/40 in parallel with individual stock swings.
- **Risk tolerance:** ~29% DD for A; ~20% DD for pair 60/40.
- **Bear leg:** In this 780d window, bear leg hurts more than it helps; pair benefit comes mainly from diversification, not the bear leg itself.
- **Avoid:** “Bear when negative” mode — highest DD and lower returns.
