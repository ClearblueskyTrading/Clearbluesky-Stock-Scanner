# Create desktop shortcut with hotkey for Local Voice Input
# Hotkey: Ctrl+Alt+V (launches voice_input_local.py)

$Desktop = [Environment]::GetFolderPath("Desktop")
$LnkPath = "$Desktop\Voice Input (local).lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($LnkPath)

# Use pythonw to avoid console window when launching
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue).Source }
if (-not $python) {
    # Fallback common paths
    $python = "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe"
    $python = (Get-Item $python -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
}
if (-not $python) {
    Write-Host "Python not found. Install Python and try again." -ForegroundColor Red
    exit 1
}

$Shortcut.TargetPath = $python
$Shortcut.Arguments = "`"D:\cursor\scripts\voice_input_local.py`""
$Shortcut.WorkingDirectory = "D:\cursor\scripts"
$Shortcut.Hotkey = "Ctrl+Alt+V"
$Shortcut.Description = "Local voice input for Cursor - always listening"
$Shortcut.WindowStyle = 1  # Normal - show the voice input window
$Shortcut.Save()

Write-Host "Created: $LnkPath" -ForegroundColor Green
Write-Host "Hotkey: Ctrl+Alt+V" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+Alt+V anytime to launch voice input." -ForegroundColor Gray
