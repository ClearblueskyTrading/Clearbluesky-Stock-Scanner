"""
Discretionary paper trading - scan for best setups, manage orders, maximize profits.
"""
import json
import os
import requests

# Keys
cfg = {}
cfg_path = os.path.join(os.path.dirname(__file__), "..", "app", "user_config.json")
if os.path.exists(cfg_path):
    with open(cfg_path) as f:
        cfg = json.load(f)
key = (cfg.get("alpaca_api_key") or "PKG7Y3AVEKE6W22FPKAK4E6VGZ").strip()
secret = (cfg.get("alpaca_secret_key") or "3c7yG4N9Qjk9JqgFgswPiTQMfsDRTGBE7QCGGDD5MfNn").strip()

h = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
trading_base = "https://paper-api.alpaca.markets"
data_base = "https://data.alpaca.markets"

WATCHLIST = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "JPM", "V", "WMT", "UNH", "JNJ", "PG", "MA", "HD"]

def get_prices_yf(symbols):
    """Use yfinance for current prices and daily change."""
    try:
        import yfinance as yf
        result = {}
        for sym in symbols:
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="1d")
                if hist is not None and len(hist) > 0:
                    o, c = float(hist["Open"].iloc[0]), float(hist["Close"].iloc[-1])
                    chg = (c - o) / o * 100 if o else 0
                    result[sym] = {"price": c, "open": o, "chg": chg}
            except Exception:
                pass
        return result
    except Exception as e:
        print(f"  yf error: {e}")
        return {}

def get_order(id):
    r = requests.get(f"{trading_base}/v2/orders/{id}", headers=h)
    return r.json() if r.status_code == 200 else None

def cancel_order(id):
    r = requests.delete(f"{trading_base}/v2/orders/{id}", headers=h)
    return r.status_code in (200, 204)

def place_market_buy(symbol, qty):
    r = requests.post(f"{trading_base}/v2/orders", headers={**h, "Content-Type": "application/json"},
        json={"symbol": symbol, "qty": str(int(qty)), "side": "buy", "type": "market", "time_in_force": "day"})
    return r.json() if r.status_code in (200, 201) else {"error": r.text}

def get_orders():
    r = requests.get(f"{trading_base}/v2/orders", headers=h, params={"status": "open"})
    return r.json() if r.status_code == 200 else []

def get_positions():
    r = requests.get(f"{trading_base}/v2/positions", headers=h)
    return r.json() if r.status_code == 200 else []

# 1. Get current open orders
orders = get_orders()
positions = get_positions()

# 2. Get prices (yfinance)
check_symbols = list(set(["GOOGL", "SOXL"] + WATCHLIST))
prices = get_prices_yf(check_symbols)

# 3. Assess existing orders
googl_price = prices.get("GOOGL", {}).get("price") if prices.get("GOOGL") else None
soxl_price = prices.get("SOXL", {}).get("price") if prices.get("SOXL") else None

print("=== CURRENT PRICES ===")
print(f"  GOOGL: ${googl_price:.2f}" if googl_price else "  GOOGL: N/A")
print(f"  SOXL:  ${soxl_price:.2f}" if soxl_price else "  SOXL: N/A")

# 4. Find dip candidates (down 2-5% today)
dips = []
for sym in WATCHLIST:
    p = prices.get(sym, {})
    price, chg = p.get("price"), p.get("chg")
    if price and chg is not None and -5 < chg < -1.5:
        dips.append({"sym": sym, "price": price, "chg": chg})

dips.sort(key=lambda x: x["chg"])  # most down first
print("\n=== DIP CANDIDATES (down 1.5-5% today) ===")
for d in dips[:5]:
    print(f"  {d['sym']:6} ${d['price']:.2f}  {d['chg']:.2f}%")
if not dips:
    print("  None")

# 5. Decisions
cancel_ids = []
to_buy = []

# GOOGL: limit 309. If GOOGL > 309, order won't fill - could cancel and buy a dip instead. If GOOGL < 309, order would fill.
# SOXL: limit 67. Same logic.
for o in orders:
    sym, side, qty, limit = o.get("symbol"), o.get("side"), float(o.get("qty", 0)), float(o.get("limit_price", 0) or 0)
    curr = googl_price if sym == "GOOGL" else (soxl_price if sym == "SOXL" else None)
    if curr and limit:
        dist_pct = ((curr - limit) / limit * 100) if limit else 0
        # If limit is far below current (we're waiting for big drop), consider canceling for better opportunity
        # If limit is near current, keep it
        if sym == "GOOGL" and dist_pct > 2 and dips:
            cancel_ids.append(o["id"])
        elif sym == "SOXL" and dist_pct > 3 and dips:
            cancel_ids.append(o["id"])
        else:
            print(f"\n  KEEP: {side} {qty} {sym} @ {limit} (mkt ${curr:.2f})")

# 6. Execute: cancel if we have better dips, buy best dip
for oid in cancel_ids:
    if cancel_order(oid):
        print(f"  CANCELED order {oid}")

# 7. Buy best dip if we have space (max 2 new positions, ~$3k each)
eq = requests.get(f"{trading_base}/v2/account", headers=h).json()
buying_power = float(eq.get("buying_power", 0))
pos_count = len(positions)

if dips and pos_count < 3 and buying_power > 5000:
    best = dips[0]
    sym, price = best["sym"], best["price"]
    qty = max(5, min(15, int(3000 / price)))  # 5-15 shares, ~$3k
    result = place_market_buy(sym, qty)
    if "error" in result:
        print(f"\n  BUY FAILED {sym}: {result.get('error', result)}")
    else:
        print(f"\n  BOUGHT: {qty} {sym} @ market (~${price:.2f}) - dip {best['chg']:.2f}%")
else:
    print("\n  No new buys (no dips or at position limit)")

print("\nDone.")
