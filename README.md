# ClearBlueSky Stock Scanner v7.82

**Free desktop app** that scans the market for trading ideas and generates **PDF + JSON reports** you can use with any AI (in-app via OpenRouter or paste JSON elsewhere).

- **4 Scanners** – Trend (long-term sector rotation), Swing (emotional dips), Watchlist (Down X% or All), Pre-Market (combined volume + velocity gap analysis) — S&P 500 / ETFs universe
- **Ticker Enrichment** – Earnings date warnings, news sentiment flags (DANGER/NEGATIVE/POSITIVE), live price at report time, leveraged ETF suggestions on Swing & Pre-Market
- **Overnight/Overseas Markets** – Japan, China, Brazil, Europe, India, Taiwan, South Korea ETFs tracked and fed to AI context
- **Insider Data** – SEC Form 4 insider filings folded into Trend & Swing reports (not a standalone scanner)
- **Market Intelligence** – Google News RSS headlines, Finviz news, sector performance, and market snapshot (SPY, QQQ, VIX, etc.) automatically gathered and fed to the AI
- **Smart Money Signals** – WSB/Reddit sentiment (all scanners), institutional 13F holders (Trend scanner) fed to AI for confirmation
- **Run all scans** – Optional checkbox runs all four scanners in sequence (rate-limited; ~15 minutes)
- **CLI** – Run scans from the command line for automation: `python app/scanner_cli.py --scan <type>`. See **app/CLI_FOR_CLAUDE.md**.
- **Watchlist** – 2 beeps + WATCHLIST when a watchlist ticker appears in any scan
- **Outputs** – PDF report (with per-stock SMA200 status), JSON analysis package (with `instructions` for AI), and optional `*_ai.txt` from OpenRouter
- **Optional AI pipeline** – OpenRouter API key → AI analysis saved as `*_ai.txt`; optional RAG (.txt/.pdf books), TA, sentiment, SEC insider context, chart images
- **In-app Update & Rollback** – **Update** backs up your version and applies the latest release from GitHub; **Rollback** restores the previous version. **Your `user_config.json` is never overwritten.** See **UPDATE.md**.
- **Update notice** – On startup, checks for a newer version and shows a link to download

No API key required for the scanners. Optional keys in **Settings**: Finviz, OpenRouter, Alpha Vantage (all stored only in local `user_config.json`). **Releases and the repo never include API keys or user config** – `user_config.json` is gitignored and is not copied on install; the app creates a blank config on first run.

---

## Quick start (Windows)

1. **Install** – Run `INSTALL.bat` (installs Python and dependencies if needed).
2. **Run** – Use the Desktop shortcut or run `app/START.bat` (or `python app/app.py` from `app/`).
3. **Scan** – Choose scan type and index (S&P 500 / ETFs); click **Run Scan**. Optional: check **Run all scans** (rate-limited).
4. **Report** – PDF + JSON open when done (reports show per-stock SMA200 status: Above/Below/At/N/A). If OpenRouter key is set in Settings, AI analysis opens as `*_ai.txt`.

**CLI (no GUI):** From the app folder run `python scanner_cli.py --scan trend` (or swing, watchlist, premarket). Exit 0 = success. See **app/CLI_FOR_CLAUDE.md**.

**Watchlist:** Click **Watchlist** to add symbols (max 200). Config: **Filter** = Down X% today (min % in 1–25%) or All tickers. You can **Import CSV** from a Finviz export (Ticker or Symbol column). When a watchlist ticker appears in a scan, you get 2 beeps and it's listed at the top of the report with a WATCHLIST label.

**Quick Lookup:** Enter 1-5 ticker symbols (comma or space separated) in the Quick Lookup box and click **Report** for an instant analysis report.

**Import/Export Config:** Click **Config** to export your full config (all settings + API keys) for backup or transfer to a new PC. Import to restore on a fresh install.

---

## Run on any OS (no Windows installer)

- **Docker (Linux, macOS, Windows with WSL2):** From the project root run `docker compose build` then `docker compose up`. The GUI appears via X11. See **[DOCKER.md](DOCKER.md)** for X11 setup and options.
- **Linux / macOS (native):** Install Python 3.10+ and tkinter (`python3-tk` on Debian/Ubuntu; `brew install python-tk` on macOS). Then run `./app/run.sh` or `python3 app/app.py` from the `app/` directory.

---

## Requirements

