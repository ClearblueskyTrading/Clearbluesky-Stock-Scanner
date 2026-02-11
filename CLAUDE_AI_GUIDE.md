# ClearBlueSky Stock Scanner v7.88 - Complete Build Guide

## For Claude AI (or any AI assistant)

This document contains everything needed to understand, modify, or rebuild the ClearBlueSky Stock Scanner application. Upload this file to Claude and ask for help!

---

## PROJECT OVERVIEW

**Name:** ClearBlueSky Stock Scanner  
**Version:** 7.0  
**Purpose:** Scan stocks for trading opportunities and generate PDF + JSON reports with optional AI analysis (OpenRouter), RAG, TA, sentiment, market breadth, and risk checks  
**Tech Stack:** Python 3.10+, Tkinter (GUI), Finviz (data), reportlab (PDF), OpenRouter (AI), ChromaDB (RAG), yfinance/pandas-ta (TA)  
**License:** MIT (free and open source)

### Key Features
- Scanners: Trend, Swing (emotional dips), Watchlist (Down X% or All) — S&P 500 / ETFs
- Run all scans: optional checkbox runs all six scanners in sequence (rate-limited; may take 20+ minutes)
- Queue-based scans: background thread keeps GUI responsive (no hanging)
- PDF + JSON reports with Master Trading Report Directive and optional `instructions` field for any AI
- Optional OpenRouter AI analysis → `*_ai.txt`; optional RAG (.txt/.pdf books), TA, Alpha Vantage sentiment, SEC insider context, vision charts
- Market breadth (SMA %, A/D, sector rotation, regime) for index-based scans
- Risk checks per ticker: earnings date, ex-dividend, relative volume (earnings_safe, etc.)
- Progress timers, stop button, update notice on startup

---

## FILE STRUCTURE

```
ClearBlueSky/
├── INSTALL.bat              # Windows installer script
├── README.txt               # User documentation
├── README.md                # GitHub / markdown readme
├── LICENSE.txt              # MIT license
├── CHANGELOG.md             # Version history
├── RELEASE_v7.0.md          # v7.0 release notes
├── DOCKER.md                # Run with Docker on any OS
├── Dockerfile, docker-compose.yml
├── CLAUDE_AI_GUIDE.md       # This file - for AI rebuilding
│
└── app/
    ├── app.py               # Main GUI application
    ├── trend_scan_v2.py     # Trend momentum scanner
    ├── emotional_dip_scanner.py  # Swing (emotional dips)
    ├── watchlist_scanner.py # Watchlist (Down X% or All)
    ├── velocity_leveraged_scanner.py  # Velocity Barbell
    ├── report_generator.py  # PDF report builder
    ├── scan_settings.py     # Settings dialog manager
    ├── sound_utils.py       # Scan-complete & watchlist beeps
    ├── scanner_cli.py       # CLI for automation (no GUI)
    ├── user_config.json.example  # Blank config template
    ├── START.bat            # Launch shortcut (Windows)
    ├── RUN.bat              # Direct Python launcher (Windows)
    ├── run.sh               # Run on Linux/macOS
    ├── reports/             # Generated PDF reports (runtime)
    └── scans/               # Saved scan data (runtime)
```

---

## ARCHITECTURE

### Data Flow
```
User clicks "Run Scan"
    ↓
Scanner (trend_scan_v2.py, emotional_dip_scanner.py, watchlist_scanner.py, etc.)
    ↓
Fetches data from Finviz (free scraping or Elite API)
    ↓
Scores and ranks stocks
    ↓
Report Generator (report_generator.py)
    ↓
Creates PDF with data, AI prompts (Master Trading Report Directive)
    ↓
Opens PDF
    ↓
User copies prompt to AI for analysis
```

### Module Responsibilities

**app.py** - Main application
- Tkinter GUI (dark header, white cards)
- Scanner controls and progress tracking
- AI selection and URL configuration
- Settings dialogs
- Report launching

**trend_scan_v2.py** - Trend Scanner
- Fetches S&P 500 or Russell 2000 stocks from Finviz
- Gets overview data (price, volume, market cap)
- Gets performance data (weekly, monthly, quarterly)
- Calculates momentum score
- Returns DataFrame of top candidates

