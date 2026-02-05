# ClearBlueSky on GitHub

**Repo:** [https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner](https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner)

## Creating a new release (e.g. v6.5)

1. **Commit and push** your changes to `main` (or your default branch).
2. **Tag:** `git tag -a v6.5 -m "ClearBlueSky v6.5"` then `git push origin v6.5`
3. **Build zip:** `git archive -o ClearBlueSky-6.5.zip v6.5`
4. **Create release with GitHub CLI:**  
   `gh release create v6.5 ClearBlueSky-6.5.zip --title "ClearBlueSky v6.5" --notes-file RELEASE_v6.5.md`

Or create the release on GitHub → Releases → Draft a new release: choose the tag, add title/description, attach the zip.

**No APIs or user config in the release:** API keys and preferences are only in `app/user_config.json` (not in the repo and not in the zip). Do not commit `user_config.json`, `error_log.txt`, `app/rag_store/`, or `app/backtest_signals.db`. Installer does not copy `user_config.json`; first run creates a blank config.
