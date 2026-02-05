# ============================================================
# ClearBlueSky Stock Scanner v6.5
# ============================================================

import tkinter as tk
VERSION = "6.5"
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import json
import csv
import webbrowser
import traceback
import time
import threading
import re
from datetime import datetime
from scan_settings import (
    load_scan_types,
    SCAN_PARAM_SPECS,
    SCAN_TYPES_FILE,
    export_scan_config_full,
    import_scan_config_full,
)
from sound_utils import play_scan_complete_alarm, play_watchlist_alert

# Use app folder for config and logs (portable)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "user_config.json")
LOG_FILE = os.path.join(APP_DIR, "error_log.txt")
DEFAULT_REPORTS_DIR = os.path.join(APP_DIR, "reports")
WATCHLIST_MAX = 200

# GitHub: check for new releases
GITHUB_RELEASES_API = "https://api.github.com/repos/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases/latest"
GITHUB_RELEASES_PAGE = "https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases/latest"

# Colors
BG_DARK = "#1a1a2e"
GREEN = "#28a745"
BLUE = "#007bff"
ORANGE = "#fd7e14"
PURPLE = "#6f42c1"
GRAY = "#6c757d"

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + "\n")
    except:
        pass

def log_error(e, context=""):
    log(f"{context}: {str(e)}", "ERROR")
    log(traceback.format_exc(), "TRACE")


def _parse_version(s):
    """Convert version string like '6.3' or 'v6.3' to tuple (6, 3) for comparison."""
    s = (s or "").strip().lstrip("v")
    parts = re.findall(r"\d+", s)
    if not parts:
        return (0, 0)
    return tuple(int(x) for x in parts[:2])


def _show_update_notice(root, tag, url):
    """Show a dialog that a new version is available, with link to download."""
    win = tk.Toplevel(root)
    win.title("Update available")
    win.geometry("380x140")
    win.resizable(False, False)
    win.configure(bg="white")
    win.transient(root)
    f = tk.Frame(win, bg="white", padx=16, pady=14)
    f.pack(fill="both", expand=True)
    tk.Label(
        f, text=f"A new version of ClearBlueSky is available: {tag}",
        font=("Arial", 10, "bold"), bg="white", fg="#333", wraplength=340
    ).pack(anchor="w", pady=(0, 6))
    tk.Label(
        f, text="Download the latest version from the link below.",
        font=("Arial", 9), bg="white", fg="#555", wraplength=340
    ).pack(anchor="w", pady=(0, 12))
    btn_frame = tk.Frame(f, bg="white")
    btn_frame.pack(fill="x")
    tk.Button(
        btn_frame, text="Open download page", font=("Arial", 9),
        command=lambda: (webbrowser.open(url), win.destroy()), bg=BLUE, fg="white",
        relief="flat", padx=12, pady=4, cursor="hand2"
    ).pack(side="left", padx=(0, 8))
    tk.Button(
        btn_frame, text="Later", font=("Arial", 9),
        command=win.destroy, bg=GRAY, fg="white", relief="flat", padx=12, pady=4
    ).pack(side="left")
    win.update_idletasks()
    win.grab_set()


def _check_for_updates(root):
    """Background thread: fetch latest release from GitHub; if newer, show notice on main thread."""
    try:
        import requests
        r = requests.get(GITHUB_RELEASES_API, timeout=6)
        r.raise_for_status()
        data = r.json()
        tag = data.get("tag_name", "")
        url = data.get("html_url", GITHUB_RELEASES_PAGE)
        latest = _parse_version(tag)
        current = _parse_version(VERSION)
        if latest > current:
            root.after(0, lambda t=tag, u=url: _show_update_notice(root, t, u))
    except Exception:
        pass


