# CyberTrace AI -- Application Flow Document

Version: 1.0

# Purpose

This document describes the complete end-to-end workflow of the
CyberTrace AI application, including user interactions, backend
processing, AI pipeline, and report generation.

------------------------------------------------------------------------

# Overall Application Flow

    Launch Application
            ↓
    User Authentication
            ↓
    Dashboard
            ↓
    Create / Select Investigation Case
            ↓
    Upload Digital Evidence
            ↓
    Evidence Validation
            ↓
    Evidence Storage
            ↓
    Log Parsing
            ↓
    Evidence Normalization
            ↓
    Event Correlation
            ↓
    Timeline Reconstruction
            ↓
    Threat Detection
            ↓
    AI Investigation
            ↓
    Visualization Dashboard
            ↓
    Generate Investigation Report
            ↓
    Export / Archive Case

# 1. Launch Application

Frontend loads. Backend health is checked. Database connection verified.
User session restored if token exists.

# 2. Authentication Flow

-   Register
-   Login
-   JWT token issued
-   Token stored securely
-   Redirect to Dashboard

Failure: - Invalid credentials - Expired token - Locked account

# 3. Dashboard Flow

Displays: - Recent Cases - Total Cases - Evidence Count - High Severity
Alerts - AI Recommendations - Investigation Status

Actions: - Create Case - Open Case - Delete Case - Search Cases

# 4. Case Management Flow

Create Case → Enter title → Description → Investigator → Save

Status: New → Evidence Uploaded → Parsing → Analysis → Completed →
Archived

# 5. Evidence Upload Flow

Supported: - EVTX - LOG - CSV - JSON - XML

Process: Select Files → Validate extension → Calculate SHA-256 → Store
metadata → Save file → Queue parsing

Validation: - Duplicate detection - Empty file rejection - Maximum size
check

# 6. Parsing Flow

Read file → Identify format → Select parser → Extract events → Convert
to normalized schema

Normalized fields: - timestamp - source - host - user - event_type -
severity - description

# 7. Correlation Flow

Rules: - Same user - Same IP - Same hostname - Same process - Time
proximity - Parent-child processes

Output: Related event graph

# 8. Timeline Reconstruction

Sort events chronologically. Merge correlated events. Assign confidence
score. Generate investigation timeline.

# 9. Detection Engine Flow

Detect: - Failed logins - Privilege escalation - USB insertion - File
deletion - PowerShell execution - Log clearing - Lateral movement

Each alert contains: - Severity - Confidence - Description - Evidence
references

# 10. AI Investigation Flow

Input: - Timeline - Events - Alerts - Metadata

Pipeline: Evidence → Context Builder → LLM Prompt → AI Analysis →
Recommendations

Outputs: - Executive Summary - Root Cause - Suspicious Activities - Risk
Level - Next Investigation Steps

# 11. Visualization Flow

Views: - Timeline - Attack Path Graph - Event Distribution - Severity
Chart - User Activity - Host Activity - Geographic IP Map (future)

# 12. Report Generation Flow

Collect: - Case Details - Timeline - AI Summary - Evidence - Charts

Generate: - PDF - DOCX

# 13. Search Flow

Search by: - User - IP - Host - Event ID - Keyword - Date Range -
Severity

# 14. Settings Flow

-   Update Profile
-   Change Password
-   API Key
-   Theme
-   Parser Settings
-   AI Model Settings

# 15. Error Handling

Upload errors Parsing failures Database errors API failures AI timeout
Unsupported format

Each error is logged and shown with actionable messages.

# 16. Background Jobs

-   File hashing
-   Parsing
-   AI report generation
-   Index creation
-   Cache refresh

# 17. Notifications

-   Upload complete
-   Parsing complete
-   Analysis complete
-   Report generated
-   Errors

# 18. Security Flow

User Login → JWT Verification → RBAC Authorization → API Access → Audit
Log

Evidence: Upload → SHA-256 Hash → Immutable Storage → Verification

# 19. Complete Data Flow

    User
     ↓
    React Frontend
     ↓
    FastAPI
     ↓
    Authentication
     ↓
    Case Service
     ↓
    Evidence Upload
     ↓
    Parser Engine
     ↓
    Normalization
     ↓
    Correlation Engine
     ↓
    Timeline Engine
     ↓
    Detection Engine
     ↓
    AI Service
     ↓
    Visualization
     ↓
    Report Generator
     ↓
    Export

# 20. End-to-End User Journey

1.  Login
2.  Create Case
3.  Upload Evidence
4.  Parse Logs
5.  Normalize Data
6.  Correlate Events
7.  Build Timeline
8.  Detect Threats
9.  Review Dashboard
10. Chat with AI Assistant
11. Generate Report
12. Export Results
13. Archive Case

# Future Flow

Live Collection → Stream Processing → Real-time Detection → Continuous
AI Analysis → Live Dashboard

End of Application Flow Document.
