# API Documentation — CyberTrace AI

**Base URL:** `http://localhost:8000/api`  
**Swagger UI:** `http://localhost:8000/api/docs`  

---

## Authentication Endpoints
- `POST /api/auth/register` — Register a new user
- `POST /api/auth/login` — Authenticate and receive JWT token
- `GET /api/auth/profile` — Get profile of authenticated user

## Case Management Endpoints
- `GET /api/cases/` — List all investigation cases
- `POST /api/cases/` — Create a new case
- `GET /api/cases/{case_id}` — Get case details
- `PUT /api/cases/{case_id}` — Update case details or status
- `DELETE /api/cases/{case_id}` — Delete case and associated data

## Evidence Endpoints
- `POST /api/evidence/upload` — Upload evidence file(s)
- `GET /api/evidence/case/{case_id}` — List evidence files for a case
- `DELETE /api/evidence/{evidence_id}` — Remove evidence file

## Timeline Endpoints
- `GET /api/timeline/{case_id}` — Get chronological event timeline
- `GET /api/timeline/{case_id}/suspicious` — Get flagged suspicious events

## AI & Reports Endpoints
- `POST /api/ai/analyze` — Run AI analysis or query investigator question
- `POST /api/ai/report` — Generate full AI investigation report
- `GET /api/reports/case/{case_id}` — List generated reports for a case
- `GET /api/reports/{report_id}/download` — Download report PDF
