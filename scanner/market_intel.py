"""
ClearBlueSky – Market Intelligence gathering.

Collects broad market context from FREE, API-compliant sources:
  1. Google News RSS  – top stock-market / economy / earnings headlines (no key needed)
  2. Finvizfinance    – curated financial news + blog headlines (already a dependency)
  3. Finvizfinance    – sector performance table (week / month / quarter / YTD)
  4. yfinance         – futures-proxy ETFs snapshot (SPY, QQQ, DIA, GLD, USO, TLT, ^VIX)
  5. yfinance         – overnight/overseas markets (EWJ, FXI, EWZ, EFA, EWG, EWU, INDA, EWT, EWY)

Everything is returned as a single dict suitable for:
  • Injecting into the OpenRouter AI prompt (as text)
  • Saving into the JSON analysis package
"""

import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

# ---------------------------------------------------------------------------
# Google News RSS
# ---------------------------------------------------------------------------

GOOGLE_NEWS_QUERIES = [
    ("Stock Market", "stock+market"),
    ("Economy", "economy+federal+reserve"),
    ("Earnings", "earnings+report+stock"),
]
GOOGLE_NEWS_URL = "https://news.google.com/rss/search?q={query}+when:1d&hl=en-US&gl=US&ceid=US:en"
MAX_HEADLINES_PER_TOPIC = 8


def _fetch_google_news():
    """Fetch headlines from Google News RSS (no API key needed)."""
    try:
        import feedparser
    except ImportError:
        return []

    all_headlines = []
    seen_titles = set()

    for topic_label, query in GOOGLE_NEWS_QUERIES:
        try:
            url = GOOGLE_NEWS_URL.format(query=query)
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries or []:
                if count >= MAX_HEADLINES_PER_TOPIC:
                    break
                title = (entry.get("title") or "").strip()
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)
                # Extract source from title (Google News format: "Title - Source")
                source = ""
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    source = parts[1].strip() if len(parts) > 1 else ""
                published = entry.get("published", "")
                all_headlines.append({
                    "topic": topic_label,
                    "title": title,
                    "source": source,
                    "published": published,
                    "link": entry.get("link", ""),
                })
                count += 1
        except Exception:
            continue

    return all_headlines


# ---------------------------------------------------------------------------
# Finvizfinance – curated news + blogs
# ---------------------------------------------------------------------------

MAX_FINVIZ_HEADLINES = 12


def _fetch_finviz_news():
    """Fetch news + blog headlines from finvizfinance (free, no key)."""
    headlines = []
    try:
        from finvizfinance.news import News
        n = News()
        tables = n.get_news()
        for category in ("news", "blogs"):
            df = tables.get(category)
            if df is None or not hasattr(df, "iterrows"):
                continue
            for _, row in df.head(MAX_FINVIZ_HEADLINES).iterrows():
                title = str(row.get("Title", "")).strip()
                if not title:
                    continue
                headlines.append({
                    "category": category,
                    "title": title,
                    "source": str(row.get("Source", "")).strip(),
                    "date": str(row.get("Date", "")).strip(),
                    "link": str(row.get("Link", "")).strip(),
                })
    except Exception:
        pass
    return headlines


# ---------------------------------------------------------------------------
# Finvizfinance – sector performance
# ---------------------------------------------------------------------------

def _fetch_sector_performance():
    """Fetch sector performance table (week/month/quarter/YTD) from finvizfinance."""
    sectors = []
    try:
        from finvizfinance.group.performance import Performance
        g = Performance()
        df = g.screener_view(group="Sector", order="Name")
        if df is not None and hasattr(df, "iterrows"):
            for _, row in df.iterrows():
                name = str(row.get("Name", "")).strip()
                if not name:
                    continue
                def pct(val):
                    """Convert to percentage string."""
                    try:
                        v = float(val)
                        return f"{v * 100:+.2f}%" if abs(v) < 1 else f"{v:+.2f}%"
                    except (TypeError, ValueError):
                        s = str(val).strip()
                        return s if s else "N/A"

                sectors.append({
                    "name": name,
                    "perf_week": pct(row.get("Perf Week", "")),
                    "perf_month": pct(row.get("Perf Month", "")),
                    "perf_quarter": pct(row.get("Perf Quart", "")),
                    "perf_ytd": pct(row.get("Perf YTD", "")),
                    "change_today": pct(row.get("Change", "")),
                })
    except Exception:
        pass
    return sectors


