════════════════════════════════════════════════════════════════════════════
   CLEARBLUESKY STOCK SCANNER & AI RESEARCH TOOL
   Version 6.4 | Free & Open Source | Made with Claude AI
════════════════════════════════════════════════════════════════════════════

Thank you for downloading ClearBlueSky Stock Scanner!

This FREE application scans the stock market for trading opportunities
and generates PDF reports you can analyze with AI tools like Claude,
Gemini, ChatGPT, or your own private AI.


════════════════════════════════════════════════════════════════════════════
   WHAT'S IN v6.4
════════════════════════════════════════════════════════════════════════════

• Six scanners: Trend, Swing, Watchlist, Insider, Emotional Dip, Pre-Market
• PDF + JSON reports – date/time stamped; JSON includes “instructions” for any AI
• Optional OpenRouter AI – set API key in Settings; AI analysis saved as *_ai.txt
• Optional: RAG (.txt/.pdf books), TA in report, Alpha Vantage sentiment, SEC insider context, chart images
• Watchlist – up to 200 tickers; 2 beeps + ★ WATCHLIST when one appears in a scan
• Import watchlist from Finviz CSV (Ticker or Symbol column)
• Scan Config – min score, dip %, “% down today,” price, volume per scan type
• Update notice – app checks for newer version on startup
• Optional API keys in Settings (Finviz, OpenRouter, Alpha Vantage – stored only in user_config.json)


════════════════════════════════════════════════════════════════════════════
   INSTALLATION (2–3 minutes)
════════════════════════════════════════════════════════════════════════════

1. Right-click "INSTALL.bat" → "Run as administrator"

2. Choose where to install:
   [1] C:\TradingBot        – Standard install (recommended)
   [2] Current folder       – Portable mode (USB drive)
   [3] Custom path          – You choose the location

3. Wait for installation to complete
   – Python will be installed if not found
   – Required packages will download automatically

4. Done! Find "ClearBlueSky Scanner" shortcut on your Desktop

OTHER WAYS TO RUN (no Windows installer):
• Docker (any OS): From the project folder run "docker compose build" then "docker compose up". See DOCKER.md.
• Linux / macOS: Install Python 3.10+ and tkinter, then run ./app/run.sh or "python3 app/app.py" from the app folder.


════════════════════════════════════════════════════════════════════════════
   QUICK START
════════════════════════════════════════════════════════════════════════════

1. Launch the app (Desktop shortcut or app/START.bat)

2. Select scan type: Trend - Long-term, Swing - Dips, or Watchlist - Near open

3. Select index: S&P 500 or Russell 2000 (N/A for Watchlist)

4. Click "Run Scan". When done, the PDF report opens.

5. Use the PDF with your preferred AI (Claude, Gemini, ChatGPT) for analysis.
   Reports tell the AI to use Yahoo Finance for charts (e.g. finance.yahoo.com/quote/AAPL/chart).

6. Optional: Add tickers in Watchlist (max 200). When a watchlist stock
   appears in a scan, you get 2 beeps and it’s at the top of the report (★ WATCHLIST).
   You can import from a Finviz CSV via Watchlist → Import CSV.


════════════════════════════════════════════════════════════════════════════
   FEATURES
════════════════════════════════════════════════════════════════════════════

FREE (no API key required):
• Trend, Swing, and Watchlist scanners (% down today 1–25%)
• S&P 500 and Russell 2000
• PDF reports with AI-oriented prompts
• Watchlist with 2-beep alert and report highlight
• Import watchlist from Finviz CSV
• Configurable scan parameters (Config button)
• Scan-complete sound (Settings: beep / asterisk / exclamation)

OPTIONAL – Finviz Elite API key (e.g. from finviz.com):
• Stored only in your local user_config.json (never in code or in the zip)
• Can improve speed/reliability; not required for core features



════════════════════════════════════════════════════════════════════════════
   FILES INCLUDED
════════════════════════════════════════════════════════════════════════════

INSTALL.bat          – Run this to install (Windows)
README.txt           – This file
README.md            – GitHub / markdown readme
LICENSE.txt          – MIT license
DOCKER.md            – Run with Docker on any OS
Dockerfile, docker-compose.yml – Docker setup
CLAUDE_AI_GUIDE.md   – Guide to rebuild/modify the app with AI

app/
├── app.py                  – Main application
├── trend_scan_v2.py        – Trend scanner
├── enhanced_dip_scanner.py  – Swing/dip scanner
├── watchlist_scanner.py     – Watchlist “% down today” scanner
├── report_generator.py     – PDF report builder
├── scan_settings.py        – Configuration
├── sound_utils.py          – Scan-complete & watchlist beeps
├── requirements.txt
├── scan_types.json         – Scan types (Trend, Swing, Watchlist)
├── START.bat / RUN.bat  – Start the app (Windows)
├── run.sh               – Start on Linux/macOS (no Docker)
├── reports/                – Generated PDFs (created at runtime)
└── user_config.json        – Created on first run; your settings (optional API keys) go here – never in code


════════════════════════════════════════════════════════════════════════════
   GITHUB & RELEASES
════════════════════════════════════════════════════════════════════════════

Source and release zip: see the GitHub repo.
Your API key (if you use one) is only in user_config.json on your machine;
it is not in the source code or in the release package.


════════════════════════════════════════════════════════════════════════════
   SUPPORT & DONATE
════════════════════════════════════════════════════════════════════════════

This app is FREE forever. If you find it useful, please consider
donating to Direct Relief (https://www.directrelief.org/) – medical aid worldwide.

Contact: Discord ID 340935763405570048


════════════════════════════════════════════════════════════════════════════
   DISCLAIMER
════════════════════════════════════════════════════════════════════════════

For educational purposes only. Not financial advice.
Always do your own research before trading.
Past performance does not guarantee future results.

════════════════════════════════════════════════════════════════════════════
   ClearBlueSky v6.4 – made with Claude AI
════════════════════════════════════════════════════════════════════════════
