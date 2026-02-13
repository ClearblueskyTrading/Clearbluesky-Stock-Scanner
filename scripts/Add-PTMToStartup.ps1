# Add PTM Daemon to Windows startup (runs every 5 min, paper trade only, swing only)
# Run once to install. Uses Startup folder (no admin required).

$PTMPath = "D:\cursor\scanner\ptm_daemon.py"
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
$WorkingDir = "D:\cursor\scanner"
$StartupFolder = [Environment]::GetFolderPath("Startup")

if (-not (Test-Path $PTMPath)) {
    Write-Host "PTM daemon not found: $PTMPath" -ForegroundColor Red
    exit 1
}

if (-not $PythonPath) {
    Write-Host "Python not found. Install Python and try again." -ForegroundColor Red
    exit 1
}

# Use pythonw for no-console (runs hidden in background)
$PythonWPath = $PythonPath -replace 'python\.exe$', 'pythonw.exe'
if (-not (Test-Path $PythonWPath)) { $PythonWPath = $PythonPath }

$ShortcutPath = Join-Path $StartupFolder "PTM Paper Trading Daemon.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonWPath
$Shortcut.Arguments = "`"$PTMPath`""
$Shortcut.WorkingDirectory = $WorkingDir
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Description = "PTM Daemon - paper trade every 5 min, swing only"
$Shortcut.Save()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($WshShell) | Out-Null

Write-Host "PTM Daemon added to Windows startup" -ForegroundColor Green
Write-Host "  Shortcut: $ShortcutPath"
Write-Host "  Runs: At logon, every 5 min (paper trade only, swing only)"