# ---------------------------------------------------------------------------
# yfinance – market snapshot (futures-proxy ETFs + VIX)
# ---------------------------------------------------------------------------

MARKET_SYMBOLS = {
    "SPY": "S&P 500",
    "QQQ": "Nasdaq 100",
    "DIA": "Dow Jones",
    "GLD": "Gold",
    "USO": "Oil",
    "TLT": "20Y Treasuries",
    "^VIX": "VIX",
}

# Overnight / overseas markets (ETFs that track international indices)
OVERNIGHT_SYMBOLS = {
    "EWJ": "Japan (Nikkei proxy)",
    "FXI": "China (Hang Seng proxy)",
    "EWZ": "Brazil (Bovespa proxy)",
    "EFA": "Europe/Asia Developed (EAFE)",
    "EWG": "Germany (DAX proxy)",
    "EWU": "UK (FTSE proxy)",
    "INDA": "India (Nifty proxy)",
    "EWT": "Taiwan (TSMC heavy)",
    "EWY": "South Korea (KOSPI proxy)",
}


# Alpaca supports US equities/ETFs; ^VIX is an index — use yfinance for it
MARKET_SYMBOLS_ALPACA = {k: v for k, v in MARKET_SYMBOLS.items() if not k.startswith("^")}


def _yf_snapshot_from_data(data, symbols, symbol_labels):
    """Build snapshot list from yfinance DataFrame. Returns list of dicts."""
    snapshot = []
    if data is None or data.empty:
        return snapshot
    for sym, label in symbol_labels.items():
        if sym not in symbols:
            continue
        try:
            if len(symbols) > 1 and hasattr(data.columns, "levels") and sym in data.columns.get_level_values(0):
                closes = data[sym]["Close"].dropna()
            elif len(symbols) == 1 and "Close" in data.columns:
                closes = data["Close"].dropna()
            else:
                continue
            if len(closes) < 1:
                continue
            price = round(float(closes.iloc[-1]), 2)
            change_pct = None
            if len(closes) >= 2:
                prev = float(closes.iloc[-2])
                if prev:
                    change_pct = round((price - prev) / prev * 100, 2)
            snapshot.append({"symbol": sym, "name": label, "price": price, "change_pct": change_pct})
        except Exception:
            continue
    return snapshot


def _fetch_market_snapshot(config: Optional[dict] = None):
    """Fetch latest price + daily change. Failover: yfinance first, then Alpaca for missing."""
    snapshot = []
    # 1. yfinance first
    try:
        import yfinance as yf
        data = yf.download(list(MARKET_SYMBOLS.keys()), period="5d", progress=False, group_by="ticker", timeout=30)
        snapshot = _yf_snapshot_from_data(data, list(MARKET_SYMBOLS.keys()), MARKET_SYMBOLS)
    except Exception:
        pass
    # 2. Alpaca for missing (tradeable symbols only; ^VIX stays from yfinance)
    missing = [s for s in MARKET_SYMBOLS_ALPACA if s not in {x["symbol"] for x in snapshot}]
    if missing:
        try:
            from alpaca_data import has_alpaca_keys, get_price_volume_batch
            if has_alpaca_keys(config):
                pv = get_price_volume_batch(missing, config)
                for sym in missing:
                    if sym in pv and pv[sym].get("price"):
                        snapshot.append({
                            "symbol": sym,
                            "name": MARKET_SYMBOLS[sym],
                            "price": pv[sym]["price"],
                            "change_pct": pv[sym].get("change_pct"),
                        })
        except Exception:
            pass
    return snapshot


