# Build a restore-friendly zip of Cursor agent setup (rules, scripts, docs, todo).
# With -Full: also includes velocity_memory (session_logs, trade_journal, market_context, etc.) and ChromaDB (app/rag_store) so you can restore and pick up where you left off.
# Usage: .\Build-AgentBackup.ps1  [optional output path]
#        .\Build-AgentBackup.ps1 -Full  [optional output path]
# Default output: cursor-agent-backup-YYYYMMDD.zip  or  cursor-full-backup-YYYYMMDD.zip

param([switch]$Full, [string]$ScannerRoot = "D:\scanner")

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path $repoRoot)) { $repoRoot = Split-Path -Parent $PSScriptRoot }

$date = Get-Date -Format "yyyyMMdd"
$zipName = if ($Full) { "cursor-full-backup-$date.zip" } else { "cursor-agent-backup-$date.zip" }
$outZip = Join-Path $repoRoot $zipName
if ($args[0]) { $outZip = $args[0] }

$tempDir = Join-Path $env:TEMP "cursor-backup-$date"
if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# --- Cursor agent part (always) ---
$cursorDir = if ($Full) { Join-Path $tempDir "cursor" } else { $tempDir }
if ($Full) { New-Item -ItemType Directory -Path $cursorDir -Force | Out-Null }

$rulesSrc = Join-Path $repoRoot ".cursor\rules"
$rulesDst = Join-Path $cursorDir ".cursor\rules"
if (Test-Path $rulesSrc) {
    New-Item -ItemType Directory -Path $rulesDst -Force | Out-Null
    Copy-Item -Path (Join-Path $rulesSrc "*.mdc") -Destination $rulesDst -Force
}

$scriptsSrc = Join-Path $repoRoot "scripts"
$scriptsDst = Join-Path $cursorDir "scripts"
if (Test-Path $scriptsSrc) {
    New-Item -ItemType Directory -Path $scriptsDst -Force | Out-Null
    Get-ChildItem -Path $scriptsSrc -File | Where-Object {
        $_.Name -notin @("voice_choice.txt", "strategy_for_today.txt")
    } | ForEach-Object { Copy-Item $_.FullName -Destination $scriptsDst -Force }
}

$docsSrc = Join-Path $repoRoot "docs"
$docsDst = Join-Path $cursorDir "docs"
if (Test-Path $docsSrc) {
    $subdirs = @("references", "guidelines", "strategy")
    foreach ($d in $subdirs) {
        $src = Join-Path $docsSrc $d
        $dst = Join-Path $docsDst $d
        if (Test-Path $src) {
            New-Item -ItemType Directory -Path $dst -Force | Out-Null
            Copy-Item -Path (Join-Path $src "*") -Destination $dst -Force -ErrorAction SilentlyContinue
        }
    }
    $voiceMenu = Join-Path $docsSrc "VOICE_MENU.md"
    if (Test-Path $voiceMenu) {
        if (-not (Test-Path $docsDst)) { New-Item -ItemType Directory -Path $docsDst -Force | Out-Null }
        Copy-Item $voiceMenu -Destination $docsDst -Force
    }
}

$restore = Join-Path $repoRoot "RESTORE.md"
$todo = Join-Path $repoRoot "todo.md"
if (Test-Path $restore) { Copy-Item $restore -Destination $cursorDir -Force }
if (Test-Path $todo) { Copy-Item $todo -Destination $cursorDir -Force }

# --- Full backup: scanner data + vector DB ---
if ($Full -and (Test-Path $ScannerRoot)) {
    $scannerDir = Join-Path $tempDir "scanner"
    New-Item -ItemType Directory -Path $scannerDir -Force | Out-Null

    $vmSrc = Join-Path $ScannerRoot "velocity_memory"
    $vmDst = Join-Path $scannerDir "velocity_memory"
    if (Test-Path $vmSrc) {
        Copy-Item -Path $vmSrc -Destination $vmDst -Recurse -Force
    }

    $ragStoreSrc = Join-Path $ScannerRoot "app\rag_store"
    $ragStoreDst = Join-Path $scannerDir "app\rag_store"
    if (Test-Path $ragStoreSrc) {
        New-Item -ItemType Directory -Path (Split-Path $ragStoreDst) -Force | Out-Null
        Copy-Item -Path $ragStoreSrc -Destination $ragStoreDst -Recurse -Force
    }
}

# Create zip (top-level contents: cursor\ and optionally scanner\)
$zipInput = if ($Full) { Join-Path $tempDir "*" } else { Join-Path $tempDir "*" }
if (Test-Path $outZip) { Remove-Item $outZip -Force }
Compress-Archive -Path $zipInput -DestinationPath $outZip -Force
Remove-Item -Recurse -Force $tempDir

Write-Output $outZip
