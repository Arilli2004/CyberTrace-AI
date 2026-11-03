@echo off
title CyberTrace AI - Stopping Services...
color 0C

echo ===============================================================================
echo                CYBERTRACE AI - TERMINATING ALL SERVICES
echo ===============================================================================
echo.

:: Ensure we are in the script's root directory
cd /d "%~dp0"

echo [*] Stopping backend processes on port 8000 (FastAPI / Uvicorn)...
powershell -NoProfile -Command "$pids = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; if ($pids) { $pids | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue; Write-Host ('    [+] Terminated PID: ' + $_) } } else { Write-Host '    [-] No backend process found on port 8000.' }"

echo.
echo [*] Stopping frontend processes on port 3000 (Vite / Node.js)...
powershell -NoProfile -Command "$pids = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; if ($pids) { $pids | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue; Write-Host ('    [+] Terminated PID: ' + $_) } } else { Write-Host '    [-] No frontend process found on port 3000.' }"

echo.
echo [*] Closing associated command windows...
taskkill /FI "WINDOWTITLE eq CyberTrace-AI-Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq CyberTrace-AI-Frontend*" /T /F >nul 2>&1

echo.
echo ===============================================================================
echo               ALL CYBERTRACE AI SERVICES ARE NOW STOPPED!
echo ===============================================================================
echo.
echo Ports 8000 and 3000 have been freed successfully.
echo.
timeout /t 3 /nobreak >nul
exit
