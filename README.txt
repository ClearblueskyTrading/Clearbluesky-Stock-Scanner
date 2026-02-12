════════════════════════════════════════════════════════════════════════════
   CLEARBLUESKY STOCK SCANNER & AI RESEARCH TOOL
   Version 7.89 | Free & Open Source | Made with Claude AI
════════════════════════════════════════════════════════════════════════════

Thank you for downloading ClearBlueSky Stock Scanner!

This FREE application scans the stock market for trading opportunities
and generates PDF reports you can analyze with AI tools like Claude,
Gemini, ChatGPT, or your own private AI.


════════════════════════════════════════════════════════════════════════════
   WHAT'S IN v7.89
════════════════════════════════════════════════════════════════════════════

• 3 Scanners: Velocity Trend Growth (momentum), Swing (emotional dips), Watchlist
• Finviz fallback: full S&P 500 from CSV when Finviz fails; auto-update deps on startup
• Update now: in-app Update downloads, applies, and restarts automatically
• ETF guardrails: curated ETF universe with leveraged bull + bear core, hard 100k avg-volume floor
• Velocity Trend Growth: Sector-first — ranks sectors by return, scans only leading sectors
• Ticker Enrichment: earnings warnings, news sentiment, live price, leveraged suggestions
• Insider Data: SEC Form 4 folded into Velocity Trend Growth & Swing
• Market Intelligence: Google News, Finviz news, sector performance, market snapshot
• Run all scans – Optional checkbox runs all 3 scanners in sequence (~15 min)
• CLI – python scanner_cli.py --scan velocity_trend_growth (from app folder)
• PDF + JSON reports – JSON includes "instructions" for any AI
• Optional OpenRouter AI – set API key in Settings; AI analysis saved as *_ai.txt
• Watchlist – up to 400 tickers; 2 beeps + WATCHLIST when one appears
• In-app Update & Rollback – downloads, applies, restarts; config never overwritten


════════════════════════════════════════════════════════════════════════════
   INSTALLATION (2-3 minutes)
════════════════════════════════════════════════════════════════════════════

1. Right-click "INSTALL.bat" -> "Run as administrator"

2. Choose where to install:
   [1] C:\TradingBot        - Standard install (recommended)
   [2] Current folder       - Portable mode (USB drive)
   [3] Custom path          - You choose the location

3. Wait for installation to complete
   - Python will be installed if not found
   - Required packages will download automatically

4. Done! Find "ClearBlueSky Scanner" shortcut on your Desktop

OTHER WAYS TO RUN (no Windows installer):
  Docker (any OS): From the project folder run "docker compose build" then "docker compose up". See DOCKER.md.
  Linux / macOS: Install Python 3.10+ and tkinter, then run ./app/run.sh or "python3 app/app.py" from the app folder.


════════════════════════════════════════════════════════════════════════════
   QUICK START
════════════════════════════════════════════════════════════════════════════

1. Launch the app (Desktop shortcut or app/START.bat)

2. Select scan type: Velocity Trend Growth, Swing, Watchlist

3. Click "Run Scan". Optional: check "Run all scans" (~15 min).
   When done, the PDF report opens.

4. Use the PDF with your preferred AI (Claude, Gemini, ChatGPT) for analysis.

5. Optional: Add tickers in Watchlist (max 400).
   When a watchlist stock appears in a scan, you get 2 beeps and it's at the top.


════════════════════════════════════════════════════════════════════════════
   FEATURES
════════════════════════════════════════════════════════════════════════════

FREE (no API key required):
  Velocity Trend Growth (sector-first momentum), Swing (emotional dips), Watchlist
  S&P 500 + ETFs
  Ticker enrichment: earnings warnings, news sentiment, leveraged suggestions
  Overnight/overseas market context
  Insider data in Velocity Trend Growth & Swing scans
  Run all scans
  PDF reports with AI-oriented prompts
  Watchlist with 2-beep alert and report highlight

OPTIONAL API keys (Settings):
  Finviz Elite – avoids rate limits
  OpenRouter – AI analysis (*_ai.txt)
  Alpha Vantage – news sentiment per ticker


════════════════════════════════════════════════════════════════════════════
   FILES INCLUDED
════════════════════════════════════════════════════════════════════════════

INSTALL.bat          - Run this to install (Windows)
README.txt           - This file
README.md            - GitHub / markdown readme
CURSOR_AI_GUIDE.md   - Guide for Cursor implementation
LICENSE.txt          - MIT license
RELEASE_v7.88.md     - v7.88 release notes
RELEASE_v7.89.md     - v7.89 release notes (current)
USER_MANUAL.md       - Full user manual
DOCKER.md            - Run with Docker on any OS
Dockerfile, docker-compose.yml - Docker setup

app/
  app.py                  - Main application
  velocity_trend_growth.py - Velocity Trend Growth (momentum) scanner
  emotional_dip_scanner.py - Swing (emotional dips)
  watchlist_scanner.py    - Watchlist (Down % today 0–X or All)
  ticker_enrichment.py    - Earnings, news, leveraged suggestions
  insider_scanner.py      - SEC insider data
  market_intel.py         - Market intelligence + overnight markets
  report_generator.py     - PDF report builder
  finviz_safe.py          - Timeout-protected Finviz wrapper
  scan_settings.py       - Configuration
  requirements.txt
  scan_types.json        - Scan types (3 scanners)
  scanner_cli.py         - CLI for automation
  reports/                - Generated PDFs (created at runtime)


════════════════════════════════════════════════════════════════════════════
   GITHUB & RELEASES
════════════════════════════════════════════════════════════════════════════

Source and release zip:
https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases

Your API keys (if you use any) are only in user_config.json on your machine;
they are not in the source code or in the release package.


════════════════════════════════════════════════════════════════════════════
   SUPPORT & DONATE
════════════════════════════════════════════════════════════════════════════

This app is FREE forever. If you find it useful, please consider
donating to Direct Relief (https://www.directrelief.org/) - medical aid worldwide.


════════════════════════════════════════════════════════════════════════════
   DISCLAIMER
════════════════════════════════════════════════════════════════════════════

For educational purposes only. Not financial advice.
Always do your own research before trading.
Past performance does not guarantee future results.

════════════════════════════════════════════════════════════════════════════
   ClearBlueSky v7.89 - made with Claude AI
════════════════════════════════════════════════════════════════════════════
