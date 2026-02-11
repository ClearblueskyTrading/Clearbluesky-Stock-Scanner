# Unified desktop-agent utilities for daily routines and task management.
# Usage examples:
#   .\DesktopAgentTools.ps1 -Action menu
#   .\DesktopAgentTools.ps1 -Action brief
#   .\DesktopAgentTools.ps1 -Action morning-news
#   .\DesktopAgentTools.ps1 -Action todo-add -Text "Review watchlist at 3 PM"
#   .\DesktopAgentTools.ps1 -Action todo-list
#   .\DesktopAgentTools.ps1 -Action todo-done -Id 1
#   .\DesktopAgentTools.ps1 -Action daily-wrap -Text "Session complete" -FullBackup

param(
    [ValidateSet("help", "menu", "brief", "morning-news", "open-finviz-news", "daily-start", "daily-wrap", "todo-add", "todo-list", "todo-done", "todo-remove", "session-note", "latest-report", "open-workspace")]
    [string]$Action = "help",
    [string]$Text = "",
    [int]$Id = 0,
    [switch]$FullBackup,
    [switch]$Notify,
    [string]$TodoPath = (Join-Path (Split-Path -Parent $PSScriptRoot) "todo.md"),
    [string]$MemoryRoot = "D:\scanner\velocity_memory"
)

$ErrorActionPreference = "Stop"

$ScriptsDir = $PSScriptRoot
$RepoRoot = Split-Path -Parent $ScriptsDir
$AppDir = Join-Path $RepoRoot "app"
$VoiceMenuPath = Join-Path $RepoRoot "docs\VOICE_MENU.md"
$StrategyPath = Join-Path $ScriptsDir "strategy_for_today.txt"
$KnowledgePath = "C:\Users\EricR\OneDrive\Desktop\Claude AI Knowledge"

function Ensure-TodoFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        $init = @(
            "# Todo",
            "",
            "*(Managed by scripts/DesktopAgentTools.ps1)*",
            ""
        )
        $init | Set-Content -LiteralPath $Path -Encoding UTF8
    }
}

function Get-TodoLines {
    param([string]$Path)
    Ensure-TodoFile -Path $Path
    return @(Get-Content -LiteralPath $Path -ErrorAction Stop)
}

function Parse-TodoItems {
    param([string[]]$Lines)
    $items = @()
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        $line = $Lines[$i]
        if ($line -match '^\s*-\s*\[( |x|X)\]\s*(.+)$') {
            $isDone = $matches[1] -ne " "
            $items += [PSCustomObject]@{
                LineIndex = $i
                Done = $isDone
                Text = $matches[2]
            }
        }
    }
    return $items
}

function Get-ReportsDir {
    $defaultReports = Join-Path $AppDir "reports"
    $cfgPath = Join-Path $AppDir "user_config.json"
    if (-not (Test-Path -LiteralPath $cfgPath)) { return $defaultReports }
    try {
        $cfg = Get-Content -LiteralPath $cfgPath -Raw | ConvertFrom-Json
        $raw = ("" + $cfg.reports_folder).Trim()
        if (-not $raw) { return $defaultReports }
        if ([System.IO.Path]::IsPathRooted($raw)) {
            return $raw
        }
        return (Join-Path $AppDir $raw)
    } catch {
        return $defaultReports
    }
}

function Get-LatestReport {
    $reportsDir = Get-ReportsDir
    if (-not (Test-Path -LiteralPath $reportsDir)) { return $null }
    $latest = Get-ChildItem -LiteralPath $reportsDir -Filter "*_Scan_*.json" -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    return $latest
}

