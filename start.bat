@echo off
REM ============================================================
REM  Housoft Meta - Start Script
REM  Launches the automation system with watchdog
REM ============================================================

setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    set "PY=python"
) else (
    set "PY=py"
)

echo ============================================================
echo  HOUSOFT META - STARTING
echo ============================================================
echo.
echo Dashboard will be available at:
echo   Local:  http://localhost:5000
echo   Mobile: https://[your-ngrok-url].ngrok-free.app
echo.
echo Press Ctrl+C to stop.
echo.

%PY% watchdog.py

endlocal
