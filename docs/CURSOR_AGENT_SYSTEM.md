# Cursor Agent Enhancement System — Reddit / Shareable Spec

A full spec for turning Cursor into a **voice-driven agent** with **screenshots**, **long-term memory (RAG + vector DB)**, **one-command backup/restore**, and **keyword triggers** so you don’t have to remember commands. No trading content — generic enough that you (or others) can add their own apps and data on top.

---

## What You Get

- **Voice menu** — Say “menu” or “give me the menu” and the agent shows a list of every command. You read off what you need (works great with Windows voice input / Win+H).
- **Screenshots** — “Take a screenshot” captures **each monitor at full resolution** (separate images). The agent reads them and can use them for errors, UI, or browser content. It can also take screenshots on its own when troubleshooting.
- **Clipboard as context** — “Use clipboard” / “what’s on the clipboard”: agent reads the clipboard and uses it without you pasting into chat.
- **Active window** — “What am I looking at?”: agent reports the focused window title and app (e.g. browser, Cursor).
- **Time (and optional checks)** — “What time is it?”: current time; you can add your own checks (e.g. market hours, reminders) via small scripts.
- **Actions** — “Open [URL or path]” (opens in browser or default app), “Notify me when done” (Windows toast after a long task), “Add to my todo” (appends to a single todo file).
- **Memory and RAG** — “Check your brain”: agent queries a **vector database (ChromaDB)** over **session logs** and any indexed docs. “Save conversation” writes the full chat to session_logs and reindexes. “Save system knowledge” writes a short state snapshot (decisions, open items) and reindexes. So the agent has **long-term memory** and you can restore context anytime.
- **Backup and restore** — “Full backup” creates one zip: **agent rules + scripts + all session_logs + ChromaDB vector DB**. On a new PC or after a crash you unzip, copy cursor + data into place, open the folder in Cursor — you’re back where you left off. “Restore from [path to zip]” lets the agent do the unzip and placement for you.

Everything is **keyword/trigger-driven**: you say a short phrase, the agent runs the right script or rule. No need to remember exact commands.

---

## How It Works (High Level)

1. **Cursor rules** (`.cursor/rules/*.mdc`) define the triggers and behavior: when you say “take a screenshot”, “save conversation”, “check your brain”, “menu”, etc., the agent runs the right logic.
2. **Scripts** (PowerShell on Windows): screenshot (per-monitor, full res), clipboard dump, active window, time (and optional extras), Windows toast for “notify when done”. The agent invokes these and uses their output (or the saved screenshot paths) as context.
3. **Voice menu** — One markdown file (e.g. `docs/VOICE_MENU.md`) lists every command. When you say “menu”, the agent shows that file so you can read off commands.
4. **RAG / vector DB** — A folder (e.g. `session_logs/`) holds conversation backups and state snapshots. A ChromaDB indexer (e.g. `velocity_rag.py` or equivalent) chunks and embeds those plus any other docs you add, and the agent queries it for “check your brain” and for context in new chats. So the agent has **persistent, searchable memory**.
5. **Backup script** — One script (e.g. `Build-AgentBackup.ps1 -Full`) zips: (a) all Cursor rules and scripts and the voice menu, (b) the whole session_logs (and any other RAG source folders), (c) the ChromaDB data directory (e.g. `app/rag_store` or a dedicated `chroma_db`). Restore = unzip and copy “cursor” contents into the workspace and “data” contents (session_logs + ChromaDB) into the same paths they came from. The agent can do the restore when you say “restore from [path to zip]”.

Paths (e.g. where session_logs and ChromaDB live) are configurable; the rules and backup script should use a single “memory root” or “data root” so backup/restore stays simple.

---

## Your Own Programs Can Join In

The setup is **extensible** so your own programs can participate:

- **RAG / long-term memory** — Any app can write markdown (or text) into the same **session_logs** (or another folder you index). After the next index run, the agent can “check your brain” and see that content. So your tools can feed the agent’s memory (e.g. “today I ran script X; result: …”).
- **Vector DB** — If you use ChromaDB (or another indexer), your programs can add documents or run the same indexer on new files. The agent and your apps share one vector DB and one set of rules for what gets indexed.
- **Scripts** — The screenshot, notify, clipboard, and “active window” scripts are just PowerShell. Your programs can call them (e.g. “when my build finishes, run Notify.ps1 ‘Build done’”) so the same toasts and capture behavior are available outside chat.
- **Backup** — The full backup zip includes everything the agent needs plus the RAG data and vector DB. Your apps can rely on the same backup/restore flow: one zip, one restore procedure, and both Cursor and your tools see the same session_logs and ChromaDB after restore.

