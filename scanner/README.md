# ClearBlueSky Stock Scanner v8.0

See the main **[README.md](../README.md)** in the project root for full documentation.

## Quick Reference

- **3 Scanners:** Velocity Trend Growth (momentum), Swing (emotional dips), Watchlist
- **Universe:** S&P 500 or ETFs (toggle in GUI; `--index sp500|etfs` in CLI)
- **Run:** `python app.py` (GUI) or `python scanner_cli.py --scan <type>` (CLI) or `CLI.bat --scan <type>` (Windows)
- **AI:** 6-model consensus (OpenRouter) + optional Google; chart data in JSON. Free models only.
- **Sentiment:** Alpha Vantage + FinBERT (local) for rolling 1h/4h/1d scores and spike alerts.

See **CLI_FOR_AI.md** for CLI/AI automation.
