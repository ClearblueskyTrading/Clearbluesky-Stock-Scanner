# Cursor Knowledge Folder (Tier 1)

This folder is **Tier 1** from the [RAG + System Memory Architecture](../../CURSOR_RAG_ARCHITECTURE_GENERIC.md): static docs you curate. Use `@docs/filename` in Cursor to pull them into context.

## Structure

| Folder | Use |
|--------|-----|
| **guidelines/** | Project rules, coding standards, workflow |
| **references/** | Tech stack, setup, API design, deployment |
| **decisions/** | Architecture Decision Records (why we chose X) |

## Trading Workflow

- **[guidelines/trading-workflow.md](guidelines/trading-workflow.md)** — IBKR + IBOT order entry; prompt AI to craft IBOT commands
- **[guidelines/ai-report-from-scan.md](guidelines/ai-report-from-scan.md)** — Read scan JSON/TXT and produce AI report when user says "create AI report"

## MCP Install Guides

- **[ALPACA_MCP_INSTALL.md](ALPACA_MCP_INSTALL.md)** — Alpaca MCP for Cursor
- **[IBKR_MCP_INSTALL.md](IBKR_MCP_INSTALL.md)** — Interactive Brokers MCP options (ib-mcp, IB_MCP, ib_insync)

## How This Fits With Our Setup

- **Tier 1 (this folder):** Static docs in `docs/` + shared folder `C:\Users\EricR\OneDrive\Desktop\Claude AI Knowledge\`
- **Tier 2 (RAG):** `d:\cursor\velocity_memory\` — ChromaDB (chroma_db/), session logs, trade journal. Cursor has its own velocity_rag.py; separate from D:\scanner.
- **Query RAG:** `python "d:\cursor\velocity_memory\velocity_rag.py" --query "your question"`

See **references/our-rag-setup.md** for the full mapping to the generic architecture.
