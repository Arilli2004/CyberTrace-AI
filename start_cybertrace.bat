@echo off
title CyberTrace AI - Master Launcher
cls

rem Clear any invalid system SSL certificate environment variables set by PostgreSQL
set "REQUESTS_CA_BUNDLE="
set "SSL_CERT_FILE="
set "CURL_CA_BUNDLE="

echo ======================================================================
echo   CYBERTRACE AI - AUTOMATED STARTUP (WINDOWS)
echo ======================================================================
echo.

rem Navigate to project root directory
cd /d "%~dp0"

rem 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to system PATH!
    echo Please install Python 3.12+ and make sure to check "Add Python to PATH".
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

rem 2. Check Node.js and Frontend dependencies
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Node.js (npm) is not found in PATH!
) else (
    if not exist "frontend\node_modules" (
        echo [SETUP] Installing frontend node_modules (npm install)...
        cd frontend
        call npm install
        cd ..
    )
)

rem 3. Check PostgreSQL Setup and Fallback Notice
echo [SETUP] Checking database configuration...
where psql >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] PostgreSQL CLI detected. Initializing database if needed...
    psql -U postgres -c "CREATE DATABASE cybertrace_db;" >nul 2>nul
    psql -U postgres -c "CREATE USER cybertrace WITH PASSWORD 'cybertrace123';" >nul 2>nul
    psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE cybertrace_db TO cybertrace;" >nul 2>nul
) else (
    echo [NOTICE] PostgreSQL not found. Using built-in SQLite (cybertrace.db) with auto-seeded data!
)

rem 4. Kill any stale processes running on Ports 8000 and 3000
echo [SETUP] Cleaning up existing ports 8000 and 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>nul

echo.
echo ======================================================================
echo   🚀 LAUNCHING SERVICES...
echo ======================================================================
echo.

rem Launch FastAPI Backend in a new terminal window
echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "CyberTrace AI - FastAPI Backend" cmd /k "cd /d %~dp0backend && set ""REQUESTS_CA_BUNDLE="" && set ""SSL_CERT_FILE="" && set ""CURL_CA_BUNDLE="" && set PYTHONPATH=. && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

rem Launch React Frontend in a new terminal window
echo [2/2] Starting React Frontend on http://localhost:3000 ...
start "CyberTrace AI - React Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Booting up services (3 seconds)...
timeout /t 3 /nobreak >nul

rem Auto-Open Output in Default Web Browser
echo [OK] Opening Application UI and Backend API Docs in browser...
start http://localhost:3000
start http://localhost:8000/api/docs

echo.
echo ======================================================================
echo   CYBERTRACE AI IS NOW LIVE!
echo   ------------------------------------------------------------------
echo   • Frontend Web UI  : http://localhost:3000
echo   • Backend API Docs : http://localhost:8000/api/docs
echo   • Default Admin    : admin@cybertrace.ai / Admin@123
echo   ------------------------------------------------------------------
echo   To stop all services, double-click: stop_cybertrace.bat
echo ======================================================================
echo.
pause
