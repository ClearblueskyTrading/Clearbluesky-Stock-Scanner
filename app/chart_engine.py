"""
ClearBlueSky – Chart image generation for Phase 6 vision layer.
Renders OHLC chart with matplotlib; returns base64 PNG for OpenRouter.
"""

import base64
import io
import os
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MPL_AVAILABLE = True
except ImportError:
    MPL_AVAILABLE = False


def get_chart_base64(ticker, period="3mo", figsize=(6, 3), dpi=100):
    """
    Fetch OHLC for ticker and render a simple candlestick-style chart.
    Failover: yfinance first, then Alpaca bars when keys set.
    Returns base64-encoded PNG string (data:image/png;base64,...) or None on failure.
    """
    if not MPL_AVAILABLE:
        return None
    df = None
    if YF_AVAILABLE:
        try:
            sym = yf.Ticker(ticker)
            df = sym.history(period=period, interval="1d")
        except Exception:
            pass
    if df is None or df.empty or len(df) < 5:
        try:
            from alpaca_data import has_alpaca_keys, get_bars, bars_to_dataframe
            if has_alpaca_keys():
                days = 95 if "3mo" in period else (65 if "2mo" in period else 40)
                bars = get_bars(ticker, days=days, timeframe="1Day", limit=100)
                if bars:
                    df = bars_to_dataframe(bars)
        except Exception:
            pass
    if df is None or df.empty or len(df) < 5:
        return None
    try:
        df = df.astype(float, errors="ignore")
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        ax.fill_between(df.index, df["Low"], df["High"], alpha=0.2, color="gray")
        ax.plot(df.index, df["Close"], color="steelblue", linewidth=1.2, label="Close")
        ax.plot(df.index, df["Open"], color="gray", linewidth=0.6, alpha=0.7, linestyle="--")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.xticks(rotation=25)
        ax.set_title(f"{ticker} ({period})")
        ax.legend(loc="upper left", fontsize=7)
        ax.grid(True, alpha=0.3)
        ax.set_ylabel("Price")
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=dpi)
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None


def get_charts_for_tickers(tickers, period="3mo", max_charts=5, progress_callback=None):
    """
    Return list of (ticker, base64_string) for up to max_charts tickers.
    progress_callback(ticker) optional.
    """
    out = []
    for t in tickers[:max_charts]:
        if progress_callback:
            progress_callback(t)
        b64 = get_chart_base64(t, period=period)
        if b64:
            out.append((t, b64))
    return out
