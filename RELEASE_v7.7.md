# ClearBlueSky Stock Scanner v7.7 — Feature Release

## What's New

**Scanner Consolidation (7 → 4)**
- Removed standalone Velocity Barbell, Insider, and Velocity Pre-Market Hunter scanners
- Pre-Market now combines volume scan + velocity gap analysis in one pass
- Insider data folded into Trend and Swing scans as enrichment (not a standalone scan)
- Leveraged ETF suggestions added to Swing and Pre-Market reports (no separate Barbell scan needed)
- "Run all scans" now runs 4 scanners (~15 min vs ~25 min)

**Ticker Enrichment**
- **Earnings date warnings** — per-ticker flags like "EARNINGS TOMORROW", "EARNINGS THIS WEEK" so the AI avoids risky entries before earnings
- **News sentiment flags** — DANGER / NEGATIVE / POSITIVE / NEUTRAL per ticker from recent headlines
- **Live price at report time** — stamped on each ticker so the AI has real-time reference
- **Leveraged ETF suggestions** — on Swing & Pre-Market scans, matching leveraged tickers (e.g., TQQQ for QQQ) are suggested

**Overnight / Overseas Markets**
- 9 international ETFs tracked: Japan (EWJ), China (FXI), Brazil (EWZ), Europe (EFA), Germany (EWG), UK (EWU), India (INDA), Taiwan (EWT), South Korea (EWY)
- Data injected into AI prompt as "OVERNIGHT / OVERSEAS MARKETS" context
- Critical for Pre-Market and Swing scanners — identifies gap-down risk or dip-buying opportunities from overseas sessions

**Insider Data Integration**
- SEC Form 4 insider buys/sales now fetched for Trend and Swing scan tickers
- Attached to per-ticker data in reports and AI prompt
- AI uses insider activity as confirmation signal (heavy insider buying = bullish)

**Trend Scanner Reweighted for Long-Term**
- Yearly/YTD performance: 10 → 30 points (heaviest weight)
- Quarter performance: 25 points (sector rotation signal)
- Month: 20 → 15 points
- Week: 10 → 5 points
- Today's change: 10 → 5 points
- Now prioritizes stocks with sustained multi-month sector momentum over short-term pops

**AI Prompt Improvements**
- Top picks increased from 3 to minimum 5 (ranked by conviction)
- New required section: "OVERNIGHT / OVERSEAS IMPACT"
- New required section: "NEWS & EARNINGS ALERTS"
- Critical Data references: earnings warnings, news sentiment, overnight markets, price at report time
- Insider activity section included when data available

**Russell 2000 Removed**
- Removed from all scanner index dropdowns, CLI, and docs
- S&P 500 and ETFs are the only index options (smaller, higher-quality universe)

## Upgrade Notes

Drop-in replacement for v7.6. No config changes needed — existing `user_config.json` is preserved. Old scanner config keys (velocity_leveraged, insider, velocity_premarket) are silently ignored.
