# How to install the Alpaca MCP (Cursor)

Use **one** of these methods. Paper trading keys work the same way (use your paper key/secret).

---

## Option A: Cursor Directory (easiest)

1. Open **[Cursor Directory → Alpaca](https://cursor.directory/mcp/alpaca)** in your browser.
2. Click **"Add to Cursor"** (Cursor will open).
3. When prompted, enter your **API Key** and **Secret Key** (from [Alpaca Paper Dashboard](https://app.alpaca.markets/paper/dashboard/overview) or live).
4. Restart Cursor if the MCP doesn’t show up.

No terminal or config file needed.

---

## Option B: Manual config (mcp.json)

**1. Install prerequisites**

- **Python 3.10+**  
  - Check: `python --version` or `py -3 --version`
- **uv** (runs the Alpaca MCP server)  
  - Windows (PowerShell):  
    `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`  
  - Then close and reopen your terminal so `uv` / `uvx` are on PATH.

**2. Create or edit MCP config**

- **File:** `%USERPROFILE%\.cursor\mcp.json`  
  - Full path example: `C:\Users\YourName\.cursor\mcp.json`
- **Show hidden folders:** File Explorer → View → check **Hidden items**.
- If `mcp.json` doesn’t exist, create it. If it exists, add an `"alpaca"` entry inside `"mcpServers"`.

**3. Config contents**

```json
{
  "mcpServers": {
    "alpaca": {
      "command": "uvx",
      "args": ["alpaca-mcp-server", "serve"],
      "env": {
        "ALPACA_API_KEY": "your_paper_or_live_api_key",
        "ALPACA_SECRET_KEY": "your_paper_or_live_secret_key"
      }
    }
  }
}
```

Replace `your_paper_or_live_api_key` and `your_paper_or_live_secret_key` with your real keys (paper keys from [paper dashboard](https://app.alpaca.markets/paper/dashboard/overview)).

**4. Restart Cursor** so it loads the new MCP config.

---

## Option C: install.py (from Alpaca repo)

1. In a terminal:
   ```bash
   git clone https://github.com/alpacahq/alpaca-mcp-server.git
   cd alpaca-mcp-server
   python install.py
   ```
2. When the script asks, choose **Cursor**.
3. It will configure `~/.cursor/mcp.json` (or `%USERPROFILE%\.cursor\mcp.json` on Windows) and prompt for your API keys.
4. Restart Cursor.

---

## Check that it’s working

- In Cursor: **Settings → Features → MCP**. You should see **alpaca** (or the name you gave it) with no error.
- In chat you can ask: *“What’s my Alpaca account balance?”* or *“Is the market open?”* — the AI will use the Alpaca MCP if it’s connected.

## Keys and paper vs live

- **Paper:** Get keys from [Paper Trading Dashboard](https://app.alpaca.markets/paper/dashboard/overview). Same `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` in `mcp.json`; the server uses Alpaca’s paper endpoint by default when you use paper keys.
- **Live:** Use your live keys in the same `env` block; keep `mcp.json` private (it’s in your user folder, not in this repo). Never commit real keys.

## Reference

- [Alpaca MCP Server (official)](https://github.com/alpacahq/alpaca-mcp-server)  
- [Alpaca MCP docs](https://docs.alpaca.markets/docs/alpaca-mcp-server)  
- Cursor config path (global): `~/.cursor/mcp.json` (Mac/Linux) or `%USERPROFILE%\.cursor\mcp.json` (Windows)
