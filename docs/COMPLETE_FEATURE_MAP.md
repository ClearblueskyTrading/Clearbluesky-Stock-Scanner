# Feature Map - How Everything Works Now

## Current System Architecture

```
You (voice/type) 
  ↓
Cursor Agent (with 7 MCPs)
  ↓
Actions: Trading, Scanning, Memory, Browser, Files
  ↓
Outputs: Orders, Reports, Knowledge Graph, Screenshots
```

---

## 1. SCANNING & RESEARCH

### Existing Features ✅

| Feature | How It Works | Status |
|---------|--------------|--------|
| **ClearBlueSky Scanner** | `python d:\cursor\app\app.py` (GUI) or `scanner_cli.py --scan <type>` | ✅ Working |
| **3 Scanner Types** | Velocity (momentum), Swing (dips), Watchlist | ✅ Working |
| **CLI Automation** | `python scanner_cli.py --scan velocity` | ✅ Working |
| **PDF Reports** | Auto-generated with OpenRouter AI analysis | ✅ Working |
| **Reports Storage** | `d:\cursor\app\reports\` | ✅ Working |

### How It Works NOW
```
You: "Run velocity scan"
  ↓
Agent runs: scanner_cli.py --scan velocity
  ↓
Output: app/reports/Velocity_Scan_20260212_HHMMSS.json + .pdf + _ai.txt
  ↓
Agent reads results, shows you top picks
```

### New Desktop Panel Buttons
- Row 0: Scanner GUI, Velocity, Swing, Watchlist, Reports folder
- Quick links: Finviz, TradingView, MarketWatch, Schwab, Yahoo

---

## 2. TRADING EXECUTION

### Existing Features ✅

| Feature | How It Works | Status |
|---------|--------------|--------|
| **Alpaca Paper Trading** | Via Alpaca MCP - account, positions, orders, quotes | ✅ Working |
| **Voice Commands** | "Check my positions", "Buy X shares of AAPL" | ✅ Available (needs testing) |

### New Features 🆕

| Feature | How It Works | Status |
|---------|--------------|--------|
| **Swing Dip Strategy** | `python alpaca_swing_dip_strategy.py` (automated) | 🆕 Created - needs testing tomorrow |
| **Strategy Tracker** | `app/swing_dip_tracker.json` logs entries/exits | 🆕 Auto-created by strategy |
| **Scheduled Trading** | Buys at 2:55pm, sells 8am-2pm automatically | 🆕 Tomorrow's test |

### How It Works NOW

**Manual Trading:**
```
You: "What's my buying power?"
  ↓
Agent → Alpaca MCP → get_account_info
  ↓
Agent: "Your Alpaca paper account has $200,000 buying power"

You: "Buy 10 shares of AAPL at market"
  ↓
Agent → Alpaca MCP → place_stock_order
  ↓
Agent: "Order filled: 10 AAPL @ $175.30"
```

**Automated Strategy (NEW):**
```
You start: python alpaca_swing_dip_strategy.py
  ↓
Script runs 24/7, checking schedule
  ↓
2:55pm: Scans for dips, buys top 3
  ↓
8am-2pm next day: Checks every 15 min, exits at 2.5% profit
  ↓
