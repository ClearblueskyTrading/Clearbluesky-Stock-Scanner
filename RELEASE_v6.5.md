# ClearBlueSky Stock Scanner v6.5

**Release date:** February 2026

---

## What's New in v6.5

### New Scanners

- **Watchlist 3pm** – Renamed from "Watchlist – Near open." Scans your watchlist for tickers **down X% today** (slider **1–25%**). Best run around 3 PM. Config: **% down (1–25%)** slider.
- **Watchlist – All tickers** – Scans **all** watchlist tickers with **no filters**. One-click snapshot of every ticker on your list. No parameters.
- **Velocity Barbell** – **Foundation + Runner** (or **Single Shot**) strategy from sector signals. Uses sector proxy ETFs (QQQ, SMH, SPY, etc.) to see what’s leading, then recommends:
  - **Barbell:** Foundation ticker ($5K) + **Runner Candidate 1** (score 90, with RSI/leverage) + **Runner Candidate 2** (score 95). Pick runners by oversold, catalysts, or technicals.
  - **Single Shot:** One ticker ($10K) when theme is clear.
  - Config: **Min sector % (up or down)** slider (-5 to +5), **Theme** (auto / barbell / single_shot).

### Improvements

- **AI analysis fallback** – If OpenRouter fails or returns empty, the app still writes a **fallback _ai.txt** with the error and the full instructions so you can paste them into another AI. Status bar shows a short error; a warning dialog points you to the log and _ai.txt.
- **Install / update** – INSTALL.bat now copies app **contents** into the install folder (so `app.py` and `requirements.txt` are at the root) and uses **`pip install --upgrade`** so reruns upgrade dependencies.
- **Update pop-up** – "Later" button no longer closed the dialog immediately; closure bug in the update notice lambda fixed.

### Index: ETFs

- **ETFs** – The index dropdown (S&P 500 / Russell 2000) now includes **ETFs**. When you select **ETFs**, all index-based scanners (Trend, Swing – Dips, Emotional Dip, Pre-Market) and report market breadth use the **Finviz Exchange Traded Fund** universe.

### CLI for Claude / automation

- **Command-line scanner** – Run scans without the GUI: `python scanner_cli.py --scan <type> [--index sp500|russell2000|etfs] [--watchlist-file PATH]`. Scan types: trend, swing, velocity, premarket, emotional_dip, insider, watchlist, watchlist_tickers. Exit 0 on success, 1 on failure; output uses `[OK]` / `[FAIL]` (no emoji) so it works on Windows console. See **app/CLI_FOR_CLAUDE.md** for full usage.

### Reports – SMA200 status

- **Per-stock SMA200 status** – Reports now show **SMA200 status** (Above / Below / At / N/A) for each ticker. SMA50 and SMA200 no longer show "null"; missing values display as N/A. Status is derived from TA (price vs SMA200) or from Finviz when available.

### Docs & Help

- **In-app Help (❓)** – Updated for Watchlist 3pm, Watchlist – All tickers, Velocity Barbell, ETFs index, and CLI. N/A index note for Velocity Barbell and watchlist scans.
- **README / README.txt** – Version 6.5, full scanner list, CLI, and quick start updated.

---

## Outputs (unchanged)

| File | Contents |
|------|----------|
| `*_Scan_*.pdf` | Report with Master Trading Report Directive + per-ticker data. |
| `*_Scan_*.json` | Same data + `instructions` for any AI. |
| `*_Scan_*_ai.txt` | AI analysis (OpenRouter), or fallback with error + instructions if the API fails. |

---

## Scanners in v6.5

| Scanner | Description |
|---------|-------------|
| **Trend** | Uptrending (S&P 500 / Russell 2000 / ETFs). Best: after close. |
| **Swing – Dips** | Oversold dips with news/analyst (S&P 500 / Russell 2000 / ETFs). Best: 2:30–4:00 PM. |
| **Watchlist 3pm** | Watchlist tickers down X% today (slider 1–25%). Best: ~3 PM. |
| **Watchlist – All tickers** | All watchlist tickers, no filters. |
| **Velocity Barbell** | Foundation + Runner (or Single Shot) from sector signals. Config: min sector %, theme. |
| **Insider** | Latest insider transactions (Finviz). |
| **Emotional Dip** | Late-day dip setup (S&P 500 / Russell 2000 / ETFs). Best: ~3:30 PM. |
| **Pre-Market** | Pre-market volume (S&P 500 / Russell 2000 / ETFs). Best: 7–9:25 AM. |

---

## Upgrade from v6.4

1. Replace the `app` folder (or re-run **INSTALL.bat** and choose your existing install path).
2. Your **user_config.json**, **scan_types.json**, and **reports** are preserved. If you use custom scan types, add **Watchlist 3pm**, **Watchlist – All tickers**, and **Velocity Barbell** from the Scan dropdown or from **scan_types.json** (see repo).
3. **Velocity Barbell** uses **velocity_leveraged_arsenal.json** and **velocity_leveraged_scanner.py** in `app/`. No extra setup.

---

## CLI (optional)

- From the app folder: `python scanner_cli.py --scan velocity` (or trend, swing, premarket, emotional_dip, insider, watchlist, watchlist_tickers). Use `--index etfs` for ETF universe where applicable. See **app/CLI_FOR_CLAUDE.md** for automation and Claude.

## Release package

- **File:** `ClearBlueSky-6.5.zip` (or tag `v6.5` on GitHub).
- **Excluded from zip:** `user_config.json`, `error_log.txt`, `__pycache__/`, contents of `app/reports/` and `app/rag_store/`.
- **No APIs or user data:** No API keys or user config are saved in the repo or the release. `user_config.json` is gitignored and is not copied during install; the app creates a blank config (all API keys empty) on first run. Optional: `app/user_config.json.example` is a blank template (safe to commit).
- Safe to share; no API keys or user data included.

---

*ClearBlueSky v6.5 – made with Claude AI*
