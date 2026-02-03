# ClearBlueSky Stock Scanner v6.0

**Free desktop app** that scans the market for trading ideas and generates **PDF reports** you can analyze with any AI (Claude, Gemini, ChatGPT).

- **Trend scanner** – Uptrending names (S&P 500 / Russell 2000)  
- **Swing scanner** – Oversold dips with news/analyst check  
- **Watchlist** – Get 2 beeps and top-of-report highlight when a watchlist ticker appears in a scan  
- **PDF reports** – Date/time stamped, with Master Trading Report Directive for AI and per-ticker data  

No API key required for the scanners. Optional [Finviz Elite](https://finviz.com) API key can be set in **Settings** (stored only in your local `user_config.json`, never in code or in this repo).

---

## Quick start

1. **Install** – Run `INSTALL.bat` (installs Python and dependencies if needed).  
2. **Run** – Use the Desktop shortcut or run `app/START.bat` (or `python app/app.py` from `app/`).  
3. **Scan** – Choose **Trend** or **Swing**, pick index (S&P 500 or Russell 2000), click **Run Scan**.  
4. **Report** – PDF opens when the scan finishes; use it with your preferred AI.  

**Watchlist:** Click **Watchlist** to add symbols (max 200). You can **Import CSV** from a Finviz export (Ticker or Symbol column). When a watchlist ticker appears in a scan, you get 2 beeps and it’s listed at the top of the report with a ★ WATCHLIST label.

---

## Requirements

- **Windows 10 or 11**  
- **Python 3.10+** (INSTALL.bat can install it)  
- Internet connection for Finviz data  

---

## Project layout

```
ClearBlueSky/
├── README.md           ← You are here
├── README.txt          ← Plain-text readme
├── LICENSE.txt
├── INSTALL.bat         ← Run to install
├── CLAUDE_AI_GUIDE.md  ← Guide for modifying/rebuilding with AI
└── app/
    ├── app.py                  ← Main app
    ├── trend_scan_v2.py        ← Trend scanner
    ├── enhanced_dip_scanner.py ← Swing/dip scanner
    ├── report_generator.py    ← PDF reports
    ├── scan_settings.py        ← Config & scan types
    ├── sound_utils.py          ← Scan-complete & watchlist beeps
    ├── requirements.txt
    ├── START.bat / RUN.bat
    ├── scan_types.json         ← Scan types (Trend, Swing)
    └── reports/                ← PDFs (created at runtime)
```

**Your API key (if you use one)** is stored only in `app/user_config.json`, which is **not** in the repo (see `.gitignore`). Never commit that file.

---

## Scanners

| Scanner        | Best for              | When to run        |
|----------------|------------------------|--------------------|
| **Trend**      | Longer holds (weeks–months) | After market close |
| **Swing – Dips** | Short-term dips (1–5 days) | 2:30–4:00 PM       |

Reports are PDF-only, date/time stamped. Each includes a Master Trading Report Directive for AI and tells the AI to use Yahoo Finance for charts (e.g. `https://finance.yahoo.com/quote/AAPL/chart`).

---

## Support

- **Donate:** [Direct Relief](https://www.directrelief.org/)  
- **License:** MIT (see LICENSE.txt)  
- **Disclaimer:** For education only. Not financial advice. Do your own research.

---

*ClearBlueSky v6.0 – made with Claude AI*
