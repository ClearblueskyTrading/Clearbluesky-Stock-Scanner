# ClearBlueSky Stock Scanner v7.3 — Release Notes

**Release date:** February 8, 2026

---

## What's New

### Market Intelligence

The AI now gets live market context before analyzing your scan results. A new `market_intel.py` module gathers data from 4 free sources in parallel (~3-5 seconds):

| Source | Data | API Key? |
|--------|------|----------|
| **Google News RSS** | ~24 headlines (Stock Market, Economy, Earnings) | No |
| **Finviz News** | ~24 curated financial news + blog headlines | No |
| **Sector Performance** | 11 sectors — today, week, month, quarter, YTD | No |
| **Market Snapshot** | SPY, QQQ, DIA, IWM, GLD, USO, TLT, VIX + daily change | No |

This data is:
- Injected into the AI prompt as a "MARKET INTELLIGENCE" section
- Saved in the JSON analysis package (`market_intel` field)
- Included in the text report body

Toggle on/off in **Settings → Market Intelligence** (on by default).

### RunPod / Multi-LLM Guide

The User Manual now includes a section on running ClearBlueSky's JSON output through self-hosted LLMs on RunPod or local GPUs. Covers:
- Architecture for sending to 3-5 models in parallel
- vLLM and Ollama setup instructions
- Python script for multi-model consensus
- Cost comparison (OpenRouter vs RunPod vs local)

### UI Cleanup

- **"Velocity" → "Leveraged"** — Index dropdown renamed to "Leveraged (high-conviction)" throughout the UI and docs. Scanner internal IDs unchanged.
- **Button layout** — Bottom buttons reorganized into equal-width grid (3 rows × 4 columns). Window height increased to prevent cutoff.
- **Manual button** — Renamed from "README" to "Manual"; opens USER_MANUAL.md.

---

## Files Changed

| File | Change |
|------|--------|
| `app/market_intel.py` | **NEW** — Market Intelligence module |
| `app/app.py` | v7.3, button grid layout, Manual button, Leveraged rename, Market Intel toggle in Settings |
| `app/report_generator.py` | Integrated market_intel into AI prompt, JSON, and text report |
| `app/scan_settings.py` | Added `use_market_intel` default (true) |
| `app/emotional_dip_scanner.py` | Renamed Velocity → Leveraged in index label |
| `app/enhanced_dip_scanner.py` | Renamed Velocity → Leveraged in docstring |
| `app/requirements.txt` | Added `feedparser>=6.0` |
| `README.md` | Rewritten for v7.3 |
| `USER_MANUAL.md` | Added Market Intelligence (§9), RunPod (§14), updated scanner names |
| `app/README.md` | Updated to v7.3 |
| `app/CHANGELOG.md` | Added v7.3 entry |
| `INSTALL.bat` | Updated version |

---

## Upgrade Notes

- **New dependency:** `feedparser>=6.0` — Run `pip install feedparser` or `pip install -r app/requirements.txt`.
- **No config migration needed** — `use_market_intel` defaults to `true` for new and existing users.
- **In-app updater** will handle the upgrade automatically if you use Update from v7.2.
