"""
FinBERT sentiment scorer (local, offline) for news/headlines.

Usage:
    from finbert_scorer import score_headlines
    score = score_headlines(["Stock rallies on strong earnings", ...])

Returns:
    {
        "sentiment_score": float (-1..1, avg),
        "sentiment_label": "Bearish/Neutral/Bullish",
        "per_item": [
            {"text": "...", "score": -0.34, "label": "Bearish"},
            ...
        ]
    }

Model:
    ProsusAI/finbert (Hugging Face) via transformers pipeline.

Dependencies:
    pip install transformers torch
"""

from functools import lru_cache
from typing import List, Dict, Any


@lru_cache(maxsize=1)
def _get_pipeline():
    try:
        from transformers import pipeline
    except Exception as e:
        raise RuntimeError("Install transformers: pip install transformers torch") from e
    return pipeline("text-classification", model="ProsusAI/finbert")


def _label_to_signed_score(label: str, score: float) -> float:
    """
    Convert FinBERT label/score to signed sentiment:
      - POSITIVE => +score
      - NEGATIVE => -score
      - NEUTRAL  => 0
    """
    lbl = (label or "").upper()
    if lbl == "POSITIVE":
        return score
    if lbl == "NEGATIVE":
        return -score
    return 0.0


def score_headlines(texts: List[str]) -> Dict[str, Any]:
    """
    Score a list of headlines with FinBERT.
    Returns avg sentiment_score (-1..1), sentiment_label, and per-item breakdown.
    """
    texts = [t.strip() for t in texts if t and t.strip()]
    if not texts:
        return {"sentiment_score": None, "sentiment_label": None, "per_item": []}

    nlp = _get_pipeline()
    results = nlp(texts, truncation=True, max_length=128)

    per_item = []
    signed_scores = []
    for text, r in zip(texts, results):
        label = r.get("label")
        score = float(r.get("score", 0.0) or 0.0)
        signed = _label_to_signed_score(label, score)
        signed_scores.append(signed)
        per_item.append({"text": text, "label": label, "score": signed})

    avg = sum(signed_scores) / len(signed_scores)

    if avg <= -0.35:
        label = "Bearish"
    elif avg <= -0.15:
        label = "Somewhat_Bearish"
    elif avg < 0.15:
        label = "Neutral"
    elif avg < 0.35:
        label = "Somewhat_Bullish"
    else:
        label = "Bullish"

    return {"sentiment_score": round(avg, 4), "sentiment_label": label, "per_item": per_item}
