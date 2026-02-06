# Changelog

All notable changes to ClearBlueSky Stock Scanner are documented here.

---

## [6.5] – February 2026

### Added
- **CLI for Claude / automation** – `scanner_cli.py` runs scans from the command line (no GUI). Use for automation or with tools like Desktop Commander. Exit 0 on success, 1 on failure; `[OK]` / `[FAIL]` output. See **app/CLI_FOR_CLAUDE.md** for usage.
- **ETFs index** – Index dropdown now includes **ETFs** (Finviz “Exchange Traded Fund” universe). Trend, Swing (Emotional Dip), Pre-Market, and report breadth all support ETFs when “ETFs” is selected.
- **Watchlist 3pm** – Scan watchlist tickers down X% today (slider 1–25%). Best run ~3 PM.
- **Watchlist – All tickers** – Scan all watchlist tickers with no filters.
- **Velocity Barbell** – Foundation + Runner (or Single Shot) from sector signals. Config: min sector % (up or down), theme (auto / barbell / single_shot). Runner Candidate 1 & 2 with RSI/leverage.
- **AI fallback _ai.txt** – If OpenRouter fails or returns empty, app still writes a fallback _ai.txt with error and instructions.
- **user_config.json.example** – Blank template (no API keys); safe to commit.

### Changed
- **Reports – SMA200 status** – Per-stock **SMA200 status** (Above / Below / At / N/A) is now shown in PDF, JSON, and text. SMA50/SMA200 no longer show "null"; missing values display as N/A.
- **Watchlist – Near open** renamed to **Watchlist 3pm**; slider label **% down (1–25%)**.
- **Install** – INSTALL.bat copies app contents to install root; removes any existing `user_config.json` so install starts with blank config; pip uses `--upgrade`.
- **Report min score** – Watchlist 3pm, Watchlist – All tickers, Velocity Barbell, Insider use min_score 0.
- **Update pop-up** – “Later” button and lambda closure fixed.

### Docs
- README, README.txt, RELEASE_v6.5.md, **app/CLI_FOR_CLAUDE.md** (CLI usage for Claude/automation), SCANNER_CONFIG_PARAMETERS.md (Watchlist, Velocity Barbell), GITHUB_PUSH.md (v6.5), CHANGELOG.md. No API keys or user config in repo or release.

---

## [6.4] – February 2026

- JSON analysis package with `instructions` for any AI.
- OpenRouter AI integration, RAG books, TA in report, Alpha Vantage sentiment, SEC insider context, vision charts, backtest feedback loop.
- Help and docs updated.

---

*ClearBlueSky – made with Claude AI*
