#!/usr/bin/env python3
"""
VELOCITY PRE-MARKET HUNTER — Unified morning scanner.
Single command: python velocity_scanner.py --scan premarket
Scans fixed universe, scores 4 signal types, grades A+ to F, outputs terminal + PDF.
"""
import argparse
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
SCAN_UNIVERSE = [
    "TQQQ", "SOXL", "SPXL", "NVDL",
    "NVDA", "TSLA", "AMD", "META", "NFLX", "AMZN", "GOOGL", "COIN", "MSTR",
    "AAPL", "MSFT", "JPM", "V",
]
POSITION_SIZES = {"A+": 5000, "A": 4000, "B": 3000, "C": 0}
TARGETS = {"gap_recovery": 0.03, "accumulation": 0.025, "breakout": 0.04, "gap_go": 0.05}
MIN_STOP_PCT = 0.015
MAX_STOP_PCT = 0.03
ACCOUNT_SIZE = 20000
MAX_RISK_PER_TRADE = 0.03
OUTPUT_DIR = Path(BASE_DIR) / "scanner_output"
CACHE_DIR = Path(BASE_DIR) / "cache"
# Max tickers when using index (sp500/russell2000/etfs) to keep scan time reasonable
INDEX_UNIVERSE_CAP = 200

# -----------------------------------------------------------------------------
# UNIVERSE
# -----------------------------------------------------------------------------
def get_universe_for_index(index: Optional[str]) -> List[str]:
    """
    Return ticker list for the scan. When index is sp500/russell2000/etfs, fetch from
    Finviz (not ticker restricted). Otherwise use fixed SCAN_UNIVERSE (e.g. index='velocity' or None).
    """
    if index and index in ("sp500", "russell2000", "etfs"):
        try:
            from breadth import fetch_full_index_for_breadth
            rows = fetch_full_index_for_breadth(index, progress_callback=None)
            tickers = [str(r.get("Ticker") or "").strip().upper() for r in (rows or []) if r.get("Ticker")]
            tickers = [t for t in tickers if t]
            return tickers[:INDEX_UNIVERSE_CAP] if tickers else SCAN_UNIVERSE
        except Exception:
            return SCAN_UNIVERSE
    return SCAN_UNIVERSE

# -----------------------------------------------------------------------------
# DATA FETCH (yfinance)
# -----------------------------------------------------------------------------
try:
    import yfinance as yf
    YF = True
except ImportError:
    YF = False


def _last(series):
    if series is None or (hasattr(series, "empty") and series.empty):
        return None
    try:
        return float(series.dropna().iloc[-1])
    except (IndexError, TypeError):
        return None


def fetch_market_context() -> Dict[str, Any]:
    """Step 1: SPY, QQQ, SMH (SOX proxy), VIX. Prior close + pre-market if available."""
    out = {"spy": {}, "qqq": {}, "smh": {}, "vix": {}, "regime": "UNKNOWN", "bias": "NEUTRAL", "error": None}
    if not YF:
        return out
    try:
        for sym, key in [("SPY", "spy"), ("QQQ", "qqq"), ("SMH", "smh"), ("^VIX", "vix")]:
            t = yf.Ticker(sym)
            df = t.history(period="5d", interval="1d")
            if df is not None and not df.empty:
                close = _last(df["Close"])
                out[key]["close"] = close
                out[key]["above_50"] = out[key]["above_200"] = None
                if close and len(df) >= 50:
                    sma50 = _last(df["Close"].rolling(50).mean())
                    out[key]["above_50"] = close > sma50 if sma50 else None
                if close and len(df) >= 200:
                    sma200 = _last(df["Close"].rolling(200).mean())
                    out[key]["above_200"] = close > sma200 if sma200 else None
            # Pre-market for indices (optional)
            try:
                pm = t.history(period="1d", interval="5m", prepost=True)
                if pm is not None and not pm.empty:
                    out[key]["pm_close"] = _last(pm["Close"])
                    out[key]["pm_pct"] = ((out[key].get("pm_close") or close) - close) / close * 100 if close else None
            except Exception:
                out[key]["pm_close"] = out[key].get("close")
                out[key]["pm_pct"] = 0.0
        vix = out.get("vix", {}).get("close") or 0
        if vix < 15:
            out["regime"] = "LOW FEAR"
            out["bias"] = "LONG SETUPS FAVORED"
        elif vix < 22:
            out["regime"] = "NORMAL"
            out["bias"] = "LONG SETUPS FAVORED"
        else:
            out["regime"] = "ELEVATED FEAR"
            out["bias"] = "CAUTIOUS"
    except Exception as e:
        out["error"] = str(e)
        out["regime"] = "ERROR"
    return out


