@echo off
title CyberTrace AI - Starting Services...
color 0B

echo ===============================================================================
echo                CYBERTRACE AI - INTELLIGENT DIGITAL EVIDENCE RECONSTRUCTION
echo ===============================================================================
echo.
echo [*] Initializing CyberTrace AI environment...
echo.

:: Ensure we are in the script's root directory
cd /d "%~dp0"

:: 1. Check Backend Virtual Environment
if not exist "backend\venv\Scripts\python.exe" (
    color 0C
    echo [ERROR] Backend virtual environment not found at backend\venv!
    echo Please create it first using:
    echo   cd backend
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

:: 2. Check Frontend node_modules
if not exist "frontend\node_modules\" (
    echo [*] Frontend dependencies not found. Installing node_modules...
    cd /d "%~dp0frontend"
    call npm install
    cd /d "%~dp0"
)

:: 3. Kill existing stale processes on ports 8000 and 3000 to prevent port collisions
echo [*] Checking and releasing ports 8000 and 3000 if occupied...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>&1
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>&1

:: 4. Start Backend Server in a new window
echo [*] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "CyberTrace-AI-Backend" cmd /k "title CyberTrace-AI-Backend && color 0A && cd /d ""%~dp0backend"" && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: 5. Start Frontend Server in a new window
echo [*] Starting React 19 Frontend on http://localhost:3000 ...
start "CyberTrace-AI-Frontend" cmd /k "title CyberTrace-AI-Frontend && color 09 && cd /d ""%~dp0frontend"" && npm run dev"

:: 6. Wait for servers to spin up (5 seconds)
echo.
echo [*] Waiting for services to initialize...
timeout /t 5 /nobreak >nul

:: 7. Automatically open the default browser to the web app
echo [*] Launching CyberTrace AI in your web browser...
start http://localhost:3000

echo.
echo ===============================================================================
echo                     CYBERTRACE AI IS NOW RUNNING!
echo ===============================================================================
echo.
echo   [+] Frontend Web Application:  http://localhost:3000
echo   [+] Backend REST API:          http://127.0.0.1:8000
echo   [+] Interactive API Docs:      http://127.0.0.1:8000/api/docs
echo.
echo   [*] Keep the backend and frontend terminal windows open while working.
echo   [*] To stop all services anytime, simply double-click: STOP_CYBERTRACE.bat
echo.
echo ===============================================================================
pause