So: you get one agent setup (menu, triggers, RAG, backup), and you can **write your own programs** that write to the same logs, use the same vector DB, and call the same scripts, and everything stays in sync and restorable.

---

## How to Give This to Cursor (Build-It-Yourself Prompt)

You can paste something like this into Cursor so it builds the same system in your workspace (adjust paths and names to your project):

```text
I want a Cursor agent enhancement system with these features. Use Windows PowerShell for scripts; paths are relative to the workspace root unless I specify otherwise.

1. **Voice menu**  
   - When I say "menu" or "give me the menu", show the contents of a single markdown file (e.g. docs/VOICE_MENU.md) that lists every command I can say.  
   - Create that file with short, voice-friendly bullets for each command below.

2. **Keyword triggers (Cursor rules)**  
   Create rules so when I say the following, the agent does the corresponding action:
   - "Take a screenshot" — Run a PowerShell script that captures each monitor at full resolution (one image per monitor), save to workspace/screenshots/, output the image paths; agent reads those images.
   - "Use clipboard" / "what's on the clipboard" — Run a script that outputs clipboard text; agent uses it as context.
   - "What am I looking at?" — Run a script that outputs the active window title and process name; agent reports them.
   - "What time is it?" — Run a script that outputs current time (and optionally one extra check I can customize later); agent reports it.
   - "Open [URL or path]" — Agent runs Start-Process with that URL or path.
   - "Notify me when done" — For a long task, after the task the agent runs a script that shows a Windows toast with a short message.
   - "Add to my todo [item]" — Agent appends the item to a single todo file (e.g. todo.md) in the workspace.
   - "Check your brain" — Agent queries a RAG/vector DB (e.g. ChromaDB) over a folder like session_logs/ and any indexed docs, then summarizes what it knows.
   - "Save conversation" / "backup" / "we're done talking" — Agent writes the full conversation to session_logs/ and runs the indexer so the vector DB is updated.
   - "Save system knowledge" — Agent writes a short state snapshot (decisions, open items) to session_logs/ and reindexes.
   - "Full backup" — Run a backup script that creates one zip containing: (a) all .cursor/rules, scripts, docs, voice menu, todo, RESTORE instructions; (b) the entire session_logs/ folder; (c) the ChromaDB (or vector DB) data directory. So I can restore on a new PC and pick up where I left off.
   - "Restore from [path to zip]" — Agent unzips, places "cursor" contents into the workspace and "data" contents (session_logs + vector DB) into the correct paths, then confirms.

3. **Scripts**  
   Create PowerShell scripts for: screenshot (all monitors, one file per monitor, full res), get clipboard, get active window, get current time, show Windows toast (one message argument). Put them in a scripts/ folder; rules should call them with -ExecutionPolicy Bypass -File.

4. **RAG / vector DB**  
   - Use a folder (e.g. session_logs/) for conversation backups and state snapshots.  
   - Use ChromaDB (or equivalent) in a fixed path (e.g. workspace/data/rag_store or a dedicated memory root).  
   - Provide an indexer script that chunks and indexes session_logs (and any other docs I add) into that DB.  
   - "Check your brain" = query that DB and summarize.  
   - No trading or market-specific logic; keep it generic so I can add my own data and programs later.

5. **Backup and RESTORE.md**  
   - One script (e.g. Build-AgentBackup.ps1) with a -Full flag that zips: agent files (rules, scripts, docs, menu, todo) + session_logs + vector DB directory.  
   - One RESTORE.md that explains: unzip, copy cursor part to workspace, copy data part (session_logs + vector DB) to the same paths, open folder in Cursor.  
   - Mention that my own programs can write to session_logs and use the same vector DB and backup so everything stays in sync and restorable.
```

After Cursor builds it, you only need to: (1) run the indexer once (or when you add docs), (2) say “menu” to see all commands, and (3) use “full backup” and “restore from [zip]” for disaster recovery. Your own programs can write to the same session_logs and ChromaDB and call the same scripts so the whole system stays one coherent, back-up-able setup.

---

## Summary

- **Voice menu + keyword triggers** so you don’t memorize commands.  
- **Screenshots** (per-monitor, full res), **clipboard**, **active window**, **time**, **open**, **notify**, **todo**.  
- **RAG + vector DB** for long-term memory; **save conversation** / **save system knowledge** / **check your brain**.  
- **One-command full backup** (agent + session_logs + vector DB) and **restore from zip** so you can pick up where you left off on a new PC or after a crash.  
- **Your own programs** can write to the same session_logs, use the same vector DB, and call the same scripts so the agent and your tools share one memory and one backup.

No trading or domain-specific logic — just the agent system and the hooks for you to add your own apps and data.
