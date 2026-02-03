# ClearBlueSky - Scan-complete alarm (cross-platform: Windows, Linux, macOS)

# Valid choices for config: "beep", "asterisk", "exclamation"
ALARM_CHOICES = ["beep", "asterisk", "exclamation"]


def _beep_pygame(freq: int, duration_ms: int) -> None:
    """Play a tone using pygame (works on any OS)."""
    try:
        import pygame
        import array
        import math
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        n_samples = int(round(22050 * duration_ms / 1000))
        buf = array.array("h", [0] * n_samples)
        max_amplitude = 2 ** (16 - 1) - 1
        for i in range(n_samples):
            t = float(i) / 22050
            buf[i] = int(max_amplitude * 0.3 * math.sin(2 * math.pi * freq * t))
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        sound.play()
        pygame.time.wait(duration_ms)
    except Exception:
        pass


def _beep_windows(freq: int, duration_ms: int) -> None:
    """Play a tone using winsound (Windows only)."""
    try:
        import winsound
        winsound.Beep(freq, duration_ms)
    except Exception:
        print("\a", end="")


def _beep(freq: int, duration_ms: int) -> None:
    """Play a single beep; use Windows API on Windows, pygame elsewhere."""
    import sys
    if sys.platform == "win32":
        _beep_windows(freq, duration_ms)
    else:
        _beep_pygame(freq, duration_ms)


def play_system_sound(choice: str) -> None:
    """
    Play a distinct alarm pattern. choice is one of: "beep", "asterisk", "exclamation".
    Cross-platform: Windows uses winsound; Linux/macOS use pygame.
    """
    choice = (choice or "beep").strip().lower()
    try:
        import time
        if choice == "asterisk":
            _beep(600, 150)
            time.sleep(0.05)
            _beep(900, 200)
        elif choice == "exclamation":
            for _ in range(3):
                _beep(880, 80)
                time.sleep(0.06)
        else:
            _beep(750, 300)
    except Exception:
        try:
            print("\a", end="")
        except Exception:
            pass


def play_scan_complete_alarm(alarm_sound_choice: str = "beep", enabled: bool = True) -> bool:
    """
    Play the scan-complete alarm using system sounds.
    alarm_sound_choice: "beep" | "asterisk" | "exclamation"
    Returns True if sound was played.
    """
    if not enabled:
        return False
    choice = (alarm_sound_choice or "beep").strip().lower()
    if choice not in ALARM_CHOICES:
        choice = "beep"
    play_system_sound(choice)
    return True


def play_watchlist_alert() -> None:
    """Play 2 beeps when a watchlist stock appears in scan results."""
    try:
        import time
        _beep(800, 200)
        time.sleep(0.15)
        _beep(800, 200)
    except Exception:
        try:
            print("\a\a", end="")
        except Exception:
            pass
