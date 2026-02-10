# ClearBlueSky Stock Scanner — v7.82 Release Notes

**Release Date:** February 9, 2026

---

## Unified AI Prompt & Experienced-Trader Output

### Same Prompt Everywhere

The PDF, JSON `instructions`, and AI analysis (GUI + CLI) now all use the **same** `MASTER_TRADING_REPORT_DIRECTIVE`. When you send the 3 files (PDF, JSON, _ai.txt) to any AI, they see identical instructions.

- **report_generator.py** — Single source of truth for the directive
- **app.py** — Uses `analysis_package.instructions` as system prompt (no separate short prompt)
- **scanner_cli.py** — Same

### Output Format for Experienced Traders

The directive now targets an experienced trader. Output includes:

| Section | What's New |
|---------|------------|
| **Per-pick** | R:R ratio, Invalidation level, Timing (when to enter), Catalyst (priced in or fresh?) |
| **Market snapshot** | Regime, trade implication (e.g. "tight stops mandatory") |
| **Tier 3** | Correlation notes (e.g. "Trades with NVDA/SEMIs") |
| **Risk management** | Conviction-based sizing ($2K/$5K/$10K), regime-aware |
| **Avoid list** | Why to avoid — prevents FOMO |

### Structure

- 📊 MARKET SNAPSHOT
- 🎯 TIER 1: ELITE SETUPS (90+)
- 🎯 TIER 2: STRONG SETUPS (85-90)
- 🎯 TIER 3: TACTICAL PLAYS (75-85)
- ❌ AVOID LIST (categorized)
- ⚠️ RISK MANAGEMENT
- 📈 KEY INSIGHT
- TOP 5 PLAYS

### Release Zip Security

- Excludes `mcp.json`, `.env` (may contain API keys)
- Excludes older release notes (keeps last 2 versions)

### Upgrade

Drop-in replacement — no config changes needed. Your `user_config.json` is never overwritten.

---

*ClearBlueSky Stock Scanner — Built with Claude AI*
*GitHub: https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner*