function Write-SessionNote {
    param(
        [string]$NoteText,
        [string]$Root
    )
    $sessionDir = Join-Path $Root "session_logs"
    if (-not (Test-Path -LiteralPath $sessionDir)) {
        New-Item -ItemType Directory -Path $sessionDir -Force | Out-Null
    }
    $stamp = Get-Date -Format "yyyyMMdd_HHmm"
    $path = Join-Path $sessionDir "session_${stamp}_desktop_note.md"
    $time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $summaryLine = "- "
    if ($NoteText -and $NoteText.Trim()) {
        $summaryLine = $NoteText.Trim()
    }
    $content = @(
        "# Desktop Session Note",
        "",
        "- Timestamp: $time",
        "- Source: DesktopAgentTools.ps1",
        "",
        "## Summary",
        $summaryLine,
        "",
        "## Open Items",
        "- ",
        "",
        "## Next Action",
        "- "
    )
    $content | Set-Content -LiteralPath $path -Encoding UTF8
    return $path
}

function Send-Toast {
    param(
        [string]$Title,
        [string]$Message
    )
    $notifyScript = Join-Path $ScriptsDir "Notify.ps1"
    if (Test-Path -LiteralPath $notifyScript) {
        & $notifyScript -Title $Title -Message $Message | Out-Null
    }
}

function Show-Help {
    @"
DesktopAgentTools.ps1
---------------------
Actions:
  help
  menu
  brief
  morning-news
  open-finviz-news
  daily-start
  daily-wrap     [-Text "..."] [-FullBackup] [-Notify]
  todo-add       -Text "..."
  todo-list
  todo-done      -Id <open task number>
  todo-remove    -Id <open task number>
  session-note   [-Text "..."]
  latest-report
  open-workspace
"@ | Write-Output
}

function Invoke-NumberedMenu {
    Write-Output ""
    Write-Output "=== DESKTOP AGENT MENU ==="
    Write-Output " 1) Daily brief"
    Write-Output " 2) Morning news digest (Finviz)"
    Write-Output " 3) Open Finviz news page"
    Write-Output " 4) Todo list"
    Write-Output " 5) Add todo item"
    Write-Output " 6) Mark todo done"
    Write-Output " 7) Remove todo item"
    Write-Output " 8) Daily wrap + backup"
    Write-Output " 9) Full backup now"
    Write-Output "10) Open workspace pack"
    Write-Output " 0) Exit"

    # Safety: if no interactive stdin, print menu and exit cleanly.
    if ([Console]::IsInputRedirected -or -not [Environment]::UserInteractive) {
        Write-Output ""
        Write-Output "Non-interactive session detected. Run a direct action, e.g.:"
        Write-Output "  DesktopAgentTools.ps1 -Action brief"
        Write-Output "  DesktopAgentTools.ps1 -Action morning-news"
        Write-Output "  DesktopAgentTools.ps1 -Action todo-list"
        return
    }

    $pick = (Read-Host "Pick action number").Trim()

    switch ($pick) {
        "1" { & $PSCommandPath -Action brief -TodoPath $TodoPath -MemoryRoot $MemoryRoot }
        "2" { & $PSCommandPath -Action morning-news -MemoryRoot $MemoryRoot }
        "3" { & $PSCommandPath -Action open-finviz-news }
        "4" { & $PSCommandPath -Action todo-list -TodoPath $TodoPath }
        "5" {
            $task = (Read-Host "Enter todo text").Trim()
            if ($task) { & $PSCommandPath -Action todo-add -Text $task -TodoPath $TodoPath }
        }
        "6" {
            $idText = (Read-Host "Enter open task number to mark done").Trim()
            if ($idText -match '^\d+$') {
                & $PSCommandPath -Action todo-done -Id ([int]$idText) -TodoPath $TodoPath
            } else {
                Write-Output "Invalid task number."
            }
        }
        "7" {
            $idText = (Read-Host "Enter open task number to remove").Trim()
            if ($idText -match '^\d+$') {
                & $PSCommandPath -Action todo-remove -Id ([int]$idText) -TodoPath $TodoPath
            } else {
                Write-Output "Invalid task number."
            }
        }
        "8" {
            $note = (Read-Host "Optional wrap note (Enter to skip)").Trim()
            if ($note) {
                & $PSCommandPath -Action daily-wrap -Text $note -TodoPath $TodoPath -MemoryRoot $MemoryRoot -Notify
            } else {
                & $PSCommandPath -Action daily-wrap -TodoPath $TodoPath -MemoryRoot $MemoryRoot -Notify
            }
        }
        "9" {
            $note = (Read-Host "Optional wrap note (Enter to skip)").Trim()
            if ($note) {
                & $PSCommandPath -Action daily-wrap -Text $note -TodoPath $TodoPath -MemoryRoot $MemoryRoot -FullBackup -Notify
            } else {
                & $PSCommandPath -Action daily-wrap -TodoPath $TodoPath -MemoryRoot $MemoryRoot -FullBackup -Notify
            }
        }
        "10" { & $PSCommandPath -Action open-workspace -TodoPath $TodoPath -MemoryRoot $MemoryRoot }
        "0" { return }
        default { Write-Output "Invalid choice. Pick 0-10." }
    }
}