def fetch_ticker_data(ticker: str) -> Dict[str, Any]:
    """Step 2: Prior day (close, volume, SMA, RSI, ATR, BB) + pre-market price/volume."""
    d = {"ticker": ticker, "prior_close": None, "prior_volume": None, "pm_price": None, "pm_volume": None,
         "sma20": None, "sma50": None, "sma200": None, "rsi": None, "atr": None, "bb_upper": None, "bb_lower": None,
         "earnings_days": None, "prior_high": None, "prior_low": None}
    if not YF:
        return d
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="60d", interval="1d")
        if df is None or df.empty or len(df) < 20:
            return d
        df = df.astype(float, errors="ignore")
        close = df["Close"]
        d["prior_close"] = _last(close)
        d["prior_volume"] = _last(df["Volume"]) if "Volume" in df.columns else None
        d["prior_high"] = _last(df["High"])
        d["prior_low"] = _last(df["Low"])
        d["sma20"] = _last(close.rolling(20).mean())
        d["sma50"] = _last(close.rolling(50).mean())
        d["sma200"] = _last(close.rolling(200).mean()) if len(close) >= 200 else None
        # RSI
        try:
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = (-delta).where(delta < 0, 0.0)
            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            rs = avg_gain / avg_loss.replace(0, 1e-10)
            d["rsi"] = _last(100 - (100 / (1 + rs)))
        except Exception:
            d["rsi"] = None
        # ATR(14)
        high, low = df["High"], df["Low"]
        tr = high - low
        tr = tr.combine((high - close.shift(1)).abs(), max).combine((low - close.shift(1)).abs(), max)
        d["atr"] = _last(tr.rolling(14).mean())
        # BB
        mid = close.rolling(20).mean()
        std = close.rolling(20).std()
        d["bb_upper"] = _last(mid + 2 * std)
        d["bb_lower"] = _last(mid - 2 * std)
        # Pre-market
        try:
            pm = t.history(period="1d", interval="5m", prepost=True)
            if pm is not None and not pm.empty:
                d["pm_price"] = _last(pm["Close"])
                d["pm_volume"] = int(_last(pm["Volume"]) or 0)
            if d["pm_price"] is None:
                d["pm_price"] = d["prior_close"]
        except Exception:
            d["pm_price"] = d["prior_close"]
            d["pm_volume"] = 0
        # Earnings (simplified: assume none within 3 days unless we have calendar)
        d["earnings_days"] = None
    except Exception as e:
        d["error"] = str(e)
    return d


# -----------------------------------------------------------------------------
# SIGNAL SCORING (0-100 each)
# -----------------------------------------------------------------------------
def score_gap_recovery(d: Dict) -> float:
    """Emotional Gap Recovery: gap down 1.5-4%, recovery, PM volume, above 50 SMA."""
    if d.get("prior_close") is None or d.get("pm_price") is None:
        return 0.0
    gap_pct = (d["pm_price"] - d["prior_close"]) / d["prior_close"] * 100
    if gap_pct > -0.5:
        return 0.0
    gap_size = abs(gap_pct)
    if gap_size < 1.0 or gap_size > 6.0:
        return max(0, 40 - abs(gap_size - 2.5) * 10)
    gap_low = d["prior_close"] * (1 + gap_pct / 100)
    gap_range = d["prior_close"] - gap_low
    recovery = ((d["pm_price"] - gap_low) / gap_range * 100) if gap_range and gap_range > 0 else 0
    recovery = max(0, min(100, recovery))
    pm_vol = d.get("pm_volume") or 0
    avg_vol = d.get("prior_volume") or 1
    pm_vol_ratio = min(100, (pm_vol / (avg_vol / 2)) * 100) if avg_vol else 0
    dist_50 = 0
    if d.get("sma50") and d["pm_price"]:
        dist_50 = max(0, (d["sma50"] - d["pm_price"]) / d["pm_price"] * 100)
    earn_pen = 50 if d.get("earnings_days") is not None and d.get("earnings_days") is not False else 0
    score = (100 - abs(gap_size - 2.5) * 10 - (100 - recovery) * 0.5 - (100 - pm_vol_ratio) * 0.008 - dist_50 * 5 - earn_pen)
    return max(0.0, min(100.0, score))


