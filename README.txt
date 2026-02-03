════════════════════════════════════════════════════════════════════════════
   CLEARBLUESKY STOCK SCANNER & AI RESEARCH TOOL
   Version 6.0 | Free & Open Source | Made with Claude AI
════════════════════════════════════════════════════════════════════════════

Thank you for downloading ClearBlueSky Stock Scanner!

This FREE application scans the stock market for trading opportunities
and generates PDF reports you can analyze with AI tools like Claude,
Gemini, ChatGPT, or your own private AI.


════════════════════════════════════════════════════════════════════════════
   WHAT'S IN v6.0
════════════════════════════════════════════════════════════════════════════

• Two scanners: Trend (long-term) and Swing (dips)
• PDF reports only – date/time stamped, with Master Trading Report Directive for AI
• Watchlist – add up to 200 tickers; 2 beeps + top-of-report highlight when a watchlist stock appears in a scan
• Import watchlist from Finviz CSV (Ticker or Symbol column)
• Scan Config – adjust min score, dip %, price, volume per scan type
• Optional Finviz API key in Settings (stored only in user_config.json on your PC – never in code or in the app package)


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


════════════════════════════════════════════════════════════════════════════
   QUICK START
════════════════════════════════════════════════════════════════════════════

1. Launch the app (Desktop shortcut or app/START.bat)

2. Select scan type: Trend - Long-term or Swing - Dips

3. Select index: S&P 500 or Russell 2000

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
• Trend and Swing scanners
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

INSTALL.bat          – Run this to install
README.txt           – This file
README.md            – GitHub / markdown readme
LICENSE.txt          – MIT license
CLAUDE_AI_GUIDE.md   – Guide to rebuild/modify the app with AI

app/
├── app.py                  – Main application
├── trend_scan_v2.py        – Trend scanner
├── enhanced_dip_scanner.py  – Swing/dip scanner
├── report_generator.py     – PDF report builder
├── scan_settings.py        – Configuration
├── sound_utils.py          – Scan-complete & watchlist beeps
├── requirements.txt
├── scan_types.json         – Scan types (Trend, Swing)
├── START.bat / RUN.bat
├── reports/                – Generated PDFs (created at runtime)
└── user_config.json        – Created on first run; your settings (optional API key) go here – never in code


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
   ClearBlueSky v6.0 – made with Claude AI
════════════════════════════════════════════════════════════════════════════
