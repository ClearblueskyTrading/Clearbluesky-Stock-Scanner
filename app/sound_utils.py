# ClearBlueSky - Scan-complete alarm using system beeps (distinct patterns)

# Valid choices for config: "beep", "asterisk", "exclamation"
ALARM_CHOICES = ["beep", "asterisk", "exclamation"]


def play_system_sound(choice: str) -> None:
    """
    Play a distinct alarm pattern. choice is one of: "beep", "asterisk", "exclamation".
    All three use winsound.Beep so they are clearly different (no shared system sounds).
    """
    choice = (choice or "beep").strip().lower()
    try:
        import winsound
        import time
        if choice == "asterisk":
            # Two-tone chime: low then high
            winsound.Beep(600, 150)
            time.sleep(0.05)
            winsound.Beep(900, 200)
        elif choice == "exclamation":
            # Three quick alert beeps
            for _ in range(3):
                winsound.Beep(880, 80)
                time.sleep(0.06)
        else:
            # Single beep
            winsound.Beep(750, 300)
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
        import winsound
        import time
        winsound.Beep(800, 200)
        time.sleep(0.15)
        winsound.Beep(800, 200)
    except Exception:
        try:
            print("\a\a", end="")
        except Exception:
            pass
