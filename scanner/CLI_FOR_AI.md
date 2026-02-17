# ClearBlueSky CLI – For AI / Automation

Run ClearBlueSky scans from the command line so **AI assistants** (Cursor, Claude, etc.) or automation tools can trigger scans, get predictable output, and find the reports.

---

## Quick reference

```bash
# From app folder
python scanner_cli.py --scan <TYPE> [options]

# Or use CLI.bat (Windows)
CLI.bat --scan velocity_trend_growth
```

- **Exit 0** = scan finished successfully (reports written if there were candidates).
- **Exit 1** = failure (rate limit, error, or bad args). **No retries** on rate limit.

---

## Scan types (`--scan`)

| Value | Description |
|-------|-------------|
| `velocity_trend_growth` | Momentum scan: sector-first, then S&P 500 or ETFs in leading sectors. Best after close. |
| `swing` | Emotional dips (index-based). Best 2:30–4:00 PM. Includes earnings/news/insider enrichment. |
| `watchlist` | Filter from config: Down % today (0–X%) or All tickers. Uses config or `--watchlist-file`. |

---

## Options

| Option | Description |
|--------|-------------|
| **`--scan`** (required) | One of: `velocity_trend_growth`, `swing`, `watchlist`. |
| **`--watchlist-file PATH`** | Text file, one ticker per line. Overrides watchlist for this run. |
| **`--index sp500\|etfs`** | Universe override for velocity_trend_growth and swing. Overrides `user_config.json`. |
| **`--reports-dir PATH`** | Override reports output directory. |

---

## Usage

**From app folder** (e.g. `C:\TradingBot\app` or wherever you installed):
```powershell
python scanner_cli.py --scan velocity_trend_growth
python scanner_cli.py --scan swing --index etfs
python scanner_cli.py --scan watchlist --watchlist-file C:\path\to\tickers.txt
```

**From project root:**
```powershell
python app/scanner_cli.py --scan velocity_trend_growth
```

**Windows batch (from app folder):**
```cmd
CLI.bat --scan velocity_trend_growth
CLI.bat --scan swing --index sp500 --reports-dir D:\reports
```

---

## Output: Single .md file

- **.md** – Single Markdown file with:
  - **YAML frontmatter** – Structured data (stocks, market_breadth, market_intel, etc.)
  - **Report body** – Elite Swing Trader directive + per-ticker data
  - **AI Analysis** – Consensus from 6 models (OpenRouter) + optional Google when `openrouter_api_key` is set

Chart data (30-day OHLC, recent daily bars) is included in the JSON for AI analysis; no image generation.

---

## Where reports go

- Default: **`reports/`** under the app folder.
- Override: `--reports-dir PATH` or `user_config.json` → `reports_folder`.
- Filename: `{ScanType}_Scan_{YYYYMMDD_HHMMSS}.md`

---

## Config

- **`user_config.json`** in the app folder (same as GUI).
- Universe (`scan_index`): `sp500` or `etfs` – or override with `--index`.
- OpenRouter API key enables 6-model AI analysis (free models only).

---

## Exit codes

| Code | Meaning |
|------|---------|
| **0** | Success. Reports written if candidates above min score; otherwise "no candidates" but exit 0. |
| **1** | Failure: rate limit (429), error, or bad args. **Do not retry** on rate limit. |

---

## Summary for AI / Automation

1. Run: `python scanner_cli.py --scan <type> [--index sp500|etfs] [--watchlist-file ...] [--reports-dir ...]`
2. If exit **0**: last line = `[OK] Scan complete: reports/<basename>.md` — load that path.
3. If exit **1**: do not retry on rate limit; surface the error.
