# Switch GitHub MCP from local npx (needs Node) to remote URL (no Node needed)
$path = Join-Path $env:USERPROFILE '.cursor\mcp.json'
$content = Get-Content $path -Raw

# Extract token from current config
$match = [regex]::Match($content, '"GITHUB_PERSONAL_ACCESS_TOKEN"\s*:\s*"([^"]+)"')
$token = if ($match.Success) { $match.Groups[1].Value } else { '' }

# Replace the github block
$oldBlock = '"github":\s*\{\s*"command"\s*:\s*"npx"[^}]+\}\s*\}'
$newBlock = "`"github`":{`"url`":`"https://api.githubcopilot.com/mcp/`",`"headers`":{`"Authorization`":`"Bearer $token`"}}"
$content = $content -replace $oldBlock, $newBlock

# Simpler: targeted replace
$old = '"github":{"command":"npx","args":["-y","@modelcontextprotocol/server-github"],"env":{"GITHUB_PERSONAL_ACCESS_TOKEN":"' + $token + '"}}'
$new = "`"github`":{`"url`":`"https://api.githubcopilot.com/mcp/`",`"headers`":{`"Authorization`":`"Bearer $token`"}}"
$content = $content.Replace($old, $new)
Set-Content $path $content -NoNewline
Write-Host "Switched GitHub MCP to remote URL. Restart Cursor."
