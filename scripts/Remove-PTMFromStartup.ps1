# Remove PTM Daemon from Windows startup
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "PTM Paper Trading Daemon.lnk"
if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
    Write-Host "PTM Daemon removed from startup." -ForegroundColor Green
} else {
    # Also remove old scheduled task if it existed
    Unregister-ScheduledTask -TaskName "PTMPaperTradingDaemon" -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "PTM Daemon was not in startup (or already removed)." -ForegroundColor Yellow
}
