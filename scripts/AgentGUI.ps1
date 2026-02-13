# AgentGUI.ps1 - Desktop Agent Panel (10x10 Grid)
# Enhanced panel with new features: Alpaca trading, Memory MCP, Swing Dip Strategy, etc.

Add-Type -AssemblyName System.Windows.Forms, System.Drawing

$WorkspaceRoot = "d:\cursor"
$AddonsRoot   = "d:\cursor-desktop-addons"

# Create form with 10x10 grid
$form = New-Object System.Windows.Forms.Form
$form.Text = "Trading Agent Command Center"
$form.Size = New-Object System.Drawing.Size(1040, 580)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedSingle"
$form.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 46)
$form.MaximizeBox = $false

# Grid layout settings
$btnWidth = 95
$btnHeight = 45
$btnGap = 3
$startX = 10
$startY = 10

# Button styling
$colorScanner = [System.Drawing.Color]::FromArgb(52, 152, 219)    # Blue - Scanner/Research
$colorTrading = [System.Drawing.Color]::FromArgb(46, 204, 113)    # Green - Trading
$colorMemory = [System.Drawing.Color]::FromArgb(155, 89, 182)     # Purple - Memory/Knowledge
$colorSystem = [System.Drawing.Color]::FromArgb(52, 73, 94)       # Dark - System
$colorStrategy = [System.Drawing.Color]::FromArgb(230, 126, 34)   # Orange - Strategy
$colorLinks = [System.Drawing.Color]::FromArgb(44, 62, 80)        # Gray - Quick Links

$toolTip = New-Object System.Windows.Forms.ToolTip
$toolTip.AutoPopDelay = 8000
$toolTip.InitialDelay = 400
$toolTip.ReshowDelay = 200

function Add-GridButton($row, $col, $text, $color, $tooltipText, $onClick) {
    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = $text
    $btn.Size = New-Object System.Drawing.Size($btnWidth, $btnHeight)
    $btn.Location = New-Object System.Drawing.Point(
        ($startX + ($col * ($btnWidth + $btnGap))),
        ($startY + ($row * ($btnHeight + $btnGap)))
    )
    $btn.FlatStyle = "Flat"
    $btn.BackColor = $color
    $btn.ForeColor = [System.Drawing.Color]::White
    $btn.Font = New-Object System.Drawing.Font("Segoe UI", 8, [System.Drawing.FontStyle]::Bold)
    $btn.TextAlign = "MiddleCenter"
    $btn.Add_Click($onClick)
    $toolTip.SetToolTip($btn, $tooltipText)
    $form.Controls.Add($btn)
}

