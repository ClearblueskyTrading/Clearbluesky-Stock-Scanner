# Project Structure

**Project:** Cursor Desktop Addons  
**Sub-project:** ClearBlueSky Stock Scanner (separate, integrates as needed)

This workspace is **Cursor Desktop Addons**. The **ClearBlueSky Stock Scanner** lives in `scanner/` as a separate project. Both are kept separate but integrate as needed (PTM, reports, Agent GUI buttons, etc.). The scanner can be extracted for standalone release.

## Layout

```
D:\cursor\
├── scanner/              # Scanner app (portable, extractable)
│   ├── app.py            # GUI entry point
│   ├── scanner_cli.py    # CLI entry point
│   ├── velocity_scanner.py, watchlist_scanner.py, ...
│   ├── requirements.txt
│   ├── reports/          # Scan report outputs
│   ├── scans/            # Scan data
│   └── user_config.json  # API keys, preferences (gitignored)
│
├── scripts/              # Desktop agent tooling
│   ├── AgentGUI.ps1      # Trading Agent Command Center
│   ├── Build-AgentBackup.ps1
│   ├── TakeScreenshot.ps1
│   └── ...
│
├── .cursor/rules/        # Cursor IDE rules (project-boundaries, etc.)
├── docs/                 # Documentation
├── velocity_memory/      # RAG, session logs
│
├── INSTALL.bat           # Scanner installer (uses scanner/)
├── Dockerfile            # Scanner container (uses scanner/)
├── build_release_zip.py  # Builds scanner release zip
└── PROJECT_STRUCTURE.md  # This file
```

## Boundaries

| What | Where | Project | Release? |
|------|-------|---------|----------|
| Scanner app | `scanner/` | ClearBlueSky Stock Scanner | Yes — Clearbluesky-Stock-Scanner repo, zip |
| Agent GUI, scripts | `scripts/` | Cursor Desktop Addons | Cursor-Desktop-Addons repo |
| Rules, docs | `.cursor/`, `docs/` | Cursor Desktop Addons | No (rules) / partial (docs) |

## Extracting the scanner for a standalone app

1. Zip or copy the `scanner/` folder plus root files: `INSTALL.bat`, `Dockerfile`, `docker-compose.yml`, `build_release_zip.py`, `README.md`, release notes.
2. Run `python build_release_zip.py` from a clean clone to produce `ClearBlueSky-vX.XX.zip`.
