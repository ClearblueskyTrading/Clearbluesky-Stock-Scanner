# ClearBlueSky on GitHub

**Repo:** [https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner](https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner)

## Creating a new release (e.g. v6.3)

1. **Commit and push** your changes to `main`.
2. **Tag:** `git tag -a v6.3 -m "ClearBlueSky v6.3"` then `git push origin v6.3`
3. **Build zip:** `git archive -o ClearBlueSky-6.3.zip v6.3`
4. **Create release with GitHub CLI:**  
   `gh release create v6.3 ClearBlueSky-6.3.zip --title "ClearBlueSky v6.3" --notes-file RELEASE_v6.3.md`

Or create the release on GitHub → Releases → Draft a new release: choose the tag, add title/description, attach the zip.

Your API key is only in `app/user_config.json` (not in the repo and not in the zip).
