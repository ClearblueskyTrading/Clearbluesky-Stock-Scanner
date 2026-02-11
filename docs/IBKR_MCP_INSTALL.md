# IBKR MCP and Interface Options

This doc covers MCP (Model Context Protocol) servers and direct APIs for Interactive Brokers integration with Cursor/AI workflows.

---

## Quick Comparison

| Option | Backend | Trading | Ease | Best For |
|--------|---------|---------|------|----------|
| **ib-mcp** | TWS/Gateway | Read-only | pip install | Data + portfolio in Cursor |
| **IB_MCP** (rcontesti) | Web API | Yes | Docker | Cloud, no TWS needed |
| **ib_insync** | TWS/Gateway | Full | Python library | Your own scripts |

---

## Option 1: ib-mcp (Recommended for Cursor)

**Read-only** MCP server using TWS/IB Gateway. Fast setup, works with Claude Desktop and Cursor.

### Prerequisites

- **IB Gateway or TWS** running (port 7497 for TWS, 4001 for Gateway)
- **Python 3.12+**
- API enabled in TWS: `Configure → API → Settings` → "Enable ActiveX and Socket Clients"

### Install

```bash
pip install ib-mcp
```

### Run as MCP server (STDIO for Cursor)

```bash
# Default (TWS on localhost:7497)
ib-mcp-server

# IB Gateway on port 4001
ib-mcp-server --host 127.0.0.1 --port 4001 --client-id 1
```

### Cursor mcp.json config

Add to `%USERPROFILE%\.cursor\mcp.json` (alongside alpaca or other servers):

```json
{
  "mcpServers": {
    "alpaca": { "command": "uvx", "args": ["alpaca-mcp-server", "serve"], "env": { "ALPACA_API_KEY": "...", "ALPACA_SECRET_KEY": "..." } },
    "ibkr": {
      "command": "ib-mcp-server",
      "args": ["--host", "127.0.0.1", "--port", "7497", "--client-id", "1"],
      "env": {}
    }
  }
}
```

Use `--port 4001` if you use IB Gateway instead of TWS.

### Tools exposed

- `lookup_contract` — Contract details by symbol
- `ticker_to_conid` — Symbol → contract ID
- `get_historical_data` — OHLCV bars
- `get_news` / `get_historical_news` — News
- `get_fundamental_data` — Financials
- `get_portfolio` / `get_account_summary` / `get_positions` — Account data

**Links:** [PyPI](https://pypi.org/project/ib-mcp/) | [GitHub](https://github.com/Hellek1/ib-mcp)

---

## Option 2: IB_MCP (rcontesti) — Web API

Uses **IB Client Portal Gateway** (no TWS/Gateway needed). Supports trading. Cloud-friendly.

### Prerequisites

- Docker Desktop
- IB account
- Browser on same machine for one-time auth

### Setup

```bash
git clone https://github.com/rcontesti/IB_MCP.git
cd IB_MCP
cp .env.example .env
# Edit .env if needed
docker compose up --build -d
```

1. Open `https://localhost:5055/` (or your `GATEWAY_BASE_URL`) and log in with IB credentials.
2. Add MCP config to Cursor:

```json
{
  "mcpServers": {
    "ib-web": {
      "type": "http",
      "url": "http://localhost:5002/mcp/"
    }
  }
}
```

### Notes

- Session expires ~6 min without activity; tickler keeps it alive.
- Auth must be done on the same machine as the gateway.
- More endpoints than ib-mcp; includes order placement.

**Links:** [GitHub](https://github.com/rcontesti/IB_MCP) | [Playbooks](https://playbooks.com/mcp/rcontesti-interactive-brokers)

---

## Option 3: Direct Python (ib_insync)

For custom scripts or ClearBlueSky integration (no MCP):

```bash
pip install ib_insync
```

```python
from ib_insync import *
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Historical bars
contract = Stock('AAPL', 'SMART', 'USD')
bars = ib.reqHistoricalData(contract, endDateTime='', durationStr='30 D',
    barSizeSetting='1 day', whatToShow='TRADES', useRTH=True)
df = util.df(bars)

# Portfolio
positions = ib.positions()
```

**Docs:** [ib_insync](https://ib-insync.readthedocs.io/)

---

## Summary

- **Cursor + data only:** Use **ib-mcp** (Option 1).
- **No TWS, cloud, or trading:** Use **IB_MCP** (Option 2).
- **Custom code:** Use **ib_insync** (Option 3).