switch ($Action) {
    "help" {
        Show-Help
        break
    }

    "menu" {
        Invoke-NumberedMenu
        break
    }

    "brief" {
        $timeScript = Join-Path $ScriptsDir "GetTimeAndMarket.ps1"
        $activeScript = Join-Path $ScriptsDir "GetActiveWindow.ps1"
        $timeOut = if (Test-Path -LiteralPath $timeScript) { (& $timeScript) } else { "Time/market script not found" }
        $activeOut = if (Test-Path -LiteralPath $activeScript) { (& $activeScript) } else { "(unknown)|(unknown)" }
        $latest = Get-LatestReport
        $lines = Get-TodoLines -Path $TodoPath
        $items = Parse-TodoItems -Lines $lines
        $open = @($items | Where-Object { -not $_.Done })
        $done = @($items | Where-Object { $_.Done })

        Write-Output "=== DAILY BRIEF ==="
        Write-Output $timeOut
        Write-Output "Active window: $activeOut"
        if ($latest) {
            Write-Output ("Latest scan report: {0} ({1})" -f $latest.FullName, $latest.LastWriteTime.ToString("yyyy-MM-dd HH:mm"))
        } else {
            Write-Output "Latest scan report: (none found)"
        }
        Write-Output ("Todo: {0} open / {1} done" -f $open.Count, $done.Count)
        $top = $open | Select-Object -First 5
        if ($top.Count -gt 0) {
            $n = 0
            foreach ($t in $top) {
                $n++
                Write-Output ("  [{0}] {1}" -f $n, $t.Text)
            }
        } else {
            Write-Output "  (No open tasks)"
        }
        break
    }

    "todo-add" {
        if (-not $Text.Trim()) {
            Write-Output "todo-add requires -Text"
            break
        }
        $lines = Get-TodoLines -Path $TodoPath
        $newLine = "- [ ] $($Text.Trim())"
        $lines += $newLine
        $lines | Set-Content -LiteralPath $TodoPath -Encoding UTF8
        Write-Output "Added: $newLine"
        break
    }

    "todo-list" {
        $lines = Get-TodoLines -Path $TodoPath
        $items = Parse-TodoItems -Lines $lines
        $open = @($items | Where-Object { -not $_.Done })
        $done = @($items | Where-Object { $_.Done })

        Write-Output "Open tasks:"
        if ($open.Count -eq 0) {
            Write-Output "  (none)"
        } else {
            for ($i = 0; $i -lt $open.Count; $i++) {
                Write-Output ("  [{0}] {1}" -f ($i + 1), $open[$i].Text)
            }
        }
        Write-Output ""
        Write-Output "Completed tasks:"
        if ($done.Count -eq 0) {
            Write-Output "  (none)"
        } else {
            foreach ($d in $done | Select-Object -Last 10) {
                Write-Output ("  [x] {0}" -f $d.Text)
            }
        }
        break
    }

    "todo-done" {
        if ($Id -le 0) {
            Write-Output "todo-done requires -Id (open task number)"
            break
        }
        $lines = Get-TodoLines -Path $TodoPath
        $items = Parse-TodoItems -Lines $lines
        $open = @($items | Where-Object { -not $_.Done })
        if ($Id -gt $open.Count) {
            Write-Output "Task id $Id is out of range (open tasks: $($open.Count))"
            break
        }
        $target = $open[$Id - 1]
        $line = $lines[$target.LineIndex]
        $lines[$target.LineIndex] = ($line -replace '^\s*-\s*\[\s\]', '- [x]')
        $lines | Set-Content -LiteralPath $TodoPath -Encoding UTF8
        Write-Output ("Completed: [{0}] {1}" -f $Id, $target.Text)
        break
    }

    "todo-remove" {
        if ($Id -le 0) {
            Write-Output "todo-remove requires -Id (open task number)"
            break
        }
        $lines = Get-TodoLines -Path $TodoPath
        $items = Parse-TodoItems -Lines $lines
        $open = @($items | Where-Object { -not $_.Done })
        if ($Id -gt $open.Count) {
            Write-Output "Task id $Id is out of range (open tasks: $($open.Count))"
            break
        }
        $target = $open[$Id - 1]
        $removed = $target.Text
        $out = @()
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($i -ne $target.LineIndex) { $out += $lines[$i] }
        }
        $out | Set-Content -LiteralPath $TodoPath -Encoding UTF8
        Write-Output ("Removed: [{0}] {1}" -f $Id, $removed)
        break
    }

    "morning-news" {
        $digestScript = Join-Path $ScriptsDir "MorningNewsDigest.py"
        if (Test-Path -LiteralPath $digestScript) {
            python $digestScript --save --memory-root $MemoryRoot
        } else {
            Write-Output "Digest script not found: $digestScript"
        }
        break
    }

    "open-finviz-news" {
        Start-Process -FilePath "https://finviz.com/news.ashx" | Out-Null
        Start-Process -FilePath "https://finviz.com/" | Out-Null
        Write-Output "Opened Finviz news pages."
        break
    }

    "latest-report" {
        $latest = Get-LatestReport
        if ($latest) {
            Write-Output $latest.FullName
        } else {
            Write-Output "(none)"
        }
        break
    }

    "session-note" {
        $path = Write-SessionNote -NoteText $Text -Root $MemoryRoot
        Write-Output "Session note saved: $path"
        break
    }

    "daily-start" {
        & $PSCommandPath -Action brief -TodoPath $TodoPath -MemoryRoot $MemoryRoot
        break
    }

    "daily-wrap" {
        $note = if ($Text.Trim()) { $Text.Trim() } else { "Daily wrap complete." }
        $notePath = Write-SessionNote -NoteText $note -Root $MemoryRoot
        Write-Output "Session note: $notePath"

        $backupScript = Join-Path $ScriptsDir "Build-AgentBackup.ps1"
        if (Test-Path -LiteralPath $backupScript) {
            $zipPath = if ($FullBackup) { & $backupScript -Full } else { & $backupScript }
            Write-Output "Backup zip: $zipPath"
            if ($Notify) {
                Send-Toast -Title "Desktop Agent" -Message "Daily wrap done. Backup created."
            }
        } else {
            Write-Output "Backup script not found: $backupScript"
        }
        break
    }

    "open-workspace" {
        $reportsDir = Get-ReportsDir
        $targets = @($TodoPath, $VoiceMenuPath, $StrategyPath, $reportsDir, $KnowledgePath)
        foreach ($t in $targets) {
            if (Test-Path -LiteralPath $t) {
                Start-Process -FilePath $t | Out-Null
                Write-Output "Opened: $t"
            }
        }
        break
    }

    default {
        Show-Help
        break
    }
}
