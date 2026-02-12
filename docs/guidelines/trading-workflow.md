# Trading Workflow

**Broker:** IBKR Lite  
**Order entry:** IBOT (natural language in TWS, Client Portal, or IBKR Mobile)  
**Scanner:** ClearBlueSky (Velocity Trend Growth, Swing, Watchlist)

## ⛔ Rule: No Solo Picks

**Never allow discretionary stock picks unless 3 AIs agree.**  
If you ask to buy/sell a ticker on your own impulse, the AI must refuse unless the pick is already supported by agreement from 3 separate AI analyses (e.g., scanner report + OpenRouter + another source).

## Flow

1. **Scan** — Run ClearBlueSky scanners for ideas.
2. **Decide** — Review report, AI picks, watchlist matches.
3. **Order** — Use IBOT to place orders. When needed, prompt the AI (Cursor) to craft the IBOT command.
4. **Execute** — Paste/type the command into IBOT, review, and submit.

## IBOT Order Prompts

When you want to place an order, tell the AI what you want and ask for an IBOT command. Examples:

- *"IBOT: buy 100 AAPL at 175 limit, OCO sell stop at 170"*
- *"IBOT: sell half my NVDA at market"*
- *"Create OCO for IBOT: buy 50 SOXL at 45 or sell stop at 42"*

The AI returns a plain-English command you can enter into IBOT.

## AI Report from Scan Files

After a scan, you get 3 files: `.pdf`, `.txt`, `.json`. To have the AI (Cursor) produce the final report:

- Say **"Create AI report"** or **"Read my scan reports and produce the report"**
- The AI finds the latest JSON, reads it, and produces the report (MARKET SNAPSHOT, TIER 1/2/3, AVOID, RISK, KEY INSIGHT, TOP 5 PLAYS)
- See `docs/guidelines/ai-report-from-scan.md`

## Notes

- IBOT is included with IBKR (no extra cost, unlimited use).
- IBOT supports OCO/OCA orders.
- Always review the order ticket before submitting.
- IBKR Lite does not support API connections (Trade Ideas, MCP, etc.). Use IB Pro if you need automation later.
