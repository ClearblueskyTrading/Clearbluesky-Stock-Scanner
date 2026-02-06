# ClearBlueSky Stock Scanner v7.0

**Free desktop app** that scans the market for trading ideas and generates **PDF + JSON reports** you can use with any AI (in-app via OpenRouter or paste JSON elsewhere).

- **Scanners** – Trend, Swing (emotional dips), Watchlist (Down X% or All), Velocity Barbell, Insider, Pre-Market (S&P 500 / Russell 2000 / ETFs where applicable)
- **Run all scans** – Optional checkbox runs all six scans in sequence (rate-limited; may take 20+ minutes)
- **Watchlist** – 2 beeps + WATCHLIST when a watchlist ticker appears in any scan
- **Outputs** – PDF report, JSON analysis package (with `instructions` for AI), and optional `*_ai.txt` from OpenRouter
- **Optional AI pipeline** – OpenRouter API key → AI analysis saved as `*_ai.txt`; optional RAG (.txt/.pdf books), TA, sentiment, SEC insider context, chart images
- **Update notice** – On startup, checks for a newer version and shows a link to download

No API key required for the scanners. Optional keys in **Settings**: Finviz, OpenRouter, Alpha Vantage (all stored only in local `user_config.json`).

---

## Quick start (Windows)

1. **Install** – Run `INSTALL.bat` (from project root; installs Python and dependencies if needed).
2. **Run** – Use the Desktop shortcut or run `START.bat` or `RUN.bat` from this folder (or `python app.py`).
3. **Scan** – Choose scan type (Trend, Swing, Watchlist, Velocity Barbell, Insider, Pre-Market); pick index where applicable; click **Run Scan**. Optionally check **Run all scans** (rate-limited).
4. **Report** – PDF + JSON open when done. If OpenRouter key is set in Settings, AI analysis opens as `*_ai.txt`.

**Watchlist:** Click **Watchlist** to add symbols (max 200). You can **Import CSV** from a Finviz export (Ticker or Symbol column). Config: **Filter** = Down X% today (min % in 1–25% range) or All tickers. When a watchlist ticker appears in a scan, you get 2 beeps and it's listed at the top of the report with a WATCHLIST label.

---

## Run on any OS

- **Docker:** From the project root run `docker compose build` then `docker compose up`. See project root **DOCKER.md**.
- **Linux / macOS:** Install Python 3.10+ and tkinter. Run `./run.sh` or `python3 app.py` from this folder.

---

## Requirements

- **Windows:** Windows 10 or 11; **Python 3.10+**.
- **Linux / macOS:** Python 3.10+ and tkinter.
- Internet connection for Finviz data.
- Optional: `pip install -r requirements.txt` (chromadb, PyMuPDF, etc. for RAG and full features).

---

## Outputs per run

| File | Contents |
|------|----------|
| `*_Scan_*.pdf` | Report with Master Trading Report Directive + per-ticker data. |
| `*_Scan_*.json` | Same data + `instructions` for any AI. Use with any AI: "Follow the instructions in the `instructions` field." |
| `*_Scan_*_ai.txt` | AI analysis (only if OpenRouter key set in Settings). |

Reports folder is set in **Settings → Reports → Output folder** (default: `reports/` in this folder).

---

## Scanners

| Scanner | Best for | When to run |
|---------|----------|-------------|
| **Trend** | Longer holds (weeks–months) | After market close |
| **Swing – Dips** | Emotional dips (1–5 days) | 2:30–4:00 PM |
| **Watchlist** | Watchlist tickers: Down X% today (1–25%) or All tickers | Anytime; Config: Filter, Min % down |
| **Velocity Barbell** | Sector signals → leveraged ideas | Anytime |
| **Insider** | Latest insider transactions (Finviz) | Anytime |
| **Pre-Market** | Pre-market volume | 7–9:25 AM |

---

## Settings (optional)

- **Finviz API key** – Scanner data (or scraping).
- **OpenRouter API key + model** – Enables AI analysis → `*_ai.txt`.
- **Alpha Vantage API key** – Sentiment + headlines per ticker.
- **RAG books folder** – .txt/.pdf books; click **Build RAG index**; **Include RAG excerpts in AI analysis**.
- **Include TA in report** – SMAs, RSI, MACD, BB, ATR, Fib per ticker.
- **Add SEC insider context** – 10b5-1 vs discretionary for tickers with insider data.
- **Include chart images in AI analysis** – Attach candlestick charts (multimodal models only).

See **WORKFLOW.md** in this folder for the full pipeline.

---

## Support

- **Donate:** [Direct Relief](https://www.directrelief.org/)
- **License:** MIT (see project root LICENSE.txt)
- **Disclaimer:** Education only. Not financial advice. Do your own research.

---

*ClearBlueSky v7.0 – made with Claude AI*

**v7.0:** Queue-based scans (GUI stays responsive), Run all scans (rate-limited), Swing = emotional-only dips, single Watchlist scanner (Filter: Down X% or All), Pre-Market encoding fix for Windows. See **CHANGELOG.md** for full history.