def score_accumulation(d: Dict) -> float:
    """Institutional Accumulation: small gap, PM volume, prior close in top of range, RSI 40-60."""
    if d.get("prior_close") is None or d.get("pm_price") is None:
        return 0.0
    gap_pct = (d["pm_price"] - d["prior_close"]) / d["prior_close"] * 100
    if abs(gap_pct) > 2.0:
        return max(0, 50 - abs(gap_pct) * 20)
    pm_vol = d.get("pm_volume") or 0
    avg_vol = d.get("prior_volume") or 1
    pm_vol_ratio = min(100, (pm_vol / (avg_vol / 2)) * 100) if avg_vol else 0
    prior_strength = 50
    if d.get("prior_high") and d.get("prior_low") and d["prior_close"]:
        rng = d["prior_high"] - d["prior_low"]
        if rng and rng > 0:
            prior_strength = (d["prior_close"] - d["prior_low"]) / rng * 100
    rsi = d.get("rsi") or 50
    rsi_pen = abs(rsi - 50) * 0.8
    score = 100 - abs(gap_pct) * 20 - (100 - pm_vol_ratio) * 0.006 - (100 - prior_strength) * 0.004 - rsi_pen
    return max(0.0, min(100.0, score))


def score_breakout(d: Dict) -> float:
    """Breakout Pre-Load: near resistance, PM volume, ADX proxy (trend)."""
    if d.get("prior_close") is None or d.get("pm_price") is None:
        return 0.0
    res = d.get("bb_upper") or d.get("prior_high") or d["prior_close"] * 1.02
    dist_res = abs(d["pm_price"] - res) / d["pm_price"] * 100 if d["pm_price"] else 10
    if dist_res > 5:
        return max(0, 40 - dist_res * 15)
    pm_vol = d.get("pm_volume") or 0
    avg_vol = d.get("prior_volume") or 1
    pm_vol_ratio = min(100, (pm_vol / (avg_vol / 2)) * 100) if avg_vol else 0
    adx_proxy = 25
    score = 100 - dist_res * 15 - (100 - pm_vol_ratio) * 0.007 - max(0, 25 - adx_proxy) * 2
    return max(0.0, min(100.0, score))


def score_gap_go(d: Dict) -> float:
    """Gap-and-Go Momentum: gap up 2%+, retention, PM volume."""
    if d.get("prior_close") is None or d.get("pm_price") is None:
        return 0.0
    gap_pct = (d["pm_price"] - d["prior_close"]) / d["prior_close"] * 100
    if gap_pct < 1.5:
        return 0.0
    retention = 100
    pm_vol = d.get("pm_volume") or 0
    avg_vol = d.get("prior_volume") or 1
    pm_vol_ratio = min(100, (pm_vol / (avg_vol / 2)) * 100) if avg_vol else 0
    res = d.get("bb_upper") or d["prior_close"] * 1.05
    res_prox = (res - d["pm_price"]) / d["pm_price"] * 100 if d["pm_price"] else 0
    score = 100 - (100 - retention) * 1.2 - (100 - pm_vol_ratio) * 0.005 - max(0, res_prox) * 10
    return max(0.0, min(100.0, score))


# -----------------------------------------------------------------------------
# GRADING & RISK
# -----------------------------------------------------------------------------
def grade_score(score: float) -> str:
    if score >= 85: return "A+"
    if score >= 75: return "A"
    if score >= 65: return "B"
    if score >= 55: return "C"
    return "F"


