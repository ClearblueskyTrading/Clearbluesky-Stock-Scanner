# Continuous Voice Input for Cursor

Talk into your mic, then paste into Cursor with one key. Press Enter to send.

## Quick Start

```bash
# Install dependencies (one-time)
pip install SpeechRecognition pyaudio pynput pyperclip pyautogui
```

On Windows, if `pyaudio` fails to install:
```bash
pip install pipwin
pipwin install pyaudio
```

```bash
# Run
python D:\cursor\scripts\voice_input_continuous.py
```

## How It Works

1. **Run the script** — A small window appears showing the live transcript
2. **Talk** — Speech is captured and transcribed (Google Speech API, free)
3. **F8** — Copies transcript to clipboard and pastes into the active window (Cursor chat)
4. **F9** — Clears the buffer
5. **Enter** in Cursor — Sends your message

## Flow

- Mic is always on
- Phrase ends after ~1.2 sec of silence
- Transcript accumulates until you press F8
- F8 pastes into whatever window is focused — make sure Cursor chat input is focused first

## Hotkeys

| Key | Action |
|-----|--------|
| F8 | Paste transcript into active window |
| F9 | Clear transcript buffer |

## Troubleshooting

- **"No module named"** — Install missing packages with pip
- **PyAudio install fails** — Use `pipwin install pyaudio` on Windows
- **No speech detected** — Check mic permissions; adjust `ENERGY_THRESHOLD` in the script (lower = more sensitive)
- **Paste goes to wrong window** — Click in Cursor's chat input before pressing F8

## Internet Required

Uses Google's free speech recognition API. For offline, you'd need to swap in `recognize_sphinx` (lower accuracy) or a local Whisper setup.
