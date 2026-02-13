# ClearBlueSky Stock Scanner — Cursor AI Guide

Guide for implementing and modifying the scanner within **Cursor**. Use `@CURSOR_AI_GUIDE.md` or `@docs/` to pull this into context.

---

## Workspace Rules

- **D:\cursor** — Development workspace: integrations, scripts, Cursor rules, scanner (`app/`). **All changes go here.**
- **D:\scanner** — Clean 7.8 install. **Never modify or use D:\scanner.**

---

## Project Overview

**Name:** ClearBlueSky Stock Scanner  
**Version:** 7.89  
**Purpose:** Scan stocks for trading ideas; generate PDF + JSON reports with optional OpenRouter AI analysis  

**Tech stack:** Python 3.10+, Tkinter, Finviz, yfinance, reportlab, ChromaDB (RAG)

### Scanners (3)

| Scanner | Best for |
|---------|----------|
| **Velocity Trend Growth** | Sector-first momentum (20d/50d) |
| **Swing – Dips** | Emotional dips, 1–5 day holds |
| **Watchlist** | Down % today (0–X%) or All tickers |

---

## Key Paths

| What | Path |
|------|------|
| Scanner app | `D:\cursor\app\` |
| Main app | `D:\cursor\app\app.py` |
| Config | `D:\cursor\app\user_config.json` |
| Cursor rules | `D:\cursor\.cursor\rules\` |
| Reports | `D:\cursor\app\reports\` (or per user config) |

---

## Running the Scanner

**GUI (from D:\cursor\app):**
```powershell
cd D:\cursor\app; python app.py
```

**CLI (for Cursor, automation, no GUI):**
```powershell
cd D:\cursor\app
python scanner_cli.py --scan velocity_trend_growth
python scanner_cli.py --scan swing --index etfs
python scanner_cli.py --scan watchlist --watchlist-file path\to\tickers.txt
```
Or: `CLI.bat --scan velocity_trend_growth` (Windows)

Options: `--index sp500|etfs`, `--reports-dir PATH`, `--watchlist-file PATH`. See **app/CLI_FOR_CLAUDE.md**.

---

## Architecture

```
User → app.py (GUI) or scanner_cli.py (CLI) → Scanner (velocity_trend_growth, emotional_dip_scanner, watchlist_scanner)
    → breadth.py (fetch S&P 500 or ETFs: Finviz or CSV fallback)
    → report_generator.py → PDF + JSON + _ai.txt (5-model OpenRouter consensus, charts always)
```

---

## Cursor Rules (`.cursor/rules/`)

- **user-context.mdc** — 3 AIs rule, paths, voice, Alpaca
- **trade-discussion-sources.mdc** — Use Finviz + Alpaca for prices
- **alpaca-rate-limits.mdc** — API limits
- **project-boundaries.mdc** — Never touch D:\scanner

---

## Common Modifications

**Change scan params:** `app/scan_settings.py` (SCAN_PARAM_SPECS) + `app/user_config.json`  
**Add fallback data source:** `app/breadth.py`  
**Change report layout:** `app/report_generator.py`  
**Update version:** `app/app.py` (VERSION), `README.md`, `INSTALL.bat`

---

## Quick Prompts for Cursor

- *"Run Velocity Trend Growth scan from D:\cursor\app"*
- *"Check Alpaca positions/orders"* → `python D:\cursor\scripts\check_alpaca_orders.py`
- *"Create AI report from my latest scan"* → Read JSON from reports/, produce TIER 1/2/3 + AVOID

---

*ClearBlueSky v7.89 — Cursor AI Guide*
