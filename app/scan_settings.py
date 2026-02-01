# ============================================================
# ClearBlueSky - Scan Parameters & User Settings
# Made with Claude AI
# ============================================================

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

# Get the directory where this script is located (portable support)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "user_config.json")
PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio.json")


def load_config():
    """Load user configuration"""
    defaults = {
        # Dip Scan Parameters
        "dip_min_percent": 1.0,
        "dip_max_percent": 5.0,
        "dip_min_volume_ratio": 1.5,
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
        "trend_min_quarter_perf": 10,
        "trend_require_ma_stack": True,
        
        # Filters
        "min_price": 5.0,
        "max_price": 500.0,
        "min_avg_volume": 500000,
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved = json.load(f)
                defaults.update(saved)
        except:
            pass
    
    return defaults


def save_config(config):
    """Save user configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


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
        
        # Checkboxes for filters
        tk.Label(dip_frame, text="").pack()  # spacer
        tk.Label(dip_frame, text="Quality Filters:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.news_check_var = tk.BooleanVar(value=self.config.get("dip_require_news_check", True))
        tk.Checkbutton(dip_frame, text="Check news for emotional vs fundamental dip", 
                      variable=self.news_check_var).pack(anchor="w")
        
        self.analyst_check_var = tk.BooleanVar(value=self.config.get("dip_require_analyst_check", True))
        tk.Checkbutton(dip_frame, text="Check analyst ratings & price targets", 
                      variable=self.analyst_check_var).pack(anchor="w")
        
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
        
        # Trend settings
        tk.Label(filter_frame, text="").pack()
        tk.Label(filter_frame, text="Trend Scan Settings:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        row_qtr = tk.Frame(filter_frame)
        row_qtr.pack(fill="x", pady=5)
        tk.Label(row_qtr, text="Min Quarter Perf %:", width=18, anchor="w").pack(side="left")
        self.trend_qtr = tk.Entry(row_qtr, width=8)
        self.trend_qtr.pack(side="left")
        self.trend_qtr.insert(0, str(self.config.get("trend_min_quarter_perf", 10)))
        
        self.ma_stack_var = tk.BooleanVar(value=self.config.get("trend_require_ma_stack", True))
        tk.Checkbutton(filter_frame, text="Require MA stacking (Price > SMA20 > SMA50 > SMA200)", 
                      variable=self.ma_stack_var).pack(anchor="w")

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
                # Dip settings
                "dip_min_percent": float(self.dip_min.get()),
                "dip_max_percent": float(self.dip_max.get()),
                "dip_min_volume_ratio": float(self.vol_ratio.get()),
                "dip_require_news_check": self.news_check_var.get(),
                "dip_require_analyst_check": self.analyst_check_var.get(),
                
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
                "trend_min_quarter_perf": float(self.trend_qtr.get()),
                "trend_require_ma_stack": self.ma_stack_var.get(),
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
