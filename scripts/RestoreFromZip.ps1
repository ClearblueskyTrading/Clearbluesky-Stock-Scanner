# RestoreFromZip.ps1 - Restore from cursor-full-backup or cursor-agent-backup zip
param([string]$Path)
$ErrorActionPreference = "Stop"
if (-not $Path -or -not (Test-Path $Path)) { Write-Host "Usage: .\RestoreFromZip.ps1 -Path path\to\backup.zip"; exit 1 }
$WorkspaceRoot = "d:\cursor"
$temp = Join-Path $env:TEMP "cursor_restore_$(Get-Date -Format 'yyyyMMddHHmmss')"
Expand-Archive -Path $Path -DestinationPath $temp -Force
$cursorSrc = Join-Path $temp "cursor"
if (Test-Path $cursorSrc) {
    Get-ChildItem $cursorSrc -Force | ForEach-Object {
        $dest = Join-Path $WorkspaceRoot $_.Name
        if ($_.Name -eq "app") {
            # Merge only rag_store, don't overwrite entire app
            $ragSrc = Join-Path $_.FullName "rag_store"
            if (Test-Path $ragSrc) {
                $ragDest = Join-Path $WorkspaceRoot "app\rag_store"
                if (-not (Test-Path (Split-Path $ragDest))) { New-Item -ItemType Directory -Path (Split-Path $ragDest) -Force | Out-Null }
                Copy-Item $ragSrc -Destination $ragDest -Recurse -Force
                Write-Host "Restored app\rag_store to $WorkspaceRoot"
            }
        } else {
            Copy-Item $_.FullName -Destination $dest -Recurse -Force
            Write-Host "Restored $($_.Name) to $WorkspaceRoot"
        }
    }
}
Remove-Item $temp -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Done. Open $WorkspaceRoot in Cursor; say check your brain to verify."