def primary_signal(d: Dict) -> tuple:
    """Returns (signal_name, score)."""
    s1 = score_gap_recovery(d)
    s2 = score_accumulation(d)
    s3 = score_breakout(d)
    s4 = score_gap_go(d)
    best = max((s1, "Emotional Gap Recovery"), (s2, "Institutional Accumulation"),
               (s3, "Breakout Pre-Load"), (s4, "Gap-and-Go Momentum"), key=lambda x: x[0])
    d["_score_gap"] = s1
    d["_score_accum"] = s2
    d["_score_breakout"] = s3
    d["_score_gapgo"] = s4
    return best[1], best[0]


def apply_risk_penalties(d: Dict, raw_score: float, signal_name: str) -> float:
    """Volatility, liquidity, earnings, trend violation."""
    penalty = 0
    if d.get("atr") and d.get("pm_price"):
        atr_pct = d["atr"] / d["pm_price"] * 100
        if atr_pct > 4:
            penalty += 15
    pm_vol = d.get("pm_volume") or 0
    avg_vol = d.get("prior_volume") or 1
    if avg_vol and pm_vol / (avg_vol / 2) < 0.2:
        penalty += 10
    if d.get("earnings_days") is not None and d.get("earnings_days") is not False:
        penalty += 50
    if d.get("sma50") and d.get("pm_price") and d["pm_price"] < d["sma50"] and "Gap" in signal_name:
        penalty += 25
    return max(0, raw_score - penalty)


# -----------------------------------------------------------------------------
# ENTRY CALC
# -----------------------------------------------------------------------------
def entry_plan(d: Dict, grade: str, signal_name: str) -> Dict[str, Any]:
    """Entry zone, position size, target %, stop %, order ticket."""
    price = d.get("pm_price") or d.get("prior_close") or 1
    size_dollars = POSITION_SIZES.get(grade, 0)
    shares = int(size_dollars / price) if price and size_dollars else 0
    target_pct = TARGETS.get(
        "gap_recovery" if "Gap Recovery" in signal_name else
        "accumulation" if "Accumulation" in signal_name else
        "breakout" if "Breakout" in signal_name else "gap_go", 0.03)
    atr = d.get("atr") or price * 0.02
    stop_pct = max(MIN_STOP_PCT, min(MAX_STOP_PCT, atr / price))
    target_price = round(price * (1 + target_pct), 2)
    stop_price = round(price * (1 - stop_pct), 2)
    risk_dollars = shares * (price - stop_price) if shares else 0
    reward_dollars = shares * (target_price - price) if shares else 0
    rr = reward_dollars / risk_dollars if risk_dollars else 0
    entry_lo = round(price * 0.95, 2)
    entry_hi = round(price, 2)
    return {
        "shares": shares,
        "entry_zone": f"${entry_lo}-${entry_hi}",
        "target_price": target_price,
        "target_pct": target_pct * 100,
        "stop_price": stop_price,
        "stop_pct": stop_pct * 100,
        "risk_dollars": round(risk_dollars, 0),
        "reward_dollars": round(reward_dollars, 0),
        "rr_ratio": round(rr, 1),
        "position": size_dollars,
        "order_ticket_lmt": f"BUY {shares} {d['ticker']} @ ${entry_hi:.2f} LMT (Day)",
        "order_ticket_oco": f"OCO: SELL {shares} @ ${target_price} LMT + SELL {shares} @ ${stop_price} STP",
    }


