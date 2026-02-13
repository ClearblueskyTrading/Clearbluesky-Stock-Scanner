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
DEFAULT_MODEL = "tngtech/deepseek-r1t2-chimera:free"

# 3 text models (no vision). Chart data in JSON only.
CONSENSUS_MODELS = [
    ("Meta Llama 3.3 70B", "meta-llama/llama-3.3-70b-instruct:free", False),
    ("OpenAI GPT-OSS 120B", "openai/gpt-oss-120b:free", False),
    ("DeepSeek R1T2 Chimera", "tngtech/deepseek-r1t2-chimera:free", False),
]


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
        model_id: OpenRouter model id (free models, e.g. tngtech/deepseek-r1t2-chimera:free).
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

    # Retry on transient failures (network errors, 429 rate limit, 5xx server errors)
    MAX_RETRIES = 3
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
            # Parse body for detailed errors before raise_for_status
            try:
                data = resp.json()
            except Exception:
                data = {}
            if resp.status_code >= 400:
                api_err = data.get("error")
                detail = api_err.get("message", api_err) if isinstance(api_err, dict) else str(api_err) if api_err else resp.text[:200]
                if resp.status_code in (429, 500, 502, 503) and attempt < MAX_RETRIES - 1:
                    import time
                    wait = (attempt + 1) * 5  # 5s, 10s backoff
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"OpenRouter HTTP {resp.status_code}: {detail}")

            # Check for error in response body (200 with error)
            err = data.get("error")
            if err:
                msg_text = err.get("message", err) if isinstance(err, dict) else str(err)
                raise RuntimeError(f"OpenRouter error: {msg_text}")

            # Log usage/cost info from response (OpenRouter includes this)
            usage = data.get("usage") or {}
            if usage:
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
                print(f"[OpenRouter] Model: {model_id} | Tokens: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})")

            choices = data.get("choices") or []
            if not choices:
                return ""
            msg = choices[0].get("message") or {}
            return (msg.get("content") or "").strip()

        except (requests.ConnectionError, requests.Timeout) as e:
            last_exc = e
            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep((attempt + 1) * 5)
                continue
            raise RuntimeError(f"OpenRouter connection failed after {MAX_RETRIES} attempts: {e}")

    raise RuntimeError(f"OpenRouter failed after {MAX_RETRIES} attempts: {last_exc}")


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


def analyze_with_all_models(config, system_prompt, user_content, progress_callback=None, max_tokens=8192, temperature=0.3, image_base64_list=None):
    """
    Run analysis through 5 consensus models (4 text + 1 vision). Text models get JSON only;
    vision model gets JSON + chart images when image_base64_list provided.
    Returns combined output with each model's opinion.
    If API key missing, returns None.
    """
    api_key = (config.get("openrouter_api_key") or "").strip()
    if not api_key:
        return None

    n_models = len(CONSENSUS_MODELS)
    results = []
    for i, item in enumerate(CONSENSUS_MODELS):
        label = item[0]
        model_id = item[1]
        if progress_callback:
            progress_callback(f"AI: {label} ({i + 1}/{n_models})...")
        try:
            resp = analyze(api_key, model_id, system_prompt, user_content, max_tokens=max_tokens, temperature=temperature)
            results.append((label, resp or "(no response)"))
        except Exception as e:
            results.append((label, f"[Error: {e}]"))

    lines = [
        "=" * 70,
        "AI ANALYSIS — Consensus from 3 models (Llama, OpenAI, DeepSeek)",
        "Each model analyzed the same scan data and 30-day price history.",
        "=" * 70,
    ]
    for label, content in results:
        lines.append("")
        lines.append("-" * 50)
        lines.append(f"  {label}")
        lines.append("-" * 50)
        lines.append("")
        lines.append(content)
        lines.append("")
    return "\n".join(lines)
