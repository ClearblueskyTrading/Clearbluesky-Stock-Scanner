# TakeScreenshot.ps1 - Capture each monitor at full resolution (one PNG per screen).
# Outputs one full path per line so the agent can read the images.
# Usage: powershell -ExecutionPolicy Bypass -NoProfile -File "d:\cursor\scripts\TakeScreenshot.ps1"

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing, System.Windows.Forms

$baseDir = "d:\cursor\screenshots"
if (-not (Test-Path $baseDir)) { New-Item -ItemType Directory -Path $baseDir -Force | Out-Null }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$index = 1
foreach ($screen in [Windows.Forms.Screen]::AllScreens) {
    $bounds = $screen.Bounds
    $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
    $path = Join-Path $baseDir "capture_${timestamp}_${index}.png"
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
    [System.IO.Path]::GetFullPath($path)
    $index++
}
