@echo off
title ClearBlueSky Stock Scanner v7.89
cd /d "%~dp0"
echo Starting ClearBlueSky Stock Scanner v7.89...
python app.py
if %errorLevel% neq 0 (
    echo.
    echo ERROR: Could not start the scanner.
    echo.
    echo Make sure Python is installed and in your PATH.
    echo Run INSTALL.bat first if you haven't already.
    echo.
    pause
)
