# ClearBlueSky Stock Scanner v7.6 - Stability & QA Release

## What's Fixed

**Scanner Reliability**
- All scanners now use timeout-protected Finviz calls (30s max per ticker) — no more indefinite hangs
- New shared `finviz_safe.py` module with automatic retry on rate limits (429), timeouts, and connection errors
- Premarket scanner: cancel button works mid-scan, stops early after 10 consecutive failures
- All `yfinance` downloads have 30-second timeouts
- All `ThreadPoolExecutor` futures have 60-second timeouts

**GUI Stability**
- Closing the window during a scan no longer crashes the app (TclError protection on all widget updates)
- Progress bar properly resets when no qualifying stocks are found (was stuck at 85%)
- Premarket and Pre-Market Hunter scanners now use min_score=0 by default (internal scoring is sufficient)

**Data Safety**
- Division-by-zero protection added to accuracy tracker, history analyzer, and market intel module

**AI Prompt Optimization**
- Reduced the trading directive sent to AI from 260 lines to 35 lines
- AI gets output format and required sections only — no longer receives your full trading playbook every scan
- Faster AI responses, lower token cost

## Upgrade Notes

Drop-in replacement for v7.5. No config changes needed — existing `user_config.json` is preserved.