- **Windows:** Windows 10 or 11; **Python 3.10+** (INSTALL.bat can install it and installs all dependencies from `app/requirements.txt`).
- **Linux / macOS:** Python 3.10+ and tkinter; `app/run.sh` uses a venv and `pip install -r requirements.txt`.
- **Docker:** Any OS with Docker and X11; Dockerfile installs from `requirements.txt`. See **[DOCKER.md](DOCKER.md)**.
- Internet connection for Finviz data.
- **Update check:** On startup the app checks GitHub for a newer release and shows a download link if one is available.

---

## Project layout

```
ClearBlueSky/
├── README.md           ← You are here
├── README.txt          ← Plain-text readme
├── LICENSE.txt
├── INSTALL.bat         ← Run to install (Windows)
├── DOCKER.md           ← Run with Docker on any OS
├── CLAUDE_AI_GUIDE.md  ← Guide for modifying/rebuilding with AI
├── Dockerfile
├── docker-compose.yml
├── RELEASE_v7.6.md     ← v7.6 release notes
├── RELEASE_v7.7.md     ← v7.7 release notes (current)
├── USER_MANUAL.md      ← Full user manual (scanners, settings, scoring)
├── UPDATE.md           ← In-app Update & Rollback; versioning (7.1, 7.2)
└── app/
    ├── run.sh          ← Run on Linux/macOS (no Docker)
    ├── app.py                  ← Main app
    ├── trend_scan_v2.py        ← Trend scanner (long-term sector rotation)
    ├── emotional_dip_scanner.py← Swing (emotional dips)
    ├── report_generator.py     ← PDF reports + AI prompt
    ├── watchlist_scanner.py    ← Watchlist (Down X% or All)
    ├── market_intel.py         ← Market Intelligence (news, sectors, overnight markets)
    ├── smart_money.py          ← Smart Money signals (WSB, 13F, SEC insider)
    ├── ticker_enrichment.py    ← Earnings warnings, news flags, leveraged suggestions
    ├── insider_scanner.py      ← Insider data for Trend & Swing enrichment
    ├── finviz_safe.py          ← Timeout-protected Finviz wrapper (all scanners)
    ├── price_history.py        ← 30-day price history (sanity check for AI)
    ├── history_analyzer.py     ← Scan history report generator
    ├── accuracy_tracker.py     ← Accuracy tracking (hits/misses vs current prices)
    ├── scan_settings.py        ← Config & scan types
    ├── sound_utils.py          ← Scan-complete & watchlist beeps
    ├── requirements.txt
    ├── START.bat / RUN.bat
    ├── scan_types.json         ← Scan types (4 scanners)
    ├── scanner_cli.py          ← CLI for Claude/automation (no GUI)
    ├── CLI_FOR_CLAUDE.md       ← CLI usage for automation
    └── reports/                ← PDFs (created at runtime)
```

**Your API keys (if you use any)** are stored only in `app/user_config.json`, which is **not** in the repo (see `.gitignore`). Never commit that file. The repo includes `app/user_config.json.example` (blank keys only) as a template; the installer does not copy any existing config so each install starts with a blank config.

---

## Scanners

| Scanner        | Best for              | When to run        |
|----------------|------------------------|--------------------|
| **Trend**      | Long-term sector rotation holds (weeks–months) | After market close |
| **Swing – Dips** | Emotional dips (1–5 days) | 2:30–4:00 PM       |
| **Watchlist**  | Filter: Down X% today (1–25%) or All tickers | Anytime; Config: Min % down, Filter |
| **Pre-Market** | Combined volume scan + velocity gap analysis | 7–9:25 AM |

Reports: PDF (date/time stamped, per-ticker data + enrichment), JSON (same data + `instructions` for AI), and optional `*_ai.txt` (OpenRouter output). Use JSON with any AI: "Follow the instructions in the `instructions` field." See **app/WORKFLOW.md** for the full pipeline.

---

## Support

- **Donate:** [Direct Relief](https://www.directrelief.org/)
- **License:** MIT (see LICENSE.txt)
- **Disclaimer:** For education only. Not financial advice. Do your own research.

---

*ClearBlueSky v7.7 – made with Claude AI*

**v7.7:** Scanner consolidation (7→4), ticker enrichment (earnings/news/leveraged), overnight markets, insider data in Trend & Swing, AI gives 5+ picks, Trend reweighted for long-term sector rotation.  
**v7.6:** Stability & QA — timeout protection on all Finviz/yfinance calls, TclError crash fixes, AI prompt slimmed.  
See **app/CHANGELOG.md** and **RELEASE_v7.7.md**.
