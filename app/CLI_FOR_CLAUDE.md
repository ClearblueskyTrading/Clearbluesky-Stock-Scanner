# ClearBlueSky CLI – For Claude / Automation

This document explains how to run ClearBlueSky scans from the command line so **Claude** (or another automation tool like Desktop Commander) can trigger scans, get predictable output, and find the reports.

---

## Quick reference

```bash
python scanner_cli.py --scan <TYPE> [--watchlist-file PATH]
```

- **Exit 0** = scan finished successfully (reports written if there were candidates).
- **Exit 1** = failure (rate limit, error, or bad args). **No retries** on rate limit.

---

## Scan types (`--scan`)

| Value | Description |
|-------|-------------|
| `velocity_trend_growth` | Momentum scan: sector-first (top sectors by return), then S&P 500 stocks + ETFs in leading sectors. Best after close. |
| `swing` | Emotional-only dips (index-based). Best 2:30–4:00 PM. Includes earnings/news/insider enrichment. |
| `watchlist` | Watchlist: Filter from config – Down % today (0–X%, slider=max) or All tickers. Uses config or `--watchlist-file`. |

---

## Options

- **`--scan`** (required)  
  One of: `velocity_trend_growth`, `swing`, `watchlist`.

- **`--watchlist-file PATH`** (optional)  
  Text file, **one ticker per line**. Overrides the watchlist from `user_config.json` for this run only.  
  Useful for: `watchlist`.

---

## Exit codes

| Code | Meaning |
|------|--------|
| **0** | Success. Scan ran; if there were candidates above min score, reports were written. If no candidates, message says "no candidates" but exit is still 0. |
| **1** | Failure: rate limit (429), other error, or invalid/missing args. **Do not retry** on rate limit. |

---

## Console output

- Progress lines are prefixed with spaces (e.g. `   Fetching data from Finviz...`).
- On success with a report, the last line is:  
  **`[OK] Scan complete: reports/<basename>.*`**  
  Example: `[OK] Scan complete: reports/Velocity_Trend_Growth_20260209_160015.*`
- On failure: **`[FAIL] Rate limit hit: ...`** or **`[FAIL] Scan failed: ...`** (to stderr).  
  (ASCII-only so Windows console works.)

---

## Where reports go

- Directory: **`reports/`** (under the app folder, or the path set in `user_config.json` → `reports_folder`).
- Filenames are **timestamped** and predictable:
  - `{ScanType}_Scan_{YYYYMMDD_HHMMSS}.pdf`
  - `{ScanType}_Scan_{YYYYMMDD_HHMMSS}.json`
  - `{ScanType}_Scan_{YYYYMMDD_HHMMSS}_ai.txt` (if OpenRouter is configured and ran)

So after **`[OK] Scan complete: reports/Velocity_Trend_Growth_20260209_160015.*`**, Claude can look for:
- `reports/Velocity_Trend_Growth_20260209_160015.pdf`
- `reports/Velocity_Trend_Growth_20260209_160015.json`
- `reports/Velocity_Trend_Growth_20260209_160015_ai.txt`

---

## Example commands (for Claude)

```bash
# Velocity Trend Growth (momentum) on S&P 500 + ETFs
python scanner_cli.py --scan velocity_trend_growth

# Swing scan on S&P 500 (default)
python scanner_cli.py --scan swing

# Watchlist (Filter from config: Down % today or All; override tickers with file)
python scanner_cli.py --scan watchlist --watchlist-file C:\path\to\tickers.txt
```

---

## Config and API keys

- Scanners use **`user_config.json`** in the app folder (same as the GUI).
- API keys (OpenRouter, etc.) and watchlist come from that file unless you override watchlist with **`--watchlist-file`**.
- The CLI does **not** open a browser; it writes PDF, JSON, and (if configured) `_ai.txt` only.

---

## Rate limits (Finviz)

- If the CLI prints **`[FAIL] Rate limit hit: ...`** and exits with **1**, **do not retry immediately**.
- Finviz rate-limits; wait (e.g. several minutes) before running another scan.

---

## Summary for Claude

1. Run: `python scanner_cli.py --scan <type> [--watchlist-file ...]`
2. If exit code **0**: check last line for `[OK] Scan complete: reports/<basename>.*` and use that basename to load PDF/JSON/_ai.txt from `reports/`.
3. If exit code **1**: do not retry on rate limit; treat as failure and surface the error message.
