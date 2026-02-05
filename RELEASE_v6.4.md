# ClearBlueSky v6.4 Release

**Release date:** February 2026

## What's in v6.4

- **JSON analysis package** – Every scan saves a `.json` file with the same data as the PDF (tickers, scores, TA, sentiment, insider context, etc.). The JSON includes an **`instructions`** field with the full Master Trading Report Directive and analyst prompt, so you can paste the JSON into any AI and say “follow the instructions in this JSON.”
- **OpenRouter AI integration** – Optional: set your OpenRouter API key and model in Settings. After each scan, the app sends the JSON to OpenRouter and saves the AI’s response as `*_ai.txt` (and opens it).
- **RAG book knowledge** – Optional: point Settings to a folder of `.txt` and `.pdf` trading books, click **Build RAG index**, and enable **Include RAG excerpts in AI analysis**. Relevant book chunks are added to the AI system prompt.
- **Technical analysis in report** – Optional: include TA (SMAs, RSI, MACD, BB, ATR, Fib) per ticker in the report and JSON (yfinance + pandas-ta). Toggle in Settings.
- **Alpha Vantage sentiment** – Optional: set Alpha Vantage API key for sentiment score and headlines per ticker in report/JSON.
- **SEC insider context** – Optional: when a ticker has insider data, add 10b5-1 plan vs discretionary context from SEC Form 4 (toggle in Settings).
- **Backtest feedback loop** – Signals are logged to SQLite; optional **Update backtest outcomes** in Settings; aggregate stats included in the JSON package.
- **Vision charts** – Optional: attach candlestick chart images to the OpenRouter request (multimodal models only). Toggle in Settings.
- **Help and docs** – In-app Help (❓) updated for all scan types, outputs, and Settings. See **app/WORKFLOW.md** for the full pipeline.

## Outputs per run

| File       | Contents |
|-----------|----------|
| `*_Scan_*.pdf` | Report with Master Trading Report Directive + per-ticker data. |
| `*_Scan_*.json` | Same data + `instructions` for any AI. |
| `*_Scan_*_ai.txt` | AI analysis (only if OpenRouter key set). |

## Release zip

- **File:** `ClearBlueSky-6.4.zip` (in project root).
- **Excluded from zip:** `user_config.json`, `error_log.txt`, `__pycache__/`, contents of `app/reports/` and `app/rag_store/`.
- Safe to share; no API keys or user data included.

---

*ClearBlueSky v6.4 – made with Claude AI*
