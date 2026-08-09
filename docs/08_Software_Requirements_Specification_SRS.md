# Software Requirements Specification (SRS) — CyberTrace AI

**Version:** 1.0  
**Date:** August 2026  

---

## 1. Introduction
This Software Requirements Specification (SRS) details the functional and non-functional requirements for CyberTrace AI.

## 2. Functional Requirements
### FR-1: Authentication & Authorization
- User registration and login using JWT tokens and bcrypt password hashing.
- Role-based access control (Admin, Investigator, Analyst, Viewer).

### FR-2: Case Management
- Create, read, update, and delete investigation cases.
- Priority levels: Low, Medium, High, Critical.
- Statuses: New, Evidence Uploaded, Parsing, Analysis, Completed, Archived.

### FR-3: Evidence Upload & Ingestion
- Upload `.evtx`, `.log`, `.csv`, `.json`, and `.xml` files up to 500 MB.
- Calculate SHA-256 checksums to verify evidence integrity and prevent duplicates.

### FR-4: Parsing & Normalization
- Extract timestamp, event type, user, host, IP address, process, severity, and raw data.

### FR-5: Threat Detection & Event Correlation
- Rule-based detection (Brute force login, privilege escalation, log clearing, etc.).
- Event correlation across users, IPs, and time windows.

### FR-6: AI Investigation Assistant
- Interactive Q&A over evidence timelines using OpenAI GPT models.
- Automated Executive Summary and Root Cause analysis generation.

## 3. Non-Functional Requirements
- **Performance:** Login response < 1s; dashboard load < 3s; 100 MB log parsing < 30s.
- **Security:** HTTPS, JWT token expiration, input sanitization, SHA-256 evidence hashing.
- **Scalability:** Docker containerized micro-services with Redis task queuing.
