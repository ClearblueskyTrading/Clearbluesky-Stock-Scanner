# ClearBlueSky v6.3 Release

**Release date:** February 2026

## What's in v6.3

- **Insider scanner** – Fourth scan type: latest insider transactions from Finviz (same source as elite.finviz.com/insidertrading). Config: view (latest, latest buys/sales, top week, top owner trade, etc.).
- **Leveraged play suggestions** – When a stock in the report has a good score and a bull leveraged ETF exists (e.g. MU → MUU), the PDF shows "Leveraged play: MUU" with a short risk disclaimer. Bull only; no bear/inverse. See `app/LEVERAGED_ETFS.md` for reference.
- **5 headlines per ticker** – Each ticker in the PDF now includes up to 5 recent news headlines from Finviz.
- **Reliability** – Retry on Finviz errors (timeout, 429) in report generator, swing scanner, and watchlist scanner. Clearer progress messaging during long scans.
- **Quality** – Watchlist validation (invalid/duplicate symbols); last run summary in the status bar ("Last scan: Trend, 2:45 PM"); "View log" (📋 Logs) opens the error log.

## Release zip

- **File:** `ClearBlueSky-6.3.zip` (in project root).
- **Excluded from zip:** `user_config.json`, `error_log.txt`, `__pycache__/`, contents of `app/reports/` and `app/scans/`.
- Safe to share; no API keys or user data included.

---

*ClearBlueSky v6.3 – made with Claude AI*
