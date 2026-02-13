# Build-AgentBackup.ps1 - Create cursor-agent-backup or cursor-full-backup zip
# Agent only: rules, scripts, docs, menu, todo. Full: + velocity_memory + rag_store.

param(
    [switch]$Full,
    [string]$WorkspaceRoot = "d:\cursor",
    [string]$OutputDir = "d:\cursor"
)

$ErrorActionPreference = "Stop"
$date = Get-Date -Format "yyyyMMdd"
$name = if ($Full) { "cursor-full-backup-$date" } else { "cursor-agent-backup-$date" }
$zipPath = Join-Path $OutputDir "$name.zip"
$tempDir = Join-Path $env:TEMP "cursor_backup_$date"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
$cursorDir = Join-Path $tempDir "cursor"
New-Item -ItemType Directory -Path $cursorDir -Force | Out-Null

# Copy agent files
$agentItems = @(".cursor", "scripts", "docs", "RESTORE.md", "todo.md")
# Also backup global MCP config (user's mcp.json) so it can be restored if corrupted
$globalMcp = Join-Path $env:USERPROFILE ".cursor\mcp.json"
if (Test-Path $globalMcp) {
    Copy-Item $globalMcp -Destination (Join-Path $cursorDir "mcp.json.backup") -Force
}
foreach ($item in $agentItems) {
    $src = Join-Path $WorkspaceRoot $item
    if (Test-Path $src) {
        $dest = Join-Path $cursorDir $item
        Copy-Item -Path $src -Destination $dest -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Full backup: add velocity_memory and app/rag_store from WorkspaceRoot (d:\cursor)
if ($Full) {
    $dataDir = Join-Path $tempDir "cursor"
    $vmSrc = Join-Path $WorkspaceRoot "velocity_memory"
    $ragSrc = Join-Path $WorkspaceRoot "app\rag_store"
    if (Test-Path $vmSrc) {
        $vmDest = Join-Path $dataDir "velocity_memory"
        New-Item -ItemType Directory -Path (Split-Path $vmDest) -Force | Out-Null
        Copy-Item -Path $vmSrc -Destination $vmDest -Recurse -Force
    }
    if (Test-Path $ragSrc) {
        $ragDest = Join-Path $dataDir "app\rag_store"
        New-Item -ItemType Directory -Path (Split-Path $ragDest) -Force | Out-Null
        Copy-Item -Path $ragSrc -Destination $ragDest -Recurse -Force
    }
}

# Zip
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $tempDir "*") -DestinationPath $zipPath -Force
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Created: $zipPath"
Write-Host "Size:   $([math]::Round((Get-Item $zipPath).Length / 1MB, 2)) MB"
