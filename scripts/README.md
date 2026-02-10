# Scripts

## SpeakClipboard (hear Cursor's reply)

Uses **Windows TTS** — natural (OneCore) voices when you've picked one, otherwise SAPI. No extra install.

1. **Pick a voice (once):** Double-click **`PickVoice.bat`** (or run `SpeakClipboard.ps1 -ListVoices`). Choose a number to set as default; your choice is saved in `voice_choice.txt`.
2. **Speak clipboard:** In Cursor chat, select the AI reply and copy (Ctrl+C), then double-click **`SpeakClipboard.bat`** (or run `SpeakClipboard.ps1`).

The script speaks the clipboard. Close the window when done.

**Voice input:** Focus the chat box and press **Win+H** for Windows voice typing, then send.
