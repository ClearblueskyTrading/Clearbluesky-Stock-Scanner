"""Quick Alpaca positions and orders check."""
import json
import os
import requests

cfg_path = os.path.join(os.path.dirname(__file__), "..", "app", "user_config.json")
key, secret = None, None
if os.path.exists(cfg_path):
    with open(cfg_path) as f:
        c = json.load(f)
    key, secret = c.get("alpaca_api_key") or "", c.get("alpaca_secret_key") or ""
if not key or not secret:
    key, secret = "PKG7Y3AVEKE6W22FPKAK4E6VGZ", "3c7yG4N9Qjk9JqgFgswPiTQMfsDRTGBE7QCGGDD5MfNn"  # fallback
h = {"APCA-API-KEY-ID": key.strip(), "APCA-API-SECRET-KEY": secret.strip()}
base = "https://paper-api.alpaca.markets"
pos = requests.get(base + "/v2/positions", headers=h).json()
orders = requests.get(base + "/v2/orders", headers=h, params={"status": "all", "limit": 15}).json()
acc = requests.get(base + "/v2/account", headers=h).json()

print("=== POSITIONS ===")
for p in pos:
    qty, sym = p.get("qty", 0), p.get("symbol", "")
    avg = float(p.get("avg_entry_price", 0))
    mkt = float(p.get("market_value", 0))
    print(f"  {qty:>8} {sym:8} @ {avg:.2f}  mkt ${mkt:,.2f}")
if not pos:
    print("  None")

print("\n=== OPEN ORDERS ===")
open_orders = [o for o in orders if o.get("status") in ("new", "accepted", "pending_new", "partially_filled")]
for o in open_orders:
    print(f"  {o.get('side',''):4} {o.get('qty',''):>6} {o.get('symbol',''):8} @ {o.get('limit_price','mkt')}")
if not open_orders:
    print("  None")

print("\n=== ACCOUNT ===")
print(f"  Buying power: ${float(acc.get('buying_power',0)):,.2f}")
print(f"  Equity: ${float(acc.get('equity',0)):,.2f}")
