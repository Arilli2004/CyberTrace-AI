# High-Level Design (HLD) — CyberTrace AI

**Version:** 1.0  
**Date:** August 2026  

---

## 1. Architectural Overview

```
[ User / Browser ] 
       │ HTTP / WebSockets
       ▼
 [ Nginx Proxy ] ───► [ React 19 Frontend (Vite) ]
       │
       ▼
 [ FastAPI Backend ]
   ├── Authentication Module (JWT + Bcrypt)
   ├── Case & Evidence Service
   ├── Multi-Format Parser Engine (EVTX, Syslog, CSV, JSON, XML)
   ├── Rule Correlation & Detection Engine
   ├── Timeline Reconstruction Builder
   └── AI Service (OpenAI API / LangChain)
       │
   ┌───┴───────────────┐
   ▼                   ▼
 [ PostgreSQL DB ]   [ Redis Cache ]
```

## 2. Component Design
1. **Frontend:** Built with React 19, TypeScript, Tailwind CSS, Zustand, and TanStack Query.
2. **API Gateway:** FastAPI with Uvicorn ASGI server and CORS middleware.
3. **Database Layer:** Async SQLAlchemy 2.0 with PostgreSQL 15.
4. **Log Parsers:** Modular Python parsers using `python-evtx`, `lxml`, `json`, and `csv`.
5. **AI Pipeline:** OpenAI API client with context builders and prompt templates.
