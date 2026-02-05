"""
ClearBlueSky – OpenRouter API client for AI analysis.
Sends the analysis package (text or JSON) to the selected model and returns the response.
"""

import json
import os

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-3-pro-preview"


def _build_user_content(user_content, image_base64_list=None):
    """Build user message content: string or array of text + image_url parts (OpenRouter multimodal)."""
    if isinstance(user_content, dict):
        user_content = json.dumps(user_content, indent=2)
    if not (image_base64_list and len(image_base64_list) > 0):
        return user_content
    parts = [{"type": "text", "text": user_content}]
    for i, url_or_b64 in enumerate(image_base64_list):
        if isinstance(url_or_b64, (list, tuple)) and len(url_or_b64) >= 2:
            label, url_or_b64 = url_or_b64[0], url_or_b64[1]
        else:
            label = None
        url = url_or_b64 if isinstance(url_or_b64, str) else None
        if not url:
            continue
        if not url.startswith("data:"):
            url = f"data:image/png;base64,{url}" if url else None
        if url:
            parts.append({"type": "image_url", "image_url": {"url": url}})
    return parts


def analyze(api_key, model_id, system_prompt, user_content, max_tokens=8192, temperature=0.3, image_base64_list=None):
    """
    Send analysis package to OpenRouter and return the model's text response.

    Args:
        api_key: OpenRouter API key (required).
        model_id: OpenRouter model id (e.g. google/gemini-3-pro-preview, anthropic/claude-sonnet-4.5, tngtech/deepseek-r1t2-chimera:free).
        system_prompt: System message (analyst instructions).
        user_content: User message – report text or JSON string (the analysis package).
        max_tokens: Max tokens to generate (default 8192).
        temperature: 0–2, lower = more deterministic (default 0.3).
        image_base64_list: Optional list of base64 image URLs (data:image/png;base64,...) or (label, url) for vision models.

    Returns:
        str: Content of the first choice message, or empty string on no content.

    Raises:
        ValueError: If api_key is missing or requests not available.
        RuntimeError: On API error (non-2xx or error in response body).
    """
    if not REQUESTS_AVAILABLE:
        raise ValueError("requests is required for OpenRouter; install with: pip install requests")
    api_key = (api_key or "").strip()
    if not api_key:
        raise ValueError("OpenRouter API key is required")

    model_id = (model_id or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    user_content = _build_user_content(user_content, image_base64_list)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner",
    }
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()

    # OpenRouter returns OpenAI-shaped response: choices[0].message.content
    err = data.get("error")
    if err:
        msg = err.get("message", err) if isinstance(err, dict) else str(err)
        raise RuntimeError(f"OpenRouter error: {msg}")

    choices = data.get("choices") or []
    if not choices:
        return ""
    msg = choices[0].get("message") or {}
    return (msg.get("content") or "").strip()


def analyze_with_config(config, system_prompt, user_content, max_tokens=8192, temperature=0.3, image_base64_list=None):
    """
    Call OpenRouter using keys from the app config dict.

    Uses config['openrouter_api_key'] and config['openrouter_model'].
    If API key is missing or empty, returns None and does not call the API.
    image_base64_list: optional list of base64 image URLs for vision models.
    """
    api_key = (config.get("openrouter_api_key") or "").strip()
    if not api_key:
        return None
    model_id = config.get("openrouter_model") or DEFAULT_MODEL
    return analyze(api_key, model_id, system_prompt, user_content, max_tokens=max_tokens, temperature=temperature, image_base64_list=image_base64_list)
