# AI Report from Scan Files

When the user asks you to **create the AI report**, **read the scan reports and produce the report**, or similar:

1. **Find the latest report** — Look in `app/reports/` (or `D:\cursor\app\reports`). Scan for `*_Scan_*.json` files. Use the most recent by modification time. If user specifies a path or @mentions a file, use that.

2. **Read the 3 report files** (as needed):
   - **JSON** (primary) — Has `instructions` (full AI directive) + `stocks`, `market_breadth`, `market_intel`, `price_history_30d`. Use this as your main input.
   - **TXT** (optional) — Human-readable summary; use if JSON is missing or for extra context.
   - **PDF** — Not readable as text; skip unless user needs image extraction.

3. **Produce the report** — Use the `instructions` field from the JSON as your directive. Output in the required format:
   - MARKET SNAPSHOT
   - TIER 1 / TIER 2 / TIER 3 picks (Setup, Catalyst, Invalidation, Timing)
   - AVOID LIST
   - RISK MANAGEMENT
   - KEY INSIGHT
   - TOP 5 PLAYS
   - Attribution: "This report was created using the ClearBlueSky Stock Scanner. Scanner: https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases"

4. **Save option** — If user wants the report saved, write to `{basename}_ai.txt` in the same reports folder (or a path they specify).

## Report paths

- Default: `D:\cursor\app\reports\` or `D:\scanner\app\reports\` (if scanner is at D:\scanner)
- Configurable: `user_config.json` → `reports_folder`
- File pattern: `{ScanType}_Scan_{YYYYMMDD_HHMMSS}.json` (e.g. `Velocity_Trend_Growth_Scan_20260210_143022.json`)

## Trigger phrases

- "Create AI report"
- "Read my scan reports and produce the report"
- "Make the AI report from my latest scan"
- "Analyze my scan and write the report"
