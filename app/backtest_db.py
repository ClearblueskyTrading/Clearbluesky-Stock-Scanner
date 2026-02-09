"""
ClearBlueSky – Backtest feedback loop (SQLite).
Log every signal; nightly or on-demand job updates outcomes at T+1, T+3, T+5, T+10.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = Path(BASE_DIR) / "backtest_signals.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                signal_date TEXT NOT NULL,
                score INTEGER NOT NULL,
                price_at_signal REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                signal_id INTEGER PRIMARY KEY REFERENCES signals(id),
                price_t1 REAL, price_t3 REAL, price_t5 REAL, price_t10 REAL,
                pct_t1 REAL, pct_t3 REAL, pct_t5 REAL, pct_t10 REAL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def log_signal(ticker, scan_type, score, price_at_signal=None):
    """Log one signal. Call after each qualifying ticker in a report."""
    init_db()
    conn = _get_conn()
    try:
        signal_date = datetime.now().strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO signals (ticker, scan_type, signal_date, score, price_at_signal) VALUES (?, ?, ?, ?, ?)",
            (str(ticker).strip().upper(), str(scan_type).strip(), signal_date, int(score), price_at_signal),
        )
        conn.commit()
    finally:
        conn.close()


def log_signals_from_report(stocks_data, scan_type):
    """Log all tickers from a report run. stocks_data = list of dicts with ticker, score, price (optional)."""
    for s in stocks_data:
        ticker = s.get("ticker") or s.get("Ticker")
        if not ticker:
            continue
        score = s.get("score") or s.get("Score") or s.get("SCORE") or 0
        try:
            score = int(float(score))
        except (TypeError, ValueError):
            score = 0
        price = s.get("price")
        if price not in (None, "", "N/A"):
            try:
                price = float(str(price).replace("$", "").replace(",", ""))
            except (TypeError, ValueError):
                price = None
        else:
            price = None
        log_signal(ticker, scan_type, score, price)


def update_outcomes_for_signal(signal_id, price_t1, price_t3, price_t5, price_t10, price_at_signal):
    """Store outcomes for one signal. price_at_signal used to compute pct change."""
    if price_at_signal is None or price_at_signal <= 0:
        return
    conn = _get_conn()
    try:
        def pct(p):
            if p is None:
                return None
            return round((float(p) - price_at_signal) / price_at_signal * 100, 2)

        conn.execute(
            """INSERT OR REPLACE INTO outcomes (signal_id, price_t1, price_t3, price_t5, price_t10, pct_t1, pct_t3, pct_t5, pct_t10, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (signal_id, price_t1, price_t3, price_t5, price_t10,
             pct(price_t1), pct(price_t3), pct(price_t5), pct(price_t10),
             datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def _trading_days_after(signal_date_str, n):
    """Approximate n trading days after signal_date (simple: add calendar days)."""
    try:
        d = datetime.strptime(signal_date_str[:10], "%Y-%m-%d")
        # ~5 trading days per 7 calendar days
        d += timedelta(days=max(1, int(n * 7 / 5)))
        return d.strftime("%Y-%m-%d")
    except Exception:
        return None


def update_outcomes(progress_callback=None):
    """
    For each signal without outcomes and old enough, fetch close prices at T+1, T+3, T+5, T+10
    and fill outcomes. Uses yfinance. progress_callback(msg) optional.
    """
    def progress(msg):
        if progress_callback:
            progress_callback(msg)

    try:
        import yfinance as yf
    except ImportError:
        progress("yfinance required for backtest outcomes; pip install yfinance")
        return 0

    init_db()
    conn = _get_conn()
    try:
        rows = conn.execute("""
            SELECT s.id, s.ticker, s.signal_date, s.price_at_signal
            FROM signals s
            LEFT JOIN outcomes o ON s.id = o.signal_id
            WHERE o.signal_id IS NULL AND s.signal_date <= date('now', '-11 days')
        """).fetchall()
    finally:
        conn.close()

    updated = 0
    for row in rows:
        sid, ticker, signal_date, price_at_signal = row["id"], row["ticker"], row["signal_date"], row["price_at_signal"]
        try:
            sym = yf.Ticker(ticker)
            hist = sym.history(period="1mo", interval="1d", timeout=30)
            if hist is None or hist.empty or len(hist) < 2:
                continue
            hist = hist.sort_index()
            closes = hist["Close"]
            try:
                signal_dt = datetime.strptime(signal_date[:10], "%Y-%m-%d")
            except Exception:
                continue
            # Rows on or after signal_date; T+1 = second row, T+3 = fourth, etc.
            mask = hist.index >= signal_dt
            future_closes = closes.loc[mask].iloc[:15]
            if len(future_closes) < 2:
                continue
            def at(n):
                if len(future_closes) <= n:
                    return None
                try:
                    return float(future_closes.iloc[n])
                except Exception:
                    return None
            pt1 = at(1)
            pt3 = at(3)
            pt5 = at(5)
            pt10 = at(10)
            update_outcomes_for_signal(sid, pt1, pt3, pt5, pt10, price_at_signal)
            updated += 1
        except Exception:
            continue
    progress(f"Updated outcomes for {updated} signals")
    return updated


def get_stats_for_scan_type(scan_type, min_signals=10):
    """
    Return aggregate backtest stats for this scan_type: win_rate_t1/t3/t5/t10 (pct positive),
    avg_return_t1/t3/t5/t10, sample_size. If sample_size < min_signals, returns None.
    """
    init_db()
    conn = _get_conn()
    try:
        rows = conn.execute("""
            SELECT o.pct_t1, o.pct_t3, o.pct_t5, o.pct_t10
            FROM outcomes o
            JOIN signals s ON s.id = o.signal_id
            WHERE s.scan_type = ?
        """, (str(scan_type).strip(),)).fetchall()
    finally:
        conn.close()

    if not rows or len(rows) < min_signals:
        return None
    n = len(rows)
    def stats(key):
        vals = [r[key] for r in rows if r[key] is not None]
        if not vals:
            return None, None
        wins = sum(1 for v in vals if v > 0)
        return round(wins / len(vals) * 100, 1), round(sum(vals) / len(vals), 2)
    wr1, avg1 = stats("pct_t1")
    wr3, avg3 = stats("pct_t3")
    wr5, avg5 = stats("pct_t5")
    wr10, avg10 = stats("pct_t10")
    return {
        "sample_size": n,
        "win_rate_t1": wr1, "win_rate_t3": wr3, "win_rate_t5": wr5, "win_rate_t10": wr10,
        "avg_return_t1": avg1, "avg_return_t3": avg3, "avg_return_t5": avg5, "avg_return_t10": avg10,
    }
