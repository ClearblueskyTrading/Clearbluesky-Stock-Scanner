# Polygon, yfinance, MarketAux MCP Setup

These three MCPs are now in your `%USERPROFILE%\.cursor\mcp.json`. Follow the steps below to activate them.

---

## 1. Polygon (market data) — requires API key

**Note:** Polygon.io rebranded to **Massive.com**. Use a key from [massive.com](https://massive.com) or [polygon.io](https://polygon.io).

1. Get an API key from [polygon.io](https://polygon.io) or [massive.com](https://massive.com)
2. Open `%USERPROFILE%\.cursor\mcp.json` (e.g. `C:\Users\EricR\.cursor\mcp.json`)
3. Replace `<get-from-massive.com>` in the `polygon` section with your key:
   ```json
   "MASSIVE_API_KEY": "your-actual-key-here"
   ```

**Tools:** Stock/options/forex/crypto aggregates, trades, quotes, snapshots, news, fundamentals.

---

## 2. yfinance — no API key

No setup needed. Uses Yahoo Finance (free). Restart Cursor to load it.

**Tools:** Ticker info, news, search, top entities by sector, price history, charts.

---

## 3. MarketAux (financial news) — requires API key + build

### Get API key

1. Sign up at [marketaux.com/register](https://www.marketaux.com/register)
2. Get your API token from the dashboard

### Build the MCP (one-time)

MarketAux MCP is cloned to `d:\cursor\mcp-servers\MarketAuxMcpServer`. Build it:

```powershell
cd d:\cursor\mcp-servers\MarketAuxMcpServer
npm install
npm run build
```

*(Requires Node.js and npm.)*

### Add your key

1. Open `%USERPROFILE%\.cursor\mcp.json`
2. Replace `<get-from-marketaux.com>` in the `marketaux` section:
   ```json
   "MARKETAUX_API_KEY": "your-actual-token"
   ```

**Tools:** `market_aux_news_search` — filter by symbols, industries, countries, dates.

---

## Restart Cursor

After adding API keys and building MarketAux, restart Cursor so the MCPs load.

---

## Verify

In Cursor chat, try:

- *"Get AAPL stock info"* (yfinance)
- *"Get latest price for MSFT"* (polygon)
- *"Search financial news for NVDA"* (marketaux)
