# CyberTrace AI 🔍

**Intelligent Digital Evidence Reconstruction System**

> An AI-powered digital forensics platform that automates cyber incident investigation by collecting, parsing, correlating, and reconstructing digital evidence.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![React](https://img.shields.io/badge/react-19-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## 🚀 Features

- 📁 **Evidence Upload** — EVTX, LOG, CSV, JSON, XML
- 🔍 **Log Parsing** — Multi-format parser engine
- 🔗 **Event Correlation** — Rule-based correlation engine
- 📅 **Timeline Reconstruction** — Chronological attack timelines
- 🚨 **Threat Detection** — Suspicious activity detection
- 🤖 **AI Investigation Assistant** — LLM-powered analysis
- 📊 **Dashboard & Visualizations** — Charts, graphs, and more
- 📄 **Report Generation** — PDF & DOCX reports

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.12+, SQLAlchemy, Alembic |
| Database | PostgreSQL, Redis |
| AI/ML | OpenAI API, LangChain, FAISS, Sentence Transformers |
| DevOps | Docker, Docker Compose |

---

## 📦 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### Option 1: Docker (Recommended)

```bash
git clone <repo-url>
cd CyberTrace
cp .env.example .env
# Edit .env with your credentials
docker-compose up --build
```

Visit: `http://localhost:3000`

### Option 2: Manual Setup

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📁 Project Structure

```
CyberTrace/
├── frontend/        React + Vite + TypeScript frontend
├── backend/         FastAPI Python backend
├── database/        SQL schema, seeds, migrations
├── ai/              AI prompts, embeddings, vector DB
├── datasets/        Sample forensic datasets
├── reports/         Generated reports
├── scripts/         Setup and utility scripts
├── docker/          Dockerfiles
└── docs/            All project documentation
```

---

## 🔧 Environment Variables

See `.env.example` for all required variables.

---

## 📚 Documentation

All documentation is in the `docs/` folder.

---

## 👥 Team

CyberTrace AI — Forensic Investigation Platform
