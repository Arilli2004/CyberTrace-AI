@echo off
title CyberTrace AI - Stop All Services
cls
echo ======================================================================
echo   CYBERTRACE AI - STOPPING ALL SERVICES (WINDOWS)
echo ======================================================================
echo.

echo [1/2] Terminating FastAPI Backend process on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>nul
    echo       - Process %%a terminated.
)

echo [2/2] Terminating React Frontend process on port 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>nul
    echo       - Process %%a terminated.
)

rem Additional safety cleanup for uvicorn and vite processes
powershell -Command "Stop-Process -Name 'node' -ErrorAction SilentlyContinue" >nul 2>nul

echo.
echo ======================================================================
echo   [OK] All CyberTrace AI services stopped cleanly!
echo ======================================================================
echo.
pause
