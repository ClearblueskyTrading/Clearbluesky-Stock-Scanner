"""
ClearBlueSky – News & sentiment.

Sources:
- Alpha Vantage NEWS_SENTIMENT (if API key provided)
- Optional FinBERT local scoring (transformers) for headline sentiment
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


# ---- FinBERT local scoring ----
def get_finbert_sentiment(headlines):
    """
    Optional local sentiment using FinBERT.
    Requires: pip install transformers torch
    headlines: list of headline strings
    Returns: dict with sentiment_score (-1..1), sentiment_label, per_item breakdown.
    """
    try:
        from finbert_scorer import score_headlines
    except Exception:
        return {"sentiment_score": None, "sentiment_label": None, "per_item": []}
    return score_headlines(headlines or [])


def finbert_rolling_from_headlines(headlines_with_time, now_ts=None):
    """
    Compute FinBERT sentiment with rolling windows using headline timestamps.
    headlines_with_time: list of dicts {title, time_published: YYYYMMDDHHMM...}
    Returns dict with overall + 1h/4h/1d scores and counts.
    """
    from datetime import datetime, timedelta
    try:
        from finbert_scorer import score_headlines
    except Exception:
        return {
            "finbert_score": None,
            "finbert_label": None,
            "finbert_score_1h": None,
            "finbert_score_4h": None,
            "finbert_score_1d": None,
            "finbert_count_1h": 0,
            "finbert_count_4h": 0,
            "finbert_count_1d": 0,
        }

    now = now_ts or datetime.utcnow()

    def parse_ts(ts_str):
        if not ts_str:
            return None
        try:
            return datetime.strptime(ts_str[:12], "%Y%m%d%H%M")
        except Exception:
            try:
                return datetime.strptime(ts_str[:8], "%Y%m%d")
            except Exception:
                return None

    # Overall
    texts = [h.get("title") for h in headlines_with_time if h.get("title")]
    overall = score_headlines(texts) if texts else {"sentiment_score": None, "sentiment_label": None}

    def window_scores(hours):
        cutoff = now - timedelta(hours=hours)
        texts_w = []
        for h in headlines_with_time:
            ts = parse_ts(h.get("time_published"))
            if ts and ts >= cutoff and h.get("title"):
                texts_w.append(h["title"])
        if not texts_w:
            return None, 0
        res = score_headlines(texts_w)
        return res.get("sentiment_score"), len(texts_w)

    s1, c1 = window_scores(1)
    s4, c4 = window_scores(4)
    s24, c24 = window_scores(24)

    return {
        "finbert_score": overall.get("sentiment_score"),
        "finbert_label": overall.get("sentiment_label"),
        "finbert_score_1h": s1,
        "finbert_score_4h": s4,
        "finbert_score_1d": s24,
        "finbert_count_1h": c1,
        "finbert_count_4h": c4,
        "finbert_count_1d": c24,
    }