# -----------------------------------------------------------------------------
# MAIN SCAN
# -----------------------------------------------------------------------------
def run_premarket_scan(progress_callback=None, index: Optional[str] = None) -> Dict[str, Any]:
    """Run full Velocity Pre-Market Hunter scan. Returns context, tickers, grades, output path.
    index: None or 'velocity' = fixed SCAN_UNIVERSE; 'sp500'/'russell2000'/'etfs' = index universe (not ticker restricted)."""
    start = datetime.now()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    universe = get_universe_for_index(index)
    if progress_callback:
        progress_callback("Fetching market context...")
    ctx = fetch_market_context()
    results = []
    n = len(universe)
    for i, ticker in enumerate(universe):
        if progress_callback:
            progress_callback(f"Scanning {ticker} ({i+1}/{n})...")
        d = fetch_ticker_data(ticker)
        signal_name, raw_score = primary_signal(d)
        final_score = apply_risk_penalties(d, raw_score, signal_name)
        grade = grade_score(final_score)
        d["signal"] = signal_name
        d["raw_score"] = round(raw_score, 1)
        d["score"] = round(final_score, 1)
        d["grade"] = grade
        if grade in ("A+", "A", "B"):
            d["entry"] = entry_plan(d, grade, signal_name)
        else:
            d["entry"] = None
        results.append(d)
    results.sort(key=lambda x: ({"A+": 0, "A": 1, "B": 2, "C": 3, "F": 4}.get(x["grade"], 5), -x["score"]))
    elapsed = (datetime.now() - start).total_seconds()
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    pdf_path = OUTPUT_DIR / f"{ts}_premarket.pdf"
    return {"context": ctx, "tickers": results, "elapsed": elapsed, "pdf_path": pdf_path, "timestamp": ts}


# -----------------------------------------------------------------------------
# TERMINAL OUTPUT
# -----------------------------------------------------------------------------
def print_terminal(report: Dict[str, Any]) -> None:
    """ASCII terminal output."""
    ctx = report["context"]
    tickers = report["tickers"]
    ts = report.get("timestamp", "")
    dt = datetime.now().strftime("%m/%d/%Y")
    tm = datetime.now().strftime("%I:%M %p ET")
    w = 74
    print()
    print("=" * w)
    print(" VELOCITY PRE-MARKET HUNTER -- MANUAL SCAN RESULTS ".center(w))
    print(f" {dt} | Scan Time: {tm} ".center(w))
    print("=" * w)
    print()
    spy = ctx.get("spy", {})
    qqq = ctx.get("qqq", {})
    smh = ctx.get("smh", {})
    vix = ctx.get("vix", {})
    spyc = spy.get("close") or 0
    qqqc = qqq.get("close") or 0
    smhc = smh.get("close") or 0
    spyp = spy.get("pm_pct") or 0
    qqqp = qqq.get("pm_pct") or 0
    smhp = smh.get("pm_pct") or 0
    vixv = vix.get("close") or 0
    print("[MARKET CONTEXT]")
    print(f"SPY: ${spyc:.2f} ({spyp:+.1f}%) | QQQ: ${qqqc:.2f} ({qqqp:+.1f}%) | SMH: ${smhc:.2f} ({smhp:+.1f}%) | VIX: {vixv:.1f}")
    print(f"Regime: {ctx.get('regime', 'N/A')} | Bias: {ctx.get('bias', 'N/A')}")
    print()
    print("[SCANNING {} TICKERS...]".format(len(tickers)))
    print("#" * 40 + " 100%")
    print()
    a_plus = [t for t in tickers if t["grade"] == "A+"]
    a_b = [t for t in tickers if t["grade"] in ("A", "B")]
    c_list = [t for t in tickers if t["grade"] == "C"]
    f_list = [t for t in tickers if t["grade"] == "F"]
    print("-" * w)
    print("TIER 1 -- TRADE NOW (A+ Setups)")
    print("-" * w)
    for i, t in enumerate(a_plus, 1):
        e = t.get("entry") or {}
        gap = ((t.get("pm_price") or 0) - (t.get("prior_close") or 0)) / (t.get("prior_close") or 1) * 100
        pm_vol = (t.get("pm_volume") or 0) / ((t.get("prior_volume") or 1) / 2) * 100 if t.get("prior_volume") else 0
        print()
        print(f"#{i} PRIORITY: {t['ticker']} | Grade: {t['grade']} | Score: {t['score']}/100")
        print(f"    Signal: {t['signal']}")
        print(f"    Gap: {gap:+.1f}% | PM Vol: {pm_vol:.0f}% of avg")
        print()
        print("    ENTRY PLAN:")
        print(f"    Buy: {e.get('shares', 0)} shares @ {e.get('entry_zone', 'N/A')} (Limit)")
        print(f"    Target: ${e.get('target_price', 0):.2f} (+{e.get('target_pct', 0):.1f}%) | Stop: ${e.get('stop_price', 0):.2f} (-{e.get('stop_pct', 0):.1f}%)")
        print(f"    Risk: ${e.get('risk_dollars', 0):.0f} | Reward: ${e.get('reward_dollars', 0):.0f} | R:R = {e.get('rr_ratio', 0):.1f}:1")
        print(f"    Position: ${e.get('position', 0):.0f}")
        print()
        print("    ORDER TICKET:")
        print("    -> " + e.get("order_ticket_lmt", ""))
        print("    -> " + e.get("order_ticket_oco", ""))
        print()
    if not a_plus:
        print("(No A+ setups)")
        print()
    print("-" * w)
    print("TIER 2 -- SECONDARY TARGETS (A/B Setups)")
    print("-" * w)
    for t in a_b[:10]:
        print(f"{t['ticker']} | Grade: {t['grade']} | Score: {t['score']} | Signal: {t['signal']}")
    if not a_b:
        print("(None)")
    print()
    print("-" * w)
    print("WATCHLIST -- MONITOR ONLY (C Grade)")
    print("-" * w)
    for t in c_list[:8]:
        print(f"{t['ticker']} | Score: {t['score']}")
    if not c_list:
        print("(None)")
    print()
    print("-" * w)
    print("DISQUALIFIED (F Grade)")
    print("-" * w)
    for t in f_list[:8]:
        print(f"{t['ticker']} | Score: {t['score']}")
    if not f_list:
        print("(None)")
    print()
    print("-" * w)
    print("SUMMARY:")
    print(f"A+ Setups: {len(a_plus)} | Deploy: ${sum(POSITION_SIZES.get(t['grade'], 0) for t in a_plus):,.0f}")
    print(f"A Setups: {len([t for t in a_b if t['grade']=='A'])} | B Setups: {len([t for t in a_b if t['grade']=='B'])}")
    print(f"PDF Report: {report.get('pdf_path', '')}")
    print(f"Scan Duration: {report.get('elapsed', 0):.0f} seconds")
    print("=" * w)
    print()


