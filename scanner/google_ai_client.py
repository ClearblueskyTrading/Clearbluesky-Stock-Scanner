"""
ClearBlueSky – Google AI (Gemini) API client for AI analysis.
Uses the Generative Language API (generativelanguage.googleapis.com) with free-tier models.
"""

import json

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

GOOGLE_AI_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Free-tier models (no billing). gemini-2.5-flash = best for charts (vision + thinking).
DEFAULT_MODEL = "gemini-2.5-flash"
FREE_MODELS = [
    ("Gemini 2.0 Flash", "gemini-2.0-flash"),
    ("Gemini 2.5 Flash", "gemini-2.5-flash"),
    ("Gemini 2.5 Pro", "gemini-2.5-pro"),
    ("Gemini 3 Flash Preview", "gemini-3-flash-preview"),
]


def analyze(api_key: str, model_id: str, system_prompt: str, user_content, *,
            max_tokens: int = 8192, temperature: float = 0.3,
            image_base64_list=None) -> str:
    """
    Send analysis to Google AI (Gemini) and return the text response.

    Args:
        api_key: Google AI API key (from aistudio.google.com/apikey).
        model_id: Model name (e.g. gemini-2.0-flash, gemini-2.5-flash).
        system_prompt: System / instruction text.
        user_content: User message – dict (JSON) or str.
        max_tokens: Max output tokens.
        temperature: 0–2.
        image_base64_list: Optional list of base64 image URLs for vision models.

    Returns:
        str: Model response text, or empty string on failure.
    """
    if not REQUESTS_AVAILABLE:
        raise ValueError("requests is required; install with: pip install requests")
    api_key = (api_key or "").strip()
    if not api_key:
        raise ValueError("Google AI API key is required")

    model_id = (model_id or DEFAULT_MODEL).strip() or DEFAULT_MODEL

    if isinstance(user_content, dict):
        user_content = json.dumps(user_content, indent=2)

    # Build parts: text + optional images
    parts = []

    # Combined prompt: system + user
    full_text = f"{system_prompt}\n\n---\n\n{user_content}"
    parts.append({"text": full_text})

    if image_base64_list:
        for url_or_b64 in image_base64_list:
            if isinstance(url_or_b64, (list, tuple)) and len(url_or_b64) >= 2:
                url_or_b64 = url_or_b64[1]
            b64 = url_or_b64 if isinstance(url_or_b64, str) else None
            if not b64 or len(b64) < 100:
                continue
            if "base64," in b64:
                b64 = b64.split("base64,", 1)[1]
            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": b64
                }
            })

    url = f"{GOOGLE_AI_BASE}/models/{model_id}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
        },
    }

    MAX_RETRIES = 3
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(url, params=params, headers=headers, json=payload, timeout=90)
            data = resp.json() if resp.text else {}

            if resp.status_code >= 400:
                err = data.get("error", {})
                msg = err.get("message", str(err) or resp.text[:200])
                if resp.status_code in (429, 500, 502, 503) and attempt < MAX_RETRIES - 1:
                    import time
                    time.sleep((attempt + 1) * 5)
                    continue
                raise RuntimeError(f"Google AI HTTP {resp.status_code}: {msg}")

            candidates = data.get("candidates") or []
            if not candidates:
                return ""
            parts_out = candidates[0].get("content", {}).get("parts") or []
            texts = [p.get("text", "") for p in parts_out if p.get("text")]
            result = "".join(texts).strip()

            usage = data.get("usageMetadata") or {}
            if usage:
                pt = usage.get("promptTokenCount", 0)
                ct = usage.get("candidatesTokenCount", 0)
                if pt or ct:
                    print(f"[Google AI] Model: {model_id} | Tokens: prompt={pt}, output={ct}")

            return result

        except (requests.ConnectionError, requests.Timeout) as e:
            last_exc = e
            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep((attempt + 1) * 5)
                continue
            raise RuntimeError(f"Google AI connection failed after {MAX_RETRIES} attempts: {e}")

    raise RuntimeError(f"Google AI failed: {last_exc}")
