# Deployment Guide — CyberTrace AI

---

## 1. Environment Setup

Copy `.env.example` to `.env` and fill in credentials:
```bash
cp .env.example .env
```

## 2. Option 1: Docker Compose (Recommended)

To build and launch all containers (PostgreSQL, Redis, FastAPI, React, Nginx):
```bash
docker-compose up --build -d
```

Check status:
```bash
docker-compose ps
```

Visit:
- Frontend UI: `http://localhost:3000` (or `http://localhost:80`)
- Backend API Docs: `http://localhost:8000/api/docs`

## 3. Option 2: Development Setup

### Backend
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 4. Production Considerations
- Set `DEBUG=false` in `.env`.
- Change `SECRET_KEY` to a 64-character random string.
- Provide a valid `OPENAI_API_KEY` for AI assistant capabilities.
