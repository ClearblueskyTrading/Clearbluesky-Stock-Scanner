# Injects gh auth token into Cursor mcp.json for GitHub MCP
$token = (gh auth token).Trim()
$path = Join-Path $env:USERPROFILE '.cursor\mcp.json'
$content = Get-Content $path -Raw
$content = $content.Replace('<your-github-pat>', $token)
Set-Content $path $content -NoNewline
Write-Host "Updated mcp.json with GitHub token. Restart Cursor to load the GitHub MCP."
