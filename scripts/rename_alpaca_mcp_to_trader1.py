"""Rename 'alpaca' MCP to 'alpaca_trader1' in mcp.json for consistency with alpaca_trader2."""
import json

path = r"C:\Users\EricR\.cursor\mcp.json"
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"mcp.json not found at {path}")
    exit(1)

servers = data.get("mcpServers", {})
if "alpaca" in servers and "alpaca_trader1" not in servers:
    servers["alpaca_trader1"] = servers.pop("alpaca")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Renamed 'alpaca' -> 'alpaca_trader1' in mcp.json. Restart Cursor to load it.")
elif "alpaca_trader1" in servers:
    print("alpaca_trader1 already exists. No change needed.")
else:
    print("'alpaca' not found in mcp.json. Current keys:", list(servers.keys()))
