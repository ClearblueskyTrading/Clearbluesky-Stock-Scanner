@echo off
REM List natural (OneCore) voices and optionally set one as default for SpeakClipboard.
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0SpeakClipboard.ps1" -ListVoices
pause
