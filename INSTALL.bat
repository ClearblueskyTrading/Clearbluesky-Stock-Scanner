@echo off
title ClearBlueSky Stock Scanner v6.3 - Installer
color 0A

echo.
echo  ============================================
echo    ClearBlueSky Stock Scanner v6.3
echo    Free and Open Source - Made with Claude AI
echo  ============================================
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Please run as Administrator
    echo      Right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Ask for install path
echo  Where would you like to install?
echo.
echo  [1] C:\TradingBot (recommended)
echo  [2] Current folder (portable/USB)
echo  [3] Custom path
echo.
set /p choice="  Enter choice (1/2/3): "

if "%choice%"=="1" (
    set "INSTALL_PATH=C:\TradingBot"
) else if "%choice%"=="2" (
    set "INSTALL_PATH=%~dp0ClearBlueSky"
) else if "%choice%"=="3" (
    set /p INSTALL_PATH="  Enter full path: "
) else (
    set "INSTALL_PATH=C:\TradingBot"
)

echo.
echo  Installing to: %INSTALL_PATH%
echo.

:: Create directory
if not exist "%INSTALL_PATH%" mkdir "%INSTALL_PATH%"

:: Copy files
echo  [1/5] Copying program files...
xcopy /E /I /Y "%~dp0app" "%INSTALL_PATH%" >nul 2>&1
if errorlevel 1 (
    copy /Y "%~dp0app\*.*" "%INSTALL_PATH%\" >nul 2>&1
)

:: Create subdirectories
mkdir "%INSTALL_PATH%\reports" 2>nul
mkdir "%INSTALL_PATH%\scans" 2>nul
mkdir "%INSTALL_PATH%\logs" 2>nul

:: Check if Python is installed
echo  [2/5] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo  [!] Python not found. Installing Python...
    echo.
    
    :: Download Python installer
    if exist "%~dp0python-3.12.0-amd64.exe" (
        echo  Installing Python from local file...
        "%~dp0python-3.12.0-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    ) else (
        echo  Downloading Python installer...
        powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe', '%TEMP%\python_installer.exe')"
        echo  Installing Python (this may take a few minutes)...
        "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        del "%TEMP%\python_installer.exe" 2>nul
    )
    
    :: Refresh environment
    set "PATH=%PATH%;C:\Program Files\Python312;C:\Program Files\Python312\Scripts"
    echo  Python installed successfully!
) else (
    echo  Python found!
)

:: Install dependencies
echo  [3/5] Installing required packages...
echo         This may take 1-2 minutes...
python -m pip install --upgrade pip --quiet 2>nul
python -m pip install finviz finvizfinance pandas requests pygame reportlab --quiet 2>nul

if %errorLevel% neq 0 (
    echo  [!] Package install had warnings, retrying...
    pip install finviz finvizfinance pandas requests pygame reportlab 2>nul
)

:: Create desktop shortcut
echo  [4/5] Creating desktop shortcut...
set "SHORTCUT=%USERPROFILE%\Desktop\ClearBlueSky Scanner.lnk"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = 'pythonw.exe'; $s.Arguments = '\"%INSTALL_PATH%\app.py\"'; $s.WorkingDirectory = '%INSTALL_PATH%'; $s.IconLocation = 'shell32.dll,21'; $s.Save()"

:: Create launcher batch file
echo  [5/5] Creating launcher...
(
echo @echo off
echo cd /d "%INSTALL_PATH%"
echo start "" pythonw app.py
) > "%INSTALL_PATH%\START.bat"

:: Create uninstaller
(
echo @echo off
echo title ClearBlueSky - Uninstaller
echo echo.
echo echo  This will remove ClearBlueSky Stock Scanner
echo echo.
echo set /p confirm="  Are you sure? (Y/N): "
echo if /i "%%confirm%%"=="Y" ^(
echo     rmdir /s /q "%INSTALL_PATH%" 2^>nul
echo     del "%USERPROFILE%\Desktop\ClearBlueSky Scanner.lnk" 2^>nul
echo     echo.
echo     echo  Uninstalled successfully!
echo     echo  Note: Python was NOT removed.
echo ^)
echo pause
) > "%INSTALL_PATH%\UNINSTALL.bat"

echo.
echo  ============================================
echo    Installation Complete!
echo  ============================================
echo.
echo  Installed to: %INSTALL_PATH%
echo.
echo  To start: Double-click "ClearBlueSky Scanner" 
echo            on your Desktop, or run START.bat
echo.
echo  To uninstall: Run UNINSTALL.bat in the 
echo               install folder
echo.
pause
