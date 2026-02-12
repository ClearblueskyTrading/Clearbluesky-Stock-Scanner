# How We Implement the Generic RAG Architecture

This project follows the two-tier design in **CURSOR_RAG_ARCHITECTURE_GENERIC.md** (repo root).

## Mapping

| Generic doc | Our implementation |
|-------------|---------------------|
| **Tier 1: Knowledge folder** | `d:\cursor\docs\` (this repo) + `C:\Users\EricR\OneDrive\Desktop\Claude AI Knowledge\` (shared with Claude) |
| **Tier 2: RAG vector DB** | `d:\cursor\velocity_memory\` — ChromaDB (chroma_db/), velocity_rag.py, session_logs, trade_journal, market_context |
| **Indexer** | velocity_rag.py (indexes session_logs, trade_journal, market_context, strategy_updates) — lives in d:\cursor, separate from D:\scanner |
| **Query** | `python "d:\cursor\velocity_memory\velocity_rag.py" --query "…"` or use Cursor rules |

## What We Have vs Generic Phases

- **Phase 1 (Knowledge folder):** ✅ We have `docs/` here and the shared Claude AI Knowledge folder.
- **Phase 2 (RAG DB):** ✅ We use velocity_memory with ChromaDB; query_helper and velocity_rag.py provide search.
- **Phase 3 (MCP server):** ❌ Not implemented. Cursor uses manual RAG queries via terminal or rule reminders. Could add an MCP server later for in-chat `search_memory()`.

## Quick Commands

```bash
# Search shared memory (sessions, trades, scans, etc.)
python "d:\cursor\velocity_memory\velocity_rag.py" --query "recent session"
python "d:\cursor\velocity_memory\velocity_rag.py" --query "scanner rate limits" --filter sessions
```

## Adding to Tier 1

- **This repo:** Add or edit files under `docs/guidelines/`, `docs/references/`, `docs/decisions/` and use `@docs/...` in Cursor.
- **Shared brain:** Put files in `d:\cursor\velocity_memory\session_logs\` (etc.); run velocity_rag.py to reindex.
