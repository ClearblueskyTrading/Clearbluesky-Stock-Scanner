# GetClipboard.ps1 - Output clipboard text (for agent or GUI)
Add-Type -AssemblyName System.Windows.Forms
$txt = [System.Windows.Forms.Clipboard]::GetText()
if ($txt) { $txt } else { "(empty)" }
