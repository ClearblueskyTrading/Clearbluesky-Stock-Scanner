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

# GICS sector names (CSV) -> Velocity scan sector names
_GICS_TO_FINVIZ = {
    "Health Care": "Healthcare",
    "Consumer Staples": "Consumer Defensive",
    "Consumer Discretionary": "Consumer Cyclical",
    "Information Technology": "Technology",
    "Financials": "Financial",
    "Materials": "Basic Materials",
}

_SP500_CSV_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"

def _fetch_sp500_from_csv(progress_callback=None) -> List[Dict[str, Any]]:
    """Fetch full S&P 500 with sectors from GitHub CSV. Returns [] on failure."""
    try:
        import urllib.request
        req = urllib.request.Request(_SP500_CSV_URL, headers={"User-Agent": "ClearBlueSky/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return []
    rows = []
    lines = raw.strip().split("\n")
    if not lines:
        return []
    header = lines[0].split(",")
    try:
        sym_idx = header.index("Symbol")
        sector_idx = header.index("GICS Sector")
    except ValueError:
        return []
    for line in lines[1:]:
        parts = _parse_csv_line(line)
        if len(parts) <= max(sym_idx, sector_idx):
            continue
        t = (parts[sym_idx] or "").strip().upper().replace("BRK-B", "BRK.B")
        if not t:
            continue
        gics = (parts[sector_idx] or "").strip()
        sector = _GICS_TO_FINVIZ.get(gics, gics) if gics else "Unknown"
        rows.append({"Ticker": t, "Sector": sector, "Industry": sector})
    return rows

def _parse_csv_line(line: str) -> List[str]:
    """Simple CSV line parse (handles quoted fields)."""
    parts = []
    current = []
    in_quote = False
    for c in line:
        if c == '"':
            in_quote = not in_quote
        elif in_quote:
            current.append(c)
        elif c == ",":
            parts.append("".join(current))
            current = []
        else:
            current.append(c)
    parts.append("".join(current))
    return parts

# Embedded fallback (used only when both Finviz and CSV fetch fail)
_FALLBACK_SP500 = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "BRK.B", "BRK-B", "JPM", "V", "UNH",
    "XOM", "JNJ", "WMT", "PG", "MA", "HD", "CVX", "MRK", "ABBV", "PEP", "KO", "COST", "AVGO",
    "MCD", "CSCO", "ACN", "ABT", "TMO", "DHR", "ADBE", "NEE", "NFLX", "WFC", "DIS", "CRM",
]
# Sector mapping for fallback (so velocity scan sector filter works)
_FALLBACK_SECTORS = {
    "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Technology", "GOOGL": "Communication Services",
    "GOOG": "Communication Services", "AMZN": "Consumer Cyclical", "META": "Communication Services",
    "BRK.B": "Financial", "JPM": "Financial", "V": "Financial", "UNH": "Healthcare", "XOM": "Energy",
    "JNJ": "Healthcare", "WMT": "Consumer Defensive", "PG": "Consumer Defensive", "MA": "Financial",
    "HD": "Consumer Cyclical", "CVX": "Energy", "MRK": "Healthcare", "ABBV": "Healthcare",
    "PEP": "Consumer Defensive", "KO": "Consumer Defensive", "COST": "Consumer Defensive",
    "AVGO": "Technology", "MCD": "Consumer Cyclical", "CSCO": "Technology", "ACN": "Technology",
    "ABT": "Healthcare", "TMO": "Healthcare", "DHR": "Healthcare", "ADBE": "Technology",
    "NEE": "Utilities", "NFLX": "Communication Services", "WFC": "Financial", "DIS": "Communication Services",
    "CRM": "Technology", "PM": "Consumer Defensive", "TXN": "Technology", "BMY": "Healthcare",
    "RTX": "Industrials", "UPS": "Industrials", "HON": "Industrials", "ORCL": "Technology",
    "INTC": "Technology", "AMD": "Technology", "QCOM": "Technology", "T": "Communication Services",
    "COP": "Energy", "IBM": "Technology", "GE": "Industrials", "CAT": "Industrials", "BA": "Industrials",
    "GS": "Financial", "MS": "Financial", "AXP": "Financial", "BLK": "Financial", "SBUX": "Consumer Cyclical",
    "DE": "Industrials", "INTU": "Technology", "LOW": "Consumer Cyclical", "AMGN": "Healthcare",
    "GILD": "Healthcare", "MDT": "Healthcare", "ISRG": "Healthcare", "VRTX": "Healthcare", "REGN": "Healthcare",
    "LMT": "Industrials", "ADI": "Technology", "BKNG": "Consumer Cyclical", "SYK": "Healthcare",
    "TJX": "Consumer Cyclical", "MMC": "Financial", "CI": "Healthcare", "DUK": "Utilities",
    "SO": "Utilities", "CMCSA": "Communication Services", "EOG": "Energy", "MO": "Consumer Defensive",
    "APD": "Basic Materials", "BDX": "Healthcare", "CL": "Consumer Defensive", "BSX": "Healthcare",
    "ITW": "Industrials",
    # Sector ETFs (for ImportError fallback when CURATED_ETFS included)
    "XLK": "Technology", "XLF": "Financial", "XLE": "Energy", "XLV": "Healthcare",
    "XLI": "Industrials", "XLP": "Consumer Defensive", "XLY": "Consumer Cyclical",
    "XLU": "Utilities", "XLB": "Basic Materials", "XLRE": "Real Estate", "XLC": "Communication Services",
}

def _sector_for_ticker(t: str) -> str:
    """Sector for fallback/curated ticker. Unknown → ETF for non-mapped tickers."""
    return _FALLBACK_SECTORS.get(t, "ETF")


def fetch_sp500_only(progress_callback=None) -> List[Dict[str, Any]]:
    """Fetch S&P 500 only. Finviz → CSV fallback → embedded fallback."""
    try:
        from finviz.screener import Screener
    except ImportError:
        sp500_rows = _fetch_sp500_from_csv(progress_callback)
        if sp500_rows:
            return sp500_rows
        return [_build_fallback_row(t) for t in _FALLBACK_SP500]
    if progress_callback:
        progress_callback("Fetching S&P 500...")
    try:
        screener = Screener(filters=["idx_sp500"], order="ticker")
        return [dict(stock) for stock in screener]
    except Exception as e:
        if progress_callback:
            progress_callback(f"Finviz failed ({e}), trying S&P 500 CSV...")
        sp500_rows = _fetch_sp500_from_csv(progress_callback)
        if sp500_rows:
            return sp500_rows
        if progress_callback:
            progress_callback("CSV failed, using embedded fallback...")
        return [_build_fallback_row(t) for t in _FALLBACK_SP500]


def _build_fallback_row(ticker: str) -> Dict[str, Any]:
    t = str(ticker).strip().upper().replace("BRK-B", "BRK.B")
    sector = _sector_for_ticker(t)
    return {"Ticker": t, "Sector": sector, "Industry": sector}


def fetch_etfs_only(progress_callback=None) -> List[Dict[str, Any]]:
    """Fetch ETFs only. Finviz full screener → curated fallback (~45 ETFs)."""
    SECTOR_ETF_MAP = {
        "XLK": "Technology", "XLF": "Financial", "XLE": "Energy", "XLV": "Healthcare",
        "XLI": "Industrials", "XLP": "Consumer Defensive", "XLY": "Consumer Cyclical",
        "XLU": "Utilities", "XLB": "Basic Materials", "XLRE": "Real Estate", "XLC": "Communication Services",
    }

    def _curated_rows():
        return [{"Ticker": t.strip().upper(), "Sector": SECTOR_ETF_MAP.get(t.strip().upper(), "ETF"), "Industry": "ETF"} for t in CURATED_ETFS if t]

    try:
        from finviz.screener import Screener
    except ImportError:
        if progress_callback:
            progress_callback("Finviz not installed, using curated ETFs...")
        return _curated_rows()
    if progress_callback:
        progress_callback("Fetching ETFs...")
    try:
        screener = Screener(filters=["ind_exchangetradedfund"], order="ticker")
        return [dict(stock) for stock in screener]
    except Exception as e:
        if progress_callback:
            progress_callback(f"Finviz failed ({e}), using curated ETFs...")
        return _curated_rows()


def fetch_sp500_plus_curated_etfs(progress_callback=None) -> List[Dict[str, Any]]:
    """
    Fast fetch for momentum scans: S&P 500 from Finviz + curated ETF list.
    Skips full ETF screener (~250 tickers) — saves ~1.5 min.
    Falls back to static list if Finviz fails.
    """
    seen = set()
    rows = []
    try:
        from finviz.screener import Screener
    except ImportError:
        if progress_callback:
            progress_callback("Finviz not installed, trying S&P 500 CSV...")
        sp500_rows = _fetch_sp500_from_csv(progress_callback)
        if sp500_rows:
            for r in sp500_rows:
                t = (r.get("Ticker") or "").strip().upper().replace("BRK-B", "BRK.B")
                if t and t not in seen:
                    seen.add(t)
                    rows.append(r)
        if not rows:
            if progress_callback:
                progress_callback("CSV failed, using embedded fallback...")
            for t in _FALLBACK_SP500:
                t = str(t).strip().upper().replace("BRK-B", "BRK.B")
                if t and t not in seen:
                    seen.add(t)
                    sector = _sector_for_ticker(t)
                    rows.append({"Ticker": t, "Sector": sector, "Industry": sector})
        for t in CURATED_ETFS:
            t = t.strip().upper()
            if t and t not in seen:
                seen.add(t)
                sector = _sector_for_ticker(t)
                rows.append({"Ticker": t, "Sector": sector, "Industry": sector})
        return rows
    if progress_callback:
        progress_callback("Fetching S&P 500...")
    try:
        screener = Screener(filters=["idx_sp500"], order="ticker")
        for stock in screener:
            t = (stock.get("Ticker") or "").strip().upper()
            if t and t not in seen:
                seen.add(t)
                rows.append(dict(stock))
    except Exception as e:
        if progress_callback:
            progress_callback(f"Finviz failed ({e}), trying S&P 500 CSV...")
        sp500_rows = _fetch_sp500_from_csv(progress_callback)
        if sp500_rows:
            for r in sp500_rows:
                t = (r.get("Ticker") or "").strip().upper().replace("BRK-B", "BRK.B")
                if t and t not in seen:
                    seen.add(t)
                    rows.append(r)
        else:
            if progress_callback:
                progress_callback("CSV failed, using embedded fallback...")
            for t in _FALLBACK_SP500:
                t = str(t).strip().upper().replace("BRK-B", "BRK.B")
                if t and t not in seen:
                    seen.add(t)
                    sector = _sector_for_ticker(t)
                    rows.append({"Ticker": t, "Sector": sector, "Industry": sector})
    if not rows:
        if progress_callback:
            progress_callback("Finviz returned empty, trying S&P 500 CSV...")
        sp500_rows = _fetch_sp500_from_csv(progress_callback)
        if sp500_rows:
            for r in sp500_rows:
                t = (r.get("Ticker") or "").strip().upper().replace("BRK-B", "BRK.B")
                if t and t not in seen:
                    seen.add(t)
                    rows.append(r)
        else:
            if progress_callback:
                progress_callback("CSV failed, using embedded fallback...")
            for t in _FALLBACK_SP500:
                t = str(t).strip().upper().replace("BRK-B", "BRK.B")
                if t and t not in seen:
                    seen.add(t)
                    sector = _sector_for_ticker(t)
                    rows.append({"Ticker": t, "Sector": sector, "Industry": sector})
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
    Returns list of stock dicts (Finviz keys); fallbacks on failure.
    """
    if index not in ("sp500", "etfs", "sp500_etfs"):
        return []
    if index == "sp500":
        return fetch_sp500_only(progress_callback)
    if index == "etfs":
        return fetch_etfs_only(progress_callback)
    # sp500_etfs: combined
    return fetch_sp500_plus_curated_etfs(progress_callback)
