# ============================================================
# PTM Daemon - runs Paper Trading Manager on schedule
# ============================================================
# Cursor project only. Paper trade only. Swing trade only (no same-day exit).
# Start with Windows or run manually. Use --dry to simulate without orders.
# Schedule: 8am-8pm ET weekdays by default (ptm_schedule_* in user_config).

import os
import sys
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

LOG_DIR = os.path.join(BASE_DIR, "ptm_logs")
LOG_FILE = os.path.join(LOG_DIR, "ptm_daemon.log")
INTERVAL_SEC = 900  # 15 minutes (fallback when schedule disabled)
SLEEP_OUTSIDE_WINDOW = 300  # 5 min when outside 8am-8pm


def _get_config():
    try:
        from scan_settings import load_config
        return load_config() or {}
    except Exception:
        return {}


def _get_et_now():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        from datetime import timezone, timedelta
        return datetime.now(timezone(timedelta(hours=-5)))


def _is_in_schedule_window(config: dict) -> bool:
    """True if current ET time is within ptm_schedule_start_hour to ptm_schedule_end_hour, weekdays only."""
    if not config.get("ptm_schedule_enabled"):
        return True  # no schedule = always run
    now = _get_et_now()
    start = int(config.get("ptm_schedule_start_hour", 8))
    end = int(config.get("ptm_schedule_end_hour", 20))
    weekdays_only = config.get("ptm_schedule_weekdays_only", True)
    if weekdays_only and now.weekday() >= 5:
        return False
    return start <= now.hour < end


def _is_at_run_time(config: dict) -> bool:
    """
    If ptm_run_times is set (e.g. ["09:35", "12:00", "15:45"]), only run when current time
    is within 2 min of one of those. Otherwise run whenever in schedule window.
    """
    run_times = config.get("ptm_run_times")
    if not run_times or not isinstance(run_times, (list, tuple)):
        return True  # no specific times = run every cycle
    now = _get_et_now()
    current_minutes = now.hour * 60 + now.minute
    for t in run_times:
        t = str(t).strip()
        if not t:
            continue
        parts = t.replace(".", ":").split(":")
        h = int(parts[0]) if parts else 0
        m = int(parts[1]) if len(parts) > 1 else 0
        target_minutes = h * 60 + m
        if abs(current_minutes - target_minutes) <= 2:
            return True
    return False


def _schedule_interval_sec(config: dict) -> int:
    """Interval in seconds from config, or default."""
    m = config.get("ptm_schedule_interval_min")
    if m is not None and isinstance(m, (int, float)) and m > 0:
        return int(m * 60)
    return INTERVAL_SEC


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def main():
    dry_run = "--dry" in (sys.argv or [])
    run_once = "--run-once" in (sys.argv or [])
    mode = "DRY-RUN" if dry_run else "LIVE (paper only)"
    config = _get_config()
    interval = _schedule_interval_sec(config)
    sched = "enabled" if config.get("ptm_schedule_enabled") else "disabled"
    sh, eh = config.get("ptm_schedule_start_hour", 8), config.get("ptm_schedule_end_hour", 20)
    window = f"{sh}am-{eh % 12 or 12}pm ET" if sched == "enabled" else "24/7"
    run_times = config.get("ptm_run_times", [])
    rt_str = f" | run_times={run_times}" if run_times else ""
    log(f"PTM Daemon started | {mode} | schedule={sched} ({window}) | interval={interval}s{rt_str}")
    log("Paper trade only. Swing trade only (no same-day exit).")

    skip_count = 0
    while True:
        try:
            config = _get_config()
            if not config.get("ptm_enabled"):
                log("PTM disabled (ptm_enabled: false). Sleeping.")
            elif config.get("ptm_schedule_enabled") and not _is_in_schedule_window(config):
                skip_count += 1
                if skip_count == 1 or skip_count % 12 == 0:
                    sh, eh = config.get("ptm_schedule_start_hour", 8), config.get("ptm_schedule_end_hour", 20)
                    log(f"Outside schedule window ({sh}am-{eh}pm ET weekdays). Sleeping.")
            elif not _is_at_run_time(config):
                skip_count += 1
                rt = config.get("ptm_run_times", [])
                if skip_count == 1 or skip_count % 12 == 0:
                    log(f"Not at run time {rt}. Sleeping.")
            else:
                skip_count = 0
                from paper_trading_manager import run_cycle, _ptm_trader2_combined_cycle, _run_ai_reasoning_pass
                # D. AI reasoning pass: recommended action for this cycle (logged to ptm_logs/ai_recommendation.txt)
                rec = _run_ai_reasoning_pass(config)
                if rec:
                    log(f"[AI] Recommendation: {rec[:200]}..." if len(rec) > 200 else f"[AI] Recommendation: {rec}")
                # Trader 1: 3 Stock Rotation (skip if ptm_trader1_enabled false)
                if config.get("ptm_trader1_enabled", True):
                    import paper_trading_manager as _ptm
                    _ptm._current_trader = "T1"
                    out = run_cycle(config=config, dry_run=dry_run)
                    for line in out.strip().split("\n"):
                        log(line)
                else:
                    log("[T1] Trader 1 disabled (ptm_trader1_enabled: false). Skipping.")
                # Trader 2: Combined Rotation+Swing
                if config.get("ptm_trader2_enabled"):
                    import paper_trading_manager as _ptm
                    _ptm._current_trader = "T2"
                    t2_dry = config.get("ptm_trader2_dry_run", True)
                    log(f"[T2] Running Combined Rotation+Swing (dry_run={t2_dry})")
                    t2_out = _ptm_trader2_combined_cycle(config, dry_run=t2_dry)
                    for line in t2_out.strip().split("\n"):
                        log(line)
        except KeyboardInterrupt:
            log("PTM Daemon stopped (Ctrl+C)")
            break
        except Exception as e:
            log(f"Error: {e}")
        if run_once:
            log("PTM run-once complete. Exiting.")
            break
        # Sleep: outside window = 5 min; at run times = 2 min recheck; else interval
        config = _get_config()
        if config.get("ptm_schedule_enabled") and not _is_in_schedule_window(config):
            sleep_sec = SLEEP_OUTSIDE_WINDOW
        elif config.get("ptm_run_times"):
            sleep_sec = 120  # 2 min when using run times (recheck frequently to hit the slot)
        else:
            sleep_sec = _schedule_interval_sec(config)
        time.sleep(sleep_sec)


if __name__ == "__main__":
    main()
