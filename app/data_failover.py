# ============================================================
# ClearBlueSky - Price/volume failover: yfinance > finviz > alpaca
# ============================================================
# When data is missing, try sources in this order.
# Single-ticker and batch helpers.

import sys
import io
from typing import Dict, List, Optional

# Rate limit: yfinance and finviz callers should add delays; we keep Alpaca logic in alpaca_data


def get_price_volume(ticker: str, config: Optional[dict] = None) -> Optional[Dict]:
    """
    Get current price/volume for one ticker. Failover order: yfinance > finviz > alpaca.
    Returns dict with price, volume, change_pct, source; or None if all fail.
    """
    ticker = (ticker or "").strip().upper()
    if not ticker:
        return None

    # 1. yfinance
    try:
        import yfinance as yf
        _old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            data = yf.download(ticker, period="1d", interval="1d", progress=False, auto_adjust=True, timeout=15)
        finally:
            sys.stderr = _old_stderr
        if data is not None and not data.empty:
            if hasattr(data.columns, "levels"):
                data.columns = data.columns.get_level_values(0)
            close = data.get("Close")
            if close is not None and len(close) > 0:
                price = float(close.iloc[-1])
                if price and price > 0:
                    vol = 0
                    if "Volume" in data.columns:
                        try:
                            vol = int(float(data["Volume"].iloc[-1]))
                        except (TypeError, ValueError):
                            pass
                    change_pct = None
                    if len(close) >= 2:
                        try:
                            prev = float(close.iloc[-2])
                            if prev and prev > 0:
                                change_pct = round((price - prev) / prev * 100, 2)
                        except (TypeError, ValueError):
                            pass
                    return {"price": round(price, 2), "volume": vol, "change_pct": change_pct, "source": "yfinance"}
    except Exception:
        pass

    # 2. finviz
    try:
        from finviz_safe import get_stock_safe
        stock = get_stock_safe(ticker, timeout=12.0, max_attempts=1)
        if stock:
            price_raw = stock.get("Price") or stock.get("price")
            if price_raw is not None and str(price_raw).strip():
                try:
                    price = float(str(price_raw).replace(",", "").replace("$", "").strip())
                    if price > 0:
                        vol = 0
                        v_raw = stock.get("Volume") or stock.get("volume")
                        if v_raw is not None:
                            try:
                                vol = int(float(str(v_raw).replace(",", "").replace("K", "e3").replace("M", "e6")))
                            except (TypeError, ValueError):
                                pass
                        change_raw = stock.get("Change") or stock.get("change")
                        change_pct = None
                        if change_raw is not None and str(change_raw).strip():
                            try:
                                s = str(change_raw).replace("%", "").strip()
                                if s:
                                    change_pct = round(float(s), 2)
                            except (TypeError, ValueError):
                                pass
                        return {"price": round(price, 2), "volume": vol, "change_pct": change_pct, "source": "finviz"}
                except (TypeError, ValueError):
                    pass
    except Exception:
        pass

    # 3. alpaca
    try:
        from alpaca_data import has_alpaca_keys, get_price_volume as alpaca_pv
        if has_alpaca_keys(config):
            pv = alpaca_pv(ticker, config)
            if pv and pv.get("price") and pv["price"] > 0:
                return {
                    "price": pv["price"],
                    "volume": pv.get("volume", 0),
                    "change_pct": pv.get("change_pct"),
                    "source": "alpaca",
                }
    except Exception:
        pass

    return None


def get_price_volume_batch(tickers: List[str], config: Optional[dict] = None) -> Dict[str, Dict]:
    """
    Get price/volume for multiple tickers. Failover: yfinance batch first, then finviz for missing, then alpaca for missing.
    """
    if not tickers:
        return {}
    tickers = [str(t).strip().upper() for t in tickers if str(t).strip()]
    tickers = list(dict.fromkeys(tickers))[:100]

    out = {}
    missing_after_yf = []

    # 1. yfinance batch
    try:
        import yfinance as yf
        _old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            data = yf.download(tickers, period="1d", interval="1d", progress=False, auto_adjust=True, timeout=30)
        finally:
            sys.stderr = _old_stderr
        if data is not None and not data.empty:
            if len(tickers) == 1:
                if hasattr(data.columns, "levels"):
                    data.columns = data.columns.get_level_values(0)
                if not data.empty and "Close" in data.columns:
                    try:
                        price = float(data["Close"].iloc[-1])
                        if price > 0:
                            vol = int(float(data["Volume"].iloc[-1])) if "Volume" in data.columns else 0
                            out[tickers[0]] = {"price": round(price, 2), "volume": vol, "change_pct": None, "source": "yfinance"}
                    except (TypeError, ValueError, IndexError):
                        pass
            else:
                if hasattr(data.columns, "levels") and "Close" in data.columns.get_level_values(0):
                    close = data["Close"] if "Close" in data.columns else None
                    if close is not None:
                        for t in tickers:
                            try:
                                if t in close.columns:
                                    val = close[t].iloc[-1]
                                    if val is not None and val == val and float(val) > 0:
                                        vol = 0
                                        if "Volume" in data.columns and t in data["Volume"].columns:
                                            try:
                                                vol = int(float(data["Volume"][t].iloc[-1]))
                                            except Exception:
                                                pass
                                        out[t] = {"price": round(float(val), 2), "volume": vol, "change_pct": None, "source": "yfinance"}
                            except Exception:
                                pass
        missing_after_yf = [t for t in tickers if t not in out]
    except Exception:
        missing_after_yf = tickers

    # 2. finviz for missing (one at a time)
    still_missing = []
    for t in missing_after_yf:
        pv = get_price_volume(t, config)
        if pv:
            out[t] = pv
        else:
            still_missing.append(t)

    # 3. alpaca batch for still missing
    if still_missing:
        try:
            from alpaca_data import has_alpaca_keys, get_price_volume_batch as alpaca_batch
            if has_alpaca_keys(config):
                pv = alpaca_batch(still_missing, config)
                for t, d in pv.items():
                    if d and d.get("price") and d["price"] > 0:
                        out[t] = {"price": d["price"], "volume": d.get("volume", 0), "change_pct": d.get("change_pct"), "source": "alpaca"}
        except Exception:
            pass

    return out
