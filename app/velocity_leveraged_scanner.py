# ============================================================
# ClearBlueSky - Velocity Barbell Strategy Scanner
# ============================================================
# Core decision: Is today's theme CLEAR or UNCERTAIN?
# CLEAR → Single Shot ($10K one ticker)
# UNCERTAIN → Barbell ($5K Foundation + $5K Runner)
# Uses sector proxy ETFs to pick leading theme, then outputs
# Barbell combo (Foundation + Runner) or Single Shot with rules.

import json
import os
import time
from typing import List, Dict, Optional, Callable

import finviz
from scan_settings import load_config
from finviz_safe import get_stock_safe

ARSENAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "velocity_leveraged_arsenal.json")

BARBELL_RULES = "BARBELL: Foundation -3%=$150 max, Runner -5%=$250 max. Combined max $400/day. Targets: Foundation +2-3% ($100-150), Runner +5-7% ($250-350)."
SINGLE_SHOT_RULES = "SINGLE SHOT: Stop -6%=$600 max. Target +3.5-5% ($350-500)."


def _load_arsenal() -> Dict:
    """Load velocity_leveraged_arsenal.json."""
    try:
        with open(ARSENAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sector_proxies": [], "barbell_combos": [], "single_shot_combos": [], "vehicles": []}


def _parse_change_pct(stock: dict) -> Optional[float]:
    """Get today's Change % from Finviz."""
    val = stock.get("Change", "") or stock.get("change", "")
    if val is None or val == "" or val == "N/A":
        return None
    s = str(val).strip().replace(",", "").replace("%", "").strip()
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _vehicle_info(arsenal: dict, ticker: str) -> Dict:
    """Get name, leverage, sector for a vehicle ticker from arsenal."""
    for v in arsenal.get("vehicles", []):
        if (v.get("ticker") or "").strip().upper() == (ticker or "").strip().upper():
            return {"name": v.get("name", ticker), "leverage": v.get("leverage", "—"), "sector": v.get("sector", "—")}
    return {"name": ticker, "leverage": "—", "sector": "—"}


def _get_rsi_for_ticker(ticker: str) -> Optional[float]:
    """Fetch RSI (14) or RSI from Finviz for a ticker. Returns float or None."""
    if not ticker or ticker == "CASH":
        return None
    try:
        stock = get_stock_safe(ticker)
        if not stock:
            return None
        val = stock.get("RSI (14)") or stock.get("RSI") or stock.get("rsi")
        if val is None or val == "" or val == "N/A":
            return None
        s = str(val).strip().replace(",", "").replace("%", "").strip()
        return float(s)
    except Exception:
        return None


def _barbell_by_signal(arsenal: dict, signal: str) -> Dict:
    """Get barbell combo for leading signal. Fallback to Broad market rally then No clear read."""
    combos = arsenal.get("barbell_combos", [])
    for c in combos:
        if (c.get("signal") or "").strip() == (signal or "").strip():
            return c
    for c in combos:
        if c.get("signal") == "Broad market rally":
            return c
    for c in combos:
        if c.get("signal") == "No clear read":
            return c
    return {"signal": signal, "scenario": "No trade", "foundation": None, "runner": None}


def _single_shot_by_signal(arsenal: dict, signal: str) -> Dict:
    """Get single-shot combo for leading signal. Fallback to Broad then No clear read."""
    combos = arsenal.get("single_shot_combos", [])
    for c in combos:
        if (c.get("signal") or "").strip() == (signal or "").strip():
            return c
    for c in combos:
        if c.get("signal") == "Broad market rally":
            return c
    for c in combos:
        if c.get("signal") == "No clear read":
            return c
    return {"signal": signal, "scenario": "No trade", "ticker": None, "trigger": "Cash is a position"}


def run_velocity_leveraged_scan(
    progress_callback: Optional[Callable[[str], None]] = None,
    config: Optional[Dict] = None,
) -> List[Dict]:
    """
    Run Velocity Barbell Strategy scan: fetch sector proxy performance,
    decide CLEAR (Single Shot) vs UNCERTAIN (Barbell), return recommended
    tickers with strategy rules.
    config["velocity_min_sector_pct"]: only recommend when leading sector >= this (default 0).
    config["velocity_barbell_theme"]: "auto" | "barbell" | "single_shot".
    Returns list of dicts with Ticker, Score, Strategy (Barbell/Single Shot), Role, Combo, Trigger, Company, etc.
    """
    cfg = config or load_config()
    min_sector_pct = float(cfg.get("velocity_min_sector_pct", 0.0))
    min_sector_pct = max(-5.0, min(5.0, min_sector_pct))
    theme = (cfg.get("velocity_barbell_theme") or "auto").strip().lower()
    if theme not in ("auto", "barbell", "single_shot"):
        theme = "auto"

    def progress(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    arsenal = _load_arsenal()
    proxies = arsenal.get("sector_proxies", [])

    if not proxies:
        progress("Velocity arsenal not found or empty.")
        return []

    progress(f"Fetching sector proxies (min % = {min_sector_pct}, theme = {theme})...")
    sector_changes = []
    total = len(proxies)
    for i, p in enumerate(proxies):
        ticker = p.get("ticker", "")
        signal = p.get("signal", "")
        name = p.get("name", ticker)
        if progress_callback:
            progress(f"Checking ({i+1}/{total}): {ticker} ({name})...")
        try:
            stock = get_stock_safe(ticker)
            change = _parse_change_pct(stock) if stock else None
            if change is not None:
                sector_changes.append({"ticker": ticker, "signal": signal, "name": name, "change_pct": change})
        except Exception:
            pass
        time.sleep(0.15)

    if not sector_changes:
        progress("Could not get sector proxy data.")
        return []

    sector_changes.sort(key=lambda x: x["change_pct"], reverse=True)
    leading = sector_changes[0]
    lead_signal = leading["signal"]
    lead_change = leading["change_pct"]
    second_change = sector_changes[1]["change_pct"] if len(sector_changes) > 1 else lead_change

    if lead_change < min_sector_pct:
        progress(f"Leading sector {lead_signal} is {lead_change}% (below {min_sector_pct}%). No clear read.")
        results = [{
            "Ticker": "CASH",
            "ticker": "CASH",
            "Score": 50,
            "score": 50,
            "Company": "No trade — Cash is a position",
            "Strategy": "No trade",
            "Role": "avoid",
            "Combo": "No clear read",
            "Trigger": f"Leading {lead_signal} at {lead_change}% (below threshold)",
            "Signal": lead_signal,
            "Change": f"{lead_change}%",
            "Volume": "—",
            "Sector": "—",
            "Industry": SINGLE_SHOT_RULES,
        }]
        return results

    # Decide Barbell vs Single Shot
    if theme == "barbell":
        use_single_shot = False
    elif theme == "single_shot":
        use_single_shot = True
    else:
        # Auto: CLEAR if one sector clearly leading (strong and gap vs 2nd)
        use_single_shot = (lead_change >= 0.8 and (lead_change - second_change) >= 0.5)

    results = []

    if use_single_shot:
        combo = _single_shot_by_signal(arsenal, lead_signal)
        ticker = combo.get("ticker")
        scenario = combo.get("scenario", "Single Shot")
        trigger = combo.get("trigger", "")
        if ticker:
            info = _vehicle_info(arsenal, ticker)
            results.append({
                "Ticker": ticker,
                "ticker": ticker,
                "Score": 100,
                "score": 100,
                "Company": info["name"],
                "Strategy": "Single Shot",
                "Role": "single_shot",
                "Combo": scenario,
                "Trigger": trigger,
                "Signal": lead_signal,
                "Change": f"{lead_change}%",
                "Volume": "—",
                "Sector": info["sector"],
                "Industry": f"{SINGLE_SHOT_RULES} Trigger: {trigger}",
            })
            progress(f"SINGLE SHOT: {ticker} — {scenario}. Leading: {lead_signal} ({lead_change}%).")
        else:
            results.append({
                "Ticker": "CASH",
                "ticker": "CASH",
                "Score": 50,
                "score": 50,
                "Company": "No trade — Cash is a position",
                "Strategy": "No trade",
                "Role": "avoid",
                "Combo": scenario,
                "Trigger": trigger,
                "Signal": lead_signal,
                "Change": f"{lead_change}%",
                "Volume": "—",
                "Sector": "—",
                "Industry": SINGLE_SHOT_RULES,
            })
            progress(f"No single-shot combo for {lead_signal}. Cash.")
    else:
        combo = _barbell_by_signal(arsenal, lead_signal)
        foundation = combo.get("foundation")
        runner = combo.get("runner")
        runner_alt = combo.get("runner_alt")
        scenario = combo.get("scenario", "Barbell")
        if foundation:
            info = _vehicle_info(arsenal, foundation)
            results.append({
                "Ticker": foundation,
                "ticker": foundation,
                "Score": 100,
                "score": 100,
                "Company": info["name"],
                "Strategy": "Barbell",
                "Role": "foundation",
                "Candidate_label": "Foundation Candidate",
                "Combo": scenario,
                "Trigger": f"$5K Foundation. {BARBELL_RULES}",
                "Signal": lead_signal,
                "Change": f"{lead_change}%",
                "Volume": "—",
                "Sector": info["sector"],
                "Industry": f"Foundation Candidate. $5K. -3%=$150 max. Target +2-3%. Pick by catalysts/technicals.",
            })
        # Runner Candidate 1 (runner_alt) = score 90; Runner Candidate 2 (runner) = score 95. Gives choice on oversold/catalysts/technicals.
        if runner_alt and runner_alt != runner:
            info = _vehicle_info(arsenal, runner_alt)
            rsi = _get_rsi_for_ticker(runner_alt)
            time.sleep(0.15)
            company_display = f"{info['name']} (RSI {int(rsi)}, {info['leverage']})" if rsi is not None else f"{info['name']} ({info['leverage']})"
            results.append({
                "Ticker": runner_alt,
                "ticker": runner_alt,
                "Score": 90,
                "score": 90,
                "Company": company_display,
                "Strategy": "Barbell",
                "Role": "runner",
                "Candidate_label": "Runner Candidate 1",
                "Combo": scenario,
                "Trigger": f"$5K Runner. {BARBELL_RULES}",
                "Signal": lead_signal,
                "Change": f"{lead_change}%",
                "Volume": "—",
                "Sector": info["sector"],
                "Industry": f"Runner Candidate 1. $5K. -5%=$250 max. Target +5-7%. Pick by oversold/catalysts/technicals.",
                "RSI": rsi,
                "leverage": info["leverage"],
            })
        if runner:
            info = _vehicle_info(arsenal, runner)
            rsi = _get_rsi_for_ticker(runner)
            time.sleep(0.15)
            company_display = f"{info['name']} (RSI {int(rsi)}, {info['leverage']})" if rsi is not None else f"{info['name']} ({info['leverage']})"
            results.append({
                "Ticker": runner,
                "ticker": runner,
                "Score": 95,
                "score": 95,
                "Company": company_display,
                "Strategy": "Barbell",
                "Role": "runner",
                "Candidate_label": "Runner Candidate 2" if runner_alt and runner_alt != runner else "Runner Candidate 1",
                "Combo": scenario,
                "Trigger": f"$5K Runner. {BARBELL_RULES}",
                "Signal": lead_signal,
                "Change": f"{lead_change}%",
                "Volume": "—",
                "Sector": info["sector"],
                "Industry": f"Runner Candidate 2. $5K. -5%=$250 max. Target +5-7%. Pick by oversold/catalysts/technicals." if runner_alt and runner_alt != runner else f"Runner Candidate 1. $5K. {BARBELL_RULES}",
                "RSI": rsi,
                "leverage": info["leverage"],
            })
        if results:
            runners = [r["Ticker"] for r in results if r.get("Role") == "runner"]
            progress(f"BARBELL: {scenario} — Foundation {foundation or '—'}, Runners {', '.join(runners)}. Leading: {lead_signal} ({lead_change}%).")
        else:
            results.append({
                "Ticker": "CASH",
                "ticker": "CASH",
                "Score": 50,
                "score": 50,
                "Company": "No trade — Cash is a position",
                "Strategy": "No trade",
                "Role": "avoid",
                "Combo": scenario,
                "Trigger": "No combo for this signal",
                "Signal": lead_signal,
                "Change": f"{lead_change}%",
                "Volume": "—",
                "Sector": "—",
                "Industry": BARBELL_RULES,
            })
            progress(f"No barbell combo for {lead_signal}. Cash.")

    return results
