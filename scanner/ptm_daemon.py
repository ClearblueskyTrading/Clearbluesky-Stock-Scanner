# ============================================================
# PTM Daemon - runs Paper Trading Manager every 5 minutes
# ============================================================
# Cursor project only. Paper trade only. Swing trade only (no same-day exit).
# Start with Windows or run manually. Use --dry to simulate without orders.

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
INTERVAL_SEC = 900  # 15 minutes


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
    mode = "DRY-RUN" if dry_run else "LIVE (paper only)"
    log(f"PTM Daemon started | {mode} | interval={INTERVAL_SEC}s")
    log("Paper trade only. Swing trade only (no same-day exit).")

    while True:
        try:
            from paper_trading_manager import run_cycle, _get_config
            config = _get_config()
            if not config.get("ptm_enabled"):
                log("PTM disabled (ptm_enabled: false). Sleeping.")
            else:
                out = run_cycle(config=config, dry_run=dry_run)
                for line in out.strip().split("\n"):
                    log(line)
        except KeyboardInterrupt:
            log("PTM Daemon stopped (Ctrl+C)")
            break
        except Exception as e:
            log(f"Error: {e}")
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
