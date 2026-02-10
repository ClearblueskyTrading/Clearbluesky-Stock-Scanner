# Cursor Knowledge Folder (Tier 1)

This folder is **Tier 1** from the [RAG + System Memory Architecture](../../CURSOR_RAG_ARCHITECTURE_GENERIC.md): static docs you curate. Use `@docs/filename` in Cursor to pull them into context.

## Structure

| Folder | Use |
|--------|-----|
| **guidelines/** | Project rules, coding standards, workflow |
| **references/** | Tech stack, setup, API design, deployment |
| **decisions/** | Architecture Decision Records (why we chose X) |

## How This Fits With Our Setup

- **Tier 1 (this folder):** Static docs in `docs/` + shared folder `C:\Users\EricR\OneDrive\Desktop\Claude AI Knowledge\`
- **Tier 2 (RAG):** `D:\scanner\velocity_memory\` — ChromaDB, session logs, trade journal, auto-indexed. Shared with Claude Desktop.
- **Query RAG:** `python "D:\scanner\velocity_memory\velocity_rag.py" --query "your question"`

See **references/our-rag-setup.md** for the full mapping to the generic architecture.
