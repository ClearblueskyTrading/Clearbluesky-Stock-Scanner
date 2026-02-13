# Setup Gemini CLI + VoiceMode (fully free - your Google key + local voice)
# No Cursor usage, no OpenAI key, no payment.

$geminiDir = "$env:USERPROFILE\.gemini"
$settingsPath = "$geminiDir\settings.json"

$voiceModeConfig = @'
{
  "mcpServers": {
    "voice-mode": {
      "command": "uvx",
      "args": ["voice-mode"],
      "env": {
        "VOICEMODE_TTS_BASE_URLS": "http://127.0.0.1:8880/v1",
        "VOICEMODE_STT_BASE_URLS": "http://127.0.0.1:2022/v1",
        "VOICEMODE_PREFER_LOCAL": "true"
      }
    }
  }
}
'@

Write-Host "=== Gemini CLI + VoiceMode (Free) Setup ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check Node / npm
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js required. Install from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# 2. Install Gemini CLI
Write-Host "1. Installing Gemini CLI..." -ForegroundColor Yellow
npm install -g @google/gemini-cli
if ($LASTEXITCODE -ne 0) {
    Write-Host "npm install failed" -ForegroundColor Red
    exit 1
}
Write-Host "   Done." -ForegroundColor Green

# 3. Auth (user must do manually)
Write-Host ""
Write-Host "2. Log in with your Google AI key:" -ForegroundColor Yellow
Write-Host "   gemini-cli auth login" -ForegroundColor White
Write-Host "   Get a free key at: https://aistudio.google.com/apikey" -ForegroundColor Gray
Write-Host ""

# 4. Install local voice
Write-Host "3. Installing local voice (Whisper + Kokoro)..." -ForegroundColor Yellow
uvx voice-mode kokoro install 2>$null
uvx voice-mode whisper install 2>$null
Write-Host "   Done." -ForegroundColor Green

# 5. Write Gemini CLI settings
if (-not (Test-Path $geminiDir)) {
    New-Item -ItemType Directory -Path $geminiDir -Force | Out-Null
}

if (Test-Path $settingsPath) {
    $content = Get-Content $settingsPath -Raw
    if ($content -match '"voice-mode"') {
        Write-Host "4. voice-mode already in Gemini CLI config" -ForegroundColor Yellow
    } else {
        $block = ',"voice-mode":{"command":"uvx","args":["voice-mode"],"env":{"VOICEMODE_TTS_BASE_URLS":"http://127.0.0.1:8880/v1","VOICEMODE_STT_BASE_URLS":"http://127.0.0.1:2022/v1","VOICEMODE_PREFER_LOCAL":"true"}}'
        $merged = $content -replace '(\}\s*)\}(\s*)$', "$block}`n}`$2"
        if ($merged -ne $content) {
            Set-Content $merged -Path $settingsPath -NoNewline -Encoding UTF8
            Write-Host "4. Added voice-mode to existing $settingsPath" -ForegroundColor Green
        } else {
            Write-Host "4. Could not auto-merge - add manually (see VOICEMODE_GEMINI_FREE.md)" -ForegroundColor Yellow
        }
    }
} else {
    Set-Content $voiceModeConfig -Path $settingsPath -Encoding UTF8
    Write-Host "4. Created $settingsPath with VoiceMode config" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Next steps ===" -ForegroundColor Cyan
Write-Host "1. Run:  gemini-cli auth login    (use your Google AI key)"
Write-Host "2. In one terminal:  uvx voice-mode kokoro start"
Write-Host "3. In another:       uvx voice-mode whisper start  (if needed)"
Write-Host "4. Run:  gemini-cli"
Write-Host "5. Say: 'Let''s have a voice conversation'"
Write-Host ""
Write-Host "Full guide: D:\cursor\docs\VOICEMODE_GEMINI_FREE.md" -ForegroundColor Gray
