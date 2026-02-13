# Desktop Agent Panel - Updated 10x10 Grid

## What's New

Complete redesign with **10x10 button grid** (100 buttons total) organized by function:

### Row 0: Scanner & Research (Blue)
- Scanner GUI, Velocity, Swing Dips, Watchlist scans
- Reports folder
- Quick links: Finviz, TradingView, MarketWatch, Schwab, Yahoo Finance

### Row 1: Alpaca Trading (Green)
- Alpaca web dashboard
- Positions, Orders, Account status
- Stock bars, Watchlists
- Buy/Sell quick commands
- Close all, Refresh P&L

### Row 2: Swing Dip Strategy (Orange)
- Start/Stop strategy
- View strategy log
- Edit parameters
- Backtest analysis
- Strategy documentation
- Test scans, Check dips, View signals

### Row 3: Memory & Knowledge (Purple)
- Check your brain
- Save conversation
- Memory graph, Search memory
- Session logs, Full backup
- RAG store, Reindex
- Docs folder, MCP config

### Row 4: System & Tools (Dark)
- Screenshot, Clipboard
- Active window, Time/Market
- Notification test
- Workspace, Rules, Scripts folders
- Screenshots folder, Notepad

### Row 5: Quick Actions (Dark)
- Menu, Help, Restart
- Debug, Status, Performance
- Goals, Learn, Predict
- ChatGPT link

### Rows 6-9: Reserved (40 buttons)
- Available for future features
- Easy to add custom buttons

## How Buttons Work

**Two types:**

1. **Action buttons** - Launch apps, open folders, run scripts
2. **Clipboard buttons** - Copy command to clipboard, paste in Cursor

Most agent commands use **clipboard** method:
- Click button
- Command copied to clipboard
- Popup tells you what was copied
- Paste in Cursor chat

## Color Coding

- 🔵 **Blue** - Scanner & Research
- 🟢 **Green** - Trading & Alpaca
- 🟠 **Orange** - Strategy & Automation
- 🟣 **Purple** - Memory & Knowledge
- ⚫ **Dark** - System & Tools

## Launch It

```powershell
d:\cursor\scripts\AgentGUI.ps1
```

Or via batch file:
```
d:\cursor\scripts\GUI_PLEASE.bat
```

Or say to agent: "gui please"

## New Features Added

**Alpaca Trading:**
- Direct links to Alpaca dashboard
- Quick buy/sell commands
- Position monitoring
- Close all positions (with warning)

**Swing Dip Strategy:**
- Start/stop automation
- View tracker log
- Edit strategy parameters
- Quick dip checks

**Memory MCP:**
- Knowledge graph access
- Memory search
- Session logs
- RAG reindexing

**System Tools:**
- Clipboard integration
- Screenshot capture
- Active window detection
- Notification system

## Customization

Edit `AgentGUI.ps1` to:
- Change button colors
- Add new commands
- Rearrange layout
- Update paths

Rows 6-9 are reserved for **your custom buttons** - add whatever you use most!

## Future Ideas

Potential buttons to add:
- Trade journal entry
- Risk calculator
- Position sizer
- Backtesting tools
- News alerts
- Economic calendar
- Earnings tracker
- Options screener
- Crypto dashboard
- Portfolio analyzer

Let me know what you want!
