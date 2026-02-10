# Cursor Agent Setup — Restore from backup

Use this when you have a **new PC**, **recover from a crash**, or want to **replicate this setup** elsewhere. Two backup types:

- **cursor-agent-backup-YYYYMMDD.zip** — Agent only (rules, scripts, docs, menu, todo). Use when you only need the Cursor/voice setup.
- **cursor-full-backup-YYYYMMDD.zip** — Agent + **all data**: session_logs, trade_journal, market_context, strategy_updates, **ChromaDB vector database** (app/rag_store), and velocity_memory indexer. Use this so you can **pick up exactly where you left off** (conversations, RAG, regime, trades).

---

## What's in each backup

### Agent backup (cursor-agent-backup-*.zip)
- **`.cursor/rules/`** — All Cursor rules (keyword triggers, conversation backup, screenshots, RAG, session continuity, user preferences, etc.)
- **`scripts/`** — PowerShell and batch scripts (screenshot, clipboard, active window, time/market, notify, speak clipboard, pick voice, **Build-AgentBackup.ps1**)
- **`docs/VOICE_MENU.md`** — Full voice menu (say "menu" or "give me the menu")
- **`docs/references/our-rag-setup.md`**, **`docs/guidelines/project-overview.md`**, **`docs/strategy/`**
- **`todo.md`**, **`RESTORE.md`**

### Full backup (cursor-full-backup-*.zip)
Everything above, plus (inside a **`scanner/`** folder in the zip):
- **`scanner/velocity_memory/`** — Entire RAG content: session_logs, trade_journal, market_context, strategy_updates, .indexed_files.txt, velocity_rag.py, and related files.
- **`scanner/app/rag_store/`** — ChromaDB vector database (all indexed conversations, sessions, trades, books, etc.).

Not included (recreate or optional): `voice_choice.txt` (say "pick voice" to set again), `screenshots/`, API keys (restore from your own secure copy), `user_config.json` (scanner config; restore separately if needed).

---

## Restore on a new PC (full backup — pick up where you left off)

### 1. Prerequisites
- **Cursor** installed  
- **PowerShell** (Windows)  
- **Python** (for RAG; `pip install chromadb` and deps if you use velocity_rag)

### 2. Unzip
- Unzip **cursor-full-backup-YYYYMMDD.zip** to a temporary folder (e.g. `C:\Restore`). You’ll see:
  - **`cursor/`** — agent setup
  - **`scanner/`** — velocity_memory + app/rag_store

### 3. Restore Cursor agent
- Create or open your project folder (e.g. **`d:\cursor`**).
- Copy **everything inside** `cursor/` into that folder so you have:
  - `d:\cursor\.cursor\rules\`
  - `d:\cursor\scripts\`
  - `d:\cursor\docs\`
  - `d:\cursor\RESTORE.md`
  - `d:\cursor\todo.md`

### 4. Restore RAG and vector DB (so you pick up where you left off)
- Create **`D:\scanner`** (or your chosen scanner root) if it doesn’t exist.
- Copy **`scanner/velocity_memory`** to **`D:\scanner\velocity_memory`** (replace if it exists).
- Copy **`scanner/app/rag_store`** to **`D:\scanner\app\rag_store`** (create `D:\scanner\app` first if needed).

Result: All session logs, conversations, trade journal, market context, and the **ChromaDB vector database** are back. No need to reindex unless you add new files.

### 5. Open in Cursor
- **File → Open Folder** → select your project folder (e.g. `d:\cursor`).
- Say **"give me the menu"** to confirm the voice menu.
- Say **"check your brain"** to confirm RAG and past context are working.

### 6. Optional
- If your **scanner root** is not `D:\scanner`, edit the rules that reference it: search for `D:\scanner\velocity_memory` in `.cursor/rules/` and update paths.
- If you use the scanner app, ensure **`D:\scanner\app`** has the rest of the app (code, config); the backup only includes **rag_store** (vector DB) and **velocity_memory**.

---

## Restore agent-only backup (cursor-agent-backup-*.zip)

- Unzip into your project folder (e.g. `d:\cursor`) so `.cursor/`, `scripts/`, `docs/`, `RESTORE.md`, `todo.md` are at the root.
- Open that folder in Cursor.
- Set up RAG separately: create `D:\scanner\velocity_memory\`, add velocity_rag.py and any session_logs/trade_journal you have, run `python velocity_rag.py` to index. ChromaDB will be created in `D:\scanner\app\rag_store` when you first run the indexer (or copy from another backup).

---

## Restore by pointing the agent at the zip

On the new PC, open Cursor and say:

- *"Restore my agent setup from [path to cursor-full-backup-YYYYMMDD.zip]"*  
  or  
- *"Restore from [path to cursor-agent-backup-YYYYMMDD.zip]"*

The agent will unzip and place **cursor** contents into your workspace and, for a **full** zip, will instruct you (or place) **scanner/velocity_memory** and **scanner/app/rag_store** to **D:\scanner** so you can pick up where you left off.

---

## Creating a fresh backup

- **Agent only:**  
  `powershell -ExecutionPolicy Bypass -File "d:\cursor\scripts\Build-AgentBackup.ps1"`
- **Full (agent + all data + vector DB):**  
  `powershell -ExecutionPolicy Bypass -File "d:\cursor\scripts\Build-AgentBackup.ps1" -Full`

Default output: `d:\cursor\cursor-agent-backup-YYYYMMDD.zip` or `cursor-full-backup-YYYYMMDD.zip`.  
If your scanner root is not `D:\scanner`, use:  
`.\Build-AgentBackup.ps1 -Full -ScannerRoot "X:\your\scanner\path"`
