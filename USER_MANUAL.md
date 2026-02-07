# ClearBlueSky Stock Scanner v7.2 — User Manual

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Main Interface](#2-main-interface)
3. [Scanners — What They Do and When to Use Them](#3-scanners)
4. [Scanner Config (Per-Scanner Settings)](#4-scanner-config)
5. [Quick Lookup](#5-quick-lookup)
6. [Watchlist](#6-watchlist)
7. [Settings (API Keys and Options)](#7-settings)
8. [Reports and AI Analysis](#8-reports-and-ai-analysis)
9. [Import / Export Config](#9-import--export-config)
10. [Update and Rollback](#10-update-and-rollback)
11. [Keyboard Shortcuts](#11-keyboard-shortcuts)
12. [Scoring System](#12-scoring-system)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Getting Started

### Installation

1. Run `INSTALL.bat` (Windows) — it installs Python and all dependencies automatically.
2. Or manually: install Python 3.10+, then run `pip install -r app/requirements.txt`.
3. Launch with `python app/app.py` or double-click `app/RUN.bat`.

### First Launch

- The app opens a compact GUI window. No API keys are required to run scanners.
- Optional: Open **Settings** to add API keys for enhanced features (AI analysis, news sentiment, etc.).

### What You Get Per Scan

Every scan produces up to 3 files in the `reports/` folder:

| File | Description |
|------|-------------|
| `*.pdf` | Visual PDF report with scores, news, TA data, and the AI trading directive |
| `*.json` | Machine-readable analysis package — paste into any AI chat with "follow the instructions in this JSON" |
| `*_ai.txt` | AI-generated analysis (only if OpenRouter API key is configured) |

---

## 2. Main Interface

### Stock Scanner Section

- **Scan dropdown** — Select which scanner to run (7 options).
- **Index dropdown** — Choose the stock universe:
  - **S&P 500** — ~500 large-cap stocks
  - **Russell 2000** — ~2000 small-cap stocks
  - **ETFs** — Exchange-traded funds
  - **Velocity (high-conviction)** — Fixed list of 17 high-volume tickers (TQQQ, NVDA, TSLA, etc.)
- **Run Scan** — Starts the selected scan in the background. The GUI stays responsive.
- **Stop** — Cancels a running scan.
- **Config** — Opens per-scanner settings (sliders/toggles specific to the selected scanner).
- **Run all scans** — Checkbox that runs all 7 scanners in sequence with 60-second delays between them to respect API rate limits. May take 20+ minutes.

### OpenRouter Status Line

Below "Run all scans" you'll see the AI status:

- `AI: $9.82 credit · Model: gemini-3-pro-preview` — Key works, showing remaining credit
- `AI: Key active · Model: gemini-3-pro-preview` — Key works but credits can't be queried
- `AI: No API key set · Model: gemini-3-pro-preview` — No key configured (scans still work, just no AI analysis)

### Progress Bar and Status

Shows real-time progress during scans: ticker count, current phase, elapsed time.

---

## 3. Scanners

### Trend — Long-term

**What it does:** Finds stocks in strong uptrends using moving average stacking (SMA20 > SMA50 > SMA200), quarterly/monthly/weekly performance, and relative volume.

**Best time to run:** After market close (4:00 PM ET) or anytime — uses daily data.

**Index options:** S&P 500, Russell 2000, ETFs.

**Use case:** Finding stocks with institutional momentum for swing or position trades.

---

### Swing — Dips

**What it does:** Finds emotional (non-fundamental) dip candidates — stocks down 1.5–4% on high relative volume with no fundamental red flags. Checks analyst ratings, upside to price target, SMA200 position, and RSI.

**Best time to run:** 2:30–4:00 PM ET (emotional selling peaks in the last 90 minutes).

**Index options:** S&P 500, Russell 2000, ETFs, Velocity (high-conviction).

**Use case:** Buying 1–5 day bounce plays on quality stocks that dipped on emotion, not fundamentals.

---

### Watchlist

**What it does:** Monitors your personal watchlist tickers. Two modes:
- **Down X% today** — Only shows watchlist stocks down at least X% from today's open.
- **All tickers** — Shows all watchlist stocks with current data.

**Best time to run:** Anytime during market hours for real-time monitoring.

**Index options:** N/A (uses your watchlist).

**Use case:** Tracking your existing positions or stocks you're watching for entry.

---

### Velocity Barbell

**What it does:** Sector-based momentum scanner. Identifies the hottest sector, then suggests a "barbell" pair: a Foundation stock (solid underlying) and a Runner (leveraged ETF for that sector). Also has a "Single Shot" mode for one leveraged idea.

**Best time to run:** 10:00 AM – 2:00 PM ET (after initial volatility settles, sector trends are clearer).

**Index options:** N/A (sector-based, auto-selects universe).

**Use case:** Leveraged intraday or 1–3 day sector momentum plays.

---

### Insider — Latest

**What it does:** Pulls the latest SEC insider transactions from Finviz. Can filter by: latest buys, latest sales, top of the week, or top owner trades.

**Best time to run:** Anytime — uses filed SEC data (not real-time).

**Index options:** N/A.

**Use case:** Finding stocks where insiders are buying heavily — a long-term bullish signal.

---

### Pre-Market

**What it does:** Scans for stocks with unusual pre-market volume, gap percentage, and dollar volume. Tracks sector heat.

**Best time to run:** 7:00–9:25 AM ET (pre-market session).

**Index options:** S&P 500, Russell 2000, ETFs.

**Use case:** Identifying stocks likely to move at the open based on pre-market activity.

---

### Velocity Pre-Market Hunter

**What it does:** Advanced pre-market scanner that scores 4 specific signal types:
- **Gap Recovery** — Stock gapped down 1.5–4%, showing recovery in pre-market
- **Institutional Accumulation** — Small gap, high PM volume, strong prior close
- **Breakout** — Price above Bollinger upper band with volume
- **Gap-and-Go** — Gap up 2%+, holding the gap with volume

Each ticker is graded A+ through F. Only A+, A, and B grades get entry plans with specific entry zones, targets, and stop-losses.

**Best time to run:** 7:00–9:25 AM ET.

**Index options:** S&P 500, Russell 2000, ETFs, Velocity (high-conviction).

**Use case:** Pre-market setup identification with specific trade plans.

---

## 4. Scanner Config

Click the **Config** button next to the scan dropdown to open per-scanner settings. Each scanner has different parameters:

### Trend Config
| Setting | Default | Description |
|---------|---------|-------------|
| Min Score | 70 | Minimum trend score (0–100) to include in results |
| Min Quarter % | 10 | Minimum quarterly performance percentage |
| Min Price $ | 5 | Exclude penny stocks below this price |
| Max Price $ | 500 | Exclude very high-priced stocks |
| Min Avg Vol (K) | 500 | Minimum average daily volume in thousands |
| Require MA Stack | On | Require SMA20 > SMA50 > SMA200 |

### Swing Config
| Setting | Default | Description |
|---------|---------|-------------|
| Min Score | 65 | Minimum emotional dip score |
| Min Dip % | 1.5 | Minimum dip from open to qualify |
| Max Dip % | 4.0 | Maximum dip (larger dips may be fundamental) |
| Min Rel Vol | 1.8 | Minimum relative volume (conviction indicator) |
| Min Upside % | 10.0 | Minimum analyst upside to price target |
| Above SMA200 | On | Require stock above 200-day moving average |
| Require Buy rating | On | Require analyst Buy/Strong Buy rating |
| Min/Max Price | 5/500 | Price range filter |

### Pre-Market Config
| Setting | Default | Description |
|---------|---------|-------------|
| Min Score | 70 | Minimum pre-market score |
| Min PM Vol (K) | 100 | Minimum pre-market volume (thousands) |
| Min Rel Vol | 2.0 | Minimum relative volume vs average |
| Min Gap % | 2.0 | Minimum gap from prior close |
| Max Gap % | 15.0 | Maximum gap (avoid extreme moves) |
| Min $ Vol (K) | 500 | Minimum dollar volume (thousands) |
| Vol/Float | 0.01 | Minimum volume-to-float ratio |
| Track sector heat | On | Include sector context in report |

### Watchlist Config
| Setting | Default | Description |
|---------|---------|-------------|
| Filter | Down X% | "down_pct" = only show stocks down X% today; "all" = show everything |
| Min % down | 5 | Minimum percentage down from open (when filter = down_pct) |

### Velocity Barbell Config
| Setting | Default | Description |
|---------|---------|-------------|
| Min sector % | 0.0 | Minimum sector move (up or down) to trigger |
| Theme | auto | "auto" picks barbell or single shot; "barbell" = Foundation + Runner; "single_shot" = one leveraged idea |

### Insider Config
| Setting | Default | Description |
|---------|---------|-------------|
| Insider view | latest | Which insider data to pull (latest, latest buys, latest sales, top week, etc.) |
| Min Score | 0 | Minimum score for the report (0 = include all) |

### Velocity Pre-Market Hunter
No configurable parameters — uses a fixed scoring algorithm. Select the stock universe via the Index dropdown.

---

## 5. Quick Lookup

Enter 1–5 ticker symbols (comma or space separated) in the Quick Lookup box and click **Report**.

**Example:** `AAPL, MSFT, NVDA` or `TSLA AMZN`

This generates an instant PDF report for those specific tickers without running a full scan. Useful for:
- Researching a stock someone mentioned
- Getting a quick AI analysis of your current holdings
- Generating a report before opening a position

The report runs in the background — the GUI stays responsive.

---

## 6. Watchlist

Click **Watchlist** to manage your personal stock list (up to 200 tickers).

- **Add** — Type a ticker and click Add
- **Remove** — Select a ticker and click Remove
- **Import CSV** — Import from a Finviz CSV export (File > Export on finviz.com)

**How it works during scans:** When any scanner finds a stock that's on your watchlist:
- Two alert beeps play
- The stock is marked as **WATCHLIST** in the report
- It appears at the top of the results

---

## 7. Settings

Click **Settings** to configure API keys and app options.

### Finviz API Key
- **What:** API key from finviz.com (Elite plan)
- **Required?** No — the app scrapes Finviz by default. An API key avoids rate limits.
- **Get one:** https://finviz.com/elite.ashx

### OpenRouter API (AI Analysis)
- **What:** API key from openrouter.ai — one key works for all AI models.
- **Required?** No — scanners work without it. Only needed for AI-generated `*_ai.txt` analysis.
- **Get one:** https://openrouter.ai/keys
- **Models:**
  - **Gemini 3 Pro Preview** (credits) — Best quality, costs ~$0.01–0.05 per analysis
  - **DeepSeek R1 T2 Chimera** (free) — Free, good quality, no credits needed

### Alpha Vantage API Key
- **What:** API key for news sentiment headlines per ticker.
- **Required?** No — reports work without it. Adds extra headline data when available.
- **Get one:** https://www.alphavantage.co/support/#api-key (free tier available)

### RAG Books
- **What:** Folder containing .txt or .pdf files (trading books, strategies, etc.)
- **How it works:** Click "Build RAG Index" to create a vector database. When enabled, relevant passages from your books are included in the AI prompt for context.
- **Required?** No — purely optional enhancement.

### Other Settings
| Setting | Description |
|---------|-------------|
| Include TA in report | Add technical analysis data (RSI, MAs, Bollinger) to reports |
| Include SEC insider context | Add insider trading context to AI analysis |
| Chart images in AI analysis | Send candlestick chart images to multimodal AI models |
| Reports folder | Where PDF/JSON files are saved (default: `app/reports/`) |
| Play alarm on complete | Beep when a scan finishes |
| Alarm sound | Choose: beep, asterisk, or exclamation |

---

## 8. Reports and AI Analysis

### What's in a Report

Every scan generates a PDF with:

1. **Header** — Scan type, timestamp, ticker count
2. **Per-ticker sections** — Score, price, change %, news headlines, analyst rating, technical data
3. **AI Trading Directive** — The "Elite Swing Trader System Prompt" is embedded in every report:
   - 1–5 day maximum hold (optimal 1–2 days)
   - S&P 500 stocks + leveraged ETFs
   - Entry/exit windows (8AM–8AM cycle)
   - The 1-2-5 exit framework
   - Position sizing by conviction score

### JSON Analysis Package

The `*.json` file contains the same data in machine-readable format with an `instructions` field. You can paste this into any AI (ChatGPT, Claude, Gemini, etc.) and say: *"Follow the instructions in this JSON and give me your analysis."*

### AI Analysis (_ai.txt)

If you have an OpenRouter API key configured, the app automatically sends the JSON package to the selected AI model and saves the response as `*_ai.txt`. This file opens automatically after the scan.

### GitHub Attribution

All reports include a link to the releases page:
https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases

---

## 9. Import / Export Config

Click **Config** (bottom button row) to back up or restore your full configuration.

- **Export** — Saves `user_config.json` to a location you choose. Includes all settings and API keys.
- **Import** — Loads a previously exported config file. Overwrites current settings.

**Use cases:**
- Backup before updating
- Transfer settings to a new PC
- Share settings (remove API keys first!)

**Warning:** The exported file contains your API keys in plain text. Keep it secure.

---

## 10. Update and Rollback

### Update

Click **Update** to download and install the latest release from GitHub.

1. Your current version is automatically backed up first
2. The update is downloaded, verified (integrity check), and applied
3. Your `user_config.json` is **never overwritten** — all your settings and API keys are preserved
4. Restart the app to use the new version

### Rollback

Click **Rollback** to restore from the last backup if an update causes issues.

1. Select Rollback and confirm
2. Your settings are preserved (just like updates)
3. Restart the app

---

## 11. Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Enter** | Run Scan |
| **Escape** | Stop Scan |
| **F1** | Open Help |

---

## 12. Scoring System

All scanners use a 0–100 scoring system:

| Score Range | Grade | Meaning |
|------------|-------|---------|
| 90–100 | Elite | Highest conviction — rare, strong setup |
| 70–89 | Strong | Good setup, worth considering |
| 60–69 | Decent | Meets minimum criteria, lower conviction |
| Below 60 | Skip | Does not meet quality threshold |

### Velocity Pre-Market Hunter Grades

| Grade | Score | Position Size |
|-------|-------|--------------|
| A+ | 85+ | $5,000 |
| A | 75–84 | $4,000 |
| B | 65–74 | $3,000 |
| C | 55–64 | $0 (watch only) |
| F | Below 55 | Skip |

---

## 13. Troubleshooting

### "No results found"
- Normal — not every scan finds qualifying stocks. The filters are intentionally strict.
- Try a broader index (Russell 2000 has more stocks than S&P 500).
- Lower the Min Score in Config.
- For Swing, try running at 2:30–4:00 PM when emotional selling peaks.

### Scan takes a long time
- Some scanners make many API calls (one per ticker). Russell 2000 scans take longer.
- "Run all scans" adds 60-second delays between scanners to avoid rate limits.
- The Velocity Pre-Market Hunter uses parallel scanning (8 threads) for speed.

### OpenRouter / AI analysis fails
- Check your API key in Settings
- The credit line below "Run all scans" shows your balance
- The app retries up to 3 times on network errors
- Try the free DeepSeek model if you're out of credits

### Reports not opening
- Check the Reports folder path in Settings
- Click **Reports** button to open the folder directly
- PDF generation requires `reportlab` — if not installed, reports save as TXT

### App won't start
- Run `pip install -r app/requirements.txt` to install all dependencies
- Make sure Python 3.10+ is installed
- On Linux/macOS: install `python3-tk` (e.g., `sudo apt install python3-tk`)

### Auto-cleanup
- Reports older than 30 days are automatically cleaned up on startup.

---

## File Reference

| File | Purpose |
|------|---------|
| `app/app.py` | Main GUI application |
| `app/user_config.json` | Your settings and API keys (never shared or overwritten by updates) |
| `app/scan_types.json` | Scanner definitions (which scanners appear in dropdown) |
| `app/scan_presets.json` | Named presets for quick config switching |
| `app/reports/` | Generated PDF, JSON, and AI analysis files |
| `app/requirements.txt` | Python dependencies |

---

*ClearBlueSky Stock Scanner v7.2 — Made with Claude AI*
*https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases*
