# breadth.py - Market Breadth Calculator
# ClearBlueSky - Add market breadth (SMA %, A/D, RSI, sector rotation, regime) to scan output.

from collections import Counter
from datetime import datetime
from typing import Dict, List, Any, Optional


def calculate_market_breadth(all_stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate market breadth metrics from index stock data (e.g. S&P 500).

    Args:
        all_stocks: List of stock dicts from Finviz with keys like:
                   'Ticker', 'Sector', 'RSI', 'RSI (14)', 'SMA50', 'SMA200',
                   '50-Day Simple Moving Average', '200-Day Simple Moving Average',
                   'Change', 'Rel Volume', 'Relative Volume', etc.

    Returns:
        Dictionary with breadth metrics for JSON output.
    """
    if not all_stocks:
        return {"error": "No stock data provided"}

    total = len(all_stocks)

    # --- SMA Calculations ---
    above_sma50 = 0
    above_sma200 = 0

    for stock in all_stocks:
        sma50_pct = _parse_percent(
            stock.get("SMA50")
            or stock.get("50-Day Simple Moving Average")
            or stock.get("sma50", "0")
        )
        sma200_pct = _parse_percent(
            stock.get("SMA200")
            or stock.get("200-Day Simple Moving Average")
            or stock.get("sma200", "0")
        )
        if sma50_pct is not None and sma50_pct > 0:
            above_sma50 += 1
        if sma200_pct is not None and sma200_pct > 0:
            above_sma200 += 1

    # --- Advance/Decline ---
    advancers = 0
    decliners = 0

    for stock in all_stocks:
        change = _parse_percent(stock.get("Change") or stock.get("change", "0"))
        if change is not None:
            if change > 0:
                advancers += 1
            elif change < 0:
                decliners += 1

    advance_decline = advancers - decliners

    # --- RSI Analysis ---
    rsi_values = []
    oversold_count = 0
    overbought_count = 0

    for stock in all_stocks:
        rsi = _parse_float(
            stock.get("RSI (14)") or stock.get("RSI") or stock.get("rsi", "50")
        )
        if rsi is not None:
            rsi_values.append(rsi)
            if rsi < 30:
                oversold_count += 1
            elif rsi > 70:
                overbought_count += 1

    avg_rsi = (
        round(sum(rsi_values) / len(rsi_values), 2) if rsi_values else None
    )

    # --- Sector Rotation ---
    sector_performance = _calculate_sector_performance(all_stocks)
    sectors_sorted = sorted(
        sector_performance.items(), key=lambda x: x[1], reverse=True
    )
    sectors_leading = [s[0] for s in sectors_sorted[:3] if s[1] > 0]
    sectors_lagging = [s[0] for s in sectors_sorted[-3:] if s[1] < 0]

    # --- Volume Analysis ---
    high_volume_count = 0
    for stock in all_stocks:
        rel_vol = _parse_float(
            stock.get("Rel Volume")
            or stock.get("Relative Volume")
            or stock.get("rel_volume", "1")
        )
        if rel_vol is not None and rel_vol > 1.5:
            high_volume_count += 1

    # --- Market Regime Classification ---
    regime = _classify_market_regime(
        pct_above_sma50=round((above_sma50 / total) * 100, 1),
        pct_above_sma200=round((above_sma200 / total) * 100, 1),
        advance_decline=advance_decline,
        avg_rsi=avg_rsi,
    )

    return {
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "scan_time": datetime.now().strftime("%H:%M:%S"),
        "total_stocks_analyzed": total,
        "sp500_above_sma50": above_sma50,
        "sp500_above_sma50_pct": round((above_sma50 / total) * 100, 1),
        "sp500_above_sma200": above_sma200,
        "sp500_above_sma200_pct": round((above_sma200 / total) * 100, 1),
        "advancers": advancers,
        "decliners": decliners,
        "advance_decline": advance_decline,
        "advance_decline_ratio": (
            round(advancers / decliners, 2) if decliners > 0 else None
        ),
        "avg_rsi_sp500": avg_rsi,
        "stocks_oversold_rsi30": oversold_count,
        "stocks_overbought_rsi70": overbought_count,
        "sectors_leading": sectors_leading,
        "sectors_lagging": sectors_lagging,
        "sector_performance": sector_performance,
        "high_relative_volume_count": high_volume_count,
        "market_regime": regime,
    }


def _calculate_sector_performance(stocks: List[Dict]) -> Dict[str, float]:
    """Calculate average daily change by sector."""
    sector_changes: Dict[str, float] = {}
    sector_counts: Counter = Counter()

    for stock in stocks:
        sector = stock.get("Sector") or stock.get("sector", "Unknown")
        change = _parse_percent(
            stock.get("Change") or stock.get("change", "0")
        )
        if sector and change is not None:
            sector_changes[sector] = sector_changes.get(sector, 0) + change
            sector_counts[sector] += 1

    return {
        sector: round(sector_changes[sector] / sector_counts[sector], 2)
        for sector in sector_changes
        if sector_counts[sector] > 0
    }


def _classify_market_regime(
    pct_above_sma50: float,
    pct_above_sma200: float,
    advance_decline: int,
    avg_rsi: Optional[float],
) -> str:
    """
    Classify current market regime for position sizing guidance.

    Returns one of:
    STRONG_BULL, BULL, NEUTRAL, BEAR, STRONG_BEAR
    """
    score = 0

    if pct_above_sma50 >= 70:
        score += 2
    elif pct_above_sma50 >= 55:
        score += 1
    elif pct_above_sma50 <= 30:
        score -= 2
    elif pct_above_sma50 <= 45:
        score -= 1

    if pct_above_sma200 >= 70:
        score += 1
    elif pct_above_sma200 <= 40:
        score -= 1

    if advance_decline > 200:
        score += 1
    elif advance_decline < -200:
        score -= 1

    if avg_rsi is not None and avg_rsi > 60:
        score += 1
    elif avg_rsi is not None and avg_rsi < 40:
        score -= 1

    if score >= 4:
        return "STRONG_BULL"
    elif score >= 2:
        return "BULL"
    elif score <= -4:
        return "STRONG_BEAR"
    elif score <= -2:
        return "BEAR"
    else:
        return "NEUTRAL"


def _parse_percent(value: Any) -> Optional[float]:
    """Parse percentage string like '-2.35%' or '5.67%' to float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(
            str(value).replace("%", "").replace(",", "").strip()
        )
    except (ValueError, TypeError):
        return None


def _parse_float(value: Any) -> Optional[float]:
    """Parse numeric string to float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        s = str(value).replace(",", "").replace("x", "").strip()
        return float(s)
    except (ValueError, TypeError):
        return None


# Hard floor used by scanner ETF paths (avg volume).
ETF_MIN_AVG_VOLUME = 100_000

# Curated ETF universe — focused and liquid, with leveraged bull + bear coverage.
# This avoids full ETF sweeps while still including the most-used leveraged names.
CURATED_ETFS = [
    # Index / broad
    "SPY", "QQQ", "IWM", "DIA",
    # Sector / thematic anchors
    "XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE", "XLC",
    "SMH", "KRE", "XBI", "ARKK", "VNQ",
    # Commodities / macro
    "GLD", "SLV", "GDX", "USO", "UNG",
    # Leveraged bull (core)
    "TQQQ", "QLD", "UPRO", "SSO", "SPXL", "TNA", "SOXL", "TECL",
    "FAS", "LABU", "ERX", "GUSH", "NUGT", "CURE", "DFEN", "DPST", "UTSL",
    "NVDL", "TSLL", "AAPU", "AMZU", "GGLL", "MSFU", "CONL", "BITX", "BITU",
    "YINN", "EDC",
    # Leveraged bear / inverse (core)
    "SQQQ", "QID", "SPXU", "SDS", "SPXS", "SOXS", "TECS", "TZA",
    "FAZ", "LABD", "ERY", "DRIP", "DUST", "SDOW", "SRTY",
]

def fetch_sp500_plus_curated_etfs(progress_callback=None) -> List[Dict[str, Any]]:
    """
    Fast fetch for momentum scans: S&P 500 from Finviz + curated ETF list.
    Skips full ETF screener (~250 tickers) — saves ~1.5 min.
    """
    seen = set()
    rows = []
    try:
        from finviz.screener import Screener
    except ImportError:
        return []
    if progress_callback:
        progress_callback("Fetching S&P 500...")
    try:
        screener = Screener(filters=["idx_sp500"], order="ticker")
        for stock in screener:
            t = (stock.get("Ticker") or "").strip().upper()
            if t and t not in seen:
                seen.add(t)
                rows.append(dict(stock))
    except Exception:
        pass
    # Sector ETF -> GICS sector (for sector-first filtering in velocity scan)
    SECTOR_ETF_MAP = {
        "XLK": "Technology", "XLF": "Financial", "XLE": "Energy", "XLV": "Healthcare",
        "XLI": "Industrials", "XLP": "Consumer Defensive", "XLY": "Consumer Cyclical",
        "XLU": "Utilities", "XLB": "Basic Materials", "XLRE": "Real Estate", "XLC": "Communication Services",
    }
    for t in CURATED_ETFS:
        t = t.strip().upper()
        if t and t not in seen:
            seen.add(t)
            sector = SECTOR_ETF_MAP.get(t, "ETF")
            rows.append({"Ticker": t, "Sector": sector, "Industry": sector})
    return rows


def fetch_full_index_for_breadth(
    index: str, progress_callback=None
) -> List[Dict[str, Any]]:
    """
    Fetch full index from Finviz for breadth calculation.
    index: 'sp500', 'etfs', or 'sp500_etfs' (S&P 500 + ETFs combined)
    Returns list of stock dicts (Finviz keys); empty list on error.
    """
    if index not in ("sp500", "etfs", "sp500_etfs"):
        return []
    try:
        from finviz.screener import Screener
    except ImportError:
        return []
    if index == "sp500_etfs":
        # Use fast path: S&P 500 + curated ETFs only (skip full 250+ ETF screener)
        return fetch_sp500_plus_curated_etfs(progress_callback)
    idx_filter = "ind_exchangetradedfund" if index == "etfs" else "idx_sp500"
    try:
        if progress_callback:
            progress_callback("Fetching index for breadth...")
        screener = Screener(filters=[idx_filter], order="ticker")
        rows = []
        for stock in screener:
            rows.append(dict(stock))
        return rows
    except Exception:
        return []
