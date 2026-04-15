@echo off
REM ============================================================
REM  Housoft Meta - Stop Script
REM  Stops all watchdog and main.py processes
REM ============================================================

setlocal
cd /d "%~dp0"

echo Stopping Housoft Meta...

REM Kill any Python processes running watchdog.py or main.py
taskkill /F /FI "WINDOWTITLE eq watchdog.py*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq main.py*" >nul 2>nul

REM Also try by command line match (requires Windows 10+)
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH 2^>nul') do (
    taskkill /F /PID %%i >nul 2>nul
)
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV /NH 2^>nul') do (
    taskkill /F /PID %%i >nul 2>nul
)

echo Done.
pause
endlocal
