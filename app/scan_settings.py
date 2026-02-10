# ============================================================
# ClearBlueSky - Scan Parameters & User Settings
# Made with Claude AI
# ============================================================

import json
import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

# Get the directory where this script is located (portable support)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "user_config.json")
PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio.json")
SCAN_TYPES_FILE = os.path.join(BASE_DIR, "scan_types.json")
SCAN_PRESETS_FILE = os.path.join(BASE_DIR, "scan_presets.json")

# Default scan type definitions (can be customized & shared via JSON)
DEFAULT_SCAN_TYPES = [
    {
        "id": "velocity_trend_growth",
        "label": "Velocity Trend Growth",
        "scanner": "velocity_trend_growth",
    },
    {
        "id": "swing_dips",
        "label": "Swing - Dips",
        "scanner": "swing",  # uses emotional_dip_scanner (emotional-only dips, always on)
    },
    {
        "id": "watchlist",
        "label": "Watchlist",
        "scanner": "watchlist",  # Filter: Down X% today or All tickers
    },
    {
        "id": "premarket",
        "label": "Pre-Market",
        "scanner": "premarket",  # combined: premarket_volume_scanner + velocity_scanner premarket
    },
]

# Slider/param specs per scanner (core params only; strict institutional gates removed so scans pass)
SCAN_PARAM_SPECS = {
    "velocity_trend_growth": [
        {"key": "vtg_trend_days", "label": "Trend Days", "type": "choice", "default": 20, "options": [20, 50]},
        {"key": "vtg_target_return_pct", "label": "Target Return %", "min": 1, "max": 300, "default": 5, "type": "float",
         "hint": "1-5% weak markets | 8-15% strong. 20d stocks: 8-15% typical"},
        {"key": "vtg_risk_pct", "label": "Risk % of Account", "min": 5, "max": 50, "default": 30, "type": "float"},
        {"key": "vtg_max_tickers", "label": "Max Tickers", "min": 5, "max": 50, "default": 20, "type": "int"},
        {"key": "vtg_min_price", "label": "Min Price $", "min": 1, "max": 100, "default": 25, "type": "float"},
        {"key": "vtg_max_price", "label": "Max Price $", "min": 50, "max": 2000, "default": 600, "type": "float"},
        {"key": "vtg_require_beats_spy", "label": "Require beats SPY", "default": False, "type": "bool"},
        {"key": "vtg_min_volume", "label": "Min Avg Volume (K)", "min": 0, "max": 10000, "default": 100, "type": "int"},
        {"key": "vtg_require_volume_confirm", "label": "Volume above 20d avg", "default": False, "type": "bool"},
        {"key": "vtg_require_ma_stack", "label": "Require MA stack (10>20>50)", "default": False, "type": "bool"},
        {"key": "vtg_rsi_min", "label": "RSI min (0=off)", "min": 0, "max": 100, "default": 0, "type": "int"},
        {"key": "vtg_rsi_max", "label": "RSI max (100=off)", "min": 0, "max": 100, "default": 100, "type": "int"},
    ],
    "swing": [
        {"key": "emotional_min_score", "label": "Min Score", "min": 50, "max": 90, "default": 65, "type": "int"},
        {"key": "emotional_dip_min_percent", "label": "Min Dip %", "min": 0, "max": 5, "default": 1.0, "type": "float"},
        {"key": "emotional_dip_max_percent", "label": "Max Dip %", "min": 1, "max": 10, "default": 5.0, "type": "float"},
        {"key": "emotional_min_volume_ratio", "label": "Min Rel Vol", "min": 1.0, "max": 5.0, "default": 1.2, "type": "float"},
        {"key": "emotional_min_upside_to_target", "label": "Min Upside %", "min": 0, "max": 30, "default": 5.0, "type": "float"},
        {"key": "emotional_require_above_sma200", "label": "Above SMA200", "default": False, "type": "bool"},
        {"key": "emotional_require_buy_rating", "label": "Require Buy rating", "default": False, "type": "bool"},
        {"key": "min_price", "label": "Min Price $", "min": 1, "max": 50, "default": 5, "type": "float"},
        {"key": "max_price", "label": "Max Price $", "min": 100, "max": 1000, "default": 500, "type": "float"},
    ],
    "premarket": [
        {"key": "premarket_min_score", "label": "Min Score", "min": 50, "max": 95, "default": 70, "type": "int"},
        {"key": "premarket_min_volume", "label": "Min PM Vol (K)", "min": 50, "max": 500, "default": 100, "type": "int_vol_k"},
        {"key": "premarket_min_relative_volume", "label": "Min Rel Vol", "min": 1.0, "max": 5.0, "default": 2.0, "type": "float"},
        {"key": "premarket_min_gap_percent", "label": "Min Gap %", "min": 0, "max": 10, "default": 2.0, "type": "float"},
        {"key": "premarket_max_gap_percent", "label": "Max Gap %", "min": 5, "max": 30, "default": 15.0, "type": "float"},
        {"key": "premarket_min_dollar_volume", "label": "Min $ Vol (K)", "min": 100, "max": 5000, "default": 500, "type": "int_vol_k"},
        {"key": "premarket_min_vol_float_ratio", "label": "Vol/Float", "min": 0, "max": 0.1, "default": 0.01, "type": "float"},
        {"key": "premarket_track_sector_heat", "label": "Track sector heat", "default": True, "type": "bool"},
    ],
    "watchlist": [
        {"key": "watchlist_filter", "label": "Filter", "type": "choice", "default": "down_pct", "options": ["down_pct", "all"]},
        {"key": "watchlist_pct_down_from_open", "label": "Min % down (range 1–25%)", "min": 1, "max": 25, "default": 5, "type": "float"},
    ],
    # Legacy scanner params kept for backward compat with user_config.json
    # velocity_leveraged, insider, velocity_premarket removed from UI in v7.7
}


