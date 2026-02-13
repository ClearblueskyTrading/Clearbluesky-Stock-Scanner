"""Add alpaca_trader2 to mcp.json. Run once."""
import json

path = r"C:\Users\EricR\.cursor\mcp.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

data["mcpServers"]["alpaca_trader2"] = {
    "env": {
        "ALPACA_API_KEY": "PK2KIWV4ZZG32YAPUTBTBOVLZ3",
        "ALPACA_SECRET_KEY": "8o7eTm8qZ96S9m53DSgR9kDMHCEhYEAtfkhzQ6mmMgYN",
    },
    "command": "uvx alpaca-mcp-server serve",
    "args": [],
}

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("Added alpaca_trader2 to mcp.json. Restart Cursor to load it.")
