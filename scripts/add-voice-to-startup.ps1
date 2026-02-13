# Add Voice Input to Windows startup (run when Windows starts)

$StartupFolder = [Environment]::GetFolderPath("Startup")
$LnkPath = "$StartupFolder\Voice Input (local).lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($LnkPath)

$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue).Source }
if (-not $python) {
    Write-Host "Python not found." -ForegroundColor Red
    exit 1
}

# Use pythonw to avoid console window on startup
$pythonw = $python -replace "python\.exe$", "pythonw.exe"
if (-not (Test-Path $pythonw)) { $pythonw = $python }

$Shortcut.TargetPath = $pythonw
$Shortcut.Arguments = "`"D:\cursor\scripts\voice_input_local.py`""
$Shortcut.WorkingDirectory = "D:\cursor\scripts"
$Shortcut.Description = "Local voice input - runs at Windows startup"
$Shortcut.WindowStyle = 1
$Shortcut.Save()

Write-Host "Added to startup: $LnkPath" -ForegroundColor Green
Write-Host "Voice input will run when Windows starts." -ForegroundColor Cyan
Write-Host "To remove: delete the shortcut in Startup folder" -ForegroundColor Gray