def export_scan_config_full(config, dest_path, include_scan_types=True):
    """Export config and optionally scan types to one JSON file."""
    data = {"config": config}
    if include_scan_types:
        data["scan_types"] = load_scan_types()
    with open(dest_path, "w") as f:
        json.dump(data, f, indent=2)


def import_scan_config_full(path):
    """
    Import from a JSON file with 'config' and optionally 'scan_types'.
    Returns (config_updates dict, scan_types_list or None).
    """
    with open(path, "r") as f:
        data = json.load(f)
    config_updates = data.get("config", data) if isinstance(data, dict) else {}
    if isinstance(config_updates, list):
        config_updates = {}
    scan_types_list = data.get("scan_types") if isinstance(data, dict) else None
    return (config_updates, scan_types_list)


def load_scan_presets():
    """Load named presets from scan_presets.json. Returns dict: preset_name -> config dict."""
    if not os.path.exists(SCAN_PRESETS_FILE):
        return {}
    try:
        with open(SCAN_PRESETS_FILE, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_scan_preset(name, payload):
    """Save a named preset. payload can be a config dict or {config, scan_type, scan_index}."""
    name = (name or "").strip()
    if not name:
        return False
    presets = load_scan_presets()
    presets[name] = dict(payload) if isinstance(payload, dict) else {"config": payload}
    try:
        with open(SCAN_PRESETS_FILE, "w") as f:
            json.dump(presets, f, indent=2)
        return True
    except Exception:
        return False


def delete_scan_preset(name):
    """Remove a named preset."""
    name = (name or "").strip()
    if not name:
        return False
    presets = load_scan_presets()
    if name not in presets:
        return False
    del presets[name]
    try:
        with open(SCAN_PRESETS_FILE, "w") as f:
            json.dump(presets, f, indent=2)
        return True
    except Exception:
        return False


def load_config():
    """Load user configuration"""
    defaults = {
        # Legacy Dip Scan Parameters (used by enhanced_dip_scanner standalone GUI)
        # Active emotional dip params are emotional_* keys below
        "dip_min_percent": 1.0,
        "dip_max_percent": 5.0,
        "dip_min_volume_ratio": 1.5,
        "swing_min_score": 60,
        "dip_require_news_check": True,
        "dip_require_analyst_check": True,
        
        # Risk Settings
        "risk_per_trade_percent": 2.0,
        "max_position_dollars": 5000,
        "max_daily_loss_dollars": 1000,
        "max_concurrent_positions": 5,
        
        # Account
        "account_size": 20000,
        
        # Trend Scan Parameters
        "trend_min_score": 70,
        "trend_min_quarter_perf": 10,
        "trend_require_ma_stack": True,
        
        # Filters
        "min_price": 5.0,
        "max_price": 500.0,
        "min_avg_volume": 500000,
        
        # Emotional Dip Scanner (runs ~3:30 PM, buy by 4 PM)
        "emotional_min_score": 60,
        "emotional_dip_min_percent": 1.0,
        "emotional_dip_max_percent": 5.0,
        "emotional_min_volume_ratio": 1.2,
        "emotional_require_above_sma200": False,
        "emotional_min_upside_to_target": 5.0,
        "emotional_require_buy_rating": False,
        
        # Pre-Market Volume Scanner (7:00 AM - 9:25 AM)
        "premarket_min_score": 70,
        "premarket_min_volume": 100000,
        "premarket_min_relative_volume": 2.0,
        "premarket_min_gap_percent": 2.0,
        "premarket_max_gap_percent": 15.0,
        "premarket_min_dollar_volume": 500000,
        "premarket_max_spread_percent": 1.0,
        "premarket_min_vol_float_ratio": 0.01,
        "premarket_track_sector_heat": True,
        
        # Watchlist scanner (today's Change % down 1-25% — big-name dips)
        "watchlist_pct_down_from_open": 5.0,
        
        # Velocity Barbell scanner: min sector %, theme = auto | barbell | single_shot
        "velocity_min_sector_pct": 0.0,
        "velocity_barbell_theme": "auto",
        
        # Scan-complete alarm (system sound: beep | asterisk | exclamation)
        "play_alarm_on_complete": True,
        "alarm_sound_choice": "beep",

        # API keys – all blank by default; never commit user_config.json (see .gitignore)
        "finviz_api_key": "",
        # OpenRouter API (for AI analysis; one key for all models)
        "openrouter_api_key": "",
        "openrouter_model": "google/gemini-3-pro-preview",  # or tngtech/deepseek-r1t2-chimera:free (free)
        "use_vision_charts": False,  # Phase 6: attach chart images to OpenRouter (multimodal models only)
        # Alpha Vantage (optional news sentiment; NEWS_SENTIMENT endpoint)
        "alpha_vantage_api_key": "",
        # Alpaca (trading API – paper or live; used by MCP / integrations)
        "alpaca_api_key": "",
        "alpaca_secret_key": "",
        # Market Intelligence (Google News RSS + Finviz news + sector performance + market snapshot)
        "use_market_intel": True,
        # SEC EDGAR insider context (10b5-1 plan vs discretionary)
        "use_sec_insider_context": False,
        # RAG book knowledge (ChromaDB; folder of .txt trading books)
        "rag_books_folder": "",
        "rag_enabled": False,

        # Report: include programmatic TA (yfinance + pandas-ta: SMAs, RSI, MACD, BB, ATR, Fib) per ticker
        "include_ta_in_report": True,
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved = json.load(f)
                defaults.update(saved)
                # One-time migration: Gemini API -> OpenRouter
                if saved.get("gemini_api_key") and not saved.get("openrouter_api_key"):
                    defaults["openrouter_api_key"] = saved.get("gemini_api_key", "")
                gm = saved.get("gemini_model")
                if gm and not saved.get("openrouter_model"):
                    defaults["openrouter_model"] = "google/gemini-3-pro-preview" if gm == "gemini-3-pro-preview" else "tngtech/deepseek-r1t2-chimera:free"
                # v7.2 migration: Claude removed — switch to Gemini
                if "claude" in (defaults.get("openrouter_model") or "").lower():
                    defaults["openrouter_model"] = "google/gemini-3-pro-preview"
                # v7.4 migration: Loosen emotional dip defaults (was too strict, 0 results)
                if saved.get("emotional_require_above_sma200") is True and saved.get("emotional_min_volume_ratio", 0) >= 1.8:
                    defaults["emotional_require_above_sma200"] = False
                    defaults["emotional_require_buy_rating"] = False
                    defaults["emotional_min_volume_ratio"] = 1.2
                    defaults["emotional_min_upside_to_target"] = 5.0
                    defaults["emotional_dip_min_percent"] = 1.0
                    defaults["emotional_dip_max_percent"] = 5.0
        except Exception:
            pass

    return defaults


def save_config(config):
    """Save user configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def load_scan_types():
    """
    Load scan-type definitions from JSON.
    
    Structure:
    [
      {"id": "velocity_trend_growth", "label": "Velocity Trend Growth", "scanner": "velocity_trend_growth"},
      {"id": "swing_dips", "label": "Swing - Dips", "scanner": "swing"}
    ]
    
    Users can edit/replace this file to configure and share scan presets.
    """
    # If custom file exists, try to load it
    if os.path.exists(SCAN_TYPES_FILE):
        try:
            with open(SCAN_TYPES_FILE, "r") as f:
                data = json.load(f)
                # Basic validation: must be a list of dicts with required keys
                valid = []
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    if not all(k in item for k in ("id", "label", "scanner")):
                        continue
                    valid.append(
                        {
                            "id": str(item["id"]),
                            "label": str(item["label"]),
                            "scanner": str(item["scanner"]),
                        }
                    )
                if valid:
                    return valid
        except Exception:
            # Fall back to defaults if anything goes wrong
            pass
    
    # Save defaults so users have a JSON file they can edit/share
    try:
        with open(SCAN_TYPES_FILE, "w") as f:
            json.dump(DEFAULT_SCAN_TYPES, f, indent=2)
    except Exception:
        pass
    
    return DEFAULT_SCAN_TYPES.copy()


class ScanSettingsWindow:
    """GUI for configuring scan parameters"""
    
    def __init__(self, parent, callback=None):
        self.callback = callback
        self.config = load_config()
        
        self.win = tk.Toplevel(parent)
        self.win.title("Scan Settings")
        self.win.geometry("500x600")
        self.win.resizable(False, False)
        self.win.grab_set()
        
        self.build_ui()
    
    def build_ui(self):
        """Build settings UI"""
        # Notebook for tabs
        notebook = ttk.Notebook(self.win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === TAB 1: Dip Scan Settings ===
        dip_frame = tk.Frame(notebook, padx=15, pady=15)
        notebook.add(dip_frame, text="Dip Scan")
        
        tk.Label(dip_frame, text="Dip Scan Parameters", 
                font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(dip_frame, text="Configure how dips are detected",
                font=("Arial", 9), fg="gray").pack(anchor="w", pady=(0,15))
        
        # Min/Max dip percent
        row1 = tk.Frame(dip_frame)
        row1.pack(fill="x", pady=5)
        tk.Label(row1, text="Min Dip %:", width=15, anchor="w").pack(side="left")
        self.dip_min = tk.Entry(row1, width=10)
        self.dip_min.pack(side="left")
        self.dip_min.insert(0, str(self.config.get("dip_min_percent", 1.0)))
        tk.Label(row1, text="(stocks must be down at least this much)").pack(side="left", padx=10)

        row2 = tk.Frame(dip_frame)
        row2.pack(fill="x", pady=5)
        tk.Label(row2, text="Max Dip %:", width=15, anchor="w").pack(side="left")
        self.dip_max = tk.Entry(row2, width=10)
        self.dip_max.pack(side="left")
        self.dip_max.insert(0, str(self.config.get("dip_max_percent", 5.0)))
        tk.Label(row2, text="(avoid stocks down more - could be fundamental)").pack(side="left", padx=10)
        
        # Volume ratio
        row3 = tk.Frame(dip_frame)
        row3.pack(fill="x", pady=5)
        tk.Label(row3, text="Min Vol Ratio:", width=15, anchor="w").pack(side="left")
        self.vol_ratio = tk.Entry(row3, width=10)
        self.vol_ratio.pack(side="left")
        self.vol_ratio.insert(0, str(self.config.get("dip_min_volume_ratio", 1.5)))
        tk.Label(row3, text="x (relative to average volume)").pack(side="left", padx=10)
        
        # News and analyst ratings are always checked for all scans (no option to disable).
        tk.Label(dip_frame, text="").pack()  # spacer
        tk.Label(dip_frame, text="All scans include news and analyst ratings (Finviz).", font=("Arial", 9), fg="gray").pack(anchor="w")
        
        # === TAB 2: Risk Settings ===
        risk_frame = tk.Frame(notebook, padx=15, pady=15)
        notebook.add(risk_frame, text="Risk & Position")
        
        tk.Label(risk_frame, text="Risk Management", 
                font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(risk_frame, text="Control your position sizing and risk",
                font=("Arial", 9), fg="gray").pack(anchor="w", pady=(0,15))

        # Account size
        row_acc = tk.Frame(risk_frame)
        row_acc.pack(fill="x", pady=5)
        tk.Label(row_acc, text="Account Size $:", width=18, anchor="w").pack(side="left")
        self.account_size = tk.Entry(row_acc, width=12)
        self.account_size.pack(side="left")
        self.account_size.insert(0, str(self.config.get("account_size", 20000)))
        
        # Risk per trade
        row_risk = tk.Frame(risk_frame)
        row_risk.pack(fill="x", pady=5)
        tk.Label(row_risk, text="Risk per Trade %:", width=18, anchor="w").pack(side="left")
        self.risk_pct = tk.Entry(row_risk, width=12)
        self.risk_pct.pack(side="left")
        self.risk_pct.insert(0, str(self.config.get("risk_per_trade_percent", 2.0)))
        
        # Max position
        row_pos = tk.Frame(risk_frame)
        row_pos.pack(fill="x", pady=5)
        tk.Label(row_pos, text="Max Position $:", width=18, anchor="w").pack(side="left")
        self.max_pos = tk.Entry(row_pos, width=12)
        self.max_pos.pack(side="left")
        self.max_pos.insert(0, str(self.config.get("max_position_dollars", 5000)))
        
        # Max daily loss
        row_loss = tk.Frame(risk_frame)
        row_loss.pack(fill="x", pady=5)
        tk.Label(row_loss, text="Max Daily Loss $:", width=18, anchor="w").pack(side="left")
        self.max_loss = tk.Entry(row_loss, width=12)
        self.max_loss.pack(side="left")
        self.max_loss.insert(0, str(self.config.get("max_daily_loss_dollars", 1000)))
        
        # Max positions
        row_conc = tk.Frame(risk_frame)
        row_conc.pack(fill="x", pady=5)
        tk.Label(row_conc, text="Max Positions:", width=18, anchor="w").pack(side="left")
        self.max_positions = tk.Entry(row_conc, width=12)
        self.max_positions.pack(side="left")
        self.max_positions.insert(0, str(self.config.get("max_concurrent_positions", 5)))

        # === TAB 3: Filters ===
        filter_frame = tk.Frame(notebook, padx=15, pady=15)
        notebook.add(filter_frame, text="Stock Filters")
        
        tk.Label(filter_frame, text="Stock Filters", 
                font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(filter_frame, text="Filter which stocks are included in scans",
                font=("Arial", 9), fg="gray").pack(anchor="w", pady=(0,15))
        
        # Price range
        row_price = tk.Frame(filter_frame)
        row_price.pack(fill="x", pady=5)
        tk.Label(row_price, text="Price Range $:", width=15, anchor="w").pack(side="left")
        self.min_price = tk.Entry(row_price, width=8)
        self.min_price.pack(side="left")
        self.min_price.insert(0, str(self.config.get("min_price", 5.0)))
        tk.Label(row_price, text=" to ").pack(side="left")
        self.max_price = tk.Entry(row_price, width=8)
        self.max_price.pack(side="left")
        self.max_price.insert(0, str(self.config.get("max_price", 500.0)))
        
        # Min volume
        row_vol = tk.Frame(filter_frame)
        row_vol.pack(fill="x", pady=5)
        tk.Label(row_vol, text="Min Avg Volume:", width=15, anchor="w").pack(side="left")
        self.min_volume = tk.Entry(row_vol, width=12)
        self.min_volume.pack(side="left")
        self.min_volume.insert(0, str(self.config.get("min_avg_volume", 500000)))
        
        # === BUTTONS at bottom ===
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        btn_save = tk.Button(btn_frame, text="Save Settings", command=self.save_settings,
                            bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=12)
        btn_save.pack(side="left", padx=5)
        
        btn_reset = tk.Button(btn_frame, text="Reset Defaults", command=self.reset_defaults, width=12)
        btn_reset.pack(side="left", padx=5)
        
        btn_close = tk.Button(btn_frame, text="Cancel", command=self.win.destroy, width=10)
        btn_close.pack(side="right", padx=5)
    
    def save_settings(self):
        """Save all settings"""
        try:
            self.config.update({
                # Dip settings (news/analyst always on, not stored from UI)
                "dip_min_percent": float(self.dip_min.get()),
                "dip_max_percent": float(self.dip_max.get()),
                "dip_min_volume_ratio": float(self.vol_ratio.get()),
                
                # Risk settings
                "account_size": float(self.account_size.get()),
                "risk_per_trade_percent": float(self.risk_pct.get()),
                "max_position_dollars": float(self.max_pos.get()),
                "max_daily_loss_dollars": float(self.max_loss.get()),
                "max_concurrent_positions": int(self.max_positions.get()),
                
                # Filters
                "min_price": float(self.min_price.get()),
                "max_price": float(self.max_price.get()),
                "min_avg_volume": int(self.min_volume.get()),
            })
            
            save_config(self.config)
            messagebox.showinfo("Saved", "Settings saved successfully!")
            
            if self.callback:
                self.callback()
            
            self.win.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid value: {e}")
    
    def reset_defaults(self):
        """Reset to default values"""
        if messagebox.askyesno("Reset", "Reset all settings to defaults?"):
            os.remove(CONFIG_FILE) if os.path.exists(CONFIG_FILE) else None
            self.win.destroy()
            messagebox.showinfo("Reset", "Settings reset. Reopen to see defaults.")


class ScanTypeManagerWindow:
    """Simple UI for importing/exporting scan type presets (scan_types.json)."""
    
    def __init__(self, parent, on_change=None):
        self.on_change = on_change
        self.win = tk.Toplevel(parent)
        self.win.title("Scan Type Presets")
        self.win.geometry("420x320")
        self.win.resizable(False, False)
        self.win.grab_set()
        
        tk.Label(
            self.win,
            text="Scan Type Presets (scan_types.json)",
            font=("Arial", 12, "bold"),
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        tk.Label(
            self.win,
            text="These presets control the scan dropdown in the main window.\n"
                 "You can export them to share, or import from another setup.",
            font=("Arial", 9),
            fg="gray",
            justify="left",
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        # List of current scan types
        list_frame = tk.Frame(self.win)
        list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        self.listbox = tk.Listbox(list_frame, height=6)
        self.listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        self.refresh_list()
        
        # Buttons
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Button(
            btn_frame,
            text="Import...",
            command=self.import_scan_types,
            bg="#17a2b8",
            fg="white",
            font=("Arial", 9, "bold"),
            width=10,
            relief="flat",
        ).pack(side="left", padx=3)
        
        tk.Button(
            btn_frame,
            text="Export...",
            command=self.export_scan_types,
            bg="#6c757d",
            fg="white",
            font=("Arial", 9, "bold"),
            width=10,
            relief="flat",
        ).pack(side="left", padx=3)
        
        tk.Button(
            btn_frame,
            text="Close",
            command=self.win.destroy,
            width=8,
        ).pack(side="right", padx=3)
    
    def refresh_list(self):
        """Reload listbox contents from current scan_types.json."""
        self.listbox.delete(0, tk.END)
        types_ = load_scan_types()
        for item in types_:
            label = item.get("label", "")
            scanner = item.get("scanner", "")
            self.listbox.insert(tk.END, f"{label}   [{scanner}]")
    
    def import_scan_types(self):
        """Import scan_types.json from another location."""
        path = filedialog.askopenfilename(
            title="Import Scan Types",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            # Basic validation similar to load_scan_types
            if not isinstance(data, list):
                raise ValueError("Expected a list of scan type definitions.")
            
            valid = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                if not all(k in item for k in ("id", "label", "scanner")):
                    continue
                valid.append(
                    {
                        "id": str(item["id"]),
                        "label": str(item["label"]),
                        "scanner": str(item["scanner"]),
                    }
                )
            
            if not valid:
                raise ValueError("No valid scan types found in file.")
            
            with open(SCAN_TYPES_FILE, "w") as f:
                json.dump(valid, f, indent=2)
            
            messagebox.showinfo("Scan Types", "Scan types imported successfully.")
            self.refresh_list()
            
            if self.on_change:
                self.on_change()
        except Exception as e:
            messagebox.showerror("Import Failed", str(e))
    
    def export_scan_types(self):
        """Export current scan_types.json to another location."""
        if not os.path.exists(SCAN_TYPES_FILE):
            messagebox.showerror("Export Failed", "No scan_types.json file found to export.")
            return
        
        dest = filedialog.asksaveasfilename(
            title="Export Scan Types",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not dest:
            return
        
        try:
            shutil.copyfile(SCAN_TYPES_FILE, dest)
            messagebox.showinfo("Scan Types", "Scan types exported successfully.")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))


def manage_scan_types(parent, on_change=None):
    """Entry point for opening the Scan Type Manager window."""
    ScanTypeManagerWindow(parent, on_change=on_change)
