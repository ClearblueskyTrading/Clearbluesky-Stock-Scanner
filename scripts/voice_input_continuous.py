#!/usr/bin/env python3
"""
Continuous Voice Input for Cursor
=================================
Always-on mic → transcribes speech → hotkey pastes into Cursor.

Flow:
  1. Run this script (small window shows live transcript)
  2. Talk — speech is transcribed and appended to buffer
  3. Press F8 (or configured hotkey) — copies transcript to clipboard and pastes
     into the active window (Cursor chat)
  4. Press Enter in Cursor to send

Requirements: pip install SpeechRecognition pyaudio pynput pyperclip pyautogui
On Windows, PyAudio may need: pip install pipwin && pipwin install pyaudio
"""

import threading
import time
import sys
from datetime import datetime

# Optional deps — fail gracefully if missing
try:
    import speech_recognition as sr
except ImportError:
    print("Install: pip install SpeechRecognition")
    sys.exit(1)
try:
    import pyperclip
    import pyautogui
except ImportError:
    print("Install: pip install pyperclip pyautogui")
    sys.exit(1)
try:
    from pynput import keyboard
except ImportError:
    print("Install: pip install pynput")
    sys.exit(1)

HOTKEY_PASTE = "f8"  # Change if needed
PHRASE_TIMEOUT = 1.2  # Seconds of silence to end phrase
ENERGY_THRESHOLD = 300  # Mic sensitivity (adjust if too sensitive/quiet)
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024


class VoiceInputApp:
    def __init__(self):
        self.transcript_buffer: list[str] = []
        self._lock = threading.Lock()
        self._running = True
        self._listening = False
        self._last_phrase = ""

    def _listen_loop(self):
        r = sr.Recognizer()
        r.energy_threshold = ENERGY_THRESHOLD
        r.dynamic_energy_threshold = True
        r.pause_threshold = PHRASE_TIMEOUT
        r.phrase_threshold = 0.3

        with sr.Microphone(sample_rate=SAMPLE_RATE) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            self._listening = True
            while self._running:
                try:
                    audio = r.listen(source, timeout=5, phrase_time_limit=15)
                    text = r.recognize_google(audio)
                    if text and text.strip():
                        with self._lock:
                            self.transcript_buffer.append(text.strip())
                            self._last_phrase = " ".join(self.transcript_buffer)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    print(f"  [STT error: {e}]")
                except Exception as e:
                    if self._running:
                        print(f"  [Error: {e}]")
        self._listening = False

    def _on_paste_key(self):
        with self._lock:
            text = " ".join(self.transcript_buffer) if self.transcript_buffer else self._last_phrase
        if not text or not text.strip():
            return
        pyperclip.copy(text)
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "v")
        with self._lock:
            self.transcript_buffer.clear()
        print(f"  [Pasted {len(text)} chars]")

    def _on_clear_key(self):
        with self._lock:
            self.transcript_buffer.clear()
            self._last_phrase = ""
        print("  [Cleared]")

    def run_gui(self):
        try:
            import tkinter as tk
            from tkinter import font
        except ImportError:
            self._run_cli()
            return

        root = tk.Tk()
        root.title("Voice Input — F8 paste")
        root.geometry("420x180")
        root.attributes("-topmost", True)
        root.configure(bg="#1a1a2e")

        text_var = tk.StringVar(value="Listening... Say something.")

        def update_display():
            with self._lock:
                t = " ".join(self.transcript_buffer) if self.transcript_buffer else "(nothing yet)"
            text_var.set(t[:200] + "..." if len(t) > 200 else t)
            root.after(500, update_display)

        lbl = tk.Label(root, textvariable=text_var, font=("Segoe UI", 10), wraplength=380,
                       bg="#1a1a2e", fg="#e0e0e0", justify="left")
        lbl.pack(pady=10, padx=10, anchor="w")

        hint = tk.Label(root, text="F8 = Paste into Cursor  •  F9 = Clear", font=("Segoe UI", 9),
                       bg="#1a1a2e", fg="#6c6c8a")
        hint.pack(pady=4)

        def on_closing():
            self._running = False
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.after(200, update_display)

        # Hotkey listener (global)
        def on_press(key):
            try:
                if hasattr(key, "name") and key.name == "f8":
                    self._on_paste_key()
                elif hasattr(key, "name") and key.name == "f9":
                    self._on_clear_key()
            except Exception:
                pass

        kb_listener = keyboard.Listener(on_press=on_press)
        kb_listener.start()

        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()

        root.mainloop()
        self._running = False
        kb_listener.stop()

    def _run_cli(self):
        """Fallback if no tkinter."""
        print("Continuous voice input — F8 paste, F9 clear, Ctrl+C quit")
        print("Listening...\n")

        def on_press(key):
            try:
                if hasattr(key, "name") and key.name == "f8":
                    self._on_paste_key()
                elif hasattr(key, "name") and key.name == "f9":
                    self._on_clear_key()
            except Exception:
                pass

        kb_listener = keyboard.Listener(on_press=on_press)
        kb_listener.start()
        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        self._running = False
        kb_listener.stop()


def main():
    app = VoiceInputApp()
    app.run_gui()


if __name__ == "__main__":
    main()
