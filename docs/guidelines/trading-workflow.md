# Trading Workflow

**Broker:** Alpaca (paper trading)  
**Order entry:** Alpaca dashboard, API, or PTM (Paper Trading Manager) when enabled  
**Scanner:** ClearBlueSky (Velocity Trend Growth, Swing, Watchlist)

## ⛔ Rule: No Solo Picks (3 Checks)

**Never allow discretionary stock picks unless all 3 checks pass (AND logic).**  
If you ask to buy/sell a ticker on your own impulse, the AI must refuse unless the pick passes all three:

| Check | Requirement | Source |
|-------|--------------|--------|
| **1. Scan** | Ticker appears in the report with score ≥ 85 | ClearBlueSky scan |
| **2. AI** | OpenRouter analysis lists it in TOP 5 PLAYS or TIER 1/2 | Report AI output |
| **3. Sanity** | At least one: (a) appears in 2+ scan types run that day, OR (b) no DANGER/NEGATIVE news flags | Scan + news data |

**Rule:** `approved = (scan_qualified) AND (ai_picked) AND (sanity_ok)`

## Flow

1. **Scan** — Run ClearBlueSky scanners for ideas.
2. **Decide** — Review report, AI picks, watchlist matches.
3. **Order** — Place via Alpaca (paper): dashboard, API, or PTM daemon when enabled.
4. **Execute** — Review and submit. PTM can auto-buy from scan reports when under max positions.

## AI Report from Scan Files

After a scan, you get 3 files: `.pdf`, `.txt`, `.json`. To have the AI (Cursor) produce the final report:

- Say **"Create AI report"** or **"Read my scan reports and produce the report"**
- The AI finds the latest JSON, reads it, and produces the report (MARKET SNAPSHOT, TIER 1/2/3, AVOID, RISK, KEY INSIGHT, TOP 5 PLAYS)
- See `docs/guidelines/ai-report-from-scan.md`

## Extended Hours (Pre-Market 4–9:30 AM | After-Hours 4–8 PM ET)

**Rule:** Always use **LIMIT orders** in extended hours. Market orders are not executed during extended hours — they queue for the next regular session.

| Do | Don't |
|----|-------|
| Limit buy/sell with `extended_hours=true` | Market orders (will not fill until 9:30 AM) |
| Whole shares only | Fractional shares (not supported) |
| Expect lower liquidity, wider spreads | Assume regular-session fill speed |

**Other considerations:**
- Lower volume → partial fills or no fill possible; wider spreads
- Price can gap significantly overnight; stale quotes during extended hours
- For exits: use limit slightly below (sells) or above (buys) last quote
- **Automation/AI:** When placing orders 4–9:30 AM or 4–8 PM, must use limit orders + `extended_hours=true`; tools like `close_position` may send market orders — use explicit limit sell instead

## Notes

- Alpaca paper trading: free, supports API and MCP for automation.
- PTM (Paper Trading Manager) can auto-buy from scan reports when enabled; set alpaca_api_key and ptm_enabled in config.
- Always review the order before submitting.
