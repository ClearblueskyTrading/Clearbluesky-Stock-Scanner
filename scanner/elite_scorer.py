# ============================================================
# ClearBlueSky - Elite Second-Round Scoring
# ============================================================
# Tight scrutiny for top candidates. Computes elite_score and
# landmine flags (earnings, sentiment) to gate TIER 1 / TOP 5.

from typing import Dict, List, Optional, Tuple


ELITE_THRESHOLD = 80
TOP_CANDIDATES_COUNT = 7


def _to_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def compute_elite_score(row: Dict) -> Tuple[int, bool, List[str]]:
    """
    Second-round scoring for top candidates.
    Returns (elite_score, elite_qualified, landmine_reasons).

    Penalties:
      - Earnings within 2 days: -15 (landmine)
      - Earnings within 5 days: -8
      - Sentiment DANGER: -15 (landmine)
      - Sentiment NEGATIVE: -10
      - RSI > 70 (overbought): -5
      - News danger/negative: -5

    Boosts:
      - Sentiment POSITIVE: +5
      - Above SMA200: +5
      - Relative volume > 2x: +5
      - Insider 10b5-1 plan: +5
    """
    base = int(row.get("score", 0) or 0)
    elite = base
    landmines = []

    # Earnings proximity (from ticker_enrichment or risk_checks)
    days_away = None
    earnings = row.get("earnings") or {}
    rc = row.get("risk_checks") or {}
    days_away = earnings.get("days_away") or rc.get("days_until_earnings")
    if days_away is not None:
        try:
            d = int(days_away)
            if d <= 2:
                elite -= 15
                landmines.append("earnings within 2 days")
            elif d <= 5:
                elite -= 8
        except (ValueError, TypeError):
            pass

    # Sentiment: news_sentiment (ticker enrichment) = DANGER/NEGATIVE/POSITIVE
    # Alpha Vantage sentiment_label = Bearish/Somewhat_Bearish/Neutral/Somewhat_Bullish/Bullish
    news_sentiment = row.get("news_sentiment") or {}
    ns = str(news_sentiment.get("sentiment") or news_sentiment.get("label") or "").upper()
    if "DANGER" in ns:
        elite -= 15
        landmines.append("news DANGER")
    elif "NEGATIVE" in ns:
        elite -= 10
    elif "POSITIVE" in ns:
        elite += 5

    av_label = str(row.get("sentiment_label") or "").lower()
    if "bearish" in av_label and "news DANGER" not in landmines:
        elite -= 8
    elif "bullish" in av_label:
        elite += 3

    # RSI overbought
    rsi = _to_float(row.get("rsi"))
    if rsi is not None and rsi > 70:
        elite -= 5

    # Above SMA200 boost (velocity sets above_sma200; swing/enriched use sma200_status)
    above_sma200 = row.get("above_sma200")
    sma200_status = row.get("sma200_status")
    above = (
        above_sma200 is True
        or (isinstance(above_sma200, str) and "above" in str(above_sma200).lower())
        or (sma200_status and "above" in str(sma200_status).lower())
    )
    if above:
        elite += 5

    # Relative volume
    rel_vol = _to_float(row.get("rel_volume") or row.get("Relative Volume") or row.get("Rel Volume"))
    if rel_vol is not None and rel_vol >= 2.0:
        elite += 5

    # Insider 10b5-1 plan
    if row.get("insider_10b5_1_plan") is True:
        elite += 5

    elite = max(0, min(100, elite))
    elite_qualified = elite >= ELITE_THRESHOLD and len(landmines) == 0

    return elite, elite_qualified, landmines


def add_elite_scores(stocks_data: List[Dict], top_n: int = TOP_CANDIDATES_COUNT) -> None:
    """
    Mutate stocks_data: add elite_score, elite_qualified, elite_landmines to each row.
    Computes for all; top N are the candidates for TOP 5 gate.
    """
    if not stocks_data:
        return
    for row in stocks_data:
        elite, qualified, landmines = compute_elite_score(row)
        row["elite_score"] = elite
        row["elite_qualified"] = qualified
        row["elite_landmines"] = landmines