class AnimatedMoneyPrinter(tk.Canvas):
    """Animated money printer with flying bills"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, width=60, height=40, highlightthickness=0, **kwargs)
        self.animating = False
        self.frame = 0
        self.bills = []  # Track flying bills
        self.draw_idle()
    
    def draw_idle(self):
        self.delete("all")
        # Printer body
        self.create_rectangle(5, 15, 50, 35, fill="#666", outline="#444", width=2)
        # Paper slot
        self.create_rectangle(12, 8, 43, 15, fill="#444", outline="#333")
        # Display/light (gray when idle)
        self.create_oval(40, 20, 47, 27, fill="#888", outline="#666")
        # Feet
        self.create_rectangle(8, 35, 15, 38, fill="#555", outline="")
        self.create_rectangle(40, 35, 47, 38, fill="#555", outline="")
    
    def draw_frame(self):
        self.delete("all")
        
        # Printer body (slight shake when printing)
        shake = 1 if self.frame % 2 == 0 else -1
        self.create_rectangle(5, 15+shake, 50, 35+shake, fill="#555", outline="#333", width=2)
        # Paper slot
        self.create_rectangle(12, 8+shake, 43, 15+shake, fill="#333", outline="#222")
        # Blinking green light
        light_color = "#00ff00" if self.frame % 3 == 0 else "#00aa00"
        self.create_oval(40, 20+shake, 47, 27+shake, fill=light_color, outline="#005500")
        # Feet
        self.create_rectangle(8, 35, 15, 38, fill="#555", outline="")
        self.create_rectangle(40, 35, 47, 38, fill="#555", outline="")
        
        # Bill coming out of printer
        bill_y = (self.frame % 12)
        if bill_y < 8:
            by = 10 - bill_y
            self.create_rectangle(15, by, 40, by+6, fill="#85bb65", outline="#2d5016", width=1)
            self.create_text(27, by+3, text="$", font=("Arial", 5, "bold"), fill="#2d5016")
        
        # Flying bills animation
        if self.frame % 12 == 7:
            self.bills.append({'x': 42, 'y': 5, 'vx': 2, 'vy': -1, 'rot': 0})
        
        # Update and draw flying bills
        new_bills = []
        for bill in self.bills:
            bill['x'] += bill['vx']
            bill['y'] += bill['vy']
            bill['vy'] += 0.3  # Gravity
            bill['rot'] += 5
            
            if bill['y'] < 45 and bill['x'] < 70:
                # Draw flying bill
                x, y = bill['x'], bill['y']
                self.create_rectangle(x-6, y-3, x+6, y+3, fill="#85bb65", outline="#2d5016")
                self.create_text(x, y, text="$", font=("Arial", 4, "bold"), fill="#2d5016")
                new_bills.append(bill)
        
        self.bills = new_bills[-5:]  # Keep max 5 bills
        self.frame += 1
    
    def start(self):
        self.animating = True
        self.frame = 0
        self.bills = []
        self._animate()
    
    def stop(self):
        self.animating = False
        self.bills = []
        self.after(100, self.draw_idle)
    
    def _animate(self):
        if self.animating:
            self.draw_frame()
            self.after(80, self._animate)


class ProgressBar(tk.Canvas):
    """Clean progress bar"""
    def __init__(self, parent, width=200, height=20, color="#28a745", **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, **kwargs)
        self.w = width
        self.h = height
        self.color = color
        self.progress = 0
        self.text = "Ready"
        self.draw()
    
    def draw(self):
        self.delete("all")
        # Background
        self.create_rectangle(0, 0, self.w, self.h, fill="#e9ecef", outline="#dee2e6")
        # Fill
        if self.progress > 0:
            fw = int(self.w * self.progress / 100)
            self.create_rectangle(0, 0, fw, self.h, fill=self.color, outline="")
        # Text
        self.create_text(self.w//2, self.h//2, text=self.text, fill="#333", font=("Arial", 8, "bold"))
    
    def set(self, value, text=""):
        self.progress = max(0, min(100, value))
        self.text = text if text else f"{int(self.progress)}%"
        self.draw()
        self.update()


class TradeBotApp:
    def __init__(self, root):
        log("App starting...")
        self.root = root
        self.root.title(f"ClearBlueSky Stock Scanner v{VERSION}")
        self.root.geometry("420x460")
        self.root.minsize(380, 420)
        self.root.resizable(True, True)
        self.root.configure(bg="#f8f9fa")
        
        self.config = self.load_config()
        # Load scan-type presets from JSON so they can be shared/imported/exported
        try:
            self.scan_types = load_scan_types()
        except Exception as e:
            log_error(e, "Failed to load scan types, using defaults")
            self.scan_types = [
                {"id": "trend_long", "label": "Trend - Long-term", "scanner": "trend"},
                {"id": "swing_dips", "label": "Swing - Dips", "scanner": "swing"},
                {"id": "watchlist_open", "label": "Watchlist 3pm", "scanner": "watchlist"},
                {"id": "watchlist_tickers", "label": "Watchlist - All tickers", "scanner": "watchlist_tickers"},
                {"id": "velocity_leveraged", "label": "Velocity Barbell", "scanner": "velocity_leveraged"},
            ]
        self.build_ui()
        log("UI ready")
        # Check for new version after a short delay (non-blocking)
        root.after(1500, lambda: threading.Thread(target=_check_for_updates, args=(root,), daemon=True).start())
    
    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}

    def build_ui(self):
        # === HEADER ===
        header = tk.Frame(self.root, bg=BG_DARK, height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"☁️ ClearBlueSky Stock Scanner v{VERSION}", font=("Arial", 12, "bold"),
                fg="white", bg=BG_DARK).pack(pady=(6, 0))
        tk.Label(header, text="AI Research Tool · made with Claude", font=("Arial", 8),
                fg="#aaaaaa", bg=BG_DARK).pack(pady=(0, 4))
        
        # === MAIN CONTENT ===
        main = tk.Frame(self.root, bg="#f8f9fa", padx=14, pady=10)
        main.pack(fill="x")
        
        # --- SCANNERS ---
        scan_label = tk.Label(main, text="📊 Stock Scanner", font=("Arial", 9, "bold"),
                             bg="#f8f9fa", fg="#333")
        scan_label.pack(anchor="w", pady=(4, 2))
        
        scan_frame = tk.Frame(main, bg="white", relief="solid", bd=1)
        scan_frame.pack(fill="x", pady=(0, 6), ipady=6, ipadx=8)
        
        # Scan + Index on one row
        type_row = tk.Frame(scan_frame, bg="white")
        type_row.pack(fill="x", padx=6, pady=(6, 2))
        tk.Label(type_row, text="Scan:", font=("Arial", 9), bg="white", fg="#555").pack(side="left")
        default_label = self.scan_types[0]["label"] if self.scan_types else "Trend - Long-term"
        self.scan_type = tk.StringVar(value=default_label)
        self.scan_type_combo = ttk.Combobox(
            type_row,
            textvariable=self.scan_type,
            values=[st["label"] for st in self.scan_types] or [default_label],
            state="readonly",
            width=16,
            font=("Arial", 9),
        )
        self.scan_type_combo.pack(side="left", padx=(4, 12))
        tk.Label(type_row, text="Index:", font=("Arial", 9), bg="white", fg="#555").pack(side="left")
        self.scan_index = tk.StringVar(value="S&P 500")
        ttk.Combobox(
            type_row,
            textvariable=self.scan_index,
            values=["S&P 500", "Russell 2000"],
            state="readonly",
            width=10,
            font=("Arial", 9),
        ).pack(side="left", padx=(4, 0))
        
        scan_btn_row = tk.Frame(scan_frame, bg="white")
        scan_btn_row.pack(fill="x", padx=6, pady=(2, 4))
        
        self.scan_btn = tk.Button(
            scan_btn_row,
            text="▶ Run Scan",
            command=self.run_scan,
            bg=GREEN,
            fg="white",
            font=("Arial", 10, "bold"),
            width=12,
            height=1,
            cursor="hand2",
            relief="flat",
        )
        self.scan_btn.pack(side="left")
        
        self.scan_stop_btn = tk.Button(
            scan_btn_row,
            text="■ Stop",
            command=self.stop_scan,
            bg="#dc3545",
            fg="white",
            font=("Arial", 9),
            width=5,
            cursor="hand2",
            relief="flat",
            state="disabled",
        )
        self.scan_stop_btn.pack(side="left", padx=(5, 0))
        
        tk.Button(
            scan_btn_row,
            text="Config",
            command=self.open_scan_config_panel,
            bg="#e9ecef",
            fg="#333",
            font=("Arial", 9),
            width=6,
            cursor="hand2",
            relief="flat",
        ).pack(side="left", padx=(5, 0))
        
        self.scan_printer = AnimatedMoneyPrinter(scan_btn_row, bg="white")
        self.scan_printer.pack(side="right")
        
        self.scan_progress = ProgressBar(scan_frame, width=260, height=14, color=GREEN)
        self.scan_progress.pack(padx=6, pady=(0, 2))
        self.scan_status = tk.Label(scan_frame, text="", font=("Arial", 8), bg="white", fg="#666")
        self.scan_status.pack(anchor="w", padx=6, pady=(0, 4))
        
        # --- QUICK TICKER ---
        ticker_label = tk.Label(main, text="🔍 Quick Lookup", font=("Arial", 9, "bold"),
                               bg="#f8f9fa", fg="#333")
        ticker_label.pack(anchor="w", pady=(4, 2))
        
        ticker_frame = tk.Frame(main, bg="white", relief="solid", bd=1)
        ticker_frame.pack(fill="x", pady=(0, 6), ipady=6, ipadx=8)
        
        ticker_row = tk.Frame(ticker_frame, bg="white")
        ticker_row.pack(pady=4, padx=6)
        tk.Label(ticker_row, text="Symbol:", font=("Arial", 9), bg="white", fg="#333").pack(side="left", padx=(0, 4))
        self.symbol_entry = tk.Entry(ticker_row, width=7, font=("Arial", 11), relief="solid", bd=1)
        self.symbol_entry.pack(side="left")
        tk.Button(ticker_row, text="📄 Report", command=self.generate_report,
                  bg=ORANGE, fg="white", font=("Arial", 9, "bold"), width=8,
                  cursor="hand2", relief="flat").pack(side="left", padx=(8, 0))
        
        # --- BOTTOM BUTTONS (3 rows for more room) ---
        btn_frame = tk.Frame(main, bg="#f8f9fa")
        btn_frame.pack(fill="x", pady=(6, 2))
        
        row1 = tk.Frame(btn_frame, bg="#f8f9fa")
        row1.pack(fill="x", pady=(0, 3))
        for text, cmd in [("💼 Broker", self.open_broker),
                          ("📁 Reports", self.open_reports),
                          ("📋 Logs", self.view_logs)]:
            tk.Button(row1, text=text, command=cmd, bg="#e9ecef", fg="#333",
                     font=("Arial", 9), width=10, relief="flat", cursor="hand2").pack(side="left", padx=3)
        
        row2 = tk.Frame(btn_frame, bg="#f8f9fa")
        row2.pack(fill="x", pady=(0, 3))
        for text, cmd in [("⭐ Watchlist", self.open_watchlist),
                          ("⚙️ Settings", self.api_settings),
                          ("❓ Help", self.show_help),
                          ("📄 README", self.open_readme)]:
            tk.Button(row2, text=text, command=cmd, bg="#e9ecef", fg="#333",
                     font=("Arial", 9), width=10, relief="flat", cursor="hand2").pack(side="left", padx=3)
        
        row3 = tk.Frame(btn_frame, bg="#f8f9fa")
        row3.pack(fill="x")
        btn_width = 18
        tk.Button(row3, text="❤️ Donate to Direct Relief", command=lambda: webbrowser.open("https://www.directrelief.org/"),
                 bg="#E91E63", fg="white", font=("Arial", 9), width=btn_width, relief="flat", cursor="hand2").pack(side="left", padx=3, fill="x", expand=True)
        tk.Button(row3, text="❌ Exit", command=self.root.quit, bg="#dc3545", fg="white",
                 font=("Arial", 9), width=btn_width, relief="flat", cursor="hand2").pack(side="left", padx=3, fill="x", expand=True)
        
        self.status = tk.Label(main, text="Ready", font=("Arial", 8), bg="#f8f9fa", fg="#666")
        self.status.pack(pady=(4, 0))
        
        # Scan state
        self.scan_cancelled = False
        self.scan_start_time = 0
        self.last_scan_type = None
        self.last_scan_time = None
    
    def _on_scan_types_changed(self):
        """Reload scan types after an import, updating the dropdown."""
        try:
            new_types = load_scan_types()
            if not new_types:
                return
            old_label = self.scan_type.get() if hasattr(self, "scan_type") else None
            self.scan_types = new_types
            labels = [st["label"] for st in self.scan_types]
            self.scan_type_combo["values"] = labels
            # Preserve selection if possible, else default to first
            if old_label in labels:
                self.scan_type.set(old_label)
            else:
                self.scan_type.set(labels[0])
        except Exception as e:
            log_error(e, "Failed to reload scan types")
    
    def open_scan_config_panel(self):
        """Scan config: grid layout so Load/Save/Import/Export and parameters always visible."""
        win = tk.Toplevel(self.root)
        win.title("Scan configuration")
        win.geometry("600x720")
        win.configure(bg="white")
        win.minsize(540, 620)

        main_f = tk.Frame(win, bg="white", padx=15, pady=15)
        main_f.pack(fill="both", expand=True)
        main_f.grid_rowconfigure(3, weight=1)
        main_f.grid_columnconfigure(1, weight=1)

        # Row 0: Scan, Index
        tk.Label(main_f, text="Scan:", font=("Arial", 9), bg="white", fg="#333").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=4)
        types_list = load_scan_types()
        labels = [st["label"] for st in types_list]
        current_scan = getattr(self, "scan_type", None)
        current_scan = current_scan.get() if current_scan and hasattr(current_scan, "get") else (labels[0] if labels else "Trend - Long-term")
        scan_var = tk.StringVar(value=current_scan)
        combo = ttk.Combobox(main_f, textvariable=scan_var, values=labels, state="readonly", width=24, font=("Arial", 9))
        combo.grid(row=0, column=1, sticky="ew", padx=(0, 15), pady=4)
        tk.Label(main_f, text="Index:", font=("Arial", 9), bg="white", fg="#333").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=4)
        idx_var = tk.StringVar(value=self.scan_index.get())
        ttk.Combobox(main_f, textvariable=idx_var, values=["S&P 500", "Russell 2000"], state="readonly", width=12, font=("Arial", 9)).grid(row=0, column=3, sticky="w", pady=4)

        # Row 1: Load, Save, Import, Export (always visible)
        btn_f = tk.Frame(main_f, bg="white")
        btn_f.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(8, 12))

        def _add_buttons():
            tk.Button(btn_f, text="Save", command=lambda: _collect_and_save(), bg=GREEN, fg="white", font=("Arial", 9), width=8, relief="flat", cursor="hand2").pack(side="left", padx=(0, 6))
            tk.Button(btn_f, text="Import", command=lambda: _do_import(), bg="#17a2b8", fg="white", font=("Arial", 9), width=8, relief="flat", cursor="hand2").pack(side="left", padx=(0, 6))
            tk.Button(btn_f, text="Export", command=lambda: _do_export(), bg="#6c757d", fg="white", font=("Arial", 9), width=8, relief="flat", cursor="hand2").pack(side="left")

        # Row 2: Parameters label
        tk.Label(main_f, text="Parameters", font=("Arial", 10, "bold"), bg="white", fg="#333").grid(row=2, column=0, columnspan=4, sticky="w", pady=(0, 6))

        # Row 3: scrollable parameters (canvas + scrollbar)
        params_container = tk.Frame(main_f, bg="white")
        params_container.grid(row=3, column=0, columnspan=4, sticky="nsew", pady=(0, 10))
        params_container.grid_rowconfigure(0, weight=1)
        params_container.grid_columnconfigure(0, weight=1)
        canvas = tk.Canvas(params_container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(params_container)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=canvas.yview)
        sliders_frame = tk.Frame(canvas, bg="white")
        canvas_window = canvas.create_window(0, 0, window=sliders_frame, anchor="nw")
        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
        sliders_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

        widget_vars = {}  # key -> (var, spec) for saving

        def get_scanner():
            label = scan_var.get()
            for st in load_scan_types():
                if st.get("label") == label:
                    return st.get("scanner", "trend")
            return "trend"

        def build_sliders():
            for w in sliders_frame.winfo_children():
                w.destroy()
            widget_vars.clear()
            scanner = get_scanner()
            specs = SCAN_PARAM_SPECS.get(scanner, SCAN_PARAM_SPECS.get("trend", []))
            cfg = self.config
            for spec in specs:
                key = spec["key"]
                label_text = spec["label"]
                ptype = spec.get("type", "float")
                if ptype == "bool":
                    default = cfg.get(key, spec.get("default", True))
                    if isinstance(default, str):
                        default = default.lower() in ("true", "1", "yes")
                    var = tk.BooleanVar(value=default)
                    tk.Checkbutton(sliders_frame, text=label_text, variable=var, bg="white", font=("Arial", 9)).pack(anchor="w", pady=2)
                    widget_vars[key] = (var, spec)
                    continue
                if ptype == "str":
                    default = cfg.get(key, spec.get("default", ""))
                    if not isinstance(default, str):
                        default = str(default or "")
                    var = tk.StringVar(value=default)
                    row = tk.Frame(sliders_frame, bg="white")
                    row.pack(fill="x", pady=4)
                    tk.Label(row, text=label_text, font=("Arial", 9), bg="white", width=32, anchor="w").pack(side="left")
                    tk.Entry(row, textvariable=var, font=("Arial", 9), width=36).pack(side="left", padx=(5, 0), fill="x", expand=True)
                    widget_vars[key] = (var, spec)
                    continue
                if ptype == "choice":
                    options = spec.get("options", [])
                    default = cfg.get(key, spec.get("default", options[0] if options else ""))
                    if default not in options and options:
                        default = options[0]
                    var = tk.StringVar(value=default)
                    row = tk.Frame(sliders_frame, bg="white")
                    row.pack(fill="x", pady=4)
                    tk.Label(row, text=label_text, font=("Arial", 9), bg="white", width=32, anchor="w").pack(side="left")
                    ttk.Combobox(row, textvariable=var, values=options, state="readonly", width=34, font=("Arial", 9)).pack(side="left", padx=(5, 0), fill="x", expand=True)
                    widget_vars[key] = (var, spec)
                    continue
                else:
                    if ptype == "int_vol_k":
                        raw = cfg.get(key, spec.get("default", 500))
                        try:
                            raw = int(float(raw))
                        except (TypeError, ValueError):
                            raw = spec.get("default", 500)
                        default = int(raw / 1000) if raw >= 1000 else raw
                        default = max(spec["min"], min(spec["max"], default))
                    else:
                        default = cfg.get(key, spec.get("default", 0))
                        try:
                            default = float(default) if ptype == "float" else int(round(float(default)))
                        except (TypeError, ValueError):
                            default = spec.get("default", 0)
                        default = max(spec["min"], min(spec["max"], default))
                    var = tk.DoubleVar(value=float(default))
                    row = tk.Frame(sliders_frame, bg="white")
                    row.pack(fill="x", pady=4)
                    tk.Label(row, text=label_text, font=("Arial", 9), bg="white", width=32, anchor="w").pack(side="left")
                    res = (spec["max"] - spec["min"]) / 50.0 if ptype == "float" and (spec["max"] - spec["min"]) <= 1 else (0.5 if ptype == "float" else 1)
                    scale = tk.Scale(row, from_=spec["min"], to=spec["max"], orient="horizontal", variable=var,
                                    length=240, resolution=res, showvalue=1, bg="white", font=("Arial", 8))
                    scale.pack(side="left", padx=(5, 0))
                    widget_vars[key] = (var, spec)

        def on_scan_change_internal(*args):
            self.scan_type.set(scan_var.get())
            build_sliders()

        def _collect_and_save():
            self.scan_type.set(scan_var.get())
            self.scan_index.set(idx_var.get())
            for key, (var, spec) in widget_vars.items():
                ptype = spec.get("type", "float")
                val = var.get()
                if ptype == "int_vol_k":
                    self.config[key] = int(val) * 1000
                elif ptype == "bool":
                    self.config[key] = bool(val)
                elif ptype == "str":
                    self.config[key] = str(val).strip()
                elif ptype == "choice":
                    self.config[key] = str(val).strip()
                elif ptype == "int":
                    self.config[key] = int(round(val))
                else:
                    self.config[key] = round(float(val), 2)
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=2)
            self.status.config(text="Scan config saved")
            win.destroy()

        def _do_import():
            path = filedialog.askopenfilename(title="Import scan config", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
            if not path:
                return
            try:
                config_updates, scan_types_list = import_scan_config_full(path)
                if config_updates:
                    self.config.update(config_updates)
                    with open(CONFIG_FILE, "w") as f:
                        json.dump(self.config, f, indent=2)
                if scan_types_list and isinstance(scan_types_list, list):
                    with open(SCAN_TYPES_FILE, "w") as f:
                        json.dump(scan_types_list, f, indent=2)
                    self._on_scan_types_changed()
                    scan_var.set(self.scan_type.get())
                    combo["values"] = [st["label"] for st in load_scan_types()]
                build_sliders()
                messagebox.showinfo("Import", "Config imported.")
            except Exception as e:
                messagebox.showerror("Import failed", str(e))

        def _do_export():
            path = filedialog.asksaveasfilename(title="Export scan config", defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
            if not path:
                return
            try:
                export_cfg = dict(self.config)
                for key, (var, spec) in widget_vars.items():
                    ptype = spec.get("type", "float")
                    val = var.get()
                    if ptype == "int_vol_k":
                        export_cfg[key] = int(val) * 1000
                    elif ptype == "bool":
                        export_cfg[key] = bool(val)
                    elif ptype == "str":
                        export_cfg[key] = str(val).strip()
                    elif ptype == "int":
                        export_cfg[key] = int(round(val))
                    else:
                        export_cfg[key] = round(float(val), 2)
                export_scan_config_full(export_cfg, path, include_scan_types=True)
                messagebox.showinfo("Export", "Config and scan types exported.")
            except Exception as e:
                messagebox.showerror("Export failed", str(e))

        _add_buttons()
        try:
            build_sliders()
        except Exception as e:
            log_error(e, "Scan config build_sliders")
            tk.Label(sliders_frame, text="Parameters could not load. Check config.", font=("Arial", 9), bg="white", fg="#c00").pack(anchor="w")
        idx_var.trace("w", lambda *a: self.scan_index.set(idx_var.get()))
        scan_var.trace("w", on_scan_change_internal)

        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.update_idletasks()
        win.update()

    # === SCANNER METHODS ===

    def stop_scan(self):
        """Stop the currently running scan (any scan type)."""
        self.scan_cancelled = True
        self.scan_status.config(text="Stopping...")
    
    def _get_current_scan_def(self):
        """Return the scan-type definition for the currently selected label."""
        label = self.scan_type.get()
        for st in getattr(self, "scan_types", []):
            if st.get("label") == label:
                return st
        # Fallback based on label text if config is missing
        if "Trend" in label:
            return {"id": "trend_fallback", "label": label, "scanner": "trend"}
        if "Swing" in label or "Dip" in label:
            return {"id": "swing_fallback", "label": label, "scanner": "swing"}
        if "Watchlist" in label and "All tickers" in label:
            return {"id": "watchlist_tickers_fallback", "label": label, "scanner": "watchlist_tickers"}
        if "Watchlist" in label:
            return {"id": "watchlist_fallback", "label": label, "scanner": "watchlist"}
        if "Velocity" in label and "Leveraged" in label:
            return {"id": "velocity_leveraged_fallback", "label": label, "scanner": "velocity_leveraged"}
        if "insider" in label.lower():
            return {"id": "insider_fallback", "label": label, "scanner": "insider"}
        return None
    
    def _run_trend_scan(self, index: str):
        """Internal helper to run the Trend scan using the unified UI."""
        log("=== TREND SCAN ===")
        self.scan_cancelled = False
        self.scan_start_time = time.time()
        self.scan_progress.set(5, "Starting...")
        self.scan_status.config(text="Connecting...")
        self.scan_printer.start()
        self.scan_btn.config(state="disabled")
        self.scan_stop_btn.config(state="normal")
        self.root.update()
        
        try:
            from trend_scan_v2 import trend_scan
            
            def progress(msg):
                if self.scan_cancelled:
                    return
                log(f"Trend: {msg}")
                elapsed = int(time.time() - self.scan_start_time)
                time_str = f"{elapsed}s"
                
                lower = msg.lower()
                if "overview" in lower:
                    self.scan_progress.set(25, f"25% ({time_str})")
                    self.scan_status.config(text="Getting stock data from Finviz...")
                elif "performance" in lower:
                    self.scan_progress.set(50, f"50% ({time_str})")
                    self.scan_status.config(text="Getting performance metrics...")
                elif "merging" in lower:
                    self.scan_progress.set(65, f"65% ({time_str})")
                    self.scan_status.config(text="Combining data...")
                elif "scoring" in lower:
                    self.scan_progress.set(80, f"80% ({time_str})")
                    self.scan_status.config(text="Ranking candidates...")
                elif "done" in lower:
                    self.scan_progress.set(90, f"90% ({time_str})")
                    self.scan_status.config(text="Building report...")
                self.root.update()
            
            df = trend_scan(progress_callback=progress, index=index)
            
            if self.scan_cancelled:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "Cancelled",
                    self.scan_stop_btn,
                )
                return
            
            if df is not None and len(df) > 0:
                elapsed = int(time.time() - self.scan_start_time)
                self.generate_report_from_results(
                    df.to_dict("records"),
                    "Trend",
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    self.scan_stop_btn,
                    elapsed,
                    index=index,
                )
            else:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "No results",
                    self.scan_stop_btn,
                )
        except Exception as e:
            log_error(e, "Trend failed")
            self.scan_complete(
                self.scan_progress,
                self.scan_status,
                self.scan_printer,
                self.scan_btn,
                "Error!",
                self.scan_stop_btn,
            )
            messagebox.showerror("Error", str(e))
    
    def _run_swing_scan(self, index: str):
        """Internal helper to run the Swing/Dip scan using the unified UI."""
        log("=== SWING SCAN ===")
        self.scan_cancelled = False
        self.scan_start_time = time.time()
        self.scan_progress.set(5, "Starting...")
        self.scan_status.config(text="Connecting...")
        self.scan_printer.start()
        self.scan_btn.config(state="disabled")
        self.scan_stop_btn.config(state="normal")
        self.root.update()
        
        try:
            from enhanced_dip_scanner import run_enhanced_dip_scan
            
            def progress(msg):
                if self.scan_cancelled:
                    return
                log(f"Swing: {msg}")
                elapsed = int(time.time() - self.scan_start_time)
                time_str = f"{elapsed}s"
                self.scan_status.config(text=msg[:50])
                
                lower = msg.lower()
                if "analyzing" in lower:
                    try:
                        if "(" in msg and "/" in msg:
                            parts = msg.split("(")[1].split(")")[0].split("/")
                            cur, tot = int(parts[0]), int(parts[1])
                            pct = 10 + int((cur / tot) * 75)
                            self.scan_progress.set(pct, f"{pct}% ({time_str})")
                    except Exception:
                        pass
                elif "complete" in lower:
                    self.scan_progress.set(90, f"90% ({time_str})")
                self.root.update()
            
            results = run_enhanced_dip_scan(progress, index=index)
            
            if self.scan_cancelled:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "Cancelled",
                    self.scan_stop_btn,
                )
                return
            
            if results and len(results) > 0:
                elapsed = int(time.time() - self.scan_start_time)
                self.generate_report_from_results(
                    results,
                    "Swing",
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    self.scan_stop_btn,
                    elapsed,
                    index=index,
                )
            else:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "No dips today",
                    self.scan_stop_btn,
                )
        except Exception as e:
            log_error(e, "Swing failed")
            self.scan_complete(
                self.scan_progress,
                self.scan_status,
                self.scan_printer,
                self.scan_btn,
                "Error!",
                self.scan_stop_btn,
            )
            messagebox.showerror("Error", str(e))
    
    def _run_watchlist_scan(self):
        """Internal helper to run the Watchlist 3pm scan (watchlist tickers down X%, slider 1–25%)."""
        log("=== WATCHLIST 3PM SCAN ===")
        self.scan_cancelled = False
        self.scan_start_time = time.time()
        self.scan_progress.set(5, "Starting...")
        self.scan_status.config(text="Connecting...")
        self.scan_printer.start()
        self.scan_btn.config(state="disabled")
        self.scan_stop_btn.config(state="normal")
        self.root.update()
        try:
            from watchlist_scanner import run_watchlist_scan
            def progress(msg):
                if self.scan_cancelled:
                    return
                log(f"Watchlist: {msg}")
                elapsed = int(time.time() - self.scan_start_time)
                time_str = f"{elapsed}s"
                self.scan_status.config(text=msg[:50])
                if "(" in msg and "/" in msg:
                    try:
                        parts = msg.split("(")[1].split(")")[0].split("/")
                        cur, tot = int(parts[0]), int(parts[1])
                        pct = 10 + int((cur / tot) * 75) if tot else 50
                        self.scan_progress.set(pct, f"{pct}% ({time_str})")
                    except Exception:
                        pass
                elif "Found" in msg:
                    self.scan_progress.set(90, f"90% ({time_str})")
                self.root.update()
            results = run_watchlist_scan(progress_callback=progress, config=self.config)
            if self.scan_cancelled:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "Cancelled",
                    self.scan_stop_btn,
                )
                return
            if results and len(results) > 0:
                elapsed = int(time.time() - self.scan_start_time)
                scan_label = (self._get_current_scan_def() or {}).get("label", "Watchlist 3pm")
                self.generate_report_from_results(
                    results,
                    scan_label,
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    self.scan_stop_btn,
                    elapsed,
                )
            else:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "No watchlist tickers down in range",
                    self.scan_stop_btn,
                )
        except Exception as e:
            log_error(e, "Watchlist scan failed")
            self.scan_complete(
                self.scan_progress,
                self.scan_status,
                self.scan_printer,
                self.scan_btn,
                "Error!",
                self.scan_stop_btn,
            )
            messagebox.showerror("Error", str(e))
    
    def _run_watchlist_tickers_scan(self):
        """Internal helper to run the Watchlist - All tickers scan (no parameters)."""
        log("=== WATCHLIST - ALL TICKERS SCAN ===")
        self.scan_cancelled = False
        self.scan_start_time = time.time()
        self.scan_progress.set(5, "Starting...")
        self.scan_status.config(text="Connecting...")
        self.scan_printer.start()
        self.scan_btn.config(state="disabled")
        self.scan_stop_btn.config(state="normal")
        self.root.update()
        try:
            from watchlist_scanner import run_watchlist_tickers_scan
            def progress(msg):
                if self.scan_cancelled:
                    return
                log(f"Watchlist tickers: {msg}")
                elapsed = int(time.time() - self.scan_start_time)
                time_str = f"{elapsed}s"
                self.scan_status.config(text=msg[:50])
                if "(" in msg and "/" in msg:
                    try:
                        parts = msg.split("(")[1].split(")")[0].split("/")
                        cur, tot = int(parts[0]), int(parts[1])
                        pct = 10 + int((cur / tot) * 75) if tot else 50
                        self.scan_progress.set(pct, f"{pct}% ({time_str})")
                    except Exception:
                        pass
                elif "Found" in msg:
                    self.scan_progress.set(90, f"90% ({time_str})")
                self.root.update()
            results = run_watchlist_tickers_scan(progress_callback=progress, config=self.config)
            if self.scan_cancelled:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "Cancelled",
                    self.scan_stop_btn,
                )
                return
            if results and len(results) > 0:
                elapsed = int(time.time() - self.scan_start_time)
                self.generate_report_from_results(
                    results,
                    "Watchlist - All tickers",
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    self.scan_stop_btn,
                    elapsed,
                )
            else:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "No watchlist tickers found",
                    self.scan_stop_btn,
                )
        except Exception as e:
            log_error(e, "Watchlist tickers scan failed")
            self.scan_complete(
                self.scan_progress,
                self.scan_status,
                self.scan_printer,
                self.scan_btn,
                "Error!",
                self.scan_stop_btn,
            )
            messagebox.showerror("Error", str(e))
    
    def _run_velocity_leveraged_scan(self):
        """Internal helper to run the Velocity Leveraged ETF scan (sector proxies → recommended vehicles)."""
        log("=== VELOCITY LEVERAGED ETF SCAN ===")
        self.scan_cancelled = False
        self.scan_start_time = time.time()
        self.scan_progress.set(5, "Starting...")
        self.scan_status.config(text="Connecting...")
        self.scan_printer.start()
        self.scan_btn.config(state="disabled")
        self.scan_stop_btn.config(state="normal")
        self.root.update()
        try:
            from velocity_leveraged_scanner import run_velocity_leveraged_scan
            def progress(msg):
                if self.scan_cancelled:
                    return
                log(f"Velocity Leveraged: {msg}")
                elapsed = int(time.time() - self.scan_start_time)
                time_str = f"{elapsed}s"
                self.scan_status.config(text=msg[:50])
                if "(" in msg and "/" in msg:
                    try:
                        parts = msg.split("(")[1].split(")")[0].split("/")
                        cur, tot = int(parts[0]), int(parts[1])
                        pct = 10 + int((cur / tot) * 75) if tot else 50
                        self.scan_progress.set(pct, f"{pct}% ({time_str})")
                    except Exception:
                        pass
                elif "Leading:" in msg:
                    self.scan_progress.set(90, f"90% ({time_str})")
                self.root.update()
            results = run_velocity_leveraged_scan(progress_callback=progress, config=self.config)
            if self.scan_cancelled:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "Cancelled",
                    self.scan_stop_btn,
                )
                return
            if results and len(results) > 0:
                elapsed = int(time.time() - self.scan_start_time)
                self.generate_report_from_results(
                    results,
                    "Velocity Barbell",
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    self.scan_stop_btn,
                    elapsed,
                )
            else:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "No recommendations",
                    self.scan_stop_btn,
                )
        except Exception as e:
            log_error(e, "Velocity Leveraged scan failed")
            self.scan_complete(
                self.scan_progress,
                self.scan_status,
                self.scan_printer,
                self.scan_btn,
                "Error!",
                self.scan_stop_btn,
            )
            messagebox.showerror("Error", str(e))
    
    def _run_insider_scan(self):
        """Internal helper to run the Insider trading scan using the unified UI."""
        log("=== INSIDER SCAN ===")
        self.scan_cancelled = False
        self.scan_start_time = time.time()
        self.scan_progress.set(5, "Starting...")
        self.scan_status.config(text="Fetching insider data...")
        self.scan_printer.start()
        self.scan_btn.config(state="disabled")
        self.scan_stop_btn.config(state="normal")
        self.root.update()
        try:
            from insider_scanner import run_insider_scan
            def progress(msg):
                if self.scan_cancelled:
                    return
                log(f"Insider: {msg}")
                elapsed = int(time.time() - self.scan_start_time)
                time_str = f"{elapsed}s"
                self.scan_status.config(text=msg[:50])
                if "Found" in msg:
                    self.scan_progress.set(90, f"90% ({time_str})")
                self.root.update()
            results = run_insider_scan(progress_callback=progress, config=self.config)
            if self.scan_cancelled:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "Cancelled",
                    self.scan_stop_btn,
                )
                return
            if results and len(results) > 0:
                elapsed = int(time.time() - self.scan_start_time)
                self.generate_report_from_results(
                    results,
                    "Insider",
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    self.scan_stop_btn,
                    elapsed,
                )
            else:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "No insider transactions",
                    self.scan_stop_btn,
                )
        except Exception as e:
            log_error(e, "Insider scan failed")
            self.scan_complete(
                self.scan_progress,
                self.scan_status,
                self.scan_printer,
                self.scan_btn,
                "Error!",
                self.scan_stop_btn,
            )
            messagebox.showerror("Error", str(e))
    
    def _run_emotional_scan(self, index: str):
        """Internal helper to run the Emotional Dip scan using the unified UI."""
        log("=== EMOTIONAL DIP SCAN ===")
        self.scan_cancelled = False
        self.scan_start_time = time.time()
        self.scan_progress.set(5, "Starting...")
        self.scan_status.config(text="Connecting...")
        self.scan_printer.start()
        self.scan_btn.config(state="disabled")
        self.scan_stop_btn.config(state="normal")
        self.root.update()
        
        try:
            from emotional_dip_scanner import run_emotional_dip_scan
            
            def progress(msg):
                if self.scan_cancelled:
                    return
                log(f"Emotional: {msg}")
                elapsed = int(time.time() - self.scan_start_time)
                time_str = f"{elapsed}s"
                self.scan_status.config(text=msg[:50])
                
                lower = msg.lower()
                if "analyzing" in lower:
                    try:
                        if "(" in msg and "/" in msg:
                            parts = msg.split("(")[1].split(")")[0].split("/")
                            cur, tot = int(parts[0]), int(parts[1])
                            pct = 10 + int((cur / tot) * 75)
                            self.scan_progress.set(pct, f"{pct}% ({time_str})")
                    except Exception:
                        pass
                elif "complete" in lower:
                    self.scan_progress.set(90, f"90% ({time_str})")
                self.root.update()
            
            results = run_emotional_dip_scan(progress, index=index)
            
            if self.scan_cancelled:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "Cancelled",
                    self.scan_stop_btn,
                )
                return
            
            if results and len(results) > 0:
                elapsed = int(time.time() - self.scan_start_time)
                self.generate_report_from_results(
                    results,
                    "Emotional",
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    self.scan_stop_btn,
                    elapsed,
                    index=index,
                )
            else:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "No emotional dips found",
                    self.scan_stop_btn,
                )
        except Exception as e:
            log_error(e, "Emotional scan failed")
            self.scan_complete(
                self.scan_progress,
                self.scan_status,
                self.scan_printer,
                self.scan_btn,
                "Error!",
                self.scan_stop_btn,
            )
            messagebox.showerror("Error", str(e))
    
    def _run_premarket_scan(self, index: str):
        """Internal helper to run the Pre-Market Volume scan using the unified UI."""
        log("=== PRE-MARKET VOLUME SCAN ===")
        self.scan_cancelled = False
        self.scan_start_time = time.time()
        self.scan_progress.set(5, "Starting...")
        self.scan_status.config(text="Connecting...")
        self.scan_printer.start()
        self.scan_btn.config(state="disabled")
        self.scan_stop_btn.config(state="normal")
        self.root.update()
        
        try:
            from premarket_volume_scanner import run_premarket_volume_scan
            
            def progress(msg):
                if self.scan_cancelled:
                    return
                log(f"Premarket: {msg}")
                elapsed = int(time.time() - self.scan_start_time)
                time_str = f"{elapsed}s"
                self.scan_status.config(text=msg[:50])
                
                lower = msg.lower()
                if "analyzing" in lower:
                    try:
                        if "(" in msg and "/" in msg:
                            parts = msg.split("(")[1].split(")")[0].split("/")
                            cur, tot = int(parts[0]), int(parts[1])
                            pct = 10 + int((cur / tot) * 75)
                            self.scan_progress.set(pct, f"{pct}% ({time_str})")
                    except Exception:
                        pass
                elif "complete" in lower:
                    self.scan_progress.set(90, f"90% ({time_str})")
                self.root.update()
            
            results = run_premarket_volume_scan(progress, index=index)
            
            if self.scan_cancelled:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "Cancelled",
                    self.scan_stop_btn,
                )
                return
            
            if results and len(results) > 0:
                elapsed = int(time.time() - self.scan_start_time)
                self.generate_report_from_results(
                    results,
                    "Premarket",
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    self.scan_stop_btn,
                    elapsed,
                    index=index,
                )
            else:
                self.scan_complete(
                    self.scan_progress,
                    self.scan_status,
                    self.scan_printer,
                    self.scan_btn,
                    "No pre-market activity",
                    self.scan_stop_btn,
                )
        except Exception as e:
            log_error(e, "Premarket scan failed")
            self.scan_complete(
                self.scan_progress,
                self.scan_status,
                self.scan_printer,
                self.scan_btn,
                "Error!",
                self.scan_stop_btn,
            )
            messagebox.showerror("Error", str(e))
    
    def run_scan(self):
        """Entry point for the unified Scan button."""
        # Determine index
        index = "sp500" if "S&P" in self.scan_index.get() else "russell2000"
        
        # Route based on selected scan-type definition
        scan_def = self._get_current_scan_def()
        scanner_kind = (scan_def or {}).get("scanner", "")
        if scanner_kind == "trend":
            self._run_trend_scan(index)
        elif scanner_kind == "swing":
            self._run_swing_scan(index)
        elif scanner_kind == "watchlist":
            self._run_watchlist_scan()
        elif scanner_kind == "watchlist_tickers":
            self._run_watchlist_tickers_scan()
        elif scanner_kind == "velocity_leveraged":
            self._run_velocity_leveraged_scan()
        elif scanner_kind == "insider":
            self._run_insider_scan()
        elif scanner_kind == "emotional":
            self._run_emotional_scan(index)
        elif scanner_kind == "premarket":
            self._run_premarket_scan(index)
        else:
            messagebox.showwarning("Scan Type", "Please select a valid scan type.")
    
    def generate_report_from_results(self, results, scan_type, progress, status, printer, btn, stop_btn=None, elapsed=0, index=None):
        """Generate PDF report (analyst prompt at beginning, then stock data). index='sp500' or 'russell2000' to include market breadth."""
        try:
            from report_generator import HTMLReportGenerator

            min_score = int(self.config.get(f'{scan_type.lower()}_min_score', 0 if scan_type in ("Watchlist", "Watchlist 3pm", "Watchlist - All tickers", "Insider", "Velocity Barbell") else 65))
            reports_dir = self.config.get("reports_folder", DEFAULT_REPORTS_DIR) or DEFAULT_REPORTS_DIR
            gen = HTMLReportGenerator(save_dir=reports_dir)
            watchlist = self.config.get("watchlist", []) or []
            watchlist_set = set(str(t).upper().strip() for t in watchlist if t)

            def _ticker(r):
                return (r.get("Ticker") or r.get("ticker") or "").strip().upper()
            qualifying_tickers = [_ticker(r) for r in results if _ticker(r)]
            watchlist_matches = [t for t in qualifying_tickers if t in watchlist_set]
            if watchlist_matches:
                play_watchlist_alert()
                status.config(text=f"Watchlist match: {', '.join(watchlist_matches)}")

            def rpt_progress(msg):
                if "Processing" in msg:
                    try:
                        ticker = msg.split(":")[-1].strip()
                        progress.set(92, ticker)
                        status.config(text=f"Getting {ticker} data...")
                    except Exception:
                        pass
                self.root.update()

            path, analysis_text, analysis_package = gen.generate_combined_report_pdf(results, scan_type, min_score, rpt_progress, watchlist_tickers=watchlist_set, config=self.config, index=index)

            if path:
                file_url = "file:///" + path.replace("\\", "/").lstrip("/")
                self.last_scan_type = scan_type
                self.last_scan_time = datetime.now()
                content_to_send = json.dumps(analysis_package, indent=2) if analysis_package else (analysis_text or "") if self.config.get("openrouter_api_key") else ""
                # If we're going to call OpenRouter, keep progress bar moving through AI phase
                if self.config.get("openrouter_api_key") and content_to_send:
                    progress.set(92, "Report saved")
                    status.config(text="Opening PDF...")
                    self.root.update()
                    webbrowser.open(file_url)
                    try:
                        progress.set(94, "Preparing AI...")
                        status.config(text="Building prompt...")
                        self.root.update()
                        from openrouter_client import analyze_with_config
                        system_prompt = "You are a professional stock analyst. You are receiving a structured JSON analysis package (scan results, technical indicators, news). For each stock provide: YOUR SCORE (1-100), chart/TA summary, news check, RECOMMENDATION (BUY/HOLD/PASS), and if BUY: Entry, Stop, Target, position size. End with TOP PICKS, AVOID LIST, and RISK MANAGEMENT notes."
                        if self.config.get("rag_enabled") and self.config.get("rag_books_folder"):
                            try:
                                from rag_engine import get_rag_context_for_scan
                                rag_ctx = get_rag_context_for_scan(self.last_scan_type or "Scan", k=5)
                                if rag_ctx:
                                    system_prompt = system_prompt + "\n\n" + rag_ctx
                            except Exception:
                                pass
                        progress.set(95, "Prompt ready")
                        image_list = None
                        if self.config.get("use_vision_charts") and analysis_package and analysis_package.get("stocks"):
                            try:
                                from chart_engine import get_charts_for_tickers
                                tickers = [s.get("ticker") for s in analysis_package["stocks"] if s.get("ticker")]
                                status.config(text="Generating chart images...")
                                self.root.update()
                                charts = get_charts_for_tickers(tickers, max_charts=5, progress_callback=lambda t: (status.config(text=f"Chart {t}..."), self.root.update()))
                                image_list = [b64 for _, b64 in charts] if charts else None
                            except Exception:
                                image_list = None
                        progress.set(97, "Sending to AI...")
                        status.config(text="Sending to AI (OpenRouter) – may take a minute...")
                        self.root.update()
                        ai_response = analyze_with_config(self.config, system_prompt, content_to_send, image_base64_list=image_list)
                        progress.set(99, "Received")
                        status.config(text="Saving AI response...")
                        self.root.update()
                        base = path[:-4] if path.lower().endswith(".pdf") else path
                        ai_path = base + "_ai.txt"
                        if ai_response:
                            with open(ai_path, "w", encoding="utf-8") as f:
                                f.write(ai_response)
                            webbrowser.open("file:///" + ai_path.replace("\\", "/").lstrip("/"))
                            progress.set(100, f"Done! ({elapsed}s)")
                            status.config(text="AI analysis saved and opened")
                        else:
                            fallback = "AI returned no response (empty). You can paste the instructions below into another AI.\n\n--- Instructions ---\n" + (analysis_package.get("instructions", "") if analysis_package else "")
                            try:
                                with open(ai_path, "w", encoding="utf-8") as f:
                                    f.write(fallback)
                            except Exception:
                                pass
                            progress.set(100, f"Done ({elapsed}s)")
                            status.config(text="AI response empty; see _ai.txt for instructions")
                        self._update_status_ready()
                    except Exception as e:
                        log_error(e, "OpenRouter analysis")
                        progress.set(100, f"Done ({elapsed}s)")
                        err_short = str(e).strip()[:80]
                        status.config(text=f"AI failed: {err_short}")
                        base = path[:-4] if path.lower().endswith(".pdf") else path
                        ai_path = base + "_ai.txt"
                        fallback = f"AI analysis failed: {e}\n\nDetails in: {LOG_FILE}\n\n--- Instructions (paste into another AI if needed) ---\n" + (analysis_package.get("instructions", "") if analysis_package else "")
                        try:
                            with open(ai_path, "w", encoding="utf-8") as f:
                                f.write(fallback)
                            webbrowser.open("file:///" + ai_path.replace("\\", "/").lstrip("/"))
                        except Exception:
                            pass
                        messagebox.showwarning("AI analysis failed", f"{e}\n\nSee error_log.txt for details.\nA fallback _ai.txt was saved with instructions you can paste elsewhere.")
                        self._update_status_ready()
                else:
                    progress.set(100, f"Done! ({elapsed}s)")
                    status.config(text="Opening PDF report...")
                    self.root.update()
                    webbrowser.open(file_url)
                    self._update_status_ready()
            else:
                status.config(text=f"No stocks above score {min_score}")
        except Exception as e:
            log_error(e, "Report failed")
            status.config(text="Report error")
        
        printer.stop()
        btn.config(state="normal")
        if stop_btn:
            stop_btn.config(state="disabled")
        self._play_scan_alarm()
    
    def scan_complete(self, progress, status, printer, btn, msg, stop_btn=None):
        progress.set(0, msg)
        status.config(text="")
        printer.stop()
        btn.config(state="normal")
        if stop_btn:
            stop_btn.config(state="disabled")
        self._play_scan_alarm()
        self._update_status_ready()

    def _update_status_ready(self):
        """Update bottom status to show Ready and last scan summary."""
        try:
            if self.last_scan_type and self.last_scan_time:
                time_str = self.last_scan_time.strftime("%I:%M %p").lstrip("0") if hasattr(self.last_scan_time, "strftime") else str(self.last_scan_time)
                self.status.config(text=f"Ready | Last scan: {self.last_scan_type}, {time_str}")
            else:
                self.status.config(text="Ready")
        except Exception:
            self.status.config(text="Ready")
    
    def _play_scan_alarm(self):
        """Play alarm sound when a scan finishes (if enabled)."""
        try:
            enabled = self.config.get("play_alarm_on_complete", True)
            choice = self.config.get("alarm_sound_choice", "beep")
            play_scan_complete_alarm(alarm_sound_choice=choice, enabled=enabled)
        except Exception as e:
            log_error(e, "Alarm play")
    
    # === SINGLE TICKER ===
    
    def generate_report(self):
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol:
            return
        
        self.status.config(text=f"Loading {symbol}...")
        self.root.update()

        try:
            from report_generator import HTMLReportGenerator
            reports_dir = self.config.get("reports_folder", DEFAULT_REPORTS_DIR) or DEFAULT_REPORTS_DIR
            gen = HTMLReportGenerator(save_dir=reports_dir)
            path, _, _ = gen.generate_combined_report_pdf([{'ticker': symbol, 'score': 80}], "Analysis", 0)
            if path:
                file_url = "file:///" + path.replace("\\", "/").lstrip("/")
                webbrowser.open(file_url)
            self.status.config(text="PDF report opened")
        except Exception as e:
            self.status.config(text="Error")
            messagebox.showerror("Error", str(e))
    
    # === SETTINGS ===

    def api_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("620x720")
        win.transient(self.root)
        win.grab_set()
        win.configure(bg="white")
        win.minsize(560, 580)
        win.resizable(True, True)
        
        # Scrollable container so all settings fit on any screen
        canvas = tk.Canvas(win, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="white")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        cwin_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_canvas_configure(event):
            canvas.itemconfig(cwin_id, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        win.bind("<Destroy>", _unbind_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        tk.Label(scroll_frame, text="Settings", font=("Arial", 12, "bold"),
                bg="white", fg="#333").pack(pady=(15,10))
        
        f = tk.Frame(scroll_frame, bg="white", padx=20)
        f.pack(fill="x")
        
        tk.Label(f, text="Finviz API Key (optional):", font=("Arial", 9),
                bg="white", fg="#666").pack(anchor="w")
        api_var = tk.StringVar(value=self.config.get('finviz_api_key', ''))
        api_entry = tk.Entry(f, textvariable=api_var, width=40)
        api_entry.pack(anchor="w", pady=(2,10))
        
        # Only mask if there's a value
        def update_mask(*args):
            if api_var.get():
                api_entry.config(show="*")
            else:
                api_entry.config(show="")
        api_var.trace("w", update_mask)
        update_mask()  # Initial check
        
        tk.Label(f, text="Broker URL:", font=("Arial", 9), bg="white", fg="#666").pack(anchor="w")
        broker_var = tk.StringVar(value=self.config.get('broker_url', 'https://www.schwab.com'))
        tk.Entry(f, textvariable=broker_var, width=40).pack(anchor="w", pady=(2,10))

        # --- OpenRouter API (AI analysis) ---
        sep_openrouter = tk.Frame(scroll_frame, bg="#ddd", height=1)
        sep_openrouter.pack(fill="x", padx=20, pady=8)
        tk.Label(scroll_frame, text="OpenRouter API (AI analysis)", font=("Arial", 10, "bold"),
                bg="white", fg="#333").pack(anchor="w", padx=20)
        tk.Label(scroll_frame, text="Used when sending the analysis package to AI. One key for all models. Use credits for Gemini/Sonnet, or free model when no credits.",
                font=("Arial", 8), bg="white", fg="#666", wraplength=540, justify="left").pack(anchor="w", padx=20)
        openrouter_f = tk.Frame(scroll_frame, bg="white", padx=20)
        openrouter_f.pack(fill="x")
        tk.Label(openrouter_f, text="API Key:", font=("Arial", 9), bg="white", fg="#666").pack(anchor="w")
        openrouter_api_var = tk.StringVar(value=self.config.get("openrouter_api_key", "") or "")
        openrouter_api_entry = tk.Entry(openrouter_f, textvariable=openrouter_api_var, width=40)
        openrouter_api_entry.pack(anchor="w", pady=(2, 4))
        def openrouter_update_mask(*args):
            if openrouter_api_var.get():
                openrouter_api_entry.config(show="*")
            else:
                openrouter_api_entry.config(show="")
        openrouter_api_var.trace("w", openrouter_update_mask)
        openrouter_update_mask()
        tk.Label(openrouter_f, text="Model:", font=("Arial", 9), bg="white", fg="#666").pack(anchor="w", pady=(8, 0))
        OPENROUTER_MODELS = [
            ("Gemini 3 Pro Preview (credits)", "google/gemini-3-pro-preview"),
            ("Claude Sonnet 4.5 (credits)", "anthropic/claude-sonnet-4.5"),
            ("DeepSeek R1 T2 Chimera (free)", "tngtech/deepseek-r1t2-chimera:free"),
        ]
        current_openrouter_id = self.config.get("openrouter_model", "google/gemini-3-pro-preview") or "google/gemini-3-pro-preview"
        initial_label = "Gemini 3 Pro Preview (credits)"
        for label, mid in OPENROUTER_MODELS:
            if mid == current_openrouter_id:
                initial_label = label
                break
        openrouter_model_var = tk.StringVar(value=initial_label)
        openrouter_combo = ttk.Combobox(openrouter_f, textvariable=openrouter_model_var, width=38, state="readonly",
                                        values=[label for label, _ in OPENROUTER_MODELS])
        openrouter_combo.pack(anchor="w", pady=(2, 4))

        def openrouter_model_from_display():
            sel = openrouter_model_var.get()
            for label, mid in OPENROUTER_MODELS:
                if label == sel:
                    return mid
            return "google/gemini-3-pro-preview"
        use_vision_var = tk.BooleanVar(value=self.config.get("use_vision_charts", False))
        tk.Checkbutton(openrouter_f, text="Include chart images in AI analysis (vision layer; multimodal models only)", variable=use_vision_var,
                      bg="white", font=("Arial", 9), wraplength=540, justify="left").pack(anchor="w", pady=(6, 0))

        # --- News / Sentiment (Alpha Vantage) ---
        sep_av = tk.Frame(scroll_frame, bg="#ddd", height=1)
        sep_av.pack(fill="x", padx=20, pady=8)
        tk.Label(scroll_frame, text="News / Sentiment (Alpha Vantage)", font=("Arial", 10, "bold"),
                bg="white", fg="#333").pack(anchor="w", padx=20)
        tk.Label(scroll_frame, text="Optional. Add sentiment score and earnings-in-news flag per ticker (NEWS_SENTIMENT). Free tier: 25 requests/day.",
                font=("Arial", 8), bg="white", fg="#666", wraplength=540, justify="left").pack(anchor="w", padx=20)
        av_f = tk.Frame(scroll_frame, bg="white", padx=20)
        av_f.pack(fill="x")
        tk.Label(av_f, text="Alpha Vantage API Key:", font=("Arial", 9), bg="white", fg="#666").pack(anchor="w")
        av_var = tk.StringVar(value=self.config.get("alpha_vantage_api_key", "") or "")
        av_entry = tk.Entry(av_f, textvariable=av_var, width=40)
        av_entry.pack(anchor="w", pady=(2, 4))
        def av_mask(*args):
            av_entry.config(show="*" if av_var.get() else "")
        av_var.trace("w", av_mask)
        av_mask()

        # --- SEC insider context (10b5-1 vs discretionary) ---
        sec_insider_var = tk.BooleanVar(value=self.config.get("use_sec_insider_context", False))
        tk.Checkbutton(scroll_frame, text="Add SEC insider context for tickers with insider data (10b5-1 plan vs discretionary from Form 4)", variable=sec_insider_var,
                      bg="white", font=("Arial", 9), wraplength=540, justify="left").pack(anchor="w", padx=20, pady=(4, 0))

        # --- Backtest outcomes ---
        sep_bt = tk.Frame(scroll_frame, bg="#ddd", height=1)
        sep_bt.pack(fill="x", padx=20, pady=8)
        tk.Label(scroll_frame, text="Backtest outcomes", font=("Arial", 10, "bold"),
                bg="white", fg="#333").pack(anchor="w", padx=20)
        tk.Label(scroll_frame, text="Signals are logged each scan. Update outcomes (T+1, T+3, T+5, T+10) to see historical win rates in the JSON/API.",
                font=("Arial", 8), bg="white", fg="#666", wraplength=540, justify="left").pack(anchor="w", padx=20)
        bt_f = tk.Frame(scroll_frame, bg="white", padx=20)
        bt_f.pack(fill="x")
        def run_backtest_update():
            try:
                from backtest_db import update_outcomes
                self.status.config(text="Updating backtest outcomes...")
                win.update()
                n = update_outcomes(progress_callback=lambda m: (self.status.config(text=m), win.update()))
                self.status.config(text=f"Backtest: updated {n} outcomes")
            except Exception as e:
                log_error(e, "Backtest update")
                self.status.config(text="Backtest update failed")
        tk.Button(bt_f, text="Update backtest outcomes now", command=run_backtest_update, width=28).pack(anchor="w", pady=(2, 4))

        # --- RAG book knowledge ---
        sep_rag = tk.Frame(scroll_frame, bg="#ddd", height=1)
        sep_rag.pack(fill="x", padx=20, pady=8)
        tk.Label(scroll_frame, text="RAG book knowledge", font=("Arial", 10, "bold"),
                bg="white", fg="#333").pack(anchor="w", padx=20)
        tk.Label(scroll_frame, text="Folder of .txt and .pdf trading books. Build index (ChromaDB), then include excerpts in AI analysis.",
                font=("Arial", 8), bg="white", fg="#666", wraplength=540, justify="left").pack(anchor="w", padx=20)
        rag_f = tk.Frame(scroll_frame, bg="white", padx=20)
        rag_f.pack(fill="x")
        rag_folder_var = tk.StringVar(value=self.config.get("rag_books_folder", "") or "")
        tk.Label(rag_f, text="Books folder (.txt, .pdf):", font=("Arial", 9), bg="white", fg="#666").pack(anchor="w")
        rag_row = tk.Frame(rag_f, bg="white")
        rag_row.pack(fill="x", pady=(2, 4))
        tk.Entry(rag_row, textvariable=rag_folder_var, width=36).pack(side="left")
        def browse_rag():
            path = filedialog.askdirectory(title="Select folder of .txt / .pdf trading books", initialdir=rag_folder_var.get() or APP_DIR)
            if path:
                rag_folder_var.set(path)
        tk.Button(rag_row, text="Browse...", command=browse_rag, width=8).pack(side="left", padx=(6, 0))
        rag_status_lbl = tk.Label(rag_f, text="", font=("Arial", 8), bg="white", fg="#666")
        rag_status_lbl.pack(anchor="w", pady=(2, 0))
        def build_rag_index():
            folder = rag_folder_var.get().strip()
            rag_status_lbl.config(text="")
            if not folder:
                rag_status_lbl.config(text="Select a books folder first.")
                messagebox.showwarning("RAG", "Select a books folder first.")
                return
            try:
                from rag_engine import build_index
                rag_status_lbl.config(text="Building RAG index...")
                self.status.config(text="Building RAG index...")
                win.update()
                last_msg = [""]
                def on_progress(m):
                    last_msg[0] = m
                    rag_status_lbl.config(text=m)
                    self.status.config(text=m)
                    win.update()
                n = build_index(folder, progress_callback=on_progress)
                rag_status_lbl.config(text=f"Indexed {n} chunks." if n else (last_msg[0] or "No .txt or .pdf chunks found."))
                self.status.config(text=f"RAG index: {n} chunks")
                if n:
                    messagebox.showinfo("RAG", f"RAG index built: {n} chunks from your books folder.")
                else:
                    messagebox.showwarning("RAG", last_msg[0] or "No .txt or .pdf files found, or ChromaDB failed. Check the folder has .txt/.pdf files and that ChromaDB is installed (pip install chromadb PyMuPDF).")
            except Exception as e:
                log_error(e, "RAG build")
                err = str(e)
                rag_status_lbl.config(text="Build failed.")
                self.status.config(text="RAG build failed")
                messagebox.showerror("RAG build failed", err)
        tk.Button(rag_f, text="Build RAG index", command=build_rag_index, width=20).pack(anchor="w", pady=(2, 4))
        rag_enabled_var = tk.BooleanVar(value=self.config.get("rag_enabled", False))
        tk.Checkbutton(rag_f, text="Include RAG excerpts in AI analysis", variable=rag_enabled_var,
                      bg="white", font=("Arial", 9), wraplength=540, justify="left").pack(anchor="w")
        
        # --- Reports output folder ---
        sep_reports = tk.Frame(scroll_frame, bg="#ddd", height=1)
        sep_reports.pack(fill="x", padx=20, pady=8)
        tk.Label(scroll_frame, text="Reports", font=("Arial", 10, "bold"),
                bg="white", fg="#333").pack(anchor="w", padx=20)
        tk.Label(scroll_frame, text="PDF reports (date/time stamped) are saved in the folder below. Include TA: SMAs, RSI, MACD, BB, ATR, Fib per ticker (slower when enabled).",
                font=("Arial", 8), bg="white", fg="#666", wraplength=540, justify="left").pack(anchor="w", padx=20)
        reports_f = tk.Frame(scroll_frame, bg="white", padx=20)
        reports_f.pack(fill="x")
        include_ta_var = tk.BooleanVar(value=self.config.get("include_ta_in_report", True))
        tk.Checkbutton(reports_f, text="Include TA in report (SMAs, RSI, MACD, BB, ATR, Fib)", variable=include_ta_var,
                      bg="white", font=("Arial", 9), wraplength=540, justify="left").pack(anchor="w", pady=(0, 6))
        tk.Label(reports_f, text="Output folder:", font=("Arial", 9), bg="white", fg="#666").pack(anchor="w")
        reports_folder_var = tk.StringVar(value=self.config.get("reports_folder", "") or DEFAULT_REPORTS_DIR)
        reports_row = tk.Frame(reports_f, bg="white")
        reports_row.pack(fill="x", pady=(2, 4))
        tk.Entry(reports_row, textvariable=reports_folder_var, width=42).pack(side="left")
        def browse_reports():
            path = filedialog.askdirectory(title="Select reports folder", initialdir=reports_folder_var.get() or APP_DIR)
            if path:
                reports_folder_var.set(path)
        tk.Button(reports_row, text="Browse...", command=browse_reports, width=8).pack(side="left", padx=(6, 0))
        
        # --- Scan-complete alarm ---
        sep = tk.Frame(scroll_frame, bg="#ddd", height=1)
        sep.pack(fill="x", padx=20, pady=8)
        tk.Label(scroll_frame, text="Scan-complete alarm", font=("Arial", 10, "bold"),
                bg="white", fg="#333").pack(anchor="w", padx=20)
        tk.Label(scroll_frame, text="Play a system sound when a scan finishes.", font=("Arial", 8),
                bg="white", fg="#666", wraplength=540, justify="left").pack(anchor="w", padx=20)
        
        alarm_f = tk.Frame(scroll_frame, bg="white", padx=20)
        alarm_f.pack(fill="x")
        play_alarm_var = tk.BooleanVar(value=self.config.get("play_alarm_on_complete", True))
        tk.Checkbutton(alarm_f, text="Play alarm when scan finishes", variable=play_alarm_var,
                      bg="white", font=("Arial", 9), wraplength=540, justify="left").pack(anchor="w")
        tk.Label(alarm_f, text="Sound:", font=("Arial", 9), bg="white").pack(anchor="w", pady=(6,0))
        alarm_row = tk.Frame(alarm_f, bg="white")
        alarm_row.pack(fill="x", pady=(2,4))
        alarm_choice_var = tk.StringVar(value=(self.config.get("alarm_sound_choice", "beep") or "beep").capitalize())
        alarm_combo = ttk.Combobox(alarm_row, textvariable=alarm_choice_var, values=("Beep", "Asterisk", "Exclamation"),
                                  state="readonly", width=14, font=("Arial", 9))
        alarm_combo.pack(side="left")
        def test_alarm():
            c = alarm_choice_var.get().strip().lower()
            choice = c if c in ("beep", "asterisk", "exclamation") else "beep"
            play_scan_complete_alarm(alarm_sound_choice=choice, enabled=True)
        tk.Button(alarm_row, text="Test", command=test_alarm, width=5).pack(side="left", padx=(8,0))
        
        def save():
            self.config['finviz_api_key'] = api_var.get()
            self.config['broker_url'] = broker_var.get()
            self.config['openrouter_api_key'] = openrouter_api_var.get().strip()
            self.config['openrouter_model'] = openrouter_model_from_display()
            self.config['use_vision_charts'] = use_vision_var.get()
            self.config['alpha_vantage_api_key'] = av_var.get().strip()
            self.config['use_sec_insider_context'] = sec_insider_var.get()
            self.config['rag_books_folder'] = rag_folder_var.get().strip()
            self.config['rag_enabled'] = rag_enabled_var.get()
            raw_reports = reports_folder_var.get().strip()
            self.config['reports_folder'] = raw_reports if raw_reports else DEFAULT_REPORTS_DIR
            self.config['include_ta_in_report'] = include_ta_var.get()
            self.config['play_alarm_on_complete'] = play_alarm_var.get()
            c = alarm_choice_var.get().strip().lower()
            self.config['alarm_sound_choice'] = c if c in ("beep", "asterisk", "exclamation") else "beep"
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            win.destroy()
        
        btn_frame = tk.Frame(scroll_frame, bg="white")
        btn_frame.pack(pady=(15, 10))
        tk.Button(btn_frame, text="Save", command=save, bg=GREEN, fg="white",
                 font=("Arial", 10, "bold"), width=10, relief="flat").pack(side="left", padx=5)
        tk.Frame(scroll_frame, bg="white", height=20).pack()  # bottom padding
    
    def open_watchlist(self):
        """Edit watchlist: stocks that get 2 beeps and top/highlighted in report when they appear in a scan."""
        win = tk.Toplevel(self.root)
        win.title("Watchlist")
        win.geometry("320x340")
        win.configure(bg="white")
        win.transient(self.root)
        f = tk.Frame(win, bg="white", padx=12, pady=12)
        f.pack(fill="both", expand=True)
        tk.Label(f, text="Stocks on your watchlist appear at the top of scan reports and trigger 2 beeps.",
                font=("Arial", 9), bg="white", fg="#555", wraplength=280).pack(anchor="w", pady=(0, 4))
        count_label = tk.Label(f, text="", font=("Arial", 9), bg="white", fg="#666")
        count_label.pack(anchor="w", pady=(0, 4))
        list_frame = tk.Frame(f, bg="white")
        list_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        listbox = tk.Listbox(list_frame, font=("Arial", 10), height=10, yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        loaded = self.config.get("watchlist", []) or []
        for t in loaded[:WATCHLIST_MAX]:
            if isinstance(t, str) and t.strip():
                listbox.insert(tk.END, t.strip().upper())
        def update_count():
            n = listbox.size()
            count_label.config(text=f"{n} / {WATCHLIST_MAX} tickers")
        update_count()
        btn_row = tk.Frame(f, bg="white")
        btn_row.pack(fill="x", pady=(8, 4))
        def _valid_ticker(s):
            s = (s or "").strip().upper()
            if not s or len(s) > 5:
                return None
            if not s.isalpha():
                return None
            return s

        def add_ticker():
            if listbox.size() >= WATCHLIST_MAX:
                messagebox.showinfo("Watchlist", f"Watchlist is limited to {WATCHLIST_MAX} tickers.", parent=win)
                return
            ticker = simpledialog.askstring("Add ticker", "Symbol (1–5 letters):", parent=win)
            sym = _valid_ticker(ticker)
            if not sym:
                if ticker and ticker.strip():
                    messagebox.showwarning("Watchlist", "Symbol must be 1–5 letters (e.g. AAPL).", parent=win)
                return
            existing = {listbox.get(i) for i in range(listbox.size())}
            if sym in existing:
                messagebox.showinfo("Watchlist", f"{sym} is already on the watchlist.", parent=win)
                return
            listbox.insert(tk.END, sym)
            update_count()
        def remove_ticker():
            sel = listbox.curselection()
            if sel:
                listbox.delete(sel[0])
                update_count()
        def clear_all():
            listbox.delete(0, tk.END)
            update_count()
        def save_watchlist():
            tickers = [listbox.get(i) for i in range(listbox.size())]
            tickers = [t for t in tickers if t and str(t).strip()]
            tickers = tickers[:WATCHLIST_MAX]
            self.config["watchlist"] = tickers
            try:
                with open(CONFIG_FILE, "r") as fp:
                    data = json.load(fp)
            except Exception:
                data = {}
            data["watchlist"] = tickers
            with open(CONFIG_FILE, "w") as fp:
                json.dump(data, fp, indent=2)
            self.status.config(text=f"Watchlist saved ({len(tickers)} tickers)")
            win.destroy()
        def import_csv():
            path = filedialog.askopenfilename(
                title="Import Finviz CSV",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                parent=win,
            )
            if not path:
                return
            try:
                existing = {listbox.get(i) for i in range(listbox.size())}
                ticker_col = None
                imported = 0
                skipped = 0
                hit_limit = False
                with open(path, "r", encoding="utf-8", errors="replace") as fp:
                    reader = csv.reader(fp)
                    try:
                        header = next(reader)
                    except StopIteration:
                        messagebox.showwarning("Import", "CSV file is empty.", parent=win)
                        return
                    # Finviz exports use "Ticker" or "Symbol"; try case-insensitive match
                    for i, col in enumerate(header):
                        if (col or "").strip().lower() in ("ticker", "symbol"):
                            ticker_col = i
                            break
                    if ticker_col is None:
                        # Try first column as ticker
                        ticker_col = 0
                    for row in reader:
                        if ticker_col >= len(row):
                            continue
                        t = (row[ticker_col] or "").strip().upper()
                        if not t or len(t) > 10 or not t.isalpha():
                            skipped += 1
                            continue
                        if t in existing:
                            skipped += 1
                            continue
                        existing.add(t)
                        if listbox.size() >= WATCHLIST_MAX:
                            hit_limit = True
                            break
                        listbox.insert(tk.END, t)
                        imported += 1
                update_count()
                msg = f"Imported {imported} ticker(s) from CSV."
                if skipped > 0:
                    msg += f" Skipped {skipped} invalid or duplicate."
                if hit_limit:
                    msg += f" Watchlist limit ({WATCHLIST_MAX}) reached."
                messagebox.showinfo("Import", msg, parent=win)
            except Exception as e:
                messagebox.showerror("Import failed", str(e), parent=win)
        tk.Button(btn_row, text="Add", command=add_ticker, bg=GREEN, fg="white", font=("Arial", 9), width=6, relief="flat", cursor="hand2").pack(side="left", padx=(0, 4))
        tk.Button(btn_row, text="Remove", command=remove_ticker, bg="#6c757d", fg="white", font=("Arial", 9), width=6, relief="flat", cursor="hand2").pack(side="left", padx=2)
        tk.Button(btn_row, text="Clear", command=clear_all, bg="#6c757d", fg="white", font=("Arial", 9), width=6, relief="flat", cursor="hand2").pack(side="left", padx=2)
        tk.Button(btn_row, text="Import CSV", command=import_csv, bg=BLUE, fg="white", font=("Arial", 9), width=9, relief="flat", cursor="hand2").pack(side="left", padx=2)
        tk.Button(btn_row, text="Save", command=save_watchlist, bg=BLUE, fg="white", font=("Arial", 9), width=6, relief="flat", cursor="hand2").pack(side="left", padx=2)

    def open_broker(self):
        webbrowser.open(self.config.get('broker_url', 'https://www.schwab.com'))
    
    def open_reports(self):
        reports_dir = self.config.get("reports_folder", DEFAULT_REPORTS_DIR) or DEFAULT_REPORTS_DIR
        os.makedirs(reports_dir, exist_ok=True)
        os.startfile(reports_dir)
    
    def view_logs(self):
        if os.path.exists(LOG_FILE):
            os.startfile(LOG_FILE)
    
    def open_readme(self):
        """Open README.md from the app folder (browser or default app)."""
        readme_path = os.path.join(APP_DIR, "README.md")
        if os.path.isfile(readme_path):
            url = "file:///" + readme_path.replace("\\", "/").lstrip("/")
            webbrowser.open(url)
        else:
            messagebox.showinfo("README", "README.md not found in app folder.")

    def show_help(self):
        help_text = """
