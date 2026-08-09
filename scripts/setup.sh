#!/usr/bin/env bash
# CyberTrace AI Setup Script for Linux/macOS

set -e

echo "🚀 Setting up CyberTrace AI environment..."

# Check Python version
python3 --version || { echo "Python 3 is required"; exit 1; }

# Setup backend venv
echo "📦 Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Setup frontend
echo "💻 Installing Node.js packages..."
cd frontend
npm install
cd ..

echo "✅ CyberTrace AI Setup Complete!"
