# ============================================================
# ClearBlueSky - Scan Alerts Module
# Sound + Toast notifications for scan completion
# ============================================================

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Try to import Windows-specific modules
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

# Try to import win10toast for Windows toast notifications
try:
    from win10toast import ToastNotifier
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False


def play_sound(sound_type="success"):
    """
    Play a notification sound.
    sound_type: 'success', 'error', 'warning'
    """
    if not WINSOUND_AVAILABLE:
        return

    try:
        if sound_type == "success":
            # Play a pleasant chime
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        elif sound_type == "error":
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
        elif sound_type == "warning":
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
        else:
            # Default notification sound
            winsound.MessageBeep(winsound.MB_OK)
    except Exception:
        pass


def play_custom_beep(frequency=800, duration=200):
    """Play a custom beep with specified frequency and duration."""
    if not WINSOUND_AVAILABLE:
        return

    try:
        winsound.Beep(frequency, duration)
    except Exception:
        pass


def play_scan_complete_melody():
    """Play a pleasant melody when scan completes successfully."""
    if not WINSOUND_AVAILABLE:
        return

    def _play():
        try:
            # Pleasant ascending chime
            winsound.Beep(523, 100)  # C5
            winsound.Beep(659, 100)  # E5
            winsound.Beep(784, 150)  # G5
        except Exception:
            pass

    # Play in background thread to not block UI
    threading.Thread(target=_play, daemon=True).start()


def show_toast(title, message, duration=5):
    """
    Show a Windows 10/11 toast notification.
    Falls back to nothing if not available.
    """
    if not TOAST_AVAILABLE:
        return

    def _show():
        try:
            toaster = ToastNotifier()
            toaster.show_toast(
                title,
                message,
                duration=duration,
                threaded=True
            )
        except Exception:
            pass

    # Run in background to not block
    threading.Thread(target=_show, daemon=True).start()


class ToastPopup:
    """
    Custom toast-style popup that works on all systems.
    Appears in the corner of the screen and fades away.
    """

    def __init__(self, parent, title, message, duration=4000,
                 bg_color="#28a745", fg_color="white", position="bottom-right"):
        """
        Create a toast popup.

        Args:
            parent: Parent tkinter window
            title: Toast title
            message: Toast message
            duration: Display time in milliseconds
            bg_color: Background color
            fg_color: Text color
            position: 'bottom-right', 'bottom-left', 'top-right', 'top-left'
        """
        self.parent = parent
        self.duration = duration

        # Create toplevel window
        self.toast = tk.Toplevel(parent)
        self.toast.overrideredirect(True)  # No window decorations
        self.toast.attributes('-topmost', True)
        self.toast.configure(bg=bg_color)

        # Create content
        frame = tk.Frame(self.toast, bg=bg_color, padx=15, pady=10)
        frame.pack(fill="both", expand=True)

        # Title
        tk.Label(frame, text=title, font=("Arial", 10, "bold"),
                bg=bg_color, fg=fg_color).pack(anchor="w")

        # Message
        tk.Label(frame, text=message, font=("Arial", 9),
                bg=bg_color, fg=fg_color, wraplength=250).pack(anchor="w", pady=(2,0))

        # Close button
        close_btn = tk.Label(frame, text="×", font=("Arial", 12, "bold"),
                            bg=bg_color, fg=fg_color, cursor="hand2")
        close_btn.place(relx=1.0, rely=0, anchor="ne")
        close_btn.bind("<Button-1>", lambda e: self.close())

        # Position the toast
        self.toast.update_idletasks()
        width = self.toast.winfo_width()
        height = self.toast.winfo_height()

        screen_width = self.toast.winfo_screenwidth()
        screen_height = self.toast.winfo_screenheight()

        padding = 20

        if position == "bottom-right":
            x = screen_width - width - padding
            y = screen_height - height - padding - 50  # Account for taskbar
        elif position == "bottom-left":
            x = padding
            y = screen_height - height - padding - 50
        elif position == "top-right":
            x = screen_width - width - padding
            y = padding
        else:  # top-left
            x = padding
            y = padding

        self.toast.geometry(f"+{x}+{y}")

        # Auto-close after duration
        self.toast.after(duration, self.close)

        # Click anywhere to close
        self.toast.bind("<Button-1>", lambda e: self.close())

    def close(self):
        """Close the toast."""
        try:
            self.toast.destroy()
        except Exception:
            pass


def show_scan_complete_alert(parent, scan_type, result_count, elapsed_time=None,
                              success=True, enable_sound=True, enable_toast=True):
    """
    Show a scan complete notification with sound and toast.

    Args:
        parent: Parent tkinter window
        scan_type: 'Trend' or 'Swing'
        result_count: Number of results found
        elapsed_time: Time taken in seconds (optional)
        success: Whether scan was successful
        enable_sound: Play sound notification
        enable_toast: Show toast notification
    """
    if success:
        if result_count > 0:
            title = f"{scan_type} Scan Complete!"
            time_str = f" in {elapsed_time}s" if elapsed_time else ""
            message = f"Found {result_count} stocks{time_str}"
            bg_color = "#28a745"  # Green
            sound_type = "success"

            if enable_sound:
                play_scan_complete_melody()
        else:
            title = f"{scan_type} Scan Complete"
            message = "No matching stocks found"
            bg_color = "#fd7e14"  # Orange
            sound_type = "warning"

            if enable_sound:
                play_sound("warning")
    else:
        title = f"{scan_type} Scan Failed"
        message = "Check logs for details"
        bg_color = "#dc3545"  # Red
        sound_type = "error"

        if enable_sound:
            play_sound("error")

    # Show toast notification
    if enable_toast:
        ToastPopup(parent, title, message, bg_color=bg_color)


def show_custom_toast(parent, title, message, toast_type="info"):
    """
    Show a custom toast notification.

    Args:
        parent: Parent tkinter window
        title: Toast title
        message: Toast message
        toast_type: 'success', 'error', 'warning', 'info'
    """
    colors = {
        "success": "#28a745",
        "error": "#dc3545",
        "warning": "#fd7e14",
        "info": "#007bff"
    }

    bg_color = colors.get(toast_type, "#007bff")
    ToastPopup(parent, title, message, bg_color=bg_color)


# Alert settings management
def load_alert_settings():
    """Load alert settings from config."""
    import json
    config_file = os.path.join(BASE_DIR, "user_config.json")
    defaults = {
        "alerts_enabled": True,
        "alert_sound_enabled": True,
        "alert_toast_enabled": True,
    }

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            for key, value in defaults.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception:
        return defaults


def save_alert_settings(settings):
    """Save alert settings to config."""
    import json
    config_file = os.path.join(BASE_DIR, "user_config.json")

    try:
        # Load existing config
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception:
            config = {}

        # Update with alert settings
        config.update(settings)

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass


# Test function
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Alert Test")
    root.geometry("300x200")

    def test_success():
        show_scan_complete_alert(root, "Trend", 15, 32)

    def test_warning():
        show_scan_complete_alert(root, "Swing", 0, 45)

    def test_error():
        show_scan_complete_alert(root, "Trend", 0, success=False)

    tk.Button(root, text="Test Success Alert", command=test_success).pack(pady=10)
    tk.Button(root, text="Test Warning Alert", command=test_warning).pack(pady=10)
    tk.Button(root, text="Test Error Alert", command=test_error).pack(pady=10)

    root.mainloop()
