# ClearBlueSky Stock Scanner v7.0

**Free desktop app** that scans the market for trading ideas and generates **PDF + JSON reports** you can use with any AI (in-app via OpenRouter or paste JSON elsewhere).

- **Scanners** – Trend, Swing (emotional dips), Watchlist (Down X% or All), Velocity Barbell, Insider, Pre-Market (S&P 500 / Russell 2000 / ETFs where applicable)
- **Run all scans** – Optional checkbox runs all six scanners in sequence (rate-limited; may take 20+ minutes)
- **CLI** – Run scans from the command line for automation (e.g. Claude, Desktop Commander): `python app/scanner_cli.py --scan <type>`. See **app/CLI_FOR_CLAUDE.md**.
- **Watchlist** – 2 beeps + WATCHLIST when a watchlist ticker appears in any scan
- **Outputs** – PDF report (with per-stock SMA200 status), JSON analysis package (with `instructions` for AI), and optional `*_ai.txt` from OpenRouter
- **Optional AI pipeline** – OpenRouter API key → AI analysis saved as `*_ai.txt`; optional RAG (.txt/.pdf books), TA, sentiment, SEC insider context, chart images
- **Update notice** – On startup, checks for a newer version and shows a link to download

No API key required for the scanners. Optional keys in **Settings**: Finviz, OpenRouter, Alpha Vantage (all stored only in local `user_config.json`). **Releases and the repo never include API keys or user config** – `user_config.json` is gitignored and is not copied on install; the app creates a blank config on first run.

---

## Quick start (Windows)

1. **Install** – Run `INSTALL.bat` (installs Python and dependencies if needed).
2. **Run** – Use the Desktop shortcut or run `app/START.bat` (or `python app/app.py` from `app/`).
3. **Scan** – Choose scan type (Trend, Swing, Watchlist, Velocity Barbell, Insider, Pre-Market); pick index (S&P 500 / Russell 2000 / ETFs) where applicable; click **Run Scan**. Optional: check **Run all scans** (rate-limited).
4. **Report** – PDF + JSON open when done (reports show per-stock SMA200 status: Above/Below/At/N/A). If OpenRouter key is set in Settings, AI analysis opens as `*_ai.txt`.

**CLI (no GUI):** From the app folder run `python scanner_cli.py --scan velocity` (or trend, swing, watchlist, insider, premarket). Exit 0 = success. See **app/CLI_FOR_CLAUDE.md**.

**Watchlist:** Click **Watchlist** to add symbols (max 200). Config: **Filter** = Down X% today (min % in 1–25%) or All tickers. You can **Import CSV** from a Finviz export (Ticker or Symbol column). When a watchlist ticker appears in a scan, you get 2 beeps and it's listed at the top of the report with a WATCHLIST label.

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
├── RELEASE_v7.0.md     ← v7.0 release notes
└── app/
    ├── run.sh          ← Run on Linux/macOS (no Docker)
    ├── app.py                  ← Main app
    ├── trend_scan_v2.py        ← Trend scanner
    ├── emotional_dip_scanner.py← Swing (emotional dips)
    ├── report_generator.py     ← PDF reports
    ├── watchlist_scanner.py    ← Watchlist (Down X% or All)
    ├── scan_settings.py        ← Config & scan types
    ├── sound_utils.py          ← Scan-complete & watchlist beeps
    ├── requirements.txt
    ├── START.bat / RUN.bat
    ├── scan_types.json         ← Scan types (Trend, Swing, Watchlist, Velocity Barbell, Insider, Pre-Market)
    ├── scanner_cli.py          ← CLI for Claude/automation (no GUI)
    ├── CLI_FOR_CLAUDE.md       ← CLI usage for automation
    ├── insider_scanner.py      ← Insider trading scan (Finviz)
    └── reports/                ← PDFs (created at runtime)
```

**Your API keys (if you use any)** are stored only in `app/user_config.json`, which is **not** in the repo (see `.gitignore`). Never commit that file. The repo includes `app/user_config.json.example` (blank keys only) as a template; the installer does not copy any existing config so each install starts with a blank config.

---

## Scanners

| Scanner        | Best for              | When to run        |
|----------------|------------------------|--------------------|
| **Trend**      | Longer holds (weeks–months) | After market close |
| **Swing – Dips** | Emotional dips (1–5 days) | 2:30–4:00 PM       |
| **Watchlist**  | Filter: Down X% today (1–25%) or All tickers | Anytime; Config: Min % down, Filter |
| **Velocity Barbell** | Sector signals → leveraged ideas | Config: min sector %, theme |
| **Insider**    | Latest insider transactions (Finviz) | Anytime |
| **Pre-Market** | Pre-market volume | 7–9:25 AM |

Reports: PDF (date/time stamped, Master Trading Report Directive + per-ticker data), JSON (same data + `instructions` for any AI), and optional `*_ai.txt` (OpenRouter output). Use JSON with any AI: "Follow the instructions in the `instructions` field." See **app/WORKFLOW.md** for the full pipeline.

---

## Support

- **Donate:** [Direct Relief](https://www.directrelief.org/)
- **License:** MIT (see LICENSE.txt)
- **Disclaimer:** For education only. Not financial advice. Do your own research.

---

*ClearBlueSky v7.0 – made with Claude AI*

**v7.0:** Queue-based scans, Run all scans (rate-limited), Swing = emotional-only, single Watchlist (Filter: Down X% or All), Pre-Market encoding fix. See **app/CHANGELOG.md** and **RELEASE_v7.0.md**.
