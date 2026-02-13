# Add VoiceMode to Cursor MCP config
# Run from PowerShell. Requires uv/uvx (already installed).

$mcpPath = "$env:USERPROFILE\.cursor\mcp.json"
$voiceModeBlock = ',"voice-mode":{"command":"uvx","args":["voice-mode"],"env":{"OPENAI_API_KEY":"YOUR_OPENAI_API_KEY_HERE"}}'

if (-not (Test-Path $mcpPath)) {
    Write-Host "mcp.json not found at $mcpPath - create it first in Cursor" -ForegroundColor Red
    exit 1
}

$content = Get-Content $mcpPath -Raw
if ($content -match '"voice-mode"') {
    Write-Host "voice-mode already in mcp.json - skipping" -ForegroundColor Yellow
    exit 0
}

# Insert voice-mode entry before the closing }} of mcpServers
# Handles both minified and pretty-printed JSON
$newContent = $content -replace '\}\s*\}\s*$', "}$voiceModeBlock}}"

Set-Content $newContent -Path $mcpPath -NoNewline -Encoding UTF8
Write-Host "Added voice-mode to $mcpPath" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Edit mcp.json and replace YOUR_OPENAI_API_KEY_HERE with your OpenAI API key." -ForegroundColor Yellow
Write-Host "Restart Cursor. Then: Ctrl+K -> type 'Talk to me' or 'Let''s have a voice conversation'" -ForegroundColor Cyan
