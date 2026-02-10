# Market Strategy — ClearBlueSky Scanner (DRAFT)
**Discuss before committing. Do not save to velocity_memory until approved.**

---

## 1. Timing & Hold Period

| Phase | Time (ET) | Action |
|-------|-----------|--------|
| **Scan** | 2:45–3:15 PM | Run scanners; review PDF + AI picks |
| **Entry** | 3:00–3:45 PM | Enter positions (final hour) |
| **Hold** | Overnight | Max 24 hours |
| **Exit** | Next day 9:30 AM–12:00 PM | Take profit or stop |

**Target per trade:** +1.5% to +3%.  
**Rationale:** Overnight institutional flow, morning gap, T+1 alignment, minimal tick-watching.

---

## 2. Capital (from Feb 6)

- **Portfolio:** ~$19,400 (Schwab).
- **Tier 1 — Active swing (50% max):** $9,700 → 2 positions, $3,500–5,000 each.
- **Tier 2 — Strategic long-term (30%):** Not for scanner trades (LRCX, APH, NVDA, GEV, AMAT, metals).
- **Tier 3 — Cash (20%):** Buffer + A++ opportunities.

**Bear market (current regime):**
- Position size: **$3,500** (not $5,000).
- Max **2** positions.
- Stops: **1.5–2.5%** (not 3%).
- Cash reserve: **50%** (not 30%).

---

## 3. How Each Scanner Feeds the Strategy

### Trend (Long-term)
- **What it does:** Scores S&P 500 / ETFs by YTD, quarter, month, relative volume; above MAs.
- **Strategy use:** Sector rotation context and **long-term watchlist**. Names that appear here can be candidates for **Signal C (sector laggard)** or for Tier 2 adds — not for same-day 3 PM entries unless they also show up in Swing/Watchlist with a 3 PM setup.
- **When to run:** Weekly or when you want a refreshed sector/trend view. Not required daily for 3 PM entries.

### Swing (Dips)
- **What it does:** Finds names down 1–5% (configurable), filters emotional vs fundamental dips, scores upside to target, RSI, analyst rating.
- **Strategy use:** Primary source for **Signal D (reversal hammer / emotional dip)** and dip-buys into the close. Run by **2:45–3:15 PM**; use report + AI to pick 1–2 that fit: recovered from intraday low, support held, no earnings tomorrow.
- **When to run:** Daily, 2:45–3:15 PM.

### Watchlist
- **What it does:** Scores your curated list (change %, relative volume, RSI, SMA200, analyst, upside).
- **Strategy use:** Your universe for **Signals A, B, C, D**. Run same window as Swing; filter AI picks to names that match one of the four 3 PM patterns (EOD ramp, bull flag, sector laggard, reversal hammer).
- **When to run:** Daily, 2:45–3:15 PM.

### Pre-Market
- **What it does:** Unusual pre-market volume, gap %, float, sector heat (7–9:25 AM).
- **Strategy use:** Different time window. Use for (a) **next-day context** (which sectors/gaps to watch at open), or (b) a **separate morning strategy** (e.g. gap-and-go with same-day exit). Not part of the core 3 PM → next-day exit flow unless we explicitly add a “pre-market watchlist for 3 PM” step.
- **When to run:** 7:00–9:25 AM if you want morning bias; optional for the 3 PM strategy.

---

## 4. The Four 3 PM Signals (Quick Reference)

| Signal | Scanner that feeds it | Example |
|--------|------------------------|--------|
| **A: EOD Ramp** | Watchlist, Trend (context) | +1.5–4% day, new high last 2h, volume >1.5x, RSI 55–70 |
| **B: Bull flag into close** | Watchlist | Morning spike +3–6%, pullback to +1.5–2.5% by 3 PM, hold VWAP |
| **C: Sector laggard** | Trend + Watchlist | Sector up 4–7%, name up 0.5–1.5%, strong fundamentals |
| **D: Reversal hammer** | **Swing (Dips)** | Was -3 to -5%, recovered to -0.5% to +1% by 3 PM, emotional only |

---

## 5. Daily Workflow (Scanner → Trade)

1. **2:45–3:15 PM:** Run **Swing** and **Watchlist** (and optionally Trend if you want sector context).
2. **Review:** Open latest PDF + AI section; note earnings warnings and overnight/overseas impact from report.
3. **Filter:** Keep only names that match one of the four signals and pass AI “AVOID” / earnings filters.
4. **Size:** 1–2 positions, $3,500 each (bear regime).
5. **Entry:** 3:00–3:45 PM; set stop 1.5–2.5% below entry.
6. **Exit:** Next day 9:30 AM–12:00 PM; target +1.5–3% or stop.

---

## 6. Regime Overlay

- **Current (Feb 6):** Bear with sector rotation. Semis/industrials leading; big tech lagging. Trade exceptions, not the rule; expect 50–60% win rate; tighter stops, more cash.
- **When regime improves:** Breadth >10% above 50 SMA → consider loosening slightly; >50% → bull confirmation, can revisit position size and stop width (per your breadth milestones in `current_regime.md`).

---

## 7. What We Can Change Before Committing

- **Pre-Market:** Keep as “separate / context only” or fold into a single “daily scan sequence” with a defined role.
- **Trend:** Explicitly “weekly only” or “daily for sector context”?
- **Signal definitions:** Any tweaks to A/B/C/D criteria to match how you actually click the button?
- **Where to save:** Once approved: `velocity_memory/strategy_updates/` and/or `docs/strategy/` (and add to RAG index).

---

*Draft — discuss and edit before committing.*
