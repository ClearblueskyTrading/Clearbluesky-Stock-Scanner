#!/usr/bin/env python3
"""Check Alpaca paper trading orders and positions."""
import json
import os
import sys

# Try config from app folder
CONFIG_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "app", "user_config.json"),
    os.path.join(os.path.dirname(__file__), "..", "app", "..", "app", "user_config.json"),
]

def get_keys():
    for p in CONFIG_PATHS:
        p = os.path.abspath(p)
        if os.path.exists(p):
            try:
                with open(p) as f:
                    c = json.load(f)
                k = (c.get("alpaca_api_key") or "").strip()
                s = (c.get("alpaca_secret_key") or "").strip()
                if k and s:
                    return k, s
            except Exception:
                pass
    k = os.environ.get("APCA_API_KEY_ID") or os.environ.get("ALPACA_API_KEY_ID")
    s = os.environ.get("APCA_API_SECRET_KEY") or os.environ.get("ALPACA_SECRET_KEY")
    if k and s:
        return k, s
    return None, None

def main():
    key, secret = get_keys()
    if not key or not secret:
        print("No Alpaca keys in user_config.json or env (APCA_API_KEY_ID, APCA_API_SECRET_KEY)")
        sys.exit(1)

    try:
        import requests
    except ImportError:
        print("pip install requests")
        sys.exit(1)

    base = "https://paper-api.alpaca.markets"
    headers = {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": secret,
    }

    # Orders
    r = requests.get(f"{base}/v2/orders", headers=headers, params={"status": "all", "limit": 20})
    if r.status_code != 200:
        print(f"Orders API error: {r.status_code} {r.text[:200]}")
        sys.exit(1)
    orders = r.json()

    # Positions
    r2 = requests.get(f"{base}/v2/positions", headers=headers)
    positions = r2.json() if r2.status_code == 200 else []

    # Filter filled
    filled = [o for o in orders if o.get("status") == "filled"]
    pending = [o for o in orders if o.get("status") in ("new", "accepted", "pending_new", "partially_filled")]

    print("=== Alpaca Paper - Recent Orders ===")
    if not orders:
        print("No orders.")
    else:
        for o in orders[:15]:
            st = o.get("status", "")
            sym = o.get("symbol", "")
            side = o.get("side", "")
            qty = o.get("qty") or o.get("filled_qty") or "?"
            t = o.get("filled_at") or o.get("created_at", "")[:19]
            print(f"  {st:12} {side:4} {qty} {sym:8} @ {t}")

    print("\n=== Filled (last 24h) ===")
    if not filled:
        print("No fills yet.")
    else:
        for o in filled[:10]:
            sym = o.get("symbol", "")
            side = o.get("side", "")
            qty = o.get("filled_qty") or o.get("qty")
            avg = o.get("filled_avg_price") or "?"
            t = (o.get("filled_at") or "")[:19]
            print(f"  {side:4} {qty} {sym:8} @ {avg}  {t}")

    print("\n=== Positions ===")
    if not positions:
        print("No positions.")
    else:
        for p in positions:
            sym = p.get("symbol", "")
            qty = p.get("qty", "")
            mkt = p.get("market_value", "")
            print(f"  {qty:>8} {sym:8}  mkt_val ${float(mkt or 0):,.2f}" if mkt else f"  {qty} {sym}")

if __name__ == "__main__":
    main()
