# ClearBlueSky Stock Scanner — v7.84 Release Notes

**Release Date:** February 10, 2026

---

## Watchlist Scanner

### Filter: 0–25% down range

- **Before:** Slider = min % down. Filter showed tickers down between X% and 25%.
- **After:** Slider = max % down. Filter shows tickers down between 0% and X%.
- Example: Slider at 5 → tickers down 0.01% to 5% (shallow dips). Slider at 25 → 0–25% (full range).

### Slider range

- 0–25% (was 0.5–25%). Full flexibility for shallow or deep dips.

### Filter options

| Option | Description |
|--------|-------------|
| Down % today | Only tickers down today within 0–X% (X = slider) |
| All tickers | Every watchlist ticker, no change filter |

### UI improvements

- **Max % down slider** disabled when "All tickers" selected.
- **Hints** — Filter and slider hint text explain behavior.
- **Backward compatible** — Config still stores `down_pct` / `all`.

---

## run_watchlist_10.py

Added helper script in `app/` to run watchlist scan with 10% down filter from CLI:

```bash
cd app
python run_watchlist_10.py
```

---

## Upgrade

Drop-in replacement — no config changes needed. Your `user_config.json` is never overwritten.

---

*ClearBlueSky Stock Scanner — Built with Claude AI*
*GitHub: https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner*
