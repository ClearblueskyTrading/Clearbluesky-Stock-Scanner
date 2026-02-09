# ClearBlueSky Stock Scanner — v7.8 Release Notes

**Release Date:** February 9, 2026

---

## API Rate-Limit Protection (All Scanners)

This release is focused entirely on **protecting all external API calls** across every scanner and module. No new features — just stability and safety.

### What Changed

Every module that calls Finviz, yfinance, SEC EDGAR, or apewisdom has been audited and hardened:

| Module | Before | After |
|--------|--------|-------|
| `finviz_safe.py` | 1.5s retry backoff | 3s/6s/9s exponential backoff |
| `velocity_scanner.py` | 8 parallel workers | Fully sequential + 0.3s delay |
| `smart_money.py` | 4 parallel workers | Fully sequential + 0.5s delay |
| `price_history.py` | 8 parallel workers | 3 workers + 0.2s delay |
| `market_intel.py` | 5 parallel workers | 2 workers + 0.3s delay |
| `premarket_volume_scanner.py` | 0.3s inter-ticker delay | 0.5s inter-ticker delay |
| `report_generator.py` | 0.5s inter-ticker delay | 0.8s inter-ticker delay |
| `enhanced_dip_scanner.py` | 0.5s inter-ticker, 2s news retry | 0.8s inter-ticker, 4s news retry |
| `insider_scanner.py` | 0.5s between calls | 1.0s between calls |
| `trend_scan_v2.py` | No delay between screener calls | 1.0s delay between calls |
| `ticker_enrichment.py` | Already sequential (v7.7) | No change needed |
| `watchlist_scanner.py` | Already sequential (v7.7) | No change needed |
| `accuracy_tracker.py` | Single batch download | No change needed |

### Philosophy

- **Safety over speed.** Scans may take a few minutes longer, but you won't get IP-banned by Finviz or rate-limited by yfinance/SEC EDGAR.
- **No parallel workers hammering APIs.** Most modules now run sequentially with polite delays.
- **Exponential backoff on retries.** Failed requests wait progressively longer before retrying.

### Upgrade

Drop-in replacement — no config changes needed. Just replace the `app/` folder.

---

*ClearBlueSky Stock Scanner — Built with Claude AI*
*GitHub: https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner*
