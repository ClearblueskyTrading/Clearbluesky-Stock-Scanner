# Alpaca Integration – Data-Only (Archived)

**Status:** Paper-trade flow was removed. Alpaca is used **only for data** (prices, volume).

---

## Current Use

- **Alpaca Data API** – With API key and secret in Settings, the scanner uses Alpaca for live price and volume data.
- **Config:** `alpaca_api_key`, `alpaca_secret_key` in Settings and `scan_settings.py` / `user_config.json`.
- **Rate limits:** 60/min, 3/sec (see `.cursor/rules/alpaca-rate-limits.mdc`).

---

## Removed (Previously Planned)

- Paper-trade approval flow after reports
- Alpaca Trading API integration (`alpaca_client.py`, `alpaca_trades_storage.py`)
- Paper-trade dashboard
- `alpaca_integration_enabled` toggle
- `alpaca_trades.json` storage

---

## Original Vision (for reference)

The original plan proposed:
1. Paper-only: approve best setups from report → submit to Alpaca → dashboard in app.
2. Later: live account option.
3. Later: automated trade app with approvals only.

This is archived; the app is data-only for Alpaca today.