**emotional_dip_scanner.py** - Swing Scanner (emotional dips)
- Fetches stocks with recent price drops (index-based)
- Analyzes dip percentage, volume, emotional triggers
- Calculates recovery potential score
- Returns list of dip opportunities

**watchlist_scanner.py** - Watchlist Scanner
- Filter: Down % today (0–X% range, slider = max) or All tickers
- Scans only tickers in user watchlist
- Returns list for report

**report_generator.py** - Report Builder
- Takes scanner results
- Fetches TradingView chart images
- Builds beautiful HTML report
- Embeds AI prompts for each AI tool
- Saves to reports/ folder

**scan_settings.py** - Settings Manager
- Trend scanner settings (min score, MA stack, etc)
- Swing scanner settings (dip %, price range, etc)
- Saves/loads from user_config.json

---

## KEY CONFIGURATION

### user_config.json
```json
{
  "trend_min_score": "70",
  "swing_min_score": "60",
  "dip_min_percent": 1.0,
  "dip_max_percent": 5.0,
  "min_price": "5",
  "max_price": "500",
  "min_avg_volume": "500000",
  "trend_min_quarter_perf": "10",
  "trend_require_ma_stack": true,
  "dip_require_news_check": true,
  "dip_require_analyst_check": true,
  "other_ai_url": "",
  "finviz_api_key": ""
}
```

### Paths (Windows)
```python
BASE_DIR = r"C:\TradingBot"  # or portable location
CONFIG_FILE = os.path.join(BASE_DIR, "user_config.json")
LOG_FILE = os.path.join(BASE_DIR, "error_log.txt")
```

---

## GUI COMPONENTS

### Color Scheme
```python
BG_DARK = "#1a1a2e"      # Dark blue header
GREEN = "#28a745"         # Trend scanner, success
BLUE = "#007bff"          # Swing scanner
PURPLE = "#6f42c1"        # Qwen/private AI
PINK = "#E91E63"          # Donate button
```

### Main Window Structure
```
┌─────────────────────────────────────┐
│  ☁️ ClearBlueSky (dark header)      │
│  Stock Scanner v5.1                 │
│  made with Claude                   │
├─────────────────────────────────────┤
│  🤖 AI Research Tool [Dropdown] ⚙  │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐    │
│  │ 📈 Trend Scanner            │    │
│  │ [Index ▼] [▶ Run] [■ Stop]  │    │
│  │ [====Progress====] 50% (12s)│    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 📉 Swing Scanner            │    │
│  │ [Index ▼] [▶ Run] [■ Stop]  │    │
│  │ [====Progress====] 25% (8s) │    │
│  └─────────────────────────────┘    │
├─────────────────────────────────────┤
│ [Reports] [History] [Logs] [Config] │
│ [Settings] [Help] [Donate] [Exit]   │
├─────────────────────────────────────┤
│ Status: Ready                       │
└─────────────────────────────────────┘
```

---

## SCANNER LOGIC

### Trend Scanner (trend_scan_v2.py)

```python
def trend_scan(progress_callback=None, index="sp500"):
    """
    1. Fetch overview data from Finviz (all stocks in index)
    2. Fetch performance data (weekly, monthly, quarterly returns)
    3. Merge datasets
    4. Calculate momentum score:
       - Quarterly performance (weight: 40%)
       - Monthly performance (weight: 30%)
       - Weekly performance (weight: 20%)
       - Volume trend (weight: 10%)
    5. Filter by MA stack if required (SMA20 > SMA50 > SMA200)
    6. Return top 20 stocks by score
    """
```

### Swing Scanner (enhanced_dip_scanner.py)

```python
def run_enhanced_dip_scan(progress_callback=None, index="sp500"):
    """
    1. Fetch stocks down 1-5% today from Finviz
    2. Filter by price range and volume
    3. For each stock:
       - Calculate dip severity score
       - Check RSI (oversold = better)
       - Check if above 200 SMA (uptrend = better)
       - Optional: Check recent news
       - Optional: Check analyst ratings
    4. Score and rank opportunities
    5. Return top dip candidates
    """
```

---

## API MODES

### Free Mode (No API Key)
- Uses web scraping via finvizfinance library
- Rate limited (1 request per second)
- Slower but works without payment
- May break if Finviz changes their HTML

