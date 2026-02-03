# ClearBlueSky on GitHub

**Repo:** [https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner](https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner)

Code and tag **v6.0** have been pushed. To add a downloadable release:

---

## 3. Create the v6.0 release and attach the zip

1. On GitHub, open your repo → **Releases** → **Create a new release**
2. **Choose a tag:** select **v6.0**
3. **Release title:** `ClearBlueSky v6.0`
4. **Describe:** paste from RELEASE_v6.0.md or write a short summary
5. **Attach:** drag and drop **ClearBlueSky-6.0.zip**  
   (from `d:\cursor\ClearBlueSky-6.0.zip` or `C:\Users\EricR\ClearBlueSky-6.0.zip`)
6. Click **Publish release**

---

## Optional: use your own name/email in the commit

```bash
cd d:\cursor
git config user.name "Your Name"
git config user.email "your@email.com"
git commit --amend --no-edit --reset-author
git push --force origin main
```

Then re-push the tag if you already created the release:

```bash
git tag -d v6.0
git tag -a v6.0 -m "ClearBlueSky v6.0"
git push origin :refs/tags/v6.0
git push origin v6.0
```

---

Done. Your API key is only in `app/user_config.json` (not in the repo and not in the zip).
