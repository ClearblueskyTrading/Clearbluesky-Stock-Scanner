# ============================================================
# ClearBlueSky Stock Scanner v5.1
# ============================================================

import tkinter as tk
VERSION = "5.1"
from tkinter import ttk, messagebox
import os
import json
import webbrowser
import traceback
import time
from datetime import datetime

BASE_DIR = r"C:\TradingBot"
CONFIG_FILE = os.path.join(BASE_DIR, "user_config.json")
LOG_FILE = os.path.join(BASE_DIR, "error_log.txt")

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
        self.root.geometry("380x850")
        self.root.resizable(False, False)
        self.root.configure(bg="#f8f9fa")
        
        self.config = self.load_config()
        self.build_ui()
        log("UI ready")
    
    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def build_ui(self):
        # === HEADER ===
        header = tk.Frame(self.root, bg=BG_DARK, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="☁️ ClearBlueSky", font=("Arial", 16, "bold"), 
                fg="white", bg=BG_DARK).pack(pady=(10,0))
        tk.Label(header, text=f"Stock Scanner & AI Research Tool v{VERSION}", font=("Arial", 10), 
                fg="#cccccc", bg=BG_DARK).pack()
        tk.Label(header, text="made with Claude", font=("Arial", 8, "italic"), 
                fg="#888888", bg=BG_DARK).pack()
        
        # === MAIN CONTENT ===
        main = tk.Frame(self.root, bg="#f8f9fa", padx=20, pady=15)
        main.pack(fill="both", expand=True)
        
        # --- AI SELECTION ---
        ai_frame = tk.Frame(main, bg="#f8f9fa")
        ai_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(ai_frame, text="🤖 AI Research Tool", font=("Arial", 10, "bold"), 
                bg="#f8f9fa", fg="#333").pack(anchor="w")
        
        ai_row = tk.Frame(ai_frame, bg="#f8f9fa")
        ai_row.pack(fill="x", pady=(5,0))
        
        self.ai_choice = tk.StringVar(value="Claude (Best)")
        ai_combo = ttk.Combobox(ai_row, textvariable=self.ai_choice, 
                                values=["Claude (Best)", "Gemini", "ChatGPT", "Qwen3 (Free)", "Other"],
                                state="readonly", width=15, font=("Arial", 10))
        ai_combo.pack(side="left")
        
        tk.Button(ai_row, text="⚙", command=self.ai_config, bg="#e9ecef", fg="#333",
                 font=("Arial", 10), width=3, relief="flat", cursor="hand2").pack(side="left", padx=(5,0))
        
        # Qwen note
        self.qwen_note = tk.Label(ai_frame, text="💡 Qwen3 - FREE super large AI LLM with vision!", 
                                  font=("Arial", 8), bg="#f8f9fa", fg="#6f42c1")
        
        def on_ai_change(event=None):
            if "Qwen" in self.ai_choice.get():
                self.qwen_note.pack(anchor="w", pady=(3,0))
            else:
                self.qwen_note.pack_forget()
        
        ai_combo.bind("<<ComboboxSelected>>", on_ai_change)
        
        # --- SCANNERS ---
        scan_label = tk.Label(main, text="📊 Stock Scanners", font=("Arial", 10, "bold"), 
                             bg="#f8f9fa", fg="#333")
        scan_label.pack(anchor="w", pady=(10, 8))
        
        # TREND SCANNER
        trend_frame = tk.Frame(main, bg="white", relief="solid", bd=1)
        trend_frame.pack(fill="x", pady=(0, 10), ipady=10, ipadx=10)
        
        trend_top = tk.Frame(trend_frame, bg="white")
        trend_top.pack(fill="x", padx=10, pady=(10,3))
        
        tk.Label(trend_top, text="Trend Scanner", font=("Arial", 11, "bold"), 
                bg="white", fg="#333").pack(side="left")
        tk.Label(trend_top, text="~30 sec", font=("Arial", 9), 
                bg="white", fg="#888").pack(side="right")
        
        tk.Label(trend_frame, text="Long-term plays (90+ days) - ride big winners", 
                font=("Arial", 9, "italic"), bg="white", fg="#666").pack(anchor="w", padx=10)
        
        # Index selection row for Trend
        trend_idx_row = tk.Frame(trend_frame, bg="white")
        trend_idx_row.pack(fill="x", padx=10, pady=(5,0))
        tk.Label(trend_idx_row, text="Index:", font=("Arial", 9), bg="white", fg="#555").pack(side="left")
        self.trend_index = tk.StringVar(value="S&P 500")
        ttk.Combobox(trend_idx_row, textvariable=self.trend_index,
                     values=["S&P 500", "Russell 2000"],
                     state="readonly", width=12, font=("Arial", 9)).pack(side="left", padx=(5,0))
        
        trend_btn_row = tk.Frame(trend_frame, bg="white")
        trend_btn_row.pack(fill="x", padx=10, pady=(8,5))
        
        self.trend_btn = tk.Button(trend_btn_row, text="▶ Run Scan", command=self.run_trend,
                                   bg=GREEN, fg="white", font=("Arial", 10, "bold"),
                                   width=12, height=1, cursor="hand2", relief="flat")
        self.trend_btn.pack(side="left")
        
        self.trend_stop_btn = tk.Button(trend_btn_row, text="■ Stop", command=self.stop_trend_scan,
                                        bg="#dc3545", fg="white", font=("Arial", 9),
                                        width=5, cursor="hand2", relief="flat", state="disabled")
        self.trend_stop_btn.pack(side="left", padx=(5,0))
        
        tk.Button(trend_btn_row, text="⚙", command=self.trend_settings,
                  bg="#e9ecef", fg="#333", font=("Arial", 10), width=3,
                  cursor="hand2", relief="flat").pack(side="left", padx=(5,0))
        
        self.trend_printer = AnimatedMoneyPrinter(trend_btn_row, bg="white")
        self.trend_printer.pack(side="right")
        
        self.trend_progress = ProgressBar(trend_frame, width=300, height=18, color=GREEN)
        self.trend_progress.pack(padx=10, pady=(0,5))
        
        self.trend_status = tk.Label(trend_frame, text="", font=("Arial", 8), 
                                     bg="white", fg="#666")
        self.trend_status.pack(anchor="w", padx=10, pady=(0,5))
        
        # SWING SCANNER
        swing_frame = tk.Frame(main, bg="white", relief="solid", bd=1)
        swing_frame.pack(fill="x", pady=(0, 10), ipady=10, ipadx=10)
        
        swing_top = tk.Frame(swing_frame, bg="white")
        swing_top.pack(fill="x", padx=10, pady=(10,3))
        
        tk.Label(swing_top, text="Swing Scanner", font=("Arial", 11, "bold"), 
                bg="white", fg="#333").pack(side="left")
        tk.Label(swing_top, text="S&P ~2min | Russell ~5min", font=("Arial", 8), 
                bg="white", fg="#888").pack(side="right")
        
        tk.Label(swing_frame, text="Short-term plays (1-5 days) - buy dips, sell rips", 
                font=("Arial", 9, "italic"), bg="white", fg="#666").pack(anchor="w", padx=10)
        
        # Index selection row
        idx_row = tk.Frame(swing_frame, bg="white")
        idx_row.pack(fill="x", padx=10, pady=(5,0))
        tk.Label(idx_row, text="Index:", font=("Arial", 9), bg="white", fg="#555").pack(side="left")
        self.swing_index = tk.StringVar(value="S&P 500")
        idx_combo = ttk.Combobox(idx_row, textvariable=self.swing_index,
                                 values=["S&P 500", "Russell 2000"],
                                 state="readonly", width=12, font=("Arial", 9))
        idx_combo.pack(side="left", padx=(5,0))
        
        swing_btn_row = tk.Frame(swing_frame, bg="white")
        swing_btn_row.pack(fill="x", padx=10, pady=(8,5))
        
        self.swing_btn = tk.Button(swing_btn_row, text="▶ Run Scan", command=self.run_dips,
                                   bg=BLUE, fg="white", font=("Arial", 10, "bold"),
                                   width=12, height=1, cursor="hand2", relief="flat")
        self.swing_btn.pack(side="left")
        
        self.swing_stop_btn = tk.Button(swing_btn_row, text="■ Stop", command=self.stop_swing_scan,
                                        bg="#dc3545", fg="white", font=("Arial", 9),
                                        width=5, cursor="hand2", relief="flat", state="disabled")
        self.swing_stop_btn.pack(side="left", padx=(5,0))
        
        tk.Button(swing_btn_row, text="⚙", command=self.dip_settings,
                  bg="#e9ecef", fg="#333", font=("Arial", 10), width=3,
                  cursor="hand2", relief="flat").pack(side="left", padx=(5,0))
        
        self.swing_printer = AnimatedMoneyPrinter(swing_btn_row, bg="white")
        self.swing_printer.pack(side="right")
        
        self.swing_progress = ProgressBar(swing_frame, width=300, height=18, color=BLUE)
        self.swing_progress.pack(padx=10, pady=(0,5))
        
        self.swing_status = tk.Label(swing_frame, text="", font=("Arial", 8), 
                                     bg="white", fg="#666")
        self.swing_status.pack(anchor="w", padx=10, pady=(0,5))
        
        # --- QUICK TICKER ---
        ticker_label = tk.Label(main, text="🔍 Quick Lookup", font=("Arial", 10, "bold"), 
                               bg="#f8f9fa", fg="#333")
        ticker_label.pack(anchor="w", pady=(10, 8))
        
        ticker_frame = tk.Frame(main, bg="white", relief="solid", bd=1)
        ticker_frame.pack(fill="x", ipady=10)
        
        ticker_row = tk.Frame(ticker_frame, bg="white")
        ticker_row.pack(pady=10)
        
        tk.Label(ticker_row, text="Symbol:", font=("Arial", 10), 
                bg="white", fg="#333").pack(side="left", padx=(10,5))
        
        self.symbol_entry = tk.Entry(ticker_row, width=8, font=("Arial", 12), relief="solid", bd=1)
        self.symbol_entry.pack(side="left")
        
        tk.Button(ticker_row, text="📄 Report", command=self.generate_report,
                  bg=ORANGE, fg="white", font=("Arial", 10, "bold"), width=8,
                  cursor="hand2", relief="flat").pack(side="left", padx=(10,0))
        
        # --- BOTTOM BUTTONS ---
        btn_frame = tk.Frame(main, bg="#f8f9fa")
        btn_frame.pack(fill="x", pady=(15, 5))
        
        # Row 1: Quick links
        row1 = tk.Frame(btn_frame, bg="#f8f9fa")
        row1.pack(fill="x", pady=(0,5))
        
        for text, cmd in [("🌐 Finviz", lambda: webbrowser.open("https://finviz.com")),
                          ("💼 Broker", self.open_broker),
                          ("📁 Reports", self.open_reports),
                          ("📋 Logs", self.view_logs)]:
            tk.Button(row1, text=text, command=cmd, bg="#e9ecef", fg="#333",
                     font=("Arial", 9), width=9, relief="flat", cursor="hand2").pack(side="left", padx=2)
        
        # Row 2: Settings and Exit
        row2 = tk.Frame(btn_frame, bg="#f8f9fa")
        row2.pack(fill="x")
        
        tk.Button(row2, text="⚙️ Settings", command=self.api_settings, bg="#6c757d", fg="white",
                 font=("Arial", 9), width=10, relief="flat", cursor="hand2").pack(side="left", padx=2)
        
        tk.Button(row2, text="❓ Help", command=self.show_help, bg="#17a2b8", fg="white",
                 font=("Arial", 9), width=6, relief="flat", cursor="hand2").pack(side="left", padx=2)
        
        tk.Button(row2, text="❤️ Donate to Direct Relief", command=lambda: webbrowser.open("https://www.directrelief.org/"),
                 bg="#E91E63", fg="white", font=("Arial", 9), width=20, relief="flat", cursor="hand2").pack(side="left", padx=2)
        
        tk.Button(row2, text="❌ Exit", command=self.root.quit, bg="#dc3545", fg="white",
                 font=("Arial", 9), width=6, relief="flat", cursor="hand2").pack(side="left", padx=2)
        
        # Status
        self.status = tk.Label(main, text="Ready", font=("Arial", 9), bg="#f8f9fa", fg="#666")
        self.status.pack(pady=(10,0))
        
        # Scan state
        self.trend_cancelled = False
        self.swing_cancelled = False
        self.trend_start_time = 0
        self.swing_start_time = 0
    
    # === SCANNER METHODS ===
    
    def stop_trend_scan(self):
        self.trend_cancelled = True
        self.trend_status.config(text="Stopping...")
    
    def stop_swing_scan(self):
        self.swing_cancelled = True
        self.swing_status.config(text="Stopping...")
    
    def run_trend(self):
        log("=== TREND SCAN ===")
        self.trend_cancelled = False
        self.trend_start_time = time.time()
        self.trend_progress.set(5, "Starting...")
        self.trend_status.config(text="Connecting...")
        self.trend_printer.start()
        self.trend_btn.config(state="disabled")
        self.trend_stop_btn.config(state="normal")
        self.root.update()
        
        # Get selected index
        index = "sp500" if "S&P" in self.trend_index.get() else "russell2000"
        
        try:
            from trend_scan_v2 import trend_scan
            
            def progress(msg):
                if self.trend_cancelled:
                    return
                log(f"Trend: {msg}")
                elapsed = int(time.time() - self.trend_start_time)
                time_str = f"{elapsed}s"
                
                if "overview" in msg.lower():
                    self.trend_progress.set(25, f"25% ({time_str})")
                    self.trend_status.config(text="Getting stock data from Finviz...")
                elif "performance" in msg.lower():
                    self.trend_progress.set(50, f"50% ({time_str})")
                    self.trend_status.config(text="Getting performance metrics...")
                elif "merging" in msg.lower():
                    self.trend_progress.set(65, f"65% ({time_str})")
                    self.trend_status.config(text="Combining data...")
                elif "scoring" in msg.lower():
                    self.trend_progress.set(80, f"80% ({time_str})")
                    self.trend_status.config(text="Ranking candidates...")
                elif "done" in msg.lower():
                    self.trend_progress.set(90, f"90% ({time_str})")
                    self.trend_status.config(text="Building report...")
                self.root.update()
            
            df = trend_scan(progress_callback=progress, index=index)
            
            if self.trend_cancelled:
                self.scan_complete(self.trend_progress, self.trend_status,
                                   self.trend_printer, self.trend_btn, "Cancelled", self.trend_stop_btn)
                return
            
            if df is not None and len(df) > 0:
                elapsed = int(time.time() - self.trend_start_time)
                self.generate_report_from_results(df.to_dict('records'), "Trend", 
                    self.trend_progress, self.trend_status, self.trend_printer, self.trend_btn,
                    self.trend_stop_btn, elapsed)
            else:
                self.scan_complete(self.trend_progress, self.trend_status, 
                                   self.trend_printer, self.trend_btn, "No results", self.trend_stop_btn)
        except Exception as e:
            log_error(e, "Trend failed")
            self.scan_complete(self.trend_progress, self.trend_status,
                               self.trend_printer, self.trend_btn, "Error!", self.trend_stop_btn)
            messagebox.showerror("Error", str(e))
    
    def run_dips(self):
        log("=== SWING SCAN ===")
        self.swing_cancelled = False
        self.swing_start_time = time.time()
        self.swing_progress.set(5, "Starting...")
        self.swing_status.config(text="Connecting...")
        self.swing_printer.start()
        self.swing_btn.config(state="disabled")
        self.swing_stop_btn.config(state="normal")
        self.root.update()
        
        # Get selected index
        index = "sp500" if "S&P" in self.swing_index.get() else "russell2000"
        
        try:
            from enhanced_dip_scanner import run_enhanced_dip_scan
            
            def progress(msg):
                if self.swing_cancelled:
                    return
                log(f"Swing: {msg}")
                elapsed = int(time.time() - self.swing_start_time)
                time_str = f"{elapsed}s"
                self.swing_status.config(text=msg[:50])
                
                if "analyzing" in msg.lower():
                    try:
                        if "(" in msg and "/" in msg:
                            parts = msg.split("(")[1].split(")")[0].split("/")
                            cur, tot = int(parts[0]), int(parts[1])
                            pct = 10 + int((cur / tot) * 75)
                            self.swing_progress.set(pct, f"{pct}% ({time_str})")
                    except:
                        pass
                elif "complete" in msg.lower():
                    self.swing_progress.set(90, f"90% ({time_str})")
                self.root.update()
            
            results = run_enhanced_dip_scan(progress, index=index)
            
            if self.swing_cancelled:
                self.scan_complete(self.swing_progress, self.swing_status,
                                   self.swing_printer, self.swing_btn, "Cancelled", self.swing_stop_btn)
                return
            
            if results and len(results) > 0:
                elapsed = int(time.time() - self.swing_start_time)
                self.generate_report_from_results(results, "Swing",
                    self.swing_progress, self.swing_status, self.swing_printer, self.swing_btn,
                    self.swing_stop_btn, elapsed)
            else:
                self.scan_complete(self.swing_progress, self.swing_status,
                                   self.swing_printer, self.swing_btn, "No dips today", self.swing_stop_btn)
        except Exception as e:
            log_error(e, "Swing failed")
            self.scan_complete(self.swing_progress, self.swing_status,
                               self.swing_printer, self.swing_btn, "Error!", self.swing_stop_btn)
            messagebox.showerror("Error", str(e))
    
    def generate_report_from_results(self, results, scan_type, progress, status, printer, btn, stop_btn=None, elapsed=0):
        """Generate HTML report"""
        try:
            from report_generator import HTMLReportGenerator
            
            min_score = int(self.config.get(f'{scan_type.lower()}_min_score', 65))
            gen = HTMLReportGenerator()
            
            def rpt_progress(msg):
                if "Processing" in msg:
                    try:
                        ticker = msg.split(":")[-1].strip()
                        progress.set(92, ticker)
                        status.config(text=f"Getting {ticker} data...")
                    except:
                        pass
                self.root.update()
            
            path = gen.generate_combined_report(results, scan_type, min_score, rpt_progress)
            
            if path:
                progress.set(100, f"Done! ({elapsed}s)")
                status.config(text="Opening report in browser...")
                webbrowser.open(f"file://{path}")
            else:
                status.config(text=f"No stocks above score {min_score}")
        except Exception as e:
            log_error(e, "Report failed")
            status.config(text="Report error")
        
        printer.stop()
        btn.config(state="normal")
        if stop_btn:
            stop_btn.config(state="disabled")
    
    def scan_complete(self, progress, status, printer, btn, msg, stop_btn=None):
        progress.set(0, msg)
        status.config(text="")
        printer.stop()
        btn.config(state="normal")
        if stop_btn:
            stop_btn.config(state="disabled")
    
    # === SINGLE TICKER ===
    
    def generate_report(self):
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol:
            return
        
        self.status.config(text=f"Loading {symbol}...")
        self.root.update()
        
        try:
            from report_generator import HTMLReportGenerator
            gen = HTMLReportGenerator()
            path = gen.generate_combined_report([{'ticker': symbol, 'score': 80}], "Analysis", 0)
            webbrowser.open(f"file://{path}")
            self.status.config(text="Report opened")
        except Exception as e:
            self.status.config(text="Error")
            messagebox.showerror("Error", str(e))
    
    def quick_analysis(self):
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol:
            return
        
        prompt = f"Analyze {symbol}: 1) Trend 2) Support/resistance 3) BUY/SELL/HOLD with entry & stop"
        self.root.clipboard_clear()
        self.root.clipboard_append(prompt)
        
        ai = self.ai_choice.get().split()[0]
        urls = {
            "Claude": "https://claude.ai/new", 
            "Gemini": "https://gemini.google.com/app", 
            "ChatGPT": "https://chat.openai.com",
            "Other": self.config.get('other_ai_url', 'https://claude.ai/new')
        }
        webbrowser.open(urls.get(ai, urls["Claude"]))
        self.status.config(text="Prompt copied - paste in AI")
    
    def ai_config(self):
        """Configure custom AI URL"""
        win = tk.Toplevel(self.root)
        win.title("AI Configuration")
        win.geometry("450x320")
        win.transient(self.root)
        win.grab_set()
        win.configure(bg="white")
        
        tk.Label(win, text="AI Tool Configuration", font=("Arial", 12, "bold"),
                bg="white", fg="#333").pack(pady=(15,10))
        
        f = tk.Frame(win, bg="white", padx=20)
        f.pack(fill="x")
        
        tk.Label(f, text="Custom AI URL (for 'Other' option):", font=("Arial", 9),
                bg="white", fg="#666").pack(anchor="w")
        tk.Label(f, text="e.g., RunPod endpoint, local LLM, or other AI", font=("Arial", 8),
                bg="white", fg="#999").pack(anchor="w")
        
        url_var = tk.StringVar(value=self.config.get('other_ai_url', 'https://'))
        tk.Entry(f, textvariable=url_var, width=50, font=("Arial", 10)).pack(anchor="w", pady=(5,15))
        
        def save():
            self.config['other_ai_url'] = url_var.get()
            with open(CONFIG_FILE, 'w') as file:
                json.dump(self.config, file, indent=2)
            win.destroy()
            self.status.config(text="AI config saved")
        
        tk.Button(win, text="Save", command=save, bg=GREEN, fg="white",
                 font=("Arial", 10, "bold"), width=10, relief="flat").pack(pady=10)
        
        # Learn How section
        sep = tk.Frame(win, bg="#ddd", height=1)
        sep.pack(fill="x", padx=20, pady=10)
        
        tk.Label(win, text="🚀 Want to run your OWN private AI?", font=("Arial", 10, "bold"),
                bg="white", fg="#6f42c1").pack()
        tk.Label(win, text="Build a multi-model trading AI system on RunPod", font=("Arial", 9),
                bg="white", fg="#666").pack()
        tk.Label(win, text="No limits • Private • ~$0.30/hour • Weekend project", font=("Arial", 8),
                bg="white", fg="#999").pack(pady=(2,8))
        
        def show_learn_guide():
            guide_win = tk.Toplevel(win)
            guide_win.title("Build Your Own AI - Copy This Prompt")
            guide_win.geometry("700x500")
            guide_win.configure(bg="white")
            
            tk.Label(guide_win, text="📋 Copy this prompt to Claude/ChatGPT", 
                    font=("Arial", 11, "bold"), bg="white", fg="#333").pack(pady=10)
            tk.Label(guide_win, text="It will teach you how to build your own private AI trading system",
                    font=("Arial", 9), bg="white", fg="#666").pack()
            
            text_frame = tk.Frame(guide_win, bg="white")
            text_frame.pack(fill="both", expand=True, padx=15, pady=10)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side="right", fill="y")
            
            text_box = tk.Text(text_frame, wrap="word", font=("Consolas", 9),
                              yscrollcommand=scrollbar.set)
            text_box.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=text_box.yview)
            
            # Load the guide
            guide_path = os.path.join(os.path.dirname(__file__), "RUNPOD_AI_GUIDE.txt")
            try:
                with open(guide_path, 'r') as gf:
                    guide_text = gf.read()
            except:
                guide_text = "Guide file not found. Please reinstall the app."
            
            text_box.insert("1.0", guide_text)
            text_box.config(state="normal")
            
            def copy_guide():
                guide_win.clipboard_clear()
                guide_win.clipboard_append(guide_text)
                copy_btn.config(text="✓ Copied!")
                guide_win.after(2000, lambda: copy_btn.config(text="📋 Copy All to Clipboard"))
            
            btn_frame = tk.Frame(guide_win, bg="white")
            btn_frame.pack(pady=10)
            
            copy_btn = tk.Button(btn_frame, text="📋 Copy All to Clipboard", command=copy_guide,
                                bg="#6f42c1", fg="white", font=("Arial", 10, "bold"),
                                relief="flat", padx=20, cursor="hand2")
            copy_btn.pack(side="left", padx=5)
            
            tk.Button(btn_frame, text="Open Claude", 
                     command=lambda: webbrowser.open("https://claude.ai/new"),
                     bg="#e9ecef", fg="#333", font=("Arial", 9),
                     relief="flat", padx=10, cursor="hand2").pack(side="left", padx=5)
        
        tk.Button(win, text="📚 Learn How to Build Your Own AI", command=show_learn_guide,
                 bg="#6f42c1", fg="white", font=("Arial", 10, "bold"),
                 relief="flat", padx=15, cursor="hand2").pack(pady=5)
    
    # === SETTINGS ===
    
    def trend_settings(self):
        """Trend scanner settings"""
        win = tk.Toplevel(self.root)
        win.title("Trend Scanner Settings")
        win.geometry("320x350")
        win.transient(self.root)
        win.grab_set()
        win.configure(bg="white")
        
        tk.Label(win, text="Trend Scanner Settings", font=("Arial", 12, "bold"),
                bg="white", fg="#333").pack(pady=(15,10))
        
        f = tk.Frame(win, bg="white", padx=25)
        f.pack(fill="x")
        
        # Min Score
        tk.Label(f, text="Min Score for Report:", font=("Arial", 9), bg="white").pack(anchor="w", pady=(5,0))
        score_var = tk.StringVar(value=self.config.get('trend_min_score', '70'))
        tk.Entry(f, textvariable=score_var, width=10).pack(anchor="w")
        
        # Min Quarter Performance
        tk.Label(f, text="Min Quarter Performance %:", font=("Arial", 9), bg="white").pack(anchor="w", pady=(10,0))
        qtr_var = tk.StringVar(value=self.config.get('trend_min_quarter_perf', '10'))
        tk.Entry(f, textvariable=qtr_var, width=10).pack(anchor="w")
        
        # Min Price
        tk.Label(f, text="Min Stock Price $:", font=("Arial", 9), bg="white").pack(anchor="w", pady=(10,0))
        minprice_var = tk.StringVar(value=self.config.get('min_price', '5'))
        tk.Entry(f, textvariable=minprice_var, width=10).pack(anchor="w")
        
        # Max Price
        tk.Label(f, text="Max Stock Price $:", font=("Arial", 9), bg="white").pack(anchor="w", pady=(10,0))
        maxprice_var = tk.StringVar(value=self.config.get('max_price', '500'))
        tk.Entry(f, textvariable=maxprice_var, width=10).pack(anchor="w")
        
        # Min Volume
        tk.Label(f, text="Min Avg Volume:", font=("Arial", 9), bg="white").pack(anchor="w", pady=(10,0))
        vol_var = tk.StringVar(value=self.config.get('min_avg_volume', '500000'))
        tk.Entry(f, textvariable=vol_var, width=12).pack(anchor="w")
        
        # Require MA Stack
        ma_var = tk.BooleanVar(value=self.config.get('trend_require_ma_stack', True))
        tk.Checkbutton(f, text="Require MA Stack (20>50>200)", variable=ma_var,
                      bg="white", font=("Arial", 9)).pack(anchor="w", pady=(10,0))
        
        def save():
            self.config['trend_min_score'] = score_var.get()
            self.config['trend_min_quarter_perf'] = qtr_var.get()
            self.config['min_price'] = minprice_var.get()
            self.config['max_price'] = maxprice_var.get()
            self.config['min_avg_volume'] = vol_var.get()
            self.config['trend_require_ma_stack'] = ma_var.get()
            with open(CONFIG_FILE, 'w') as file:
                json.dump(self.config, file, indent=2)
            win.destroy()
            self.status.config(text="Trend settings saved")
        
        tk.Button(win, text="Save", command=save, bg=GREEN, fg="white",
                 font=("Arial", 10, "bold"), width=12, relief="flat").pack(pady=20)
    
    def dip_settings(self):
        """Swing/Dip scanner settings"""
        win = tk.Toplevel(self.root)
        win.title("Swing Scanner Settings")
        win.geometry("320x400")
        win.transient(self.root)
        win.grab_set()
        win.configure(bg="white")
        
        tk.Label(win, text="Swing Scanner Settings", font=("Arial", 12, "bold"),
                bg="white", fg="#333").pack(pady=(15,10))
        
        f = tk.Frame(win, bg="white", padx=25)
        f.pack(fill="x")
        
        # Min Score
        tk.Label(f, text="Min Score for Report:", font=("Arial", 9), bg="white").pack(anchor="w", pady=(5,0))
        score_var = tk.StringVar(value=self.config.get('swing_min_score', '60'))
        tk.Entry(f, textvariable=score_var, width=10).pack(anchor="w")
        
        # Min Dip %
        tk.Label(f, text="Min Dip % (e.g. 1):", font=("Arial", 9), bg="white").pack(anchor="w", pady=(10,0))
        mindip_var = tk.StringVar(value=self.config.get('dip_min_percent', '1'))
        tk.Entry(f, textvariable=mindip_var, width=10).pack(anchor="w")
        
        # Max Dip %
        tk.Label(f, text="Max Dip % (e.g. 5):", font=("Arial", 9), bg="white").pack(anchor="w", pady=(10,0))
        maxdip_var = tk.StringVar(value=self.config.get('dip_max_percent', '5'))
        tk.Entry(f, textvariable=maxdip_var, width=10).pack(anchor="w")
        
        # Min Price
        tk.Label(f, text="Min Stock Price $:", font=("Arial", 9), bg="white").pack(anchor="w", pady=(10,0))
        minprice_var = tk.StringVar(value=self.config.get('min_price', '5'))
        tk.Entry(f, textvariable=minprice_var, width=10).pack(anchor="w")
        
        # Max Price  
        tk.Label(f, text="Max Stock Price $:", font=("Arial", 9), bg="white").pack(anchor="w", pady=(10,0))
        maxprice_var = tk.StringVar(value=self.config.get('max_price', '500'))
        tk.Entry(f, textvariable=maxprice_var, width=10).pack(anchor="w")
        
        # Check news
        news_var = tk.BooleanVar(value=self.config.get('dip_require_news_check', True))
        tk.Checkbutton(f, text="Check news (slower but smarter)", variable=news_var,
                      bg="white", font=("Arial", 9)).pack(anchor="w", pady=(10,0))
        
        # Check analyst ratings
        analyst_var = tk.BooleanVar(value=self.config.get('dip_require_analyst_check', True))
        tk.Checkbutton(f, text="Check analyst ratings", variable=analyst_var,
                      bg="white", font=("Arial", 9)).pack(anchor="w", pady=(5,0))
        
        def save():
            self.config['swing_min_score'] = score_var.get()
            self.config['dip_min_percent'] = float(mindip_var.get())
            self.config['dip_max_percent'] = float(maxdip_var.get())
            self.config['min_price'] = minprice_var.get()
            self.config['max_price'] = maxprice_var.get()
            self.config['dip_require_news_check'] = news_var.get()
            self.config['dip_require_analyst_check'] = analyst_var.get()
            with open(CONFIG_FILE, 'w') as file:
                json.dump(self.config, file, indent=2)
            win.destroy()
            self.status.config(text="Swing settings saved")
        
        tk.Button(win, text="Save", command=save, bg=BLUE, fg="white",
                 font=("Arial", 10, "bold"), width=12, relief="flat").pack(pady=20)
    
    def api_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("350x200")
        win.transient(self.root)
        win.grab_set()
        win.configure(bg="white")
        
        tk.Label(win, text="Settings", font=("Arial", 12, "bold"),
                bg="white", fg="#333").pack(pady=(15,10))
        
        f = tk.Frame(win, bg="white", padx=20)
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
        
        def save():
            self.config['finviz_api_key'] = api_var.get()
            self.config['broker_url'] = broker_var.get()
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            win.destroy()
        
        tk.Button(win, text="Save", command=save, bg=GREEN, fg="white",
                 font=("Arial", 10, "bold"), width=10, relief="flat").pack(pady=10)
    
    def open_broker(self):
        webbrowser.open(self.config.get('broker_url', 'https://www.schwab.com'))
    
    def open_reports(self):
        os.makedirs(os.path.join(BASE_DIR, "reports"), exist_ok=True)
        os.startfile(os.path.join(BASE_DIR, "reports"))
    
    def view_logs(self):
        if os.path.exists(LOG_FILE):
            os.startfile(LOG_FILE)
    
    def show_help(self):
        help_text = """
ClearBlueSky Stock Scanner & AI Research Tool

QUICK START:
1. Select your AI tool (Claude recommended)
2. Run a scanner (Trend or Swing)
3. Report opens in browser
4. Click "Copy AI Prompt" then paste in AI
5. Get BUY/SELL/HOLD recommendations!

SCANNERS:
• Trend Scanner - Finds uptrending stocks
  Best for: Longer holds (weeks/months)
  Run: Evenings after market close

• Swing Scanner - Finds oversold dips  
  Best for: Quick trades (1-5 days)
  Run: 2:30-4:00 PM before close

SCORES:
  90-100 = Elite (rare, full position)
  70-89  = Strong (standard position)
  60-69  = Decent (small position)
  Below 60 = Skip

─────────────────────────────────
Made with Claude AI 🤖

Contact: Discord ID 340935763405570048
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
