#!/bin/bash
# =====================================================================
# CyberTrace AI — macOS Multi-Tab Startup Launcher
# Double-click this file in Finder to launch Backend & Frontend in Terminal tabs.
# =====================================================================

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python3"

echo "======================================================================"
echo "  CYBERTRACE AI — LAUNCHING FULL-STACK APPLICATION"
echo "======================================================================"
echo "Project Directory: $PROJECT_DIR"
echo "Python Binary    : $PYTHON_BIN"
echo "Frontend Port    : 3000"
echo "Backend Port     : 8000"
echo ""

# Clean up any stale processes on ports 8000 & 3000
pkill -f uvicorn 2>/dev/null || true
pkill -f vite 2>/dev/null || true
sleep 1

# AppleScript to open macOS Terminal tabs using native 'do script'
osascript <<EOF
tell application "Terminal"
    activate

    -- Tab 1: FastAPI Backend (Port 8000)
    do script "cd '$PROJECT_DIR' && export PYTHONPATH=backend && echo '====================================================' && echo '  🚀 CYBERTRACE AI BACKEND (FastAPI - Port 8000)' && echo '====================================================' && '$PYTHON_BIN' -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --loop asyncio --ws none"

    -- Tab 2: React Frontend (Port 3000)
    do script "cd '$PROJECT_DIR/frontend' && echo '====================================================' && echo '  🎨 CYBERTRACE AI FRONTEND (React + Vite - Port 3000)' && echo '====================================================' && npm run dev"

    -- Tab 3: System Status & Web Browser Auto-Launch
    do script "cd '$PROJECT_DIR' && echo '====================================================' && echo '  🌐 CYBERTRACE AI SYSTEM LINKS' && echo '====================================================' && echo 'Backend API Docs : http://localhost:8000/api/docs' && echo 'Frontend Web UI  : http://localhost:3000' && echo '' && sleep 4 && open http://localhost:8000/api/docs && open http://localhost:3000"

end tell
EOF

echo "✓ Terminal tabs launched successfully!"
echo "• Tab 1: FastAPI Backend (http://localhost:8000)"
echo "• Tab 2: React Frontend  (http://localhost:3000)"
echo "• Tab 3: API Docs & Web App Auto-Launcher"
echo ""
echo "Press [Enter] to close this launcher..."
read key