ClearBlueSky Stock Scanner v6.5

QUICK START:
1. Select scan type and index (N/A for Watchlist / Velocity Barbell / Insider).
2. Click Run Scan. You get: PDF report + JSON analysis package.
3. If OpenRouter API key is set (Settings): AI analysis runs and opens *_ai.txt.

OUTPUTS (per run):
• PDF – Report with Master Trading Report Directive + per-ticker data.
• JSON – Same data + "instructions" field (use with any AI: "follow the instructions in this JSON").
• *_ai.txt – AI analysis (only if OpenRouter key set in Settings).

SCANNERS:
• Trend – Uptrending (S&P 500 / Russell 2000). Best: after close.
• Swing – Oversold dips with news/analyst. Best: 2:30–4:00 PM.
• Watchlist 3pm – Watchlist tickers down X% today (slider 1–25%). Best: ~3 PM.
• Watchlist – All tickers – Scan all watchlist tickers, no filters.
• Velocity Barbell – Foundation + Runner (or Single Shot) from sector signals. Config: min sector %, theme.
• Insider – Latest insider transactions (Finviz).
• Emotional Dip – Late-day dip setup. Best: ~3:30 PM.
• Pre-Market – Pre-market volume. Best: 7–9:25 AM.

WATCHLIST:
• Add tickers (max 200). When one appears in a scan: 2 beeps + ★ WATCHLIST in report.
• Import from Finviz CSV: Watchlist → Import CSV.

SETTINGS (optional):
• Finviz API key – Scanner data (or scraping).
• OpenRouter API key + model – Enables AI analysis → *_ai.txt.
• Alpha Vantage key – Sentiment + headlines per ticker.
• RAG books folder – .txt/.pdf books; Build RAG index; include in AI prompt.
• Include TA / SEC insider context / chart images – Toggle report and AI inputs.

See app/WORKFLOW.md for full pipeline. Scores: 90–100 Elite | 70–89 Strong | 60–69 Decent | <60 Skip.
─────────────────────────────────
Made with Claude AI · ClearBlueSky v6.5
─────────────────────────────────
        """
        messagebox.showinfo("Help", help_text)


def main():
    log("=" * 40)
    log(f"ClearBlueSky v{VERSION}")
    root = tk.Tk()
    TradeBotApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
