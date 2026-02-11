# Scripts

## Desktop Agent GUI (click buttons)

If you want a clickable control panel, run:

- `scripts\GUI_PLEASE.bat`  (quick launcher)
- or `scripts\DesktopAgentGUI.bat`

What it does:

- Opens a desktop window with buttons for:
  - Daily brief
  - Morning Finviz digest
  - Finviz news opener
  - Todo list/add/done/remove
  - Daily wrap backup / full backup
  - Latest report and workspace opener
- Shows command output in a live console area inside the GUI.
- Runs one action at a time to avoid overlap/crash behavior.

Quick validation without opening UI:

- `python scripts/DesktopAgentGUI.py --check`

## Desktop Agent Menu (numbered actions)

Use a keyboard-first numbered menu instead of voice commands:

- Double-click `DesktopAgentMenu.bat`, or run:
  - `DesktopAgentTools.ps1 -Action menu`
- Includes:
  - Daily brief
  - Morning Finviz digest
  - Finviz news opener
  - Todo add/list/done/remove
  - Daily wrap + backup
  - Full backup

## Morning Finviz Digest

- Run: `python scripts/MorningNewsDigest.py --save`
- Output:
  - Prioritized last-24h Finviz headlines
  - Theme heatmap (macro, earnings, AI/semis, policy, etc.)
  - Sector leaders/laggards context
- Saved digest path:
  - `D:\scanner\velocity_memory\market_context\morning_news_digest_YYYYMMDD.md`

## SpeakClipboard (hear Cursor's reply)

Uses **Windows TTS** — natural (OneCore) voices when you've picked one, otherwise SAPI. No extra install.

1. **Pick a voice (once):** Double-click **`PickVoice.bat`** (or run `SpeakClipboard.ps1 -ListVoices`). Choose a number to set as default; your choice is saved in `voice_choice.txt`.
2. **Speak clipboard:** In Cursor chat, select the AI reply and copy (Ctrl+C), then double-click **`SpeakClipboard.bat`** (or run `SpeakClipboard.ps1`).

The script speaks the clipboard. Close the window when done.

**Voice input:** Focus the chat box and press **Win+H** for Windows voice typing, then send.
