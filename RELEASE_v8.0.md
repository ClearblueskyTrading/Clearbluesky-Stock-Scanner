# ClearBlueSky Stock Scanner v8.0

**Date:** 2026-02-17

---

## Added

### Earnings & risk
- **Earnings window flags** — `earnings_flag` (pre/post/none), `earnings_days_to`, `earnings_time`, `earnings_status`, `earnings_source` — ±5 trading days. Used in reports and AI context. Source: yfinance.

### News sentiment
- **FinBERT local sentiment** — New `finbert_scorer.py` using ProsusAI/finbert. Runs locally; no API cost. Requires `transformers` and `torch` (in requirements.txt).
- **Rolling sentiment** — 1h, 4h, 1d windows. Reports: `finbert_score_1h/4h/1d`, `finbert_count_1h/4h/1d`.
- **Sentiment spike alerts** — Detects sudden shifts. Reports: `finbert_spike`, `finbert_spike_reason`, `finbert_delta_vs_4h`, `finbert_delta_vs_1d`. Config: `sentiment_spike_threshold` (default 0.4).
- **Alpha Vantage + FinBERT** — When `alpha_vantage_api_key` is set, Alpha Vantage headlines → local FinBERT scoring.

### Workflow
- **Run All Scans** — `run_all_scans.py` runs velocity → swing → watchlist. GUI checkbox to run all three.

### AI
- **6-model consensus** — OpenRouter: DeepSeek, Arcee Trinity, Gemini Vision, Llama 3.3 70B, GPT-OSS 120B, StepFun Step 3.5. Optional Google AI adds 7th. Synthesis step.

---

## Changed

- Report enrichment: FinBERT rolling scores and sentiment spikes when Alpha Vantage key set.
- Settings: News/Sentiment section updated; sentiment spike threshold field.
- Version: app.py, README, INSTALL.bat → v8.0.

---

*ClearBlueSky Stock Scanner v8.0*
