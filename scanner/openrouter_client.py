"""
ClearBlueSky – OpenRouter API client for AI analysis.
Sends the analysis package (text or JSON) to the selected model and returns the response.
"""

import json
import os
import re

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "tngtech/deepseek-r1t2-chimera:free"

# 5 text + 1 vision model. Vision model = Gemini 2.0 Flash (understanding), NOT image-preview (generation).
# Order: strong reasoning first, then vision, then diversity. Gemini 2.0 Flash = best free vision for chart analysis.
CONSENSUS_MODELS = [
    ("DeepSeek R1T2 Chimera", "tngtech/deepseek-r1t2-chimera:free", False),       # Strong reasoning
    ("Arcee Trinity Large", "arcee-ai/trinity-large-preview:free", False),        # Strong reasoning
    ("Google Gemini 2.0 Flash (Vision)", "google/gemini-2.0-flash-exp:free", True),  # Chart understanding
    ("Meta Llama 3.3 70B", "meta-llama/llama-3.3-70b-instruct:free", False),
    ("OpenAI GPT-OSS 120B", "openai/gpt-oss-120b:free", False),
    ("StepFun Step 3.5 Flash", "stepfun/step-3.5-flash:free", False),
]

# Model used for synthesis (single call after consensus). Prefer strong reasoning.
SYNTHESIS_MODEL = "arcee-ai/trinity-large-preview:free"


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


def _parse_consensus_vote_line(text):
    """Extract CONSENSUS_VOTE: TICKER:BUY|SKIP|AVOID,... from model response. Returns dict {TICKER: "BUY"|"SKIP"|"AVOID"}."""
    out = {}
    if not text:
        return out
    m = re.search(r"CONSENSUS_VOTE:\s*([^\n]+)", text, re.IGNORECASE | re.DOTALL)
    if not m:
        return out
    raw = m.group(1).strip()
    for part in re.split(r"[,;]+", raw):
        part = part.strip()
        if ":" in part:
            ticker, vote = part.split(":", 1)
            ticker = ticker.strip().upper()
            vote = vote.strip().upper()
            if ticker and vote in ("BUY", "SKIP", "AVOID"):
                out[ticker] = vote
    return out


def _aggregate_consensus_votes(results):
    """Aggregate votes from all model responses. Returns (vote_summary_str, votes_by_ticker)."""
    all_votes = {}  # ticker -> list of (model_label, vote)
    for label, content in results:
        votes = _parse_consensus_vote_line(content)
        for ticker, vote in votes.items():
            if ticker not in all_votes:
                all_votes[ticker] = []
            all_votes[ticker].append((label, vote))
    if not all_votes:
        return "", {}
    lines = ["", "=" * 70, "CONSENSUS VOTE SUMMARY", "=" * 70]
    for ticker in sorted(all_votes.keys()):
        lst = all_votes[ticker]
        buys = sum(1 for _, v in lst if v == "BUY")
        skips = sum(1 for _, v in lst if v == "SKIP")
        avoids = sum(1 for _, v in lst if v == "AVOID")
        total = len(lst)
        if buys >= total * 0.5:
            consensus = "BUY"
        elif avoids >= total * 0.5:
            consensus = "AVOID"
        elif skips >= total * 0.5:
            consensus = "SKIP"
        else:
            consensus = "MIXED"
        detail = ", ".join(f"{v}" for _, v in lst)
        lines.append(f"  {ticker}: {consensus} ({buys}B/{skips}S/{avoids}A) [{detail}]")
    lines.append("")
    return "\n".join(lines), all_votes