Logs all trades to swing_dip_tracker.json
```

### New Desktop Panel Buttons
- Row 1: Alpaca dashboard, Positions, Orders, Account, Bars, Watchlist, Buy, Sell, Close All, Refresh
- Row 2: Start/Stop strategy, View log, Edit params, Backtest, Docs, Test scan

---

## 3. MEMORY & KNOWLEDGE

### Existing Features ✅

| Feature | How It Works | Status |
|---------|--------------|--------|
| **Check Your Brain** | Query Velocity RAG (ChromaDB) over session logs + docs | ✅ Working |
| **Save Conversation** | Write full chat to session_logs/, reindex RAG | ✅ Working |
| **Session Logs** | `velocity_memory/session_logs/*.md` | ✅ Working |
| **ChromaDB** | `velocity_memory/chroma_db/chroma.sqlite3` | ✅ Working |
| **Full Backup** | `Build-AgentBackup.ps1 -Full` → zip with everything | ✅ Working |

### New Features 🆕

| Feature | How It Works | Status |
|---------|--------------|--------|
| **Memory MCP** | Persistent knowledge graph (entities, relations) | 🆕 Installed, populated |
| **Knowledge Graph** | 25 entities: You, Scanner, MCPs, Strategies, Tools | 🆕 Created today |
| **Cross-Session Memory** | Memory MCP survives restarts (vs ChromaDB = current session) | 🆕 Ready |

### How It Works NOW

**Velocity RAG (Existing):**
```
You: "check your brain"
  ↓
Agent runs: python velocity_memory/velocity_rag.py --query "recent context"
  ↓
Searches: session_logs/*.md + indexed docs
  ↓
Agent: "Here's what I know from past sessions..."
```

**Memory MCP (NEW):**
```
You: "What MCPs do I have?"
  ↓
Agent → Memory MCP → search_nodes("MCP")
  ↓
Agent: "You have 11 MCPs: Alpaca, GitHub, yfinance..."
  (persists across restarts)
```

**Combined:**
- **Memory MCP** = structured facts (entities, relationships)
- **Velocity RAG** = full conversation history, deep context

### New Desktop Panel Buttons
- Row 3: Check brain, Save conv, Memory graph, Search memory, Session logs, Full backup, RAG store, Reindex, Docs, MCPs

---

## 4. SYSTEM & TOOLS

### Existing Features ✅

| Feature | How It Works | Status |
|---------|--------------|--------|
| **Screenshot** | `TakeScreenshot.ps1` - multi-monitor capture | ✅ Working |
| **Clipboard** | `GetClipboard.ps1` - read clipboard text | ✅ Working |
| **Active Window** | `GetActiveWindow.ps1` - focused app/title | ✅ Working |
| **Time/Market** | `GetTimeAndMarket.ps1` - current time + market status | ✅ Working |
| **Desktop GUI** | `AgentGUI.ps1` - click-button panel | ✅ Working (just upgraded) |
| **Full Backup** | `Build-AgentBackup.ps1 -Full` - zip everything | ✅ Working |
| **Restore** | `RestoreFromZip.ps1` - restore from backup | ✅ Working |

### New Features 🆕

| Feature | How It Works | Status |
|---------|--------------|--------|
| **Playwright MCP** | Browser automation (navigate, click, fill forms) | 🆕 Installed, tested on Schwab |
| **Fetch MCP** | Fetch URLs → Markdown conversion | 🆕 Installed |
| **Filesystem MCP** | Direct file read/write in workspace | 🆕 Installed |
| **Sequential Thinking MCP** | Step-by-step reasoning for complex problems | 🆕 Installed, used today |
| **Screenshot MCP** | Webpage screenshots (Puppeteer) | 🆕 Installed |
| **OpenAPI MCP** | REST API integration (currently Petstore demo) | 🆕 Installed |

### How It Works NOW

**PowerShell Scripts (Existing):**
```
You: "take a screenshot"
  ↓
Agent runs: TakeScreenshot.ps1
  ↓
Saves: screenshots/capture_YYYYMMDD_HHMMSS_1.png (per monitor)
  ↓
Agent reads images and analyzes
```

**Playwright MCP (NEW):**
```
You: "Test Schwab order entry"
  ↓
Agent → Playwright MCP → navigate, fill form, screenshot
  ↓
Agent: "Filled username 'erunkel' successfully"
```

**Filesystem MCP (NEW):**
```
You: "What's in my workspace?"
  ↓
Agent → Filesystem MCP → directory_tree("d:\cursor")
  ↓
Agent shows complete folder structure
```

### New Desktop Panel Buttons
- Row 4: Screenshot, Clipboard, Active Win, Time/Market, Notify, Workspace, Rules, Scripts, Screenshots folder, Notepad
- Row 5: Menu, Help, Restart, Debug, Status, Performance, Goals, Learn, Predict, ChatGPT

---

## 5. MCPs (DATA & INTEGRATION)

### Existing MCPs ✅

| MCP | What It Does | How You Use It |
|-----|--------------|----------------|
| **Alpaca** | Trading, quotes, positions, orders | "Check positions", "Buy 10 AAPL" |
| **GitHub** | Repos, issues, PRs, code search | "List my repos", "Create PR" |
| **yfinance** | Yahoo Finance data (stocks, news, history) | "Get AAPL info", "Show NVDA news" |
| **MarkItDown** | Convert docs/URLs to Markdown | "Convert this PDF", "Fetch this URL" |

### New MCPs 🆕

| MCP | What It Does | How You Use It |
|-----|--------------|----------------|
| **Playwright** | Browser automation | "Navigate to Schwab", "Fill this form" |
| **Fetch** | Web scraping → Markdown | "Fetch this article", "Get webpage content" |
| **Memory** | Knowledge graph (persistent) | "What do you know about X?", "Show memory graph" |
| **Filesystem** | File operations in workspace | "List files in app/", "Read this config" |
| **Sequential Thinking** | Step-by-step reasoning | Auto-used for complex problems |
| **Screenshot** | Webpage screenshots | "Screenshot this page" |
| **OpenAPI** | REST APIs | (Reserved for Schwab API if needed later) |

### How It Works NOW

**Example - Multi-MCP Workflow:**
```
You: "Analyze NVDA and place an order"
  ↓
1. Agent → yfinance MCP → get_ticker_info("NVDA")
   Shows: Price, PE, fundamentals
  ↓
2. Agent → Alpaca MCP → get_stock_latest_quote("NVDA")
   Shows: Real-time bid/ask
  ↓
3. Agent → Memory MCP → search_nodes("NVDA")
   Shows: Past trades, notes about NVDA
  ↓
4. Agent analyzes, recommends action
  ↓
5. You: "Buy 10 shares"
  ↓
6. Agent → Alpaca MCP → place_stock_order
   Order filled
  ↓
7. Agent → Memory MCP → add_observation("NVDA trade placed at $875")
```

---

## 6. COMPLETE WORKFLOW EXAMPLES

### Morning Routine

```
8:00am - You arrive at desk

Desktop Agent Panel (click):
  → "🧠 Check Brain" → Paste in Cursor
  
Agent: 
  - Queries Memory MCP (trading setup, strategies)
  - Queries Velocity RAG (recent sessions, decisions)
  - Shows: "Yesterday you ran swing scan, found 3 dips, planning to paper trade this week"

You: "What's the market looking like?"
  
Agent → yfinance MCP → Gets SPY, QQQ data
Agent: "SPY up 0.5% premarket, NVDA earnings today..."

Desktop Panel (click):
  → "🔍 Velocity" (runs scanner)
  
Scanner outputs to app/reports/
Agent reads results: "Top 5 momentum plays: NVDA, MSFT, AAPL..."
```

### Trading Session

```
2:55pm - Swing dip strategy time

Desktop Panel (click):
  → "▶️ Start Swing" (launches strategy script)
  
Strategy runs:
  - Scans for stocks down 2-5%
  - Filters: above 50-day MA, high volume
  - Buys top 3 dips in Alpaca paper account
  
You get notification: "Bought dips: MSFT, AAPL, NVDA"

Next morning 8:00am:
  Strategy auto-checks positions every 15 min
  Exits at 2.5% profit or 2pm
  
Desktop Panel (click):
  → "📈 Strategy Log" (opens tracker.json)
  
See: Entry/exit prices, profit%, timestamps

You: "How did the strategy do?"
  
Agent reads tracker:
  "3 trades: MSFT +2.5% ✅, AAPL +2.6% ✅, NVDA +1.2% (held to 2pm) ✅"
```

### Evening Wrap-Up

```
5:00pm - End of day

You: "Analyze today's performance"
  
Agent:
  - Alpaca MCP → get positions, closed orders
  - Memory MCP → compare to past days
  - Shows: P&L, win rate, notes

Desktop Panel (click):
  → "💾 Save Conv" → Paste in Cursor
  
Agent:
  - Writes full conversation to session_logs/
  - Runs velocity_rag.py to reindex
  - Updates Memory MCP with today's learnings
  
Agent: "Saved to session logs and reindexed RAG"

Desktop Panel (click):
  → "💾 Full Backup" (runs Build-AgentBackup.ps1)
  
Creates zip:
  - All rules, scripts, docs
  - session_logs/
  - chroma_db/
  - Knowledge graph (Memory MCP)
```

---

## 7. VOICE COMMAND FLOW

### How Keywords Work

**You have 8 Cursor rules files:**
- `keyword-triggers.mdc` - Main command list
- `screenshot-trigger.mdc` - Screenshot behavior
- `conversation-backup.mdc` - Save/backup triggers
- `alpaca-rate-limits.mdc` - API usage limits
- `trade-discussion-sources.mdc` - Data source priority
- `project-boundaries.mdc` - What agent can/can't do
- `pre-commit-security.mdc` - Security checks
- `agent-helpers.mdc` - General guidance

**When you say a keyword:**
```
You: "check your brain"
  ↓
keyword-triggers.mdc activates
  ↓
Agent knows: Query RAG + Memory MCP
  ↓
Agent runs both, combines results
  ↓
Shows you comprehensive context
```

### Current Keyword Triggers ✅

| Keyword | What Happens | Files Involved |
|---------|--------------|----------------|
| **menu** | Show voice menu | keyword-triggers.mdc |
| **check your brain** | Query RAG + Memory MCP | keyword-triggers.mdc, velocity_rag.py |
| **save conversation** | Write to session_logs, reindex | conversation-backup.mdc |
| **take a screenshot** | Capture monitors, agent reads | screenshot-trigger.mdc, TakeScreenshot.ps1 |
| **use clipboard** | Read clipboard content | keyword-triggers.mdc, GetClipboard.ps1 |
| **what am I looking at** | Get active window | keyword-triggers.mdc, GetActiveWindow.ps1 |
| **what time is it** | Time + market status | keyword-triggers.mdc, GetTimeAndMarket.ps1 |
| **gui please** | Launch Desktop Agent panel | keyword-triggers.mdc, AgentGUI.ps1 |
| **open [URL/path]** | Open in browser/app | keyword-triggers.mdc |

---

## 8. DATA FLOW DIAGRAM

### Current Data Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    YOU (Trader)                         │
│  Voice: Win+H | Type in Cursor | Desktop Panel Clicks   │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│              Cursor Agent (Claude 4.5)                  │
│   Rules: .cursor/rules/*.mdc                            │
│   Scripts: scripts/*.ps1                                │
└─────────┬─────────────────────────────┬─────────────────┘
          ↓                             ↓
┌─────────────────────┐     ┌──────────────────────────┐
│   MCPs (11 total)   │     │  Local Scripts (7)       │
├─────────────────────┤     ├──────────────────────────┤
│ • Alpaca            │     │ • TakeScreenshot.ps1     │
│ • GitHub            │     │ • GetClipboard.ps1       │
│ • yfinance          │     │ • GetActiveWindow.ps1    │
│ • MarkItDown        │     │ • GetTimeAndMarket.ps1   │
│ • Playwright        │     │ • AgentGUI.ps1           │
│ • Fetch             │     │ • Build-AgentBackup.ps1  │
│ • Memory (NEW)      │     │ • RestoreFromZip.ps1     │
│ • Filesystem (NEW)  │     └──────────────────────────┘
│ • Seq. Think (NEW)  │
│ • Screenshot (NEW)  │
│ • OpenAPI (NEW)     │
└─────────┬───────────┘
          ↓
┌─────────────────────────────────────────────────────────┐
│                  Data Sources                           │
├─────────────────────────────────────────────────────────┤
│ • Alpaca API (trading, quotes, bars)                    │
│ • Yahoo Finance (fundamentals, news)                    │
│ • finviz (screening data)                               │
│ • SEC Edgar (insider filings)                           │
│ • OpenRouter AI (report generation)                     │
└─────────┬───────────────────────────┬───────────────────┘
          ↓                           ↓
┌──────────────────────┐   ┌─────────────────────────────┐
│  ClearBlueSky App    │   │  Knowledge Storage          │
├──────────────────────┤   ├─────────────────────────────┤
│ • app.py (GUI)       │   │ • Velocity RAG (ChromaDB)   │
│ • scanner_cli.py     │   │   - session_logs/*.md       │
│ • 3 scanners         │   │   - chroma.sqlite3          │
│ • PDF reports        │   │                             │
│                      │   │ • Memory MCP Knowledge Graph│
│ Outputs:             │   │   - Entities (25)           │
│ • app/reports/*.json │   │   - Relations (26)          │
│ • app/reports/*.pdf  │   │   - Persistent across       │
│ • app/reports/*_ai   │   │     restarts                │
└──────────────────────┘   └─────────────────────────────┘
```

---

## 9. DESKTOP AGENT PANEL GRID (10x10)

### Current Layout

**Row 0: Scanner & Research (Blue)**
```
[Scanner GUI] [Velocity] [Swing] [Watchlist] [Reports]
[Finviz] [TradingView] [MarketWatch] [Schwab] [Yahoo]
```

**Row 1: Alpaca Trading (Green)**
```
[Alpaca Web] [Positions] [Orders] [Account] [Bars]
[Watchlist] [Buy] [Sell] [Close All] [Refresh]
```

**Row 2: Swing Dip Strategy (Orange)**
```
[Start Swing] [Stop Swing] [Strategy Log] [Edit Params] [Backtest]
[Strategy Doc] [Config] [Test Run] [Check Dips] [Signals]
```

**Row 3: Memory & Knowledge (Purple)**
```
[Check Brain] [Save Conv] [Memory Graph] [Search] [Session Logs]
[Full Backup] [RAG Store] [Reindex] [Docs] [MCPs]
```

**Row 4: System & Tools (Dark)**
```
[Screenshot] [Clipboard] [Active Win] [Time/Market] [Notify]
[Workspace] [Rules] [Scripts] [Screenshots] [Notepad]
```

**Row 5: Quick Actions (Dark)**
```
[Menu] [Help] [Restart] [Debug] [Status]
[Performance] [Goals] [Learn] [Predict] [Chat]
```

**Rows 6-9: Reserved (40 buttons)**
```
[⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜]
[⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜]
[⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜]
[⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜] [⬜]
```

---

## 10. COMPLETE FEATURE STATUS

### Core Features (17) ✅

| Feature | Implementation | Status |
|---------|----------------|--------|
| Voice commands | Cursor rules | ✅ Working |
| Multi-monitor screenshots | TakeScreenshot.ps1 | ✅ Working |
| Clipboard access | GetClipboard.ps1 | ✅ Working |
| Active window detection | GetActiveWindow.ps1 | ✅ Working |
| Time & market status | GetTimeAndMarket.ps1 | ✅ Working |
| Desktop GUI panel | AgentGUI.ps1 (10x10 grid) | ✅ Updated today |
| ClearBlueSky scanners (3) | app.py, scanner_cli.py | ✅ Working |
| PDF reports with AI | report_generator.py | ✅ Working |
| Alpaca trading | Alpaca MCP | ✅ Working |
| Alpaca paper trading | Alpaca MCP | ✅ Active |
| Velocity RAG | ChromaDB + velocity_rag.py | ✅ Working |
| Session backup | conversation-backup.mdc | ✅ Working |
| Full backup/restore | Build-AgentBackup.ps1 | ✅ Working |
| GitHub integration | GitHub MCP | ✅ Working |
| Yahoo Finance data | yfinance MCP | ✅ Working |
| Document conversion | MarkItDown MCP | ✅ Working |
| Browser automation | Playwright MCP | ✅ Installed |

### New Features (7) 🆕

| Feature | Implementation | Status |
|---------|----------------|--------|
| Swing Dip Strategy | alpaca_swing_dip_strategy.py | 🆕 Ready to test tomorrow |
| Memory knowledge graph | Memory MCP | 🆕 Installed, 25 entities created |
| Filesystem operations | Filesystem MCP | 🆕 Installed, tested |
| Sequential reasoning | Sequential Thinking MCP | 🆕 Installed, used |
| Web scraping | Fetch MCP | 🆕 Installed |
| Webpage screenshots | Screenshot MCP | 🆕 Installed |
| REST API integration | OpenAPI MCP | 🆕 Installed (Petstore demo) |

### Testing Tomorrow (1) 🔜

| Feature | Plan |
|---------|------|
| Swing Dip Strategy paper trading | Install deps, run script, monitor for 1 week |

---

## 11. HOW TO USE EVERYTHING

### Method 1: Voice Commands (Fastest)
```
Win+H (Windows voice input)
Say: "check your brain"
Agent responds with context
```

### Method 2: Desktop Panel (Visual)
```
Run: d:\cursor\scripts\AgentGUI.ps1
Click button (copies command)
Paste in Cursor
```

### Method 3: Direct Chat (Natural)
```
Type in Cursor: "Show me NVDA analysis"
Agent uses MCPs to gather data
Agent presents analysis
```

### Method 4: Automated (Set & Forget)
```
Start: python alpaca_swing_dip_strategy.py
Runs 24/7 on schedule
Trades automatically
Check tracker.json for results
```

---

## Summary: Before vs After

### BEFORE (What You Had)
- ✅ ClearBlueSky scanner
- ✅ Alpaca MCP (paper trading)
- ✅ Velocity RAG (session memory)
- ✅ Desktop Agent GUI (6 buttons)
- ✅ PowerShell scripts (screenshots, etc.)
- ✅ 4 MCPs (Alpaca, GitHub, yfinance, MarkItDown)

### AFTER (What You Have Now)
- ✅ Everything above PLUS:
- 🆕 **7 new MCPs** (Playwright, Fetch, Memory, Filesystem, Sequential Thinking, Screenshot, OpenAPI)
- 🆕 **Memory knowledge graph** (persistent entities & relations)
- 🆕 **Swing Dip Strategy** (automated paper trading)
- 🆕 **Desktop GUI 10x10** (100 buttons, 60 active)
- 🆕 **Schwab browser automation** (tested username entry)
- 🆕 **Complete documentation** (TOMORROW_PLAN.md, feature maps)

### TOMORROW
- 🔜 Test Swing Dip Strategy (paper trade)
- 🔜 Monitor results for 1 week
- 🔜 Go live if results good

---

## Quick Reference Card

**Print this or keep handy:**

| I want to... | Say/Do |
|--------------|--------|
| See all commands | "menu" |
| Run scanner | Click "Velocity" in panel OR "run velocity scan" |
| Check positions | Click "Positions" OR "check my positions" |
| Place trade | "Buy 10 AAPL at market" |
| Start auto strategy | Click "▶️ Start Swing" |
| See past context | "check your brain" |
| Take screenshot | "take a screenshot" OR Click "📷 Screenshot" |
| Save session | "save conversation" |
| Backup everything | Click "💾 Full Backup" |
| Open GUI | Run `GUI_PLEASE.bat` OR "gui please" |

---

**Everything is now mapped and documented!** Test the panel with `GUI_PLEASE.bat` or `powershell d:\cursor\scripts\AgentGUI.ps1`
