@echo off
title CyberTrace AI - Database Inspector
cls
echo ======================================================================
echo   CYBERTRACE AI - DATABASE INSPECTOR
echo ======================================================================
echo.

cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    pause
    exit /b 1
)

python backend\scripts\view_db.py

echo.
pause
