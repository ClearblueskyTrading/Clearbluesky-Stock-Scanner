# Speak clipboard text using Windows TTS.
# Uses natural (OneCore) voices when you've picked one; otherwise SAPI.
# Sanitizes markdown/code so it reads as plain sentences.
# Usage:
#   .\SpeakClipboard.ps1              # Speak clipboard with saved or default voice
#   .\SpeakClipboard.ps1 -ListVoices   # List voices and optionally save a choice

param([switch] $ListVoices)

$ScriptDir = Split-Path -LiteralPath $MyInvocation.MyCommand.Path
$VoiceChoiceFile = Join-Path $ScriptDir "voice_choice.txt"

function Get-SanitizedClipboardText {
    $raw = Get-Clipboard -Raw
    if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
    $text = $raw -replace '```[\s\S]*?```', ' ' -replace '`[^`]+`', ' ' -replace '\[([^\]]+)\]\([^\)]+\)', '$1'
    $text = $text -replace '\r\n', ' ' -replace '\n+', ' ' -replace '\s+', ' ' -replace '^\s+|\s+$', ''
    if ($text.Length -gt 1500) { $text = $text.Substring(0, 1500) + '. End.' }
    return $text
}

# --- List natural (OneCore) voices and optionally save choice ---
if ($ListVoices) {
    try {
        Add-Type -AssemblyName System.Runtime.WindowsRuntime
        [void][Windows.Foundation.IAsyncOperation`1, Windows.Foundation, ContentType=WindowsRuntime]
        [void][Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType=WindowsRuntime]
        [void][Windows.Media.SpeechSynthesis.SpeechSynthesisStream, Windows.Media.SpeechSynthesis, ContentType=WindowsRuntime]
        $allVoices = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices
        if (-not $allVoices -or $allVoices.Count -eq 0) {
            $allVoices = @([Windows.Media.SpeechSynthesis.SpeechSynthesizer]::DefaultVoice)
        }
        Write-Host "Natural (OneCore) voices:"
        Write-Host ""
        $i = 0
        foreach ($v in $allVoices) {
            $name = if ($v.DisplayName) { $v.DisplayName } else { $v.Id }
            $lang = if ($v.Language) { $v.Language } else { "" }
            Write-Host ("  {0,2}. {1}  ({2})" -f ($i+1), $name, $lang)
            $i++
        }
        Write-Host ""
        $pick = Read-Host "Enter number to set as default voice (or Enter to skip)"
        if ($pick -match '^\d+$' -and [int]$pick -ge 1 -and [int]$pick -le $allVoices.Count) {
            $chosen = $allVoices[[int]$pick - 1]
            $displayName = if ($chosen.DisplayName) { $chosen.DisplayName } else { $chosen.Id }
            $displayName | Set-Content -LiteralPath $VoiceChoiceFile -Encoding UTF8
            Write-Host "Saved default voice: $displayName"
        } elseif ($pick -eq '0' -or $pick -eq '') {
            if (Test-Path -LiteralPath $VoiceChoiceFile) {
                Remove-Item -LiteralPath $VoiceChoiceFile -Force
                Write-Host "Cleared saved voice; will use system default."
            }
        }
    } catch {
        Write-Warning "Could not load natural voices: $_"
        Write-Host "Listing SAPI voices instead:"
        Add-Type -AssemblyName System.Speech
        $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
        $s.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo } | ForEach-Object -Begin { $i=0 } -Process { $i++; Write-Host ("  {0,2}. {1}  ({2})" -f $i, $_.Name, $_.Culture) }
        $pick = Read-Host "Enter number to set as default (or Enter to skip)"
        $voices = @($s.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo })
        if ($pick -match '^\d+$' -and [int]$pick -ge 1 -and [int]$pick -le $voices.Count) {
            $voices[[int]$pick - 1].Name | Set-Content -LiteralPath $VoiceChoiceFile -Encoding UTF8
            Write-Host "Saved: $($voices[[int]$pick - 1].Name)"
        }
    }
    exit
}

# --- Speak clipboard ---
$text = Get-SanitizedClipboardText
if (-not $text) {
    Add-Type -AssemblyName System.Speech
    (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("Clipboard is empty.")
    exit
}

$savedVoice = $null
if (Test-Path -LiteralPath $VoiceChoiceFile) {
    $savedVoice = (Get-Content -LiteralPath $VoiceChoiceFile -Raw -ErrorAction SilentlyContinue) -replace '\s+$', ''
}

# Try WinRT (natural) with saved voice
if ($savedVoice) {
    try {
        Add-Type -AssemblyName System.Runtime.WindowsRuntime
        [void][Windows.Foundation.IAsyncOperation`1, Windows.Foundation, ContentType=WindowsRuntime]
        [void][Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType=WindowsRuntime]
        [void][Windows.Media.SpeechSynthesis.SpeechSynthesisStream, Windows.Media.SpeechSynthesis, ContentType=WindowsRuntime]

        $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
            $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
        })[0]
        function Await($WinRtTask, $ResultType) {
            $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
            $netTask = $asTask.Invoke($null, @($WinRtTask))
            $netTask.Wait(-1) | Out-Null
            $netTask.Result
        }

        $allVoices = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices
        if (-not $allVoices) { $allVoices = @([Windows.Media.SpeechSynthesis.SpeechSynthesizer]::DefaultVoice) }
        $voiceInfo = $allVoices | Where-Object { $_.DisplayName -eq $savedVoice } | Select-Object -First 1
        if (-not $voiceInfo) { $voiceInfo = $allVoices | Where-Object { $_.DisplayName -like "*$savedVoice*" } | Select-Object -First 1 }

        $speak = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::new()
        if ($voiceInfo) { $speak.Voice = $voiceInfo }

        $winrtStream = Await ($speak.SynthesizeTextToStreamAsync($text)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
        $stream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($winrtStream)
        $player = New-Object System.Media.SoundPlayer $stream
        $player.PlaySync()
        $player.Dispose(); $stream.Dispose(); $winrtStream.Dispose(); $speak.Dispose()
        exit
    } catch {
        # Fall back to SAPI
    }
}

# SAPI fallback (or no saved voice)
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($savedVoice) {
    try {
        $s.SelectVoice($savedVoice)
    } catch { }
}
$s.Speak($text)
