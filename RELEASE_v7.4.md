# ClearBlueSky Stock Scanner v7.4 — Release Notes

**Release date:** 2026-02-08

---

## What's New

### Smart Money Signals
New `smart_money.py` module adds three layers of institutional and social data to your scan reports:

- **WSB/Reddit Sentiment** (all scanners) — Pulls top ~200 trending tickers from apewisdom.io with mention count, upvotes, and 24h trend direction. If a scan candidate is trending on WallStreetBets, the AI knows about it.
- **Institutional 13F Holdings** (Trend scanner) — Identifies notable hedge funds (Berkshire Hathaway, BlackRock, Bridgewater, Citadel, etc.) among top holders and flags whether positions are increasing. Sourced from yfinance.
- **SEC Form 4 Insider Filings** (Trend scanner) — Counts recent insider transactions per ticker via SEC EDGAR full-text search.

All Smart Money data is injected into the AI prompt, JSON report, and text report alongside Market Intelligence. Toggle on/off in Settings (`use_smart_money_signals`).

### Emotional Dip Scanner — Fixed
The Swing – Dips scanner was returning 0 results due to six overly strict filters stacking together. Changes:

| Setting | Old Default | New Default |
|---------|------------|-------------|
| Require Above SMA200 | Yes | No |
| Require Buy Rating | Yes | No |
| Min Relative Volume | 1.8x | 1.2x |
| Min Upside to Target | 10% | 5% |
| Dip Range | 1.5–4% | 1–5% |
| "Unclear" Dip Type | Blocked | Allowed |

The scanner now returns ~30 actionable candidates per run. All settings remain user-adjustable in Settings. Existing configs with old strict values are auto-migrated on startup.

---

## Upgrade Notes

- **From v7.3:** Drop-in replacement. Your `user_config.json` is preserved. Emotional dip settings are automatically migrated to loosened defaults.
- **From earlier versions:** Use in-app Update or download the zip and run `INSTALL.bat`.
- **New dependency:** None (smart_money.py uses `requests`, `yfinance`, and stdlib — all already installed).

---

*ClearBlueSky v7.4 — Made with Claude AI*
