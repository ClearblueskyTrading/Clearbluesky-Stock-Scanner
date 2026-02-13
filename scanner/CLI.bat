@echo off
title ClearBlueSky CLI v7.89
cd /d "%~dp0"
python scanner_cli.py %*
exit /b %errorLevel%
