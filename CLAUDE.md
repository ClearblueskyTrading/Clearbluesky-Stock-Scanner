# CLAUDE.md - AI Assistant Guide for ClearBlueSky Stock Scanner

## Project Overview

**ClearBlueSky Stock Scanner** is a free, open-source desktop application for scanning stocks and generating AI-ready analysis reports. It uses Python/Tkinter for the GUI and Finviz for market data.

- **Version**: 5.1
- **License**: MIT
- **Platform**: Windows (Python 3.10+)
- **Purpose**: Educational stock analysis tool (not financial advice)

## Quick Start Commands

```bash
# Run the application
cd app && python app.py

# Or use the batch launchers (Windows)
./app/RUN.bat       # Shows console output
./app/START.bat     # Headless mode

# Install dependencies (if needed)
pip install finvizfinance finviz pandas requests beautifulsoup4
```

## Repository Structure

```
Clearbluesky-Stock-Scanner/
├── CLAUDE_AI_GUIDE.md       # Detailed rebuild guide (comprehensive)
├── README.txt               # User documentation
├── LICENSE.txt              # MIT license
├── INSTALL.bat              # Windows installer script
│
└── app/                     # Main application code
    ├── app.py               # Main GUI application (929 lines)
    ├── trend_scan_v2.py     # Trend momentum scanner (191 lines)
    ├── enhanced_dip_scanner.py  # Swing/dip scanner (371 lines)
    ├── report_generator.py  # HTML report builder (484 lines)
    ├── scan_settings.py     # Settings dialogs & config (281 lines)
    ├── user_config.json     # User preferences (created at runtime)
    ├── RUNPOD_AI_GUIDE.txt  # Private AI setup guide
    ├── START.bat / RUN.bat  # Launchers
    ├── reports/             # Generated HTML reports
    └── scans/               # Saved CSV scan data
```

## Architecture

```
┌─────────────────────────────────┐
│   app.py (Main GUI)             │
│   - Tkinter UI                  │
│   - Scanner orchestration       │
│   - Progress tracking           │
└──────────────┬──────────────────┘
               │
    ┌──────────┴───────────┬─────────────────────┐
    │                      │                     │
┌───▼──────────────┐  ┌────▼──────────┐   ┌──────▼──────────┐
│ trend_scan_v2.py │  │enhanced_dip_  │   │report_generator │
│ (Trend Scanner)  │  │scanner.py     │   │.py              │
│                  │  │(Swing Scanner)│   │(HTML Builder)   │
└──────────────────┘  └───────────────┘   └─────────────────┘
               │              │                    │
               └──────────────┴────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Finviz API/Scraper│
                    │ (Data Source)     │
                    └───────────────────┘
```

## Key Code Patterns

### Naming Conventions
- **Functions**: `snake_case` (e.g., `trend_scan`, `analyze_dip_quality`)
- **Classes**: `PascalCase` (e.g., `TradeBotApp`, `ProgressBar`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `BG_DARK`, `GREEN`, `OUTPUT_DIR`)
- **GUI Colors**: Hex constants defined at module level

### Color Scheme (used throughout)
```python
BG_DARK = "#1a1a2e"    # Dark blue header
GREEN = "#28a745"       # Trend scanner, success
BLUE = "#007bff"        # Swing scanner
PURPLE = "#6f42c1"      # Qwen/private AI
ORANGE = "#fd7e14"      # Warnings
GRAY = "#6c757d"        # Disabled elements
```

### Progress Callback Pattern
All scanners use a callback pattern for real-time UI updates:
```python
def trend_scan(progress_callback=None, index="sp500"):
    def progress(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)

    progress("Starting scan...")
    # ... scan logic ...
```

### Configuration Management
```python
# Loading config with defaults
from scan_settings import load_config, save_config

config = load_config()  # Returns dict with defaults + saved values
config['new_setting'] = value
save_config(config)
```

### Portable Path Handling
All modules use this pattern for portability:
```python
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "user_config.json")
```

## Module Responsibilities

### app.py - Main Application
- Tkinter GUI with dark/light theme
- Scanner orchestration and threading
- Progress bars with elapsed time display
- AI tool selection and URL handling
- Stop button support via cancellation flags

### trend_scan_v2.py - Trend Scanner
- Fetches S&P 500 or Russell 2000 stocks
- Filters: Above SMA20/50/200, >500K volume, >$5 price
- **Scoring Algorithm** (0-100):
  - Quarterly performance: up to 25 pts
  - Monthly performance: up to 20 pts
  - Weekly performance: up to 10 pts
  - Relative volume: up to 15 pts
  - Today's change: up to 10 pts
  - Yearly bonus: up to 10 pts
  - Base points (passed filters): 10 pts
