# GitHub Release – v7.0

Use this as the **Release notes** when creating a new release on GitHub.

---

## Tag

- **Tag name:** `v7.0`
- **Target:** default branch (e.g. `main` or `master`)

---

## Release title

**ClearBlueSky Stock Scanner v7.0**

---

## Description (copy into GitHub release body)

### Highlights

- **Queue-based scans** – Scans run in a background thread so the GUI stays responsive (no more hanging).
- **Run all scans** – New checkbox runs all seven scanners in sequence with 60-second delays to respect API rate limits. Note: may take 20+ minutes.
- **In-app Update & Rollback** – **Update** backs up your version and applies the latest release; **Rollback** restores the previous version. **Your `user_config.json` is never overwritten.** See root **UPDATE.md**. Versioning from v7.0: **7.1, 7.2**, etc.
- **Simplified scanners** – Swing is always emotional-only dips (Index: S&P 500 / Russell / ETFs or **Velocity (high-conviction)**); Watchlist is one scanner with Filter: "Down X% today" or "All tickers".
- **Velocity Pre-Market Hunter** – New scan type: pre-market setups (gap recovery, accumulation, breakout, gap-and-go) with grades A+–F. Index: S&P 500 / Russell / ETFs (not ticker-restricted) or Velocity universe.
- **Pre-Market** – Fixed Windows encoding when outside the optimal scan window.

### Scanners (7)

| Scanner | Description |
|---------|-------------|
| **Trend – Long-term** | Uptrending (S&P 500 / Russell 2000 / ETFs). |
| **Swing – Dips** | Emotional-only dips (1–5 days). Index: S&P 500 / Russell / ETFs / Velocity (high-conviction). |
| **Watchlist** | Filter: Down X% today (min % in 1–25%) or All tickers. |
| **Velocity Barbell** | Sector signals → leveraged ideas. |
| **Insider – Latest** | Latest insider transactions (Finviz). |
| **Pre-Market** | Pre-market volume (7–9:25 AM). |
| **Velocity Pre-Market Hunter** | Pre-market setups (gap recovery, accumulation, breakout, gap-and-go); grades A+–F. Index: S&P 500 / Russell / ETFs or Velocity universe. |

### Requirements

- Windows 10/11, or Linux/macOS with Python 3.10+ and tkinter.
- Internet connection. No API key required for scanners; optional keys for OpenRouter, Finviz, Alpha Vantage.

### Full changelog

See [CHANGELOG.md](CHANGELOG.md) in the `app` folder.

---

## Pre-release checklist

- [ ] Version set to `7.0` in `app/app.py` (VERSION, header, help text).
- [ ] README.md and CHANGELOG.md updated.
- [ ] Tag `v7.0` created and pushed.
- [ ] GitHub Release created with title and description above.
- [ ] Optional: attach a zip of the `app` folder (or built executable) as release asset.

---

## Next release (planned)

- **No duplicates in watchlist** – Ensure watchlist (config + UI) stores and displays each ticker only once (dedupe on add/import/save).
- **No duplicates in reports** – Ensure scan results and report output contain no duplicate tickers (dedupe before generating report / writing PDF).
- **Executive summary when all 3 files go to AI** – When all 3 report files (PDF, JSON, _ai.txt) are sent to an AI, the output should include a clear executive summary of all the info—not just what trades to make. Explain context, market/sector backdrop, scan rationale, and key findings in plain language; then include trade recommendations.
