# Output clipboard content (raw text) so the agent can use it as context.
# Usage: .\GetClipboard.ps1
$raw = Get-Clipboard -Raw -ErrorAction SilentlyContinue
if ($raw) { Write-Output $raw } else { Write-Output "[Clipboard empty or not text]" }
