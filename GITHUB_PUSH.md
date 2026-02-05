# ClearBlueSky on GitHub

**Repo:** [https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner](https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner)

## Creating a new release (e.g. v6.4)

1. **Commit and push** your changes to `main` (or your default branch).
2. **Tag:** `git tag -a v6.4 -m "ClearBlueSky v6.4"` then `git push origin v6.4`
3. **Build zip:** `git archive -o ClearBlueSky-6.4.zip v6.4`
4. **Create release with GitHub CLI:**  
   `gh release create v6.4 ClearBlueSky-6.4.zip --title "ClearBlueSky v6.4" --notes-file RELEASE_v6.4.md`

Or create the release on GitHub → Releases → Draft a new release: choose the tag, add title/description, attach the zip.

Your API keys and preferences are only in `app/user_config.json` (not in the repo and not in the zip). Do not commit `user_config.json`, `error_log.txt`, `app/rag_store/`, or `app/backtest_signals.db`.