- Returns top stocks sorted by score as DataFrame

### enhanced_dip_scanner.py - Swing Scanner
- Finds stocks down 1-5% today within price/volume filters
- **Quality Analysis** for each stock:
  - Analyst ratings and price targets
  - News sentiment (emotional vs fundamental dips)
  - RSI levels (oversold = good)
  - SMA200 position
- Classifies dips as `emotional` (buyable) or `fundamental` (avoid)
- Returns ranked list with recommendations

### report_generator.py - Report Builder
- Creates HTML reports with TradingView charts
- Embeds AI-optimized prompts for each tool
- Includes news headlines and key metrics
- Copy-to-clipboard functionality

### scan_settings.py - Settings Manager
- Tkinter dialogs for configuration
- Loads/saves user_config.json
- Provides defaults for all settings

## Configuration Reference

### user_config.json Structure
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
  "broker_url": "https://www.schwab.com",
  "other_ai_url": "",
  "finviz_api_key": ""
}
```

## Data API Modes

### Free Mode (No API Key)
- Uses web scraping via `finvizfinance` library
- Rate limited: ~1 request/second
- Slower but completely free
- May break if Finviz changes HTML

### Elite API Mode (With API Key)
- Direct API access to Finviz
- Much faster (30 sec vs 2-3 min)
- Requires Finviz Elite subscription ($39/month)

## Development Guidelines

### Adding a New Scanner
1. Create `app/new_scanner.py` with main function accepting `progress_callback` and `index`
2. Import in `app.py`
3. Add UI card similar to existing trend/swing cards
4. Add to report generator for HTML output

### Adding a New AI Option
1. Add to `ai_combo` values in `app.py:create_widgets()`
2. Add URL handling in `open_ai()` method
3. Add prompt template in `report_generator.py`

### Modifying Scan Parameters
1. Add default in `scan_settings.py:load_config()` defaults dict
2. Add UI control in `ScanSettingsWindow.build_ui()`
3. Use value in scanner files via `load_config()`

### Error Handling Pattern
```python
def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + "\n")
    except:
        pass

def log_error(e, context=""):
    log(f"{context}: {str(e)}", "ERROR")
    log(traceback.format_exc(), "TRACE")
```

## Dependencies

```
finvizfinance>=0.14    # Finviz web scraper
finviz                 # Finviz API client
pandas>=1.5            # Data manipulation
requests>=2.28         # HTTP requests
beautifulsoup4>=4.11   # HTML parsing
tkinter                # GUI (built-in with Python)
```

## Testing

No automated test suite exists. Manual testing workflow:
```python
# Test trend scanner directly
from trend_scan_v2 import trend_scan
df = trend_scan(print)
print(df.head())

# Test swing scanner directly
from enhanced_dip_scanner import run_enhanced_dip_scan
results = run_enhanced_dip_scan(print)
```

## Common Tasks

### Debugging Scan Issues
1. Check `error_log.txt` in the app directory
2. Run scanner directly in Python to see full traceback
3. Verify internet connectivity to Finviz

### Report Not Opening
1. Check `app/reports/` folder exists
2. Verify default browser handles .html files
3. Try opening report file manually

### API Key Issues
1. Verify key is set in Settings
2. Check Finviz Elite subscription is active
3. Key should be alphanumeric string

## Important Notes

- **Windows-only**: Paths like `C:\TradingBot` are hardcoded in some places
- **No automated tests**: All testing is manual
- **Rate limiting**: Scanners include `time.sleep(0.5)` between API calls
- **Cancellation**: Use `self.trend_cancelled` / `self.swing_cancelled` flags
- **Threading**: UI remains responsive during scans via callbacks

## Additional Documentation

- `CLAUDE_AI_GUIDE.md` - Complete rebuild guide with detailed architecture
- `README.txt` - User-facing installation and usage guide
- `RUNPOD_AI_GUIDE.txt` - Guide for building private AI system

## Code Quality Notes

Strengths:
- Modular architecture with clear separation of concerns
- Comprehensive error handling with logging
- Real-time progress feedback
- Portable design (works from USB drives)

Areas to be aware of:
- No requirements.txt (dependencies listed in CLAUDE_AI_GUIDE.md)
- API key stored in plain JSON (not encrypted)
- Limited input validation
- No async/threading for long operations (uses callbacks)