def _fetch_overnight_markets(config: Optional[dict] = None):
    """Fetch latest price + daily change for overseas/overnight ETFs. Failover: yfinance first, then Alpaca."""
    snapshot = []
    symbols = list(OVERNIGHT_SYMBOLS.keys())
    # 1. yfinance first
    try:
        import yfinance as yf
        data = yf.download(symbols, period="5d", progress=False, group_by="ticker", timeout=30)
        snapshot = _yf_snapshot_from_data(data, symbols, OVERNIGHT_SYMBOLS)
    except Exception:
        pass
    # 2. Alpaca for missing
    missing = [s for s in symbols if s not in {x["symbol"] for x in snapshot}]
    if missing:
        try:
            from alpaca_data import has_alpaca_keys, get_price_volume_batch
            if has_alpaca_keys(config):
                pv = get_price_volume_batch(missing, config)
                for sym in missing:
                    if sym in pv and pv[sym].get("price"):
                        snapshot.append({
                            "symbol": sym,
                            "name": OVERNIGHT_SYMBOLS[sym],
                            "price": pv[sym]["price"],
                            "change_pct": pv[sym].get("change_pct"),
                        })
        except Exception:
            pass
    return snapshot


# ---------------------------------------------------------------------------
# Market pulse – SPY/QQQ % from open, VIX vs 10d avg
# ---------------------------------------------------------------------------

def _fetch_market_pulse():
    """
    Fetch intraday pulse: SPY/QQQ % from today's open, VIX vs 10-day average.
    Uses yfinance. Returns dict with spy_pct_from_open, qqq_pct_from_open, vix, vix_10d_avg, vix_vs_10d.
    """
    pulse = {
        "spy_pct_from_open": None,
        "qqq_pct_from_open": None,
        "vix": None,
        "vix_10d_avg": None,
        "vix_vs_10d": None,
    }
    try:
        import yfinance as yf
        # SPY/QQQ: latest bar = today; (Close - Open) / Open
        for sym, key in [("SPY", "spy_pct_from_open"), ("QQQ", "qqq_pct_from_open")]:
            try:
                d = yf.Ticker(sym)
                h = d.history(period="5d", interval="1d")
                if h is not None and len(h) >= 1 and "Open" in h.columns and "Close" in h.columns:
                    row = h.iloc[-1]
                    o, c = float(row["Open"]), float(row["Close"])
                    if o and o != 0:
                        pulse[key] = round((c - o) / o * 100, 2)
            except Exception:
                pass
        # VIX: current vs 10-day average
        try:
            vix = yf.Ticker("^VIX")
            h = vix.history(period="15d", interval="1d")
            if h is not None and len(h) >= 1:
                pulse["vix"] = round(float(h["Close"].iloc[-1]), 2)
                if len(h) >= 5:
                    avg = float(h["Close"].tail(10).mean())
                    pulse["vix_10d_avg"] = round(avg, 2)
                    curr = pulse["vix"]
                    if curr and avg:
                        if curr > avg * 1.05:
                            pulse["vix_vs_10d"] = "above"
                        elif curr < avg * 0.95:
                            pulse["vix_vs_10d"] = "below"
                        else:
                            pulse["vix_vs_10d"] = "at"
        except Exception:
            pass
    except Exception:
        pass
    return pulse


# ---------------------------------------------------------------------------
# Public API – gather everything
# ---------------------------------------------------------------------------

def gather_market_intel(progress_callback=None, config: Optional[dict] = None):
    """
    Gather all market intelligence in parallel.

    Returns dict:
        {
            "timestamp": "...",
            "google_news": [...],
            "finviz_news": [...],
            "sector_performance": [...],
            "market_snapshot": [...],
        }
    """
    def progress(msg):
        if progress_callback:
            progress_callback(msg)

    progress("Gathering market intelligence...")
    result = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "google_news": [],
        "finviz_news": [],
        "sector_performance": [],
        "market_snapshot": [],
        "overnight_markets": [],
        "market_pulse": {},
    }

    # Run fetches in controlled parallel — max 2 workers to be polite to Finviz + yfinance
    tasks = {
        "google_news": _fetch_google_news,
        "finviz_news": _fetch_finviz_news,
        "sector_performance": _fetch_sector_performance,
        "market_snapshot": lambda: _fetch_market_snapshot(config=config),
        "overnight_markets": lambda: _fetch_overnight_markets(config=config),
        "market_pulse": _fetch_market_pulse,
    }
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(fn): key for key, fn in tasks.items()}
        for future in as_completed(futures):
            key = futures[future]
            try:
                val = future.result(timeout=60)
                result[key] = val if val is not None else ([] if key != "market_pulse" else {})
            except Exception:
                result[key] = [] if key != "market_pulse" else {}
            time.sleep(0.3)  # polite delay between completing tasks

    # market_pulse returns dict, not list — handle non-list results
    if not isinstance(result.get("market_pulse"), dict):
        result["market_pulse"] = {}
    counts = (
        f"{len(result['google_news'])} headlines, "
        f"{len(result['finviz_news'])} Finviz articles, "
        f"{len(result['sector_performance'])} sectors, "
        f"{len(result['market_snapshot'])} US markets, "
        f"{len(result['overnight_markets'])} overseas"
    )
    progress(f"Market intel ready: {counts}")
    return result


