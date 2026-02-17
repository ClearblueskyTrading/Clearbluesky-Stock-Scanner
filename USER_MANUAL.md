# ClearBlueSky Stock Scanner v7.90 — User Manual

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
9. [Market Intelligence](#9-market-intelligence)
10. [Ticker Enrichment (v7.7)](#10-ticker-enrichment)
11. [Import / Export Config](#11-import--export-config)
12. [Update and Rollback](#12-update-and-rollback)
13. [Keyboard Shortcuts](#13-keyboard-shortcuts)
14. [Scoring System](#14-scoring-system)
15. [Running on RunPod / Multi-LLM Deployment](#15-running-on-runpod--multi-llm-deployment)
16. [Troubleshooting](#16-troubleshooting)

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

Every scan produces a single **.md** file in the `reports/` folder:

| File | Description |
|------|-------------|
| `*.md` | Single Markdown report: YAML frontmatter (structured data), report body (per-ticker data, market breadth, price history), and AI analysis (when OpenRouter key is set). 6-model consensus (DeepSeek, Arcee Trinity, Gemini Vision, Llama, GPT-OSS, StepFun) + optional Google. Chart data included as JSON (30-day OHLC, recent daily bars) — no chart images. |

---

## 2. Main Interface

### Stock Scanner Section

- **Scan dropdown** — Select which scanner to run (3 options: Velocity Trend Growth, Swing, Watchlist).
- **Universe** — Toggle between **S&P 500** or **ETFs** (own row for visibility). Velocity and Swing use the selected universe; Watchlist uses your watchlist.
- **Run Scan** — Starts the selected scan in the background. The GUI stays responsive.
- **Stop** — Cancels a running scan.
- **Config** — Opens per-scanner settings (sliders/toggles specific to the selected scanner).
- **Run all scans** — Checkbox that runs all 3 scanners in sequence with 60-second delays between them to respect API rate limits. Takes ~15 minutes.

### AI Status Line

Below "Run all scans" you'll see the AI connection status:

- **AI: Connected** (green) — OpenRouter API key works; AI analysis will run.
- **AI: No API key set** — No key configured (scans still work, just no AI analysis).
- **AI: Key invalid or expired** (red) — Key rejected; check Settings and regenerate at openrouter.ai/keys.

### Progress Bar and Status

Shows real-time progress: step labels (Report: 5/12 tickers, Enrichment..., AI: Meta Llama (1/3)...) and elapsed time (e.g. **• 2:15**).

---

## 3. Scanners

### Velocity Trend Growth

**What it does:** Momentum scan with sector-first logic. Ranks 11 GICS sectors by N-day return (sector SPDRs), then scans only S&P 500 stocks + ETFs in the top 4 leading sectors. Filters by target return %, optional beat SPY, volume, MA stack, RSI. Includes SEC insider data and sector heat in output.

**Best time to run:** After market close (4:00 PM ET) or anytime — uses daily data.

**Index:** S&P 500 + curated ETFs (automatic).

**Use case:** Finding momentum leaders in sectors that are already moving. Faster than full-market scan (~160 tickers vs ~400).

---

### Swing — Dips

**What it does:** Finds emotional (non-fundamental) dip candidates — stocks down 1–5% on high relative volume with no fundamental red flags. Checks analyst ratings, upside to price target, SMA200 position, and RSI. Enriched with earnings date warnings, news sentiment flags, live price, and leveraged ETF suggestions. Includes SEC insider data for confirmation.

**Best time to run:** 2:30–4:00 PM ET (emotional selling peaks in the last 90 minutes).

**Index options:** S&P 500, ETFs.

**Use case:** Buying 1–5 day bounce plays on quality stocks that dipped on emotion, not fundamentals. Earnings warnings prevent entries before risky catalysts.

---

### Watchlist

**What it does:** Monitors your personal watchlist tickers. Two modes:
- **Down % today** — Only shows watchlist stocks down within the 0–X% range (X = slider max).
- **All tickers** — Shows all watchlist stocks with current data.

**Best time to run:** Anytime during market hours for real-time monitoring.

**Index options:** N/A (uses your watchlist).

**Use case:** Tracking your existing positions or stocks you're watching for entry.

---

### Pre-Market *(removed in v7.88)*

**What it did:** Combined pre-market scanner that ran both volume analysis and velocity gap analysis in a single pass. Scans for unusual pre-market volume, gap percentage, dollar volume, and sector heat. Also scores 4 velocity signal types: Gap Recovery, Institutional Accumulation, Breakout, and Gap-and-Go. Enriched with earnings warnings, news flags, and leveraged ETF suggestions.

**Best time to run:** 7:00–9:25 AM ET (pre-market session).

**Index options:** S&P 500, ETFs.

**Use case:** Identifying stocks likely to move at the open based on pre-market activity, with specific setup grades and leveraged alternatives.

---

## 4. Scanner Config

Click the **Config** button next to the scan dropdown to open per-scanner settings. Each scanner has different parameters:

### Velocity Trend Growth Config
| Setting | Default | Description |
|---------|---------|-------------|
| Trend Days | 20 | 20 or 50 trading days |
| Target Return % | 5 | Minimum N-day return (1–300%) |
| Min/Max Price $ | 25/600 | Price range filter |
| Require beats SPY | Off | Only stocks outperforming SPY |
| Min Volume (K) | 100 | Minimum average volume |
| Volume above 20d avg | Off | Accumulation confirmation |
| Require MA stack | Off | Price > EMA10 > EMA20 > EMA50 |
| RSI min/max | 0/100 | RSI band (0/100 = off) |

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

### Pre-Market Config *(removed in v7.88)*
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
| Filter | Down % today | "down_pct" = only show stocks down in the 0–X% range today; "all" = show everything |
| Max % down | 5 | Maximum percentage down in the 0–X% range (when filter = down_pct) |

*Note: Pre-Market scanner was removed in v7.88. Velocity Barbell and Insider were folded into other scanners in v7.7. Current scanners: Velocity Trend Growth, Swing, Watchlist.*

---

## 5. Quick Lookup

Enter 1–5 ticker symbols (comma or space separated) in the Quick Lookup box and click **Report**.

**Example:** `AAPL, MSFT, NVDA` or `TSLA AMZN`

This generates an instant .md report for those specific tickers without running a full scan. Useful for:
- Researching a stock someone mentioned
- Getting a quick AI analysis of your current holdings
- Generating a report before opening a position

The report runs in the background — the GUI stays responsive.

---

## 6. Watchlist

Click **Watchlist** to manage your personal stock list (up to 400 tickers).

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
- **Required?** No — scanners work without it. Only needed for AI analysis in the .md report.
- **Get one:** https://openrouter.ai/keys
- **Models:** 3 free models (Llama 3.3 70B, OpenAI GPT-OSS 120B, DeepSeek R1T2 Chimera). Consensus analysis included in the .md file. Chart data (30-day OHLC, recent daily bars) is in the JSON sent to the AI — no chart images.

### Alpha Vantage API Key
- **What:** API key for news sentiment headlines per ticker.
- **Required?** No — reports work without it. Adds extra headline data when available.
- **Get one:** https://www.alphavantage.co/support/#api-key (free tier available)

### Market Intelligence
- **What:** Automatically gathers Google News headlines, Finviz financial news, sector performance, and market snapshot (SPY, QQQ, VIX, etc.) before AI analysis.
- **Required?** No API key needed — all sources are free.
- **Toggle:** Enable/disable in Settings. On by default. Adds ~5 seconds to AI report generation.
- **See:** [Section 9: Market Intelligence](#9-market-intelligence) for details.

### RAG Books
- **What:** Folder containing .txt or .pdf files (trading books, strategies, etc.)
- **How it works:** Click "Build RAG Index" to create a vector database. When enabled, relevant passages from your books are included in the AI prompt for context.
- **Required?** No — purely optional enhancement.

### Other Settings
| Setting | Description |
|---------|-------------|
| Include TA in report | Add technical analysis data (RSI, MAs, Bollinger) to reports |
| Include SEC insider context | Add insider trading context to AI analysis |
| Reports folder | Where .md reports are saved (default: `app/reports/`) |
| Play alarm on complete | Beep when a scan finishes |
| Alarm sound | Choose: beep, asterisk, or exclamation |

---

## 8. Reports and AI Analysis

### What's in a Report

Every scan generates a single **.md** file with:

1. **YAML frontmatter** — Structured data: stocks (ticker, score, price, TA, etc.), market_breadth, market_intel, price_history_30d (with recent daily OHLC for chart-like data).
2. **Report body** — Per-ticker sections, score, price, change %, news headlines, analyst rating, technical data, Elite Swing Trader directive.
3. **AI Analysis** — When OpenRouter key is set: consensus from 6 OpenRouter models (DeepSeek, Arcee Trinity, Gemini Vision, Llama, GPT-OSS, StepFun) + optional Google AI. Chart data (30-day high/low/close, recent daily bars) is in the JSON sent to the AI — no chart images. The AI response is appended to the .md file.

### AI Consensus (6 models)

The app sends the analysis package to 6 free OpenRouter models: DeepSeek R1T2 Chimera, Arcee Trinity Large, Google Gemini 2.0 Flash (Vision), Meta Llama 3.3 70B, OpenAI GPT-OSS 120B, StepFun Step 3.5 Flash. Optional Google AI (gemini-2.5-flash) adds a 7th. A synthesis step produces a final summary. All models receive the same data including price history; no chart images are sent.

### GitHub Attribution

All reports include a link to the releases page:
https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases

---

## 9. Market Intelligence

When Market Intelligence is enabled (Settings toggle, on by default), the app automatically gathers live market context before sending data to the AI. This data is also saved in the JSON analysis package.

### What's Gathered

| Source | Data | API Key Needed? |
|--------|------|----------------|
| **Google News RSS** | ~24 headlines across Stock Market, Economy, and Earnings topics | No |
| **Finviz News** | ~24 curated financial news + blog headlines | No |
| **Sector Performance** | All 11 sectors with today/week/month/quarter/YTD changes | No |
| **Market Snapshot** | SPY, QQQ, DIA, GLD, USO, TLT, VIX — price + daily change | No |
| **Overnight Markets** | EWJ (Japan), FXI (China), EWZ (Brazil), EFA (Europe), EWG (Germany), EWU (UK), INDA (India), EWT (Taiwan), EWY (S. Korea) — price + daily change | No |

### How It's Used

1. **AI Prompt** — The market intel is injected as a "MARKET INTELLIGENCE" section at the top of the AI prompt, before the per-stock data. The AI uses this to understand:
   - Overall market direction (is SPY up or down? Is VIX elevated?)
   - Which sectors are leading/lagging (sector rotation)
   - Overnight/overseas market impact (gap risk from Asia/Europe sessions)
   - Breaking news that could affect trades
   - Economic/earnings headlines

2. **JSON Package** — The full market intel data is included in the `market_intel` field of the JSON file, so you can feed it to any AI or use it in your own analysis.

3. **Text Report** — Market snapshot, overnight markets, sector table, and headlines appear in the text body of the report.

### Performance

All 5 sources (news, Finviz, sectors, US markets, overnight markets) are fetched in parallel (~3–5 seconds total). If any source fails, the others still work.

---

## 10. Ticker Enrichment

New in v7.7 — after the initial scan data is gathered, each ticker is enriched with additional context before report generation and AI analysis.

### What's Added Per Ticker

| Enrichment | Description | Which Scanners |
|-----------|-------------|----------------|
| **Earnings Date Warning** | Flags like "EARNINGS TOMORROW", "EARNINGS THIS WEEK", "EARNINGS NEXT WEEK" | All scanners |
| **News Sentiment** | DANGER / NEGATIVE / POSITIVE / NEUTRAL from recent headlines | All scanners |
| **Live Price** | Current price stamped at report generation time | All scanners |
| **Leveraged Suggestion** | Matching leveraged ETF (e.g., TQQQ for QQQ-tracking stocks) | Swing only |
| **Insider Activity** | Recent SEC Form 4 insider buys/sales (owner, transaction type, value) | Velocity Trend Growth & Swing |

### How It's Used

- **AI Prompt** — Earnings warnings and news sentiment are appended to each ticker's data line. The AI is instructed to avoid entries before earnings and flag news risks.
- **Reports** — Enrichment data appears in both PDF and JSON outputs.
- **Leveraged Suggestions** — When a stock on the Swing scan has a leveraged ETF equivalent, the AI can suggest the leveraged play for higher-conviction entries.
- **Insider Data** — Heavy insider buying on a Velocity Trend Growth or Swing pick adds conviction. The AI references insider activity in its analysis.

### Performance

Enrichment runs in parallel with 4 workers after the main scan. Adds ~5–10 seconds depending on ticker count.

---

## 11. Import / Export Config

Click **Config** (bottom button row) to back up or restore your full configuration.

- **Export** — Saves `user_config.json` to a location you choose. Includes all settings and API keys.
- **Import** — Loads a previously exported config file. Overwrites current settings.

**Use cases:**
- Backup before updating
- Transfer settings to a new PC
- Share settings (remove API keys first!)

**Warning:** The exported file contains your API keys in plain text. Keep it secure.

---

## 12. Update and Rollback

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

## 13. Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Enter** | Run Scan |
| **Escape** | Stop Scan |
| **F1** | Open Help |

---

## 14. Scoring System

All scanners use a 0–100 scoring system:

| Score Range | Grade | Meaning |
|------------|-------|---------|
| 90–100 | Elite | Highest conviction — rare, strong setup |
| 70–89 | Strong | Good setup, worth considering |
| 60–69 | Decent | Meets minimum criteria, lower conviction |
| Below 60 | Skip | Does not meet quality threshold |

### Pre-Market Velocity Grades *(removed in v7.88)*

The velocity gap analysis portion of the Pre-Market scanner (removed) used to grade each signal:

| Grade | Score | Position Size |
|-------|-------|--------------|
| A+ | 85+ | $5,000 |
| A | 75–84 | $4,000 |
| B | 65–74 | $3,000 |
| C | 55–64 | $0 (watch only) |
| F | Below 55 | Skip |

---

## 15. Running on RunPod / Multi-LLM Deployment

The ClearBlueSky scanner is designed as a desktop app, but its JSON output is model-agnostic. You can use the generated analysis packages with **any LLM** — including self-hosted models on RunPod, together.ai, or your own GPU servers. This section explains how to scale the AI analysis beyond the built-in OpenRouter integration.

### Why Use RunPod / Self-Hosted LLMs?

- **Run multiple models in parallel** — Send the same JSON package to 3–5 different LLMs simultaneously and compare their analysis. One model might catch a risk another misses.
- **No per-token costs** — Pay for GPU time instead of per-token API pricing. Especially useful for large analysis packages.
- **Custom fine-tuned models** — Use models fine-tuned on financial data or your own trading history.
- **Privacy** — Your analysis data stays on your infrastructure.
- **No rate limits** — Run as many analyses as your GPUs can handle.

### Architecture

```
ClearBlueSky Scanner (desktop)
     │
     ├── Generates *.json analysis package (with market intel + instructions)
     │
     ▼
RunPod / GPU Server
     │
     ├── LLM #1 (e.g. Llama 3.3 70B) ──→ analysis_llama.txt
     ├── LLM #2 (e.g. Qwen 2.5 72B)  ──→ analysis_qwen.txt
     ├── LLM #3 (e.g. Mixtral 8x22B)  ──→ analysis_mixtral.txt
     └── LLM #4 (e.g. DeepSeek V3)    ──→ analysis_deepseek.txt
     │
     ▼
Consensus / Comparison
     │
     └── Combine results: majority vote on BUY/PASS, average scores,
         flag disagreements as "needs manual review"
```

### Step-by-Step Setup

**1. Generate the JSON package**

Run any scan in ClearBlueSky. The `*.json` file in `app/reports/` contains everything the AI needs: the `instructions` field (Elite Swing Trader System Prompt), per-ticker data, market intelligence, technical analysis, and news.

**2. Set up RunPod**

1. Create an account at [runpod.io](https://www.runpod.io/)
2. Deploy a GPU pod (A100 80GB or H100 recommended for 70B+ models)
3. Choose a template with vLLM, text-generation-inference (TGI), or Ollama pre-installed
4. Start the pod — it exposes an OpenAI-compatible API endpoint

**3. Deploy models**

With vLLM (recommended for throughput):

```bash
# On your RunPod pod
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.3-70B-Instruct \
  --port 8000 \
  --tensor-parallel-size 2
```

Or with Ollama (easier setup):

```bash
ollama pull llama3.3:70b
ollama pull qwen2.5:72b
ollama serve  # Exposes API on port 11434
```

**4. Send the JSON package to your models**

Write a simple Python script that reads the JSON and sends it to each model:

```python
import json
import requests

# Load the ClearBlueSky analysis package
with open("reports/Velocity_Trend_Growth_20260208_160000.json") as f:
    package = json.load(f)

system_prompt = package.get("instructions", "Analyze these stocks.")
user_content = json.dumps(package, indent=2)

# List of your RunPod endpoints (or local Ollama)
endpoints = [
    {"name": "Llama-3.3-70B", "url": "https://your-pod-id-8000.proxy.runpod.net/v1/chat/completions", "model": "meta-llama/Llama-3.3-70B-Instruct"},
    {"name": "Qwen-2.5-72B", "url": "https://your-pod-id-8001.proxy.runpod.net/v1/chat/completions", "model": "Qwen/Qwen2.5-72B-Instruct"},
]

for ep in endpoints:
    resp = requests.post(ep["url"], json={
        "model": ep["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 8192,
        "temperature": 0.3,
    })
    result = resp.json()["choices"][0]["message"]["content"]
    with open(f"analysis_{ep['name']}.txt", "w") as f:
        f.write(result)
    print(f"{ep['name']}: done")
```

**5. Compare results**

Read the output files from each model and look for:
- **Consensus picks** — Stocks that all models agree are BUY
- **Disagreements** — Where one model says BUY and another says PASS (investigate further)
- **Score spread** — If all models give 85+ on a stock, that's high conviction
- **Unique insights** — Each model may catch different news or technical patterns

### Cost Comparison

| Approach | Cost per scan (15 tickers) | Speed |
|----------|---------------------------|-------|
| OpenRouter (Gemini 3 Pro) | ~$0.03 | ~30 sec |
| OpenRouter (DeepSeek free) | $0.00 | ~45 sec |
| RunPod A100 (Llama 70B) | ~$0.02 (GPU time) | ~20 sec |
| RunPod H100 (4 models parallel) | ~$0.10 (GPU time) | ~25 sec for ALL 4 |
| Local RTX 4090 (Ollama) | $0.00 (electricity only) | ~60 sec |

### Tips

- **Start with OpenRouter** — The built-in integration is the easiest way to get AI analysis. Only move to RunPod if you need multi-model consensus or have high volume.
- **Use the JSON `instructions` field** — It contains the full Elite Swing Trader System Prompt. Any LLM that follows instructions well will produce structured analysis.
- **70B+ models recommended** — Smaller models (7B, 13B) often miss nuance in financial analysis. 70B+ models perform comparably to GPT-4/Claude for this task.
- **Batch processing** — If running multiple scans (e.g., all 3 scanners), collect all JSON files and send them to RunPod in one batch to minimize GPU idle time.
- **Serverless RunPod** — Use RunPod's serverless endpoints to avoid paying for idle GPUs. You're charged only when processing requests.

---

## 16. Troubleshooting

### "No results found"
- Normal — not every scan finds qualifying stocks. The filters are intentionally strict.
- Try ETFs index (broader universe than S&P 500).
- Lower the Min Score in Config.
- For Swing, try running at 2:30–4:00 PM when emotional selling peaks.

### Scan takes a long time
- Some scanners make many API calls (one per ticker). S&P 500 scans take longer than ETFs.
- "Run all scans" adds 60-second delays between scanners to avoid rate limits.
- *(Pre-Market scanner was removed in v7.88.)*

### OpenRouter / AI analysis fails
- Check your API key in Settings
- The AI status line shows: Connected (green), No key, or Invalid
- The app retries up to 3 times on network errors
- All 6 models are free — no credits required

### Reports not opening
- Check the Reports folder path in Settings
- Click **Reports** button to open the folder directly
- Reports are saved as .md (Markdown) — open with any text editor or browser

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
| `app/scan_types.json` | Scanner definitions (3 scanners) |
| `app/scan_settings.py` | Config specs, default values, and scan param definitions |
| `app/market_intel.py` | Market Intelligence module (Google News, Finviz, sectors, market snapshot, overnight markets) |
| `app/ticker_enrichment.py` | Earnings warnings, news sentiment, live price, leveraged suggestions |
| `app/insider_scanner.py` | SEC insider data — enrichment for Velocity Trend Growth & Swing |
| `app/report_generator.py` | .md report generation + AI prompt construction |
| `app/finviz_safe.py` | Timeout-protected Finviz wrapper used by all scanners |
| `app/reports/` | Generated .md report files (YAML + body + AI analysis) |
| `app/requirements.txt` | Python dependencies |

---

*ClearBlueSky Stock Scanner v7.90*
*https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases*