def analyze_with_all_models(config, system_prompt, user_content, progress_callback=None, max_tokens=8192, temperature=0.3, image_base64_list=None):
    """
    Run analysis through 6 OpenRouter consensus models + optional Google AI (Gemini) free models.
    Text models get JSON only; vision models get JSON + chart images when image_base64_list provided.
    Returns combined output with each model's opinion.
    If both API keys missing, returns None.
    """
    api_key = (config.get("openrouter_api_key") or "").strip()
    google_key = (config.get("google_ai_api_key") or "").strip()
    if not api_key and not google_key:
        return None

    results = []
    n_models = len(CONSENSUS_MODELS)

    # 1. OpenRouter consensus models (when key set)
    if api_key:
        for i, item in enumerate(CONSENSUS_MODELS):
            label, model_id, is_vision = item[0], item[1], item[2] if len(item) > 2 else False
            imgs_for_model = image_base64_list if (is_vision and image_base64_list) else None
            if progress_callback:
                progress_callback(f"AI: {label} ({i + 1}/{n_models})...")
            try:
                resp = analyze(api_key, model_id, system_prompt, user_content, max_tokens=max_tokens, temperature=temperature, image_base64_list=imgs_for_model)
                results.append((label, resp or "(no response)"))
            except Exception as e:
                results.append((label, f"[Error: {e}]"))

    # 2. Google AI (Gemini) free model – adds to consensus when key set
    if google_key:
        model_name = config.get("google_ai_model") or "gemini-2.5-flash"
        label = f"Google {model_name}"
        if progress_callback:
            progress_callback(f"AI: {label}...")
        try:
            from google_ai_client import analyze as google_analyze
            imgs = image_base64_list if config.get("use_vision_charts") else None
            resp = google_analyze(google_key, model_name, system_prompt, user_content, max_tokens=max_tokens, temperature=temperature, image_base64_list=imgs)
            results.append((label, resp or "(no response)"))
        except Exception as e:
            results.append((label, f"[Error: {e}]"))

    if not results:
        return None

    n_total = len(results)
    lines = [
        "=" * 70,
        f"AI ANALYSIS — Consensus from {n_total} models",
        "Each model analyzed the same scan data. Vision-capable models received chart images when enabled.",
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
    # Append consensus vote summary if any model included CONSENSUS_VOTE
    vote_summary, _ = _aggregate_consensus_votes(results)
    if vote_summary:
        lines.append(vote_summary)
    combined = "\n".join(lines)

    # B. Synthesis step: OpenRouter model synthesizes all opinions (requires OpenRouter key)
    synthesis = _run_synthesis(api_key, combined, config.get("openrouter_synthesis_enabled", True), progress_callback, n_models=n_total)
    if synthesis:
        combined = synthesis + "\n\n" + combined
    return combined


def _run_synthesis(api_key, combined_output, enabled, progress_callback=None, n_models=7):
    """
    Run one synthesis call: given full consensus output, produce final trading summary.
    Returns synthesis text or "" if disabled/failed.
    """
    if not enabled or not api_key:
        return ""
    sys_prompt = f"""You are a senior trading analyst. You will receive analyses from {n_models} AI models on the same stock scan.
Synthesize them into ONE concise final summary (max 400 words):
1. MARKET VIEW: Bull/bear/neutral and key risk
2. TOP PICKS: 3–5 tickers with entry/stop/target and why
3. AVOID: Tickers to skip and why
4. CONSENSUS_VOTE: TICKER:BUY|SKIP|AVOID for each ticker discussed (one line)

MANDATORY RULES for CONSENSUS_VOTE:
- If ANY model said AVOID for a ticker due to EARNINGS (earnings in 1–5 days, landmine, binary risk), you MUST output AVOID for that ticker. Do NOT override earnings caution with majority BUY.
- For split consensus (e.g. 6 BUY, 1 AVOID): prefer the cautious vote when it cites earnings, invalidation, or risk. Otherwise note lower conviction.
- When market breadth shows 0% above SMA50/200 (bear regime), emphasize tight stops are mandatory in your summary.
Be direct. No fluff."""
    user_prompt = f"Synthesize these {n_models} model analyses into one final trading summary:\n\n{combined_output[:90000]}"
    if progress_callback:
        progress_callback("Synthesis (Trinity Large)...")
    try:
        return analyze(api_key, SYNTHESIS_MODEL, sys_prompt, user_prompt, max_tokens=2048, temperature=0.3)
    except Exception:
        return ""
