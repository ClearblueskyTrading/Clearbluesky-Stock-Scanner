# ClearBlueSky Stock Scanner v7.90

**Date:** 2026-02-12

Major UI and output changes: single .md report, 3-model AI consensus, Universe toggle, progress improvements, simplified AI status.

---

## Changed

### Output
- **Single .md report** — Replaces separate PDF, JSON, and `*_ai.txt`. One file per scan: YAML frontmatter (structured data), report body (per-ticker data, market breadth, price history), and AI consensus (when OpenRouter key set).

### AI
- **3-model consensus** — Meta Llama 3.3 70B, OpenAI GPT-OSS 120B, DeepSeek R1T2 Chimera. All free; no credits.
- **Chart data** — 30-day OHLC and last 10 daily bars in JSON sent to AI. No chart images.
- **AI status** — Simple: `AI: Connected` (green), `AI: No API key set`, or `AI: Key invalid or expired`. Credit display removed.

### UI
- **Universe toggle** — Own row under scan type: `Universe: ○ S&P 500  ○ ETFs`.
- **Progress** — Step labels (Enrichment, Market breadth, Smart money, AI: Meta Llama (1/3)...) and elapsed time (e.g. `• 2:15`).

---

## Removed

- Fast mode (`openrouter_fast_mode`)
- Quick Report option
- AI credit display
- Chart images in AI analysis
- Separate PDF, JSON, `*_ai.txt` outputs

---

## Version

- **app/app.py** — VERSION = `7.90`
- All docs updated: USER_MANUAL, README, SCANNER_CONFIG_PARAMETERS, CLI_FOR_AI

---

*ClearBlueSky Stock Scanner v7.90*
