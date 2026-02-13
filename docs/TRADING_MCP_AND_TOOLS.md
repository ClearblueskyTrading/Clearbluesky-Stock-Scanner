# Trading MCPs, Cloud Agents & Tools

What to add for trading workflows in Cursor. You already have **Alpaca MCP** (quotes, positions, orders, watchlists).

---

## MCPs Worth Adding

### Already in your setup

| MCP | Purpose | Status |
|-----|---------|--------|
| **Alpaca** | Stocks, ETFs, crypto, options — account, positions, orders, quotes, bars | ✅ Installed |
| **IBKR (ib-mcp)** | Read portfolio/data from TWS/Gateway | Docs in `IBKR_MCP_INSTALL.md` |

### Suggested additions

| MCP | Purpose | When to add |
|-----|---------|-------------|
| **GitHub** | Repos, issues, PRs, search, branch ops | If you want AI to work with your GitHub repos |
| **IBKR (ib-mcp)** | Portfolio, positions, data from Interactive Brokers | If you use IB for execution |
| **Polygon** | Pro market data (stocks, options, forex) | If you want richer/faster data than Alpaca |
| **yfinance** | Free stock data from Yahoo Finance | Backup / cross-check pricing |
| **MarketAux** | Financial news by symbol, sector, date | News research |
| **Binance** | Crypto prices and trading | If you trade crypto |
| **Alpha Vantage** | Already in scanner for sentiment | Optional MCP if you want it in chat too |

### Where to browse

- [cursor.directory](https://cursor.directory/mcp) — search “finance” or “trading”
- [cursormcp.dev Finance & Fintech](https://cursormcp.dev/ca/finance-fintech) — 130+ finance MCPs

---

## Cloud Agents (Cursor)

Cursor’s **Cloud Agents** (Settings → Cloud Agents) are:

- **Manage Settings** — GitHub, team, user config
- **Connect Slack** — Use Cloud Agents from Slack
- **Workspace Configuration** — Env vars, secrets

There is no built-in “trading” Cloud Agent. Trading flows run via **MCPs** (local or remote) or your own scripts.

---

## Other tools

| Tool | Purpose |
|------|---------|
| **Desktop Agent panel** | Quick buttons: Schwab, Finviz, Costco, etc.; Check your brain; Memory backup |
| **Scanner app** | Velocity Trend, Swing Dips, Watchlist; OpenRouter AI analysis |
| **velocity_rag** | RAG over sessions + docs; “check your brain” |
| **Rules** | `.cursor/rules/` — triggers for “save conversation”, “check your brain”, alpaca rate limits |

---

## New MCPs added (1–5, 12, 17, 18)

| MCP | Purpose |
|-----|---------|
| **Playwright** | Browser automation (navigate, click, snapshot) |
| **Fetch** | Read URLs as Markdown |
| **Brave Search** | Web search — **needs API key** |
| **Memory** | Persistent knowledge graph across sessions |
| **Filesystem** | Read/write files in `d:\cursor` |
| **Sequential thinking** | Step-by-step reasoning for complex problems |
| **OpenAPI** | Connect to REST APIs (e.g. Schwab when ready) |
| **Screenshot** (Puppeteer) | Capture webpage screenshots |

### Setup steps

1. **Brave Search** — Get free API key at [brave.com/search/api](https://brave.com/search/api) (2,000 queries/month). Replace `YOUR_BRAVE_API_KEY` in `mcp.json`.

2. **OpenAPI** — Preconfigured with Swagger Petstore for testing. When you have Schwab API, update `OPENAPI_SPEC_PATH` and `API_BASE_URL` in `mcp.json` to Schwab's spec and base URL.

3. **Playwright** — Run `npx playwright install` once to install browsers.

4. **Restart Cursor** after editing `mcp.json`.

---

## Quick install examples

### GitHub

```json
"github": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "<your-github-pat>"
  }
}
```

Create a PAT at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` scope.

### Polygon

```json
"polygon": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-polygon"],
  "env": {
    "POLYGON_API_KEY": "<your-key>"
  }
}
```

---

1. **Cursor Settings** → **Features** → **MCP** → Add server  
2. Or edit `%USERPROFILE%\.cursor\mcp.json`  
3. Restart Cursor

---

*Last updated: 2026-02*
