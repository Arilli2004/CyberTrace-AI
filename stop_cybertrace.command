#!/bin/bash
# =====================================================================
# CyberTrace AI — Stop All Services (macOS / Linux)
# =====================================================================

echo "======================================================================"
echo "  CYBERTRACE AI — STOPPING ALL SERVICES"
echo "======================================================================"

echo "[1/2] Stopping FastAPI Backend (Port 8000)..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

echo "[2/2] Stopping React Frontend (Port 3000)..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

pkill -f uvicorn 2>/dev/null || true
pkill -f vite 2>/dev/null || true

echo ""
echo "[OK] All CyberTrace AI services stopped successfully!"
echo "======================================================================"