### Elite API Mode (With API Key)
- Direct API access to Finviz
- Much faster (30 seconds vs 2-3 minutes)
- More reliable
- Requires Finviz Elite subscription ($39/month)

```python
# Detection in scanners
api_key = config.get('finviz_api_key', '')
if api_key:
    # Use Elite API
    from finvizfinance.quote import finvizfinance
    stock = finvizfinance(ticker, api_key=api_key)
else:
    # Use free scraping
    from finvizfinance.screener.overview import Overview
```

---

## PROGRESS TRACKING

### Timer Implementation
```python
import time

self.trend_start_time = time.time()

def progress(msg):
    elapsed = int(time.time() - self.trend_start_time)
    self.trend_progress.set(50, f"50% ({elapsed}s)")
```

### Stop Button Implementation
```python
self.trend_cancelled = False

def stop_trend_scan(self):
    self.trend_cancelled = True

def progress(msg):
    if self.trend_cancelled:
        return  # Stop processing
```

---

## COMMON MODIFICATIONS

### Add New AI Option
1. Edit `ai_combo` values in `create_widgets()`
2. Add URL in `open_ai()` method
3. Add prompt template in `report_generator.py`

### Change Scanner Parameters
1. Edit defaults in `user_config.json`
2. Add UI controls in `scan_settings.py`
3. Use values in scanner files

### Add New Scanner Type
1. Create new `my_scanner.py` file
2. Import in `app.py`
3. Add UI card similar to trend/swing
4. Add to report generator

### Modify Report Appearance
1. Edit HTML templates in `report_generator.py`
2. CSS is inline in the `<style>` section
3. Charts come from TradingView widget

---

## TROUBLESHOOTING

### "No module named 'finvizfinance'"
```bash
pip install finvizfinance
```

### "Scan stuck / no progress"
- Check internet connection
- Finviz may be blocking (try later)
- Try with API key for more reliable access

### "Report won't open"
- Check reports/ folder exists
- Check browser is set as default for .html
- Try opening file manually

### "API key not working"
- Verify key in Settings
- Check Finviz Elite subscription is active
- Key format should be alphanumeric string

---

## REBUILD FROM SCRATCH

If you need to rebuild the entire app, here's the process:

### 1. Create Project Structure
```bash
mkdir ClearBlueSky
cd ClearBlueSky
mkdir app app/reports app/scans
```

### 2. Create Requirements
```
finviz>=0.14
finvizfinance>=0.14
pandas>=1.5
requests>=2.28
pygame>=2.1
```
(Optional: beautifulsoup4 for scraping. pygame is used for scan-complete alarm MP3.)

### 3. Build Components in Order
1. `user_config.json` - Configuration
2. `scan_settings.py` - Settings dialogs
3. `trend_scan_v2.py` - Trend scanner
4. `enhanced_dip_scanner.py` - Swing scanner
5. `report_generator.py` - Report builder
6. `app.py` - Main GUI
7. Batch files for Windows

### 4. Test Each Component
```python
# Test scanner
from trend_scan_v2 import trend_scan
df = trend_scan(print)
print(df.head())
```

---

## VERSION HISTORY

- **v6.4** (Current): JSON + instructions, OpenRouter AI, RAG (.txt/.pdf), TA, sentiment, SEC insider, market breadth, risk checks (earnings/ex-div/rel vol), progress for AI phase, Settings window sizing
- **v6.3**: Insider scanner, leveraged play suggestions (bull only), 5 headlines per ticker
- **v6.2**: Update notice, Docker/cross-platform, cross-platform sound
- **v6.1**: Docker, Linux/macOS support, cross-platform beeps
- **v6.0**: PDF-only reports, watchlist, Master Trading Report Directive

---

## CONTACT & SUPPORT

- **Discord:** 340935763405570048
- **Donate:** https://www.directrelief.org/

---

## QUICK PROMPTS FOR CLAUDE

**Add a feature:**
> "Looking at this app structure, please add [feature]. Here's what I want it to do: [description]"

**Fix a bug:**
> "The scanner is [problem]. Here's the error: [error]. Please help fix it."

**Explain code:**
> "Please explain how the trend_scan function works step by step."

**Modify UI:**
> "I want to change the [element] to [new style]. How do I do that?"

---

*This guide was generated for ClearBlueSky Stock Scanner v6.4*
*Made with Claude AI - Free and Open Source*
