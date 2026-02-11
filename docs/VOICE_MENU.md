# Voice menu — say "menu" or "give me the menu" to see this

Say the number or the phrase. Example: "5" or "take a screenshot."

---

## Memory and knowledge

1. **Check your brain** — I query RAG and summarize what I know (sessions, regime, context).
2. **Save conversation** — Full chat saved to session_logs and RAG (use when we're done or for daily backup).
3. **Save system knowledge** — Short state snapshot (decisions, regime, open items) saved to RAG, no full transcript.
4. **Backup** / **we're done talking** / **daily backup** — Same as "save conversation."

---

## Screenshots and context

5. **Take a screenshot** — I capture each monitor at full resolution and read the images (errors, UI, browser).
6. **Use clipboard** / **what's on the clipboard** — I read the clipboard and use it as context (no need to paste).
7. **What am I looking at?** — I report the active window title and app (e.g. browser, Cursor).

---

## Time and market

8. **What time is it?** / **Market open?** — I give current time (ET) and whether the US market is open (9:30–4 ET, Mon–Fri).

---

## Scan reports

9. **Create AI report** / **read my scan reports and produce the report** — I find the latest scan JSON, read it, and produce the trading report (MARKET SNAPSHOT, TIER 1/2/3, AVOID, RISK, KEY INSIGHT, TOP 5 PLAYS).

---

## Actions

10. **Open this** — Say "open" plus a URL or file path; I open it in the browser or default app.
11. **Notify me when done** — For a long task, I run it and then show a Windows toast when it's finished.
12. **Add to my todo** — I append the next thing you say to your todo file (e.g. "add to my todo: fix the scanner bug").

---

## Execution and status

13. **Do it** / **keep going** — I run the next steps without extra explanation.
14. **Where we at?** / **What's left?** — Short status or checklist.
15. **Zip on Desktop and Downloads** — I copy the release zip to Desktop and Downloads.

---

## Backup and restore

16. **Full backup** — I run a full backup (agent + session_logs, trade_journal, ChromaDB) so you can restore and pick up where you left off after a crash or on a new PC.
17. **Restore from [path to zip]** — I unzip the backup and place cursor + scanner data so you're set up again.

---

*Say **menu** or **give me the menu** anytime to see this list. You can say the number (e.g. "5") or the phrase.*