# -----------------------------------------------------------------------------
# PDF REPORT
# -----------------------------------------------------------------------------
def write_pdf(report: Dict[str, Any]) -> Path:
    """Write PDF to scanner_output/."""
    path = report.get("pdf_path")
    if not path:
        return None
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        c = canvas.Canvas(str(path), pagesize=letter)
        width, height = letter
        margin = inch
        x, y = margin, height - margin
        line = 12
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, "VELOCITY PRE-MARKET HUNTER — Scan Results")
        y -= line * 1.5
        c.setFont("Helvetica", 10)
        c.drawString(x, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} ET | Duration: {report.get('elapsed', 0):.0f}s")
        y -= line * 2
        for t in report.get("tickers", []):
            if y < margin + line * 4:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", 10)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x, y, f"{t['ticker']} — {t['grade']} | Score: {t['score']} | {t['signal']}")
            y -= line
            c.setFont("Helvetica", 9)
            gap = ((t.get("pm_price") or 0) - (t.get("prior_close") or 0)) / (t.get("prior_close") or 1) * 100
            c.drawString(x, y, f"  Gap: {gap:+.1f}% | PM Price: ${t.get('pm_price') or 0:.2f} | Prior Close: ${t.get('prior_close') or 0:.2f}")
            y -= line
            if t.get("entry"):
                e = t["entry"]
                c.drawString(x, y, f"  Entry: {e.get('entry_zone')} | Target: ${e.get('target_price')} (+{e.get('target_pct')}%) | Stop: ${e.get('stop_price')}")
                y -= line
            y -= 4
        c.save()
        return path
    except Exception as e:
        print(f"PDF write failed: {e}")
        return None


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Velocity Pre-Market Hunter")
    parser.add_argument("--scan", required=True, choices=["premarket"], help="Scan type (premarket only)")
    args = parser.parse_args()
    if args.scan != "premarket":
        print("[FAIL] Only --scan premarket is supported.")
        return 1
    def progress(msg):
        print("   ", msg, flush=True)
    report = run_premarket_scan(progress_callback=progress)
    write_pdf(report)
    print_terminal(report)
    print("[OK] Scan complete: " + str(report.get("pdf_path", "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
