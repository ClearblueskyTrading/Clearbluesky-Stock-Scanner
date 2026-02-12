# ClearBlueSky – Workflow (with API keys)

When you run a scan and have API keys set, this is the flow:

1. **Scan** → Scanner runs (Finviz API if `finviz_api_key` set), returns qualifying tickers.

2. **Report generation** (`report_generator.generate_combined_report_pdf`):
   - Per ticker: **Finviz** data (price, RSI, target, etc.).
   - **TA** (yfinance + pandas-ta): SMAs, RSI, MACD, BB, ATR, Fib — if `include_ta_in_report` is true (default).
   - **Alpha Vantage** sentiment: score, label, headlines — if `alpha_vantage_api_key` is set.
   - **SEC insider context** (10b5-1 vs discretionary): if `use_sec_insider_context` is true and ticker has insider data.
   - **Backtest stats**: historical win rates for this scan type (from SQLite) are included in the analysis package.
   - Output: Single `.md` file (YAML frontmatter + report body + AI section).

3. **AI analysis** (only if `openrouter_api_key` is set):
   - **System prompt**: Base analyst instructions.
   - **RAG**: If `rag_enabled` and `rag_books_folder` are set, relevant book chunks (from ChromaDB index of .txt/.pdf) are appended to the system prompt.
   - **User content**: The JSON analysis package is sent to OpenRouter.
   - **Chart data**: 30-day price history and recent daily OHLC are included in the JSON (no chart images).
   - **OpenRouter**: 3-model consensus (Llama, OpenAI, DeepSeek). Response is included in the `.md` file and opened.

**Settings that affect the pipeline**

| Setting | Effect |
|--------|--------|
| `finviz_api_key` | Scanner data from Finviz (optional; can use scraping). |
| `openrouter_api_key` | Enables AI analysis step; required for OpenRouter. |
| `openrouter_model` | Model used for analysis (free models only, e.g. tngtech/deepseek-r1t2-chimera:free). |
| `alpha_vantage_api_key` | Enables sentiment + headlines per ticker in report/JSON. |
| `include_ta_in_report` | Include TA (SMAs, RSI, MACD, etc.) in report and JSON. |
| `use_sec_insider_context` | Add 10b5-1 vs discretionary context for tickers with insider data. |
| `rag_books_folder` + `rag_enabled` | Include RAG book excerpts in AI system prompt (.txt and .pdf). |
| `use_vision_charts` | Legacy; chart data is now in JSON only (no images sent). |

**RAG books**: Place `.txt` and/or `.pdf` files in the books folder, then click **Build RAG index** in Settings. With **Include RAG excerpts in AI analysis** checked, relevant chunks are added to the AI system prompt for each scan.
