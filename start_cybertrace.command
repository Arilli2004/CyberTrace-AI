#!/bin/bash
# =====================================================================
# CyberTrace AI — Automated Startup & Environment Setup (macOS / Linux)
# =====================================================================

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

echo "======================================================================"
echo "  CYBERTRACE AI — AUTOMATED STARTUP & ENVIRONMENT SETUP"
echo "======================================================================"
echo "Project Directory: $PROJECT_DIR"
echo ""

# 1. Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3.12+."
    exit 1
fi

# 2. Check & Create Virtual Environment
if [ ! -d "backend/venv" ]; then
    echo "[SETUP] Creating Python virtual environment in backend/venv..."
    python3 -m venv backend/venv
fi

PYTHON_BIN="$PROJECT_DIR/backend/venv/bin/python"
echo "[SETUP] Installing & verifying Python backend dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pip --quiet
"$PYTHON_BIN" -m pip install -r backend/requirements.txt --quiet

# 3. Check Node.js and Frontend dependencies
if ! command -v npm &> /dev/null; then
    echo "[WARNING] npm (Node.js) is not found in PATH."
else
    if [ ! -d "frontend/node_modules" ]; then
        echo "[SETUP] Installing frontend node_modules (npm install)..."
        (cd frontend && npm install)
    fi
fi

# 4. Check PostgreSQL Database Setup
echo "[SETUP] Checking PostgreSQL database service..."
if command -v psql &> /dev/null; then
    echo "[OK] PostgreSQL CLI (psql) detected."
    psql -U postgres -c "CREATE DATABASE cybertrace_db;" 2>/dev/null || true
    psql -U postgres -c "CREATE USER cybertrace WITH PASSWORD 'cybertrace123';" 2>/dev/null || true
    psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE cybertrace_db TO cybertrace;" 2>/dev/null || true
else
    echo "[NOTICE] PostgreSQL (psql) not installed. CyberTrace AI will auto-fallback to SQLite (cybertrace.db)."
fi

# 5. Clean up any stale processes on ports 8000 & 3000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1

# 6. Open Terminal Windows / Tabs (macOS AppleScript support or Linux nohup fallback)
if [[ "$OSTYPE" == "darwin"* ]]; then
    osascript <<EOF
    tell application "Terminal"
        activate

        -- Tab 1: FastAPI Backend (Port 8000)
        do script "cd '$PROJECT_DIR/backend' && export PYTHONPATH=. && echo '====================================================' && echo '  🚀 CYBERTRACE AI BACKEND (FastAPI - Port 8000)' && echo '====================================================' && '$PYTHON_BIN' -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

        -- Tab 2: React Frontend (Port 3000)
        do script "cd '$PROJECT_DIR/frontend' && echo '====================================================' && echo '  🎨 CYBERTRACE AI FRONTEND (React + Vite - Port 3000)' && echo '====================================================' && npm run dev"

        -- Tab 3: System Status & Browser Auto-Launch
        do script "cd '$PROJECT_DIR' && echo '====================================================' && echo '  🌐 CYBERTRACE AI SYSTEM LINKS' && echo '====================================================' && echo 'Backend API Docs : http://localhost:8000/api/docs' && echo 'Frontend Web UI  : http://localhost:3000' && echo '' && sleep 4 && open http://localhost:8000/api/docs && open http://localhost:3000"

    end tell
EOF
else
    # Linux fallback
    (cd backend && export PYTHONPATH=. && "$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) &
    (cd frontend && npm run dev) &
    sleep 4
    xdg-open http://localhost:3000 2>/dev/null || true
    xdg-open http://localhost:8000/api/docs 2>/dev/null || true
fi

echo "======================================================================"
echo "  ✓ CyberTrace AI launched successfully!"
echo "  • Frontend Web UI  : http://localhost:3000"
echo "  • Backend API Docs : http://localhost:8000/api/docs"
echo "======================================================================"
