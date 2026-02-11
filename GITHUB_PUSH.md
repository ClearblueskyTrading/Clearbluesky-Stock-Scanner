# ClearBlueSky on GitHub

**Repo:** [https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner](https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner)

---

## Project boundaries

- **Scanner app (GitHub)** — The repo is the scanner project only: app code, INSTALL, Docker, release notes, scanner docs. No `.cursor/`, no `scripts/`, no voice/agent tooling. What you clone from GitHub is just the scanner.
- **Cursor project (local)** — This workspace is the full Cursor project: the scanner app **plus** Cursor rules, `scripts/` (e.g. TakeScreenshot), `.cursor/`, and any other agent/voice/local tooling. It stays local and is not pushed to GitHub.

Going forward: keep the scanner app as a separate project on GitHub, and the Cursor project (this workspace) separate. Changes that belong only in the Cursor project (rules, scripts, local docs) are not committed to the scanner repo.

---

## Why the Cursor agent can't run `git push` (and how to fix it)

With **GitHub MFA (2FA) required**, Git over HTTPS may prompt for a Personal Access Token (PAT) or open a browser. The Cursor agent runs commands in a **non-interactive** environment with a **time limit** (~60s), so it cannot:

- Type a password or PAT when prompted
- Complete a browser login or MFA step
- Wait for you to approve a device flow

So when the agent runs `git push`, the command often **times out** or hangs waiting for credentials.

**Official GitHub docs:** [Accessing GitHub using two-factor authentication](https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/accessing-github-using-two-factor-authentication) — for the command line you use either a **token (PAT)** or **SSH**; 2FA does not change SSH behavior.

**Ways to make pushes work without prompts (so you can push from your terminal, and in some setups the agent might succeed if credentials are cached):**

1. **SSH (recommended)**  
   - Add an SSH key to your GitHub account: [Connecting to GitHub with SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh).  
   - Switch the remote to SSH and push from your machine once:
     ```bash
     git remote set-url origin git@github.com:ClearblueskyTrading/Clearbluesky-Stock-Scanner.git
     git push origin main
     ```
   - After that, `git push` uses the key and does **not** ask for MFA. If the agent runs in the same user context with the same SSH key available (e.g. ssh-agent), it might be able to push; otherwise you continue to push from your terminal.

2. **HTTPS + Personal Access Token (PAT)**  
   - Create a PAT: [Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) (use it as the “password” when Git asks).  
   - Use [Git Credential Manager](https://github.com/GitCredentialManager/git-credential-manager) (or `git config credential.helper store`) so the PAT is cached after you enter it once in your terminal.  
   - Then `git push` from your terminal won’t prompt every time. The agent might still not have access to that cached credential depending on how Cursor runs the shell.

**Bottom line:** You must run `git push` (and any tag push) from **your** terminal so you can complete MFA or enter the PAT once. After switching to SSH or caching a PAT, your own pushes are non-interactive. The agent can still run tag creation, build the zip, and prepare release notes; only the actual push to GitHub needs to be done by you.

---

## Creating a new release (e.g. v6.5)

1. **Commit and push** your changes to `main` (or your default branch).
2. **Tag:** `git tag -a v6.5 -m "ClearBlueSky v6.5"` then `git push origin v6.5`
3. **Build zip:** `git archive -o ClearBlueSky-6.5.zip v6.5`
4. **Create release with GitHub CLI:**  
   `gh release create v6.5 ClearBlueSky-6.5.zip --title "ClearBlueSky v6.5" --notes-file RELEASE_v6.5.md`

Or create the release on GitHub → Releases → Draft a new release: choose the tag, add title/description, attach the zip.

**No APIs or user config in the release:** API keys and preferences are only in `app/user_config.json` (not in the repo and not in the zip). Do not commit `user_config.json`, `error_log.txt`, `app/rag_store/`, or `app/backtest_signals.db`. Installer does not copy `user_config.json`; first run creates a blank config.
