# ClearBlueSky – Workflow (with API keys)

When you run a scan and have API keys set, this is the flow:

1. **Scan** → Scanner runs (Finviz API if `finviz_api_key` set), returns qualifying tickers.

2. **Report generation** (`report_generator.generate_combined_report_pdf`):
   - **Leveraged tickers:** When a stock has a leveraged alternative (e.g. NVDA→NVDU, AAPL→AAPU), the AI suggests it as "Leveraged alt" with 3-day max hold.
   - Per ticker: **Finviz** data (price, RSI, target, etc.).
   - **TA** (yfinance + pandas-ta): SMAs, RSI, MACD, BB, ATR, Fib — if `include_ta_in_report` is true (default).
   - **Alpha Vantage** sentiment: score, label, headlines — if `alpha_vantage_api_key` is set.
   - **SEC insider context** (10b5-1 vs discretionary): if `use_sec_insider_context` is true and ticker has insider data.
   - **Backtest stats**: historical win rates for this scan type (from SQLite) are included in the analysis package.
   - Output: Single `.md` file (YAML frontmatter + report body + AI section).

3. **AI analysis** (only if `openrouter_api_key` is set):
   - **System prompt**: Base analyst instructions.
   - **RAG**: If `rag_enabled` and `rag_books_folder` are set, relevant AI Knowledge chunks (from ChromaDB index of .txt, .pdf, .md, etc.) are appended to the system prompt.
   - **User content**: The JSON analysis package is sent to OpenRouter.
   - **Chart data**: 30-day price history and recent daily OHLC are included in the JSON (no chart images).
   - **OpenRouter**: 6-model consensus (DeepSeek, Arcee Trinity, Gemini Vision, Llama, GPT-OSS, StepFun) + optional Google AI. Response is included in the `.md` file and opened.

**Settings that affect the pipeline**

| Setting | Effect |
|--------|--------|
| `finviz_api_key` | Scanner data from Finviz (optional; can use scraping). |
| `openrouter_api_key` | Enables AI analysis step; required for OpenRouter. |
| `openrouter_model` | Model used for analysis (free models only, e.g. tngtech/deepseek-r1t2-chimera:free). |
| `alpha_vantage_api_key` | Enables headlines per ticker; fed to local FinBERT for sentiment. Rolling 1h/4h/1d + spike alerts. |
| `sentiment_spike_threshold` | Delta (0.0–1.0, default 0.4) for 1h vs 4h/1d to flag sentiment spike. |
| `include_ta_in_report` | Include TA (SMAs, RSI, MACD, etc.) in report and JSON. |
| `use_sec_insider_context` | Add 10b5-1 vs discretionary context for tickers with insider data. |
| `rag_books_folder` + `rag_enabled` | Include RAG AI Knowledge excerpts in AI system prompt (.txt, .pdf, .md, .docx, etc.). |
| `use_vision_charts` | Legacy; chart data is now in JSON only (no images sent). |

**RAG books**: Place `.txt` and/or `.pdf` files in the books folder, then click **Build RAG index** in Settings. With **Include RAG excerpts in AI analysis** checked, relevant chunks are added to the AI system prompt for each scan.
