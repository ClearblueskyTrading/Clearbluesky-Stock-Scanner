@echo off
REM One-click: speak whatever is on the clipboard (Windows SAPI).
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0SpeakClipboard.ps1"
pause
