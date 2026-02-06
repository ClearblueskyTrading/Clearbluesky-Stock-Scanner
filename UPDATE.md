# ClearBlueSky – Updates & Versioning

## In-app updater (v7.0+)

- **Update** – Backs up your current version, then downloads and applies the latest release from GitHub. **Your `user_config.json` is never overwritten** (API keys and preferences are kept).
- **Rollback** – If an update causes issues, use **Rollback** to restore the previous version from the backup. **Your current `user_config.json` is kept** when you rollback.
- **Where** – In the app: **Update** and **Rollback** buttons (below Settings / Help). Rollback is only available after you have run an update at least once (a backup is created before each update).

Backups are stored in `app/update_backups/`. The updater uses the GitHub release source zip (tag `v7.0`, `v7.1`, etc.) and applies only the `app/` folder contents; root files (README, INSTALL.bat, etc.) are in the repo—re-download the full release zip if you need to refresh those.

---

## Versioning (from v7.0 onward)

- **v7.0** – Base release with queue-based scans, Run all scans, Swing (emotional dips), Watchlist, Velocity Barbell, Insider, Pre-Market, **Velocity Pre-Market Hunter**, in-app **Update** and **Rollback**, and update docs.
- **v7.1, v7.2, …** – Strict incremental versions for all future releases. Each release will be tagged on GitHub as `v7.1`, `v7.2`, etc., and the in-app updater will offer the latest when it’s newer than your installed version.

When you **Update** from the app, you get the latest release (e.g. 7.1 or 7.2). When you **Rollback**, you return to the version you had before that update (e.g. back to 7.0).

---

## Manual update (optional)

If you prefer not to use the in-app updater:

1. Download the latest release zip from [GitHub Releases](https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases).
2. Extract and copy files over your install, but **do not overwrite** `app/user_config.json` (keep your existing file).
3. Restart the app.

---

*ClearBlueSky – made with Claude AI*
