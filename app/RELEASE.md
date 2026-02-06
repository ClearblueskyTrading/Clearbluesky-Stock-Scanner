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
- **Run all scans** – New checkbox runs all six scanners in sequence with 60-second delays to respect API rate limits. Note: may take 20+ minutes.
- **Simplified scanners** – Swing is always emotional-only dips; Watchlist is one scanner with Filter: "Down X% today" or "All tickers".
- **Pre-Market** – Fixed Windows encoding when outside the optimal scan window.

### Scanners (6)

| Scanner | Description |
|---------|-------------|
| **Trend – Long-term** | Uptrending (S&P 500 / Russell 2000 / ETFs). |
| **Swing – Dips** | Emotional-only dips (1–5 days). |
| **Watchlist** | Filter: Down X% today (min % in 1–25%) or All tickers. |
| **Velocity Barbell** | Sector signals → leveraged ideas. |
| **Insider – Latest** | Latest insider transactions (Finviz). |
| **Pre-Market** | Pre-market volume (7–9:25 AM). |

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
