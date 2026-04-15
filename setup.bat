@echo off
REM ============================================================
REM  Housoft Meta - One-time Setup Script
REM  Installs dependencies and prepares the environment
REM ============================================================

setlocal
cd /d "%~dp0"

echo ============================================================
echo  HOUSOFT META - SETUP
echo ============================================================
echo.

REM Check Python
where py >nul 2>nul
if errorlevel 1 (
    where python >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Python not found. Install Python 3.11+ from python.org
        echo        and make sure to check "Add Python to PATH" during install.
        pause
        exit /b 1
    )
    set "PY=python"
) else (
    set "PY=py"
)

echo [1/4] Using Python command: %PY%
%PY% --version

echo.
echo [2/4] Upgrading pip...
%PY% -m pip install --upgrade pip

echo.
echo [3/4] Installing Python dependencies...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [4/4] Creating folders...
if not exist logs mkdir logs
if not exist templates mkdir templates

echo.
echo ============================================================
echo  SETUP COMPLETE
echo ============================================================
echo.
echo Next steps:
echo   1. Edit .env to set your ngrok auth token and dashboard password
echo   2. Capture Housoft UI templates: %PY% capture_templates.py
echo   3. Start the system:             start.bat
echo.
echo To install auto-start (run at Windows logon):
echo   %PY% install_autostart.py
echo   (must run as Administrator)
echo.
pause
endlocal
