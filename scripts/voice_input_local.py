#!/usr/bin/env python3
"""
Local Voice Input for Cursor (no API, fully offline)
====================================================
Always-on listen mode: mic stays open, detects when you stop talking, transcribes.

Flow:
  1. Run this script
  2. Talk — speech is detected and transcribed when you pause
  3. Press F8 — pastes into active window (Cursor chat)
  4. Press F9 — clears buffer
  5. Press F10 — pause/mute (walk away without transcribing)

100% local: faster-whisper + sounddevice. No APIs.
"""

import threading
import time
import sys

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    print("Install: pip install sounddevice numpy")
    sys.exit(1)
try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Install: pip install faster-whisper")
    sys.exit(1)
try:
    import pyperclip
    import pyautogui
    from pynput import keyboard
except ImportError:
    print("Install: pip install pyperclip pyautogui pynput")
    sys.exit(1)

# Config
SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)
WHISPER_MODEL = "base"  # base=fast, small, medium, large-v3
SILENCE_FRAMES = 25  # ~0.75 sec silence to end phrase
MIN_PHRASE_FRAMES = 10  # ~0.3 sec min to avoid noise
ENERGY_THRESHOLD = 0.01  # RMS threshold for speech (raise if too sensitive)
HOTKEY_PASTE = "f8"
HOTKEY_CLEAR = "f9"
HOTKEY_PAUSE = "f10"


class LocalVoiceInput:
    def __init__(self):
        self.transcript_buffer: list[str] = []
        self._lock = threading.Lock()
        self._running = True
        self._paused = False
        self._model = None

    def _load_model(self):
        if self._model is None:
            print("Loading Whisper model (first run may download)...")
            self._model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            print("Ready. Listening... F8 paste, F9 clear.")

    def _transcribe(self, audio: np.ndarray) -> str:
        """Convert float32 mono 16kHz audio to text."""
        if len(audio) < 1600:
            return ""
        self._load_model()
        segments, _ = self._model.transcribe(audio, language="en", vad_filter=True)
        return " ".join(s.text.strip() for s in segments).strip()

    def _transcribe_and_append(self, audio: np.ndarray):
        text = self._transcribe(audio)
        if text and self._running:
            with self._lock:
                self.transcript_buffer.append(text)
            print(f"  Heard: {text[:60]}{'...' if len(text) > 60 else ''}")

    def _listen_loop(self):
        shared_buffer = []
        shared_lock = threading.Lock()

        def callback(indata, frames, time_info, status):
            if status:
                print(f"  [Audio: {status}]")
            with shared_lock:
                shared_buffer.append(indata.copy())

        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype=np.float32,
            blocksize=FRAME_SIZE,
            callback=callback,
        )
        stream.start()

        in_speech = False
        silence_frames = 0
        phrase_frames = []

        while self._running:
            time.sleep(0.02)
            if self._paused:
                with shared_lock:
                    shared_buffer.clear()
                phrase_frames.clear()
                in_speech = False
                silence_frames = 0
                continue
            with shared_lock:
                chunks = list(shared_buffer)
                shared_buffer.clear()
            for chunk in chunks:
                frame = chunk.flatten()
                rms = np.sqrt(np.mean(frame ** 2))
                is_speech = rms > ENERGY_THRESHOLD
                if is_speech:
                    in_speech = True
                    silence_frames = 0
                    phrase_frames.append(frame.copy())
                elif in_speech:
                    silence_frames += 1
                    phrase_frames.append(frame.copy())
                    if silence_frames >= SILENCE_FRAMES:
                        if len(phrase_frames) >= MIN_PHRASE_FRAMES:
                            audio = np.concatenate(phrase_frames)
                            self._transcribe_and_append(audio)
                        phrase_frames.clear()
                        in_speech = False
                        silence_frames = 0

        stream.stop()
        stream.close()

    def _on_paste(self):
        with self._lock:
            text = " ".join(self.transcript_buffer)
        if not text.strip():
            return
        pyperclip.copy(text)
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "v")
        with self._lock:
            self.transcript_buffer.clear()
        print(f"  [Pasted {len(text)} chars]")

    def _on_clear(self):
        with self._lock:
            self.transcript_buffer.clear()
        print("  [Cleared]")

    def _on_pause(self):
        self._paused = not self._paused
        print(f"  [{'Paused (muted)' if self._paused else 'Listening'}]")

    def run(self):
        def on_press(key):
            try:
                name = getattr(key, "name", None)
                if name == HOTKEY_PASTE:
                    self._on_paste()
                elif name == HOTKEY_CLEAR:
                    self._on_clear()
                elif name == HOTKEY_PAUSE:
                    self._on_pause()
            except Exception:
                pass

        print("Local Voice Input — F8 paste, F9 clear, F10 pause, Ctrl+C quit")
        print("(Fully local, no API. First run downloads Whisper model.)")
        print()

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        listen_thread.start()

        try:
            import tkinter as tk
            root = tk.Tk()
            root.title("Voice Input (local) — F8 paste")
            root.geometry("420x120")
            root.attributes("-topmost", True)
            root.configure(bg="#1a1a2e")
            text_var = tk.StringVar(value="Listening...")
            def update():
                if not self._running:
                    return
                prefix = "[PAUSED] " if self._paused else ""
                with self._lock:
                    t = " ".join(self.transcript_buffer) if self.transcript_buffer else "(listening...)"
                text_var.set(prefix + ((t[:200] + "...") if len(t) > 200 else t))
                root.after(400, update)
            lbl = tk.Label(root, textvariable=text_var, font=("Segoe UI", 10), wraplength=380,
                           bg="#1a1a2e", fg="#e0e0e0", justify="left")
            lbl.pack(pady=10, padx=10, anchor="w")
            tk.Label(root, text="F8 = Paste  •  F9 = Clear  •  F10 = Pause", font=("Segoe UI", 9),
                    bg="#1a1a2e", fg="#6c6c8a").pack(pady=4)
            def on_close():
                self._running = False
                root.destroy()
            root.protocol("WM_DELETE_WINDOW", on_close)
            root.after(200, update)
            root.mainloop()
        except ImportError:
            try:
                while self._running:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                pass
        self._running = False
        listener.stop()


def main():
    app = LocalVoiceInput()
    app.run()


if __name__ == "__main__":
    main()
