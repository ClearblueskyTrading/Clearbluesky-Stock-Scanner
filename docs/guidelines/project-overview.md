# ClearBlueSky Scanner — Project Overview

## Purpose

Stock scanner app (Trend, Swing/Dip, Watchlist) with PDF/JSON reports and OpenRouter AI analysis. Python, Tkinter, Finviz, yfinance, optional Alpha Vantage.

## Key Paths

- **App (this repo):** `d:\cursor\app\` (or `D:\scanner\app\`)
- **RAG / shared memory:** `D:\scanner\velocity_memory\`
- **Knowledge base:** `C:\Users\EricR\OneDrive\Desktop\Claude AI Knowledge\`
- **Reports:** `app/reports/`

## Rules

- API keys only in `user_config.json` or external api keys file — never in git or docs.
- Pre-commit: scan for secrets (see .cursor/rules/pre-commit-security.mdc).
- Rate-limit safety: no aggressive parallel workers; polite delays for Finviz, yfinance, SEC EDGAR.
