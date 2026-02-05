"""
ClearBlueSky – News & sentiment (Alpha Vantage NEWS_SENTIMENT).
Optional: score headline sentiment, flag earnings in topics.
"""

import time

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

AV_BASE = "https://www.alphavantage.co/query"
LIMIT_PER_TICKER = 10


def get_sentiment_for_ticker(ticker, api_key, limit=LIMIT_PER_TICKER):
    """
    Fetch news sentiment for a ticker from Alpha Vantage NEWS_SENTIMENT.
    Returns dict: sentiment_score (float -1 to 1 or None), sentiment_label (Bearish/Neutral/Somewhat_Bullish/etc),
    earnings_in_topics (bool), relevance_avg (float), headlines (list of {title, url, time_published}).
    On failure or no key, returns empty/default dict.
    """
    out = {"sentiment_score": None, "sentiment_label": None, "earnings_in_topics": False, "relevance_avg": None, "headlines": []}
    if not REQUESTS_AVAILABLE or not (api_key or "").strip():
        return out
    api_key = api_key.strip()
    try:
        params = {"function": "NEWS_SENTIMENT", "tickers": ticker, "limit": min(limit, 50), "apikey": api_key}
        r = requests.get(AV_BASE, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        feed = data.get("feed") or []
        if not feed:
            return out
        scores = []
        relevance_list = []
        headlines = []
        earnings_in_topics = False
        for item in feed:
            ts = item.get("time_published", "")[:8] if item.get("time_published") else ""
            headlines.append({
                "title": (item.get("title") or "").strip(),
                "url": (item.get("url") or "").strip(),
                "time_published": ts,
            })
            for t in (item.get("topics") or []):
                if (t.get("topic") or "").lower() == "earnings":
                    earnings_in_topics = True
                    break
            ticker_sentiment = item.get("ticker_sentiment") or []
            for ts in ticker_sentiment:
                if (ts.get("ticker") or "").upper() == ticker.upper():
                    try:
                        s = float(ts.get("sentiment_score"))
                        if -1 <= s <= 1:
                            scores.append(s)
                    except (TypeError, ValueError):
                        pass
                    try:
                        rel = float(ts.get("relevance_score"))
                        if 0 <= rel <= 1:
                            relevance_list.append(rel)
                    except (TypeError, ValueError):
                        pass
                    break
        out["earnings_in_topics"] = earnings_in_topics
        out["headlines"] = headlines[:5]
        if scores:
            out["sentiment_score"] = round(sum(scores) / len(scores), 4)
        if relevance_list:
            out["relevance_avg"] = round(sum(relevance_list) / len(relevance_list), 4)
        if out["sentiment_score"] is not None:
            s = out["sentiment_score"]
            if s <= -0.35:
                out["sentiment_label"] = "Bearish"
            elif s <= -0.15:
                out["sentiment_label"] = "Somewhat_Bearish"
            elif s < 0.15:
                out["sentiment_label"] = "Neutral"
            elif s < 0.35:
                out["sentiment_label"] = "Somewhat_Bullish"
            else:
                out["sentiment_label"] = "Bullish"
    except Exception:
        pass
    return out
