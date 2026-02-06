# Scanner Naming & Duplicate Audit (v7.0)

## Names vs. What They Do

| Label | Scanner | What it does | Name OK? |
|-------|---------|--------------|----------|
| **Trend - Long-term** | trend | Uptrending stocks (above SMA20/50/200, volume). Best after close. | ✓ |
| **Swing - Dips** | swing | Index stocks down X% today → full quality analysis (news, analyst, targets) → scored. Best 2:30–4 PM. | ✓ |
| **Emotional Dip** | emotional | Same dip pool as Swing → filter for **emotional-only** (news sentiment, above SMA200, buy rating, upside). Best ~3:30 PM. | ✓ |
| **Watchlist 3pm** | watchlist | Watchlist tickers **down X% today** (slider 1–25%). Best ~3 PM. | ✓ |
| **Watchlist - All tickers** | watchlist_tickers | **All** watchlist tickers, no filters. Snapshot of every ticker. | ✓ |
| **Velocity Barbell** | velocity_leveraged | Sector proxy ETFs → theme (clear/uncertain) → Foundation + Runner or Single Shot. | ✓ |
| **Insider - Latest** | insider | Latest insider transactions from Finviz (configurable: latest, top week, etc.). | ✓ |
| **Pre-Market** | premarket | Pre-market volume/gap scan. Best 7–9:25 AM. | ✓ |

All names match what the scanners do. No renaming needed.

---

## Shared Code (Not Duplicate Functions)

- **Swing** and **Emotional Dip** both use `get_sp500_dips()` from `enhanced_dip_scanner` to get stocks down X% today.  
  - **Swing** then runs `analyze_dip_quality()` on every candidate and returns all scored.  
  - **Emotional Dip** filters that list for emotional-only (news keywords, above SMA200, buy rating, upside) and returns a subset.  
- So they share one **data step** (dips) and differ in **filtering/scoring**. That is intentional: two products from the same base. No duplicate logic to remove.

---

## Fixes Applied

1. **Emotional Dip** and **Pre-Market** were missing from the default scan-type list (dropdown). They are now in `DEFAULT_SCAN_TYPES` and `scan_types.json`.
2. **Fallback** in `_get_current_scan_def()` was updated so:
   - **Emotional** is checked before **Dip** → maps to `emotional` (not `swing`).
   - **Pre-Market** / **Pre** → maps to `premarket`.
   - **Barbell** in label → maps to `velocity_leveraged` (so "Velocity Barbell" works even if config is missing).

---

*ClearBlueSky – scanner naming audit*
