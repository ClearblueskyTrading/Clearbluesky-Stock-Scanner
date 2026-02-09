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


def _fetch_market_snapshot():
    """Fetch latest price + daily change for key market ETFs via yfinance."""
    snapshot = []
    try:
        import yfinance as yf
        symbols = list(MARKET_SYMBOLS.keys())
        data = yf.download(symbols, period="5d", progress=False, group_by="ticker", timeout=30)
        for sym, label in MARKET_SYMBOLS.items():
            try:
                if len(MARKET_SYMBOLS) > 1:
                    closes = data[sym]["Close"].dropna()
                else:
                    closes = data["Close"].dropna()
                if len(closes) < 1:
                    continue
                price = round(float(closes.iloc[-1]), 2)
                change_pct = None
                if len(closes) >= 2:
                    prev = float(closes.iloc[-2])
                    if prev:
                        change_pct = round((price - prev) / prev * 100, 2)
                snapshot.append({
                    "symbol": sym,
                    "name": label,
                    "price": price,
                    "change_pct": change_pct,
                })
            except Exception:
                continue
    except Exception:
        pass
    return snapshot


def _fetch_overnight_markets():
    """Fetch latest price + daily change for overseas/overnight market ETFs."""
    snapshot = []
    try:
        import yfinance as yf
        symbols = list(OVERNIGHT_SYMBOLS.keys())
        data = yf.download(symbols, period="5d", progress=False, group_by="ticker", timeout=30)
        for sym, label in OVERNIGHT_SYMBOLS.items():
            try:
                if len(OVERNIGHT_SYMBOLS) > 1:
                    closes = data[sym]["Close"].dropna()
                else:
                    closes = data["Close"].dropna()
                if len(closes) < 1:
                    continue
                price = round(float(closes.iloc[-1]), 2)
                change_pct = None
                if len(closes) >= 2:
                    prev = float(closes.iloc[-2])
                    if prev and prev != 0:
                        change_pct = round((price - prev) / prev * 100, 2)
                snapshot.append({
                    "symbol": sym,
                    "name": label,
                    "price": price,
                    "change_pct": change_pct,
                })
            except Exception:
                continue
    except Exception:
        pass
    return snapshot


# ---------------------------------------------------------------------------
# Public API – gather everything
# ---------------------------------------------------------------------------

def gather_market_intel(progress_callback=None):
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
    }

    # Run fetches in controlled parallel — max 2 workers to be polite to Finviz + yfinance
    tasks = {
        "google_news": _fetch_google_news,
        "finviz_news": _fetch_finviz_news,
        "sector_performance": _fetch_sector_performance,
        "market_snapshot": _fetch_market_snapshot,
        "overnight_markets": _fetch_overnight_markets,
    }
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(fn): key for key, fn in tasks.items()}
        for future in as_completed(futures):
            key = futures[future]
            try:
                result[key] = future.result(timeout=60)
            except Exception:
                result[key] = []
            time.sleep(0.3)  # polite delay between completing tasks

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
