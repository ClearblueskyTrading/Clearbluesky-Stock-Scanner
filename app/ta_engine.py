"""
ClearBlueSky – Programmatic technical analysis (yfinance + pandas-ta).
Computes MAs, BB, RSI, MACD, ATR, OBV, Fib levels for each ticker.
"""

import os
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False


def get_ta_for_ticker(ticker, period="6mo", interval="1d"):
    """
    Fetch OHLCV and compute TA for a ticker. Returns a dict of computed values (latest).
    Keys: sma20, sma50, sma200, rsi, macd_hist, bb_upper, bb_mid, bb_lower, atr, obv,
    fib_38, fib_50, fib_62, price_vs_sma20, price_vs_sma50, price_vs_sma200.
    On failure or missing deps, returns empty dict or partial dict.
    """
    out = {}
    if not YF_AVAILABLE or not PANDAS_AVAILABLE:
        return out

    try:
        sym = yf.Ticker(ticker)
        df = sym.history(period=period, interval=interval)
        if df is None or df.empty or len(df) < 30:
            return out
        df = df.astype(float, errors="ignore")
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"] if "Volume" in df else None

        # SMAs
        out["sma20"] = _last(close.rolling(20).mean())
        out["sma50"] = _last(close.rolling(50).mean())
        out["sma200"] = _last(close.rolling(200).mean()) if len(close) >= 200 else None
        last_close = _last(close)
        out["close"] = last_close
        out["price_vs_sma20"] = _pct(last_close, out["sma20"])
        out["price_vs_sma50"] = _pct(last_close, out["sma50"])
        out["price_vs_sma200"] = _pct(last_close, out["sma200"])

        # RSI
        if PANDAS_TA_AVAILABLE:
            rsi_ = ta.rsi(close, length=14)
            out["rsi"] = _last(rsi_)
        else:
            out["rsi"] = _rsi_manual(close, 14)

        # MACD
        if PANDAS_TA_AVAILABLE:
            macd = ta.macd(close, fast=12, slow=26, signal=9)
            if macd is not None and not macd.empty:
                if isinstance(macd, pd.DataFrame):
                    hist_col = [c for c in macd.columns if "h" in c.lower() or "hist" in c.lower()]
                    hist = macd[hist_col[0]] if hist_col else (macd.iloc[:, 2] if len(macd.columns) >= 3 else None)
                    out["macd_hist"] = _last(hist) if hist is not None else None
                else:
                    out["macd_hist"] = _last(macd)
        else:
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            sig = macd_line.ewm(span=9, adjust=False).mean()
            out["macd_hist"] = _last(macd_line - sig)

        # Bollinger Bands
        if PANDAS_TA_AVAILABLE:
            bb = ta.bbands(close, length=20, std=2)
            if bb is not None and not bb.empty:
                if isinstance(bb, pd.DataFrame):
                    out["bb_upper"] = _last(bb.iloc[:, 0]) if len(bb.columns) >= 1 else None
                    out["bb_mid"] = _last(bb.iloc[:, 1]) if len(bb.columns) >= 2 else None
                    out["bb_lower"] = _last(bb.iloc[:, 2]) if len(bb.columns) >= 3 else None
                else:
                    out["bb_upper"] = out["bb_mid"] = out["bb_lower"] = None
        else:
            mid = close.rolling(20).mean()
            std = close.rolling(20).std()
            out["bb_upper"] = _last(mid + 2 * std)
            out["bb_mid"] = _last(mid)
            out["bb_lower"] = _last(mid - 2 * std)

        # ATR (14)
        if PANDAS_TA_AVAILABLE:
            atr_ = ta.atr(high, low, close, length=14)
            out["atr"] = _last(atr_)
        else:
            tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
            out["atr"] = _last(tr.rolling(14).mean())

        # OBV
        if volume is not None and not volume.empty:
            d = close.diff()
            direction = d.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
            obv = (volume * direction).cumsum()
            out["obv"] = _last(obv)
        else:
            out["obv"] = None

        # Fib levels from recent swing (last 60 bars)
        lookback = min(60, len(close))
        recent_high = high.tail(lookback).max()
        recent_low = low.tail(lookback).min()
        span = recent_high - recent_low
        if span and span > 0:
            out["fib_38"] = round(recent_high - 0.382 * span, 2)
            out["fib_50"] = round(recent_high - 0.5 * span, 2)
            out["fib_62"] = round(recent_high - 0.618 * span, 2)
            out["recent_high"] = round(recent_high, 2)
            out["recent_low"] = round(recent_low, 2)
        else:
            out["fib_38"] = out["fib_50"] = out["fib_62"] = out["recent_high"] = out["recent_low"] = None

    except Exception:
        pass
    return out


def _last(series):
    if series is None or (hasattr(series, "empty") and series.empty):
        return None
    try:
        v = series.dropna().iloc[-1]
        return round(float(v), 4) if v is not None else None
    except Exception:
        return None


def _pct(price, base):
    if price is None or base is None or not base:
        return None
    try:
        return round((float(price) - float(base)) / float(base) * 100, 2)
    except Exception:
        return None


def _rsi_manual(close, length=14):
    try:
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1 / length, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / length, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return _last(rsi)
    except Exception:
        return None


def format_ta_for_report(ta_dict):
    """Format TA dict as a short multi-line string for report body."""
    if not ta_dict:
        return "TA: (unavailable)"
    parts = []
    if ta_dict.get("close") is not None:
        parts.append(f"Close={ta_dict['close']}")
    if ta_dict.get("sma20") is not None:
        parts.append(f"SMA20={ta_dict['sma20']}")
    if ta_dict.get("sma50") is not None:
        parts.append(f"SMA50={ta_dict['sma50']}")
    if ta_dict.get("sma200") is not None:
        parts.append(f"SMA200={ta_dict['sma200']}")
    if ta_dict.get("rsi") is not None:
        parts.append(f"RSI={ta_dict['rsi']}")
    if ta_dict.get("macd_hist") is not None:
        parts.append(f"MACD_hist={ta_dict['macd_hist']}")
    if ta_dict.get("atr") is not None:
        parts.append(f"ATR={ta_dict['atr']}")
    if ta_dict.get("bb_upper") is not None and ta_dict.get("bb_lower") is not None:
        parts.append(f"BB=[{ta_dict['bb_lower']}, {ta_dict['bb_upper']}]")
    if ta_dict.get("fib_38") is not None:
        parts.append(f"Fib38/50/62={ta_dict['fib_38']}/{ta_dict.get('fib_50')}/{ta_dict.get('fib_62')}")
    if not parts:
        return "TA: (unavailable)"
    return "TA: " + " | ".join(parts)