def format_intel_for_prompt(intel):
    """
    Convert market_intel dict into a text block for the AI prompt.
    Keeps it concise so it doesn't eat too many tokens.
    """
    if not intel:
        return ""

    lines = [
        "",
        "═══════════════════════════════════════════════════",
        "MARKET INTELLIGENCE (live data)",
        "═══════════════════════════════════════════════════",
    ]

    # Market pulse (SPY/QQQ from open, VIX vs 10d)
    pulse = intel.get("market_pulse") or {}
    if any(pulse.get(k) is not None for k in ("spy_pct_from_open", "qqq_pct_from_open", "vix")):
        lines.append("")
        lines.append("MARKET PULSE (today's intraday context):")
        if pulse.get("spy_pct_from_open") is not None:
            lines.append(f"  SPY from open: {pulse['spy_pct_from_open']:+.2f}%")
        if pulse.get("qqq_pct_from_open") is not None:
            lines.append(f"  QQQ from open: {pulse['qqq_pct_from_open']:+.2f}%")
        if pulse.get("vix") is not None:
            vix_line = f"  VIX: {pulse['vix']}"
            if pulse.get("vix_10d_avg") is not None and pulse.get("vix_vs_10d"):
                vix_line += f" (10d avg {pulse['vix_10d_avg']}, {pulse['vix_vs_10d']} avg)"
            lines.append(vix_line)

    # Market snapshot
    snap = intel.get("market_snapshot", [])
    if snap:
        lines.append("")
        lines.append("MARKET SNAPSHOT:")
        for s in snap:
            chg = f" ({s['change_pct']:+.2f}%)" if s.get("change_pct") is not None else ""
            lines.append(f"  {s['name']}: ${s['price']}{chg}")

    # Overnight / overseas markets
    overnight = intel.get("overnight_markets", [])
    if overnight:
        lines.append("")
        lines.append("OVERNIGHT / OVERSEAS MARKETS:")
        for s in overnight:
            chg = f" ({s['change_pct']:+.2f}%)" if s.get("change_pct") is not None else ""
            lines.append(f"  {s['name']}: ${s['price']}{chg}")

    # Sector performance
    sectors = intel.get("sector_performance", [])
    if sectors:
        lines.append("")
        lines.append("SECTOR PERFORMANCE:")
        lines.append(f"  {'Sector':<25} {'Today':>8} {'Week':>8} {'Month':>8} {'YTD':>8}")
        for s in sectors:
            lines.append(
                f"  {s['name']:<25} {s['change_today']:>8} {s['perf_week']:>8} "
                f"{s['perf_month']:>8} {s['perf_ytd']:>8}"
            )

    # News headlines (Google News + Finviz combined, capped)
    google = intel.get("google_news", [])
    finviz = intel.get("finviz_news", [])
    if google or finviz:
        lines.append("")
        lines.append("TODAY'S MARKET NEWS:")
        shown = 0
        max_total = 20
        for h in google:
            if shown >= max_total:
                break
            src = f" ({h['source']})" if h.get("source") else ""
            lines.append(f"  [{h['topic']}] {h['title']}{src}")
            shown += 1
        for h in finviz:
            if shown >= max_total:
                break
            src = f" ({h['source']})" if h.get("source") else ""
            lines.append(f"  [Finviz {h['category']}] {h['title']}{src}")
            shown += 1

    lines.append("")
    return "\n".join(lines)
