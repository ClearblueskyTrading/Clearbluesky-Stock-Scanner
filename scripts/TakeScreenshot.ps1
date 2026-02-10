# Take a screenshot of each monitor separately at full resolution (no scaling).
# Saves one PNG per monitor so the agent can read text and UI clearly.
# Usage: .\TakeScreenshot.ps1
# Output: One full path per line (so the agent can read each image).

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$outDir = Join-Path (Split-Path -Parent $PSScriptRoot) "screenshots"
if (-not (Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$screens = [System.Windows.Forms.Screen]::AllScreens | Sort-Object { $_.Bounds.X }

$n = 0
foreach ($screen in $screens) {
    $n++
    $bounds = $screen.Bounds
    $path = Join-Path $outDir "capture_${timestamp}_${n}.png"

    $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bmp)
    $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bmp.Dispose()

    Write-Output $path
}