# Row 0: Scanner & Research
Add-GridButton 0 0 "Scanner`nGUI" $colorScanner "Launch the ClearBlueSky Stock Scanner desktop app" {
    $apps = @("d:\cursor\scanner\app.py")
    foreach ($p in $apps) {
        if (Test-Path $p) {
            Start-Process python -ArgumentList "`"$p`"" -WindowStyle Normal
            break
        }
    }
}

Add-GridButton 0 1 "Velocity" $colorScanner "Run velocity scan for momentum stocks (opens CLI window)" {
    $cli = "d:\cursor\scanner\scanner_cli.py"
    if (Test-Path $cli) {
        Start-Process powershell -ArgumentList "python `"$cli`" --scan velocity" -WindowStyle Normal
    }
}

Add-GridButton 0 2 "Swing`nDips" $colorScanner "Scan for swing dip buying opportunities" {
    $cli = "d:\cursor\scanner\scanner_cli.py"
    if (Test-Path $cli) {
        Start-Process powershell -ArgumentList "python `"$cli`" --scan swing" -WindowStyle Normal
    }
}

Add-GridButton 0 3 "Watchlist" $colorScanner "Scan your saved watchlist symbols" {
    $cli = "d:\cursor\scanner\scanner_cli.py"
    if (Test-Path $cli) {
        Start-Process powershell -ArgumentList "python `"$cli`" --scan watchlist" -WindowStyle Normal
    }
}

Add-GridButton 0 4 "Reports" $colorScanner "Open the scanner reports folder" {
    $r = "d:\cursor\scanner\reports"
    if (Test-Path $r) { Start-Process explorer $r }
}

Add-GridButton 0 5 "Finviz" $colorLinks "Open Finviz market map" {
    Start-Process "https://finviz.com/map.ashx"
}

Add-GridButton 0 6 "Trading`nView" $colorLinks "Open TradingView charts" {
    Start-Process "https://www.tradingview.com/"
}

Add-GridButton 0 7 "Market`nWatch" $colorLinks "Open MarketWatch" {
    Start-Process "https://www.marketwatch.com/"
}

Add-GridButton 0 8 "Schwab" $colorLinks "Open Schwab client portal" {
    Start-Process "https://client.schwab.com/"
}

Add-GridButton 0 9 "Yahoo" $colorLinks "Open Yahoo Finance" {
    Start-Process "https://finance.yahoo.com/"
}

# Row 1: Alpaca Trading
Add-GridButton 1 0 "Alpaca`nWeb" $colorTrading "Open Alpaca paper trading dashboard" {
    Start-Process "https://app.alpaca.markets/paper/dashboard/overview"
}

Add-GridButton 1 1 "Positions" $colorTrading "Copy 'Check my Alpaca positions' - paste in Cursor" {
    # Open Cursor and paste command
    $clipText = "Check my Alpaca positions"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Alpaca")
}

Add-GridButton 1 2 "Orders" $colorTrading "Copy 'Show my Alpaca orders' - paste in Cursor" {
    $clipText = "Show my Alpaca orders"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Alpaca")
}

Add-GridButton 1 3 "Account" $colorTrading "Copy 'What is my Alpaca account status?' - paste in Cursor" {
    $clipText = "What's my Alpaca account status?"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Alpaca")
}

Add-GridButton 1 4 "Bars" $colorTrading "Copy 'Get stock bars for' - add symbol, paste in Cursor" {
    $clipText = "Get stock bars for "
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nAdd symbol and paste in Cursor", "Alpaca")
}

Add-GridButton 1 5 "Watchlist" $colorTrading "Copy 'Show my Alpaca watchlists' - paste in Cursor" {
    $clipText = "Show my Alpaca watchlists"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Alpaca")
}

Add-GridButton 1 6 "Buy" $colorTrading "Copy 'Buy' - add shares/symbol, paste in Cursor" {
    $clipText = "Buy "
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nAdd 'X shares of SYMBOL' and paste", "Alpaca")
}

Add-GridButton 1 7 "Sell" $colorTrading "Copy 'Sell' - add shares/symbol, paste in Cursor" {
    $clipText = "Sell "
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nAdd 'X shares of SYMBOL' and paste", "Alpaca")
}

Add-GridButton 1 8 "Close`nAll" $colorTrading "Copy 'Close all Alpaca positions' - CONFIRM before pasting" {
    $clipText = "Close all Alpaca positions"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nCONFIRM before pasting!", "Alpaca")
}

Add-GridButton 1 9 "Refresh" $colorTrading "Copy 'What are my current positions and P&L?' - paste in Cursor" {
    $clipText = 'What are my current positions and P&L?'
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Alpaca")
}

# Row 2: Swing Dip Strategy
Add-GridButton 2 0 "Start`nSwing" $colorStrategy "Start the automated swing dip strategy" {
    $script = "d:\cursor\scanner\alpaca_swing_dip_strategy.py"
    if (Test-Path $script) {
        Start-Process powershell -ArgumentList "python `"$script`"" -WindowStyle Normal
    } else {
        [System.Windows.Forms.MessageBox]::Show("Script not found: $script", "Strategy")
    }
}

Add-GridButton 2 1 "Stop`nSwing" $colorStrategy "Stop any running swing strategy processes" {
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*swing*"} | Stop-Process -Force
    [System.Windows.Forms.MessageBox]::Show("Stopped any running swing strategy processes", "Strategy")
}

Add-GridButton 2 2 "Strategy`nLog" $colorStrategy "Open swing dip tracker JSON" {
    $log = "d:\cursor\scanner\swing_dip_tracker.json"
    if (Test-Path $log) {
        Start-Process notepad $log
    } else {
        [System.Windows.Forms.MessageBox]::Show("No tracker file yet. Run strategy first.", "Strategy")
    }
}

Add-GridButton 2 3 "Edit`nParams" $colorStrategy "Edit swing strategy script parameters" {
    $script = "d:\cursor\scanner\alpaca_swing_dip_strategy.py"
    if (Test-Path $script) {
        Start-Process notepad $script
    }
}

Add-GridButton 2 4 "Backtest" $colorStrategy "Copy backtest request - paste in Cursor" {
    $clipText = "Analyze the performance of my swing dip strategy"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Strategy")
}

Add-GridButton 2 5 "Strategy`nDoc" $colorStrategy "Open Hybrid 60/30/10 strategy (PTM_README)" {
    $doc = "d:\cursor\scanner\PTM_README.md"
    if (Test-Path $doc) {
        Start-Process notepad $doc
    }
}

Add-GridButton 2 6 "Config" $colorStrategy "Edit user_config.json" {
    $config = "d:\cursor\scanner\user_config.json"
    if (Test-Path $config) {
        Start-Process notepad $config
    }
}

Add-GridButton 2 7 "Test`nRun" $colorStrategy "Copy test scan request - paste in Cursor" {
    $clipText = "Run a test scan for swing dip opportunities now"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Strategy")
}

Add-GridButton 2 8 "Check`nDips" $colorStrategy "Copy dip scan request - paste in Cursor" {
    $clipText = "What stocks are down 2-5% today with good fundamentals?"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Strategy")
}

Add-GridButton 2 9 "Signals" $colorStrategy "Copy today's signals request - paste in Cursor" {
    $clipText = "Show me today's swing dip signals"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Strategy")
}

# Row 3: Memory & Knowledge
Add-GridButton 3 0 "Check`nBrain" $colorMemory "Copy 'check your brain' - AI recalls conversation/summary" {
    $clipText = "check your brain"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Memory")
}

Add-GridButton 3 1 "Save`nConv" $colorMemory "Copy 'save conversation' - persists to memory" {
    $clipText = "save conversation"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Memory")
}

Add-GridButton 3 2 "Memory`nGraph" $colorMemory "Copy 'Show me my knowledge graph' - paste in Cursor" {
    $clipText = "Show me my knowledge graph"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Memory")
}

Add-GridButton 3 3 "Search`nMemory" $colorMemory "Copy 'Search your memory for' - add query, paste in Cursor" {
    $clipText = "Search your memory for "
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nAdd query and paste in Cursor", "Memory")
}

Add-GridButton 3 4 "Session`nLog" $colorMemory "Open velocity session logs folder" {
    $logs = "d:\cursor\velocity_memory\session_logs"
    if (Test-Path $logs) {
        Start-Process explorer $logs
    }
}

Add-GridButton 3 5 "Full`nBackup" $colorMemory "Run full agent backup script" {
    $script = "d:\cursor\scripts\Build-AgentBackup.ps1"
    if (Test-Path $script) {
        Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$script`" -Full" -WindowStyle Normal
    }
}

Add-GridButton 3 6 "RAG`nStore" $colorMemory "Open Chroma RAG database folder" {
    $rag = "d:\cursor\velocity_memory\chroma_db"
    if (Test-Path $rag) {
        Start-Process explorer $rag
    }
}

Add-GridButton 3 7 "Reindex`nRAG" $colorMemory "Copy reindex request - paste in Cursor" {
    $clipText = "Reindex the RAG database"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Memory")
}

Add-GridButton 3 8 "Docs" $colorMemory "Open docs folder" {
    $docs = "d:\cursor\docs"
    if (Test-Path $docs) {
        Start-Process explorer $docs
    }
}

Add-GridButton 3 9 "MCPs" $colorMemory "Edit MCP config (mcp.json)" {
    $mcp = "C:\Users\EricR\.cursor\mcp.json"
    if (Test-Path $mcp) {
        Start-Process notepad $mcp
    }
}

# Row 4: System & Tools
Add-GridButton 4 0 "Screenshot" $colorSystem "Take a screenshot (saved to screenshots folder)" {
    $script = "d:\cursor\scripts\TakeScreenshot.ps1"
    if (Test-Path $script) {
        Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$script`"" -WindowStyle Hidden
    }
}

Add-GridButton 4 1 "Clipboard" $colorSystem "Copy 'use clipboard' - AI reads clipboard content" {
    $clipText = "use clipboard"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "System")
}

Add-GridButton 4 2 "Active`nWin" $colorSystem "Copy 'what am I looking at?' - AI uses screenshot/browser" {
    $clipText = "what am I looking at?"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "System")
}

Add-GridButton 4 3 "Time/`nMarket" $colorSystem "Copy 'what time is it?' - AI reports time and market status" {
    $clipText = "what time is it?"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "System")
}

Add-GridButton 4 4 "Notify`nTest" $colorSystem "Test system tray notification" {
    Add-Type -AssemblyName System.Windows.Forms
    $notification = New-Object System.Windows.Forms.NotifyIcon
    $notification.Icon = [System.Drawing.SystemIcons]::Information
    $notification.BalloonTipTitle = "Agent Test"
    $notification.BalloonTipText = "Notification system working!"
    $notification.Visible = $true
    $notification.ShowBalloonTip(3000)
}

Add-GridButton 4 5 "Workspace" $colorSystem "Open D:\cursor workspace in Explorer" {
    Start-Process explorer "d:\cursor"
}

Add-GridButton 4 6 "Rules" $colorSystem "Open .cursor\rules folder" {
    $rules = "d:\cursor\.cursor\rules"
    if (Test-Path $rules) {
        Start-Process explorer $rules
    }
}

Add-GridButton 4 7 "Scripts" $colorSystem "Open scripts folder" {
    $scripts = "d:\cursor\scripts"
    if (Test-Path $scripts) {
        Start-Process explorer $scripts
    }
}

Add-GridButton 4 8 "Screenshots" $colorSystem "Open screenshots folder" {
    $screenshots = "d:\cursor\screenshots"
    if (Test-Path $screenshots) {
        Start-Process explorer $screenshots
    }
}

Add-GridButton 4 9 "Notepad" $colorSystem "Open Notepad" {
    Start-Process notepad
}

# Row 5: Quick Actions
Add-GridButton 5 0 "Menu" $colorSystem "Copy 'menu' - paste in Cursor to see all commands" {
    $clipText = "menu"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor to see all commands", "Menu")
}

Add-GridButton 5 1 "Help" $colorSystem "Copy help prompt - paste in Cursor" {
    $clipText = "What can you help me with today?"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Help")
}

Add-GridButton 5 2 "Restart" $colorSystem "Reminder to restart Cursor to reload MCPs" {
    [System.Windows.Forms.MessageBox]::Show("Close and restart Cursor to reload MCPs", "Restart")
}

Add-GridButton 5 3 "Debug" $colorSystem "Copy diagnostics request - paste in Cursor" {
    $clipText = "Run diagnostics on the trading system"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Debug")
}

Add-GridButton 5 4 "Status" $colorSystem "Copy status request - paste in Cursor" {
    $clipText = "Show me system status: scanner, Alpaca connection, strategy running"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Status")
}

Add-GridButton 5 5 "Performance" $colorSystem "Copy performance summary request - paste in Cursor" {
    $clipText = "Show my trading performance summary"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Performance")
}

Add-GridButton 5 6 "Goals" $colorSystem "Copy goals/tracking request - paste in Cursor" {
    $clipText = "What are my trading goals and am I on track?"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nPaste in Cursor", "Goals")
}

Add-GridButton 5 7 "Learn" $colorSystem "Copy 'Teach me about' - add topic, paste in Cursor" {
    $clipText = "Teach me about "
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nAdd topic and paste in Cursor", "Learn")
}

Add-GridButton 5 8 "Predict" $colorSystem "Copy outlook prompt - add symbol, paste in Cursor" {
    $clipText = "Based on current market data, what's your outlook for "
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied to clipboard: '$clipText'`n`nAdd symbol and paste in Cursor", "Predict")
}

Add-GridButton 5 9 "Chat" $colorSystem "Open ChatGPT in browser" {
    Start-Process 'https://chat.openai.com'
}

# Row 6: PTM + reserved
Add-GridButton 6 0 "PTM" $colorTrading "Single PTM cycle (dry-run): check positions, scan buys" {
    $ptm = "d:\cursor\scanner\paper_trading_manager.py"
    if (Test-Path $ptm) {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd d:\cursor\scanner; python paper_trading_manager.py"
    } else {
        [System.Windows.Forms.MessageBox]::Show("PTM not found: $ptm", "Paper Trading Manager")
    }
}

Add-GridButton 6 1 "PTM`nDaemon" $colorTrading "Start PTM Daemon: runs every 5 min, paper trade only, swing only (no same-day exit)" {
    $daemon = "d:\cursor\scanner\ptm_daemon.py"
    if (Test-Path $daemon) {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd d:\cursor\scanner; python ptm_daemon.py"
    } else {
        [System.Windows.Forms.MessageBox]::Show("PTM Daemon not found: $daemon", "PTM Daemon")
    }
}

Add-GridButton 6 2 "PTM`nStartup" $colorTrading "Add PTM Daemon to Windows startup (run once)" {
    $script = "d:\cursor\scripts\Add-PTMToStartup.ps1"
    if (Test-Path $script) {
        Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass", "-File", "`"$script`"" -Wait
    } else {
        [System.Windows.Forms.MessageBox]::Show("Add-PTMToStartup.ps1 not found", "PTM Startup")
    }
}

Add-GridButton 6 3 "Reindex`nBooks" $colorMemory "Re-index trading books from AI Knowledge folder into RAG" {
    $script = "d:\cursor\scripts\Reindex-Books.ps1"
    if (Test-Path $script) {
        Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy Bypass", "-File", "`"$script`""
    } else {
        [System.Windows.Forms.MessageBox]::Show("Reindex-Books.ps1 not found", "Reindex Books")
    }
}

Add-GridButton 6 4 "Trader`nOne" $colorTrading "Copy Trader One status (main Alpaca, hybrid 60/30/10)" {
    $clipText = "Check my Alpaca positions and orders for Trader One hybrid plan"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied: '$clipText'`n`nPaste in Cursor", "Trader One")
}

Add-GridButton 6 5 "Trader`nTwo" $colorTrading "Copy Trader Two status (paper Alpaca account)" {
    $clipText = "Check my Alpaca positions and orders for Trader Two"
    [System.Windows.Forms.Clipboard]::SetText($clipText)
    [System.Windows.Forms.MessageBox]::Show("Copied: '$clipText'`n`nPaste in Cursor", "Trader Two")
}

# Row 6-9: Rest reserved for future expansion
$reservedText = 'Reserved'
for ($row = 6; $row -lt 10; $row++) {
    for ($col = 0; $col -lt 10; $col++) {
        if ($row -eq 6 -and $col -lt 6) { continue }
        $r = $row; $c = $col
        Add-GridButton $row $col '...' $colorSystem "Reserved for future feature" {
            [System.Windows.Forms.MessageBox]::Show('Button available for future feature', $reservedText)
        }
    }
}

$form.ShowDialog() | Out-Null
